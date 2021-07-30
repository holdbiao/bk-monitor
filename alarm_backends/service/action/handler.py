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

from alarm_backends.core.cache.key import KEY_PREFIX
from alarm_backends.core.handlers import base
from alarm_backends.core.storage.redis import Cache

logger = logging.getLogger("action")


class ActionHandler(base.BaseHandler):
    """
    动作执行
    """

    QUEUE_KEY_TEMPLATE = KEY_PREFIX + ".action.{}"

    ActionTypes = ["notice", "message_queue", "webhook"]

    def __init__(self, action_type=None, *args, **kwargs):
        super(ActionHandler, self).__init__(*args, **kwargs)
        self.redis_client = Cache("queue")
        self.action_type = action_type

    def handle(self):
        from .tasks import run_action

        action_keys = {self.QUEUE_KEY_TEMPLATE.format(action_type): action_type for action_type in self.ActionTypes}

        # 从动作队列中拉取待处理的事件
        result = self.redis_client.brpop(list(action_keys.keys()), timeout=5)
        if not result:
            return

        action_type = action_keys[result[0]]
        event_action_id = int(result[1])
        run_action.delay(action_type, event_action_id)
