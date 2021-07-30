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
from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from core.drf_resource import resource


class StrategiesViewSet(IAMPermissionMixin, ResourceViewSet):

    iam_read_actions = ActionEnum.VIEW_RULE
    iam_write_actions = ActionEnum.MANAGE_RULE

    def get_iam_actions(self):
        if self.action in [
            "get_unit_list",
            "get_scenario_list",
            "strategy_label",
            "strategy_label_list",
            "delete_strategy_label",
        ]:
            return []
        if self.action in ["strategy_config_list", "fetch_item_status"]:
            return [ActionEnum.VIEW_RULE]
        if self.action == "get_metric_list":
            return [ActionEnum.VIEW_RULE, ActionEnum.EXPLORE_METRIC]
        return super(StrategiesViewSet, self).get_iam_actions()

    resource_routes = [
        # 获取全部监控场景
        ResourceRoute("GET", resource.strategies.get_scenario_list, endpoint="get_scenario_list"),
        # 获取全部监控指标
        ResourceRoute("POST", resource.strategies.get_metric_list, endpoint="get_metric_list"),
        # 获取指标维度最近所上报的值
        ResourceRoute("POST", resource.strategies.get_dimension_values, endpoint="get_dimension_values"),
        # 创建、修改监控策略
        ResourceRoute("POST", resource.strategies.strategy_config, endpoint="strategy_config"),
        # 拷贝监控策略
        ResourceRoute("POST", resource.strategies.clone_strategy_config, endpoint="clone_strategy_config"),
        # 删除监控策略
        ResourceRoute("POST", resource.strategies.delete_strategy_config, endpoint="delete_strategy_config"),
        # 获取监控策略列表
        ResourceRoute("POST", resource.strategies.strategy_config_list, endpoint="strategy_config_list"),
        # 获取监控策略详情
        ResourceRoute("GET", resource.strategies.strategy_config_detail, endpoint="strategy_config_detail"),
        # 批量修改策略接口
        ResourceRoute("POST", resource.strategies.bulk_edit_strategy, endpoint="bulk_edit_strategy"),
        # 获取指标的维度列表
        ResourceRoute("GET", resource.strategies.get_dimension_list, endpoint="get_dimension_list"),
        # 获取监控策略轻量列表
        ResourceRoute("GET", resource.strategies.plain_strategy_list, endpoint="plain_strategy_list"),
        # 获取监控策略信息
        ResourceRoute("GET", resource.strategies.strategy_info, endpoint="strategy_info"),
        # 获取模板变量列表
        ResourceRoute("GET", resource.strategies.notice_variable_list, endpoint="notice_variable_list"),
        # 获取索引列表
        ResourceRoute("GET", resource.strategies.get_index_set_list, endpoint="get_index_set_list"),
        # 获取索引field
        ResourceRoute("GET", resource.strategies.get_log_fields, endpoint="get_log_fields"),
        # 渲染通知模板
        ResourceRoute("POST", resource.strategies.render_notice_template, endpoint="render_notice_template"),
        # 获取动态单位列表
        ResourceRoute("GET", resource.strategies.get_unit_list, endpoint="get_unit_list"),
        # 获取单位详情
        ResourceRoute("GET", resource.strategies.get_unit_info, endpoint="get_unit_info"),
        # 创建、修改策略标签
        ResourceRoute("POST", resource.strategies.strategy_label, endpoint="strategy_label"),
        # 获取策略标签列表
        ResourceRoute("GET", resource.strategies.strategy_label_list, endpoint="strategy_label_list"),
        # 删除策略标签
        ResourceRoute("POST", resource.strategies.delete_strategy_label, endpoint="delete_strategy_label"),
        # 查询指标策略配置及告警情况
        ResourceRoute("POST", resource.strategies.fetch_item_status, endpoint="fetch_item_status"),
    ]
