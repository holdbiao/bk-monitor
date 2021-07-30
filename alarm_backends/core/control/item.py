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


import logging
from typing import List


from alarm_backends.core.control.mixins.detect import DetectMixin
from alarm_backends.core.control.mixins.nodata import CheckMixin
from bkmonitor.data_source import load_data_source

logger = logging.getLogger("core.control")


class Item(DetectMixin, CheckMixin):
    def __init__(self, item_config, strategy=None):
        self.id = item_config.get("id")
        self.name = item_config.get("name")
        self.metric_id = item_config.get("metric_id")

        self.data_source_label = item_config.get("data_source_label")
        self.data_type_label = item_config.get("data_type_label")

        self.algorithm_list = item_config.get("algorithm_list", [])

        self.no_data_config = item_config.get("no_data_config", {})

        self.rt_query_config = item_config.get("rt_query_config", {})
        self.unit = self.rt_query_config.get("unit", "")
        self.item_config = item_config
        self.strategy = strategy
        self.target = item_config.get("target", [[]])
        self.rt_query_config["target"] = self.target
        self.data_source = load_data_source(self.data_source_label, self.data_type_label).init_by_rt_query_config(
            rt_query_config=self.rt_query_config,
            name=self.name,
            bk_biz_id=self.strategy.bk_biz_id,
        )

    def query_record(self, start_time: int, end_time: int) -> List:
        records = self.data_source.query_data(start_time * 1000, end_time * 1000)
        for record in records:
            record["_time_"] //= 1000
        return records
