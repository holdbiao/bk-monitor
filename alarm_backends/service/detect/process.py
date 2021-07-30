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
import time

import six
from django.conf import settings
from django.utils.translation import ugettext as _

from alarm_backends.core.cache import key
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.core.i18n import i18n
from alarm_backends.core.lock.service_lock import service_lock
from alarm_backends.service.detect import DataPoint

logger = logging.getLogger("detect")


class DetectProcess(object):
    def __init__(self, strategy_id):
        self.strategy_id = strategy_id
        self.inputs = {}
        self.outputs = {}
        self.strategy = Strategy(strategy_id)
        i18n.set_biz(self.strategy.bk_biz_id)
        self.is_busy = False

    def pull_data(self, item, inputs=None):
        """
        :return: [datapoint, …]
        {
            "record_id":"f7659f5811a0e187c71d119c7d625f23",
            "value":1.38,
            "values":{
                "timestamp":1569246480,
                "load5":1.38
            },
            "dimensions":{
                "ip":"10.0.0.1"
            },
            "time":1569246480
        }
        """
        self.inputs[item.id] = []
        if inputs is not None:
            self.inputs[item.id].extend(inputs)
            return
        # pull data
        data_channel = key.DATA_LIST_KEY.get_key(strategy_id=self.strategy_id, item_id=item.id)
        client = key.DATA_LIST_KEY.client

        total_points = client.llen(data_channel)
        assert settings.SQL_MAX_LIMIT > 0
        offset = min([total_points, settings.SQL_MAX_LIMIT])
        if offset == 0:
            logger.info(_("[detect] strategy({}) item({}) 暂无待检测数据").format(self.strategy_id, item.id))
            return
        if offset == settings.SQL_MAX_LIMIT:
            self.is_busy = True
            logger.error(
                _("[detect] strategy({}) item({}) 待检测数据量达到配置值" "(SQL_MAX_LIMIT){}，部分数据可能存在处理延时").format(
                    self.strategy_id, item.id, settings.SQL_MAX_LIMIT
                )
            )

        records = client.lrange(data_channel, -offset, -1)

        unexpected_record_count = 0
        last_unexpected_record = None
        if records:
            client.ltrim(data_channel, 0, -offset - 1)
            # 队列左进右出，lrange 取出时需要做一次倒序才能保证先进先出
            for record in reversed(records):
                try:
                    data_point = DataPoint(json.loads(record), item)
                    # fill data point into inputs list
                    self.inputs[item.id].append(data_point)
                except ValueError:
                    unexpected_record_count += 1
                    last_unexpected_record = record
            if unexpected_record_count > 0:
                logger.error(
                    _("[detect] strategy({}) item({}) 发现非期望格式的待检测数据{}条," " 其中之一: {}").format(
                        self.strategy_id, item.id, unexpected_record_count, last_unexpected_record
                    )
                )

            logger.info(
                _("[detect] strategy({}) item({}) 拉取数据({})条").format(
                    self.strategy_id, item.id, len(self.inputs[item.id])
                )
            )

    def handle_data(self, item):
        # detect data
        data_points = self.inputs[item.id]
        self.outputs[item.id] = item.detect(data_points)

    def push_data(self):
        # detect.anomaly.signal: 异常信号队列
        # detect.anomaly.list.{strategy_id}.{item_id}.{level}: 异常结果信息队列
        anomaly_count = 0
        anomaly_signal_list = []
        pipeline = key.ANOMALY_LIST_KEY.client.pipeline(transaction=False)
        for item_id, outputs in six.iteritems(self.outputs):
            if outputs:
                outputs_data = [json.dumps(i) for i in outputs]
                anomaly_count += len(outputs_data)
                anomaly_signal_list.append(
                    "{strategy_id}.{item_id}".format(strategy_id=self.strategy_id, item_id=item_id)
                )

                anomaly_queue_key = key.ANOMALY_LIST_KEY.get_key(strategy_id=self.strategy_id, item_id=item_id)
                pipeline.lpush(anomaly_queue_key, *outputs_data)
                pipeline.expire(anomaly_queue_key, key.ANOMALY_LIST_KEY.ttl)

        if anomaly_signal_list:
            anomaly_signal_key = key.ANOMALY_SIGNAL_KEY.get_key()
            pipeline.lpush(anomaly_signal_key, *anomaly_signal_list)
            pipeline.expire(anomaly_signal_key, key.ANOMALY_SIGNAL_KEY.ttl)
            pipeline.execute()

        if any(self.inputs.values()):
            logger.info(_("[detect] strategy({}) 异常检测完成: 异常记录数({})").format(self.strategy_id, anomaly_count))

    def process(self):
        with service_lock(key.SERVICE_LOCK_DETECT, strategy_id=self.strategy_id):
            start_at = time.time()
            logger.info("[detect] strategy({}) processing start".format(self.strategy_id))
            self.strategy.gen_strategy_snapshot()
            for item in self.strategy.items:
                self.pull_data(item)
                self.handle_data(item)
            self.push_data()
            logger.info("[detect] strategy({}) processing end in {}".format(self.strategy_id, time.time() - start_at))
