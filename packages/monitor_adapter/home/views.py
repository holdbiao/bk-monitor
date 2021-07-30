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

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import ugettext as _

from core.drf_resource import resource
from bkmonitor.utils.upgrade import allow_upgrade, is_new_biz
from monitor_web.strategies.built_in import run_build_in
from common.log import logger


def home(request):
    biz_id_list = resource.cc.get_app_ids_by_user(request.user)
    if not biz_id_list:
        cc_biz_id = settings.DEMO_BIZ_ID
        logger.info(_("用户:%s 没有任何业务权限.") % request.user)
    else:
        cc_biz_id = request.GET.get("bizId") or request.session.get("bk_biz_id") or request.COOKIES.get("bk_biz_id")
        if cc_biz_id not in biz_id_list:
            cc_biz_id = biz_id_list[0]

        if not allow_upgrade() or is_new_biz(cc_biz_id):
            # 如果当前环境允许做3.1迁移，则不自动创建策略，而是通过迁移页面手动创建
            # 创建内置策略
            run_build_in(int(cc_biz_id))

    response = render(
        request, "monitor/index.html", {"cc_biz_id": cc_biz_id, "AGENT_SETUP_URL": settings.AGENT_SETUP_URL}
    )

    if biz_id_list:
        response.set_cookie("bk_biz_id", str(cc_biz_id))

    return response


def service_worker(request):
    return render(request, "monitor/service-worker.js", content_type="application/javascript")


def manifest(request):
    return render(request, "monitor/manifest.json", content_type="application/json")
