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


import pytest

from alarm_backends.core.storage.redis import Cache
from alarm_backends.service.action.handler import ActionHandler

pytestmark = pytest.mark.django_db


class TestHandler(object):
    def test_handler(self, mock):
        with mock.patch("alarm_backends.service.action.tasks.run_action.delay"):
            client = Cache("queue")
            client.lpush(ActionHandler.QUEUE_KEY_TEMPLATE.format("notice"), 1234)

            handler = ActionHandler()
            handler.handle()

            from alarm_backends.service.action.tasks import run_action

            assert run_action.delay.call_count == 1
            assert True
