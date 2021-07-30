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

from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.control.record_parser import EventIDParser
from alarm_backends.core.i18n import i18n
from alarm_backends.service.event.manager.status_checker import (
    CloseStatusChecker,
    RecoverStatusChecker,
    ShieldStatusChecker,
)
from bkmonitor.models import Event

logger = logging.getLogger("event.manager")


INSTALLED_CHECKERS = (
    CloseStatusChecker,
    RecoverStatusChecker,
    ShieldStatusChecker,
)

# 无数据告警恢复，在 nodata 模块处理，只要有数据就恢复，不需要在这里判断
NO_DATA_CHECKERS = (CloseStatusChecker, ShieldStatusChecker)


class EventManagerProcessor(object):
    def __init__(self, event):
        """
        :param Event event: 事件对象
        """
        self.event = event
        i18n.set_biz(self.event.bk_biz_id)

        self.strategy_id = self.event.strategy_id
        # 解析出维度MD5
        self.event_id_parser = EventIDParser(self.event.event_id)
        self.dimensions_md5 = self.event_id_parser.dimensions_md5
        self.item_id = self.event_id_parser.item_id

    def process(self):
        """
        事件状态检测的主流程
        """

        if self.event.status != Event.EventStatus.ABNORMAL:
            logger.info(
                "[process result] (ignored) event({}), strategy({}) ignored because it is not anomaly".format(
                    self.event.event_id, self.event.strategy_id
                )
            )
            return

        strategy = StrategyCacheManager.get_strategy_by_id(self.event.strategy_id)
        # 无数据告警的恢复由 nodata 模块处理
        if self.event.is_no_data:
            checkers = NO_DATA_CHECKERS
        else:
            checkers = INSTALLED_CHECKERS
        for checker_cls in checkers:
            checker = checker_cls(self.event, strategy, self.event_id_parser)
            if checker.check():
                # 如果返回了 True 的结果，则后面的检测流程不再进行
                return
