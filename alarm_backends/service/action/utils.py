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
from django.db.models import Max
from django.utils.translation import ugettext as _

from alarm_backends.core.cache.cmdb import BusinessManager
from alarm_backends.core.cache.key import ACTION_LIST_KEY
from alarm_backends.core.cache.strategy import StrategyCacheManager
from api.cmdb.define import Business
from bkmonitor.models import AnomalyRecord, Event, EventAction
from bkmonitor.utils.event_related_info import get_event_relation_info

logger = logging.getLogger("action")


def create_actions(event_id, action_list, event_type, should_create_action=lambda x: True):
    """
    创建动作并推送到执行队列
    :param event_id: 事件ID
    :type event_id: int
    :param action_list: 动作配置列表
    :type action_list: list
    :param should_create_action: 根据action配置判断是否需要创建
    :type should_create_action: function
    """
    # 记录通知时的最新异常点
    try:
        # 优化查询
        event = Event(event_id=event_id)
        anomaly_id = event.latest_anomaly_record.anomaly_id if event.latest_anomaly_record else None
    except Event.DoesNotExist:
        anomaly_id = None

    pipeline = ACTION_LIST_KEY.client.pipeline(transaction=False)

    # 消息队列
    message_queue_event_action = None
    need_message_queue = settings.ENABLE_MESSAGE_QUEUE and settings.MESSAGE_QUEUE_DSN
    if need_message_queue:
        message_queue_operate = EventAction.MESSAGE_QUEUE_OPERATE_TYPE_MAPPING.get(event_type)
        message_queue_event_action = EventAction(
            operate=message_queue_operate,
            status=EventAction.Status.RUNNING,
            event_id=event_id,
            extend_info={"action": None, "anomaly_id": anomaly_id},
        )

    for action in action_list:
        action_type = action["action_type"]
        if action_type not in EventAction.ACTION_TYPE_MAPPING:
            continue
        operate = EventAction.ACTION_TYPE_MAPPING[action_type].get(event_type)
        if not operate:
            continue

        if not should_create_action(action):
            message_queue_event_action = None
            continue

        if need_message_queue and message_queue_event_action:
            message_queue_event_action.extend_info["action"] = action

        # 推送到通知队列
        if event_type == "recovery" and not action["config"].get("send_recovery_alarm"):
            continue
        elif event_type == "close" and not action["config"].get("send_close_alarm"):
            continue

        event_action = EventAction.objects.create(
            operate=operate,
            status=EventAction.Status.RUNNING,
            event_id=event_id,
            extend_info={"action": action, "anomaly_id": anomaly_id},
        )
        key = ACTION_LIST_KEY.get_key(action_type=action_type)

        pipeline.lpush(key, event_action.id)
        pipeline.expire(key, ACTION_LIST_KEY.ttl)

        logger.debug(
            "Event({event_id}) create event_action {action_type} EventAction({action_id})".format(
                event_id=event_id, action_type=action_type, action_id=event_action.id
            )
        )

    # 推送到消息队列
    if need_message_queue and message_queue_event_action:
        message_queue_event_action.save()
        message_queue_key = ACTION_LIST_KEY.get_key(action_type="message_queue")
        pipeline.lpush(message_queue_key, message_queue_event_action.id)
        pipeline.expire(message_queue_key, ACTION_LIST_KEY.ttl)

    pipeline.execute()


def get_notice_message(event, event_action):
    """
    推送给第三方的统一通知消息
    :param event: Event
    :param event_action: EventAction
    :return: dict
    """
    last_record = AnomalyRecord.objects.filter(event_id=event.event_id).values("event_id").annotate(last_id=Max("id"))
    if last_record:
        anomaly_record = AnomalyRecord.objects.get(id=last_record[0]["last_id"])
        anomaly_record = {
            "anomaly_id": anomaly_record.id,
            "source_time": anomaly_record.source_time.strftime("%Y-%m-%d %H:%M:%S"),
            "create_time": anomaly_record.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "origin_alarm": anomaly_record.origin_alarm,
        }
    else:
        anomaly_record = {}

    strategy = StrategyCacheManager.get_strategy_by_id(event.strategy_id) or event.origin_config
    biz = BusinessManager.get(event.bk_biz_id) or Business(bk_biz_id=event.bk_biz_id)

    data_source_names = {
        "bk_monitor": _("监控平台"),
        "bk_log_search": _("日志平台"),
        "bk_data": _("计算平台"),
        "custom": _("用户自定义"),
    }

    data_type_names = {
        "log": _("日志关键字"),
        "event": _("事件"),
        "time_series": _("时序"),
    }
    try:
        event_relation_info = get_event_relation_info(event)
    except Exception as e:
        logger.exception(f"get event[{event.id}] relation info error: {e}")
        event_relation_info = "get event relation info error: %s" % e
    return {
        "type": event_action.operate,
        "scenario": strategy["scenario"],
        "bk_biz_id": event.bk_biz_id,
        "bk_biz_name": biz.bk_biz_name,
        "event": {
            "id": event.id,
            "event_id": event.event_id,
            "begin_time": event.begin_time.strftime("%Y-%m-%d %H:%M:%S"),
            "create_time": event.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S") if event.end_time else None,
            "level": event.level,
            "level_name": event.level_name,
            "dimensions": event.origin_alarm["data"]["dimensions"],
            "dimension_translation": event.origin_alarm["dimension_translation"],
        },
        "strategy": {
            "id": strategy["id"],
            "name": strategy["name"],
            "scenario": strategy["scenario"],
            "item_list": [
                {
                    "metric_field": item["metric_id"].split(".")[-1],
                    "metric_field_name": item["name"],
                    "data_source_label": item["data_source_label"],
                    "data_source_name": data_source_names.get(item["data_source_label"], _("其他")),
                    "data_type_label": item["data_type_label"],
                    "data_type_name": data_type_names.get(item["data_type_label"], _("其他")),
                    "metric_id": item["metric_id"],
                }
                for item in strategy["item_list"]
            ],
        },
        "latest_anomaly_record": anomaly_record,
        "related_info": event_relation_info,
        "labels": strategy.get("labels", []),
    }
