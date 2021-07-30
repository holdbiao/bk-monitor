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

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from core.drf_resource import Resource, api
from monitor_web.models.function_switch import PluginFunction

logger = logging.getLogger(__name__)


class ListFunctionResource(Resource):
    """
    获取功能列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        functions = PluginFunction.list_functions(bk_biz_id)
        result = [
            {
                "id": function.function_id,
                "display_name": function.display_name,
                "plugin_id": function.plugin_id,
                "is_enable": function.is_enable,
                "bk_biz_id": function.bk_biz_id,
                "host_count": {
                    "success": "-",
                    "total": "-",
                },
            }
            for function in functions
        ]

        return result


class SwitchFunctionResource(Resource):
    """
    开关切换
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        id = serializers.CharField(required=True, label=_("功能ID"))
        is_enable = serializers.BooleanField(required=True, label=_("开关"))

    def get_subscription_params(self, function: PluginFunction):
        """
        拼接订阅参数
        """
        scope = {
            "bk_biz_id": function.bk_biz_id,
            "object_type": "HOST",
            "node_type": "TOPO",
            "nodes": [{"bk_inst_id": function.bk_biz_id, "bk_obj_id": "biz"}],
        }
        step = {
            "id": function.plugin_id,
            "type": "PLUGIN",
            "config": {
                "plugin_name": function.plugin_id,
                "plugin_version": "latest",
                "config_templates": [
                    {
                        "name": f"{function.plugin_id}.conf",
                        "version": "latest",
                        "is_main": True,
                    }
                ],
            },
            "params": {"context": {}},
        }
        params = {
            "scope": scope,
            "steps": [step],
            "run_immediately": True,
            "is_main": True,
        }
        return params

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        function_id = validated_request_data["id"]
        is_enable = validated_request_data["is_enable"]

        function = PluginFunction.objects.get(
            bk_biz_id=bk_biz_id,
            function_id=function_id,
        )
        subscription_id = function.subscription_id

        if not subscription_id and is_enable:
            # 没有订阅ID，去创建订阅
            params = self.get_subscription_params(function)
            result = api.node_man.create_subscription(params)

            logger.info(
                f"[Switch Function] bk_biz_id: {bk_biz_id}, function_id: {function_id},"
                f"is_enable: {is_enable}, create subscription result: {result}"
            )

            subscription_id = result["subscription_id"]

        if not subscription_id:
            # 如果没有订阅ID，且为禁用的，直接忽略
            return

        # 有订阅ID，直接切换订阅状态
        result = api.node_man.switch_subscription(
            subscription_id=subscription_id, action="enable" if is_enable else "disable"
        )

        logger.info(
            f"[Switch Function] bk_biz_id: {bk_biz_id}, function_id: {function_id},"
            f"is_enable: {is_enable}, switch subscription result: {result}"
        )

        function.subscription_id = subscription_id
        function.is_enable = is_enable
        function.save()
