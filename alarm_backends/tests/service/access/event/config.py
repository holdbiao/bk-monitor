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

from api.cmdb.define import Host, TopoNode

now = arrow.now()
utc_now = now.to("utc")
now_str = str(now.to("local").naive)
utc_now_str = str(now.to("utc").naive)
utc_timestamp = now.timestamp

AGENT_LOSE_DATA = {
    "utctime2": utc_now_str,
    "value": [
        {
            "event_raw_id": 29,
            "event_type": "gse_basic_alarm_type",
            "event_time": utc_now_str,
            "extra": {"count": 1, "host": [{"ip": "127.0.0.10", "cloudid": 0, "bizid": 0}], "type": 2},
            "event_title": "",
            "event_desc": "",
            "event_source_system": "",
        }
    ],
    "server": "127.0.0.11",
    "utctime": utc_now_str,
    "time": utc_now_str,
    "timezone": 8,
}

AGENT_LOSE_DATA_CLEAN = {
    "data": {
        "record_id": "393445ecd532f1134ff370bddaf261d9.{}".format(utc_timestamp),
        "values": {"value": "", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.0.10",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "",
        "time": utc_timestamp,
    },
    "anomaly": {
        3: {
            "anomaly_message": "GSE AGENT \u5931\u8054",
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "393445ecd532f1134ff370bddaf261d9.{}.31.54.3".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.31.1572868513",
}

AGENT_LOSE_STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "update_time": 1572868513,
            "data_type_label": "event",
            "metric_id": "bk_monitor.agent-gse",
            "item_name": "Agent\u5fc3\u8df3\u4e22\u5931",
            "strategy_id": 31,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "update_time": 1572868513,
                    "trigger_config": {"count": 1, "check_window": 10},
                    "strategy_id": 31,
                    "level": 3,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 10},
                    "create_time": 1572868513,
                    "algorithm_id": 90,
                    "message_template": "",
                    "item_id": 54,
                    "id": 90,
                }
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "create_time": 1572868513,
            "rt_query_config_id": 0,
            "item_id": 54,
            "rt_query_config": {},
            "id": 54,
            "name": "Agent\u5fc3\u8df3\u4e22\u5931",
        }
    ],
    "update_time": 1572868513,
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_ip": "127.0.0.10", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.11", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.16", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.9", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.8", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.4", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.45", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.80", "bk_target_cloud_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 31,
    "action_list": [
        {
            "update_time": 1572868513,
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "id": 52,
            "notice_group_list": [],
            "create_time": 1572868513,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "strategy_id": 31,
            "action_id": 52,
        }
    ],
    "source_type": "BASEALARM",
    "strategy_name": "Agent\u5fc3\u8df3\u4e22\u5931-test",
    "create_time": 1572868513,
    "id": 31,
    "name": "Agent\u5fc3\u8df3\u4e22\u5931-test",
}

PING_UNREACH_DATA = {
    "server": "127.0.0.11",
    "time": now,
    "value": [
        {
            "event_desc": "",
            "event_raw_id": 27422,
            "event_source_system": "",
            "event_time": utc_now_str,
            "event_timezone": 0,
            "event_title": "",
            "event_type": "gse_basic_alarm_type",
            "extra": {
                "bizid": 0,
                "cloudid": 0,
                "count": 30,
                "host": "127.0.0.11",
                "iplist": [
                    "127.0.0.10",
                    "127.0.0.16",
                ],
                "type": 8,
            },
        }
    ],
}

PING_UNREACH_DATA_CLEAN = {
    "data": {
        "record_id": "393445ecd532f1134ff370bddaf261d9.{}".format(utc_timestamp),
        "values": {"value": "", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.0.10",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "",
        "time": utc_timestamp,
    },
    "anomaly": {
        1: {
            "anomaly_message": "Ping不可达",
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "393445ecd532f1134ff370bddaf261d9.{}.35.58.1".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.35.1572868637",
}

PING_UNREACH_STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "update_time": 1572868637,
            "data_type_label": "event",
            "metric_id": "bk_monitor.ping-gse",
            "item_name": "PING\u4e0d\u53ef\u8fbe\u544a\u8b66",
            "strategy_id": 35,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "update_time": 1572868637,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "strategy_id": 35,
                    "level": 1,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 5},
                    "create_time": 1572868637,
                    "algorithm_id": 94,
                    "message_template": "",
                    "item_id": 58,
                    "id": 94,
                }
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "create_time": 1572868637,
            "rt_query_config_id": 0,
            "item_id": 58,
            "rt_query_config": {},
            "id": 58,
            "name": "PING\u4e0d\u53ef\u8fbe\u544a\u8b66",
        }
    ],
    "update_time": 1572868637,
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_ip": "127.0.0.10", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.11", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.16", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.9", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.8", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.4", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.45", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.80", "bk_target_cloud_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 35,
    "action_list": [
        {
            "update_time": 1572868637,
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "id": 56,
            "notice_group_list": [],
            "create_time": 1572868637,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "strategy_id": 35,
            "action_id": 56,
        }
    ],
    "source_type": "BASEALARM",
    "strategy_name": "Ping\u4e0d\u53ef\u8fbe-test",
    "create_time": 1572868637,
    "id": 35,
    "name": "Ping\u4e0d\u53ef\u8fbe-test",
}

DISK_READ_ONLY_DATA = {
    "isdst": 0,
    "utctime2": utc_now_str,
    "value": [
        {
            "event_raw_id": 5853,
            "event_type": "gse_basic_alarm_type",
            "event_time": utc_now_str,
            "extra": {
                "cloudid": 0,
                "host": "127.0.0.10",
                "ro": [
                    {"position": r"\/sys\/fs\/cgroup", "fs": "tmpfs", "type": "tmpfs"},
                    {"position": r"\/readonly_disk", "fs": r"dev\/vdb", "type": "ext4"},
                ],
                "type": 3,
                "bizid": 0,
            },
            "event_title": "",
            "event_desc": "",
            "event_source_system": "",
        }
    ],
    "server": "127.0.0.11",
    "utctime": utc_now_str,
    "time": utc_now_str,
    "timezone": 8,
}

DISK_READ_ONLY_DATA_CLEAN = {
    "data": {
        "record_id": "393445ecd532f1134ff370bddaf261d9.{}".format(utc_timestamp),
        "values": {"value": "", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.0.10",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "",
        "time": utc_timestamp,
    },
    "anomaly": {
        2: {
            "anomaly_message": ("磁盘(tmpfs-tmpfs(\\/sys\\/fs\\/cgroup), dev\\/vdb-ext4(\\/readonly_disk))只读告警"),
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "393445ecd532f1134ff370bddaf261d9.{}.31.55.2".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.31.1572868543",
}

DISK_READ_ONLY_STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "update_time": 1572868543,
            "data_type_label": "event",
            "metric_id": "bk_monitor.disk-readonly-gse",
            "item_name": "\u78c1\u76d8\u53ea\u8bfb",
            "strategy_id": 32,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "update_time": 1572868543,
                    "trigger_config": {"count": 1, "check_window": 10},
                    "strategy_id": 32,
                    "level": 2,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 10},
                    "create_time": 1572868543,
                    "algorithm_id": 91,
                    "message_template": "",
                    "item_id": 55,
                    "id": 91,
                }
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "create_time": 1572868543,
            "rt_query_config_id": 0,
            "item_id": 55,
            "rt_query_config": {},
            "id": 55,
            "name": "\u78c1\u76d8\u53ea\u8bfb",
        }
    ],
    "update_time": 1572868543,
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_ip": "127.0.0.10", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.11", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.16", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.9", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.8", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.4", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.45", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.80", "bk_target_cloud_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 32,
    "action_list": [
        {
            "update_time": 1572868543,
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "id": 53,
            "notice_group_list": [],
            "create_time": 1572868543,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "strategy_id": 32,
            "action_id": 53,
        }
    ],
    "source_type": "BASEALARM",
    "strategy_name": "\u78c1\u76d8\u53ea\u8bfb-test",
    "create_time": 1572868543,
    "id": 32,
    "name": "\u78c1\u76d8\u53ea\u8bfb-test",
}

DISK_FULL_DATA = {
    "isdst": 0,
    "utctime2": utc_now_str,
    "value": [
        {
            "event_raw_id": 7795,
            "event_type": "gse_basic_alarm_type",
            "event_time": utc_now_str,
            "extra": {
                "used_percent": 93,
                "used": 45330684,
                "cloudid": 0,
                "free": 7,
                "fstype": "ext4",
                "host": "127.0.0.10",
                "disk": "/",
                "file_system": "/dev/vda1",
                "size": 51473888,
                "bizid": 0,
                "avail": 3505456,
                "type": 6,
            },
            "event_title": "",
            "event_desc": "",
            "event_source_system": "",
        }
    ],
    "server": "127.0.0.10",
    "utctime": utc_now_str,
    "time": utc_now_str,
    "timezone": 8,
}

DISK_FULL_DATA_CLEAN = {
    "data": {
        "record_id": "393445ecd532f1134ff370bddaf261d9.{}".format(utc_timestamp),
        "values": {"value": "", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.0.10",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "",
        "time": utc_timestamp,
    },
    "anomaly": {
        3: {
            "anomaly_message": "磁盘(/)剩余空间只有7%",
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "393445ecd532f1134ff370bddaf261d9.{}.31.64.3".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.31.1573030943",
}

DISK_FULL_STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "update_time": 1573030943,
            "data_type_label": "event",
            "metric_id": "bk_monitor.disk-full-gse",
            "item_name": "\u78c1\u76d8\u5199\u6ee1",
            "strategy_id": 33,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "update_time": 1573030943,
                    "trigger_config": {"count": 1, "check_window": 5},
                    "strategy_id": 33,
                    "level": 3,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 5},
                    "create_time": 1573030943,
                    "algorithm_id": 113,
                    "message_template": "",
                    "item_id": 64,
                    "id": 113,
                }
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "create_time": 1573030943,
            "rt_query_config_id": 0,
            "item_id": 64,
            "rt_query_config": {},
            "id": 64,
            "name": "\u78c1\u76d8\u5199\u6ee1",
        }
    ],
    "update_time": 1573030943,
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_ip": "127.0.0.10", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.80", "bk_target_cloud_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 33,
    "action_list": [
        {
            "update_time": 1573030943,
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "id": 54,
            "notice_group_list": [],
            "create_time": 1572868571,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 118,
            },
            "strategy_id": 33,
            "action_id": 54,
        }
    ],
    "source_type": "BASEALARM",
    "strategy_name": "\u78c1\u76d8\u5199\u6ee1-test",
    "create_time": 1572868571,
    "id": 33,
    "name": "\u78c1\u76d8\u5199\u6ee1-test",
}

COREFILE_DATA = {
    "isdst": 0,
    "server": "127.0.0.11",
    "time": now,
    "timezone": 8,
    "utctime": now,
    "utctime2": utc_now_str,
    "value": [
        {
            "event_desc": "",
            "event_raw_id": 11,
            "event_source_system": "",
            "event_time": utc_now_str,
            "event_title": "",
            "event_type": "gse_basic_alarm_type",
            "extra": {
                "bizid": 0,
                "cloudid": 0,
                "corefile": "/data/corefile/core_101041_2019-11-04",
                "filesize": "0",
                "host": "127.0.0.10",
                "type": 7,
            },
        }
    ],
}

COREFILE_DATA_CLEAN = {
    "data": {
        "record_id": "393445ecd532f1134ff370bddaf261d9.{}".format(utc_timestamp),
        "values": {"value": "", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.0.10",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "",
        "time": utc_timestamp,
    },
    "anomaly": {
        1: {
            "anomaly_message": "产生corefile：/data/corefile/core_101041_2019-11-04",
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "393445ecd532f1134ff370bddaf261d9.{}.31.57.1".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.31.1572868604",
}

COREFILE_STRATEGY = {
    "bk_biz_id": 2,
    "item_list": [
        {
            "update_time": 1572868604,
            "data_type_label": "event",
            "metric_id": "bk_monitor.corefile-gse",
            "item_name": "Corefile\u4ea7\u751f",
            "strategy_id": 34,
            "data_source_label": "bk_monitor",
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "update_time": 1572868604,
                    "trigger_config": {"count": 1, "check_window": 5},
                    "strategy_id": 34,
                    "level": 1,
                    "algorithm_type": "",
                    "recovery_config": {"check_window": 5},
                    "create_time": 1572868604,
                    "algorithm_id": 93,
                    "message_template": "",
                    "item_id": 57,
                    "id": 93,
                }
            ],
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "create_time": 1572868604,
            "rt_query_config_id": 0,
            "item_id": 57,
            "rt_query_config": {},
            "id": 57,
            "name": "Corefile\u4ea7\u751f",
        }
    ],
    "update_time": 1572868604,
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_ip": "127.0.0.10", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.11", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.16", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.9", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.8", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.4", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.45", "bk_target_cloud_id": 0},
                    {"bk_target_ip": "127.0.0.80", "bk_target_cloud_id": 0},
                ],
            }
        ]
    ],
    "scenario": "os",
    "strategy_id": 34,
    "action_list": [
        {
            "update_time": 1572868604,
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "id": 55,
            "notice_group_list": [],
            "create_time": 1572868604,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "strategy_id": 34,
            "action_id": 55,
        }
    ],
    "source_type": "BASEALARM",
    "strategy_name": "corefile\u4ea7\u751f-test",
    "create_time": 1572868604,
    "id": 34,
    "name": "corefile\u4ea7\u751f-test",
}

CUSTOM_STR_DATA = {
    "_bizid_": 0,
    "_cloudid_": 0,
    "_server_": "127.0.0.11",
    "_time_": now,
    "_utctime_": utc_now_str,
    "_value_": ["This service is offline"],
}

GSE_PROCESS_EVENT_DATA = {
    "data": [
        {
            "dimension": {
                "bk_target_cloud_id": "0",
                "bk_target_ip": "10.0.1.10",
                "process_group_id": "nodeman",
                "process_index": "nodeman:bkmonitorbeat",
                "process_name": "bkmonitorbeat",
            },
            "event": {"content": "check bkmonitorbeat not running, and restart it success"},
            "event_name": "process_restart_success",
            "target": "10.0.1.10|0",
            "timestamp": 1619171000,
        }
    ],
    "data_id": 1100008,
}
GSE_PROCESS_EVENT_DATA_CLEAN = {
    "data": {
        "time": 1619171,
        "value": "事件类型: 进程重启成功, 事件内容: check bkmonitorbeat not running, and restart it success",
        "values": {
            "time": 1619171,
            "value": "事件类型: 进程重启成功, 事件内容: check bkmonitorbeat not running, and restart it success",
        },
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "10.0.1.10",
            "process_group_id": "nodeman",
            "process_index": "nodeman:bkmonitorbeat",
            "process_name": "bkmonitorbeat",
            "event_name": "process_restart_success",
            "bk_topo_node": ["biz|2", "module|9", "set|5", "test|2"],
        },
        "record_id": "fc5cbf03760931e26a886ba9e6b81ab9.{}".format(1619171),
    },
    "anomaly": {
        2: {
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "fc5cbf03760931e26a886ba9e6b81ab9.{}.31.449.2".format(1619171),
            "anomaly_message": "事件类型: 进程重启成功, 事件内容: check bkmonitorbeat not running, and restart it success",
        }
    },
    "strategy_snapshot_key": "bk_bkmonitorv3.ee.cache.strategy.snapshot.209.1617956776",
}
CUSTOM_STR_DATA_CLEAN = {
    "data": {
        "record_id": "85d626c1d6b59e8ef4cdab19324405dd.{}".format(utc_timestamp),
        "values": {"value": "This service is offline", "time": utc_timestamp},
        "dimensions": {
            "bk_target_cloud_id": 0,
            "bk_target_ip": "127.0.1.11",
            "bk_topo_node": sorted({"biz|2", "test|2", "set|5", "module|9"}),
        },
        "value": "This service is offline",
        "time": utc_timestamp,
    },
    "anomaly": {
        2: {
            "anomaly_message": "This service is offline",
            "anomaly_time": arrow.get(utc_timestamp).format("YYYY-MM-DD HH:mm:ss"),
            "anomaly_id": "85d626c1d6b59e8ef4cdab19324405dd.{}.31.53.2".format(utc_timestamp),
        }
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.31.1572868423",
}

CUSTOM_STR_STRATEGY = {
    "action_list": [
        {
            "action_id": 51,
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "alarm_interval": 120,
                "alarm_start_time": "00:00:00",
                "send_recovery_alarm": False,
            },
            "create_time": 1572868423,
            "id": 51,
            "notice_group_list": [],
            "notice_template": {"anomaly_template": "", "id": 0, "recovery_template": ""},
            "strategy_id": 30,
            "update_time": 1572868423,
        }
    ],
    "bk_biz_id": 2,
    "create_time": 1572868423,
    "id": 30,
    "item_list": [
        {
            "algorithm_list": [
                {
                    "algorithm_config": "",
                    "algorithm_id": 89,
                    "algorithm_type": "",
                    "create_time": 1572868423,
                    "id": 89,
                    "item_id": 53,
                    "level": 2,
                    "message_template": "",
                    "recovery_config": {"check_window": 5},
                    "strategy_id": 30,
                    "trigger_config": {"check_window": 5, "count": 1},
                    "update_time": 1572868423,
                }
            ],
            "create_time": 1572868423,
            "data_source_label": "bk_monitor",
            "data_type_label": "event",
            "id": 53,
            "item_id": 53,
            "item_name": "\u81ea\u5b9a\u4e49\u5b57\u7b26\u578b\u544a\u8b66",
            "metric_id": "bk_monitor.gse_custom_event",
            "name": "\u81ea\u5b9a\u4e49\u5b57\u7b26\u578b\u544a\u8b66",
            "no_data_config": {"continuous": 5, "is_enabled": False},
            "rt_query_config": {},
            "rt_query_config_id": 0,
            "strategy_id": 30,
            "update_time": 1572868423,
        }
    ],
    "name": "\u81ea\u5b9a\u4e49\u5b57\u7b26\u578b-bond",
    "scenario": "os",
    "source_type": "BASEALARM",
    "strategy_id": 30,
    "strategy_name": "\u81ea\u5b9a\u4e49\u5b57\u7b26\u578b-bond",
    "target": [
        [
            {
                "field": "bk_target_ip",
                "method": "eq",
                "value": [
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.10"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.11"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.16"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.9"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.8"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.4"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.45"},
                    {"bk_target_cloud_id": 0, "bk_target_ip": "10.0.1.80"},
                ],
            }
        ]
    ],
    "update_time": 1572868423,
}

PROCESS_EVENT_STRATEGY = {
    "id": 441,
    "strategy_id": 441,
    "name": "Gse\u8fdb\u7a0b\u6258\u7ba1\u4e8b\u4ef6\u544a\u8b66(\u5e73\u53f0\u4fa7)",
    "strategy_name": "Gse\u8fdb\u7a0b\u6258\u7ba1\u4e8b\u4ef6\u544a\u8b66(\u5e73\u53f0\u4fa7)",
    "bk_biz_id": 18,
    "scenario": "host_process",
    "is_enabled": True,
    "update_time": "2021-04-21 21:35:06+0800",
    "update_user": "system",
    "create_time": "2021-04-21 21:35:06+0800",
    "create_user": "system",
    "action_list": [
        {
            "id": 432,
            "action_id": 432,
            "config": {
                "alarm_start_time": "00:00:00",
                "alarm_end_time": "23:59:59",
                "alarm_interval": 1440,
                "send_recovery_alarm": False,
            },
            "action_type": "notice",
            "notice_group_list": [
                {"id": 63, "display_name": "\u3010\u84dd\u9cb8\u3011\u5b98\u65b9\u63d2\u4ef6\u7ba1\u7406\u5458"}
            ],
            "notice_group_id_list": [63],
        }
    ],
    "item_list": [
        {
            "id": 449,
            "item_id": 449,
            "name": "Gse\u8fdb\u7a0b\u6258\u7ba1\u4e8b\u4ef6\u544a\u8b66(\u5e73\u53f0\u4fa7)",
            "item_name": "Gse\u8fdb\u7a0b\u6258\u7ba1\u4e8b\u4ef6\u544a\u8b66(\u5e73\u53f0\u4fa7)",
            "strategy_id": 441,
            "update_time": "2021-04-21 21:35:06+0800",
            "create_time": "2021-04-21 21:35:06+0800",
            "metric_id": "bk_monitor.gse_process_event",
            "target": [
                [{"field": "host_topo_node", "value": [{"bk_obj_id": "biz", "bk_inst_id": 18}], "method": "eq"}]
            ],
            "rt_query_config_id": 376,
            "data_source_label": "bk_monitor",
            "data_type_label": "event",
            "unit_conversion": 1,
            "extend_fields": {},
            "result_table_id": "system.event",
            "metric_field": "gse_process_event",
            "agg_condition": [
                {
                    "key": "process_name",
                    "value": [
                        "basereport",
                        "processbeat",
                        "exceptionbeat",
                        "bkmonitorbeat",
                        "bkmonitorproxy",
                        "bkunifylogbeat",
                    ],
                    "method": "include",
                }
            ],
            "algorithm_list": [
                {
                    "id": 395,
                    "algorithm_id": 395,
                    "algorithm_type": "",
                    "algorithm_unit": "",
                    "algorithm_config": [],
                    "level": 2,
                    "trigger_config": {"count": 1, "check_window": 5},
                    "recovery_config": {"check_window": 5},
                    "message_template": "{{content.level}}\n{{content.begin_time}}\n{{content.time}}\n{{content.duration}}\n{{content.target_type}}\n{{content.data_source}}\n{{content.content}}\n{{content.current_value}}\n{{content.biz}}\n{{content.target}}\n{{content.dimension}}\n{{content.detail}}\n{{content.related_info}}",
                }
            ],
            "metric_description": "\u6570\u636e\u6765\u6e90\uff1a\u7cfb\u7edf\u4e8b\u4ef6",
            "unit_suffix_list": [],
            "unit_suffix_id": "",
            "remarks": [],
        }
    ],
}

#####
HOST_OBJECT = Host(
    bk_host_innerip="127.0.1.11",
    bk_cloud_id=0,
    bk_host_id=2,
    bk_biz_id=2,
    bk_cloud_name="default area",
    bk_host_outerip="",
    bk_host_name="VM_1_11_centos",
    bk_os_name="linux centos",
    bk_os_version="7.4.1708",
    bk_os_type="1",
    bk_set_ids="",
    bk_module_ids=[1],
    bk_bak_operator="test",
    operator="test",
    topo_link={
        "module|9": [
            TopoNode("module", 9),
            TopoNode("set", 5),
            TopoNode("test", 2),
            TopoNode("biz", 2),
        ]
    },
)
