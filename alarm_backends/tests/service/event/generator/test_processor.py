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

import arrow
import mock
from django.test import TestCase

from alarm_backends.core.cache.key import ACTION_LIST_KEY, EVENT_EXTEND_CACHE_KEY, EVENT_ID_CACHE_KEY
from alarm_backends.service.event.generator.processor import EventGeneratorProcessor
from bkmonitor.models import AnomalyRecord, Event, EventAction
from bkmonitor.utils import time_tools
from core.errors.alarm_backends import StrategyNotFound

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
        "dimensions": {"ip": "10.0.0.1", "bk_cloud_id": "0"},
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
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.1",
        source_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
        strategy_id=1,
        origin_alarm=ANOMALY_EVENT,
        event_id="",
    )
]


def create_anomaly_records():
    AnomalyRecord.objects.create(
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246180.1.1.2",
        event_id="",
        source_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
        strategy_id=1,
        origin_alarm={},
    )
    AnomalyRecord.objects.create(
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2",
        event_id="",
        source_time=time_tools.mysql_time(arrow.get("1569246240").datetime),
        strategy_id=1,
        origin_alarm={},
    )
    AnomalyRecord.objects.create(
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2",
        event_id="",
        source_time=time_tools.mysql_time(arrow.get("1569246360").datetime),
        strategy_id=1,
        origin_alarm={},
    )
    AnomalyRecord.objects.create(
        anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2",
        event_id="",
        source_time=time_tools.mysql_time(arrow.get("1569246480").datetime),
        strategy_id=1,
        origin_alarm={},
    )


EVENT_ID_KEY = EVENT_ID_CACHE_KEY.get_key(strategy_id=1, item_id=1, dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf")


class TestProcess(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Strategy = mock.patch("alarm_backends.service.event.generator.processor.Strategy")
        mock_strategy = cls.Strategy.start()
        mock_strategy.get_strategy_snapshot_by_key.side_effect = lambda key, _: STRATEGY if key == "xxx" else None

    @classmethod
    def tearDownClass(cls):
        cls.Strategy.stop()

    def test_get_strategy(self):
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)

        strategy_config = processor.get_strategy_snapshot("xxx")
        self.assertDictEqual(strategy_config, STRATEGY)

        with self.assertRaises(StrategyNotFound):
            processor.get_strategy_snapshot("non-exist")

    def test_init(self):
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        self.assertEqual(processor.source_time, 1569246480)
        self.assertEqual(processor.dimensions_md5, "55a76cf628e46c04a052f4e19bdb9dbf")

    def clear_data(self):
        EVENT_ID_CACHE_KEY.client.flushall()
        Event.objects.all().delete()
        EventAction.objects.all().delete()
        AnomalyRecord.objects.all().delete()

    def setUp(self):
        self.clear_data()

    def tearDown(self):
        self.clear_data()

    def test_create_new_event(self):
        dimension_translation = {
            "ip": {"value": "10.0.0.1", "display_name": "ip", "display_value": "10.0.0.1"},
            "bk_cloud_id": {"value": "0", "display_name": "云区域ID", "display_value": "0"},
        }
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.create_new_event()
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2"
        event = Event.objects.get(event_id=event_id)
        self.assertEqual(event.begin_time, arrow.get(1569246240).datetime)
        self.assertEqual(event.level, 2)
        self.assertEqual(event.status, Event.EventStatus.ABNORMAL)
        self.assertDictEqual(event.origin_config, STRATEGY)
        self.assertEqual(event.target_key, "host|10.0.0.1|0")

        origin_alarm = copy.deepcopy(ANOMALY_EVENT)
        origin_alarm["dimension_translation"] = dimension_translation
        self.assertDictEqual(event.origin_alarm, origin_alarm)

        event_actions = EventAction.objects.filter(event_id=event_id)
        self.assertEqual(event_actions.count(), 3)
        self.assertEqual(event_actions[0].operate, EventAction.Operate.CREATE)
        self.assertEqual(event_actions[0].status, EventAction.Status.SUCCESS)
        self.assertEqual(event_actions[1].operate, EventAction.Operate.ANOMALY_NOTICE)
        self.assertEqual(event_actions[1].status, EventAction.Status.RUNNING)
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        self.assertEqual(int(action_id), event_actions[1].id)
        self.assertEqual(EVENT_ID_CACHE_KEY.client.get(EVENT_ID_KEY), event_id)

    def test_create_new_event_exists(self):
        Event.objects.create(
            event_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2",
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.create_new_event()
        self.assertFalse(EventAction.objects.exists())

    def test_new_event(self):
        # create_anomaly_records()
        record = [
            AnomalyRecord(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2",
                event_id="",
                source_time=time_tools.mysql_time(arrow.get("1569246240").datetime),
                strategy_id=1,
                origin_alarm={},
            ),
            AnomalyRecord(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2",
                event_id="",
                source_time=time_tools.mysql_time(arrow.get("1569246360").datetime),
                strategy_id=1,
                origin_alarm={},
            ),
            AnomalyRecord(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2",
                event_id="",
                source_time=time_tools.mysql_time(arrow.get("1569246480").datetime),
                strategy_id=1,
                origin_alarm={},
            ),
        ]
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": record}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.process()
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2"
        self.assertEqual(
            AnomalyRecord.objects.get(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2").event_id, event_id
        )
        self.assertEqual(
            AnomalyRecord.objects.get(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2").event_id, event_id
        )
        self.assertEqual(
            AnomalyRecord.objects.get(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2").event_id, event_id
        )

        self.assertEqual(EVENT_ID_CACHE_KEY.client.get(EVENT_ID_KEY), event_id)

        self.assertTrue(Event.objects.filter(event_id=event_id).exists())

    def test_low_level_event(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246180.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_ID_KEY, event_id)
        create_anomaly_records()
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.process()

        for record in AnomalyRecord.objects.all():
            self.assertEqual(record.event_id, "")

        self.assertEqual(EVENT_ID_CACHE_KEY.client.get(EVENT_ID_KEY), event_id)

        self.assertFalse(Event.objects.exists())
        self.assertFalse(EventAction.objects.exists())

    def test_equal_level_event(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2"
        EVENT_ID_CACHE_KEY.client.set(EVENT_ID_KEY, event_id)
        create_anomaly_records()
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.process()

        self.assertEqual(EVENT_ID_CACHE_KEY.client.get(EVENT_ID_KEY), event_id)

        self.assertFalse(Event.objects.exists())
        self.assertEqual(EventAction.objects.get().operate, EventAction.Operate.CONVERGE)
        latest_action = EventAction.objects.filter(event_id=event_id).last()
        extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=latest_action.id)
        need_insert = json.loads(EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys))["need_insert"]
        self.assertFalse(need_insert)

    def test_high_level_event(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.3"
        new_event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246360.1.1.2"
        EVENT_ID_CACHE_KEY.client.set(EVENT_ID_KEY, event_id)
        # create_anomaly_records()

        Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        records = [
            AnomalyRecord(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2",
                source_time=time_tools.mysql_time(arrow.get("1569246240").datetime),
                strategy_id=1,
                origin_alarm=ANOMALY_EVENT,
                event_id="",
            )
        ]

        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": records}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.process()

        self.assertEqual(EVENT_ID_CACHE_KEY.client.get(EVENT_ID_KEY), new_event_id)

        old_event = Event.objects.get(event_id=event_id)
        old_event_action = EventAction.objects.get(event_id=event_id)
        self.assertEqual(old_event.status, Event.EventStatus.RECOVERED)
        self.assertEqual(old_event.end_time, arrow.get(1569246480).datetime)
        self.assertEqual(old_event_action.operate, EventAction.Operate.RECOVER)
        self.assertEqual(old_event_action.status, EventAction.Status.SUCCESS)

        self.assertEqual(
            AnomalyRecord.objects.get(anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.2").event_id,
            new_event_id,
        )
        new_event = Event.objects.get(event_id=new_event_id)
        new_event_actions = EventAction.objects.filter(event_id=new_event_id)
        self.assertEqual(new_event.begin_time, arrow.get(1569246240).datetime)
        self.assertEqual(new_event.status, Event.EventStatus.ABNORMAL)
        self.assertEqual(new_event_actions[0].operate, EventAction.Operate.CREATE)
        self.assertEqual(new_event_actions[1].operate, EventAction.Operate.ANOMALY_NOTICE)

    def _gen_event_record(self, timestamp):
        return {
            "data": {
                "record_id": "55a76cf628e46c04a052f4e19bdb9dbf.%s" % timestamp,
                "value": 1.38,
                "values": {"timestamp": timestamp, "load5": 1.38},
                "dimensions": {"ip": "10.0.0.1"},
                "time": timestamp,
            },
            "anomaly": {
                "1": {
                    "anomaly_message": "异常测试",
                    "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.%s.1.1.1" % timestamp,
                    "anomaly_time": "2019-10-10 10:10:00",
                },
                "2": {
                    "anomaly_message": "异常测试",
                    "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.%s.1.1.2" % timestamp,
                    "anomaly_time": "2019-10-10 10:10:00",
                },
                "3": {
                    "anomaly_message": "异常测试",
                    "anomaly_id": "55a76cf628e46c04a052f4e19bdb9dbf.%s.1.1.3" % timestamp,
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

    def test_update_converge_action(self):
        # 1
        record = [
            AnomalyRecord.objects.create(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246480.1.1.2",
                event_id="event-id",
                source_time=time_tools.mysql_time(arrow.get("1569246480").datetime),
                strategy_id=1,
                origin_alarm={},
            )
        ]

        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": record}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.update_or_create_converge_action("event-id")

        action = EventAction.objects.get(event_id="event-id")

        self.assertEqual(action.extend_info["data_time"]["min"], 1569246480)
        self.assertEqual(action.extend_info["data_time"]["max"], 1569246480)
        self.assertEqual(action.extend_info["process_time"]["min"], int(arrow.get(record[0].create_time).timestamp))
        self.assertEqual(action.extend_info["process_time"]["max"], int(arrow.get(record[0].create_time).timestamp))
        self.assertEqual(action.extend_info["anomaly_count"], 1)
        self.assertDictEqual(action.extend_info["anomaly_record"], processor.anomaly_event)
        latest_action = EventAction.objects.filter(event_id="event-id").last()
        extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=latest_action.id)
        cache_extend_info = json.loads(EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys))
        self.assertFalse(cache_extend_info["need_insert"])
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["min"], 1569246480)
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["max"], 1569246480)
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["min"], int(arrow.get(record[0].create_time).timestamp)
        )
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["max"], int(arrow.get(record[0].create_time).timestamp)
        )
        self.assertEqual(cache_extend_info["extend_info"]["anomaly_count"], 1)

        # 2
        record_1 = [
            AnomalyRecord.objects.create(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246500.1.1.2",
                event_id="event-id",
                source_time=time_tools.mysql_time(arrow.get("1569246500").datetime),
                strategy_id=1,
                origin_alarm={},
            )
        ]

        anomaly_event_json = {"event_record": self._gen_event_record(1569246500), "anomaly_records": record_1}
        processor_1 = EventGeneratorProcessor(anomaly_event_json)

        processor_1.update_or_create_converge_action("event-id")

        latest_action = EventAction.objects.filter(event_id="event-id").last()
        extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=latest_action.id)
        cache_extend_info = json.loads(EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys))
        self.assertTrue(cache_extend_info["need_insert"])
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["min"], 1569246480)
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["max"], 1569246500)
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["min"], int(arrow.get(record[0].create_time).timestamp)
        )
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["max"], int(arrow.get(record_1[0].create_time).timestamp)
        )
        self.assertEqual(cache_extend_info["extend_info"]["anomaly_count"], 2)

        # 3
        record_2 = [
            AnomalyRecord.objects.create(
                anomaly_id="55a76cf628e46c04a052f4e19bdb9dbf.1569246460.1.1.2",
                event_id="event-id",
                source_time=time_tools.mysql_time(arrow.get("1569246460").datetime),
                strategy_id=1,
                origin_alarm={},
            )
        ]

        anomaly_event_json = {"event_record": self._gen_event_record(1569246460), "anomaly_records": record_2}

        processor_2 = EventGeneratorProcessor(anomaly_event_json)
        processor_2.update_or_create_converge_action("event-id")

        latest_action = EventAction.objects.filter(event_id="event-id").last()
        extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=latest_action.id)
        cache_extend_info = json.loads(EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys))
        self.assertTrue(cache_extend_info["need_insert"])
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["min"], 1569246460)
        self.assertEqual(cache_extend_info["extend_info"]["data_time"]["max"], 1569246500)
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["min"], int(arrow.get(record[0].create_time).timestamp)
        )
        self.assertEqual(
            cache_extend_info["extend_info"]["process_time"]["max"], int(arrow.get(record_2[0].create_time).timestamp)
        )
        self.assertEqual(cache_extend_info["extend_info"]["anomaly_count"], 3)

    def test_push_actions(self):
        anomaly_event_json = {"event_record": ANOMALY_EVENT, "anomaly_records": ANOMALY_RECORDS}
        processor = EventGeneratorProcessor(anomaly_event_json)
        processor.push_actions()
        event_actions = EventAction.objects.filter(event_id=processor.new_event_id)
        self.assertIn("action", event_actions[0].extend_info)
        self.assertEqual(event_actions[0].operate, EventAction.Operate.ANOMALY_NOTICE)
        self.assertEqual(event_actions[0].status, EventAction.Status.RUNNING)
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        self.assertEqual(int(action_id), event_actions[0].id)

    def test_generate_ip_target_key(self):
        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["ip", "bk_cloud_id"],
                data_dimensions={"ip": "10.0.0.1", "bk_cloud_id": "0"},
                scenario="os",
            ),
            "host|10.0.0.1|0",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["bk_target_ip", "bk_target_cloud_id"],
                data_dimensions={"bk_target_ip": "10.0.0.1", "bk_target_cloud_id": "0"},
                scenario="os",
            ),
            "host|10.0.0.1|0",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["bk_target_ip", "bk_target_cloud_id"],
                data_dimensions={"bk_target_ip": "10.0.0.1"},
                scenario="os",
            ),
            "",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=[],
                data_dimensions={"bk_target_ip": "10.0.0.1", "bk_target_cloud_id": "0"},
                scenario="os",
            ),
            "",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["ip", "bk_cloud_id"],
                data_dimensions={"ip": "10.0.0.1", "bk_cloud_id": "0"},
                scenario="service_module",
            ),
            "",
        )

    def test_generate_topo_target_key(self):
        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=[],
                data_dimensions={"bk_obj_id": "set", "bk_inst_id": "3"},
                scenario="os",
            ),
            "topo|set|3",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=[],
                data_dimensions={"bk_obj_id": "set", "bk_inst_id": "3"},
                scenario="service_module",
            ),
            "topo|set|3",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=[],
                data_dimensions={"bk_target_ip": "10.0.0.1", "bk_target_cloud_id": "0"},
                scenario="os",
            ),
            "",
        )

    def test_generate_instance_target_key(self):
        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["bk_target_service_instance_id"],
                data_dimensions={"bk_target_service_instance_id": "33"},
                scenario="service_module",
            ),
            "service|33",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=["bk_target_service_instance_id"],
                data_dimensions={"bk_target_ip": "10.0.0.1", "bk_target_cloud_id": "0"},
                scenario="service_module",
            ),
            "",
        )

        self.assertEqual(
            EventGeneratorProcessor.generate_target_key(
                agg_dimensions=[],
                data_dimensions={"bk_target_service_instance_id": "33"},
                scenario="service_module",
            ),
            "",
        )
