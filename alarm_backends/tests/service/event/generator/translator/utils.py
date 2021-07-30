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
from __future__ import absolute_import, unicode_literals

import copy

ITEM = {
    "rt_query_config": {
        "metric_field": "idle",
        "agg_dimension": ["ip", "bk_cloud_id"],
        "unit_conversion": 1.0,
        "id": 2,
        "extend_fields": {},
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
}

STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [ITEM],
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


def generate_test_strategy(data_source_label, data_type_label, result_table_id, extend_fields=None):
    item = copy.deepcopy(ITEM)
    item["data_source_label"] = data_source_label
    item["data_type_label"] = data_type_label
    item["rt_query_config"]["result_table_id"] = result_table_id
    item["rt_query_config"]["extend_fields"] = extend_fields
    strategy = copy.deepcopy(STRATEGY)
    strategy["item_list"] = [item]
    return {
        "strategy": strategy,
        "item": item,
    }
