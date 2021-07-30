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
import datetime

from django.utils.translation import ugettext as _
from rest_framework import exceptions, serializers

from bkmonitor.utils.user import get_global_user
from core.drf_resource import Resource, resource
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from bkmonitor.models import NoticeGroup, StrategyModel


class SaveAlarmStrategy(Resource):
    """
    保存告警策略
    """

    class NoticeGroupSerializer(serializers.Serializer):
        name = serializers.CharField(required=False, max_length=128)
        notice_receiver = serializers.ListField(required=False, child=serializers.CharField())
        notice_way = serializers.DictField(required=False, child=serializers.ListField())
        message = serializers.CharField(required=False, allow_blank=True)
        id = serializers.IntegerField(required=False)

        def validate(self, attrs):
            if "id" not in attrs and len({"name", "notice_receiver", "notice_way"} & set(attrs.keys())) < 3:
                raise exceptions.ValidationError("notice_group_list validate error")
            return attrs

    def parse_notice_group(self, bk_biz_id, notice_group_list):
        """
        解析通知组配置
        :param bk_biz_id: 业务ID
        :param notice_group_list: 通知组配置
        """
        serializer = self.NoticeGroupSerializer(many=True, data=notice_group_list)
        serializer.is_valid(raise_exception=True)
        notice_group_list = serializer.validated_data

        config = []
        for notice_group in notice_group_list:
            if "id" in notice_group:
                NoticeGroup.objects.filter(id=notice_group["id"]).update(**notice_group)
                config.append(notice_group["id"])
            else:
                group = NoticeGroup.objects.create(bk_biz_id=bk_biz_id, **notice_group)
                config.append(group.id)

        return config

    def perform_request(self, params):
        if "bk_biz_id" in params:
            for action in params.get("action_list", []):
                if "notice_group_list" in action:
                    action["notice_group_list"] = self.parse_notice_group(
                        params["bk_biz_id"], action["notice_group_list"]
                    )

        return resource.strategies.backend_strategy_config(**params)


class SearchAlarmStrategy(Resource):
    """
    搜索告警策略
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        order_by = serializers.CharField(required=False, default="-update_time", label=_("排序字段"))
        search = serializers.CharField(required=False, label=_("查询参数"))
        scenario = serializers.CharField(required=False, label=_("二级标签"))
        page = serializers.IntegerField(required=False, label=_("页码"))
        page_size = serializers.IntegerField(required=False, label=_("每页条数"))
        notice_group_name = serializers.CharField(required=False, label=_("告警组名称"))
        service_category = serializers.CharField(required=False, label=_("服务分类"))
        task_id = serializers.IntegerField(required=False, label=_("任务ID"))
        IP = serializers.IPAddressField(required=False, label=_("IP筛选"))
        metric_id = serializers.CharField(required=False, label=_("指标ID"))
        ids = serializers.ListField(required=False, label=_("ID列表"))

        fields = serializers.ListField(default=[], label=_("所需字段"))

    def perform_request(self, validated_request_data):
        result = resource.strategies.backend_strategy_config_list(**validated_request_data)

        if validated_request_data["fields"]:
            for index, alarm_strategy in enumerate(result):
                result[index] = {
                    key: value for key, value in alarm_strategy.items() if key in validated_request_data["fields"]
                }
        return result


class SwitchAlarmStrategy(Resource):
    """
    开关告警策略
    """

    class RequestSerializer(serializers.Serializer):
        ids = serializers.ListField(child=serializers.IntegerField(), label=_("策略ID列表"))
        is_enabled = serializers.BooleanField()

    def perform_request(self, params):
        strategies = StrategyModel.objects.filter(id__in=params["ids"])
        username = get_global_user() or "unknown"
        strategies.update(is_enabled=params["is_enabled"], update_user=username, update_time=datetime.datetime.now())

        switch_ids = [strategy.id for strategy in strategies]

        return {
            "ids": switch_ids,
        }


class AlarmStrategyViewSet(ResourceViewSet):
    """
    告警策略API
    """

    resource_routes = [
        ResourceRoute("POST", SearchAlarmStrategy, endpoint="search"),
        ResourceRoute("POST", SaveAlarmStrategy, endpoint="save"),
        ResourceRoute("POST", resource.strategies.delete_strategy_config, endpoint="delete"),
        ResourceRoute("POST", SwitchAlarmStrategy, endpoint="switch"),
    ]
