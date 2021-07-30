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

import arrow
from django.db.models.sql import AND, OR

from alarm_backends import constants
from alarm_backends.service.access.base import Filter
from alarm_backends.service.access.event.records.base import EventRecord
from bkmonitor.utils.range import load_condition_instance

logger = logging.getLogger("access.event")


class BizIdFilter(Filter):
    def __init__(self, bk_biz_ids=None):
        self.bk_biz_ids = bk_biz_ids or []

    def filter(self, event_record):
        if event_record.bk_biz_id not in self.bk_biz_ids:
            logger.info(
                "Discard the alarm (%s) because it bk_biz_id not in "
                "biz_list(%s)" % (event_record.raw_data, self.bk_biz_ids)
            )
            return True
        return False


class StrategyFilter(Filter):
    def __init__(self, strategies=None):
        self.strategies = strategies or []

    def filter(self, event_record):
        if event_record.strategy_id not in self.strategies:
            logger.info(
                "Discard the alarm (%s) because it strategy_id(%s) not"
                " in strategies_list(%s)" % (event_record.raw_data, event_record.strategy_id, self.strategies)
            )
            return True
        return False


class ExpireFilter(Filter):
    """
    过期事件过滤器
    """

    def filter(self, event_record):
        utctime = event_record.event_time
        # 丢弃超过半个小时的告警
        if arrow.utcnow().timestamp - arrow.get(utctime).timestamp > 30 * constants.CONST_MINUTES:
            logger.info("Discard the alarm (%s) because " "it takes more than 30 minutes" % event_record.raw_data)
            return True
        else:
            return False


class ConditionFilter(Filter):
    def filter(self, event_record: EventRecord) -> bool:
        try:
            agg_condition = event_record.items[0].rt_query_config.get("agg_condition", [])
        except:  # noqa
            return False

        or_cond = []
        and_cond = []
        for cond in agg_condition:
            t = {"field": cond["key"], "method": cond["method"], "value": cond["value"]}
            connector = cond.get("condition")
            if connector:
                if connector.upper() == AND:
                    and_cond.append(t)
                elif connector.upper() == OR:
                    or_cond.append(and_cond)
                    and_cond = [t]
                else:
                    raise Exception("Unsupported connector(%s)" % connector)
            else:
                and_cond = [t]

        if and_cond:
            or_cond.append(and_cond)

        condition = load_condition_instance(or_cond)
        return not condition.is_match(event_record.filter_dimensions)
