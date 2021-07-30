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


import arrow
import mock
from django.test import TestCase

from alarm_backends.core.cache.key import EVENT_ID_CACHE_KEY, LAST_CHECKPOINTS_CACHE_KEY
from alarm_backends.service.event.manager.processor import EventManagerProcessor
from alarm_backends.tests.service.event.manager import ANOMALY_EVENT, STRATEGY
from bkmonitor.models import AnomalyRecord, Event, EventAction, time_tools


class TestProcessor(TestCase):
    def clear_data(self):
        EVENT_ID_CACHE_KEY.client.flushall()
        Event.objects.all().delete()
        EventAction.objects.all().delete()
        AnomalyRecord.objects.all().delete()

    def setUp(self):
        self.clear_data()

    def tearDown(self):
        self.clear_data()

    def test_process_no_abnormal(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.RECOVERED,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        processor = EventManagerProcessor(event)
        processor.process()
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    @mock.patch(
        "alarm_backends.service.event.manager.processor.StrategyCacheManager.get_strategy_by_id", return_value=STRATEGY
    )
    def test_process_has_abnormal(self, get_strategy_by_id):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        check_time = arrow.now().replace(seconds=-200).timestamp
        LAST_CHECKPOINTS_CACHE_KEY.client.hset(
            LAST_CHECKPOINTS_CACHE_KEY.get_key(),
            LAST_CHECKPOINTS_CACHE_KEY.get_field(
                strategy_id=1,
                item_id=1,
                dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
                level=1,
            ),
            check_time,
        )
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        processor = EventManagerProcessor(event)
        processor.process()
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED
        assert not Event.objects.get(event_id=event_id).is_shielded

    def test_process_has_abnormal_2(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        processor = EventManagerProcessor(event)
        processor.process()
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED
        assert not Event.objects.get(event_id=event_id).is_shielded
