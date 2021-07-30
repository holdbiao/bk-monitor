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
from __future__ import absolute_import, print_function, unicode_literals

from rest_framework.authentication import SessionAuthentication

from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from bkmonitor.middlewares.authentication import NoCsrfSessionAuthentication
from core.drf_resource import resource
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet


class GrafanaViewSet(IAMPermissionMixin, ResourceViewSet):
    """
    时序数据DataSource
    """

    iam_read_actions = ActionEnum.VIEW_DASHBOARD
    iam_write_actions = ActionEnum.VIEW_DASHBOARD

    def get_authenticators(self):
        authenticators = super(GrafanaViewSet, self).get_authenticators()
        authenticators = [
            authenticator for authenticator in authenticators if not isinstance(authenticator, SessionAuthentication)
        ]
        authenticators.append(NoCsrfSessionAuthentication())
        return authenticators

    def get_iam_actions(self):
        if self.action == "save_to_dashboard":
            return [ActionEnum.MANAGE_DASHBOARD]
        if self.action == "time_series/query":
            return [
                ActionEnum.VIEW_DASHBOARD,
                ActionEnum.VIEW_HOST,
                ActionEnum.VIEW_COLLECTION,
                ActionEnum.EXPLORE_METRIC,
            ]
        return super(GrafanaViewSet, self).get_iam_actions()

    resource_routes = [
        # 插件接口
        ResourceRoute("GET", resource.grafana.test),
        ResourceRoute("GET", resource.commons.get_label, endpoint="get_label"),
        ResourceRoute("GET", resource.commons.get_topo_tree, endpoint="topo_tree"),
        ResourceRoute("GET", resource.strategies.get_dimension_values, endpoint="get_dimension_values"),
        ResourceRoute("POST", resource.grafana.get_variable_value, endpoint="get_variable_value"),
        ResourceRoute("GET", resource.grafana.get_variable_field, endpoint="get_variable_field"),
        ResourceRoute("POST", resource.grafana.time_series_query, endpoint="time_series/query"),
        ResourceRoute(
            "POST", resource.grafana.time_series_metric, endpoint="time_series/metric", content_encoding="gzip"
        ),
        ResourceRoute("POST", resource.grafana.time_series_metric_level, endpoint="time_series/metric_level"),
        ResourceRoute("POST", resource.grafana.log_query, endpoint="log/query"),
        # 设置默认仪表盘
        ResourceRoute("GET", resource.grafana.get_dashboard_list, endpoint="dashboards"),
        ResourceRoute("POST", resource.grafana.set_default_dashboard, endpoint="set_default_dashboard"),
        ResourceRoute("GET", resource.grafana.get_default_dashboard, endpoint="get_default_dashboard"),
        # 新老仪表盘迁移
        ResourceRoute("POST", resource.grafana.migrate_old_dashboard, endpoint="migrate_old_dashboard"),
        ResourceRoute("GET", resource.grafana.get_old_dashboards, endpoint="get_old_dashboards"),
        # 仪表盘管理
        ResourceRoute("GET", resource.grafana.get_directory_tree, endpoint="get_directory_tree"),
        ResourceRoute("POST", resource.grafana.create_dashboard_or_folder, endpoint="create_dashboard_or_folder"),
        # 视图保存
        ResourceRoute("POST", resource.data_explorer.save_to_dashboard, endpoint="save_to_dashboard"),
    ]
