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


import abc

import six

from alarm_backends.core.cache.key import EVENT_ID_CACHE_KEY
from alarm_backends.core.control.record_parser import EventIDParser
from alarm_backends.service.action.utils import create_actions


class BaseStatusChecker(six.with_metaclass(abc.ABCMeta, object)):
    def __init__(self, event, strategy=None, event_id_parser=None):
        """
        :param Event event: 事件对象
        """
        self.event = event
        self.event_id = self.event.event_id
        self.strategy_id = self.event.strategy_id
        self.strategy = strategy

        self.event_id_parser = event_id_parser or EventIDParser(self.event.event_id)
        self.dimensions_md5 = self.event_id_parser.dimensions_md5
        self.item_id = self.event_id_parser.item_id
        self.level = event.level

        self.event_id_cache_key = EVENT_ID_CACHE_KEY.get_key(
            strategy_id=self.strategy_id, item_id=self.item_id, dimensions_md5=self.dimensions_md5
        )

    def check(self):
        raise NotImplementedError

    def push_actions(self, notice_type):
        """
        将事件动作推送到队列中
        """
        if self.strategy:
            action_list = self.strategy["action_list"]
        else:
            action_list = self.event.origin_config["action_list"]
        create_actions(self.event.event_id, action_list, notice_type)
