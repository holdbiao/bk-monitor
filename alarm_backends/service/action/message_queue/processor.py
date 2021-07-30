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

from django.conf import settings

from alarm_backends.core.i18n import i18n
from alarm_backends.service.action.utils import get_notice_message
from bkmonitor.models import Event, EventAction

from .client import get_client

logger = logging.getLogger("action")


class MessageQueueProcessor(object):
    """
    消息队列处理器
    """

    def __init__(self, event_action_id):
        if not settings.ENABLE_MESSAGE_QUEUE or not settings.MESSAGE_QUEUE_DSN:
            return

        self.client = get_client(settings.MESSAGE_QUEUE_DSN)
        self.event_action = EventAction.objects.get(id=event_action_id)
        self.event = Event.objects.get(event_id=self.event_action.event_id)
        i18n.set_biz(self.event.bk_biz_id)

    def execute(self):
        if not settings.ENABLE_MESSAGE_QUEUE or not settings.MESSAGE_QUEUE_DSN:
            return

        self.client.send(json.dumps(get_notice_message(self.event, self.event_action)))
