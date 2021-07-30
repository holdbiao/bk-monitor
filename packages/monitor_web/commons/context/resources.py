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
from django.utils.translation import ugettext_lazy as _lazy

from core.drf_resource.base import Resource
from core.drf_resource import resource
from bkmonitor.utils.request import get_request
from bkmonitor.views import serializers
from common.context_processors import get_context as _get_context


class GetContextResource(Resource):
    """
    获取业务下的结果表列表（包含全业务）
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))

    def perform_request(self, validated_request_data):
        request = get_request()
        context = _get_context(request)

        result = {
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
                "ENABLE_MESSAGE_QUEUE",
                "MESSAGE_QUEUE_DSN",
                "CE_URL",
                "UPGRADE_ALLOWED",
                "MAX_AVAILABLE_DURATION_LIMIT",
                "BK_CC_URL",
                "BKLOGSEARCH_HOST",
                "MAIL_REPORT_BIZ",
                "BK_NODEMAN_HOST",
                "ENABLE_GRAFANA",
                "PAGE_TITLE",
                "GRAPH_WATERMARK",
                "COLLECTING_CONFIG_FILE_MAXSIZE",
            ]
        }

        result["BK_BIZ_LIST"] = [
            {
                "id": bk_biz_id,
                "text": f"[{bk_biz_id}] {context['cc_biz_names'][bk_biz_id]}",
                "is_demo": bk_biz_id == int(settings.DEMO_BIZ_ID),
            }
            for bk_biz_id in context["cc_biz_names"]
        ]

        result["PLATFORM"] = {key: getattr(context["PLATFORM"], key) for key in ["ce", "ee", "te"]}

        biz_id_list = resource.cc.get_app_ids_by_user(request.user)
        if biz_id_list:

            bk_biz_id = request.session.get("bk_biz_id") or request.COOKIES.get("bk_biz_id")
            if bk_biz_id not in biz_id_list:
                bk_biz_id = biz_id_list[0]

            result["BK_BIZ_ID"] = int(bk_biz_id)

        return result
