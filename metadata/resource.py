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


import base64
import json

from django.conf import settings
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from rest_framework import serializers

from bkmonitor.utils import consul
from core.drf_resource import Resource
from bkmonitor.utils.request import get_app_code_by_request, get_request
from metadata import config, models


class FieldSerializer(serializers.Serializer):
    field_name = serializers.CharField(required=True, label=_("字段名"))
    field_type = serializers.CharField(required=True, label=_("字段类型"))
    tag = serializers.CharField(required=True, label=_("字段类型，指标或维度"))
    unit = serializers.CharField(required=False, allow_blank=True, label=_("字段单位"))
    description = serializers.CharField(required=False, allow_blank=True, label=_("字段描述"))
    alias_name = serializers.CharField(required=False, label=_("字段别名"), default="", allow_blank=True)
    option = serializers.DictField(required=False, label=_("字段选项"), default={})


class CreateDataIDResource(Resource):

    """创建数据源ID"""

    class RequestSerializer(serializers.Serializer):

        data_name = serializers.CharField(required=True, label=_("数据源名称"))
        etl_config = serializers.CharField(required=True, label=_("清洗模板配置"))
        operator = serializers.CharField(required=True, label=_("操作者"))
        mq_cluster = serializers.IntegerField(required=False, label=_("数据源使用的消息集群"), default=None)
        data_description = serializers.CharField(required=False, label=_("数据源描述"))
        is_custom_source = serializers.BooleanField(required=False, label=_("是否用户自定义数据源"), default=True)
        source_label = serializers.CharField(required=True, label=_("数据源标签"))
        type_label = serializers.CharField(required=True, label=_("数据类型标签"))
        option = serializers.DictField(required=False, label=_("数据源配置项"))
        custom_label = serializers.CharField(required=False, label=_("自定义标签"))
        transfer_cluster_id = serializers.CharField(required=False, label=_("transfer集群ID"))

    def perform_request(self, validated_request_data):

        request = get_request()
        bk_app_code = get_app_code_by_request(request)

        validated_request_data["source_system"] = bk_app_code

        new_data_source = models.DataSource.create_data_source(**validated_request_data)

        return {"bk_data_id": new_data_source.bk_data_id}


class CreateResultTableResource(Resource):
    """创建结果表"""

    class RequestSerializer(serializers.Serializer):

        bk_data_id = serializers.IntegerField(required=True, label=_("数据源ID"))
        table_id = serializers.CharField(required=True, label=_("结果表ID"))
        table_name_zh = serializers.CharField(required=True, label=_("结果表中文名"))
        is_custom_table = serializers.BooleanField(required=True, label=_("是否用户自定义结果表"))
        schema_type = serializers.CharField(required=True, label=_("结果表字段配置方案"))
        operator = serializers.CharField(required=True, label=_("操作者"))
        default_storage = serializers.CharField(required=True, label=_("默认存储方案"))
        default_storage_config = serializers.DictField(required=False, label=_("默认存储参数"))
        field_list = FieldSerializer(many=True, required=False, label=_("字段列表"))
        bk_biz_id = serializers.IntegerField(required=False, label=_("结果表所属ID"), default=0)
        label = serializers.CharField(required=False, label=_("结果表标签"), default=models.Label.RESULT_TABLE_LABEL_OTHER)
        external_storage = serializers.JSONField(required=False, label=_("额外存储配置"), default=None)
        is_time_field_only = serializers.BooleanField(required=False, label=_("是否仅需要提供时间默认字段"), default=False)
        option = serializers.JSONField(required=False, label=_("结果表选项内容"), default=None)
        time_alias_name = serializers.CharField(required=False, label=_("时间节点"))
        time_option = serializers.DictField(required=False, label=_("时间字段选项配置"), default=None)

    def perform_request(self, request_data):

        new_result_table = models.ResultTable.create_result_table(is_sync_db=True, **request_data)

        return {"table_id": new_result_table.table_id}


class ListResultTableResource(Resource):
    """查询返回结果表"""

    class RequestSerializer(serializers.Serializer):
        datasource_type = serializers.CharField(required=False, label=_("过滤的结果表类型"), default=None)
        bk_biz_id = serializers.IntegerField(required=False, label=_("获取指定业务下的结果表信息"), default=None)
        is_public_include = serializers.IntegerField(required=False, label=_("是否包含全业务结果表"), default=None)
        is_config_by_user = serializers.BooleanField(required=False, label=_("是否需要包含非用户定义的结果表"), default=True)

    def perform_request(self, request_data):

        result_table_queryset = models.ResultTable.objects.filter(is_deleted=False)

        # 判断是否有结果表类型的过滤
        datasource_type = request_data["datasource_type"]
        if datasource_type is not None:
            result_table_queryset = result_table_queryset.filter(table_id__startswith="%s." % datasource_type)

        # 判断是否有全业务和单业务的过滤需求
        bk_biz_id = []
        if request_data["is_public_include"] is not None and request_data["is_public_include"]:
            bk_biz_id.append(0)

        if request_data["bk_biz_id"] is not None:
            bk_biz_id.append(request_data["bk_biz_id"])

        if len(bk_biz_id) != 0:
            result_table_queryset = result_table_queryset.filter(bk_biz_id__in=bk_biz_id)

        # 判断是否需要带上非用户字段的内容
        if request_data["is_config_by_user"]:
            result_table_queryset = result_table_queryset.filter(~Q(table_id__endswith="_cmdb_level"))

        result_list = models.ResultTable.batch_to_json(
            result_table_id_list=result_table_queryset.values_list("table_id", flat=True)
        )

        return result_list


class ModifyResultTableResource(Resource):
    """修改结果表"""

    class RequestSerializer(serializers.Serializer):

        table_id = serializers.CharField(required=True, label=_("结果表ID"))
        operator = serializers.CharField(required=True, label=_("操作者"))
        field_list = FieldSerializer(many=True, required=False, label=_("字段列表"), default=None)
        table_name_zh = serializers.CharField(required=False, label=_("结果表中文名"))
        default_storage = serializers.CharField(required=False, label=_("默认存储方案"))
        label = serializers.CharField(required=False, label=_("结果表标签"), default=None)
        external_storage = serializers.DictField(required=False, label=_("额外存储"), default=None)
        option = serializers.JSONField(required=False, label=_("结果表选项内容"), default=None)
        is_enable = serializers.BooleanField(required=False, label=_("是否启用结果表"), default=None)
        is_time_field_only = serializers.BooleanField(required=False, label=_("默认字段仅有time"), default=False)
        is_reserved_check = serializers.BooleanField(required=False, label=_("检查内置字段"), default=True)
        time_option = serializers.DictField(required=False, label=_("时间字段选项配置"), default=None, allow_null=True)

    def perform_request(self, request_data):

        table_id = request_data.pop("table_id")

        result_table = models.ResultTable.objects.get(table_id=table_id)
        result_table.modify(**request_data)

        # 刷新一波对象，防止存在缓存等情况
        result_table.refresh_from_db()

        # 判断是否修改了字段，而且是存在ES存储，如果是，需要重新创建一下当前的index
        query_set = models.ESStorage.objects.filter(table_id=table_id)
        if query_set.exists() and request_data["field_list"] is not None:
            storage = query_set[0]
            storage.update_index_and_aliases(ahead_time=0)

        return result_table.to_json()


class AccessBkDataByResultTableResource(Resource):
    """
    接入计算平台（根据结果表）
    """

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_("结果表ID"))

    def perform_request(self, validated_request_data):
        if not settings.IS_ACCESS_BK_DATA:
            return

        table_id = validated_request_data.pop("table_id")
        try:
            models.ResultTable.objects.get(table_id=table_id)
        except models.ResultTable.DoesNotExist:
            raise ValueError(_("结果表%s不存在，请确认后重试") % table_id)

        models.BkDataStorage.create_table(table_id)


class CreateDownSampleDataFlowResource(Resource):
    """
    创建统计节点（按指定的降采样频率）
    """

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_("结果表ID"))
        agg_interval = serializers.IntegerField(label=_("统计周期"), default=60)

    def perform_request(self, validated_request_data):
        if not settings.IS_ACCESS_BK_DATA:
            return

        table_id = validated_request_data.pop("table_id")
        agg_interval = validated_request_data.get("agg_interval") or 60
        try:
            models.ResultTable.objects.get(table_id=table_id)
        except models.ResultTable.DoesNotExist:
            raise ValueError(_("结果表%s不存在，请确认后重试") % table_id)

        from metadata.task import tasks

        tasks.create_statistics_data_flow.delay(table_id, agg_interval)


class QueryDataSourceResource(Resource):
    """查询数据源"""

    class RequestSerializer(serializers.Serializer):

        bk_data_id = serializers.IntegerField(required=False, label=_("数据源ID"), default=None)
        data_name = serializers.CharField(required=False, label=_("数据源名称"), default=None)

    def perform_request(self, request_data):

        if request_data["bk_data_id"] is not None:
            data_source = models.DataSource.objects.get(bk_data_id=request_data["bk_data_id"])
        elif request_data["data_name"] is not None:
            data_source = models.DataSource.objects.get(data_name=request_data["data_name"])

        else:
            raise ValueError(_("找不到请求参数，请确认后重试"))

        return data_source.to_json()


class ModifyDataSource(Resource):
    """修改数据源"""

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(required=True, label=_("操作者"))
        data_id = serializers.IntegerField(required=True, label=_("数据源ID"))
        data_name = serializers.CharField(required=False, label=_("数据源名称"), default=None)
        data_description = serializers.CharField(required=False, label=_("数据源描述"), default=None)
        option = serializers.DictField(required=False, label=_("数据源配置项"))
        is_enable = serializers.BooleanField(required=False, label=_("是否启用数据源"), default=None)

    def perform_request(self, request_data):

        try:
            data_source = models.DataSource.objects.get(bk_data_id=request_data["data_id"])

        except models.DataSource.DoesNotExist:
            raise ValueError(_("数据源不存在，请确认后重试"))

        data_source.update_config(
            operator=request_data["operator"],
            data_name=request_data["data_name"],
            data_description=request_data["data_description"],
            option=request_data.get("option"),
            is_enable=request_data["is_enable"],
        )
        return data_source.to_json()


class QueryResultTableSourceResource(Resource):
    """查询结果表"""

    class RequestSerializer(serializers.Serializer):

        table_id = serializers.CharField(required=True, label=_("结果表ID"))

    def perform_request(self, request_data):

        result_table = models.ResultTable.get_result_table(table_id=request_data["table_id"])
        return result_table.to_json()


class UpgradeResultTableResource(Resource):
    """结果表升级为全局业务表"""

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(required=True, label=_("操作者"))
        table_id_list = serializers.ListField(required=True, label=_("结果表ID列表"))

    def perform_request(self, request_data):

        result_table_list = []

        for table_id in request_data["table_id_list"]:
            result_table = models.ResultTable.get_result_table(table_id=table_id)
            result_table_list.append(result_table)

        with atomic(config.DATABASE_CONNECTION_NAME):
            for result_table in result_table_list:
                result_table.upgrade_result_table()

        return


class FullCmdbNodeInfoResource(Resource):
    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_("结果表ID"))

    def perform_request(self, validated_request_data):
        if not settings.IS_ACCESS_BK_DATA:
            return

        table_id = validated_request_data["table_id"]
        try:
            models.ResultTable.objects.get(table_id=table_id)
        except models.ResultTable.DoesNotExist:
            raise ValueError(_("结果表%s不存在，请确认后重试") % table_id)

        from metadata.task.tasks import create_full_cmdb_level_data_flow

        create_full_cmdb_level_data_flow.delay(table_id)


class CreateResultTableMetricSplitResource(Resource):
    """创建结果表的CMDB层级拆分记录"""

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(required=True, label=_("操作者"))
        table_id = serializers.CharField(required=True, label=_("结果表ID列表"))
        cmdb_level = serializers.CharField(required=True, label=_("CMDB拆分层级目标"))

    def perform_request(self, request_data):

        try:
            result_table = models.ResultTable.objects.get(table_id=request_data["table_id"], is_deleted=False)

        except models.DataSource.DoesNotExist:
            raise ValueError(_("结果表不存在，请确认后重试"))

        result = result_table.set_metric_split(cmdb_level=request_data["cmdb_level"], operator=request_data["operator"])

        return {"bk_data_id": result.bk_data_id, "table_id": result.target_table_id}


class CleanResultTableMetricSplitResource(Resource):
    """清理结果表的CMDB层级拆分记录"""

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(required=True, label=_("操作者"))
        table_id = serializers.CharField(required=True, label=_("结果表ID列表"))
        cmdb_level = serializers.CharField(required=True, label=_("CMDB拆分层级目标"))

    def perform_request(self, validated_request_data):

        try:
            result_table = models.ResultTable.objects.get(table_id=validated_request_data["table_id"], is_deleted=False)

        except models.DataSource.DoesNotExist:
            raise ValueError(_("结果表不存在，请确认后重试"))

        result_table.clean_metric_split(
            cmdb_level=validated_request_data["cmdb_level"], operator=validated_request_data["operator"]
        )

        return


class LabelResource(Resource):
    """返回所有的标签内容"""

    class RequestSerializer(serializers.Serializer):
        include_admin_only = serializers.BooleanField(required=True, label=_("是否展示管理员可见标签"))
        label_type = serializers.CharField(required=False, label=_("标签类型"), default=None)
        level = serializers.IntegerField(required=False, label=_("标签层级"), default=None)
        is_plain_text = serializers.BooleanField(required=False, label=_("是否明文展示"), default=False)

    def perform_request(self, validated_request_data):

        return models.Label.get_label_info(
            include_admin_only=validated_request_data["include_admin_only"],
            label_type=validated_request_data["label_type"],
            level=validated_request_data["level"],
        )


class GetResultTableStorageResult(Resource):
    """返回一个结果表指定存储的数据"""

    class RequestSerializer(serializers.Serializer):
        result_table_list = serializers.CharField(required=True, label=_("结果表列表"))
        storage_type = serializers.CharField(required=True, label=_("存储类型"))
        is_plain_text = serializers.BooleanField(required=False, label=_("是否明文显示链接信息"))

    def perform_request(self, validated_request_data):

        # 判断请求的存储类型是否有效
        storage_type = validated_request_data["storage_type"]
        if storage_type not in models.ResultTable.REAL_STORAGE_DICT:
            raise ValueError(_("请求存储类型暂不支持，请确认"))

        # 遍历判断所有的存储信息
        result_table_list = validated_request_data["result_table_list"].split(",")
        storage_class = models.ResultTable.REAL_STORAGE_DICT[storage_type]
        result = {}

        for result_table in result_table_list:
            try:
                storage_info = storage_class.objects.get(table_id=result_table)

            except storage_class.DoesNotExist:
                # raise ValueError(_("请求结果表[{}]不存在，请确认".format(result_table)))
                continue

            result[result_table] = storage_info.consul_config

            # 判断是否需要明文返回链接信息
            if not validated_request_data["is_plain_text"]:
                result[result_table]["auth_info"] = base64.b64encode(
                    json.dumps(result[result_table]["auth_info"]).encode("utf-8")
                )

        # 返回
        return result


class CreateClusterInfoResource(Resource):
    """创建存储集群资源"""

    class RequestSerializer(serializers.Serializer):
        cluster_name = serializers.CharField(required=True, label=_("集群名"))
        cluster_type = serializers.CharField(required=True, label=_("集群类型"))
        domain_name = serializers.CharField(required=True, label=_("集群域名"))
        port = serializers.IntegerField(required=True, label=_("集群端口"))
        description = serializers.CharField(required=False, label=_("集群描述数据"), default="")
        auth_info = serializers.JSONField(required=False, label=_("身份认证信息"), default={})
        version = serializers.CharField(required=False, label=_("版本信息"), default="")
        custom_option = serializers.CharField(required=False, label=_("自定义标签"), default="")
        schema = serializers.CharField(required=False, label=_("链接协议"), default="")
        is_ssl_verify = serializers.BooleanField(required=False, label=_("是否需要SSL验证"), default=False)
        operator = serializers.CharField(required=True, label=_("操作者"))

    def perform_request(self, validated_request_data):

        # 获取请求来源系统
        request = get_request()
        bk_app_code = get_app_code_by_request(request)
        validated_request_data["registered_system"] = bk_app_code

        # 获取配置的用户名和密码
        auth_info = validated_request_data.pop("auth_info", {})
        validated_request_data["username"] = auth_info.get("username", None)
        validated_request_data["password"] = auth_info.get("password", None)

        cluster = models.ClusterInfo.create_cluster(**validated_request_data)
        return cluster.cluster_id


class ModifyClusterInfoResource(Resource):
    """修改存储集群信息"""

    class RequestSerializer(serializers.Serializer):
        # 由于cluster_id和cluster_name是二选一，所以两个都配置未require
        cluster_id = serializers.IntegerField(required=False, label=_("存储集群ID"), default=None)
        cluster_name = serializers.CharField(required=False, label=_("存储集群名"), default=None)
        description = serializers.CharField(required=False, label=_("存储集群描述"), default=None)
        auth_info = serializers.JSONField(required=False, label=_("身份认证信息"), default={})
        custom_option = serializers.CharField(required=False, label=_("集群自定义标签"), default=None)
        schema = serializers.CharField(required=False, label=_("集群链接协议"), default=None)
        is_ssl_verify = serializers.BooleanField(required=False, label=_("是否需要强制SSL/TLS认证"), default=None)
        operator = serializers.CharField(required=True, label=_("操作者"))

    def perform_request(self, validated_request_data):

        request = get_request()
        bk_app_code = get_app_code_by_request(request)

        # 1. 判断是否存在cluster_id或者cluster_name
        cluster_id = validated_request_data.pop("cluster_id")
        cluster_name = validated_request_data.pop("cluster_name")

        if cluster_id is None and cluster_name is None:
            raise ValueError(_("需要至少提供集群ID或集群名"))

        # 2. 判断是否可以拿到一个唯一的cluster_info
        query_dict = {"cluster_id": cluster_id} if cluster_id is not None else {"cluster_name": cluster_name}
        try:
            cluster_info = models.ClusterInfo.objects.get(registered_system=bk_app_code, **query_dict)
        except models.ClusterInfo.DoesNotExist:
            raise ValueError(_("找不到指定的集群配置，请确认后重试"))

        # 3. 判断获取是否需要修改用户名和密码
        auth_info = validated_request_data.pop("auth_info", {})
        validated_request_data["username"] = auth_info.get("username", None)
        validated_request_data["password"] = auth_info.get("password", None)

        # 4. 触发修改内容
        cluster_info.modify(**validated_request_data)
        return cluster_info.consul_config


class QueryClusterInfoResource(Resource):
    class RequestSerializer(serializers.Serializer):
        cluster_id = serializers.IntegerField(required=False, label=_("存储集群ID"), default=None)
        cluster_name = serializers.CharField(required=False, label=_("存储集群名"), default=None)
        cluster_type = serializers.CharField(required=False, label=_("存储集群类型"), default=None)
        is_plain_text = serializers.BooleanField(required=False, label=_("是否需要明文显示登陆信息"), default=False)

    def perform_request(self, validated_request_data):

        request = get_request()
        bk_app_code = get_app_code_by_request(request)

        query_dict = {}
        if validated_request_data["cluster_id"] is not None:
            query_dict = {
                "cluster_id": validated_request_data["cluster_id"],
            }

        elif validated_request_data["cluster_name"] is not None:
            query_dict = {"cluster_name": validated_request_data["cluster_name"]}

        if validated_request_data["cluster_type"] is not None:
            query_dict["cluster_type"] = validated_request_data["cluster_type"]

        query_result = models.ClusterInfo.objects.filter(**query_dict)

        # 增加查询的系统信息
        query_result.filter(
            Q(registered_system=models.ClusterInfo.DEFAULT_REGISTERED_SYSTEM) | Q(registered_system=bk_app_code)
        )

        result_list = []
        is_plain_text = validated_request_data["is_plain_text"]

        for cluster_info in query_result:
            cluster_consul_config = cluster_info.consul_config

            # 如果不是明文的方式，需要进行base64编码
            if not is_plain_text:
                cluster_consul_config["auth_info"] = base64.b64encode(
                    json.dumps(cluster_consul_config["auth_info"]).encode("utf-8")
                )

            result_list.append(cluster_consul_config)

        return result_list


class QueryEventGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        label = serializers.CharField(required=False, label=_("事件分组标签"), default=None)
        event_group_name = serializers.CharField(required=False, label=_("事件分组名称"), default=None)
        bk_biz_id = serializers.CharField(required=False, label=_("业务ID"), default=None)

    def perform_request(self, validated_request_data):

        # 默认都是返回已经删除的内容
        query_set = models.EventGroup.objects.filter(is_delete=False)

        label = validated_request_data["label"]
        bk_biz_id = validated_request_data["bk_biz_id"]
        event_group_name = validated_request_data["event_group_name"]

        if label is not None:
            query_set = query_set.filter(label=label)

        if bk_biz_id is not None:
            query_set = query_set.filter(bk_biz_id=bk_biz_id)

        if event_group_name is not None:
            query_set = query_set.filter(event_group_name=event_group_name)

        return [event_group.to_json() for event_group in query_set]


class CreateEventGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_data_id = serializers.CharField(required=True, label=_("数据源ID"))
        bk_biz_id = serializers.CharField(required=True, label=_("业务ID"))
        event_group_name = serializers.CharField(required=True, label=_("事件分组名"))
        label = serializers.CharField(required=True, label=_("事件分组标签"))
        operator = serializers.CharField(required=True, label=_("创建者"))
        event_info_list = serializers.ListField(required=False, label=_("事件列表"), default=None)

    def perform_request(self, validated_request_data):

        # 默认都是返回已经删除的内容
        event_group = models.EventGroup.create_event_group(**validated_request_data)
        return event_group.to_json()


class ModifyEventGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        event_group_id = serializers.IntegerField(required=True, label=_("事件分组ID"))
        operator = serializers.CharField(required=True, label=_("修改者"))
        event_group_name = serializers.CharField(required=False, label=_("事件分组名"), default=None)
        label = serializers.CharField(required=False, label=_("事件分组标签"))
        event_info_list = serializers.ListField(required=False, label=_("事件列表"), default=None)
        is_enable = serializers.BooleanField(required=False, label=_("是否启用事件分组"), default=None)

    def perform_request(self, validated_request_data):

        try:
            event_group = models.EventGroup.objects.get(
                # 将事件分组的ID去掉
                event_group_id=validated_request_data.pop("event_group_id"),
                is_delete=False,
            )
        except models.EventGroup.DoesNotExist:
            raise ValueError(_("事件分组不存在，请确认后重试"))

        event_group.modify_event_group(**validated_request_data)
        event_group.refresh_from_db()

        return event_group.to_json()


class DeleteEventGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        event_group_id = serializers.IntegerField(required=True, label=_("事件分组ID"))
        operator = serializers.CharField(required=True, label=_("操作者"))

    def perform_request(self, validated_request_data):

        try:
            event_group = models.EventGroup.objects.get(
                # 将事件分组的ID去掉
                event_group_id=validated_request_data.pop("event_group_id"),
                is_delete=False,
            )
        except models.EventGroup.DoesNotExist:
            raise ValueError(_("事件分组不存在，请确认后重试"))

        event_group.delete_event_group(validated_request_data["operator"])
        return


class GetEventGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        event_group_id = serializers.IntegerField(required=True, label=_("事件分组ID"))
        with_result_table_info = serializers.BooleanField(required=False, label=_("是否需要带结果表信息"))

    def perform_request(self, validated_request_data):

        try:
            event_group = models.EventGroup.objects.get(
                # 将事件分组的ID去掉
                event_group_id=validated_request_data.pop("event_group_id"),
                is_delete=False,
            )
        except models.EventGroup.DoesNotExist:
            raise ValueError(_("事件分组不存在，请确认后重试"))

        if not validated_request_data["with_result_table_info"]:
            return event_group.to_json()

        result = event_group.to_json()

        # 查询增加结果表信息
        result_table = models.ResultTable.objects.get(table_id=event_group.table_id)
        result["shipper_list"] = [real_table.consul_config for real_table in result_table.real_storage_list]

        return result


class CreateTimeSeriesGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_data_id = serializers.CharField(required=True, label=_("数据源ID"))
        bk_biz_id = serializers.CharField(required=True, label=_("业务ID"))
        time_series_group_name = serializers.CharField(required=True, label=_("自定义时序分组名"))
        label = serializers.CharField(required=True, label=_("自定义时序分组标签"))
        operator = serializers.CharField(required=True, label=_("创建者"))
        metric_info_list = serializers.ListField(required=False, label=_("自定义时序metric列表"), default=None)
        table_id = serializers.CharField(required=False, label=_("结果表id"))

    def perform_request(self, validated_request_data):

        # 默认都是返回已经删除的内容
        time_series_group = models.TimeSeriesGroup.create_time_series_group(**validated_request_data)
        return time_series_group.to_json()


class ModifyTimeSeriesGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=True, label=_("自定义时序分组ID"))
        operator = serializers.CharField(required=True, label=_("修改者"))
        time_series_group_name = serializers.CharField(required=False, label=_("自定义时序分组名"), default=None)
        label = serializers.CharField(required=False, label=_("自定义时序分组标签"))
        field_list = serializers.ListField(required=False, label=_("字段列表"), default=None)
        is_enable = serializers.BooleanField(required=False, label=_("是否启用自定义分组"), default=None)

    def perform_request(self, validated_request_data):

        try:
            time_series_group = models.TimeSeriesGroup.objects.get(
                time_series_group_id=validated_request_data.pop("time_series_group_id"), is_delete=False
            )
        except models.TimeSeriesGroup.DoesNotExist:
            raise ValueError(_("自定义时序分组不存在，请确认后重试"))

        time_series_group.modify_time_series_group(**validated_request_data)
        time_series_group.refresh_from_db()

        return time_series_group.to_json()


class DeleteTimeSeriesGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=True, label=_("自定义分组ID"))
        operator = serializers.CharField(required=True, label=_("操作者"))

    def perform_request(self, validated_request_data):

        try:
            time_series_group = models.TimeSeriesGroup.objects.get(
                time_series_group_id=validated_request_data.pop("time_series_group_id"), is_delete=False
            )
        except models.TimeSeriesGroup.DoesNotExist:
            raise ValueError(_("自定义时序分组不存在，请确认后重试"))

        time_series_group.delete_time_series_group(validated_request_data["operator"])
        return


class GetTimeSeriesGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=True, label=_("自定义时序分组ID"))
        with_result_table_info = serializers.BooleanField(required=False, label=_("是否需要带结果表信息"))

    def perform_request(self, validated_request_data):

        try:
            time_series_group = models.TimeSeriesGroup.objects.get(
                time_series_group_id=validated_request_data.pop("time_series_group_id"), is_delete=False
            )
        except models.TimeSeriesGroup.DoesNotExist:
            raise ValueError(_("自定义时序分组不存在，请确认后重试"))

        if not validated_request_data["with_result_table_info"]:
            return time_series_group.to_json()

        result = time_series_group.to_json()

        # 查询增加结果表信息
        result_table = models.ResultTable.objects.get(table_id=time_series_group.table_id)
        result["shipper_list"] = [real_table.consul_config for real_table in result_table.real_storage_list]

        return result


class GetTimeSeriesMetricsResource(Resource):
    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_("结果表ID"))

    def perform_request(self, validated_request_data):

        table_id = validated_request_data.pop("table_id")
        try:
            time_series_group = models.TimeSeriesGroup.objects.get(table_id=table_id)
        except models.TimeSeriesGroup.DoesNotExist:
            raise ValueError(_("自定义时序分组不存在，请确认后重试"))

        return {"metric_info_list": time_series_group.get_metric_info_list()}


class QueryTimeSeriesGroupResource(Resource):
    class RequestSerializer(serializers.Serializer):
        label = serializers.CharField(required=False, label=_("自定义分组标签"), default=None)
        time_series_group_name = serializers.CharField(required=False, label=_("自定义分组名称"), default=None)
        bk_biz_id = serializers.CharField(required=False, label=_("业务ID"), default=None)

    def perform_request(self, validated_request_data):

        # 默认都是返回已经删除的内容
        query_set = models.TimeSeriesGroup.objects.filter(is_delete=False)

        label = validated_request_data["label"]
        bk_biz_id = validated_request_data["bk_biz_id"]
        time_series_group_name = validated_request_data["time_series_group_name"]

        if label is not None:
            query_set = query_set.filter(label=label)

        if bk_biz_id is not None:
            query_set = query_set.filter(bk_biz_id=bk_biz_id)

        if time_series_group_name is not None:
            query_set = query_set.filter(time_series_group_name=time_series_group_name)

        return [time_series_group.to_json() for time_series_group in query_set]


class QueryTagValuesResource(Resource):
    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_("结果表ID"))
        tag_name = serializers.CharField(required=True, label=_("dimension/tag名称"))

    def perform_request(self, validated_request_data):

        table_id = validated_request_data.pop("table_id")
        try:
            rt = models.ResultTable.objects.get(table_id=table_id)
        except models.TimeSeriesGroup.DoesNotExist:
            raise ValueError(_("结果表不存在，请确认后重试"))

        return {"tag_values": rt.get_tag_values(tag_name=validated_request_data["tag_name"])}


class ListTransferClusterResource(Resource):
    """
    获取所有transfer集群信息
    """

    def perform_request(self, validated_request_data):
        consul_client = consul.BKConsul()

        # 根据 service 和 tag 去过滤出 transfer 配置
        index, nodes = consul_client.health.service(service="bkmonitorv3", tag="transfer", passing=True)

        cluster_list = []
        for node in nodes:
            service_meta = node["Service"]["Meta"]
            if service_meta and "cluster_id" in service_meta:
                cluster_list.append({"cluster_id": service_meta["cluster_id"]})

        return cluster_list
