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
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from core.drf_resource import resource


class CollectViewSet(ResourceViewSet):
    """
    采集下发API
    """

    resource_routes = [
        # 获取采集配置列表信息
        ResourceRoute("POST", resource.collecting.collect_config_list, endpoint="config_list"),
        # 获取采集配置详情信息
        ResourceRoute("GET", resource.collecting.collect_config_detail, endpoint="config_detail"),
        # 获取采集配置详情信息(前端接口)
        ResourceRoute("GET", resource.collecting.frontend_collect_config_detail, endpoint="frontend_config_detail"),
        # 获取采集下发状态
        ResourceRoute("GET", resource.collecting.collect_target_status, endpoint="status"),
        # 获取拓扑采集目标下发状态
        ResourceRoute("GET", resource.collecting.collect_node_status, endpoint="node_status"),
        # 启停采集配置
        ResourceRoute("POST", resource.collecting.toggle_collect_config_status, endpoint="toggle"),
        # 删除采集配置
        ResourceRoute("POST", resource.collecting.delete_collect_config, endpoint="delete"),
        # 克隆采集配置
        ResourceRoute("POST", resource.collecting.clone_collect_config, endpoint="clone"),
        # 重试部分实例或主机
        ResourceRoute("POST", resource.collecting.retry_target_nodes, endpoint="retry"),
        # 终止部分实例或主机
        ResourceRoute("POST", resource.collecting.revoke_target_nodes, endpoint="revoke"),
        # 批量终止实例或主机
        ResourceRoute("POST", resource.collecting.batch_revoke_target_nodes, endpoint="batch_revoke"),
        # 批量重试采集配置的失败实例
        ResourceRoute("POST", resource.collecting.batch_retry_config, endpoint="batch_retry"),
        # 新建/编辑采集配置
        ResourceRoute("POST", resource.collecting.save_collect_config, endpoint="save"),
        # 采集配置插件升级
        ResourceRoute("POST", resource.collecting.upgrade_collect_plugin, endpoint="upgrade"),
        # 采集配置回滚
        ResourceRoute("POST", resource.collecting.rollback_deployment_config, endpoint="rollback"),
        # 图表展示
        ResourceRoute("POST", resource.collecting.graph_point, endpoint="graph_point"),
        # 获取采集对象和状态
        ResourceRoute("POST", resource.collecting.frontend_target_status_topo, endpoint="target_status_topo"),
        # 获取对应插件版本的指标参数
        ResourceRoute("GET", resource.collecting.get_metrics, endpoint="metrics"),
        # 采集配置名称修改
        ResourceRoute("POST", resource.collecting.rename_collect_config, endpoint="rename"),
        # 获取采集配置的部署配置差异
        ResourceRoute("GET", resource.collecting.deployment_config_diff, endpoint="deployment_diff"),
        # 获取采集配置主机的运行状态
        ResourceRoute("GET", resource.collecting.collect_running_status, endpoint="running_status"),
        # 获取采集下发详细日志
        ResourceRoute("GET", resource.collecting.get_collect_log_detail, endpoint="get_collect_log_detail"),
        # 测试接口，更新采集配置的主机数目/异常数目
        ResourceRoute("GET", resource.collecting.update_config_instance_count, endpoint="update_config_instance_count"),
        # 获取采集配置变量列表
        ResourceRoute("GET", resource.collecting.get_collect_variables, endpoint="get_collect_variables"),
        # 配置执行详情列表接口
        ResourceRoute("GET", resource.collecting.collect_instance_status, endpoint="collect_instance_status"),
        # 重试失败的节点步骤
        ResourceRoute("POST", resource.collecting.batch_retry, endpoint="batch_retry_detailed"),
        # toolkit
        # 获取各个采集项遗留的订阅配置及节点管理无效的订阅任务
        ResourceRoute("GET", resource.collecting.list_legacy_subscription, endpoint="list_legacy_subscription"),
        # 停用并删除遗留的订阅配置
        ResourceRoute("GET", resource.collecting.clean_legacy_subscription, endpoint="clean_legacy_subscription"),
        # 列出当前无效的告警策略
        ResourceRoute("GET", resource.collecting.list_legacy_strategy, endpoint="list_legacy_strategy"),
    ]