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
import time

from celery.task import task

from alarm_backends.core.cache.key import RECOVERY_CHECK_EVENT_ID_KEY, SERVICE_LOCK_RECOVERY
from alarm_backends.core.lock.service_lock import service_lock
from alarm_backends.service.event.manager.processor import EventManagerProcessor
from bkmonitor.models import Event
from core.errors.alarm_backends import LockError

logger = logging.getLogger("event.manager")


def check_abnormal_event():
    """
    拉取未恢复的事件，并将事件ID推到队列中
    """
    event_ids = Event.objects.filter(notify_status__gte=0, status=Event.EventStatus.ABNORMAL).values_list(
        "event_id", flat=True
    )
    if event_ids:
        RECOVERY_CHECK_EVENT_ID_KEY.client.sadd(RECOVERY_CHECK_EVENT_ID_KEY.get_key(), *event_ids)
        RECOVERY_CHECK_EVENT_ID_KEY.expire()
        logger.debug("[timed task] not recovery event ID: {}".format(", ".join(event_ids)))

    logger.info("[timed task] push not recovery event to detect queue，count: {}".format(len(event_ids)))
    return event_ids


def run_manager():
    event_id = RECOVERY_CHECK_EVENT_ID_KEY.client.spop(RECOVERY_CHECK_EVENT_ID_KEY.get_key())
    if not event_id:
        time.sleep(1)
        return
    handle_manager.delay(event_id)


@task(ignore_result=True, queue="celery_action")
def handle_manager(event_id):
    try:
        event = Event.objects.get(event_id=event_id)
        processor = EventManagerProcessor(event)
    except Exception as e:
        logger.exception("event_id({}) data process error, reason: {}".format(event_id, e))
        return

    logger.info("[start] strategy({}), event({})，status({})".format(processor.strategy_id, event_id, event.status))

    try:
        with service_lock(
            SERVICE_LOCK_RECOVERY, strategy_id=processor.strategy_id, dimensions_md5=processor.dimensions_md5
        ):
            processor.process()
    except LockError:
        logger.info(
            "[get service lock fail] strategy({}), dimensions_md5({}). will process later".format(
                processor.strategy_id, processor.dimensions_md5
            )
        )
        RECOVERY_CHECK_EVENT_ID_KEY.client.delay("sadd", RECOVERY_CHECK_EVENT_ID_KEY.get_key(), event_id, delay=1)
    except Exception as e:
        logger.exception("[error] strategy({}), event({}). reason: {}".format(processor.strategy_id, event_id, e))

    logger.info("[end] strategy({}), event({}), status({})".format(processor.strategy_id, event_id, event.status))
