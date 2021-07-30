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


import json
import logging
import time

import six.moves.cPickle
from celery.task import task

from alarm_backends.core.cache.key import (
    EVENT_EXTEND_CACHE_KEY,
    EVENT_EXTEND_ID_CACHE_KEY,
    SERVICE_LOCK_EVENT,
    SERVICE_LOCK_PULL_TRIGGER,
    TRIGGER_EVENT_LIST_KEY,
    EVENT_ID_CACHE_KEY,
)
from alarm_backends.core.lock.service_lock import service_lock, share_lock
from alarm_backends.core.storage.redis_cluster import setup_client
from alarm_backends.service.event.generator.processor import EventGeneratorProcessor
from bkmonitor.models import AnomalyRecord, EventAction, CacheNode, Event
from core.errors.alarm_backends import LockError

logger = logging.getLogger("event.generator")

# 数据拉取超时
DATA_FETCH_TIMEOUT = 5
EVENT_MAX_PULL_LENGTH = 5000


@share_lock()
def update_event_action_from_cache():
    cache_extend_id_keys = EVENT_EXTEND_ID_CACHE_KEY.get_key()
    event_action_ids = EVENT_EXTEND_ID_CACHE_KEY.client.smembers(cache_extend_id_keys)
    for event_action_id in event_action_ids:
        extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=event_action_id)
        cache_extend_info = EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys)
        if not cache_extend_info:
            EVENT_EXTEND_ID_CACHE_KEY.client.srem(cache_extend_id_keys, event_action_id)
            continue
        cache_extend_info = json.loads(cache_extend_info)
        need_insert = cache_extend_info["need_insert"]
        if need_insert:
            EventAction.objects.filter(id=event_action_id).update(extend_info=cache_extend_info["extend_info"])
            cache_extend_info["need_insert"] = False
            EVENT_EXTEND_CACHE_KEY.client.set(
                extend_cache_keys, json.dumps(cache_extend_info), ex=EVENT_EXTEND_CACHE_KEY.ttl
            )


@share_lock()
def sync_event_cache():
    """
    将db的未恢复事件和redis中的未恢复事件ID进行同步
    """
    nodes = CacheNode.objects.all()
    backend = EVENT_ID_CACHE_KEY.backend
    for node in nodes:
        client = setup_client(node, backend)
        check_key = EVENT_ID_CACHE_KEY.key_prefix
        check_key += "."
        check_key += EVENT_ID_CACHE_KEY.key_tpl.format(strategy_id="*", item_id="*", dimensions_md5="*")
        to_be_checked = client.keys(check_key)
        logger.info("[sync_event_cache]: check {} get total {} event_ids".format(node, len(to_be_checked)))
        if not to_be_checked:
            continue
        event_ids = client.mget(to_be_checked)
        need_check = Event.objects.filter(
            event_id__in=event_ids, status__in=[Event.EventStatus.RECOVERED, Event.EventStatus.CLOSED]
        ).exists()
        if not need_check:
            continue
        for key, event_id in zip(to_be_checked, event_ids):
            if not event_id:
                continue
            event = Event.objects.filter(event_id=event_id).first()
            if not event:
                client.delete(key)
                logger.info("[sync_event_cache]: clean invalid key {}, event({}) not exists".format(key, event.id))
                continue
            if event.status in [Event.EventStatus.RECOVERED, Event.EventStatus.CLOSED]:
                client.delete(key)
                logger.info("[sync_event_cache]: clean invalid key {}, event({}) status changed".format(key, event.id))


def run_generator():
    with service_lock(SERVICE_LOCK_PULL_TRIGGER):
        anomaly_event_list = TRIGGER_EVENT_LIST_KEY.client.lrange(
            TRIGGER_EVENT_LIST_KEY.get_key(), -EVENT_MAX_PULL_LENGTH, -1
        )
        TRIGGER_EVENT_LIST_KEY.client.ltrim(TRIGGER_EVENT_LIST_KEY.get_key(), 0, -len(anomaly_event_list) - 1)

    if not anomaly_event_list:
        time.sleep(1)
        return
    anomaly_records = []
    for anomaly_event_json in reversed(anomaly_event_list):
        try:
            anomaly_event = six.moves.cPickle.loads(anomaly_event_json.encode("latin1"))
        except Exception as e:
            logger.exception("cPick.loads data error，reason：{}，origin data：{}".format(e, anomaly_event_json))
            continue

        try:
            processor = EventGeneratorProcessor(anomaly_event)
            if processor.event_id:
                for anomaly_record in anomaly_event["anomaly_records"]:
                    if anomaly_record.anomaly_id in anomaly_event["event_record"]["trigger"]["anomaly_ids"]:
                        anomaly_record.event_id = processor.event_id
            anomaly_records += anomaly_event["anomaly_records"]
        except Exception as e:
            logger.exception("anomaly_event process error，reason：{}，anomaly_event data：{}".format(e, anomaly_event))
            continue
        handle_event.delay(processor, anomaly_event_json)
    if anomaly_records:
        AnomalyRecord.objects.ignore_blur_create(anomaly_records, batch_size=200)


@task(ignore_result=True, queue="celery_action")
def handle_event(processor, anomaly_event_json):
    logger.info("[start] strategy({}), anomaly({})".format(processor.strategy_id, processor.new_event_id))
    try:
        with service_lock(
            SERVICE_LOCK_EVENT, strategy_id=processor.strategy_id, dimensions_md5=processor.dimensions_md5
        ):
            processor.process()
    except LockError:
        logger.info(
            "[get server lock fail] strategy({}), dimensions_md5({}). will process later".format(
                processor.strategy_id, processor.dimensions_md5
            )
        )
        TRIGGER_EVENT_LIST_KEY.client.delay("rpush", TRIGGER_EVENT_LIST_KEY.get_key(), anomaly_event_json, delay=1)
    except Exception as e:
        logger.exception(
            "[process error] strategy({}), anomaly({})。reason：{}".format(
                processor.strategy_id, processor.new_event_id, e
            )
        )

    logger.info("[end] strategy({}), anomaly({})".format(processor.strategy_id, processor.new_event_id))
