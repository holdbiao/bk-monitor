# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - 监控平台 (BlueKing - Monitor) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""


from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from core.drf_resource.exceptions import CustomException
from core.drf_resource.base import Resource
from core.drf_resource import resource
from bkmonitor.utils.cache import CacheType, using_cache
from bkmonitor.utils.common_utils import safe_int
from bkmonitor.views import serializers
from common.log import logger
from constants.data_source import LabelType
from core.drf_resource import api
from core.drf_resource.contrib.cache import CacheResource
from monitor import constants


@using_cache(CacheType.DATA(60 * 60))
def get_key_alias(result_table_id):
    """获取字段的别名"""

    result = api.metadata.get_result_table(table_id=result_table_id)
    return {field["field_name"]: field["description"] or field["field_name"] for field in result["field_list"]}


def has_fstype_dimension(result_table_id):
    key_alias = resource.commons.get_key_alias.cacheless(result_table_id)
    return settings.FILE_SYSTEM_TYPE_FIELD_NAME in key_alias


def get_desc_by_field(rt_id, field):
    """
    获取表字段的中文描述
    """
    try:
        ret = get_key_alias(rt_id).get(field, field)
        return _(ret) if ret else ret
    except Exception as e:
        logger.warning(_("获取表字段的中文描述失败") + " rt_id:{} field:{}, except:{}".format(rt_id, field, e))
        return field


def trans_bkcloud_bizid(kwargs):
    for param_key in kwargs:
        if param_key in constants.BIZ_ID_FIELD_NAMES:
            value = safe_int(kwargs.get(param_key, 0), 0)
            if value < settings.RT_TABLE_PREFIX_VALUE:
                kwargs[param_key] = settings.RT_TABLE_PREFIX_VALUE + int(value)
        if param_key in ["result_table_id", "rt_id", "target_result_table_id"]:
            kwargs[param_key] = trans_bkcloud_rt_bizid(kwargs[param_key])
    return kwargs


def trans_bkcloud_rt_bizid(result_table_id):
    # rt id 第一段为biz_id
    final_rt = result_table_id
    rt_id_infos = result_table_id.split("_")
    if (not rt_id_infos) or (len(rt_id_infos) < 2):
        return result_table_id
    biz_id = safe_int(rt_id_infos[0], 0)
    if biz_id < settings.RT_TABLE_PREFIX_VALUE:
        rt_id_infos[0] = "%s" % (int(biz_id) + settings.RT_TABLE_PREFIX_VALUE)
        final_rt = "_".join(rt_id_infos)
    return final_rt


class ResultTableResponseSerializer(serializers.Serializer):
    class FieldSerializer(serializers.Serializer):
        field = serializers.CharField(required=True, label=_lazy("字段名称"))
        description = serializers.CharField(required=True, allow_blank=True, label=_lazy("字段描述"))
        is_dimension = serializers.BooleanField(required=True, label=_lazy("是否为维度字段"))
        processor = serializers.CharField(default=None, allow_null=True, label=_lazy("聚合方法"), allow_blank=True)
        processor_args = serializers.CharField(default=None, allow_null=True, allow_blank=True, label=_lazy("聚合方法参数"))

    id = serializers.CharField(required=True, label=_lazy("结果表名称"))
    storages = serializers.ListField(required=True, label=_lazy("存储类型"))
    description = serializers.CharField(required=True, allow_blank=True, label=_lazy("结果表描述"))
    count_freq = serializers.IntegerField(required=True, label=_lazy("监控周期（秒）"), allow_null=True)
    fields = FieldSerializer(required=True, many=True, label=_lazy("结果表字段列表"))
    is_statistical = serializers.BooleanField(required=True, label=_lazy("是否为统计结果表"))
    need_access = serializers.BooleanField(required=True, label=_lazy("是否需要接入"))
    rt_id_backend = serializers.CharField(required=False, allow_blank=True, label=_lazy("未处理的rt表"))

    def validate(self, attrs):
        attrs["result_table_id"] = attrs["id"]
        return attrs


class QueryDataBackend(object):
    def list_result_table(self, bk_biz_id):
        raise NotImplementedError

    def get_result_table(self, bk_biz_id, result_table_id):
        raise NotImplementedError

    def adapt_data(self, rt_info, bk_biz_id):
        raise NotImplementedError


class QueryMetadataBackend(QueryDataBackend):
    def list_result_table(self, bk_biz_id):
        result_tables = api.metadata.list_monitor_result_table(bk_biz_id=bk_biz_id, is_public_include=True)
        return [self.adapt_data(rt_info, bk_biz_id) for rt_info in result_tables]

    def get_result_table(self, bk_biz_id, result_table_id):
        rt_info = api.metadata.get_result_table(table_id=result_table_id)
        return self.adapt_data(rt_info, bk_biz_id)

    def adapt_data(self, rt_info, bk_biz_id):
        rt_id = rt_info["table_id"].replace(".", "_")
        rt_id_backend = rt_info["table_id"]
        if not rt_info["bk_biz_id"]:
            # 将全业务RT表名转换为单业务RT表名
            rt_id = "{}_{}".format(bk_biz_id, rt_id)
            rt_id_backend = "{}_{}".format(bk_biz_id, rt_id_backend)

        adapted_rt_info = {
            "count_freq": 0,
            "description": rt_info["table_name_zh"],
            "fields": [
                {
                    "field": field["field_name"],
                    "description": field["description"],
                    "is_dimension": field["tag"] in ["dimension", "group"],
                }
                for field in rt_info["field_list"]
            ],
            "id": rt_id,
            "is_statistical": False,
            "storages": ["tsdb"],
            "need_access": False,
            # 未处理的rt表
            "rt_id_backend": rt_id_backend,
        }
        return adapted_rt_info


class QueryBkdataBackend(QueryDataBackend):
    def list_result_table(self, bk_biz_id):
        result_tables = api.bkdata.list_result_table(bk_biz_id=bk_biz_id)
        real_result_tables = self.filter_result_table(result_tables)
        return [self.adapt_data(rt_info, bk_biz_id) for rt_info in real_result_tables]

    def get_result_table(self, bk_biz_id, result_table_id):
        rt_info = api.bkdata.get_result_table(result_table_id=result_table_id)
        return self.adapt_data(rt_info, bk_biz_id)

    def filter_result_table(self, result_tables):
        return_table = []
        constant_storage = {"mysql", "tsdb", "tspider"}
        for table in result_tables:
            if not set(table["storages"].keys()) & constant_storage or table["generate_type"] != "user":
                continue
            return_table.append(table)
        return return_table

    def adapt_data(self, rt_info, bk_biz_id):
        rt_id = rt_info["result_table_id"]
        storages = list(rt_info["storages"].keys())
        if "tsdb" in storages:
            storages = ["bk_tsdb"]
        elif "tspider" in storages:
            storages = ["bk_tspider"]
        else:
            storages = ["bk_mysql"]

        adapted_rt_info = {
            "count_freq": rt_info["count_freq"],
            "description": rt_info["description"],
            "fields": [
                {
                    "field": field["field_name"],
                    "description": field["field_alias"],
                    "is_dimension": field["is_dimension"],
                }
                for field in rt_info["fields"]
            ],
            "id": rt_id,
            "is_statistical": False,
            "storages": storages,
            "need_access": False,
        }
        return adapted_rt_info


class ListResultTableAccessInfoResource(Resource):
    """
    获取业务下的结果表列表（包含全业务）
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))

    ResponseSerializer = ResultTableResponseSerializer

    many_response_data = True

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        query_data_backends = [QueryMetadataBackend, QueryBkdataBackend]
        return_mes = []
        for backend in query_data_backends:
            try:
                result_table_mes = backend().list_result_table(bk_biz_id)
                return_mes.extend(result_table_mes)
            except Exception as e:
                logger.error(_("获取列表失败：%s") % e)
        return return_mes


class GetResultTableAccessInfoResource(Resource):
    """
    根据结果表ID获取结果表信息
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务 ID"))
        id = serializers.CharField(required=True, label=_lazy("结果表ID"))

    ResponseSerializer = ResultTableResponseSerializer

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        result_table_id = validated_request_data["id"]
        query_data_backends = [QueryMetadataBackend, QueryBkdataBackend]
        for backend in query_data_backends:
            try:
                return backend().get_result_table(bk_biz_id, result_table_id)
            except Exception:
                pass

        raise CustomException(_("结果表不存在:%s") % result_table_id)


class GetLabelResource(CacheResource):
    """
    列出结果表的分类标签
    """

    cache_type = CacheType.DATA

    class RequestSerializer(serializers.Serializer):
        # 标签层级, 层级从1开始计算, 该配置只在label_type为result_table时生效
        label_type = serializers.CharField(required=False, default=LabelType.ResultTableLabel, label=_lazy("标签类别"))
        level = serializers.IntegerField(required=False, label=_lazy("标签层级"))
        include_admin_only = serializers.BooleanField(required=False, default=True, label=_lazy("是否展示管理员标签"))

    def perform_request(self, validated_request_data):
        try:
            result = api.metadata.get_label(**validated_request_data)
        except Exception as e:
            raise CustomException(_("获取分类标签失败：{}").format(e))

        return_data = []
        index = 0
        first_mapping_second = {}
        for label_msg in result["result_table_label"]:
            if label_msg["level"] == 1:
                return_data.append(
                    {
                        "id": label_msg["label_id"],
                        "name": label_msg["label_name"],
                        "index": label_msg["index"],
                        "children": [],
                    }
                )
                first_mapping_second[label_msg["label_id"]] = index
                index += 1

        for label_msg in result["result_table_label"]:
            parent_label = label_msg.get("parent_label", None)
            if parent_label:
                index = first_mapping_second[parent_label]
                return_data[index]["children"].append(
                    {"id": label_msg["label_id"], "name": label_msg["label_name"], "index": label_msg["index"]}
                )

        return_data.sort(key=lambda x: x["index"])
        return_data = [label_msg for label_msg in return_data if len(label_msg["children"]) > 0]
        return return_data


def get_label_msg(label):
    """
    根据二级标签获取一级标签信息
    """
    result = {}
    label_map = resource.commons.get_label()
    for first_label in label_map:
        for second_label in first_label["children"]:
            if second_label["id"] == label:
                result["first_label"] = first_label["id"]
                result["first_label_name"] = first_label["name"]
                result["second_label"] = second_label["id"]
                result["second_label_name"] = second_label["name"]
                return result
    else:
        raise CustomException(_("获取{}一级标签失败".format(label)))
