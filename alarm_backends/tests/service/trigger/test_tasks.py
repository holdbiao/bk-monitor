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
from django.conf import settings

from alarm_backends.service.trigger.tasks import clean_anomaly_records
from bkmonitor.models import AnomalyRecord

pytestmark = pytest.mark.django_db


class TestTasks(object):
    def setup(self):
        AnomalyRecord.objects.all().delete()

    def teardown(self):
        AnomalyRecord.objects.all().delete()

    def test_clear_anomaly_records(self):
        anomaly1 = AnomalyRecord.objects.create(
            anomaly_id="test1",
            event_id="test",
            origin_alarm=None,
            source_time=arrow.now().datetime,
            strategy_id=1,
        )
        anomaly1.create_time = arrow.now().replace(days=-settings.ANOMALY_RECORD_SAVE_DAYS).datetime
        anomaly1.save()
        anomaly2 = AnomalyRecord.objects.create(
            anomaly_id="test2",
            event_id="test",
            origin_alarm=None,
            source_time=arrow.now().datetime,
            strategy_id=1,
        )
        anomaly2.create_time = arrow.now().replace(days=-settings.ANOMALY_RECORD_SAVE_DAYS + 1).datetime
        anomaly2.save()
        clean_anomaly_records()
        assert AnomalyRecord.objects.count() == 1
        assert AnomalyRecord.objects.get().id == anomaly2.id
