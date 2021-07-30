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

from alarm_backends.core.handlers import base
from alarm_backends.service.event import EventType
from alarm_backends.service.event.generator.tasks import run_generator
from alarm_backends.service.event.manager.tasks import run_manager

logger = logging.getLogger("event")


class EventHandler(base.BaseHandler):
    def __init__(self, event_type, *args, **kwargs):
        self.event_type = event_type
        super(EventHandler, self).__init__(*args, **kwargs)

    def handle(self):
        if self.event_type == EventType.GENERATOR:
            run_generator()
        elif self.event_type == EventType.MANAGER:
            run_manager()
