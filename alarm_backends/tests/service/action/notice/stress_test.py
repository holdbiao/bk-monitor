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
import json
from datetime import datetime

import pytest

from bkmonitor.models import Event, AnomalyRecord, EventAction, Alert, AlertCollect

pytestmark = pytest.mark.django_db


def data_preparation():
    # clean
    EventAction.objects.all().delete()
    Event.objects.all().delete()
    AnomalyRecord.objects.all().delete()

    Alert.objects.all().delete()
    AlertCollect.objects.all().delete()

    events = []
    event_actions = []
    anomaly_records = []

    strategy = {
        "bk_biz_id": 2,
        "item_list": [
            {
                "update_time": 1575980596,
                "data_type_label": "time_series",
                "metric_id": "bk_monitor.system.cpu_summary.usage",
                "item_name": "使用率",
                "strategy_id": 1,
                "data_source_label": "bk_monitor",
                "algorithm_list": [
                    {
                        "algorithm_config": [{"threshold": 10.0, "method": "gte"}],
                        "update_time": 1575980596,
                        "trigger_config": {"count": 3, "check_window": 5},
                        "strategy_id": 157,
                        "level": 1,
                        "algorithm_type": "Threshold",
                        "recovery_config": {"check_window": 5},
                        "create_time": 1575980596,
                        "algorithm_id": 341,
                        "message_template": "",
                        "item_id": 1,
                        "id": 1,
                    }
                ],
                "no_data_config": {"is_enabled": False, "continuous": 5},
                "create_time": 1575980596,
                "rt_query_config_id": 1,
                "item_id": 1,
                "rt_query_config": {
                    "update_time": 1575980596,
                    "metric_field": "usage",
                    "agg_dimension": ["bk_target_ip", "bk_target_cloud_id", "device_name"],
                    "unit_conversion": 1.0,
                    "result_table_id": "system.cpu_summary",
                    "extend_fields": {
                        "result_table_name": "CPU",
                        "data_source_label": "bk_monitor",
                        "related_id": "system",
                    },
                    "create_time": 1575980596,
                    "rt_query_config_id": 1,
                    "agg_method": "AVG",
                    "agg_condition": [],
                    "agg_interval": 60,
                    "id": 1,
                    "unit": "percent",
                },
                "id": 1,
                "name": "使用率",
            }
        ],
        "update_time": 1575980596,
        "target": [
            [
                {
                    "field": "bk_target_ip",
                    "method": "eq",
                    "value": [
                        {"bk_target_ip": "10.0.1.10", "bk_target_cloud_id": 0},
                        {"bk_target_ip": "10.0.1.11", "bk_target_cloud_id": 0},
                    ],
                }
            ]
        ],
        "scenario": "os",
        "strategy_id": 1,
        "action_list": [
            {
                "update_time": 1575980596,
                "notice_template": {
                    "recovery_template": "",
                    "update_time": 1575980596,
                    "create_time": 1575980596,
                    "anomaly_template": "",
                    "action_id": 1,
                },
                "id": 1,
                "notice_group_list": [
                    {
                        "update_time": 1575980551,
                        "notice_receiver": ["group#bk_biz_maintainer"],
                        "name": "运维",
                        "notice_way": {
                            "1": ["weixin", "mail", "sms", "voice"],
                            "3": ["weixin", "mail", "sms", "voice"],
                            "2": ["weixin", "mail", "sms", "voice"],
                        },
                        "create_time": 1575980551,
                        "notice_group_id": 1,
                        "message": "",
                        "notice_group_name": "运维",
                        "id": 1,
                    }
                ],
                "create_time": 1575980596,
                "action_type": "notice",
                "config": {
                    "alarm_end_time": "23:59:59",
                    "send_recovery_alarm": False,
                    "alarm_start_time": "00:00:00",
                    "alarm_interval": 120,
                },
                "strategy_id": 1,
                "action_id": 1,
            }
        ],
        "source": "bk_monitor",
        "strategy_name": "CPU总使用率",
        "create_time": 1575980596,
        "id": 1,
        "name": "CPU总使用率",
    }

    origin_alarm = {
        "data": {
            "record_id": "48af047a4251b9f49b7cdbc66579c23a.1575980880",
            "values": {"usage": 80.32, "time": 1575980880},
            "dimensions": {
                "bk_target_cloud_id": "0",
                "bk_target_ip": "10.0.1.10",
                "bk_topo_node": ["module|6"],
                "device_name": "",
            },
            "value": 80.32,
            "time": 1575980880,
        },
        "trigger": {
            "level": "1",
            "anomaly_ids": [
                "48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
                "48af047a4251b9f49b7cdbc66579c23a.1575980820.1.191.1",
                "48af047a4251b9f49b7cdbc66579c23a.1575980880.1.191.1",
            ],
        },
        "anomaly": {
            "1": {
                "anomaly_message": "avg(usage) >= 10.0, \u5f53\u524d\u503c80.32",
                "anomaly_time": "2019-12-10 12:30:14",
                "anomaly_id": "48af047a4251b9f49b7cdbc66579c23a.1575980880.1.191.1",
            }
        },
        "dimension_translation": {
            "bk_target_cloud_id": {"display_name": "bk_target_cloud_id", "display_value": "0", "value": "0"},
            "bk_target_ip": {"display_name": "bk_target_ip", "display_value": "10.0.1.10", "value": "10.0.1.10"},
            "bk_topo_node": {
                "display_name": "bk_topo_node",
                "display_value": [{"bk_obj_name": "模块", "bk_inst_name": "dataapi"}],
                "value": ["module|6"],
            },
            "device_name": {"display_name": "设备名", "display_value": "", "value": ""},
        },
        "strategy_snapshot_key": "bk_bkmonitor.ee.cache.strategy.snapshot.1.1575980858",
    }

    for i in range(100000):
        origin_alarm = json.loads(json.dumps(origin_alarm))
        origin_alarm["data"]["dimensions"]["device_name"] = str(i)
        origin_alarm["dimension_translation"]["device_name"]["display_value"] = str(i)
        origin_alarm["dimension_translation"]["device_name"]["value"] = str(i)

        anomaly_records.append(
            AnomalyRecord(
                anomaly_id=str(i),
                source_time=datetime.now(),
                strategy_id=1,
                origin_alarm=origin_alarm,
                event_id=str(i),
                count=1,
            )
        )
        events.append(
            Event(
                event_id=str(i),
                begin_time=datetime.now(),
                bk_biz_id=2,
                strategy_id=1,
                origin_alarm=origin_alarm,
                origin_config=strategy,
                level=1,
                target_key="host|127.0.0.1",
            )
        )
        event_actions.append(
            EventAction(
                operate="ANOMALY_NOTICE",
                extend_info={
                    "action": {
                        "strategy_id": 1,
                        "notice_template": {"anomaly_template": "", "action_id": 1, "recovery_template": ""},
                        "notice_group_list": [
                            {
                                "wxwork_group": {},
                                "notice_receiver": [f"user#user{i}" for i in range(20)],
                                "name": "主备负责人",
                                "id": 1,
                                "notice_way": {
                                    "1": ["weixin", "mail"],
                                    "3": ["weixin", "mail"],
                                    "2": ["weixin", "mail"],
                                },
                                "notice_group_id": 1,
                                "webhook_url": "",
                                "notice_group_name": "主备负责人",
                                "message": "",
                            }
                        ],
                        "action_type": "notice",
                        "config": {
                            "alarm_end_time": "23:59:59",
                            "send_recovery_alarm": False,
                            "alarm_start_time": "00:00:00",
                            "alarm_interval": 1440,
                        },
                        "id": 1,
                        "action_id": 1,
                    }
                },
                status="RUNNING",
                event_id=str(i),
            )
        )

    Event.objects.bulk_create(events, batch_size=500)
    EventAction.objects.bulk_create(event_actions, batch_size=500)
    AnomalyRecord.objects.bulk_create(anomaly_records, batch_size=500)
