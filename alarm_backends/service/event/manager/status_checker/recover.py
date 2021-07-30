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


import bisect
import logging

import arrow
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from six.moves import range

from alarm_backends.core.cache.key import CHECK_RESULT_CACHE_KEY, EVENT_ID_CACHE_KEY, LAST_CHECKPOINTS_CACHE_KEY
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.core.detect_result import ANOMALY_LABEL
from alarm_backends.service.event.manager.status_checker.base import BaseStatusChecker
from bkmonitor.data_source import CustomEventDataSource
from bkmonitor.models import Event, EventAction
from constants.data_source import DataTypeLabel, DataSourceLabel

logger = logging.getLogger("event.manager")


class RecoverStatusChecker(BaseStatusChecker):
    """
    事件恢复判断
    """

    DEFAULT_CHECK_WINDOW_UNIT = 60
    DEFAULT_CHECK_WINDOW_SIZE = 5
    DEFAULT_TRIGGER_COUNT = 0

    def __init__(self, event, strategy=None, event_id_parser=None):
        super(RecoverStatusChecker, self).__init__(event, strategy, event_id_parser)

        self.strategy = strategy or event.origin_config
        # 计算恢复窗口时间偏移量
        item = Strategy.get_item_in_strategy(self.strategy, self.item_id)

        # 是否为事件类型告警
        self.is_event_type = item["data_type_label"] == DataTypeLabel.EVENT

        # 是否是自定义事件上报
        self.is_custom_report = (
            item["data_type_label"] == DataTypeLabel.EVENT and item["data_source_label"] == DataSourceLabel.CUSTOM
        )

        try:
            self.window_unit = item["rt_query_config"]["agg_interval"]
        except Exception:
            self.window_unit = self.DEFAULT_CHECK_WINDOW_UNIT

        try:
            self.recovery_window_size = item["algorithm_list"][0]["recovery_config"]["check_window"]
        except Exception:
            self.recovery_window_size = self.DEFAULT_CHECK_WINDOW_SIZE

        self.event_id_cache_key = EVENT_ID_CACHE_KEY.get_key(
            strategy_id=self.strategy_id, item_id=self.item_id, dimensions_md5=self.dimensions_md5
        )

        self.recovery_window_offset = self.window_unit * self.recovery_window_size

        self.now_timestamp = arrow.now().timestamp

        self.level = self.event_id_parser.level

        try:
            trigger_config = Strategy.get_trigger_configs(item)[str(self.level)]
            self.trigger_window_size = trigger_config["check_window_size"]
            self.trigger_count = trigger_config["trigger_count"]
        except Exception:
            logger.exception(
                "strategy({}), item({}) level({}) trigger_config does not exist, "
                "using default trigger config".format(self.strategy_id, self.item_id, self.level)
            )
            # 如果获取trigger失败，则将触发窗口设置为与恢复窗口一样大小
            self.trigger_window_size = self.recovery_window_size
            self.trigger_count = self.DEFAULT_TRIGGER_COUNT

        self.trigger_window_offset = self.window_unit * self.trigger_window_size - 1

    def check(self):
        return self.check_event_expired() or self.check_trigger_result() or self.check_custom_event_recovery()

    def check_event_expired(self):
        # 获取当前正在发生的事件ID
        current_event_id = EVENT_ID_CACHE_KEY.client.get(self.event_id_cache_key)

        if current_event_id != self.event_id:
            # 如果正在发生的事件ID与当前事件ID不一致，则说明事件已经过期，直接恢复
            logger.info(
                _("[处理结果] (do_recover) event({}), strategy({}) 已经过期，当前事件为: event({})，" "进行事件恢复").format(
                    self.event_id, self.strategy_id, current_event_id
                )
            )
            self.recover(_("当前维度存在更新的告警事件，告警已恢复"), remove_event_key=False)
            return True
        return False

    def check_trigger_result(self):
        """
        检测触发结果是否满足条件
        """
        if self.is_event_type:
            # 如果是事件类型告警，则使用当前时间去判断
            last_check_timestamp = self.now_timestamp
        else:
            # 如果是时序或日志类型告警，则使用最后一次上报时间判断
            last_check_timestamp = LAST_CHECKPOINTS_CACHE_KEY.client.hget(
                LAST_CHECKPOINTS_CACHE_KEY.get_key(),
                LAST_CHECKPOINTS_CACHE_KEY.get_field(
                    strategy_id=self.strategy_id,
                    item_id=self.item_id,
                    dimensions_md5=self.dimensions_md5,
                    level=self.level,
                ),
            )
            if not last_check_timestamp:
                # key 已经过期，超时恢复
                self.recover(_("在恢复检测周期内无数据上报，告警已恢复"))
                logger.info(
                    _("[处理结果] (no_data) event({}), strategy({}) 在恢复检测周期内无数据上报，进行事件恢复").format(
                        self.event.event_id, self.strategy_id
                    )
                )
                return True
            last_check_timestamp = max(
                int(last_check_timestamp),
                self.now_timestamp - settings.EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE * self.window_unit,
            )

        if self.check_result_cache(last_check_timestamp):
            # 满足恢复条件，开始恢复
            self.recover(_("连续 {} 个周期不满足触发条件，告警已恢复").format(self.recovery_window_size))
            logger.info(
                _("[处理结果] (do_recover) event({}), strategy({}) 连续 {} 个周期内不满足触发条件，进行事件恢复").format(
                    self.event.event_id, self.strategy_id, self.recovery_window_size
                )
            )
            return True

        logger.info(
            _("[处理结果] (no_recover) event({}), strategy({}) 在恢复检测周期内仍满足触发条件，不进行恢复").format(
                self.event.event_id, self.strategy_id
            )
        )
        return False

    def check_custom_event_recovery(self):
        """
        根据event_type维度判断自定义事件是恢复还是异常
        """
        if not self.is_custom_report:
            return False

        item = Strategy.get_item_in_strategy(self.strategy, self.item_id)
        datasource = CustomEventDataSource.init_by_rt_query_config(item["rt_query_config"])

        es_data, recovery_total = datasource.add_recovery_filter(datasource).query_log(
            start_time=int(self.event.begin_time.timestamp() * 1000)
        )

        # 存在恢复event则恢复
        if recovery_total > 0:
            self.recover(_("接收到自定义恢复事件，告警已恢复"))
            return True

        return False

    def check_result_cache(self, last_check_timestamp):
        """
        通过查询检测结果缓存判断事件是否达到恢复条件
        """
        # 如果有 last_check_timestamp 就需要判断是否满足触发条件
        check_cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=self.strategy_id,
            item_id=self.item_id,
            dimensions_md5=self.dimensions_md5,
            level=self.level,
        )
        # 时间范围为：最后一次上报时间 - 触发窗口偏移 - 恢复窗口偏移
        min_check_timestamp = last_check_timestamp - self.recovery_window_offset - self.trigger_window_offset
        check_results = CHECK_RESULT_CACHE_KEY.client.zrangebyscore(
            name=check_cache_key, min=min_check_timestamp, max=last_check_timestamp, withscores=True
        )

        # 取出包含异常数的个数，并排序
        check_result_timestamps = [int(score) for label, score in check_results]
        check_result_timestamps.sort()
        anomaly_timestamps = [int(score) for label, score in check_results if label.endswith(ANOMALY_LABEL)]
        anomaly_timestamps.sort()

        logger.debug(
            "[check_result_cache] event({}), strategy({}), start_time({}), end_time({}) "
            "anomaly_timestamps({})".format(
                self.event.event_id, self.strategy_id, min_check_timestamp, last_check_timestamp, anomaly_timestamps
            )
        )

        trigger_check_result = {}
        # 按照监控周期移动触发判断窗口
        current_check_end_time = last_check_timestamp
        current_check_start_time = current_check_end_time - self.trigger_window_offset
        for i in range(self.recovery_window_size):
            # 使用二分查找找到起止时间对应的下标
            start_index = bisect.bisect_left(anomaly_timestamps, current_check_start_time)
            end_index = bisect.bisect_right(anomaly_timestamps, current_check_end_time)
            anomaly_count = end_index - start_index

            if anomaly_count >= self.trigger_count:
                # 当某个窗口的异常数量大于等于触发个数，即满足了触发条件，不恢复
                return False

            # 需要校验trigger触发窗口的合法性，对于时序数据，如果检测结果数量没有大于或等于检测窗口大小，则是不合法的窗口
            if self.is_event_type:
                is_window_valid = True
                logger.debug(
                    "[check_trigger_count] event({}), strategy({}), start_time({}), end_time({}) "
                    "anomaly_count({}), data_type_label(Event)".format(
                        self.event.event_id,
                        self.strategy_id,
                        current_check_start_time,
                        current_check_end_time,
                        anomaly_count,
                    )
                )
            else:
                data_count = bisect.bisect_right(check_result_timestamps, current_check_end_time) - bisect.bisect_left(
                    check_result_timestamps, current_check_start_time
                )
                is_window_valid = data_count >= self.trigger_window_size
                logger.debug(
                    "[check_trigger_count] event({}), strategy({}), start_time({}), end_time({}) "
                    "anomaly_count({}), data_count({})".format(
                        self.event.event_id,
                        self.strategy_id,
                        current_check_start_time,
                        current_check_end_time,
                        anomaly_count,
                        data_count,
                    )
                )

            trigger_check_result[current_check_end_time] = is_window_valid

            # 未满足条件，则移动窗口，继续判断
            current_check_start_time -= self.window_unit
            current_check_end_time -= self.window_unit

        # # 如果窗口都没满足触发条件，会执行以下判断
        # # 所有的检测窗口都是合法的，才会认可本次的恢复检测结果，哪怕有一个窗口的数据是不完整的，也不允许恢复
        # is_all_window_valid = all(trigger_check_result.values())
        #
        # return is_all_window_valid

        return True

    def recover(self, message, remove_event_key=True):
        """
        事件恢复
        """
        self.event.status = Event.EventStatus.RECOVERED
        self.event.end_time = timezone.now()
        self.event.save(update_fields=["status", "end_time"])
        EventAction.objects.create(
            operate=EventAction.Operate.RECOVER,
            status=EventAction.Status.SUCCESS,
            event_id=self.event.event_id,
            message=message,
        )

        # 事件恢复的同时，创建对应动作
        self.push_actions(notice_type="recovery")

        # 删除正在产生的事件 key
        if remove_event_key:
            EVENT_ID_CACHE_KEY.client.delete(self.event_id_cache_key)
