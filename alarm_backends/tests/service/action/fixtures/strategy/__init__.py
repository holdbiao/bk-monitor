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


from collections import defaultdict

import pytest

from api.cmdb.define import Business
from bkmonitor.models import *  # noqa

from .os_time_series import os_time_series_run

StrategyMapping = defaultdict(os_time_series_run, {"os_time_series": os_time_series_run})


def clean_data():
    Event.objects.all().delete()
    EventAction.objects.all().delete()
    AnomalyRecord.objects.all().delete()
    Alert.objects.all().delete()
    AlertCollect.objects.all().delete()


@pytest.fixture
def strategy(mocker, request):
    clean_data()
    params = getattr(request, "param", {})

    path = params.get("path", "alarm_backends.core.control.strategy.StrategyCacheManager.get_strategy_by_id")
    _type = params.get("type", "os_time_series")
    strategy_config, event_action = StrategyMapping[_type]()
    mocker.patch(path, return_value=strategy_config)

    mocker.patch(
        "alarm_backends.core.cache.cmdb.BusinessManager.get",
        return_value=Business(
            **{
                "bk_biz_id": 2,
                "bk_biz_name": "蓝鲸",
                "bk_biz_developer": ["admin"],
                "bk_biz_maintainer": ["admin"],
                "bk_biz_tester": ["admin"],
                "bk_biz_productor": ["admin"],
                "time_zone": "Asia/Shanghai",
                "language": "1",
            }
        ),
    )

    yield event_action
    clean_data()
