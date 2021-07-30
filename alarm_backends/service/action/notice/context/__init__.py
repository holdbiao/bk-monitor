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
from typing import List, Dict

from django.db.models import Max
from django.utils.functional import cached_property

from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.service.action.notice.utils import get_display_dimensions, get_display_targets
from bkmonitor.models import AlertCollect, AnomalyRecord, Event, EventAction

logger = logging.getLogger("action")


class NoticeContext(object):
    """
    通知上线文
    """

    Fields = [
        "notice_way",
        "content_template",
        "event_infos",
        "user_content",
        "target",
        "alarm",
        "event",
        "anomaly_record",
        "content",
        "strategy",
        "business",
    ]

    DEFAULT_TEMPLATE = (
        "{{content.level}}\n"
        "{{content.begin_time}}\n"
        "{{content.time}}\n"
        "{{content.duration}}\n"
        "{{content.target_type}}\n"
        "{{content.data_source}}\n"
        "{{content.content}}\n"
        "{{content.current_value}}\n"
        "{{content.biz}}\n"
        "{{content.target}}\n"
        "{{content.dimension}}\n"
        "{{content.detail}}\n"
        "{{content.related_info}}\n"
    )

    def __init__(self, notice_way, event_actions: List[Dict], alert_collect):
        self.notice_way = notice_way
        self.event_actions = event_actions
        self.alert_collect = alert_collect  # type: AlertCollect
        self.user_content = ""
        self.limit = False

    @cached_property
    def events(self):
        event_ids = [event_action["event_id"] for event_action in self.event_actions]
        return Event.objects.filter(event_id__in=event_ids)

    @cached_property
    def event(self):
        return self.events[0]

    @cached_property
    def anomaly_record(self):
        return self.event.latest_anomaly_record

    @cached_property
    def event_action(self):
        return EventAction.objects.get(id=self.event_actions[0]["id"])

    @cached_property
    def event_infos(self):
        strategy_cache = {}
        latest_anomaly_records = {}

        # 查询时间的最新异常点
        event_ids = {event_action["event_id"] for event_action in self.event_actions}
        records = (
            AnomalyRecord.objects.filter(event_id__in=event_ids).values("event_id").annotate(latest_record_id=Max("id"))
        )
        latest_records = AnomalyRecord.objects.filter(id__in=[record["latest_record_id"] for record in records])
        for record in latest_records:
            latest_anomaly_records[record.event_id] = record

        infos = []
        # 最多展示90条
        for event in self.events[:90]:
            try:
                if event.strategy_id not in strategy_cache:
                    strategy_cache[event.strategy_id] = (
                        StrategyCacheManager.get_strategy_by_id(event.strategy_id) or event.origin_config
                    )
                strategy = strategy_cache[event.strategy_id]

                # 获取当前值
                latest_anomaly_record = latest_anomaly_records.get(event.event_id)
                current_value = (
                    latest_anomaly_record.origin_alarm["data"]["value"]
                    if latest_anomaly_record
                    else event.origin_alarm["data"]["value"]
                )

                display_dimensions = get_display_dimensions(event, strategy)
                display_targets = get_display_targets(event, strategy)

                infos.append(
                    {
                        "id": event.id,
                        "name": strategy["strategy_name"],
                        "target": ",".join(display_targets) or "-",
                        "dimension": ",".join(display_dimensions) or "-",
                        "current_value": current_value or "-",
                    }
                )
            except Exception as e:
                logger.exception(e)

        return infos

    @cached_property
    def alarm(self):
        from .alarm import Alarm

        return Alarm(self)

    @cached_property
    def target(self):
        from .target import Target

        return Target(self)

    @cached_property
    def business(self):
        return self.target.business

    @cached_property
    def strategy(self):
        """
        告警策略
        """
        return Strategy(self.event.strategy_id)

    @cached_property
    def content(self):
        """
        通知内容变量
        """
        from .content import DimensionCollectContent, MultiStrategyCollectContent

        if self.alert_collect.collect_type == "DIMENSION":
            return DimensionCollectContent(self)
        elif self.alert_collect.collect_type == "MULTI_STRATEGY":
            return MultiStrategyCollectContent(self)
        return None

    def get_default_template(self, notice_type):
        if notice_type == "recovery":
            # 恢复通知不展示异常数据
            return self.DEFAULT_TEMPLATE.replace("{{content.content}}\n", "")
        return self.DEFAULT_TEMPLATE

    @cached_property
    def content_template(self):
        """
        自定义告警内容模板
        """
        notice_type = self.event_action.operate.split("_")[0].lower()
        template = self.event_action.extend_info["action"]["notice_template"].get(notice_type + "_template")
        if not template:
            template = self.get_default_template(notice_type)
        return template

    def get_dictionary(self):
        result = {}
        for field in self.Fields:
            try:
                result[field] = getattr(self, field)
            except Exception as e:
                result[field] = None
                logger.exception(
                    "EventAction({}) create context field({}) error, {}".format(self.event_action.id, field, e)
                )
        return result


class BaseContextObject(object):
    def __init__(self, parent):
        self.parent = parent  # type: NoticeContext
