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

from core.drf_resource import api, resource


def fetch_panel_title_ids(bk_biz_id, dashboard_uid):
    """
    获取仪表盘的所有Panel信息
    :param bk_biz_id: 业务ID
    :param dashboard_uid: 仪表盘uid
    :return: [{
        "title": panel["title"],
        "id": panel["id"]
    }]
    """
    if bk_biz_id == "-1":
        bk_biz_id = settings.MAIL_REPORT_BIZ
    org = api.grafana.get_organization_by_name(name=str(bk_biz_id))
    if org.get("data") and org["data"].get("id"):
        org_id = org["data"]["id"]
        dashboard_config = api.grafana.get_dashboard_by_uid(uid=dashboard_uid, org_id=int(org_id))
        if not dashboard_config.get("data"):
            return []
        dashboard_panels = dashboard_config["data"].get("dashboard", {}).get("panels", [])
        panel_id_title = []
        for panel in dashboard_panels:
            if panel["type"] == "row":
                # 绕过行式panel
                continue
            if panel.get("panels", []):
                # 处理panel集合
                for extend_panel in panel["panels"]:
                    panel_id_title.append({"title": extend_panel["title"], "id": extend_panel["id"]})
            else:
                # 单一个panel
                panel_id_title.append({"title": panel["title"], "id": panel["id"]})
        return panel_id_title
    return []


def fetch_biz_panels(bk_biz_id):
    """
    获取业务下所有dashboard信息与其panels信息
    :param bk_biz_id: 业务ID
    :return: panelsID
    """
    dashboards = resource.grafana.get_dashboard_list(bk_biz_id=bk_biz_id, is_report=True)
    for dashboard in dashboards:
        dashboard["bk_biz_id"] = bk_biz_id
        panels = fetch_panel_title_ids(bk_biz_id, dashboard["uid"])
        dashboard["panels"] = panels
    return dashboards
