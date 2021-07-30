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

import six.moves.cPickle

from alarm_backends.core.cache.key import ANOMALY_LIST_KEY, ANOMALY_SIGNAL_KEY, TRIGGER_EVENT_LIST_KEY
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.service.trigger.checker import AnomalyChecker
from bkmonitor.models import AnomalyRecord
from core.errors.alarm_backends import StrategyNotFound

logger = logging.getLogger("trigger")


class TriggerProcessor(object):

    # 单次处理量(默认为全量处理)
    MAX_PROCESS_COUNT = 0

    def __init__(self, strategy_id, item_id):
        self.strategy_id = int(strategy_id)
        self.item_id = int(item_id)
        self.anomaly_list_key = ANOMALY_LIST_KEY.get_key(strategy_id=self.strategy_id, item_id=self.item_id)
        self.anomaly_points = []
        self.anomaly_records = []
        self.event_records = []
        # 策略快照数据
        self._strategy_snapshots = {}

    def get_strategy_snapshot(self, key):
        """
        获取配置快照
        """
        try:
            # 查询对应的key快照是否存在
            return self._strategy_snapshots[key]
        except KeyError:
            # 如果查不到内存快照，则查询redis
            snapshot = Strategy.get_strategy_snapshot_by_key(key, self.strategy_id)
            if not snapshot:
                raise StrategyNotFound({"key": key})
            self._strategy_snapshots[key] = snapshot
            return snapshot

    def pull(self):
        self.anomaly_points = ANOMALY_LIST_KEY.client.lrange(self.anomaly_list_key, -self.MAX_PROCESS_COUNT, -1)
        # 对列表做翻转，按数据从旧到新的顺序处理
        self.anomaly_points.reverse()
        if self.anomaly_points:
            ANOMALY_LIST_KEY.client.ltrim(self.anomaly_list_key, 0, -len(self.anomaly_points) - 1)
            if len(self.anomaly_points) == self.MAX_PROCESS_COUNT:
                # 拉取到的数量若等于最大数量，说明还没拉取完，下次需要再次拉取处理
                signal_key = "{strategy_id}.{item_id}".format(strategy_id=self.strategy_id, item_id=self.item_id)
                ANOMALY_SIGNAL_KEY.client.delay("rpush", ANOMALY_SIGNAL_KEY.get_key(), signal_key, delay=1)
                logger.info(
                    "[pull anomaly record] strategy({}), item({}) pull {} record."
                    "queue has data, process next time".format(self.strategy_id, self.item_id, len(self.anomaly_points))
                )
            elif self.MAX_PROCESS_COUNT:
                logger.info(
                    "[pull anomaly record] strategy({}), item({}) pull {} record".format(
                        self.strategy_id, self.item_id, len(self.anomaly_points)
                    )
                )

    def push(self):
        # 保存异常记录
        if self.anomaly_records:
            AnomalyRecord.objects.ignore_blur_create(self.anomaly_records, batch_size=200)
        # 推送事件记录到输出队列
        if self.event_records:
            pipeline = TRIGGER_EVENT_LIST_KEY.client.pipeline(transaction=False)
            trigger_event_list_key = TRIGGER_EVENT_LIST_KEY.get_key()
            for record in self.event_records:
                pipeline.lpush(trigger_event_list_key, six.moves.cPickle.dumps(record).decode("latin1"))
            pipeline.expire(trigger_event_list_key, TRIGGER_EVENT_LIST_KEY.ttl)
            pipeline.execute()

        if self.anomaly_records:
            logger.info(
                "[process result collect] strategy({}), item({}) finish."
                "create {} AnomalyRecord, {} Event".format(
                    self.strategy_id, self.item_id, len(self.anomaly_records), len(self.event_records)
                )
            )
        self.anomaly_points = []
        self.anomaly_records = []
        self.event_records = []

    def process(self):
        self.pull()
        for point in self.anomaly_points:
            try:
                self.process_point(point)
            except Exception as e:
                error_message = "[process error] strategy({}), item({}) reason: {} \norigin data: {}".format(
                    self.strategy_id, self.item_id, e, point
                )
                logger.exception(error_message)
        self.push()

    def process_point(self, point):
        point = json.loads(point)
        strategy = self.get_strategy_snapshot(point["strategy_snapshot_key"])
        checker = AnomalyChecker(point, strategy, self.item_id)
        anomaly_records, event_record = checker.check()

        # 暂存结果，最后批量保存
        if event_record:
            self.event_records.append({"anomaly_records": anomaly_records, "event_record": event_record})
        else:
            self.anomaly_records.extend(anomaly_records)
