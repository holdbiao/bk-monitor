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


RAW_DATA = {"bk_target_ip": "127.0.0.1", "load5": 1.381234, "bk_target_cloud_id": "0", "_time_": 1569246480000}
RAW_DATA_ZERO = {"bk_target_ip": "127.0.0.2", "load5": 0, "bk_target_cloud_id": "0", "_time_": 1569246480000}
RAW_DATA_NONE = {"bk_target_ip": "127.0.0.3", "load5": None, "bk_target_cloud_id": "0", "_time_": 1569246480000}

EVENT_RAW_DATA = {
    "_time_": "2020-06-16 12:35:06",
    "_type_": 8,
    "_bizid_": 0,
    "_cloudid_": 0,
    "_server_": "127.0.0.1",
    "_host_": "127.0.0.1",
    "_title_": "",
    "dimensions": {"bk_target_ip": "127.0.0.1", "bk_target_cloud_id": 0},
}

CORE_FILE_RAW_DATA = {
    "_time_": "2020-06-16 12:35:06",
    "_type_": 7,
    "_bizid_": 0,
    "_cloudid_": 0,
    "_server_": "127.0.0.1",
    "_host_": "127.0.0.1",
    "_title_": "",
    "_extra_": {
        "bizid": 0,
        "cloudid": 0,
        "corefile": "/data/corefile/core_101041_2018-03-10",
        "filesize": "0",
        "host": "127.0.0.1",
        "type": 7,
    },
}


FORMAT_RAW_DATA = {"bk_target_ip": "127.0.0.1", "load5": 1.38, "bk_target_cloud_id": "0", "_time_": 1569246480}

STANDARD_DATA = {
    "record_id": "ac6847eefd664275c7b3693829f68bab.1569246480",
    "value": 1.38,
    "values": {"time": 1569246480, "load5": 1.38},
    "dimensions": {"bk_target_ip": "127.0.0.1", "bk_target_cloud_id": "0"},
    "time": 1569246480,
}


STRATEGY_CONFIG = {
    "is_enabled": True,
    "update_time": 1569044491,
    "update_user": "admin",
    "action_list": [
        {
            "notice_template": {"anomaly_template": "", "recovery_template": ""},
            "notice_group_list": [
                {
                    "notice_way": {"1": ["sms"], "3": ["weixin"], "2": ["mail"]},
                    "notice_receiver": ["group#Maintainers"],
                    "id": 1,
                    "name": "ada",
                }
            ],
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "id": 1,
            "action_id": 1,
        }
    ],
    "create_user": "admin",
    "create_time": 1569044491,
    "id": 1,
    "target": [
        [{"field": "bk_target_ip", "method": "eq", "value": [{"bk_target_ip": "127.0.0.1", "bk_target_cloud_id": 0}]}]
    ],
    "bk_biz_id": 2,
    "item_list": [
        {
            "rt_query_config": {
                "metric_field": "load5",
                "agg_dimension": ["bk_target_ip", "bk_target_cloud_id"],
                "unit_conversion": 1.0,
                "id": 2,
                "extend_fields": "",
                "rt_query_config_id": 2,
                "agg_method": "AVG",
                "agg_condition": [],
                "agg_interval": 60,
                "result_table_id": "system.cpu_load",
                "unit": "%",
            },
            "algorithm_list": [
                {
                    "algorithm_config": [{"threshold": 12.0, "method": "gte"}],
                    "level": 1,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 1,
                    "id": 1,
                },
                {
                    "algorithm_config": [{"threshold": 12.0, "method": "gte"}],
                    "level": 2,
                    "trigger_config": {"count": 2, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 1,
                    "id": 2,
                },
                {
                    "algorithm_config": [{"threshold": 12.0, "method": "gte"}],
                    "level": 3,
                    "trigger_config": {"count": 1, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 1,
                    "id": 3,
                },
            ],
            "item_id": 1,
            "data_source_label": "bk_monitor",
            "name": "\\u7a7a\\u95f2\\u7387",
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "item_name": "\\u7a7a\\u95f2\\u7387",
            "data_type_label": "time_series",
            "id": 1,
            "metric_id": "system.cpu_detail.idle",
            "create_time": 1569044491,
            "update_time": 1569044491,
        }
    ],
    "name": "test",
    "scenario": "os",
    "source_type": "BKMONITOR",
    "strategy_id": 1,
    "strategy_name": "test",
}

EVENT_STRATEGY_CONFIG = {
    "bk_biz_id": 2,
    "name": "自定义字符型",
    "scenario": "os",
    "update_user": "admin",
    "source": "bk_monitorv3",
    "id": 1,
    "target": "",
    "create_user": "admin",
    "create_time": 1587992788,
    "update_time": 1591255506,
    "strategy_id": 1,
    "strategy_name": "自定义字符型",
    "item_list": [
        {
            "strategy_id": 1,
            "no_data_config": {"continuous": 5, "is_enabled": False},
            "metric_id": "bk_monitor.ping-gse",
            "id": 1,
            "name": "PING不可达",
            "data_type_label": "event",
            "data_source_label": "bk_monitor",
            "rt_query_config_id": 0,
            "create_time": 1587992788,
            "update_time": 1591255506,
            "target": [
                [
                    {
                        "field": "bk_target_ip",
                        "method": "eq",
                        "value": [{"bk_target_ip": "127.0.0.1", "bk_target_cloud_id": 0}],
                    },
                ]
            ],
            "item_id": 1,
            "item_name": "PING不可达",
            "rt_query_config": {},
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "trigger_config": {"count": 1, "check_window": 5},
                    "strategy_id": 1,
                    "level": 2,
                    "id": 1,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 5},
                    "message_template": "",
                    "item_id": 1,
                    "create_time": 1591255506,
                    "update_time": 1591255506,
                    "algorithm_id": 1,
                }
            ],
            "query_md5": "",
        }
    ],
    "action_list": [
        {
            "strategy_id": 1,
            "action_type": "notice",
            "config": {
                "alarm_interval": 1440,
                "alarm_end_time": "23:59:00",
                "alarm_start_time": "00:00:00",
                "send_recovery_alarm": False,
            },
            "id": 1,
            "create_time": 1587992788,
            "update_time": 1591255506,
            "action_id": 1,
            "notice_template": {
                "anomaly_template": "",
                "recovery_template": "",
                "action_id": 1,
                "create_time": 1591255486,
                "update_time": 1591255496,
            },
            "notice_group_list": [
                {
                    "notice_receiver": ["group#operator", "group#bk_bak_operator"],
                    "name": "主备负责人",
                    "webhook_url": "",
                    "notice_way": {"1": ["mail"], "2": ["mail"], "3": ["mail"]},
                    "message": "",
                    "id": 1,
                    "create_time": 1587992787,
                    "update_time": 1588689950,
                    "notice_group_id": 1,
                    "notice_group_name": "主备负责人",
                }
            ],
        }
    ],
}
