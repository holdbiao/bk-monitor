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
from collections import defaultdict
from typing import Dict

from blueapps.utils import get_request
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.drf_resource import Resource, api
from core.errors.dashboard import GetFolderOrDashboardError
from monitor_web.grafana.auth import GrafanaAuthSync
from monitor_web.grafana.utils import get_org_id


class GetDashboardList(Resource):
    """
    查询仪表盘列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        is_report = serializers.BooleanField(label=_("是否订阅报表请求接口"), default=False, required=False)

    def perform_request(self, params):
        org_id = GrafanaAuthSync.get_or_create_org_id(params["bk_biz_id"])

        try:
            username = get_request().user.username
            if params["is_report"]:
                username = "admin"
        except Exception:
            username = "admin"

        result = api.grafana.search_folder_or_dashboard(type="dash-db", org_id=org_id, username=username)

        if result["result"]:
            dashboards = result["data"]
        else:
            return {
                "result": result["result"],
                "code": result["code"],
                "message": result["message"],
            }

        return [
            {
                "id": dashboard["id"],
                "uid": dashboard["uid"],
                "text": (f"{dashboard['folderTitle']}/" if "folderTitle" in dashboard else "") + dashboard["title"],
                "name": dashboard["title"],
            }
            for dashboard in dashboards
        ]


class GetDirectoryTree(Resource):
    """
    查询目录树
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))

    def perform_request(self, params):
        org_id = get_org_id(params["bk_biz_id"])

        try:
            username = get_request().user.username
        except Exception:
            username = "admin"

        result = api.grafana.search_folder_or_dashboard(org_id=org_id, username=username)

        if not result:
            raise GetFolderOrDashboardError(**result)

        folders: Dict[int, Dict] = defaultdict(lambda: {"dashboards": []})
        folders[0].update(
            {"id": 0, "uid": "", "title": "General", "uri": "", "url": "", "slug": "", "tags": [], "isStarred": False}
        )

        for record in result["data"]:
            _type = record.pop("type", "")
            if _type == "dash-folder":
                folders[record["id"]].update(record)
            elif _type == "dash-db":
                folder_id = record.pop("folderId", 0)
                record.pop("folderUid", None)
                record.pop("folderTitle", None)
                record.pop("folderUrl", None)
                folders[folder_id]["dashboards"].append(record)

        return list(folders.values())


class CreateDashboardOrFolder(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        title = serializers.CharField(label=_("名称"))
        type = serializers.ChoiceField(label=_("类型"), choices=(("dashboard", _("仪表盘")), ("folder", _("文件夹"))))
        folderId = serializers.IntegerField(label=_("文件夹ID"), default=0)

    def perform_request(self, params):
        org_id = get_org_id(params["bk_biz_id"])

        if params["type"] == "folder":
            result = api.grafana.create_folder(org_id=org_id, title=params["title"])
        else:
            result = api.grafana.create_dashboard(
                dashboard={"title": params["title"], "tags": [], "timezone": "default", "schemaVersion": 0},
                folderId=params["folderId"],
                org_id=org_id,
            )

        return result


class GetDefaultDashboard(Resource):
    """
    查询当前默认仪表盘
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))

    def perform_request(self, params):
        org_id = GrafanaAuthSync.get_or_create_org_id(params["bk_biz_id"])
        result = api.grafana.get_organization_preference(org_id=org_id)

        if not result["result"]:
            return result

        home_dashboard_id = result["data"]["homeDashboardId"]
        if not home_dashboard_id:
            return {}

        result = api.grafana.search_folder_or_dashboard(type="dash-db", org_id=org_id, dashboardIds=[home_dashboard_id])

        if result["result"] and result["data"]:
            return result["data"][0]

        return {}


class SetDefaultDashboard(Resource):
    """
    设置默认仪表盘
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        dashboard_uid = serializers.CharField(label=_("仪表盘ID"))

    def perform_request(self, params):
        org_id = GrafanaAuthSync.get_or_create_org_id(params["bk_biz_id"])
        result = api.grafana.search_folder_or_dashboard(type="dash-db", org_id=org_id)

        if result["result"]:
            dashboards = result["data"]
        else:
            return {
                "result": result["result"],
                "code": result["code"],
                "message": result["message"],
            }

        for dashboard in dashboards:
            if dashboard["uid"] == params["dashboard_uid"]:
                return api.grafana.update_organization_preference(org_id=org_id, homeDashboardId=dashboard["id"])
        return {"result": False, "message": _("设置失败，找不到该仪表盘")}
