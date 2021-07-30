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


from django.core.cache import caches

from bkmonitor.utils.common_utils import fetch_biz_id_from_dict
from core.drf_resource import api
from monitor_web.core.metric import BaseMetricFactory
from monitor_web.core.metric.base import BaseMetric


class PluginMetric(BaseMetric):
    def get_category(self):
        return "plugin"


cache = caches["locmem"]


def _meta_api__with_cache(step="_", *args):
    cache_key = step.join(args) if args else step
    result_table_list = cache.get(cache_key)
    if result_table_list is None:
        result_table_list = api.metadata.list_result_table({"datasource_type": step.join(args)})
        cache.set(cache_key, result_table_list, 5)

    return result_table_list


class PluginMetricFactory(BaseMetricFactory):
    @classmethod
    def load(cls, parsed_metric_id, *args, **kwargs):
        if args:
            cc_biz_id = args[0]
        else:
            cc_biz_id = fetch_biz_id_from_dict(kwargs)
        if cc_biz_id is None:
            from bkmonitor.utils.request import get_request

            cc_biz_id = getattr(get_request(), "biz_id", None)
            if cc_biz_id is None:
                return None

        db_name, table_name, item = parsed_metric_id
        rt_id = "{}_{}".format(db_name, table_name)
        result_table_list = _meta_api__with_cache("_", cc_biz_id, db_name)
        if result_table_list:
            db_name = "{}_{}".format(cc_biz_id, db_name)
        else:
            result_table_list = _meta_api__with_cache(".", db_name)

        rt_info = [x for x in result_table_list if x["table_id"] == "{}.{}".format(db_name, table_name)]
        if not rt_info:
            return None
        rt_info = rt_info[0]

        dimension_field = list()
        item_display = None
        item_unit = ""
        for field in rt_info["field_list"]:
            field_name = field["field_name"]
            if field_name == item:
                item_display = field.get("description") or field_name
                item_unit = field.get("unit", "")
            if field["tag"] == "dimension":
                dimension_field.append(field_name)
        if item_display is None:
            return None
        description = item_display
        dimension_field = ",".join(dimension_field)
        category_display = rt_info["table_name_zh"]
        metric_id = ".".join(parsed_metric_id)

        metric_dict = {
            "result_table_id": rt_id,
            "item": item,
            "item_display": item_display,
            "description": description,
            "conversion_unit": item_unit,
            "dimension_field": dimension_field,
            "category_display": category_display,
            "metric_id": metric_id,
            "table_name": table_name,
            "collect_interval": 1,
        }
        return PluginMetric(metric_dict)
