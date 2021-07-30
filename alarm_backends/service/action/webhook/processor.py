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

import requests
from furl import furl
from django.conf import settings

from alarm_backends.core.cache.key import ACTION_LIST_KEY
from alarm_backends.core.i18n import i18n
from alarm_backends.service.action.utils import get_notice_message
from bkmonitor.models import Alert, Event, EventAction

logger = logging.getLogger("action")


class WebhookProcessor(object):
    """
    Webhook处理器
    """

    MAX_FAILED_TIMES = 3

    def __init__(self, event_action_id):
        self.event_action = EventAction.objects.get(id=event_action_id)
        self.event = Event.objects.get(event_id=self.event_action.event_id)
        self.webhook_configs = self.event_action.extend_info.get("webhook_configs", [])
        self.webhook_records = self.event_action.extend_info.get("webhook_records", {})

        i18n.set_biz(self.event.bk_biz_id)

    def send(self, webhook_url):
        """
        发送回调请求
        """
        result = True
        message = ""
        parsed_url = furl(webhook_url)
        webhook_url_params = {}
        webhook_url_params.update(parsed_url.args)
        post_params = {"webhook_url_params": webhook_url_params}
        post_params.update(parsed_url.args)
        post_params.update(self.message)
        try:
            r = requests.post(url=webhook_url, json=post_params, timeout=settings.WEBHOOK_TIMEOUT, verify=False)
            if r.status_code != 200:
                result = False
                content = "{}...".format(r.text[:20]) if len(r.text) > 17 else r.text
                message = "response not valid, status_code: {}, content: {}".format(r.status_code, content)
        except requests.Timeout:
            result = False
            message = "webhook request timeout"
        except Exception as e:
            result = False
            message = "webhook request failed, {}".format(e)

        return result, message

    def retry(self, failed_times):
        """
        重试，推送到延迟队列
        """

        delay_time_map = defaultdict(lambda: 0, {1: 5, 2: 10})

        ACTION_LIST_KEY.client.delay(
            "rpush",
            ACTION_LIST_KEY.get_key(action_type="webhook"),
            self.event_action.id,
            delay=delay_time_map[failed_times],
        )

    @property
    def message(self):
        """
        回调数据
        """
        return get_notice_message(self.event, self.event_action)

    def execute_webhook(self, webhook_config):
        webhook_url = webhook_config["url"]
        # 回调记录出初始化
        if webhook_url not in self.webhook_records:
            self.webhook_records[webhook_url] = {"result": False, "failed_times": 0, "alert_id": None}

        webhook_record = self.webhook_records[webhook_url]

        # 回调成功过的无需处理
        if webhook_record.get("result") or webhook_record["failed_times"] >= self.MAX_FAILED_TIMES:
            return

        failed_times = webhook_record.get("failed_times", 0)
        alert_id = webhook_record.get("alert_id")
        alert = Alert.objects.filter(id=alert_id)

        # 发送回调
        result, message = self.send(webhook_url)

        # 记录回调结果
        if not alert:
            # 获取username简短描述（webhook url 太长）
            notice_group_name = webhook_config.get("name", "")
            group_name_max_length = Alert._meta.get_field("username").max_length - 12
            validated_notice_group_name = notice_group_name[:group_name_max_length]
            if notice_group_name:
                if len(notice_group_name) > len(validated_notice_group_name):
                    # 这里预留webhook(...)长度
                    notice_group_name = f"{validated_notice_group_name}..."
                notice_group_name = f"({notice_group_name})"

            alert = Alert.objects.create(
                method="webhook",
                username=f"webhook{notice_group_name}",
                status="SUCCESS" if result else "FAILED",
                message=message,
                action_id=self.event_action.id,
                event_id=self.event.event_id,
                alert_collect_id=0,
            )
            webhook_record["alert_id"] = alert.id
        else:
            alert = alert[0]
            alert.status = "SUCCESS" if result else "FAILED"
            alert.message = message
            alert.save()

        # 更新回调记录
        webhook_record["result"] = result
        if not result:
            failed_times += 1
            webhook_record["failed_times"] = failed_times
            if failed_times >= self.MAX_FAILED_TIMES:
                logger.error(
                    "event_action({}) webhook({}) failed more than {} times, {}".format(
                        self.event_action.id, webhook_url, self.MAX_FAILED_TIMES, message
                    )
                )

    def execute(self):
        if not self.webhook_configs:
            return

        # 执行回调
        for webhook_config in self.webhook_configs:
            try:
                self.execute_webhook(webhook_config)
            except Exception as e:
                webhook_url = webhook_config["url"]
                self.webhook_records[webhook_url]["failed_times"] += 1
                logger.error("event_action({}) webhook({}) failed, {}".format(self.event_action.id, webhook_url, e))

        # 更新event_action
        self.event_action.extend_info["webhook_records"] = self.webhook_records
        EventAction.objects.filter(id=self.event_action.id).update(extend_info=self.event_action.extend_info)

        results = [webhook_record.get("result", False) for webhook_record in list(self.webhook_records.values())]

        # 更新event_action状态
        query = EventAction.objects.filter(id=self.event_action.id)
        if all(results):
            query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.SUCCESS)
            query.filter(status=EventAction.Status.FAILED).update(status=EventAction.Status.PARTIAL_SUCCESS)
        elif any(results):
            query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.PARTIAL_SUCCESS)
            query.filter(status=EventAction.Status.SUCCESS).update(status=EventAction.Status.PARTIAL_SUCCESS)
            query.filter(status=EventAction.Status.FAILED).update(status=EventAction.Status.PARTIAL_SUCCESS)
        else:
            query.filter(status=EventAction.Status.RUNNING).update(status=EventAction.Status.FAILED)
            query.filter(status=EventAction.Status.SUCCESS).update(status=EventAction.Status.PARTIAL_SUCCESS)

        # 判断是否要重试
        for webhook_record in list(self.webhook_records.values()):
            if not webhook_record["result"] and webhook_record["failed_times"] < self.MAX_FAILED_TIMES:
                self.retry(webhook_record["failed_times"])
                break
