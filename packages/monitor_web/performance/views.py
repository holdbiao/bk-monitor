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
from core.drf_resource.viewsets import ResourceViewSet
from core.drf_resource.viewsets import ResourceRoute
from core.drf_resource import resource


class PermissionMixin(IAMPermissionMixin):
    iam_read_actions = ActionEnum.VIEW_HOST
    iam_write_actions = ActionEnum.VIEW_HOST


class CCTopoTreeViewSet(PermissionMixin, ResourceViewSet):
    """
    获取业务拓扑树
    """

    resource_routes = [ResourceRoute("GET", resource.performance.cc_topo_tree)]


class AgentStatusViewSet(PermissionMixin, ResourceViewSet):
    """
    获取主机agent状态,
    """

    resource_routes = [ResourceRoute("GET", resource.performance.agent_status)]


class HostAlarmViewSet(PermissionMixin, ResourceViewSet):
    resource_routes = [
        # 获取主机对应的告警列表
        # ResourceRoute("GET", resource.performance.host_alarm),
        # 获取主机告警数量
        ResourceRoute("GET", resource.performance.host_alarm_count, endpoint="count"),
    ]


class HostIndexViewSet(PermissionMixin, ResourceViewSet):

    resource_routes = [
        # 获取指标列表
        ResourceRoute("GET", resource.performance.host_index),
        # 获取主机指标结果表对应字段的所有值
        ResourceRoute("POST", resource.performance.get_field_values_by_index_id, endpoint="field_values"),
        # 获取主机指标对应的图表数据
        ResourceRoute("POST", resource.performance.graph_point, endpoint="graph_point"),
    ]


class HostComponentInfoViewSet(PermissionMixin, ResourceViewSet):
    """
    获取组件实时信息
    """

    resource_routes = [
        ResourceRoute("GET", resource.performance.host_component_info),
    ]


class HostPerformanceDetailViewSet(PermissionMixin, ResourceViewSet):
    """
    获取主机详情页信息
    """

    resource_routes = [ResourceRoute("POST", resource.performance.host_performance_detail)]


class HostTopoNodeDetailViewSet(PermissionMixin, ResourceViewSet):
    """
    获取主机拓扑树上的CMDB节点信息
    """

    resource_routes = [ResourceRoute("POST", resource.performance.host_topo_node_detail)]


class HostProcessStatusViewSet(PermissionMixin, ResourceViewSet):
    """
    获取主机下的进程状态信息
    """

    resource_routes = [ResourceRoute("POST", resource.performance.host_process_status)]


class TopoNodeProcessStatusViewSet(PermissionMixin, ResourceViewSet):
    """
    获取拓扑节点下的进程状态信息
    """

    resource_routes = [ResourceRoute("POST", resource.performance.topo_node_process_status)]


class HostListViewSet(PermissionMixin, ResourceViewSet):
    """
    获取主机列表信息
    """

    resource_routes = [ResourceRoute("GET", resource.performance.host_performance, content_encoding="gzip")]


class GetHostDashboardConfigViewSet(ResourceViewSet):
    """
    获取主机图表配置
    """

    resource_routes = [ResourceRoute("POST", resource.performance.get_host_dashboard_config)]


class GetTopoNodeDashboardConfigViewSet(ResourceViewSet):
    """
    获取主机拓扑图表配置
    """

    resource_routes = [ResourceRoute("POST", resource.performance.get_topo_node_dashboard_config)]


class SearchHostInfoViewSet(ResourceViewSet):
    """
    查询主机基本信息
    """

    resource_routes = [
        ResourceRoute("POST", resource.performance.search_host_info, content_encoding="gzip"),
    ]


class SearchHostMetricViewSet(ResourceViewSet):
    """
    查询主机指标
    """

    resource_routes = [
        ResourceRoute("POST", resource.performance.search_host_metric),
    ]
