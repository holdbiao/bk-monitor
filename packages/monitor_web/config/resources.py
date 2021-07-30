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
from rest_framework import serializers

from bkmonitor.define.global_config import STANDARD_CONFIGS
from bkmonitor.models import GlobalConfig
from bkmonitor.utils.common_utils import to_page
from core.drf_resource import Resource, resource
from monitor_web.config.converter import convert_field
from monitor_web.models.config import RolePermission


class GetUserInfoResource(Resource):
    """
    获取业务权限人员
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True)
        index = serializers.IntegerField(default=1)

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        index = validated_request_data["index"]

        biz = resource.cc.get_app_by_id(bk_biz_id)
        user_info = biz.select_fields(settings.AUTHORIZED_ROLES)

        user_info_list = []
        default_permission_info = settings.DEFAULT_ROLE_PERMISSIONS.copy()
        rp_records = RolePermission.objects.filter(biz_id=bk_biz_id)
        role_permission_info = {}
        for rp in rp_records:
            role_permission_info[rp.role] = rp

        for k, v in user_info.items():
            user_list = "; ".join(list(biz.get_nick_by_uin(v, show_detail=True).values())) if v else ""

            if k in role_permission_info:
                role_permission = role_permission_info[k]
            else:
                role_permission = RolePermission.objects.create(
                    biz_id=bk_biz_id, role=k, permission=default_permission_info.get(k, "r")
                )

            user_info_list.append(
                {
                    "user_list": user_list,
                    "permission": role_permission.permission,
                    "role": k,
                    "role_display": settings.NOTIRY_MAN_DICT.get(k, k),
                    "update_user": role_permission.update_user,
                    "update_time": role_permission.update_time,
                }
            )
        user_info_list.sort(key=lambda u: u["role"], reverse=True)
        # 分页
        user_info_list = to_page(user_info_list, index)
        return user_info_list


class SaveRolePermissionResource(Resource):
    """
    保存用户角色权限信息
    """

    class RequestSerializer(serializers.Serializer):
        role = serializers.CharField(required=True)
        permission = serializers.CharField(required=False)
        bk_biz_id = serializers.IntegerField(required=True)

    class ResponseSerializer(serializers.ModelSerializer):
        class Meta:
            model = RolePermission
            fields = "__all__"

    def perform_request(self, validated_request_data):
        role_permission, _ = RolePermission.objects.update_or_create(
            defaults={"permission": validated_request_data.get("permission", "")},
            biz_id=validated_request_data["bk_biz_id"],
            role=validated_request_data["role"],
        )
        return role_permission


class ListGlobalConfig(Resource):
    """
    拉取全局配置列表
    """

    def perform_request(self, validated_request_data):
        configs = GlobalConfig.objects.filter(is_advanced=False)
        result = {}
        for config in configs:
            result[config.key] = convert_field(config)
        standard_keys = list(STANDARD_CONFIGS.keys())
        sorted_configs = []
        for key in standard_keys:
            if key in result:
                sorted_configs.append(result.pop(key))
        sorted_configs += list(result.values())
        return sorted_configs


class SetGlobalConfig(Resource):
    """
    设置全局配置
    """

    class RequestSerializer(serializers.Serializer):
        class ConfigSerializer(serializers.Serializer):
            key = serializers.CharField()
            value = serializers.JSONField()

        configs = ConfigSerializer(required=True, many=True)

    def get_serializer_cls(self, data_type, options):
        cls_name = "{}Field".format(data_type)
        serializer_cls = getattr(serializers, cls_name)
        options = options or {}
        return serializer_cls(**options)

    def perform_request(self, validated_request_data):
        configs = {config.key: config for config in GlobalConfig.objects.filter(is_advanced=False)}

        set_results = []
        for data in validated_request_data["configs"]:
            key, value = data["key"], data["value"]
            if key not in configs:
                continue
            config = configs[key]
            try:
                serializer = config.get_serializer()
                value = serializer.run_validation(value)
                config.value = value
                config.save()
                result = True
                message = "modify success"
            except Exception as e:
                result = False
                message = "modify failed: {}".format(e)
            set_results.append(
                {
                    "key": key,
                    "value": value,
                    "result": result,
                    "message": message,
                }
            )
        return set_results
