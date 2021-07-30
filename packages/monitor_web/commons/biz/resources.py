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
import logging

from django.conf import settings

from bkmonitor.iam import Permission, ActionEnum, ResourceEnum
from core.drf_resource.base import Resource
from core.drf_resource import resource
from bkmonitor.views import serializers
from bkmonitor.utils.common_utils import safe_int
from bkmonitor.utils.request import get_request
from core.drf_resource import api
from core.errors.api import BKAPIError

BK_MONITOR_SITE_URL = "/o/bk_monitorv3/"

logger = logging.getLogger(__name__)


class BusinessListOptionResource(Resource):
    def perform_request(self, validated_request_data):
        request = get_request()
        select_options = [{"id": biz.id, "text": biz.display_name} for biz in resource.cc.get_app_by_user(request.user)]
        select_options.sort(key=lambda b: safe_int(b["id"]))
        return select_options


class FetchBusinessInfoResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, default=-1)

    def perform_request(self, params):
        """
        返回业务相关信息的接口
        """
        bk_biz_id = params["bk_biz_id"]
        bk_biz_name = ""
        maintainers = ""

        try:
            business = api.cmdb.get_business(bk_biz_ids=[bk_biz_id], all=True)
            if business:
                business = business[0]
                bk_biz_id = business.bk_biz_id
                bk_biz_name = business.bk_biz_name
                maintainers = business.bk_biz_maintainer
            else:
                bk_biz_id = ""
        except BKAPIError as e:
            bk_biz_id = ""
            logger.error(e)

        permission = Permission()
        if not bk_biz_id:
            access_url = permission.get_apply_url(action_ids=[ActionEnum.VIEW_HOME, ActionEnum.VIEW_BUSINESS])
        else:
            access_url = permission.get_apply_url(
                action_ids=[ActionEnum.VIEW_HOME, ActionEnum.VIEW_BUSINESS],
                resources=[ResourceEnum.BUSINESS.create_instance(bk_biz_id)],
            )

        return {
            "bk_biz_id": bk_biz_id,
            "bk_biz_name": bk_biz_name,
            "operator": maintainers,
            "get_access_url": access_url,
            "new_biz_apply": settings.DEMO_BIZ_APPLY,
        }
