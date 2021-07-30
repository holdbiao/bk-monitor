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


import version_log.config as config
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.static import serve

from bkmonitor.iam import Permission, ActionEnum


def wrapped_serve(*args, **kwargs):
    response = serve(*args, **kwargs)
    if response.get("Content-Type") == "application/x-tar" and response.has_header("Content-Encoding"):
        # 删除编码，防止浏览器侧直接对tgz文件解压
        del response["Content-Encoding"]
    return response


urlpatterns = [
    url(r"^account/", include("blueapps.account.urls")),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^rest/v1/", include("monitor_api.urls", namespace="monitor_api")),
    url(r"^weixin/", include("weixin.urls", namespace="weixin")),
    url(r"^", include("monitor_adapter.urls", namespace="monitor_adapter")),
    url(r"^rest/v2/", include("monitor_web.urls", namespace="monitor_web")),
    url(r"^{}".format(config.ENTRANCE_URL), include("version_log.urls")),
    url(r"^media/(?P<path>.*)$", wrapped_serve, {"document_root": settings.MEDIA_ROOT}),
]


def render_403(request):
    """
    无权限页面
    PS: 加了Demo业务后，此函数仅兜底使用
    """
    from django.shortcuts import render
    from core.drf_resource import resource

    user_biz_list = resource.cc.get_app_ids_by_user(request.user)
    application_map = resource.cc.get_biz_map()
    request_biz_obj = application_map.get(request.biz_id)

    apply_url = Permission().get_apply_url([ActionEnum.VIEW_HOME, ActionEnum.VIEW_BUSINESS])

    return render(
        request,
        "/adapter/403.html",
        {
            "BK_IAM_APPLY_URL": apply_url,
            "has_biz": len(user_biz_list) > 0 and request_biz_obj,
            "request_biz_obj": request_biz_obj,
            "application_map": application_map,
        },
    )


handler403 = render_403
