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


import copy
import json
from hashlib import md5

import arrow
import pytest
from django.test import TestCase
from mock import patch

from alarm_backends.core.cache.key import (
    ACTION_LIST_KEY,
    NOTICE_DIMENSION_COLLECT_KEY,
    NOTICE_BIZ_COLLECT_KEY,
    NOTICE_BIZ_DIMENSIONS_KEY,
    NOTICE_VOICE_COLLECT_KEY,
    NOTICE_DIMENSION_COLLECT_KEY_LOCK,
    NOTICE_BIZ_COLLECT_KEY_LOCK,
)
from alarm_backends.service.action.notice.collector import DimensionCollector, BizCollector, VoiceCollector
from bkmonitor.models import AnomalyRecord, Event, EventAction

pytestmark = pytest.mark.django_db

strategy = {
    "bk_biz_id": 2,
    "is_enabled": True,
    "update_time": 1570072047,
    "update_user": "admin",
    "name": "CPU\u603b\u4f7f\u7528\u7387",
    "scenario": "os",
    "item_list": [
        {
            "rt_query_config": {
                "agg_method": "AVG",
                "agg_dimension": ["ip", "bk_cloud_id"],
                "extend_fields": "",
                "unit_conversion": 1.0,
                "agg_condition": [],
                "result_table_id": "system.cpu_summary",
                "unit": "%",
                "metric_field": "usage",
                "agg_interval": 60,
            },
            "metric_id": "system.cpu_summary.usage",
            "name": "usage",
            "algorithm_list": [
                {
                    "algorithm_config": [{"threshold": 90, "method": "gte"}],
                    "level": 1,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 6,
                    "id": 6,
                }
            ],
            "item_id": 6,
            "data_source_label": "bk_monitor",
            "id": 6,
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "item_name": "usage",
            "data_type_label": "time_series",
        }
    ],
    "strategy_id": 6,
    "strategy_name": "CPU\u603b\u4f7f\u7528\u7387",
    "action_list": [
        {
            "notice_template": {"anomaly_template": "", "recovery_template": ""},
            "notice_group_list": [
                {
                    "notice_way": {"1": ["sms"], "3": ["weixin"], "2": ["mail"]},
                    "notice_receiver": ["group#bk_biz_maintainer", "user#layman"],
                    "id": 3,
                    "name": "\u84dd\u9cb8\u8fd0\u7ef4\u7ec4",
                }
            ],
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "id": 6,
            "action_id": 6,
        }
    ],
    "create_user": "admin",
    "source_type": "BKMONITOR",
    "create_time": 1570072047,
    "id": 6,
    "target": [
        {"ip": "10.0.1.10", "bk_supplier_id": 0, "bk_cloud_id": 0},
        {"ip": "10.0.1.11", "bk_supplier_id": 0, "bk_cloud_id": 0},
    ],
}

origin_alarm = {
    "anomaly": {
        "1": {
            "anomaly_message": "\\u5f53\\u524d\\u6307\\u6807\\u503c(77.88%) >=(1.0%)",
            "anomaly_time": "2019-10-05 14:11:05",
            "anomaly_id": "11dd36c4e45b40da6a8f436a01c781cc.1570284540.6.6.1",
        }
    },
    "trigger": {
        "anomaly_ids": [
            "11dd36c4e45b40da6a8f436a01c781cc.1570284300.6.6.1",
            "11dd36c4e45b40da6a8f436a01c781cc.1570284360.6.6.1",
            "11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        ],
        "level": "1",
    },
    "data": {
        "record_id": "11dd36c4e45b40da6a8f436a01c781cc.1570284540",
        "values": {"usage": 77.88, "time": 1570284540},
        "dimensions": {
            "ip": "10.0.1.11",
            "bk_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
        },
        "value": 77.88,
        "time": 1570284540,
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.6.1570072047",
}


class TestCollector(TestCase):
    queue_key = ACTION_LIST_KEY.get_key(action_type="notice")

    @classmethod
    def setUpClass(cls):
        super(TestCollector, cls).setUpClass()
        cls.event = Event.objects.create(
            event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
            begin_time=arrow.now().datetime,
            bk_biz_id=2,
            strategy_id=6,
            origin_alarm=origin_alarm,
            origin_config=strategy,
            level=1,
            status=Event.EventStatus.ABNORMAL,
        )

        AnomalyRecord.objects.create(
            anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284300.6.6.1",
            event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
            origin_alarm=origin_alarm,
            source_time=arrow.now().datetime,
            strategy_id=6,
        )
        AnomalyRecord.objects.create(
            anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284360.6.6.1",
            event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
            origin_alarm=origin_alarm,
            source_time=arrow.now().datetime,
            strategy_id=6,
        )
        AnomalyRecord.objects.create(
            anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
            event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
            origin_alarm=origin_alarm,
            source_time=arrow.now().datetime,
            strategy_id=6,
        )
        cls.event_action = EventAction.objects.create(
            create_time=arrow.now().datetime,
            operate=EventAction.Operate.ANOMALY_NOTICE,
            extend_info={"action": {}},
            status=EventAction.Status.RUNNING,
            event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        )
        cls.event_action.id = 1
        NOTICE_DIMENSION_COLLECT_KEY.client.flushall()

    @classmethod
    def tearDownClass(cls):
        Event.objects.all().delete()
        EventAction.objects.all().delete()
        AnomalyRecord.objects.all().delete()
        ACTION_LIST_KEY.client.flushall()

    def test_dimension_hash(self):
        event = copy.deepcopy(self.event)

        collector = DimensionCollector(
            event_action=self.event_action,
            notice_way="weixin",
        )
        collector.event = event
        event.origin_alarm["data"]["dimensions"] = {
            "ip": "10.0.1.11",
            "bk_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
        }
        collect_dimensions = {}

        dimensions_hash = collector.dimension_hash
        collect_hash = md5(json.dumps(collect_dimensions, sort_keys=True).encode("utf-8")).hexdigest()
        self.assertEqual(dimensions_hash, collect_hash)

        collector = DimensionCollector(
            event_action=self.event_action,
            notice_way="weixin",
        )
        collector.event = event
        event.origin_alarm["data"]["dimensions"] = {
            "ip": "10.0.1.11",
            "bk_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
            "bk_target_service_instance_id": 1,
        }
        collect_dimensions = {}

        dimensions_hash = collector.dimension_hash
        collect_hash = md5(json.dumps(collect_dimensions, sort_keys=True).encode("utf-8")).hexdigest()
        self.assertEqual(dimensions_hash, collect_hash)

        collector = DimensionCollector(
            event_action=self.event_action,
            notice_way="weixin",
        )
        collector.event = event
        event.origin_config["item_list"][0]["rt_query_config"]["agg_dimension"] = ["ip", "bk_cloud_id", "xxx"]
        event.origin_alarm["data"]["dimensions"] = {
            "ip": "10.0.1.11",
            "bk_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
            "xxx": 1,
        }
        collect_dimensions = {
            "xxx": 1,
        }

        dimensions_hash = collector.dimension_hash
        collect_hash = md5(json.dumps(collect_dimensions, sort_keys=True).encode("utf-8")).hexdigest()
        self.assertEqual(dimensions_hash, collect_hash)

        collector = DimensionCollector(
            event_action=self.event_action,
            notice_way="weixin",
        )
        collector.event = event
        event.origin_config["scenario"] = "service_module"
        event.origin_config["item_list"][0]["rt_query_config"]["agg_dimension"] = [
            "bk_target_service_instance_id",
            "xxx",
        ]
        event.origin_alarm["data"]["dimensions"] = {
            "ip": "10.0.1.11",
            "bk_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
            "xxx": 1,
            "bk_target_service_instance_id": 23,
        }
        collect_dimensions = {"xxx": 1}

        dimensions_hash = collector.dimension_hash
        collect_hash = md5(json.dumps(collect_dimensions, sort_keys=True).encode("utf-8")).hexdigest()
        self.assertEqual(dimensions_hash, collect_hash)

    @patch("alarm_backends.service.action.notice.collector.send_dimension_collect_notice")
    def test_dimension_collect(self, mock_send_dimension_collect_notice):
        event_action = copy.deepcopy(self.event_action)
        collector = DimensionCollector(event_action=event_action, notice_way="weixin")

        key = NOTICE_DIMENSION_COLLECT_KEY.get_key(**collector.labels)
        lock_key = NOTICE_DIMENSION_COLLECT_KEY_LOCK.get_key(**collector.labels)
        client = NOTICE_DIMENSION_COLLECT_KEY.client
        client.flushall()
        receivers = collector.collect(["user1", "user2"])
        assert not receivers

        assert client.hget(key, "user1") == "1"
        assert client.hget(key, "user2") == "1"
        assert not client.get(lock_key)
        assert mock_send_dimension_collect_notice.apply_async.call_count == 1

        receivers = collector.collect(["user1", "user2"])
        assert not receivers

        assert client.hget(key, "user1") == "1"
        assert client.hget(key, "user2") == "1"
        assert client.get(lock_key)
        assert mock_send_dimension_collect_notice.apply_async.call_count == 2

        event_action.id = 2
        receivers = collector.collect(["user1", "user2"])
        assert not receivers

        assert set(client.hget(key, "user1").split(",")) == {"1", "2"}
        assert set(client.hget(key, "user2").split(",")) == {"1", "2"}
        assert mock_send_dimension_collect_notice.apply_async.call_count == 2

    @patch("alarm_backends.service.action.notice.collector.send_biz_collect_notice")
    @patch("alarm_backends.service.action.notice.collector.send_dimension_collect_notice")
    def test_biz_collect(self, mock_send_dimension_collect_notice, mock_send_biz_collect_notice):
        event_action = copy.deepcopy(self.event_action)
        collector = BizCollector(event_action=event_action, notice_way="weixin")

        user1_key = NOTICE_BIZ_COLLECT_KEY.get_key(receiver="user1", **collector.labels)
        user1_key_lock = NOTICE_BIZ_COLLECT_KEY_LOCK.get_key(receiver="user1", **collector.labels)
        user1_dimension_key = NOTICE_BIZ_DIMENSIONS_KEY.get_key(receiver="user1", **collector.labels)
        user2_key = NOTICE_BIZ_COLLECT_KEY.get_key(receiver="user2", **collector.labels)
        user2_key_lock = NOTICE_BIZ_COLLECT_KEY_LOCK.get_key(receiver="user2", **collector.labels)
        user2_dimension_key = NOTICE_BIZ_DIMENSIONS_KEY.get_key(receiver="user2", **collector.labels)
        client = NOTICE_DIMENSION_COLLECT_KEY.client

        receivers = collector.collect(["user1", "user2"])
        assert receivers == ["user1", "user2"]
        assert not client.get(user1_key_lock)
        assert not client.get(user2_key_lock)
        assert client.zscore(user1_dimension_key, f"{event_action.event.strategy_id}.{collector.dimension_hash}")
        assert client.zscore(user2_dimension_key, f"{event_action.event.strategy_id}.{collector.dimension_hash}")
        assert len(client.zrangebyscore(user1_dimension_key, "-inf", "+inf")) == 1
        assert len(client.zrangebyscore(user2_dimension_key, "-inf", "+inf")) == 1
        assert mock_send_biz_collect_notice.apply_async.call_count == 0

        collector.dimension_hash = "12345"
        receivers = collector.collect(["user1", "user2"])
        assert receivers == ["user1", "user2"]
        assert not client.get(user1_key_lock)
        assert not client.get(user2_key_lock)
        assert client.zscore(user1_dimension_key, f"{event_action.event.strategy_id}.{collector.dimension_hash}")
        assert client.zscore(user2_dimension_key, f"{event_action.event.strategy_id}.{collector.dimension_hash}")
        assert len(client.zrangebyscore(user1_dimension_key, "-inf", "+inf")) == 2
        assert len(client.zrangebyscore(user2_dimension_key, "-inf", "+inf")) == 2
        assert mock_send_biz_collect_notice.apply_async.call_count == 0

        collector.dimension_hash = "123456"
        user3_key = NOTICE_BIZ_COLLECT_KEY.get_key(receiver="user3", **collector.labels)
        user3_key_lock = NOTICE_BIZ_COLLECT_KEY_LOCK.get_key(receiver="user3", **collector.labels)
        user3_dimension_key = NOTICE_BIZ_DIMENSIONS_KEY.get_key(receiver="user3", **collector.labels)
        dimension_collect = DimensionCollector(event_action=event_action, notice_way="weixin")
        dimension_collect.collect(["user1", "user2"])
        receivers = collector.collect(["user1", "user2", "user3"])
        assert receivers == ["user3"]
        assert client.get(user1_key_lock)
        assert client.get(user2_key_lock)
        assert not client.get(user3_key_lock)
        assert client.zscore(user3_dimension_key, f"{event_action.event.strategy_id}.{collector.dimension_hash}")
        assert not client.exists(user1_dimension_key)
        assert not client.exists(user2_dimension_key)
        assert len(client.zrangebyscore(user3_dimension_key, "-inf", "+inf")) == 1
        assert client.llen(user1_key) == 1
        assert client.llen(user2_key) == 1
        assert client.llen(user3_key) == 0
        assert client.hget(NOTICE_DIMENSION_COLLECT_KEY.get_key(**dimension_collect.labels), "user1") == "1"
        assert client.hget(NOTICE_DIMENSION_COLLECT_KEY.get_key(**dimension_collect.labels), "user2") == "1"
        assert mock_send_biz_collect_notice.apply_async.call_count == 2

    @patch("alarm_backends.service.action.notice.collector.send_collect_notice")
    def test_voice_collect(self, mock_send_collect_notice):
        event_action = copy.deepcopy(self.event_action)
        collector = VoiceCollector(event_action=event_action, notice_way="voice")
        collector.collect(["user1,user2", "user3,user4"])

        labels = collector.labels
        client = NOTICE_VOICE_COLLECT_KEY.client
        key1 = NOTICE_VOICE_COLLECT_KEY.get_key(receiver="user1,user2", **labels)
        key2 = NOTICE_VOICE_COLLECT_KEY.get_key(receiver="user3,user4", **labels)

        assert client.exists(key1)
        assert client.exists(key2)
        assert mock_send_collect_notice.call_count == 2
