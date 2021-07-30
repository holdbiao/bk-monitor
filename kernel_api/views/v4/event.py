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


from rest_framework import exceptions, serializers

from core.drf_resource import Resource, resource
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from bkmonitor.models import Event, EventAction
from bkmonitor.utils.event_related_info import get_event_relation_info


class SearchEvent(Resource):
    """
    查询事件
    """

    def perform_request(self, params):
        events = resource.alert_events.query_events(**params)
        events = events.extra(order_by=["-status", "-end_time", "-id"])

        # fmt: off
        if "page" in params:
            page = params["page"]
            page_size = params.get("page_size", 100)
            events = events[(page - 1) * page_size: page * page_size]
        # fmt: on

        fields = params.get("fields")
        if not isinstance(fields, list):
            fields = []

        result = [
            {
                "id": event.id,
                "create_time": event.create_time,
                "begin_time": event.begin_time,
                "end_time": event.end_time if event.end_time else None,
                "event_id": event.event_id,
                "bk_biz_id": event.bk_biz_id,
                "strategy_id": event.strategy_id,
                "origin_alarm": event.origin_alarm,
                "origin_config": event.origin_config,
                "level": event.level,
                "status": event.status,
                "is_ack": event.is_ack,
                "p_event_id": event.p_event_id,
                "is_shielded": event.is_shielded,
                "target_key": event.target_key,
            }
            for event in events
        ]

        if fields and "related_info" in fields:
            events_dict = {event.id: event for event in events}
            for record in result:
                try:
                    record["related_info"] = get_event_relation_info(events_dict[record["id"]])
                except Exception:
                    continue

        # 字段过滤
        if fields:
            for index, event in enumerate(result):
                result[index] = {key: value for key, value in list(event.items()) if key in fields}

        return result


class SearchEventLog(Resource):
    """
    查询事件流水
    """

    class RequestSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    def perform_request(self, params):
        event = Event.objects.filter(id=params["id"])

        if event:
            event = event[0]
        else:
            raise exceptions.ValidationError("event({}) not exists.".format(params["id"]))

        event_actions = EventAction.objects.filter(event_id=event.event_id)

        return [
            {
                "operate": event_action.operate,
                "message": event_action.message,
                "extend_info": event_action.extend_info,
                "status": event_action.status,
                "event_id": event_action.event_id,
                "create_time": event_action.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for event_action in event_actions
        ]


class EventViewSet(ResourceViewSet):
    """
    告警事件API
    """

    resource_routes = [
        ResourceRoute("POST", SearchEvent, endpoint="search"),
        ResourceRoute("GET", SearchEventLog, endpoint="event_log"),
        # 告警确认
        ResourceRoute("POST", resource.alert_events.ack_event, endpoint="ack_event"),
    ]
