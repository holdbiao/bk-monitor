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

import arrow
import pytest
from six.moves import range

from alarm_backends.core.cache.key import (
    ACTION_LIST_KEY,
    CHECK_RESULT_CACHE_KEY,
    EVENT_ID_CACHE_KEY,
    LAST_CHECKPOINTS_CACHE_KEY,
)
from alarm_backends.service.event.manager.status_checker import RecoverStatusChecker
from alarm_backends.tests.service.event.manager import ANOMALY_EVENT, EVENT_KEY, STRATEGY
from bkmonitor.models import AnomalyRecord, Event, EventAction, time_tools

pytestmark = pytest.mark.django_db


class TestRecoverStatusChecker(object):
    def clear_data(self):
        EVENT_ID_CACHE_KEY.client.flushall()
        LAST_CHECKPOINTS_CACHE_KEY.client.flushall()
        CHECK_RESULT_CACHE_KEY.client.flushall()
        Event.objects.all().delete()
        EventAction.objects.all().delete()
        AnomalyRecord.objects.all().delete()

    def setup(self):
        self.clear_data()

    def teardown(self):
        self.clear_data()

    def test_set_recovered(self):
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
        checker = RecoverStatusChecker(event)
        checker.recover("测试恢复")
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED
        event_actions = EventAction.objects.filter(event_id=event_id)
        assert event_actions[0].operate == EventAction.Operate.RECOVER
        assert event_actions[0].status == EventAction.Status.SUCCESS
        assert event_actions[1].operate == EventAction.Operate.RECOVERY_NOTICE
        assert event_actions[1].status == EventAction.Status.RUNNING
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        assert int(action_id) == event_actions[1].id

    def test_has_recovered(self):
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
        checker = RecoverStatusChecker(event)
        assert checker.check()
        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None

    def test_expired_event(self):
        current_event_id = "new-event-id"
        new_event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, current_event_id)
        event = Event.objects.create(
            event_id=new_event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        checker = RecoverStatusChecker(event, STRATEGY)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == current_event_id
        assert Event.objects.get(event_id=new_event_id).status == Event.EventStatus.RECOVERED

    def test_anomaly_record_not_exist(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        checker = RecoverStatusChecker(event, STRATEGY)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    @classmethod
    def create_event(cls, event_id, strategy=None):
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        source_time = time_tools.mysql_time(arrow.now().datetime)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=source_time,
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy or STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        return event

    def test_has_trigger(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)

        checker = RecoverStatusChecker(event, STRATEGY)
        check_time = arrow.now().replace(seconds=-500).timestamp
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
        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i < 3:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_has_trigger2(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)

        checker = RecoverStatusChecker(event, STRATEGY)
        check_time = arrow.now().replace(seconds=-500).timestamp
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
        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i % 2 == 0:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_has_trigger3(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)

        checker = RecoverStatusChecker(event, STRATEGY)
        check_time = arrow.now().replace(seconds=-500).timestamp
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
        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_has_no_trigger(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

        check_time = arrow.now().replace(seconds=-500).timestamp
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
        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i < 2:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    def test_has_no_trigger2(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

        check_time = arrow.now().replace(seconds=-500).timestamp
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
        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i % 3 == 0:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    def test_push_actions(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)
        checker.push_actions("recovery")
        event_actions = EventAction.objects.filter(event_id=event_id)
        assert "action" in event_actions[0].extend_info
        assert event_actions[0].operate == EventAction.Operate.RECOVERY_NOTICE
        assert event_actions[0].status == EventAction.Status.RUNNING
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        assert int(action_id) == event_actions[0].id

    def test_push_actions_no_recovery(self):
        new_strategy = copy.deepcopy(STRATEGY)
        new_strategy["action_list"][0]["config"]["send_recovery_alarm"] = False
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id, new_strategy)
        checker = RecoverStatusChecker(event)
        checker.push_actions("recovery")
        # 强行推了次恢复 action，在处理逻辑中恢复告警会被过滤掉，应当只有消息队列有一个action
        assert len(EventAction.objects.filter(event_id=event_id)) == 1
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        assert action_id is None

    def test_check_no_data_true(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    def test_check_no_data_false(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

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

        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i < 3:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_data_report_no_delay(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

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

        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(8):
            ts = check_time - 60 * i
            if i < 3:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)
            else:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_data_report_delay(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)
        checker = RecoverStatusChecker(event, STRATEGY)

        check_time = arrow.now().replace(seconds=-1000).timestamp
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

        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(9):
            ts = check_time - 60 * i
            CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|0".format(ts), ts)

        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    def test_recover_for_event_true(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["data_type_label"] = "event"

        checker = RecoverStatusChecker(event, strategy)

        check_time = arrow.now().replace(seconds=-900).timestamp
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

        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i < 3:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)

        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.RECOVERED

    def test_recover_for_event_false(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id)

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["data_type_label"] = "event"

        checker = RecoverStatusChecker(event, STRATEGY)

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

        cache_key = CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=1,
            item_id=1,
            dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
            level=1,
        )
        for i in range(20):
            ts = check_time - 60 * i
            if i < 3:
                CHECK_RESULT_CACHE_KEY.client.zadd(cache_key, "{}|ANOMALY".format(ts), ts)

        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL
