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


from datetime import timedelta

import arrow
import mock
import pytest
from django.test import TestCase

from alarm_backends.constants import CONST_MINUTES
from alarm_backends.core.cache.key import ACTION_LIST_KEY
from alarm_backends.service.action.notice.tasks import do_create_notice_action
from alarm_backends.service.scheduler.app import app as celery
from bkmonitor.models import Event, EventAction

pytestmark = pytest.mark.django_db

arrow_now = arrow.Arrow(year=2019, month=1, day=1, tzinfo="local")


class TestCreateEventAction(TestCase):
    """
    测试通知操作EventAction生成任务
    """

    event_id = "654cc07befb731bb6a0bcfaec9ba22af.1570688400.6.6.1"
    StrategyCacheManager = mock.patch("alarm_backends.service.action.notice.tasks.StrategyCacheManager")
    arrow = mock.patch("alarm_backends.service.action.notice.tasks.arrow")
    queue_key = ACTION_LIST_KEY.get_key(action_type="notice")
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
                    "agg_dimension": [
                        "ip",
                        "bk_cloud_id",
                    ],
                    "extend_fields": "",
                    "unit_conversion": 1.0,
                    "agg_condition": [],
                    "agg_interval": 60,
                    "result_table_id": "system.cpu_summary",
                    "unit": "%",
                    "metric_field": "usage",
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

    @classmethod
    def setUpClass(cls):
        super(TestCreateEventAction, cls).setUpClass()
        Event.objects.create(
            event_id=cls.event_id,
            begin_time=arrow_now.datetime,
            bk_biz_id=2,
            strategy_id=6,
            level=1,
            status=Event.EventStatus.ABNORMAL,
            origin_config=cls.strategy,
        )

        # mock掉当前事件取值
        cls.arrow = cls.arrow.start()
        cls.arrow.now.return_value = arrow_now

        # mock掉策略接口
        manager = cls.StrategyCacheManager.start()
        manager.get_strategy_by_id.return_value = cls.strategy

        # celery task mock
        celery.conf.CELERY_ALWAYS_EAGER = True

    @classmethod
    def tearDownClass(cls):
        super(TestCreateEventAction, cls).tearDownClass()
        Event.objects.get(event_id=cls.event_id).delete()
        cls.StrategyCacheManager.stop()
        cls.arrow.stop()
        # celery task mock
        celery.conf.CELERY_ALWAYS_EAGER = False

    def tearDown(self):
        EventAction.objects.all().delete()
        ACTION_LIST_KEY.client.delete(self.queue_key)

    def test_create_first(self):
        """
        当Event没有EventAction时，创建一条EventAction
        """
        do_create_notice_action([self.event_id])

        assert EventAction.objects.filter(event_id=self.event_id).count() == 2
        event_action = EventAction.objects.filter(event_id=self.event_id)[0]  # type: EventAction

        self.assertEqual(event_action.operate, "ANOMALY_NOTICE")
        self.assertTrue("action" in event_action.extend_info)
        self.assertEqual(event_action.status, EventAction.Status.RUNNING)

        self.assertEqual(ACTION_LIST_KEY.client.llen(self.queue_key), 1)

    def test_create_when_gt_interval(self):
        """
        最新的一条EventAction的时间到现在超过了时间间隔，则创建
        """
        event_action = EventAction.objects.create(
            create_time=arrow_now.datetime
            - timedelta(
                seconds=self.strategy["action_list"][0]["config"]["alarm_interval"] * CONST_MINUTES + CONST_MINUTES
            ),
            operate=EventAction.Operate.ANOMALY_NOTICE,
            status=EventAction.Status.RUNNING,
            event_id=self.event_id,
        )
        event_action.create_time = arrow_now.datetime - timedelta(
            seconds=self.strategy["action_list"][0]["config"]["alarm_interval"] * CONST_MINUTES + CONST_MINUTES
        )
        event_action.save()

        do_create_notice_action([self.event_id])
        assert EventAction.objects.filter(event_id=self.event_id).count() == 3

        self.assertEqual(ACTION_LIST_KEY.client.llen(self.queue_key), 1)

    def test_no_create_when_lt_interval(self):
        """
        最新的一条EventAction的时间到现在小于时间间隔，则不创建
        """
        event_action = EventAction.objects.create(
            operate=EventAction.Operate.ANOMALY_NOTICE, status=EventAction.Status.RUNNING, event_id=self.event_id
        )
        event_action.create_time = arrow_now.datetime - timedelta(
            seconds=self.strategy["action_list"][0]["config"]["alarm_interval"] * CONST_MINUTES - CONST_MINUTES
        )
        event_action.save()

        do_create_notice_action([self.event_id])
        assert EventAction.objects.filter(event_id=self.event_id).count() == 1

        self.assertEqual(ACTION_LIST_KEY.client.llen(self.queue_key), 0)

    def test_create_when_eq_interval(self):
        """
        最新的一条EventAction的时间到现在等于时间间隔，则创建
        """
        event_action = EventAction.objects.create(
            operate=EventAction.Operate.ANOMALY_NOTICE, status=EventAction.Status.RUNNING, event_id=self.event_id
        )
        event_action.create_time = arrow_now.datetime - timedelta(
            seconds=self.strategy["action_list"][0]["config"]["alarm_interval"] * CONST_MINUTES
        )
        event_action.save()

        do_create_notice_action([self.event_id])
        assert EventAction.objects.filter(event_id=self.event_id).count() == 3

        self.assertEqual(ACTION_LIST_KEY.client.llen(self.queue_key), 1)

    def test_no_strategy(self):
        """
        无策略则取event的策略快照
        """
        self.StrategyCacheManager.stop()

        event_action = EventAction.objects.create(
            operate=EventAction.Operate.ANOMALY_NOTICE, status=EventAction.Status.RUNNING, event_id=self.event_id
        )
        event_action.create_time = arrow_now.datetime - timedelta(
            seconds=self.strategy["action_list"][0]["config"]["alarm_interval"] * CONST_MINUTES
        )
        event_action.save()
        do_create_notice_action([self.event_id])

        self.StrategyCacheManager.start()
