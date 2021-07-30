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
from django.utils.translation import ugettext as _, get_language

from bkmonitor.utils.common_utils import safe_int
from core.drf_resource import resource
from bkmonitor.utils import time_tools
from bkmonitor.utils.upgrade import allow_upgrade
from common.log import logger


class Platform(object):
    """
    平台信息
    """

    te = settings.BKAPP_DEPLOY_PLATFORM == "ieod"
    ee = settings.BKAPP_DEPLOY_PLATFORM == "enterprise"
    ce = settings.BKAPP_DEPLOY_PLATFORM == "community"


def _get_context(request):
    """
    渲染APP基础信息
    :param request:
    :return:
    """

    context = {
        # 基础信息
        "RUN_MODE": settings.RUN_MODE,
        "APP_CODE": settings.APP_CODE,
        "SITE_URL": settings.SITE_URL,
        "BK_PAAS_HOST": settings.BK_PAAS_HOST,
        "BK_CC_URL": settings.BK_CC_URL,
        "BK_JOB_URL": settings.JOB_URL,
        "BKLOGSEARCH_HOST": settings.BKLOGSEARCH_HOST,
        "BK_NODEMAN_HOST": settings.BK_NODEMAN_HOST,
        "GRAPH_WATERMARK": settings.GRAPH_WATERMARK,
        "MAIL_REPORT_BIZ": int(settings.MAIL_REPORT_BIZ),
        # 静态资源
        "STATIC_URL": settings.STATIC_URL,
        "STATIC_VERSION": settings.STATIC_VERSION,
        # 登录跳转链接
        "LOGIN_URL": settings.LOGIN_URL,
        # 'LOGOUT_URL': settings.LOGOUT_URL,
        # 当前页面，主要为了login_required做跳转用
        "APP_PATH": request.get_full_path(),
        "NOW": time_tools.localtime(time_tools.now()),
        "NICK": request.session.get("nick", ""),  # 用户昵称
        "AVATAR": request.session.get("avatar", ""),
        "MEDIA_URL": settings.MEDIA_URL,  # MEDIA_URL
        "BK_URL": settings.BK_URL,  # 蓝鲸平台URL
        "gettext": _,  # 国际化
        "_": _,  # 国际化
        "LANGUAGE_CODE": request.LANGUAGE_CODE,  # 国际化
        "LANGUAGES": settings.LANGUAGES,  # 国际化
        "REMOTE_STATIC_URL": settings.REMOTE_STATIC_URL,
        "WEIXIN_STATIC_URL": settings.WEIXIN_STATIC_URL,
        "WEIXIN_SITE_URL": settings.WEIXIN_SITE_URL,
        "RT_TABLE_PREFIX_VALUE": settings.RT_TABLE_PREFIX_VALUE,
        "uin": request.user.username,
        "is_superuser": str(request.user.is_superuser).lower(),
        "CSRF_COOKIE_NAME": settings.CSRF_COOKIE_NAME,
        "PLATFORM": Platform,
        "DOC_HOST": settings.DOC_HOST,
        "AGENT_SETUP_URL": settings.AGENT_SETUP_URL,
        "UTC_OFFSET": time_tools.utcoffset_in_seconds() // 60,
        "ENABLE_MESSAGE_QUEUE": "true" if settings.MESSAGE_QUEUE_DSN else "false",
        "MESSAGE_QUEUE_DSN": settings.MESSAGE_QUEUE_DSN,
        "CE_URL": settings.CE_URL,
        # 拨测前端校验参数
        "MAX_AVAILABLE_DURATION_LIMIT": settings.MAX_AVAILABLE_DURATION_LIMIT,
        "UPGRADE_ALLOWED": allow_upgrade(),
        "ENABLE_GRAFANA": bool(settings.GRAFANA_URL),
        # 页面title
        "PAGE_TITLE": (
            settings.HEADER_FOOTER_CONFIG["header"][0]["en"]
            if get_language() == "en"
            else settings.HEADER_FOOTER_CONFIG["header"][0]["zh"]
        ),
        "COLLECTING_CONFIG_FILE_MAXSIZE": settings.COLLECTING_CONFIG_FILE_MAXSIZE,
    }

    # 字段大小写标准化
    standard_context = {
        key.upper(): context[key]
        for key in context
        if key
        in [
            "APP_CODE",
            "SITE_URL",
            "STATIC_URL",
            "DOC_HOST",
            "BK_JOB_URL",
            "CSRF_COOKIE_NAME",
            "UTC_OFFSET",
            "is_superuser",
            "STATIC_VERSION",
            "AGENT_SETUP_URL",
            "RT_TABLE_PREFIX_VALUE",
            "NICK",
            "uin",
            "AVATAR",
            "APP_PATH",
            "BK_URL",
        ]
    }

    context.update(standard_context)

    # 获取用户有权限的业务列表
    context["cc_biz_names"] = dict()
    try:
        context["cc_biz_names"] = {biz.bk_biz_id: biz.bk_biz_name for biz in resource.cc.get_app_by_user(request.user)}
    except Exception as e:
        logger.error(f"Get Business Failed: {e}")

    # 格式化业务列表并排序
    context["BK_BIZ_LIST"] = [
        {"id": biz, "text": f"[{biz}] {context['cc_biz_names'][biz]}", "is_demo": biz == int(settings.DEMO_BIZ_ID)}
        for biz in context["cc_biz_names"]
    ]
    context["BK_BIZ_LIST"].sort(key=lambda biz: biz["id"])

    # 用户是否有当前访问的业务的权限
    context["BK_BIZ_ID"] = None
    biz_id_list = list(context["cc_biz_names"].keys())
    if biz_id_list:
        bk_biz_id = safe_int(request.biz_id)
        if bk_biz_id not in biz_id_list:
            bk_biz_id = biz_id_list[0]

        context["BK_BIZ_ID"] = int(bk_biz_id)

    # 如果用户没有任何权限，返回Demo业务的默认ID(-1)
    if not context["BK_BIZ_ID"]:
        context["BK_BIZ_ID"] = settings.DEMO_BIZ_ID

    # 是否开启前端视图部分，按拓扑聚合的能力。（不包含对监控策略部分的功能）
    context["ENABLE_CMDB_LEVEL"] = settings.IS_ACCESS_BK_DATA and settings.IS_ENABLE_VIEW_CMDB_LEVEL
    # 当前业务是否在AIOPS白名单中
    context["ENABLE_AIOPS"] = "false"
    try:
        if settings.IS_ACCESS_BK_DATA and {-1, safe_int(context["BK_BIZ_ID"])} & set(settings.AIOPS_BIZ_WHITE_LIST):
            context["ENABLE_AIOPS"] = "true"
    except Exception as e:
        logger.error(f"Get AIOPS_BIZ_WHITE_LIST Failed: {e}")

    return context


def get_context(request):
    try:
        return _get_context(request)
    except Exception as e:
        logger.exception(e)
        raise e
