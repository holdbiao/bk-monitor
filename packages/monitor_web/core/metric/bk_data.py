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


from constants.data_source import DataSourceLabel
from core.drf_resource import api
from monitor_web.core.metric import BaseMetricFactory
from monitor_web.core.metric.base import BaseMetric


class BkDataMetric(BaseMetric):
    def get_category(self):
        return DataSourceLabel.BK_DATA


class BkDataMetricFactory(BaseMetricFactory):
    @classmethod
    def load(cls, parsed_metric_id, *args, **kwargs):
        # format: bk_data.2_test_table.field
        system, result_table_id, item = parsed_metric_id

        if system != DataSourceLabel.BK_DATA:
            return None

        rt_info = api.bkdata.get_result_table(result_table_id=result_table_id)
        if not rt_info:
            return None

        dimension_field = list()
        item_display = None
        item_unit = ""
        description = ""
        for field in rt_info["fields"]:
            field_name = field["field_name"]
            if field_name == item:
                item_display = field.get("field_alias") or field_name
                item_unit = field.get("unit", "")
                description = field.get("description") or item_display
            if field["is_dimension"]:
                dimension_field.append(field_name)
        if item_display is None:
            return None
        dimension_field = ",".join(dimension_field)
        category_display = rt_info["result_table_name"]
        metric_id = ".".join(parsed_metric_id)

        metric_dict = {
            "result_table_id": result_table_id,
            "item": item,
            "item_display": item_display,
            "description": description,
            "conversion_unit": item_unit,
            "dimension_field": dimension_field,
            "category_display": category_display,
            "metric_id": metric_id,
            "table_name": result_table_id,
            "collect_interval": 1,
        }
        return BkDataMetric(metric_dict)
