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

from bkmonitor.models import AnomalyRecord, EventAction, Event


def os_time_series_run():
    # CPU总使用率
    # 静态阈值大于10%
    strategy = {
        "bk_biz_id": 2,
        "item_list": [
            {
                "update_time": 1575980596,
                "data_type_label": "time_series",
                "metric_id": "bk_monitor.system.cpu_summary.usage",
                "item_name": "\\u4f7f\\u7528\\u7387",
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
                    "agg_dimension": ["bk_target_ip", "bk_target_cloud_id"],
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
                "name": "\\u4f7f\\u7528\\u7387",
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
                        "name": "\\u8fd0\\u7ef4",
                        "notice_way": {
                            "1": ["weixin", "mail", "sms", "voice"],
                            "3": ["weixin", "mail", "sms", "voice"],
                            "2": ["weixin", "mail", "sms", "voice"],
                        },
                        "create_time": 1575980551,
                        "notice_group_id": 1,
                        "message": "",
                        "notice_group_name": "\\u8fd0\\u7ef4",
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
        "strategy_name": "CPU\\u603b\\u4f7f\\u7528\\u7387",
        "create_time": 1575980596,
        "id": 1,
        "name": "CPU\\u603b\\u4f7f\\u7528\\u7387",
    }

    origin_alarm = {
        "data": {
            "record_id": "48af047a4251b9f49b7cdbc66579c23a.1575980880",
            "values": {"usage": 80.32, "time": 1575980880},
            "dimensions": {"bk_target_cloud_id": "0", "bk_target_ip": "10.0.1.10", "bk_topo_node": ["module|6"]},
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
                "display_value": [{"bk_obj_name": "\u6a21\u5757", "bk_inst_name": "dataapi"}],
                "value": ["module|6"],
            },
        },
        "strategy_snapshot_key": "bk_bkmonitor.ee.cache.strategy.snapshot.1.1575980858",
    }

    AnomalyRecord.objects.create(
        anomaly_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
        event_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=1,
    )

    AnomalyRecord.objects.create(
        anomaly_id="48af047a4251b9f49b7cdbc66579c23a.1575980820.1.191.1",
        event_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=1,
    )

    AnomalyRecord.objects.create(
        anomaly_id="48af047a4251b9f49b7cdbc66579c23a.1575980880.1.191.1",
        event_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=1,
    )

    Event.objects.create(
        event_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
        begin_time=arrow.now().datetime,
        bk_biz_id=2,
        strategy_id=1,
        origin_alarm=origin_alarm,
        origin_config=strategy,
        level=1,
        status=Event.EventStatus.ABNORMAL,
    )

    event_action = EventAction.objects.create(
        create_time=arrow.now().datetime,
        operate=EventAction.Operate.ANOMALY_NOTICE,
        extend_info={"action": {"notice_template": {"anomaly_template": "", "recovery_template": ""}}},
        status=EventAction.Status.RUNNING,
        event_id="48af047a4251b9f49b7cdbc66579c23a.1575980760.1.191.1",
    )

    return strategy, event_action
