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

from bkmonitor.data_source import load_data_source
from bkmonitor.models import Event, QueryConfigModel

from django.conf import settings

__all__ = ["get_event_relation_info"]

from constants.data_source import DataSourceLabel, DataTypeLabel


def get_event_relation_info(event: Event):
    """
    获取事件最近的日志
    1. 自定义事件：查询事件关联的最近一条事件信息
    2. 日志关键字：查询符合条件的一条日志信息
    """
    item = (
        QueryConfigModel.objects.filter(strategy_id=event.strategy_id)
        .values("data_source_label", "data_type_label")
        .first()
    )
    if not item:
        return ""

    if (item["data_source_label"], item["data_type_label"]) in (
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.LOG),
        (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.LOG),
        (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.TIME_SERIES),
        (DataSourceLabel.CUSTOM, DataTypeLabel.EVENT),
    ):
        rt_query_config = event.origin_config["item_list"][0]["rt_query_config"]
        data_source = load_data_source(item["data_source_label"], item["data_type_label"]).init_by_rt_query_config(
            rt_query_config, bk_biz_id=event.bk_biz_id
        )

        data_source.filter_dict.update(
            {
                key: value
                for key, value in event.origin_alarm["data"]["dimensions"].items()
                if key in rt_query_config.get("agg_dimension", [])
            }
        )

        # 查询时间为事件开始到5个周期后
        interval = rt_query_config.get("agg_interval", 60)
        start_time = int(event.latest_anomaly_record.source_time.timestamp()) - 5 * interval
        end_time = int(event.latest_anomaly_record.source_time.timestamp()) + interval

        records, _ = data_source.query_log(start_time=start_time * 1000, end_time=end_time * 1000, limit=1)
        if not records:
            return ""

        record = records[0]
        if item["data_source_label"] in [DataSourceLabel.BK_MONITOR_COLLECTOR, DataSourceLabel.CUSTOM]:
            content = record["event"]["content"]
        else:
            content = json.dumps(record, ensure_ascii=False)
        return content[: settings.EVENT_RELATED_INFO_LENGTH] if settings.EVENT_RELATED_INFO_LENGTH else content

    return ""
