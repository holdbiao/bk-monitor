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
import logging

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from bk_dataview.grafana.views import ProxyView, StaticView, SwitchOrgView, _ORG_CACHE
from bkmonitor.iam import Permission, ActionEnum
from core.drf_resource import api
from monitor_web.grafana.utils import patch_home_panels

__all__ = ["ProxyView", "StaticView", "SwitchOrgView"]

logger = logging.getLogger(__name__)


class GrafanaProxyView(ProxyView):
    @staticmethod
    def is_modify_dashboard_api(request):
        """
        判断是否是在修改仪表盘相关配置
        """
        return request.path.rstrip("/").endswith("/api/dashboards/db") and request.method == "POST"

    @staticmethod
    def is_modify_folder_api(request):
        """
        判断是否是在修改文件夹相关配置
        """
        return request.path.rstrip("/").endswith("/api/folders") and request.method == "POST"

    def get_request_headers(self, request):
        headers = super(GrafanaProxyView, self).get_request_headers(request)

        is_dashboard_api = self.is_modify_dashboard_api(request)
        is_folder_api = self.is_modify_folder_api(request)

        bk_biz_id = int(request.org_name)
        has_permission = Permission().is_allowed_by_biz(bk_biz_id, ActionEnum.MANAGE_DASHBOARD)

        if (is_dashboard_api or is_folder_api) and has_permission:
            headers["X-WEBAUTH-USER"] = "admin"

        return headers

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        response = super(GrafanaProxyView, self).dispatch(request, *args, **kwargs)

        # 这里对 Home 仪表盘进行 patch，替换为指定的面板
        if request.method == "GET" and request.path.rstrip("/").endswith("/api/dashboards/home"):
            try:
                origin_content = json.loads(response.content)
                patched_content = json.dumps(patch_home_panels(origin_content))
                return HttpResponse(patched_content, status=response.status_code)
            except Exception as e:
                logger.exception("[patch home panels] error: {}".format(e))
                # 异常则不替换了
                return response

        # 如果是更新仪表盘的操作，则尝试重置仪表盘权限
        try:
            if self.is_modify_dashboard_api(request):
                dashboard_id = json.loads(response.content)["id"]
                org_id = _ORG_CACHE.get(request.org_name)
                result = api.grafana.update_dashboard_permission(
                    id=dashboard_id,
                    org_id=org_id,
                    items=[
                        {"role": "Viewer", "permission": 1},
                        {"role": "Editor", "permission": 2},
                    ],
                )
                if not result["result"]:
                    logger.error(f"update dashboard permission failed: {result['message']}")
        except Exception as e:
            logger.error("update dashboard permission failed.")
            logger.exception(e)

        return response

    def update_response(self, response, content):
        content = super(GrafanaProxyView, self).update_response(response, content)
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return content.replace(
            "<script>", f"<script>\nvar graphWatermark={'true' if settings.GRAPH_WATERMARK else 'false'};"
        )
