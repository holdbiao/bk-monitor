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
import pytest

from alarm_backends.service.action.shield.shielder import SaaSConfigShielder
from alarm_backends.service.event.manager.status_checker import ShieldStatusChecker
from alarm_backends.tests.service.event.manager import ANOMALY_EVENT, STRATEGY
from bkmonitor.models import Event
from bkmonitor.utils import time_tools

pytestmark = pytest.mark.django_db


class TestShieldStatusChecker(object):
    def setup(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        self.event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

    def teardown(self):
        self.event.delete()

    def get_event_is_shield(self):
        return Event.objects.get(event_id=self.event.event_id).is_shielded

    def get_event_shield_type(self):
        return Event.objects.get(event_id=self.event.event_id).shield_type

    @mock.patch("alarm_backends.service.event.manager.status_checker.shield.ShieldManager.shield")
    def test_set_shield_true(self, is_match):
        self.event.is_shielded = False
        self.event.save()
        shielder = SaaSConfigShielder(self.event)
        is_match.return_value = (True, shielder)
        checker = ShieldStatusChecker(self.event)
        assert checker.check()
        assert self.get_event_is_shield()
        assert self.get_event_shield_type() == shielder.type

    @mock.patch("alarm_backends.service.event.manager.status_checker.shield.ShieldManager.shield")
    def test_set_shield_false(self, is_match):
        self.event.is_shielded = True
        self.event.shield_type = "saas_config"
        self.event.save()
        is_match.return_value = (False, None)
        checker = ShieldStatusChecker(self.event)
        assert not checker.check()
        assert not self.get_event_is_shield()
        assert not self.get_event_shield_type()

    @mock.patch("alarm_backends.service.event.manager.status_checker.shield.ShieldManager.shield")
    def test_no_set_shield(self, is_match):
        self.event.is_shielded = True
        self.event.shield_type = "saas_config"
        self.event.save()
        shielder = SaaSConfigShielder(self.event)
        is_match.return_value = (True, shielder)
        checker = ShieldStatusChecker(self.event)
        assert checker.check()
        assert self.get_event_is_shield()
        assert self.get_event_shield_type() == shielder.type

    @mock.patch("alarm_backends.service.event.manager.status_checker.shield.ShieldManager.shield")
    def test_set_set_shield_type(self, is_match):
        self.event.is_shielded = True
        self.event.shield_type = "other"
        self.event.save()
        shielder = SaaSConfigShielder(self.event)
        is_match.return_value = (True, shielder)
        checker = ShieldStatusChecker(self.event)
        assert checker.check()
        assert self.get_event_is_shield()
        assert self.get_event_shield_type() == shielder.type
