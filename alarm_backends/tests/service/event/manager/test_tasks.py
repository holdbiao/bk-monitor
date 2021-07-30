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
import pytest
from mock import MagicMock

from alarm_backends.core.cache.key import RECOVERY_CHECK_EVENT_ID_KEY, SERVICE_LOCK_RECOVERY
from alarm_backends.core.lock.service_lock import service_lock
from alarm_backends.service.event.manager.tasks import check_abnormal_event, handle_manager, run_manager
from alarm_backends.tests.service.event.manager import ANOMALY_EVENT, STRATEGY
from bkmonitor.models import Event
from bkmonitor.utils import time_tools

pytestmark = pytest.mark.django_db


@pytest.fixture()
def processor(mocker):
    mock = MagicMock()
    mock.dimensions_md5 = "55a76cf628e46c04a052f4e19bdb9dbf"
    mock.strategy_id = 1
    mocker.patch("alarm_backends.service.event.manager.tasks.EventManagerProcessor", return_value=mock)
    return mock


@pytest.fixture()
def sleep(mock):
    return mock.patch("alarm_backends.service.event.manager.tasks.time.sleep", return_value=None)


class TestHandler(object):

    EVENT_ID = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"

    def setup(self):
        Event.objects.create(
            event_id=self.EVENT_ID,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        RECOVERY_CHECK_EVENT_ID_KEY.client.flushall()

    def teardown(self):
        Event.objects.all().delete()
        RECOVERY_CHECK_EVENT_ID_KEY.client.flushall()

    def test_no_data(self, processor, sleep):
        run_manager()

        assert processor.process.call_count == 0
        assert RECOVERY_CHECK_EVENT_ID_KEY.client.llen(RECOVERY_CHECK_EVENT_ID_KEY.get_key()) == 0

    def test_parse_error(self, processor):
        # RECOVERY_CHECK_EVENT_ID_KEY.client.sadd(RECOVERY_CHECK_EVENT_ID_KEY.get_key(), 'not-exist-event-id')

        # run_manager()
        handle_manager("not-exist-event-id")
        assert processor.process.call_count == 0
        assert RECOVERY_CHECK_EVENT_ID_KEY.client.scard(RECOVERY_CHECK_EVENT_ID_KEY.get_key()) == 0

    def test_start(self, processor):
        # RECOVERY_CHECK_EVENT_ID_KEY.client.sadd(RECOVERY_CHECK_EVENT_ID_KEY.get_key(), self.EVENT_ID)
        #
        # run_manager()
        handle_manager(self.EVENT_ID)

        assert processor.process.call_count == 1
        assert RECOVERY_CHECK_EVENT_ID_KEY.client.scard(RECOVERY_CHECK_EVENT_ID_KEY.get_key()) == 0

    def test_exception(self, processor):
        def process(*args, **kwargs):
            raise Exception("test exc")

        processor.process.side_effect = process

        # RECOVERY_CHECK_EVENT_ID_KEY.client.sadd(RECOVERY_CHECK_EVENT_ID_KEY.get_key(), self.EVENT_ID)
        #
        # run_manager()

        handle_manager(self.EVENT_ID)

        assert processor.process.call_count == 1
        assert RECOVERY_CHECK_EVENT_ID_KEY.client.scard(RECOVERY_CHECK_EVENT_ID_KEY.get_key()) == 0

    def test_lock(self, processor, sleep):
        with service_lock(SERVICE_LOCK_RECOVERY, strategy_id=1, dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf"):
            # RECOVERY_CHECK_EVENT_ID_KEY.client.sadd(RECOVERY_CHECK_EVENT_ID_KEY.get_key(), self.EVENT_ID)
            # run_manager()
            handle_manager(self.EVENT_ID)
            assert processor.process.call_count == 0
            assert RECOVERY_CHECK_EVENT_ID_KEY.client.scard(RECOVERY_CHECK_EVENT_ID_KEY.get_key()) == 1

    def test_check_abnormal_event(self):
        Event.objects.create(
            event_id="recovered-event-id",
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.RECOVERED,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        event_ids = check_abnormal_event()
        assert set(event_ids) == {self.EVENT_ID}
        event_ids_in_queue = RECOVERY_CHECK_EVENT_ID_KEY.client.smembers(RECOVERY_CHECK_EVENT_ID_KEY.get_key())
        assert set(event_ids_in_queue) == {self.EVENT_ID}
