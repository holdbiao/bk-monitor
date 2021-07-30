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
from six.moves import map

from django.conf import settings

from alarm_backends.core.cache.hash_ring import HashRingResult
from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.handlers import base
from alarm_backends.service.access import ACCESS_TYPE_TO_CLASS, AccessType
from alarm_backends.service.access.tasks import run_access_data, run_access_real_time_data, run_access_event_handler

logger = logging.getLogger("access")


class AccessHandler(base.BaseHandler):
    """
    AccessHandler
    """

    def __init__(self, targets=None, *args, **option):
        access_type = option.get("access_type")
        if access_type not in ACCESS_TYPE_TO_CLASS:
            raise Exception("Unknown Access Type(%s)." % str(access_type))

        self.access_type = access_type
        self.targets = targets or []
        self.option = option

        super(AccessHandler, self).__init__(*args, **option)

    def handle(self):
        if self.access_type == AccessType.Data:
            # 按策略分组执行
            strategy_group_keys = StrategyCacheManager.get_strategy_group_keys()
            for strategy_group_key in strategy_group_keys:
                if (
                    set(map(str, self.targets))
                    & StrategyCacheManager.get_strategy_group_detail(strategy_group_key).keys()
                ):
                    logger.info("[access.data]publish strategy_group_key: {}".format(strategy_group_key))
                    self.run_access(run_access_data, strategy_group_key)
        elif self.access_type == AccessType.RealTimeData:
            biz_targets = set(map(int, HashRingResult.get_biz_targets()))
            rt_id_to_strategies = StrategyCacheManager.get_real_time_data_strategy_ids()
            for rt_id, biz_id_to_strategies in list(rt_id_to_strategies.items()):
                biz_ids = set(map(int, list(biz_id_to_strategies.keys())))
                if biz_targets & biz_ids:
                    self.run_access(run_access_real_time_data, rt_id, biz_id_to_strategies)

        elif self.access_type == AccessType.Event:
            # 将几种自定义事件的Data ID推入处理队列
            data_ids = [
                settings.GSE_BASE_ALARM_DATAID,
                settings.GSE_CUSTOM_EVENT_DATAID,
                settings.GSE_PROCESS_REPORT_DATAID,
            ]
            for data_id in data_ids:
                self.run_access(run_access_event_handler, data_id)

    @staticmethod
    def run_access(access_func, *args):
        access_func(*args)


class AccessCeleryHandler(AccessHandler):
    """
    AccessCeleryHandler(run by celery worker)
    """

    @staticmethod
    def run_access(access_func, *args):
        access_func.delay(*args)
