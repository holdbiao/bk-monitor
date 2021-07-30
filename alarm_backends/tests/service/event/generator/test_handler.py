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

import arrow
import pytest
import six.moves.cPickle
from mock import MagicMock, patch

from alarm_backends.core.cache.key import (
    EVENT_ID_CACHE_KEY,
    SERVICE_LOCK_EVENT,
    STRATEGY_SNAPSHOT_KEY,
    TRIGGER_EVENT_LIST_KEY,
)
from alarm_backends.core.lock.service_lock import service_lock
from alarm_backends.service.event import EventType
from alarm_backends.service.event.generator.processor import EventGeneratorProcessor
from alarm_backends.service.event.generator.tasks import handle_event, run_generator
from alarm_backends.service.event.handler import EventHandler
from bkmonitor.models import AnomalyRecord
from bkmonitor.utils import time_tools

pytestmark = pytest.mark.django_db

STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "rt_query_config": {
                "metric_field": "idle",
                "agg_dimension": ["ip", "bk_cloud_id"],
                "unit_conversion": 1.0,
                "id": 2,
                "extend_fields": "",
                "rt_query_config_id": 2,
                "agg_method": "AVG",
                "agg_condition": [],
                "agg_interval": 60,
                "result_table_id": "system.cpu_detail",
                "unit": "%",
            },
            "metric_id": "bk_monitor.system.cpu_detail.idle",
            "item_name": "\u7a7a\u95f2\u7387",
            "strategy_id": 1,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": [{"threshold": 0.1, "method": "gte"}],
                    "level": 1,
                    "strategy_id": 1,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 2,
                    "message_template": "",
                    "item_id": 1,
                    "id": 1,
                },
                {
                    "algorithm_config": [{"threshold": 0.1, "method": "gte"}],
                    "level": 2,
                    "strategy_id": 1,
                    "trigger_config": {"count": 2, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 2,
                    "message_template": "",
                    "item_id": 1,
                    "id": 2,
                },
                {
                    "algorithm_config": [{"threshold": 0.1, "method": "gte"}],
                    "level": 3,
                    "strategy_id": 1,
                    "trigger_config": {"count": 1, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 2,
                    "message_template": "",
                    "item_id": 1,
                    "id": 3,
                },
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "rt_query_config_id": 2,
            "item_id": 1,
            "data_type_label": "time_series",
            "id": 2,
            "name": "\u7a7a\u95f2\u7387",
        }
    ],
    "target": [
        [
            {
                "field": "ip",
                "method": "eq",
                "value": [
                    {"ip": "127.0.0.1", "bk_cloud_id": 0, "bk_supplier_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 1,
    "action_list": [
        {
            "notice_template": {"action_id": 2, "anomaly_template": "aa", "recovery_template": ""},
            "id": 2,
            "notice_group_list": [
                {
                    "notice_receiver": ["user#test"],
                    "name": "test",
                    "notice_way": {"1": ["weixin"], "3": ["weixin"], "2": ["weixin"]},
                    "notice_group_id": 1,
                    "message": "",
                    "notice_group_name": "test",
                    "id": 1,
                }
            ],
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "strategy_id": 1,
            "action_id": 2,
        }
    ],
    "source_type": "BKMONITOR",
    "strategy_name": "test",
    "id": 1,
    "name": "test",
}

ANOMALY_EVENT = {
    "data": {
        "record_id": "55a76cf628e46c04a052f4e19bdb9dbf.1569246480",
        "value": 1.38,
        "values": {"timestamp": 1569246480, "load5": 1.38},
        "dimensions": {"ip": "10.0.0.1"},
        "time": 1569246480,
    },
    "anomaly": {
        "1": {
            "anomaly_message": "异常测试",
            "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.1",
            "anomaly_time": "2019-10-10 10:10:00",
        },
        "2": {
            "anomaly_message": "异常测试",
            "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2",
            "anomaly_time": "2019-10-10 10:10:00",
        },
        "3": {
            "anomaly_message": "异常测试",
            "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.3",
            "anomaly_time": "2019-10-10 10:10:00",
        },
    },
    "strategy_snapshot_key": "xxx",
    "trigger": {
        "level": "2",
        "anomaly_ids": [
            "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2",
            "55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2",
            "55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2",
        ],
    },
}

ANOMALY_RECORDS = [
    AnomalyRecord(
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2",
        source_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
        strategy_id=1,
        origin_alarm=ANOMALY_EVENT,
        event_id="",
    )
]


@pytest.fixture()
def processor(mocker):
    mock = MagicMock()
    mock.dimensions_md5 = "55a76cf628e46c04a052f4e19bdb9dbf"
    mock.strategy_id = 1
    mocker.patch("alarm_backends.service.event.generator.tasks.EventGeneratorProcessor", return_value=mock)
    return mock


@pytest.fixture()
def sleep(mock):
    return mock.patch("time.sleep", return_value=None)


class TestHandler(object):
    def setup(self):
        TRIGGER_EVENT_LIST_KEY.client.flushall()
        STRATEGY_SNAPSHOT_KEY.client.flushall()
        AnomalyRecord.objects.all().delete()
        EVENT_ID_CACHE_KEY.client.flushall()

    def teardown(self):
        TRIGGER_EVENT_LIST_KEY.client.flushall()
        STRATEGY_SNAPSHOT_KEY.client.flushall()
        AnomalyRecord.objects.all().delete()
        EVENT_ID_CACHE_KEY.client.flushall()

    def test_no_data(self, processor):
        run_generator()
        assert processor.process.call_count == 0
        assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 0

    def test_parse_error(self, processor):
        TRIGGER_EVENT_LIST_KEY.client.lpush(TRIGGER_EVENT_LIST_KEY.get_key(), "{xxx}")

        handler = EventHandler(EventType.GENERATOR)
        handler.handle()

        assert processor.process.call_count == 0
        assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 0

    def test_start(self, processor):
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        handle_event(processor, anomaly_event_json)

        assert processor.process.call_count == 1
        assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 0

    @patch("alarm_backends.service.event.generator.tasks.handle_event.delay", lambda *args, **kwargs: None)
    def test_run_generator(self):
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        TRIGGER_EVENT_LIST_KEY.client.lpush(
            TRIGGER_EVENT_LIST_KEY.get_key(), six.moves.cPickle.dumps(anomaly_event_json).decode("latin1")
        )
        STRATEGY_SNAPSHOT_KEY.client.set("xxx", json.dumps(STRATEGY))
        event_id_cache_key = EVENT_ID_CACHE_KEY.get_key(
            strategy_id=1, item_id=1, dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf"
        )
        EVENT_ID_CACHE_KEY.client.set(event_id_cache_key, "11111")
        run_generator()
        count = AnomalyRecord.objects.filter(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2").count()
        assert count == 1
        assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 0
        record = AnomalyRecord.objects.filter(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2").first()
        assert record.event_id == "11111"

    @patch("alarm_backends.service.event.generator.tasks.handle_event.delay", lambda *args, **kwargs: None)
    def test_run_generator_with_multi_event(self):
        anomaly_event_json1 = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        anomaly_event_json2 = {
            "event_record": ANOMALY_EVENT,
            "anomaly_records": [
                AnomalyRecord(
                    anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2",
                    source_time=time_tools.mysql_time(arrow.get("1569246360").datetime),
                    strategy_id=1,
                    origin_alarm=ANOMALY_EVENT,
                    event_id="",
                ),
            ],
        }
        TRIGGER_EVENT_LIST_KEY.client.lpush(
            TRIGGER_EVENT_LIST_KEY.get_key(), six.moves.cPickle.dumps(anomaly_event_json1).decode("latin1")
        )
        TRIGGER_EVENT_LIST_KEY.client.lpush(
            TRIGGER_EVENT_LIST_KEY.get_key(), six.moves.cPickle.dumps(anomaly_event_json2).decode("latin1")
        )

        STRATEGY_SNAPSHOT_KEY.client.set("xxx", json.dumps(STRATEGY))
        run_generator()
        event_id_cache_key = EVENT_ID_CACHE_KEY.get_key(
            strategy_id=1, item_id=1, dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf"
        )

        assert EVENT_ID_CACHE_KEY.client.get(event_id_cache_key) is None

        assert AnomalyRecord.objects.filter(event_id="").count() == 2

        handle_event(EventGeneratorProcessor(anomaly_event_json1), anomaly_event_json1)
        assert EVENT_ID_CACHE_KEY.client.get(event_id_cache_key) == "55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2"
        assert AnomalyRecord.objects.filter(event_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2").count() == 2

    def test_exception(self, processor):
        def process(*args, **kwargs):
            raise Exception("test exc")

        processor.process.side_effect = process

        # TRIGGER_EVENT_LIST_KEY.client.lpush(TRIGGER_EVENT_LIST_KEY.get_key(), ANOMALY_EVENT)
        #
        # handler = EventHandler(EventType.GENERATOR)
        # handler.handle()
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        handle_event(processor, anomaly_event_json)

        assert processor.process.call_count == 1
        assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 0

    def test_lock(self, processor, sleep):
        with service_lock(SERVICE_LOCK_EVENT, strategy_id=1, dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf"):
            # TRIGGER_EVENT_LIST_KEY.client.lpush(TRIGGER_EVENT_LIST_KEY.get_key(), ANOMALY_EVENT)
            # handler = EventHandler(EventType.GENERATOR)
            # handler.handle()
            anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
            handle_event(processor, anomaly_event_json)
            assert processor.process.call_count == 0
            assert TRIGGER_EVENT_LIST_KEY.client.llen(TRIGGER_EVENT_LIST_KEY.get_key()) == 1
