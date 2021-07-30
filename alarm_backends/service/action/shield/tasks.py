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

from celery.task import task
from django.utils.translation import ugettext as _

from alarm_backends.service.action.shield import ShieldManager
from alarm_backends.service.action.shield.shield_obj import ShieldObj
from alarm_backends.service.scheduler.tasks import perform_sharding_task
from bkmonitor.models import Event, Shield
from bkmonitor.utils import time_tools

logger = logging.getLogger("action")


def check_and_send_shield_notice():
    """
    检查当前屏蔽配置，发送屏蔽开始/结束通知
    """

    # 获取目标任务列表
    target_ids = Shield.objects.filter(
        is_enabled=True, is_deleted=False, failure_time__gte=time_tools.now()
    ).values_list("id", flat=True)

    perform_sharding_task(list(target_ids), do_check_and_send_shield_notice, num_per_task=10)


# sharded task
@task(ignore_result=True, queue="celery_cron")
def do_check_and_send_shield_notice(ids):
    shield_configs = list(
        Shield.objects.filter(
            id__in=ids, is_enabled=True, is_deleted=False, failure_time__gte=time_tools.now()
        ).values()
    )

    logger.info(_("[屏蔽通知] 开始处理。拉取到 {} 条屏蔽配置等待检测").format(len(shield_configs)))
    # TODO: 确定是否需要加锁，防止重复通知
    notice_config_ids = set()
    for shield_config in shield_configs:
        shield_obj = ShieldObj(shield_config)
        config_id = shield_obj.config["id"]
        try:
            start_notice_result, end_notice_result = shield_obj.check_and_send_notice()
        except Exception as e:
            logger.info(_("[屏蔽通知] shield({}) 处理异常，原因: {}").format(config_id, e))
            continue
        if start_notice_result:
            notice_config_ids.add(config_id)
            logger.info(_("[屏蔽通知] shield({}) 发送屏蔽开始通知，发送结果: {}").format(config_id, start_notice_result))
        if end_notice_result:
            notice_config_ids.add(config_id)
            logger.info(_("[屏蔽通知] shield({}) 发送屏蔽结束通知，发送结果: {}").format(config_id, end_notice_result))

    logger.info(_("[屏蔽通知] 结束处理。有 {} 条屏蔽告警发送了通知").format(len(notice_config_ids)))
    return notice_config_ids


@task(ignore_result=True, queue="celery_cron")
def update_event_shield_status():
    """
    更新事件屏蔽状态
    """
    events = Event.objects.filter(notify_status__gte=0, status=Event.EventStatus.ABNORMAL)

    no_shielded_event_ids = []
    shielded_event_ids = defaultdict(list)

    for event in events:
        is_shielded, shielder = ShieldManager.shield(event)
        if event.is_shielded != is_shielded or (shielder and shielder.type != event.shield_type):
            if is_shielded:
                shielded_event_ids[shielder.type].append(event.id)
            else:
                no_shielded_event_ids.append(event.id)

    for shield_type, event_ids in list(shielded_event_ids.items()):
        Event.objects.filter(id__in=event_ids).update(is_shielded=True, shield_type=shield_type)
    if no_shielded_event_ids:
        Event.objects.filter(id__in=no_shielded_event_ids).update(is_shielded=False)
