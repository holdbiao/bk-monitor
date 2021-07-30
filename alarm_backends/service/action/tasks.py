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
from collections import defaultdict
from itertools import product
from typing import List, Dict, Optional
import traceback

from celery.task import task
from django.utils.translation import ugettext as _

from alarm_backends.core.cache.key import (
    NOTICE_BIZ_COLLECT_KEY,
    NOTICE_DIMENSION_COLLECT_KEY,
    NOTICE_DIMENSION_COLLECT_KEY_LOCK,
    NOTICE_BIZ_COLLECT_KEY_LOCK,
)
from alarm_backends.core.i18n import i18n
from alarm_backends.service.action.notice.context import NoticeContext
from alarm_backends.service.action.notice.send import Sender
from alarm_backends.service.action.notice.utils import collect_info_dumps
from bkmonitor.models import Alert, AlertCollect, EventAction, Event
from bkmonitor.utils.event_notify_status import NotifyStatus

logger = logging.getLogger("action")


@task(ignore_result=True, queue="celery_notice")
def send_dimension_collect_notice(collect_info, collect_type):
    """
    单维度汇总
    """
    client = NOTICE_DIMENSION_COLLECT_KEY.client
    collect_key = NOTICE_DIMENSION_COLLECT_KEY.get_key(**collect_info)
    collect_key_lock = NOTICE_DIMENSION_COLLECT_KEY_LOCK.get_key(**collect_info)

    pipeline = client.pipeline()
    pipeline.hgetall(collect_key)
    pipeline.delete(collect_key)
    if collect_type == "long":
        pipeline.delete(collect_key_lock)
    data: Dict[bytes, bytes] = pipeline.execute()[0]

    if not data:
        return

    data: Dict[str, str] = {
        (key.decode() if isinstance(key, bytes) else key): (value.decode() if isinstance(value, bytes) else value)
        for key, value in data.items()
    }

    event_actions_to_receivers = defaultdict(list)
    for receiver, event_actions in data.items():
        if not event_actions:
            continue
        event_actions_to_receivers[event_actions].append(receiver)

    for event_actions, receivers in event_actions_to_receivers.items():
        event_action_ids = [int(event_action) for event_action in event_actions.split(",")]
        send_collect_notice(receivers, event_action_ids, collect_info, "DIMENSION")


@task(ignore_result=True, queue="celery_notice")
def send_biz_collect_notice(collect_info):
    """
    业务汇总
    """
    client = NOTICE_BIZ_COLLECT_KEY.client
    collect_key = NOTICE_BIZ_COLLECT_KEY.get_key(**collect_info)
    collect_key_lock = NOTICE_BIZ_COLLECT_KEY_LOCK.get_key(**collect_info)

    pipeline = client.pipeline()
    pipeline.lrange(collect_key, 0, -1)
    pipeline.delete(collect_key)
    pipeline.delete(collect_key_lock)
    event_actions = pipeline.execute()[0]

    if not event_actions:
        return

    event_actions = [int(event_action) for event_action in event_actions]
    send_collect_notice([collect_info["receiver"]], event_actions, collect_info, "MULTI_STRATEGY")


def send_collect_notice(receivers: List[str], event_action_ids: List[int], collect_info, collect_type):
    """
    发送汇总消息
    """
    i18n.set_biz(collect_info["bk_biz_id"])
    logger.info("--begin send collect for collect_info({})".format(collect_info_dumps(collect_info)))
    logger.info(
        "send collect for event_action({})".format(
            ",".join([str(event_action_id) for event_action_id in event_action_ids])
        )
    )

    event_actions: List[Dict] = EventAction.objects.filter(id__in=event_action_ids).values("id", "event_id")
    if not event_actions:
        logger.warning(f"send collect for event_action({event_action_ids}), but event_actions_list is empty")
        logger.info("--end send collect for collect_info({})".format(collect_info_dumps(collect_info)))
        return

    # 创建通知汇总记录
    alert_collect = AlertCollect.objects.create(
        bk_biz_id=collect_info.get("bk_biz_id", 0),
        collect_key=collect_info_dumps(collect_info),
        message=_("汇总发送"),
        collect_type=collect_type,
        extend_info={},
    )
    logger.info("create alert_collect({}) collect_key({})".format(alert_collect.id, alert_collect.collect_key))

    # 通知模板变量
    context = NoticeContext(collect_info["notice_way"], event_actions, alert_collect)
    title_template_path = "notice/{notice_type}/{collect_type}/{notice_way}_title.jinja".format(
        notice_type=collect_info["notice_type"], notice_way=collect_info["notice_way"], collect_type=collect_type
    )
    content_template_path = "notice/{notice_type}/{collect_type}/{notice_way}_content.jinja".format(
        notice_type=collect_info["notice_type"], notice_way=collect_info["notice_way"], collect_type=collect_type
    )

    # 发送通知
    sender: Optional[Sender] = None
    try:
        sender = Sender(
            title_template_path=title_template_path,
            content_template_path=content_template_path,
            context=context,
        )
        notice_result = sender.send(collect_info["notice_way"], receivers)
    except Exception as e:
        logger.exception(e)
        notice_result = {receiver: {"result": False, "message": traceback.format_exc()} for receiver in receivers}

    # 记录是否是由默认模板发送
    if sender and sender.is_use_default:
        for result in notice_result.values():
            result["message"] += "(notice by default template because exception)"

    # 保存发送内容
    if sender:
        alert_collect.extend_info = {"message": sender.content}
        alert_collect.save()

    # 根据发送结果批量创建通知记录
    alert_objs = []
    event_action_alert_status = defaultdict(list)

    for notice_receiver, event_action in product(notice_result, event_actions):
        for username in notice_receiver.split(","):
            alert_objs.append(
                Alert(
                    method=collect_info["notice_way"],
                    username=username,
                    role="",
                    status="SUCCESS" if notice_result[notice_receiver]["result"] else "FAILED",
                    action_id=event_action["id"],
                    event_id=event_action["event_id"],
                    alert_collect_id=alert_collect.id,
                    message=notice_result[notice_receiver]["message"],
                )
            )
        event_action_alert_status[event_action["id"]].append(notice_result[notice_receiver]["result"])
    Alert.objects.bulk_create(alert_objs, batch_size=100)

    # 记录通知状态
    action_status_list = {"SUCCESS": [], "PARTIAL_SUCCESS": [], "FAILED": []}

    event_ids = []

    for event_action in event_actions:
        alert_status_list = event_action_alert_status[event_action["id"]]
        if all(alert_status_list):
            action_status_list["SUCCESS"].append(event_action["id"])
        elif any(alert_status_list):
            action_status_list["PARTIAL_SUCCESS"].append(event_action["id"])
        else:
            action_status_list["FAILED"].append(event_action["id"])
        event_ids.append(event_action["event_id"])

    # 批量更新EventAction的状态
    query = EventAction.objects.filter(id__in=action_status_list["SUCCESS"])
    query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.SUCCESS)
    query.filter(status=EventAction.Status.FAILED).update(status=EventAction.Status.PARTIAL_SUCCESS)

    query = EventAction.objects.filter(id__in=action_status_list["PARTIAL_SUCCESS"])
    query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.PARTIAL_SUCCESS)
    query.filter(status=EventAction.Status.SUCCESS).update(status=EventAction.Status.PARTIAL_SUCCESS)
    query.filter(status=EventAction.Status.FAILED).update(status=EventAction.Status.PARTIAL_SUCCESS)

    query = EventAction.objects.filter(id__in=action_status_list["FAILED"])
    query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.FAILED)
    query.filter(status=EventAction.Status.SUCCESS).update(status=EventAction.Status.PARTIAL_SUCCESS)

    update_event_notify_status(event_ids)

    logger.info("--end send multi collect for collect_info({})".format(collect_info_dumps(collect_info)))


def update_event_notify_status(event_ids):
    for event_id in event_ids:
        status_list = EventAction.objects.filter(event_id=event_id).values_list("status", flat=True).distinct()
        notify_status = NotifyStatus.get(status_list)
        Event.objects.filter(event_id=event_id).update(notify_status=notify_status)


@task(ignore_result=True, queue="celery_action")
def run_action(action_type, event_action_id):
    from alarm_backends.service.action.notice.processor import NoticeProcessor
    from alarm_backends.service.action.message_queue.processor import MessageQueueProcessor
    from alarm_backends.service.action.webhook.processor import WebhookProcessor

    action_processors = {
        "notice": NoticeProcessor,
        "message_queue": MessageQueueProcessor,
        "webhook": WebhookProcessor,
    }
    processor = action_processors.get(action_type)(event_action_id)
    processor.execute()
