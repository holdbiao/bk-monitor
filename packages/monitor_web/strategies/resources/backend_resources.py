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

from django.utils.translation import ugettext as _

from bkmonitor.models import StrategyLabel
from bkmonitor.strategy.new_strategy import Strategy
from constants.data_source import DataSourceLabel, DataTypeLabel
from core.drf_resource.base import Resource
from bkmonitor.utils.time_tools import strftime_local
from bkmonitor.views import serializers
from core.unit import load_unit
from monitor_web.strategies.constant import DETECT_ALGORITHM_CHOICES
from monitor_web.strategies.serializers import (
    handel_target,
    is_validate_target,
    validate_action_config,
    validate_agg_condition_msg,
    validate_algorithm_config_msg,
    validate_algorithm_msg,
    validate_no_data_config_msg,
    validate_recovery_config_msg,
    validate_trigger_config_msg,
)
from .frontend_resources import StrategyConfigListResource
from ...models import CustomEventGroup


class BackendStrategyConfigListResource(StrategyConfigListResource):
    """
    批量获取策略列表详情
    """

    @staticmethod
    def handle_value_time(value):
        if value.get("create_time"):
            value["create_time"] = strftime_local(value["create_time"])
        if value.get("update_time"):
            value["update_time"] = strftime_local(value["update_time"])
        return value

    def perform_request(self, params):
        strategy_query = self.filter_all_strategies(params)

        # 分页
        page = params.get("page", 0)
        page_size = params.get("page_size", 0)
        if all([page, page_size]):
            # fmt: off
            strategy_query = strategy_query[(page - 1) * page_size: page * page_size]
            # fmt: on

        strategies = Strategy.from_models(strategy_query)

        configs = [strategy.to_dict_v1(config_type="backend") for strategy in strategies]
        Strategy.fill_notice_group(configs)
        return configs


class BackendStrategyConfigResource(Resource):
    class RequestSerializer(serializers.Serializer):
        class ItemListSerializer(serializers.Serializer):
            class AlgorithmSerializers(serializers.Serializer):
                class TriggerConfigSerializers(serializers.Serializer):
                    count = serializers.IntegerField(required=True, label=_("触发次数"))
                    check_window = serializers.IntegerField(required=True, label=_("检测周期"))

                class RecoveryConfigSerializers(serializers.Serializer):
                    check_window = serializers.IntegerField(required=True, label=_("检测周期"))

                trigger_config = TriggerConfigSerializers()
                algorithm_type = serializers.ChoiceField(
                    required=False, choices=DETECT_ALGORITHM_CHOICES, label=_("检测算法")
                )
                algorithm_unit = serializers.CharField(required=False, allow_blank=True, label=_("算法单位"))
                recovery_config = RecoveryConfigSerializers()
                message_template = serializers.CharField(required=False, allow_blank=True, label=_("通知模板"))
                algorithm_config = serializers.JSONField(required=False, label=_("检测算法配置"))
                level = serializers.IntegerField(required=True, label=_("告警级别"))

                def validate_algorithm_config(self, value):
                    return validate_algorithm_config_msg(value)

                def validate_trigger_config(self, value):
                    return validate_trigger_config_msg(value)

                def validate_recovery_config(self, value):
                    return validate_recovery_config_msg(value)

            class RtQueryConfigSerializers(serializers.Serializer):
                metric_field = serializers.CharField(required=False, label=_("监控指标别名"))
                unit_conversion = serializers.FloatField(required=False, default=1.0, label=_("单位换算"))
                unit = serializers.CharField(required=False, allow_blank=True, label=_("单位"))
                extend_fields = serializers.JSONField(required=False, allow_null=True, label=_("扩展字段"))
                agg_dimension = serializers.ListField(required=False, allow_empty=True, label=_("聚合维度"))
                result_table_id = serializers.CharField(required=False, allow_blank=True, label=_("表名"))
                agg_method = serializers.CharField(required=False, allow_blank=True, label=_("聚合算法"))
                agg_interval = serializers.CharField(required=False, allow_blank=True, label=_("聚合周期"))
                agg_condition = serializers.ListField(required=False, allow_empty=True, label=_("聚合条件"))
                rule = serializers.CharField(required=False, allow_blank=True, label=_("组合方式"))
                keywords = serializers.CharField(required=False, allow_blank=True, label=_("组合字段"))
                keywords_query_string = serializers.CharField(required=False, allow_blank=True, label=_("关键字查询条件"))
                bk_event_group_id = serializers.IntegerField(required=False, label=_("自定义事件分组ID"))
                custom_event_id = serializers.IntegerField(required=False, label=_("自定义事件分组ID"))

                def validate_extend_fields(self, value):
                    if not value:
                        return {}
                    return value

            id = serializers.IntegerField(required=False, label=_("item_id"))
            name = serializers.CharField(required=True, label=_("监控指标别名"))
            # 数据类型标签，例如：时序数据(time_series)，事件数据(event)，日志数据(log)
            data_type_label = serializers.CharField(required=True, label=_("数据类型标签"))
            metric_id = serializers.CharField(required=True, label=_("指标标识"))
            # 数据来源标签，例如：计算平台(bk_data)，监控采集器(bk_monitor_collector)
            data_source_label = serializers.CharField(required=True, label=_("数据来源标签"))
            algorithm_list = AlgorithmSerializers(required=True, many=True, label=_(""))
            no_data_config = serializers.DictField(required=True, label=_("无数据告警配置"))
            rt_query_config = RtQueryConfigSerializers(required=True, allow_null=True, label=_("查询表"))
            target = serializers.ListField(default=[[]], label=_("策略目标"))
            result_table_id = serializers.CharField(required=False, label=_("表名（用于GSE进程事件默认创建）"))

            def validate_no_data_config(self, value):
                return validate_no_data_config_msg(value)

            def validate_agg_condition(self, value):
                return validate_agg_condition_msg(value)

            def validate_algorithm_list(self, value):
                return validate_algorithm_msg(value)

        class ActionListSerializer(serializers.Serializer):
            class NoticeTemplateSerializer(serializers.Serializer):
                anomaly_template = serializers.CharField(required=False, allow_blank=True, label=_("告警发生通知模板"))
                recovery_template = serializers.CharField(required=False, allow_blank=True, label=_("告警恢复通知模板"))

            id = serializers.IntegerField(required=False, label=_("action_id"))
            action_type = serializers.CharField(required=False, default="notice", label=_("触发动作"))
            config = serializers.DictField(required=True, label=_("告警相关配置"))
            notice_group_list = serializers.ListField(default=[], label=_("通知组ID列表"))
            notice_template = NoticeTemplateSerializer()

            def validate_config(self, value):
                return validate_action_config(value)

        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        name = serializers.CharField(required=True, max_length=128, label=_("策略名称"))
        scenario = serializers.CharField(required=True, label=_("监控场景"))
        id = serializers.IntegerField(required=False, label=_("策略ID"))
        source = serializers.CharField(required=False, label=_("策略配置来源"))
        item_list = serializers.ListField(
            child=ItemListSerializer(required=True, label=_("监控算法配置")),
            min_length=1,
        )
        action_list = serializers.ListField(
            child=ActionListSerializer(required=True, label=_("触发动作")),
        )
        is_enabled = serializers.BooleanField(label=_("是否启用"), default=True)
        labels = serializers.ListField(child=serializers.CharField(), required=False)

        def validate_target(self, value):
            is_validate_target(value)
            return handel_target(value)

        def validate_no_data_config(self, value):
            return validate_no_data_config_msg(value)

    def perform_request(self, validated_request_data):
        # 补全算法单位
        item_list = validated_request_data["item_list"]
        for item in item_list:
            if not item["rt_query_config"]:
                continue

            for algorithm in item["algorithm_list"]:
                if "algorithm_unit" in algorithm:
                    continue

                unit = load_unit(item["rt_query_config"].get("unit", ""))
                algorithm["algorithm_unit"] = unit.unit

        for item in validated_request_data["item_list"]:
            rt_query_config = item.get("rt_query_config", {})
            if item["data_source_label"] != DataSourceLabel.CUSTOM or item["data_type_label"] != DataTypeLabel.EVENT:
                continue

            if "result_table_id" in rt_query_config:
                continue

            event_group = CustomEventGroup.objects.get(
                bk_biz_id=validated_request_data["bk_biz_id"], bk_event_group_id=rt_query_config["bk_event_group_id"]
            )
            rt_query_config["result_table_id"] = event_group.table_id

        strategy_config = Strategy.from_dict_v1(validated_request_data)
        strategy_config.save()
        StrategyLabel.save_strategy_label(
            validated_request_data["bk_biz_id"], strategy_config.id, validated_request_data.get("labels", [])
        )
        return {"id": strategy_config.id}
