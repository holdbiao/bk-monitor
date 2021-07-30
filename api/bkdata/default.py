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


import abc

import six
from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy
from rest_framework import serializers

from bkmonitor.utils.cache import CacheType
from bkmonitor.utils.request import get_request
from core.drf_resource import APIResource


class BkDataAPIGWResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url_statement = None
    base_url = settings.BKDATA_API_BASE_URL or "%s/api/c/compapi/data/" % settings.BK_PAAS_INNER_HOST

    # 模块名
    module_name = "bkdata"

    @property
    def label(self):
        return self.__doc__

    def get_request_url(self, validated_request_data):
        return super(BkDataAPIGWResource, self).get_request_url(validated_request_data).format(**validated_request_data)

    def perform_request(self, params):
        try:
            params["_origin_user"] = get_request().user.username
        except Exception:
            pass

        self.bk_username = settings.COMMON_USERNAME
        return super(BkDataAPIGWResource, self).perform_request(params)


class ListResultTableResource(BkDataAPIGWResource):
    """
    查询监控结果表
    """

    action = "/v3/meta/result_tables/"
    method = "GET"
    backend_cache_type = CacheType.METADATA

    class RequestSerializer(serializers.Serializer):
        related = serializers.ListField(required=False, default=["fields", "storages"], label=_lazy("查询条件"))
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))


class GetResultTableResource(BkDataAPIGWResource):
    """
    查询指定结果表
    """

    action = "/v3/meta/result_tables/{result_table_id}"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        result_table_id = serializers.CharField(required=True, label=_lazy("结果表名称"))
        related = serializers.ListField(required=False, default=["fields", "storages"], label=_lazy("查询条件"))

    def get_request_url(self, validated_request_data):
        return (
            super(GetResultTableResource, self).get_request_url(validated_request_data).format(**validated_request_data)
        )


class QueryDataResource(BkDataAPIGWResource):
    """
    查询数据
    """

    action = "/v3/dataquery/query/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        sql = serializers.CharField(required=True, label=_lazy("查询SQL语句"))
        prefer_storage = serializers.CharField(required=True, label=_lazy("优先使用存储类型"), allow_blank=True)
        bkdata_authentication_method = serializers.CharField(required=False, default="user")


class CommonRequestSerializer(serializers.Serializer):
    bkdata_authentication_method = serializers.CharField(default="user", label=_lazy("鉴权模式，默认 user 即可"))
    appenv = serializers.CharField(default="ieod", label=_lazy("环境，默认 ieod 即可"))


class DataAccessAPIResource(six.with_metaclass(abc.ABCMeta, BkDataAPIGWResource)):
    """
    重写BkDataAPIGWResource，对用户的处理
    """

    def perform_request(self, params):
        try:
            params["_origin_user"] = get_request().user.username
        except Exception:
            pass

        self.bk_username = settings.BK_DATA_PROJECT_MAINTAINER
        return super(BkDataAPIGWResource, self).perform_request(params)


####################################
#          auth 模型相关接口         #
####################################
class AuthTickets(BkDataAPIGWResource):
    """
    授权接口(需要以用户的身份来请求授权)
    """

    action = "/v3/auth/tickets/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        class PermissionsSerializer(serializers.Serializer):
            class ScopeSerializer(serializers.Serializer):
                result_table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))

            subject_id = serializers.CharField(required=True, label=_lazy("对象ID"))
            subject_name = serializers.CharField(required=True, label=_lazy("对象名称"))
            subject_class = serializers.CharField(required=True, label=_lazy("对象类型"))
            action = serializers.CharField(required=True, label=_lazy("授权动作"))
            object_class = serializers.CharField(required=True, label=_lazy("目标类型"))
            scope = ScopeSerializer(required=True, label=_lazy("目标"))

        ticket_type = serializers.CharField(required=True, label=_lazy("凭证类型"))
        permissions = serializers.ListField(required=True, child=PermissionsSerializer(), label=_lazy("权限列表"))
        reason = serializers.CharField(default="", label=_lazy("授权原因"))

    def perform_request(self, params):
        return super(BkDataAPIGWResource, self).perform_request(params)


class AuthProjectsDataCheck(DataAccessAPIResource):
    """
    检查项目是否有结果表权限
    """

    action = "/v3/auth/projects/{project_id}/data/check/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        project_id = serializers.IntegerField(required=True, label=_lazy("计算平台项目"))
        result_table_id = serializers.CharField(required=True, label=_lazy("结果表名称"))
        action_id = serializers.CharField(default="result_table.query_data", label=_lazy("动作方式"))


####################################
#          aiops 模型相关接口        #
####################################
class GetModelReleaseInfo(DataAccessAPIResource):
    """
    获取模型发布信息
    """

    action = "/v3/aiops/models/{model_id}/release/"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        model_id = serializers.CharField(required=True, label=_lazy("数据模型ID"))
        project_id = serializers.IntegerField(required=True, label=_lazy("计算平台项目"))
        extra_filters = serializers.CharField(required=True, label=_lazy("额外过滤条件(json字符串格式)"))


####################################
#          model 模型相关接口        #
####################################
class QueryReleaseModelList(DataAccessAPIResource):
    """
    获取已发布的模型列表
    """

    action = "/v3/model/serving/models/"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        project_id = serializers.IntegerField(required=True, label=_lazy("计算平台项目"))
        scene_name = serializers.ChoiceField(
            default="custom", choices=["custom", "timeseries_anomaly_detect"], label=_lazy("模型场景")
        )


class GetReleaseModelInfo(DataAccessAPIResource):
    """
    获取模型详情信息
    """

    action = "/v3/model/releases/{model_release_id}"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        model_release_id = serializers.IntegerField(required=True, label=_lazy("发布模型ID"))


####################################
#          数据接入 相关接口          #
####################################
class AccessDeployPlan(DataAccessAPIResource):
    """
    提交接入部署计划(数据源接入)
    """

    action = "/v3/access/deploy_plan/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        class AccessRawDataSerializer(serializers.Serializer):
            raw_data_name = serializers.CharField(required=True, label=_lazy("数据源名称，数据英文标识"))
            raw_data_alias = serializers.CharField(required=True, label=_lazy("数据别名（中文名）"))
            maintainer = serializers.CharField(required=True, label=_lazy("数据维护者"))
            data_source = serializers.CharField(required=True, label=_lazy("数据接入方式"))
            data_encoding = serializers.CharField(required=True, label=_lazy("字符集编码"))
            sensitivity = serializers.CharField(required=True, label=_lazy("数据敏感度"))
            description = serializers.CharField(required=False, label=_lazy("数据源描述"))
            tags = serializers.ListField(required=False, label=_lazy("数据标签"))
            data_source_tags = serializers.ListField(required=False, label=_lazy("数据源标签"))

        class AccessConfInfoSerializer(serializers.Serializer):
            class CollectionModelSerializer(serializers.Serializer):
                collection_type = serializers.CharField(required=True, label=_lazy("接入方式"))
                start_at = serializers.IntegerField(default=1, label=_lazy("开始接入时位置"))
                period = serializers.CharField(required=True, label=_lazy("采集周期"))

            class ConfResourceSerializer(serializers.Serializer):
                class KafkaConfScopeSerializer(serializers.Serializer):
                    master = serializers.CharField(required=True, label=_lazy("kafka的broker地址"))
                    group = serializers.CharField(required=True, label=_lazy("消费者组"))
                    topic = serializers.CharField(required=True, label=_lazy("消费topic"))
                    tasks = serializers.CharField(required=True, label=_lazy("最大并发度"))
                    use_sasl = serializers.BooleanField(required=True, label=_lazy("是否加密"))
                    security_protocol = serializers.CharField(required=False, label=_lazy("安全协议"))
                    sasl_mechanism = serializers.CharField(required=False, label=_lazy("SASL机制"))
                    user = serializers.CharField(required=False, allow_blank=True, label=_lazy("用户名"))
                    password = serializers.CharField(required=False, allow_blank=True, label=_lazy("密码"))

                type = serializers.CharField(required=True, label=_lazy("数据源类型"))
                # 这里的scope配置，固定只写了kafka的配置，如果有其他接入方式，需要增加对应的serializer
                scope = serializers.ListField(required=True, child=KafkaConfScopeSerializer(), label=_lazy("接入对象"))

            collection_model = CollectionModelSerializer(required=True, label=_lazy("数据采集接入方式配置"))
            resource = ConfResourceSerializer(required=True, label=_lazy("接入对象资源"))

        data_scenario = serializers.CharField(required=True, label=_lazy("接入场景"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        access_raw_data = AccessRawDataSerializer(required=True, label=_lazy("接入源数据信息"))
        access_conf_info = AccessConfInfoSerializer(required=True, label=_lazy("接入配置信息"))
        description = serializers.CharField(required=False, allow_blank=True, label=_lazy("接入数据备注"))


class DatabusCleans(DataAccessAPIResource):
    """
    接入数据清洗
    """

    action = "/v3/databus/cleans/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        class FieldSerializer(serializers.Serializer):
            field_name = serializers.CharField(required=True, label=_lazy("字段英文标识"))
            field_type = serializers.CharField(required=True, label=_lazy("字段类型"))
            field_alias = serializers.CharField(required=True, label=_lazy("字段别名"))
            is_dimension = serializers.BooleanField(required=True, label=_lazy("是否为维度字段"))
            field_index = serializers.IntegerField(required=True, label=_lazy("字段顺序索引"))

        raw_data_id = serializers.CharField(required=True, label=_lazy("数据接入源ID"))
        json_config = serializers.CharField(required=True, label=_lazy("数据清洗配置，json格式"))
        pe_config = serializers.CharField(default="", allow_blank=True, label=_lazy("清洗规则的pe配置"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        clean_config_name = serializers.CharField(required=True, label=_lazy("清洗配置名称"))
        result_table_name = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表英文标识"))
        result_table_name_alias = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表别名"))
        fields = serializers.ListField(required=True, child=FieldSerializer(), label=_lazy("输出字段列表"))
        description = serializers.CharField(default="", label=_lazy("清洗配置描述信息"))


class UpdateDatabusCleans(DataAccessAPIResource):
    """
    接入数据清洗
    """

    action = "/v3/databus/cleans/{processing_id}/"
    method = "PUT"

    class RequestSerializer(CommonRequestSerializer):
        class FieldSerializer(serializers.Serializer):
            field_name = serializers.CharField(required=True, label=_lazy("字段英文标识"))
            field_type = serializers.CharField(required=True, label=_lazy("字段类型"))
            field_alias = serializers.CharField(required=True, label=_lazy("字段别名"))
            is_dimension = serializers.BooleanField(required=True, label=_lazy("是否为维度字段"))
            field_index = serializers.IntegerField(required=True, label=_lazy("字段顺序索引"))

        processing_id = serializers.CharField(required=True, label=_lazy("清洗配置ID"))
        raw_data_id = serializers.CharField(required=True, label=_lazy("数据接入源ID"))
        json_config = serializers.CharField(required=True, label=_lazy("数据清洗配置，json格式"))
        pe_config = serializers.CharField(default="", allow_blank=True, label=_lazy("清洗规则的pe配置"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        clean_config_name = serializers.CharField(required=True, label=_lazy("清洗配置名称"))
        result_table_name = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表英文标识"))
        result_table_name_alias = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表别名"))
        fields = serializers.ListField(required=True, child=FieldSerializer(), label=_lazy("输出字段列表"))
        description = serializers.CharField(default="", label=_lazy("清洗配置描述信息"))


class StartDatabusCleans(DataAccessAPIResource):
    """
    启动清洗配置
    """

    action = "/v3/databus/tasks/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        result_table_id = serializers.CharField(required=True, label=_lazy("清洗结果表名称"))
        storages = serializers.ListField(default=["kafka"], label=_lazy("分发任务的存储列表"))


class StopDatabusCleans(DataAccessAPIResource):
    """
    启动清洗配置
    """

    action = "/v3/databus/tasks/{result_table_id}/"
    method = "DELETE"

    class RequestSerializer(CommonRequestSerializer):
        result_table_id = serializers.CharField(required=True, label=_lazy("清洗结果表名称"))
        storages = serializers.ListField(default=["kafka"], label=_lazy("分发任务的存储列表"))


class CreateDataStorages(DataAccessAPIResource):
    """
    创建数据入库
    """

    action = "/v3/databus/data_storages/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        class FieldSerializer(serializers.Serializer):
            physical_field = serializers.CharField(required=True, label=_lazy("物理表字段"))
            field_name = serializers.CharField(required=True, label=_lazy("字段英文标识"))
            field_type = serializers.CharField(required=True, label=_lazy("字段类型"))
            field_alias = serializers.CharField(required=True, label=_lazy("字段别名"))
            is_dimension = serializers.BooleanField(required=True, label=_lazy("是否为维度字段"))
            field_index = serializers.IntegerField(required=True, label=_lazy("字段顺序索引"))

        raw_data_id = serializers.CharField(required=True, label=_lazy("数据接入源ID"))
        data_type = serializers.CharField(required=True, label=_lazy("数据源类型"))
        result_table_name = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表英文标识"))
        result_table_name_alias = serializers.CharField(required=True, label=_lazy("清洗配置输出的结果表别名"))
        fields = serializers.ListField(required=True, child=FieldSerializer(), label=_lazy("输出字段列表"))
        storage_type = serializers.CharField(required=True, label=_lazy("存储类型"))
        storage_cluster = serializers.CharField(required=True, label=_lazy("存储集群"))
        expires = serializers.CharField(required=True, label=_lazy("过期时间"))


####################################
#          DataFlow 相关接口         #
####################################
class GetDataFlowList(DataAccessAPIResource):
    """
    获取DataFlow列表信息
    """

    action = "/v3/dataflow/flow/flows"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        project_id = serializers.IntegerField(required=True, label=_lazy("计算平台的项目ID"))


class GetDataFlow(DataAccessAPIResource):
    """
    获取DataFlow信息
    """

    action = "/v3/dataflow/flow/flows/{flow_id}"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))


class GetDataFlowGraph(DataAccessAPIResource):
    """
    获取DataFlow里的画布信息，即画布中的节点信息
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/graph"
    method = "GET"

    class RequestSerializer(CommonRequestSerializer):
        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))


class CreateDataFlow(DataAccessAPIResource):
    """
    创建DataFlow
    """

    action = "/v3/dataflow/flow/flows/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        project_id = serializers.IntegerField(required=True, label=_lazy("计算平台的项目ID"))
        flow_name = serializers.CharField(required=True, label=_lazy("DataFlow名称"))


class AddDataFlowNode(DataAccessAPIResource):
    """
    添加DataFlow节点
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/nodes/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        class FromLinksSerializer(serializers.Serializer):
            class SourceSerializer(serializers.Serializer):
                node_id = serializers.IntegerField(required=True, label=_lazy("上游节点ID"))
                id = serializers.CharField(required=True, label=_lazy("节点ID"))
                arrow = serializers.CharField(required=True, label=_lazy("连线箭头方向"))

            class TargetSerializer(serializers.Serializer):
                id = serializers.CharField(required=True, label=_lazy("节点ID"))
                arrow = serializers.CharField(required=True, label=_lazy("连线箭头方向"))

            source = SourceSerializer(required=True, label=_lazy("连线的上游节点信息"))
            target = TargetSerializer(required=True, label=_lazy("连线的下游节点信息"))

        class ConfigSerializer(serializers.Serializer):
            from_result_table_ids = serializers.ListField(required=True, label=_lazy("来源结果表list"))
            name = serializers.CharField(required=True, label=_lazy("节点名称"))

            # for stream_source 实时数据源
            bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
            result_table_id = serializers.CharField(required=False, label=_lazy("输出结果表名称"))

            # for realtime 实时计算节点
            # 重复字段
            # bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
            table_name = serializers.CharField(required=False, label=_lazy("输出表名(英文标识)"))
            output_name = serializers.CharField(required=False, label=_lazy("输出表名（中文名）"))
            window_type = serializers.CharField(required=False, label=_lazy("窗口类型"))
            # window_time = serializers.IntegerField(required=False, label=_lazy("窗口类型"))
            waiting_time = serializers.IntegerField(required=False, label=_lazy("等待时间"))
            count_freq = serializers.IntegerField(required=False, label=_lazy("统计频率"))
            sql = serializers.CharField(required=False, label=_lazy("统计sql语句"))

            # for tspider 存储节点
            # 重复字段
            # bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))
            # result_table_id = serializers.CharField(required=False, label=_lazy("输出结果表名称"))
            expires = serializers.IntegerField(required=False, label=_lazy("数据保存周期"))
            indexed_fields = serializers.ListField(default=list, label=_lazy("索引字段"))
            cluster = serializers.CharField(required=False, label=_lazy("存储集群"))

            # for model flow
            model_id = serializers.CharField(required=False, label=_lazy("数据模型ID"))
            model_release_id = serializers.IntegerField(required=False, label=_lazy("发布模型ID"))
            serving_mode = serializers.CharField(required=False, label=_lazy("serving_mode"))
            model_extra_config = serializers.DictField(required=False, label=_lazy("模型参数配置"))
            schedule_config = serializers.DictField(required=False, label=_lazy("模型调度配置"))
            input_config = serializers.DictField(required=False, label=_lazy("模型输入配置"))
            output_config = serializers.DictField(required=False, label=_lazy("模型输出配置"))
            sample_feedback_config = serializers.DictField(required=False, label=_lazy("sample_feedback_config"))
            upgrade_config = serializers.DictField(required=False, label=_lazy("upgrade_config"))

        class FrontendInfoSerializer(serializers.Serializer):
            x = serializers.IntegerField(default=0, label=_lazy("DataFlow画布上显示的x轴坐标"))
            y = serializers.IntegerField(default=0, label=_lazy("DataFlow画布上显示的y轴坐标"))

        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))
        from_links = serializers.ListField(required=True, child=FromLinksSerializer(), label=_lazy("与上游节点的连线信息"))
        node_type = serializers.CharField(required=True, label=_lazy("节点类型"))
        config = ConfigSerializer(required=True, label=_lazy("节点配置"))
        frontend_info = FrontendInfoSerializer(required=True, label=_lazy("DataFlow画布上的位置信息"))


class UpdateDataFlowNode(DataAccessAPIResource):
    """
    更新DataFlow节点
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/nodes/{node_id}"
    method = "PUT"

    class RequestSerializer(AddDataFlowNode.RequestSerializer):
        node_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的节点ID"))


class StartDataFlow(DataAccessAPIResource):
    """
    启动DataFlow
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/start/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))
        consuming_mode = serializers.CharField(default="continue", label=_lazy("数据处理模式"))
        cluster_group = serializers.CharField(default="default", label=_lazy("计算集群组"))


class StopDataFlow(DataAccessAPIResource):
    """
    停止DataFlow
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/stop/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))


class RestartDataFlow(DataAccessAPIResource):
    """
    重启DataFlow
    """

    action = "/v3/dataflow/flow/flows/{flow_id}/restart/"
    method = "POST"

    class RequestSerializer(CommonRequestSerializer):
        flow_id = serializers.IntegerField(required=True, label=_lazy("DataFlow的ID"))
        consuming_mode = serializers.CharField(default="continue", label=_lazy("数据处理模式"))
        cluster_group = serializers.CharField(default="default", label=_lazy("计算集群组"))
