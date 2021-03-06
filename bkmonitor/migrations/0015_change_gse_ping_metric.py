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
# Generated by user on 2020-08-06 16:41

from django.db import migrations


def change_gse_ping_metric(apps, schema_editor):
    """
    将PING不可达指标，由事件指标，变更为时序指标
    """
    Item = apps.get_model("bkmonitor", "Item")
    DetectAlgorithm = apps.get_model("bkmonitor", "DetectAlgorithm")
    ResultTableSQLConfig = apps.get_model("bkmonitor", "ResultTableSQLConfig")

    items = Item.objects.filter(metric_id="bk_monitor.ping-gse")
    for item in items:
        try:
            rt_config = ResultTableSQLConfig.objects.create(
                **{
                    "result_table_id": "pingserver.base",
                    "agg_method": "MAX",
                    "agg_interval": "60",
                    "agg_dimension": ["bk_target_ip", "bk_target_cloud_id", "ip", "bk_cloud_id"],
                    "agg_condition": [],
                    "unit": "",
                    "unit_conversion": 1.0,
                    "metric_field": "loss_percent",
                    "extend_fields": {},
                    "create_user": item.create_user,
                    "update_user": item.update_user,
                }
            )
            DetectAlgorithm.objects.filter(strategy_id=item.strategy_id, item_id=item.id).update(
                is_deleted=True, is_enabled=False
            )
            DetectAlgorithm.objects.create(
                **{
                    "strategy_id": item.strategy_id,
                    "item_id": item.id,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "recovery_config": {"check_window": 5},
                    "algorithm_type": "PingUnreachable",
                    "algorithm_config": [],
                    "level": 1,
                    "create_user": item.create_user,
                    "update_user": item.update_user,
                }
            )
            item.data_source_label = "bk_monitor"
            item.data_type_label = "time_series"
            item.rt_query_config_id = rt_config.id
            item.save()
        except:  # noqa
            pass


class Migration(migrations.Migration):
    dependencies = [
        ("bkmonitor", "0014_auto_20200616_1143"),
    ]

    operations = [
        migrations.RunPython(change_gse_ping_metric),
    ]
