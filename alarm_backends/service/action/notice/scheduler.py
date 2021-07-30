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

from celery.task import task
from django.conf import settings
from django.db.transaction import atomic
from django.utils import timezone

from alarm_backends.service.action.notice.tasks import do_create_notice_action
from alarm_backends.service.scheduler.tasks import perform_sharding_task
from bkmonitor.models import AnomalyRecord, Event, EventAction

logger = logging.getLogger("action")


@task(ignore_result=True, queue="celery_cron")
def collect_anomaly_record():
    # 设置事件异常汇总全局窗口，达到窗口触发异常汇总；
    # 设置单个收敛周期收敛窗口，达到窗口触发汇总，保留窗口值n条；
    # 收敛汇总窗口内保持前n/2，后n/2 -1，中间为汇总异常数据的记录。
    collect_window = settings.ANOMALY_RECORD_COLLECT_WINDOW
    converge_window = settings.ANOMALY_RECORD_CONVERGED_ACTION_WINDOW
    event_id_list = Event.objects.filter(notify_status__gte=0, status=Event.EventStatus.ABNORMAL).values_list(
        "event_id", flat=True
    )
    event_actions = (
        EventAction.objects.only("event_id", "operate", "create_time").filter(event_id__in=event_id_list).order_by("id")
    )
    event_action_map = {}
    for action in event_actions:
        event_action_map.setdefault(action.event_id, []).append(action)
    for event_id, actions in event_action_map.items():
        anomaly_count = sum(AnomalyRecord.objects.filter(event_id=event_id).values_list("count", flat=True))
        if anomaly_count >= collect_window:
            for index, action in enumerate(actions):
                if action.operate == action.Operate.CONVERGE:
                    start = action.create_time
                    if index + 1 < len(actions):
                        end = actions[index + 1].create_time  # 下个收敛动作的开始时间与当前收敛动作的开始时间构成时间段
                    else:
                        end = timezone.now()
                    anomaly_records = AnomalyRecord.objects.only("count").filter(
                        event_id=event_id, create_time__gte=start, create_time__lte=end
                    )
                    if not anomaly_records:
                        continue

                    count_list = [record.count for record in anomaly_records]
                    period_count = sum(count_list)
                    converged_count = max(count_list)  # count最大值一定是汇总记录
                    if period_count > converge_window:
                        _converge_record(converge_window, anomaly_records, converged_count)


def _converge_record(window, anomaly_records, converged_count):
    # 比如单个收敛动作窗口为10，则前面保留window // 2 = 5条，后面保留10-5-1=4条，中间一条作为汇总记录；
    # 当超过10条时，统计pre和post中间的条数，然后将count更新给post前的最后一条记录，并删除pre到post -2的记录。
    pre_reserved_index = window // 2 if window != 2 else 0
    post_reserved_num = _get_post_reserved_num(pre_reserved_index, window)
    post_reserved_index = len(anomaly_records) - post_reserved_num
    if post_reserved_index >= 2:
        new_count = (
            len(anomaly_records[pre_reserved_index:post_reserved_index]) + converged_count - 1
        )  # len多统计了一次汇总记录，故减1
        with atomic():
            converged_record = anomaly_records[post_reserved_index - 1]
            converged_record.count = new_count
            converged_record.save()
            anomaly_records.filter(
                id__range=[anomaly_records[pre_reserved_index].id, anomaly_records[post_reserved_index - 2].id]
            ).delete()  # post-1用作汇总记录，故删除post-2


def _get_post_reserved_num(pre_reserved_index, window):
    if window == 2:
        return 1
    return pre_reserved_index if window & 1 else (pre_reserved_index - 1)


def create_notice_action():
    """
    检测事件状态，根据通知配置推送通知操作
    1. 如果事件处于异常状态，且当前时间与上一次通知时间超过通知间隔或没有通知过，则发送异常通知
    2. 如果事件处于已恢复状态，且没有发送过恢复通知，则发送恢复通知
    """
    # 查询所有异常中的事件及其最新的事件操作记录
    target_ids = Event.objects.filter(
        notify_status__gte=0, status=Event.EventStatus.ABNORMAL, is_ack=False
    ).values_list("event_id", flat=True)

    perform_sharding_task(list(target_ids), do_create_notice_action, num_per_task=10)
