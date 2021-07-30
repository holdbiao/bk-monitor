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

import arrow
from celery.task import task
from django.db.models import Max

from alarm_backends.constants import CONST_MINUTES
from alarm_backends.core.cache.key import ACTION_LIST_KEY
from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.service.action.utils import create_actions
from bkmonitor.models import Event, EventAction

logger = logging.getLogger("action")


# sharded task
@task(ignore_result=True, queue="celery_cron")
def do_create_notice_action(event_ids):
    logger.info(
        "--begin create notice action for events({})".format(",".join([str(event_id) for event_id in event_ids]))
    )
    events = Event.objects.filter(
        event_id__in=event_ids,
        status=Event.EventStatus.ABNORMAL,
        is_ack=False,
    )

    redis_client = ACTION_LIST_KEY.client
    latest_event_actions = (
        EventAction.objects.filter(operate="ANOMALY_NOTICE", event_id__in=[event.event_id for event in events])
        .values("event_id")
        .annotate(max_id=Max("id"))
    )

    event_action_ids = [event_action["max_id"] for event_action in latest_event_actions]

    event_actions = {
        event_action.event_id: event_action for event_action in EventAction.objects.filter(id__in=event_action_ids)
    }

    pipeline = redis_client.pipeline()
    for event in events:
        # 获取对应的策略配置
        strategy = StrategyCacheManager.get_strategy_by_id(event.strategy_id)
        if not strategy:
            strategy = event.origin_config

        action_configs = [
            action_config
            for action_config in strategy["action_list"]
            if action_config["action_type"] in ["notice", "message_queue", "webhook"]
        ]
        latest_event_action = event_actions.get(event.event_id)

        def should_notice(action):
            # 如果有上一次通知，且当前时间与上次通知时间的时间差超过通知间隔，且上次通知后产生了新的异常点，则发送通知
            # 如果没有上一次通知，则直接发送通知
            if latest_event_action:
                last_anomaly_id = latest_event_action.extend_info.get("anomaly_id")
                if event.latest_anomaly_record and event.latest_anomaly_record.anomaly_id == last_anomaly_id:
                    return False
                time_difference = (arrow.now().datetime - latest_event_action.create_time).total_seconds()
                return time_difference >= action["config"]["alarm_interval"] * CONST_MINUTES
            return True

        create_actions(event.event_id, action_configs, "anomaly", should_notice)

    pipeline.execute()
    logger.info("--end create notice action for events({})".format(",".join([str(event_id) for event_id in event_ids])))
