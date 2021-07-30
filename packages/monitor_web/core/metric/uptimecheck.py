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


import copy

import six
from django.utils.translation import ugettext as _

from bkmonitor.utils.common_utils import fetch_biz_id_from_dict
from monitor_web.constants import UPTIME_CHECK_DB
from monitor_web.core.metric import BaseMetricFactory
from monitor_web.core.metric.base import BaseMetric
from monitor_web.uptime_check.constants import UPTIME_CHECK_METRICS, UPTIME_CHECK_RT


class UptimeCheckMetric(BaseMetric):
    def get_category(self):
        return UPTIME_CHECK_DB


class UptimeCheckFactory(BaseMetricFactory):
    DB_NAME = UPTIME_CHECK_DB

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

        if db_name != UPTIME_CHECK_DB:
            return None

        rt_info = UPTIME_CHECK_RT[table_name]

        metric_result_table_id = "{}_{}".format(db_name, table_name)
        dimension_field = list()
        item_display = None
        for field in rt_info["fields"]:
            field_name = field["field"]
            if field_name == item:
                item_display = six.text_type(field["description"]) or field_name
            if field["is_dimension"]:
                dimension_field.append(field_name)
        if item_display is None:
            return None
        description = item_display
        conversion_unit = ""
        dimension_field = dimension_field[0] if len(dimension_field) == 1 else ""
        category_display = six.text_type(rt_info["description"])
        metric_id = ".".join(parsed_metric_id)

        collect_interval = 1

        metric_dict = {
            "result_table_id": metric_result_table_id,
            "item": item,
            "item_display": item_display,
            "description": description,
            "conversion_unit": conversion_unit,
            "dimension_field": dimension_field,
            "category_display": category_display,
            "metric_id": metric_id,
            "table_name": table_name,
            "collect_interval": collect_interval,
        }
        return UptimeCheckMetric(metric_dict)

    @classmethod
    def make_metric_conf_list(cls, *args, **kwargs):
        if args:
            cc_biz_id = args[0]
        else:
            cc_biz_id = fetch_biz_id_from_dict(kwargs)
        if cc_biz_id is None:
            from bkmonitor.utils.request import get_request

            cc_biz_id = getattr(get_request(), "biz_id", None)
            if cc_biz_id is None:
                raise TypeError("miss arg: biz_id")

        uptime_tables = copy.deepcopy(UPTIME_CHECK_METRICS)
        for table in uptime_tables:
            for item in table["items"]:
                item["collect_interval"] = 1
                item["display"] = six.text_type(item["display"])
                item["description"] = six.text_type(item["description"])

        metric_conf = {
            "category": UPTIME_CHECK_DB,
            "category_display": _("服务拨测"),
            "items": uptime_tables,
        }

        return [metric_conf]
