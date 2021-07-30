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

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bkmonitor.iam import Permission, ActionEnum, ResourceEnum
from core.drf_resource import Resource, resource


class GetAuthorityMetaResource(Resource):
    """
    获取动作列表
    """

    def perform_request(self, validated_request_data):
        return Permission().list_actions()


class CheckAllowedByActionIdsResource(Resource):
    """
    查询是否有权限
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        action_ids = serializers.ListField(required=True, allow_empty=False, label=_("动作ID列表"))

    def perform_request(self, validated_request_data):
        client = Permission()
        result = []
        for action_id in validated_request_data["action_ids"]:
            is_allowed = client.is_allowed_by_biz(validated_request_data["bk_biz_id"], action_id, raise_exception=False)
            result.append({"action_id": action_id, "is_allowed": is_allowed})
        return result


class GetAuthorityDetailResource(Resource):
    """
    根据动作ID获取授权信息详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        action_ids = serializers.ListField(required=True, label=_("动作ID"))

    def perform_request(self, validated_request_data):
        action_ids = validated_request_data["action_ids"]
        client = Permission()

        try:
            business = resource.cc.get_app_by_id(validated_request_data["bk_biz_id"])
            bk_biz_id = business.bk_biz_id
        except Exception:
            bk_biz_id = 0

        if not bk_biz_id:
            # 如果业务ID不存在，则不传资源实例
            apply_data, apply_url = client.get_apply_data(action_ids)
        else:
            business_resource = ResourceEnum.BUSINESS.create_instance(bk_biz_id)
            apply_data, apply_url = client.get_apply_data(action_ids, [business_resource])
        return {
            "authority_list": apply_data,
            "apply_url": apply_url,
        }


class TestResource(Resource):
    """
    测试抛出异常
    """

    def perform_request(self, validated_request_data):
        Permission(username="xxx").is_allowed_by_biz(2, ActionEnum.VIEW_BUSINESS, raise_exception=True)
