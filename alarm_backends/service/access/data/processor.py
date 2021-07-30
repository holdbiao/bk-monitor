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
from datetime import datetime, timedelta

import arrow
import pytz
from django.conf import settings
from django.utils.functional import cached_property

from alarm_backends import constants
from alarm_backends.core.cache import key, clear_mem_cache
from alarm_backends.core.cache.hash_ring import HashRingResult
from alarm_backends.core.cache.key import ACCESS_END_TIME_KEY
from alarm_backends.core.cache.result_table import ResultTableCacheManager
from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.control.checkpoint import Checkpoint
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.core.storage.kafka import KafkaQueue
from alarm_backends.service.access import base
from alarm_backends.service.access.data.duplicate import Duplicate
from alarm_backends.service.access.data.filters import ExpireFilter, RangeFilter, HostStatusFilter
from alarm_backends.service.access.data.fullers import TopoNodeFuller
from alarm_backends.service.access.data.records import DataRecord
from bkmonitor.data_source import DataSource
from bkmonitor.utils.common_utils import get_local_ip
from constants.data_source import DataSourceLabel, DataTypeLabel

IP = get_local_ip()
logger = logging.getLogger("access.data")


class BaseAccessDataProcess(base.BaseAccessProcess):
    def __init__(self, *args, **kwargs):
        super(BaseAccessDataProcess, self).__init__(*args, **kwargs)

        self.add_filter(RangeFilter())
        self.add_filter(ExpireFilter())
        self.add_filter(HostStatusFilter())

        self.add_fuller(TopoNodeFuller())

    def post_handle(self):
        # 释放主机信息本地内存
        clear_mem_cache("host_cache")

    def pull(self):
        pass

    def _push(self, item, record_list, output_client=None, data_list_key=None):
        """
        :summary: 推送单个item的数据到检测队列或无数据待检测队列
        :param item
        :param record_list
        :param output_client
        :param data_list_key：数据队列，默认为 key.DATA_LIST_KEY
        """
        data_list_key = data_list_key or key.DATA_LIST_KEY
        client = output_client or data_list_key.client
        output_key = data_list_key.get_key(strategy_id=item.strategy.strategy_id, item_id=item.id)
        queue_length = client.llen(output_key)
        # 超过最大检测长度10倍(50w)说明detect模块处理能力不足,数据将被丢弃。
        if queue_length > settings.SQL_MAX_LIMIT * 10:
            msg = (
                f"Critical: strategy({item.strategy.strategy_id}), item({item.id})"
                f"The number of ({output_key}) records to be detected has "
                f"exceeded {queue_length}/{settings.SQL_MAX_LIMIT * 10}. "
                f"Please check if the detect process is running normally."
            )
            raise Exception(msg)

        pipeline = client.pipeline(transaction=False)
        for record in record_list:
            pipeline.lpush(output_key, json.dumps(record.data))
        pipeline.expire(output_key, data_list_key.ttl)
        pipeline.execute()

        logger.info(
            "output_key({output_key}) "
            "strategy({strategy_id}), item({item_id}), "
            "push records({records_length}).".format(
                output_key=output_key,
                strategy_id=item.strategy.strategy_id,
                item_id=item.id,
                records_length=len(record_list),
            )
        )

    def push(self, output_client=None):
        """
        推送格式化后的数据到 detect 和 nodata 中(按单个策略，单个item项，写入不同的队列)
        """
        pending_to_push = {}
        item_id_to_item = {}
        for record in self.record_list:
            for item in record.items:
                item_id = item.id
                pending_to_push.setdefault(item_id, [])
                item_id_to_item[item_id] = item

                if record.is_retains[item_id]:
                    pending_to_push[item_id].append(record)

        strategy_ids = set()
        for item_id, record_list in list(pending_to_push.items()):
            item = item_id_to_item[item_id]
            if record_list:
                strategy_ids.add(item.strategy.strategy_id)
                self._push(item, record_list, output_client)

            if item.no_data_config["is_enabled"]:
                self._push(item, self.record_list, output_client, key.NO_DATA_LIST_KEY)

        if self.record_list:
            client = output_client or key.DATA_SIGNAL_KEY.client
            if strategy_ids:
                client.lpush(key.DATA_SIGNAL_KEY.get_key(), *list(strategy_ids))
            client.expire(key.DATA_SIGNAL_KEY.get_key(), key.DATA_SIGNAL_KEY.ttl)


class AccessDataProcess(BaseAccessDataProcess):
    def __init__(self, strategy_group_key, *args, **kwargs):
        super(AccessDataProcess, self).__init__(strategy_group_key, *args, **kwargs)

        self.strategy_group_key = strategy_group_key

    def __str__(self):
        return "{}:strategy_group_key({})".format(self.__class__.__name__, self.strategy_group_key)

    @cached_property
    def items(self):
        data = []
        records = StrategyCacheManager.get_strategy_group_detail(self.strategy_group_key)
        for strategy_id, item_ids in list(records.items()):
            strategy_id = int(strategy_id)
            strategy = Strategy(strategy_id)
            for item in strategy.items:
                item_one = item.data_type_label in [DataTypeLabel.TIME_SERIES, DataTypeLabel.LOG]
                item_two = (
                    item.data_source_label == DataSourceLabel.CUSTOM and item.data_type_label == DataTypeLabel.EVENT
                )
                if item.id in item_ids and (item_one or item_two):
                    data.append(item)
        return data

    @staticmethod
    def get_max_local_time(records):
        """
        获取最大数据落地时间并剔除该字段
        """
        max_local_time = arrow.get(0).datetime
        for record in records:
            local_time = record.pop("_localTime", None)
            if not local_time:
                continue

            local_time = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            if local_time > max_local_time:
                max_local_time = local_time

        # localTime不是UTC时间，而是计算平台的机器时间
        max_local_time += timedelta(hours=settings.BKDATA_LOCAL_TIMEZONE_OFFSET)
        return max_local_time

    def pull(self):
        """
        1. 根据策略配置获取到需要拉取的数据
        2. 格式化数据，增加记录ID
        """
        if not self.items:
            return

        # 拉取一次数据，默认相同查询方法的数据拉取状态保持一致
        first_item = self.items[0]
        agg_interval = first_item.rt_query_config["agg_interval"]

        min_last_checkpoint = min([i.item_config["update_time"] for i in self.items])
        checkpoint = Checkpoint(self.strategy_group_key).get(min_last_checkpoint)
        checkpoint = checkpoint // agg_interval * agg_interval

        now_timestamp = arrow.utcnow().timestamp

        # 由于存在入库延时问题，每次多往前拉取settings.NUM_OF_COUNT_FREQ_ACCESS个周期的数据
        from_timestamp = checkpoint - settings.NUM_OF_COUNT_FREQ_ACCESS * agg_interval

        until_timestamp = None
        # 计算平台类型尝试获取上次未处理完的时间
        if first_item.data_source_label == DataSourceLabel.BK_DATA:
            end_time_key = ACCESS_END_TIME_KEY.get_key(group_key=self.strategy_group_key)
            client = ACCESS_END_TIME_KEY.client

            until_timestamp = client.get(end_time_key)
            if until_timestamp:
                client.delete(end_time_key)
                until_timestamp = int(until_timestamp)
            else:
                until_timestamp = 0

        if not until_timestamp:
            # 非计算平台数据源：
            # 由于存在入库延时问题，SUM等聚合方式最后一个点的结果会不准确，所以后台检测往前推10秒
            # 保证查询时间范围是< until_timestamp 而不是<=即可
            interval_step = min([agg_interval, constants.CONST_MINUTES])
            # 秒级监控周期，时间偏移容忍度调整为5s。
            time_shift = 10 if interval_step >= constants.CONST_MINUTES else 5
            until_timestamp = (now_timestamp - time_shift) // interval_step * interval_step

        if from_timestamp > until_timestamp:
            return

        # 计算平台指标查询localTime
        if first_item.data_source_label == DataSourceLabel.BK_DATA:
            first_item.data_source.metrics.append({"field": "localTime", "method": "MAX", "alias": "_localTime"})

        # 如果存在高级过滤条件，则条件置为空
        for condition in first_item.data_source.where:
            if condition["method"] in DataSource.ADVANCE_CONDITION_METHOD:
                first_item.data_source.where = []
                break

        try:
            item_records = first_item.query_record(from_timestamp, until_timestamp)
        except Exception as e:  # noqa
            logger.exception(
                "strategy_group_key({strategy_group_key}) query records error, {err}".format(
                    strategy_group_key=self.strategy_group_key, err=e
                )
            )
            item_records = []

        # 如果最大的localTime离得太近，那就存下until_timestamp，下次再拉取数据
        if first_item.data_source_label == DataSourceLabel.BK_DATA:
            max_local_time = self.get_max_local_time(item_records)
            first_item.data_source.metrics = [m for m in first_item.data_source.metrics if m["field"] != "localTime"]
            if now_timestamp - max_local_time.timestamp() <= settings.BKDATA_LOCAL_TIME_THRESHOLD:
                ACCESS_END_TIME_KEY.client.set(
                    ACCESS_END_TIME_KEY.get_key(group_key=self.strategy_group_key),
                    str(until_timestamp),
                    ex=ACCESS_END_TIME_KEY.ttl,
                )
                logging.info(
                    f"skip access {self.strategy_group_key} data because data local time is too close."
                    f"now: {now_timestamp}, local time: {max_local_time.timestamp()}"
                )
                return

        records = []
        dup_obj = Duplicate(self.strategy_group_key)
        duplicate_counts = none_point_counts = 0
        for record in reversed(item_records):
            point = DataRecord(self.items, record)
            if point.value is not None:
                # 去除重复数据
                if dup_obj.is_duplicate(point):
                    duplicate_counts += 1
                    continue
                dup_obj.add_record(point)
                records.append(point)
            else:
                none_point_counts += 1

        dup_obj.refresh_cache()
        self.record_list = records

        # 日志记录按strategy + item 来记录，方便问题排查
        for item in self.items:
            logger.info(
                "strategy({strategy_id}),item({item_id}),"
                "total_records({total}),"
                "access records({records_length}),"
                "duplicate({duplicate_counts}),"
                "none_point_counts({none_point_counts}),"
                "strategy_group_key({strategy_group_key}),"
                "time range({from_datetime} - {until_datetime})".format(
                    strategy_id=item.strategy.id,
                    item_id=item.id,
                    total=len(item_records),
                    records_length=len(records),
                    duplicate_counts=duplicate_counts,
                    none_point_counts=none_point_counts,
                    strategy_group_key=self.strategy_group_key,
                    from_datetime=arrow.get(from_timestamp).strftime(constants.STD_LOG_DT_FORMAT),
                    until_datetime=arrow.get(until_timestamp).strftime(constants.STD_LOG_DT_FORMAT),
                )
            )

    def push(self, output_client=None):
        super(AccessDataProcess, self).push(output_client=output_client)

        checkpoint = Checkpoint(self.strategy_group_key)
        last_checkpoint = max([checkpoint.get()] + [r.time for r in self.record_list])
        if last_checkpoint > 0:
            # 记录检测点 下次从检测点开始重新检查
            checkpoint.set(last_checkpoint)

        logger.info(
            "strategy_group_key({}), push records({}), last_checkpoint({})".format(
                self.strategy_group_key,
                len(self.record_list),
                arrow.get(last_checkpoint).strftime(constants.STD_LOG_DT_FORMAT),
            )
        )


class AccessRealTimeDataProcess(BaseAccessDataProcess):
    EXCLUDE_AGG_DIMENSION = {"bk_cmdb_level", "bk_supplier_id"}

    def __init__(self, rt_id, strategies, targets=None):
        super(AccessRealTimeDataProcess, self).__init__()
        self.rt_id = rt_id
        self.rt_info = (
            ResultTableCacheManager.get_result_table_by_id(DataSourceLabel.BK_MONITOR_COLLECTOR, self.rt_id) or {}
        )

        agg_dimension = {field["field_name"] for field in self.rt_info.get("fields", []) if field["is_dimension"]}
        self.agg_dimension = list(agg_dimension - self.EXCLUDE_AGG_DIMENSION)

        self.targets = targets or HashRingResult.get_biz_targets()

        self.strategies = {}
        strategies = strategies or {}
        for biz_id, strategy_id_list in list(strategies.items()):
            if int(biz_id) not in self.targets:
                continue

            for strategy_id in strategy_id_list:
                self.strategies.setdefault(int(biz_id), {})[strategy_id] = Strategy(strategy_id)

    def __str__(self):
        return "{}:result_table_id({})".format(self.__class__.__name__, self.rt_id)

    def flat(self, raw_data):
        """
        扁平化
        1. 数据结构转换
        2. 分策略拆分成多条DataRecord
        raw_data:
        {
            "metrics":{
                "load1":2.77,
                "load5":2.56,
                "load15":2.57
            },
            "dimensions":{
                "bk_biz_id":2,
                "bk_cmdb_level":"",
                "ip":"10.0.0.1",
                "bk_cloud_id":0,
                "bk_target_ip":"10.0.0.1",
                "bk_target_cloud_id":"0",
                "bk_supplier_id":0
            },
            "time":1573701305
        }

        standard raw_data:
        {
            "bk_target_ip":"127.0.0.1",
            "load5":2.56,
            "bk_target_cloud_id":"0",
            "time":1573701305
        }
        :param raw_data:
        :return:
        """
        data_bk_biz_id = raw_data["dimensions"].get("bk_biz_id", 0)
        strategy_dict = self.strategies.get(data_bk_biz_id)
        if not strategy_dict:
            logger.debug("abandon data(%s), not belong targets(%s)", raw_data, self.targets)
            return []

        new_record_list = []
        for strategy_id, strategy in list(strategy_dict.items()):
            standard_raw_data = {"time": raw_data["time"]}
            standard_raw_data.update(raw_data["metrics"])
            standard_raw_data.update(raw_data["dimensions"])

            item = strategy.items[0]
            item.rt_query_config["agg_dimension"] = self.agg_dimension
            new_record_list.append(DataRecord(item, standard_raw_data))
        return new_record_list

    def pull_from_kafka(self, kafka_queue, topic):
        """
        1. 从kafka拉取到数据
        2. check数据的正确性
        3. 按业务拆分数据
        3. 分业务按策略扁平化数据
        """
        try:
            kafka_queue.set_topic(topic, group_prefix="%s.0" % IP)
            result = kafka_queue.take(count=10000, timeout=1)
            for m in result:
                if not m:
                    continue

                try:
                    raw_data = json.loads(m[:-1] if m[-1] == "\x00" or m[-1] == "\n" else m)
                except Exception as e:
                    logger.warning("%s loads alarm(%s) failed", topic, m, e)
                else:
                    self.record_list.extend(self.flat(raw_data))
        except Exception as e:
            logger.warning("topic(%s) poll data failed, %s", topic, e)
        logger.info("topic(%s) poll data list(%s)", topic, len(self.record_list))

    def pull(self):
        """
        1. 根据rt_id获取到存储信息storage_info
        2. 从storage_info中提取出kafka的连接信息，topic信息等
        3. 创建好kafka消费端，拉取对应topic的数据

        storage_info format:
        {
            "storage_info":{
                "cluster_config":{
                    "cluster_name":"kafka_cluster1",
                    "is_ssl_verify":false,
                    "version":null,
                    "cluster_id":1,
                    "registered_system":"_default",
                    "custom_option":"",
                    "schema":null,
                    "domain_name":"kafka.service.consul",
                    "port":9092
                },
                "storage_config":{
                    "topic":"0bkmonitor_storage__system.load",
                    "partition":1
                },
                "auth_info":{
                    "password":"",
                    "bk_username":""
                },
                "cluster_type":"kafka"
            }
        }
        """

        storage_info = self.rt_info.get("storage_info", {})
        if storage_info:
            kfk_conf = {
                "domain": storage_info["cluster_config"]["domain_name"],
                "port": storage_info["cluster_config"]["port"],
            }
            kafka_queue = KafkaQueue(kfk_conf=kfk_conf)

            topic = storage_info["storage_config"]["topic"]
            self.pull_from_kafka(kafka_queue, topic)
        else:
            logger.warning("rt_id(%s) has no storage_info", self.rt_id)
