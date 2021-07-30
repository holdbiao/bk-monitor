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


import pytest

from alarm_backends.core.cache.strategy import StrategyCacheManager

pytestmark = pytest.mark.django_db


item = {
    "rt_query_config": {
        "agg_method": "AVG",
        "agg_dimension": ["ip", "bk_cloud_id"],
        "unit_conversion": 1.0,
        "agg_condition": [
            {"value": "0", "method": "eq", "key": "bk_cloud_id"},
            {"value": "10.0.1.11", "key": "bk_target_ip", "condition": "or", "method": "eq"},
        ],
        "agg_interval": 60,
        "extend_fields": "",
        "metric_field": "usage",
        "result_table_id": "system.cpu_summary",
        "unit": "%",
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


class TestStrategyGroup(object):
    def test_query_config_md5(self):
        query_md5 = StrategyCacheManager.get_query_md5(2, item)
        assert query_md5 == "4ca8defa2aed29a8371e665b610a2044"
        item["rt_query_config"]["agg_condition"] = [
            {"value": "10.0.1.11", "key": "bk_target_ip", "method": "eq"},
            {"value": "0", "method": "eq", "key": "bk_cloud_id", "condition": "or"},
        ]
        query_md5 = StrategyCacheManager.get_query_md5(2, item)
        assert query_md5 == "6e2170c2323fb98bdb9c31f6416cfd9e"

        item["rt_query_config"]["agg_condition"] = []
        empty_condition_query_md5 = StrategyCacheManager.get_query_md5(2, item)

        item["rt_query_config"]["agg_condition"] = [{"value": "10.0.1.11", "key": "bk_target_ip", "method": "reg"}]
        query_md5 = StrategyCacheManager.get_query_md5(2, item)
        assert empty_condition_query_md5 == query_md5

    def test_cache(self):
        pass
