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
#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy
from rest_framework import serializers

from core.drf_resource import Resource
from bkmonitor.utils.cache import CacheType
from core.drf_resource import api
from core.drf_resource.contrib.nested_api import KernelAPIResource


class MetaDataAPIGWResource(KernelAPIResource):
    base_url_statement = None
    base_url = settings.MONITOR_API_BASE_URL or "%s/api/c/compapi/v2/monitor_v3/" % settings.BK_PAAS_INNER_HOST

    # 模块名
    module_name = "metadata_v3"

    @property
    def label(self):
        return self.__doc__


class GetLabelResource(MetaDataAPIGWResource):
    """
    获取分类标签（一二级标签）
    """

    action = "/metadata_list_label/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        # 标签分类，source_label, type_label or result_table_label
        label_type = serializers.CharField(required=False, label=_lazy("标签分类"))
        # 标签层级, 层级从1开始计算, 该配置只在label_type为result_table时生效
        level = serializers.IntegerField(required=False, label=_lazy("标签层级"))
        include_admin_only = serializers.BooleanField(required=False, label=_lazy("是否展示管理员可见标签"))


class CreateDataIdResource(MetaDataAPIGWResource):
    """
    创建监控数据源
    """

    action = "/metadata_create_data_id/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        data_name = serializers.CharField(required=True)
        etl_config = serializers.CharField(required=True, allow_blank=True)
        operator = serializers.CharField(required=True)
        mq_cluster = serializers.IntegerField(required=False)
        data_description = serializers.CharField(required=False)
        is_custom_source = serializers.BooleanField(required=False, default=True)
        source_label = serializers.CharField(required=True)
        type_label = serializers.CharField(required=True)
        option = serializers.DictField(required=False)


class CreateResultTableResource(MetaDataAPIGWResource):
    """
    创建监控结果表
    """

    action = "/metadata_create_result_table/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        bk_data_id = serializers.IntegerField(required=True)
        table_id = serializers.CharField(required=True)
        table_name_zh = serializers.CharField(required=True)
        is_custom_table = serializers.BooleanField(required=True)
        schema_type = serializers.ChoiceField(required=True, choices=["free", "fixed"])
        operator = serializers.CharField(required=True)
        default_storage = serializers.ChoiceField(required=True, choices=["influxdb"])
        default_storage_config = serializers.DictField(required=False)
        field_list = serializers.ListField(required=False)
        bk_biz_id = serializers.IntegerField(required=False)
        label = serializers.CharField(required=True)
        external_storage = serializers.DictField(required=False)
        option = serializers.DictField(required=False)


class ListResultTableResource(MetaDataAPIGWResource):
    """
    查询监控结果表
    """

    action = "/metadata_list_result_table/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
        datasource_type = serializers.CharField(required=False, label=_lazy("需要过滤的结果表类型，如 system"))
        is_public_include = serializers.BooleanField(required=False, label=_lazy("是否包含全业务结果表"))

        def validate_is_public_include(self, val):
            return 1 if val else 0


class ModifyResultTableResource(MetaDataAPIGWResource):
    """
    修改监控结果表
    """

    action = "/metadata_modify_result_table/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True)
        operator = serializers.CharField(required=True)
        field_list = serializers.ListField(required=False)
        table_name_zh = serializers.CharField(required=False)
        default_storage = serializers.ChoiceField(required=False, choices=["influxdb"])
        label = serializers.CharField(required=True)
        external_storage = serializers.DictField(required=False)
        option = serializers.DictField(required=False)
        is_time_field_only = serializers.BooleanField(required=False, default=False)
        is_reserved_check = serializers.BooleanField(required=False, default=True)
        time_option = serializers.DictField(required=False, default=None)


class GetDataIdResource(MetaDataAPIGWResource):
    """
    获取监控数据源具体信息
    """

    action = "/metadata_get_data_id/"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_data_id = serializers.IntegerField(required=False)
        data_name = serializers.CharField(required=False)


class GetResultTableResource(MetaDataAPIGWResource):
    """
    获取监控结果表具体信息
    """

    action = "/metadata_get_result_table/"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True)


class GetResultTableStorageResource(MetaDataAPIGWResource):
    """
    获取监控结果表具体信息
    """

    action = "/metadata_get_result_table_storage/"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        result_table_list = serializers.CharField(required=True)
        storage_type = serializers.CharField(required=True)


class GetTsDataResource(MetaDataAPIGWResource):
    """
    数据查询
    """

    action = "/get_ts_data/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        sql = serializers.CharField(required=True)


class GetEsDataResource(MetaDataAPIGWResource):
    """
    ES数据查询
    """

    action = "/get_es_data/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))
        query_body = serializers.DictField(required=True, label=_lazy("查询内容"))


class ModifyDataIdResource(MetaDataAPIGWResource):
    """
    修改dataid和dataname的关系
    """

    action = "/metadata_modify_data_id/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(required=True, label=_lazy("操作者"))
        data_name = serializers.CharField(required=True, label=_lazy("数据源名称"))
        data_id = serializers.IntegerField(required=True, label=_lazy("数据源ID"))


class CreateResultTableMetricSplitResource(MetaDataAPIGWResource):
    """
    创建一个结果表CMDB拆分
    """

    action = "/metadata_create_result_table_metric_split/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))
        cmdb_level = serializers.CharField(required=True, label=_lazy("MDB拆分层级名"))
        operator = serializers.CharField(required=True, label=_lazy("操作者"))


class ListMonitorResultTableResource(Resource):
    # todo to being legacy
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
        datasource_type = serializers.CharField(required=False, label=_lazy("需要过滤的结果表类型，如 system"))
        is_public_include = serializers.BooleanField(required=False, label=_lazy("是否包含全业务结果表"))

    def perform_request(self, validated_request_data):
        result_data = api.metadata.list_result_table(validated_request_data)
        validated_data = []
        for table in result_data:
            # 对非法table_id的数据进行过滤
            if len(table["table_id"].split(".")) != 2:
                continue

            for field in table["field_list"]:
                if field["tag"] != "metric":
                    continue

                if not field.get("alias_name"):
                    field["alias_name"] = field["description"]

                field["unit_conversion"] = 1.0

            validated_data.append(table)
        return validated_data


class CreateEventGroupResource(MetaDataAPIGWResource):
    """
    创建事件分组
    """

    action = "/metadata_create_event_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        bk_data_id = serializers.IntegerField(label=_lazy("数据ID"))
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        event_group_name = serializers.CharField(label=_lazy("事件分组名"))
        label = serializers.CharField(label=_lazy("分组标签"))
        event_info_list = serializers.ListField(required=False, label=_lazy("事件列表"))


class ModifyEventGroupResource(MetaDataAPIGWResource):
    """
    修改事件分组
    """

    action = "/metadata_modify_event_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        event_group_id = serializers.IntegerField(label=_lazy("事件分组ID"))
        event_group_name = serializers.CharField(required=False, label=_lazy("事件分组名"))
        label = serializers.CharField(required=False, label=_lazy("分组标签"))
        event_info_list = serializers.ListField(required=False, label=_lazy("事件列表"), allow_empty=True)
        is_enable = serializers.BooleanField(required=False, label=_lazy("是否启用"))


class DeleteEventGroupResource(MetaDataAPIGWResource):
    """
    删除事件分组
    """

    action = "/metadata_delete_event_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        event_group_id = serializers.IntegerField(label=_lazy("事件分组ID"))


class GetEventGroupResource(MetaDataAPIGWResource):
    """
    获取事件分组
    """

    action = "/metadata_get_event_group/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        event_group_id = serializers.IntegerField(label=_lazy("事件分组ID"))
        with_result_table_info = serializers.BooleanField(label=_lazy("是否返回数据源信息"), required=False)


class QueryEventGroupResource(MetaDataAPIGWResource):
    """
    查询事件分组
    """

    action = "/metadata_query_event_group/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
        label = serializers.CharField(required=False, label=_lazy("分组标签"))
        event_group_name = serializers.CharField(required=False, label=_lazy("分组名称"))


class CreateTimeSeriesGroupResource(MetaDataAPIGWResource):
    """
    创建自定义时序分组
    """

    action = "/metadata_create_time_series_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        bk_data_id = serializers.IntegerField(label=_lazy("数据ID"))
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        time_series_group_name = serializers.CharField(label=_lazy("自定义时序分组名"))
        label = serializers.CharField(label=_lazy("分组标签"))
        metric_info_list = serializers.ListField(required=False, label=_lazy("Metric列表"))
        table_id = serializers.CharField(required=False, label=_lazy("结果表id"))


class ModifyTimeSeriesGroupResource(MetaDataAPIGWResource):
    """
    修改自定义时序分组
    """

    action = "/metadata_modify_time_series_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        time_series_group_id = serializers.IntegerField(label=_lazy("自定义时序分组ID"))
        time_series_group_name = serializers.CharField(required=False, label=_lazy("自定义时序分组名"))
        label = serializers.CharField(required=False, label=_lazy("分组标签"))
        field_list = serializers.ListField(required=False, label=_lazy("自定义时序列表"), allow_empty=True)
        is_enable = serializers.BooleanField(required=False, label=_lazy("是否启用"))


class DeleteTimeSeriesGroupResource(MetaDataAPIGWResource):
    """
    删除自定义时序分组
    """

    action = "/metadata_delete_time_series_group/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        operator = serializers.CharField(allow_blank=True, label=_lazy("操作者"))
        time_series_group_id = serializers.IntegerField(label=_lazy("自定义时序分组ID"))


class GetTimeSeriesGroupResource(MetaDataAPIGWResource):
    """
    获取自定义时序分组
    """

    action = "/metadata_get_time_series_group/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(label=_lazy("自定义时序分组ID"))
        with_result_table_info = serializers.BooleanField(label=_lazy("是否返回数据源信息"), required=False)


class QueryTimeSeriesGroupResource(MetaDataAPIGWResource):
    """
    查询自定义时序分组
    """

    action = "/metadata_query_time_series_group/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
        label = serializers.CharField(required=False, label=_lazy("分组标签"))
        time_series_group_name = serializers.CharField(required=False, label=_lazy("分组名称"))


class QueryTagValuesResource(MetaDataAPIGWResource):
    """
    查询指定tag/dimension valuestag/dimension values
    查询自定义时序分组
    """

    action = "/metadata_query_tag_values/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=False, label=_lazy("结果表ID"))
        tag_name = serializers.CharField(required=False, label=_lazy("TAG名称"))


class QueryClusterInfoResource(MetaDataAPIGWResource):
    """
    查询集群信息
    """

    action = "/metadata_get_cluster_info/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        cluster_id = serializers.IntegerField(required=False, label=_lazy("存储集群ID"), default=None)
        cluster_name = serializers.CharField(required=False, label=_lazy("存储集群名"), default=None)
        cluster_type = serializers.CharField(required=False, label=_lazy("存储集群类型"), default=None)
        is_plain_text = serializers.BooleanField(required=False, label=_lazy("是否需要明文显示登陆信息"), default=False)


class AccessBkDataByResultTable(MetaDataAPIGWResource):
    """
    创建降采样dataflow
    """

    action = "/access_bk_data_by_result_table/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))  # eg: system.load


class CreateDownSampleDataFlow(MetaDataAPIGWResource):
    """
    创建降采样dataflow
    """

    action = "/metadata_create_down_sample_data_flow/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        agg_interval = serializers.IntegerField(required=True)
        table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))  # eg: system.load


class FullCmdbNodeInfo(MetaDataAPIGWResource):
    """
    补充CMDB节点信息（需要保证表中有bk_target_ip、bk_target_cloud_id两个字段）
    """

    action = "/full_cmdb_node_info/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))  # eg: system.load
