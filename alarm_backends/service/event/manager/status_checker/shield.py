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

from alarm_backends.service.action.shield import ShieldManager
from alarm_backends.service.event.manager.status_checker.base import BaseStatusChecker

logger = logging.getLogger("event.manager")


class ShieldStatusChecker(BaseStatusChecker):
    """
    屏蔽状态检测
    """

    def check(self):
        shield_manager = ShieldManager()
        is_shielded, shielder = shield_manager.shield(self.event)
        shield_type = shielder.type if shielder else ""

        if self.event.is_shielded != is_shielded or self.event.shield_type != shield_type:
            logger.info(
                "[process result] (shield) event({}), "
                "strategy({}) event shield status change: ({}, {}) -> ({}, {})".format(
                    self.event.event_id,
                    self.strategy_id,
                    self.event.is_shielded,
                    self.event.shield_type,
                    is_shielded,
                    shield_type,
                )
            )
            self.event.is_shielded = is_shielded
            self.event.shield_type = shield_type
            self.event.save(update_fields=["is_shielded", "shield_type"])
        return is_shielded
