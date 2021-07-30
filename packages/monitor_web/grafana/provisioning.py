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
import json

from bk_dataview.grafana.provisioning import SimpleProvisioning, Dashboard
from django.utils.translation import ugettext as _

from core.drf_resource import api


class BkMonitorProvisioning(SimpleProvisioning):
    def dashboards(self, request, org_name: str, org_id: int):
        """
        只执行一次
        """
        from monitor.models import ApplicationConfig

        # 如果已经执行过注入操作，则不注入
        _, created = ApplicationConfig.objects.get_or_create(
            cc_biz_id=org_name, key="grafana_default_dashboard", value="created"
        )

        if not created:
            return

        # 如果已经存在仪表盘，则不注入
        result = api.grafana.search_folder_or_dashboard(type="dash-db", org_id=org_id)
        if not result["result"] or result["data"]:
            return

        yield from super(BkMonitorProvisioning, self).dashboards(request, org_name, org_id)

        # 创建用户私人文件夹
        self.create_default_user_folder(org_id, request.user.username)

    @staticmethod
    def create_default_user_folder(org_id, username):
        """
        创建用户私人文件夹
        """
        result = api.grafana.create_folder(org_id=org_id, title=f"{username}" + _("私人仪表盘"))

        uid = result["data"]["uid"]

        result = api.grafana.get_user_by_login_or_email(loginOrEmail=username)
        if not result["result"]:
            return

        api.grafana.update_folder_permission(
            uid=uid, org_id=org_id, items=[{"userId": result["data"]["id"], "permission": 2}]
        )

    def dashboard_callback(self, request, org_name: str, org_id: int, dashboard: Dashboard, status: bool, content: str):
        if not status:
            return

        result = json.loads(content)
        api.grafana.update_organization_preference(org_id=org_id, homeDashboardId=result["id"])
