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
from datetime import timedelta

import arrow

from alarm_backends.service.action.shield.shield_obj import ShieldObj

utc_now = arrow.utcnow()
now = arrow.now()

config = {
    "begin_time": utc_now.datetime,
    "bk_biz_id": 2,
    "category": "strategy",
    "content": "",
    "create_time": utc_now.datetime,
    "create_user": "admin",
    "cycle_config": {},
    "description": "\u9a71\u868a\u5668\u7fc1\u7fa4",
    "dimension_config": {"level": [2], "strategy_id": 5},
    "end_time": utc_now.datetime + timedelta(minutes=1),
    "failure_time": utc_now.datetime + timedelta(days=1),
    "id": 1,
    "is_deleted": False,
    "is_enabled": True,
    "is_quick": False,
    "notice_config": {},
    "scope_type": "",
    "update_time": utc_now.datetime,
    "update_user": "admin",
}


class TestShieldTime(object):
    """
    屏蔽测试
    """

    def test_single(self):
        shield = ShieldObj(config)

        assert not shield.time_check.is_match(now + timedelta(minutes=-1))
        assert shield.time_check.is_match(now)
        assert shield.time_check.is_match(now + timedelta(seconds=30))
        assert shield.time_check.is_match(now + timedelta(minutes=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=2))

    def test_day(self):
        shield_config = copy.deepcopy(config)
        shield_config["cycle_config"] = {
            "end_time": (now + timedelta(minutes=1)).strftime("%H:%M:%S"),
            "type": 2,
            "day_list": [],
            "week_list": [],
            "begin_time": now.strftime("%H:%M:%S"),
        }

        shield_config["end_time"] += timedelta(days=2)

        shield = ShieldObj(shield_config)

        assert not shield.time_check.is_match(now + timedelta(minutes=-1))
        assert shield.time_check.is_match(now)
        assert shield.time_check.is_match(now + timedelta(seconds=30))
        assert shield.time_check.is_match(now + timedelta(minutes=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=2))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=1))
        assert shield.time_check.is_match(now + timedelta(days=1))
        assert shield.time_check.is_match(now + timedelta(seconds=30, days=1))
        assert shield.time_check.is_match(now + timedelta(minutes=1, days=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=1))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=2))
        assert shield.time_check.is_match(now + timedelta(days=2))
        assert shield.time_check.is_match(now + timedelta(seconds=30, days=2))
        assert shield.time_check.is_match(now + timedelta(minutes=1, days=2))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=2))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=3))
        assert not shield.time_check.is_match(now + timedelta(days=3))
        assert not shield.time_check.is_match(now + timedelta(seconds=30, days=3))
        assert not shield.time_check.is_match(now + timedelta(minutes=1, days=3))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=3))

    def test_week(self):
        shield_config = copy.deepcopy(config)
        shield_config["cycle_config"] = {
            "end_time": (now + timedelta(minutes=1)).strftime("%H:%M:%S"),
            "type": 3,
            "day_list": [],
            "week_list": [now.weekday() + 1],
            "begin_time": now.strftime("%H:%M:%S"),
        }

        shield_config["end_time"] += timedelta(days=14)

        shield = ShieldObj(shield_config)

        assert not shield.time_check.is_match(now + timedelta(minutes=-1))
        assert shield.time_check.is_match(now)
        assert shield.time_check.is_match(now + timedelta(seconds=30))
        assert shield.time_check.is_match(now + timedelta(minutes=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=2))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=1))
        assert not shield.time_check.is_match(now + timedelta(days=1))
        assert not shield.time_check.is_match(now + timedelta(seconds=30, days=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=1, days=1))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=1))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=7))
        assert shield.time_check.is_match(now + timedelta(days=7))
        assert shield.time_check.is_match(now + timedelta(seconds=30, days=7))
        assert shield.time_check.is_match(now + timedelta(minutes=1, days=7))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=7))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=14))
        assert shield.time_check.is_match(now + timedelta(days=14))
        assert shield.time_check.is_match(now + timedelta(seconds=30, days=14))
        assert shield.time_check.is_match(now + timedelta(minutes=1, days=14))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=14))

        assert not shield.time_check.is_match(now + timedelta(minutes=-1, days=21))
        assert not shield.time_check.is_match(now + timedelta(days=21))
        assert not shield.time_check.is_match(now + timedelta(seconds=30, days=21))
        assert not shield.time_check.is_match(now + timedelta(minutes=1, days=21))
        assert not shield.time_check.is_match(now + timedelta(minutes=2, days=21))

    def test_month(self):
        month_now = now.replace(year=2018, month=1, day=1)

        shield_config = copy.deepcopy(config)
        shield_config["cycle_config"] = {
            "end_time": (month_now + timedelta(minutes=1)).strftime("%H:%M:%S"),
            "type": 4,
            "day_list": [1, 15, 30],
            "week_list": [],
            "begin_time": month_now.strftime("%H:%M:%S"),
        }

        shield_config["begin_time"] = month_now
        shield_config["end_time"] = month_now + timedelta(days=60)

        shield = ShieldObj(shield_config)

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1))
        assert shield.time_check.is_match(month_now)
        assert shield.time_check.is_match(month_now + timedelta(seconds=30))
        assert shield.time_check.is_match(month_now + timedelta(minutes=1))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2))

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1, days=1))
        assert not shield.time_check.is_match(month_now + timedelta(days=1))
        assert not shield.time_check.is_match(month_now + timedelta(seconds=30, days=1))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=1, days=1))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2, days=1))

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1, days=14))
        assert shield.time_check.is_match(month_now + timedelta(days=14))
        assert shield.time_check.is_match(month_now + timedelta(seconds=30, days=14))
        assert shield.time_check.is_match(month_now + timedelta(minutes=1, days=14))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2, days=14))

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1, days=29))
        assert shield.time_check.is_match(month_now + timedelta(days=29))
        assert shield.time_check.is_match(month_now + timedelta(seconds=30, days=29))
        assert shield.time_check.is_match(month_now + timedelta(minutes=1, days=29))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2, days=29))

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1, days=45))
        assert shield.time_check.is_match(month_now + timedelta(days=45))
        assert shield.time_check.is_match(month_now + timedelta(seconds=30, days=45))
        assert shield.time_check.is_match(month_now + timedelta(minutes=1, days=45))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2, days=45))

        assert not shield.time_check.is_match(month_now + timedelta(minutes=-1, days=60))
        assert not shield.time_check.is_match(month_now + timedelta(days=60))
        assert not shield.time_check.is_match(month_now + timedelta(seconds=30, days=60))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=1, days=60))
        assert not shield.time_check.is_match(month_now + timedelta(minutes=2, days=60))
