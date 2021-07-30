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
import datetime
import json
import logging
import os

import arrow
import pytz
from django.conf import settings
from django.template.loader import get_template
from django.utils.translation import ugettext as _

from alarm_backends.constants import CONST_ONE_DAY
from alarm_backends.core.i18n import i18n
from alarm_backends.service.scheduler.tasks.image_exporter import render_html_string_to_graph
from bkmonitor.data_source import load_data_source
from bkmonitor.utils import time_tools
from constants.strategy import AGG_METHOD_REAL_TIME
from core.unit import load_unit

logger = logging.getLogger("action")


def get_chart_data(bk_biz_id, item, dimensions, source_time, title=""):
    """
    获取图表数据
    :param bk_biz_id: 业务
    :param item: 监控项配置
    :type item: Item
    :param source_time: 告警事件
    :type source_time: Arrow
    :param dimensions: 维度
    :return:
    """
    data_source = load_data_source(item.data_source_label, item.data_type_label).init_by_rt_query_config(
        rt_query_config=item.rt_query_config, bk_biz_id=bk_biz_id
    )

    agg_condition = {}
    for key in dimensions:
        if key not in item.rt_query_config["agg_dimension"]:
            continue
        agg_condition[key] = dimensions[key]
    data_source.filter_dict.update(agg_condition)

    chart_option = {_("今日"): 0, _("昨日"): -1, _("上周"): -7}
    start_time = source_time.replace(hours=-1)
    end_time = source_time.replace(minutes=10)
    metric_field = data_source.metrics[0]["field"]
    unit = load_unit(item.rt_query_config.get("unit", ""))

    series = []
    for name, offset in list(chart_option.items()):
        data = []
        records = data_source.query_data(
            start_time=start_time.replace(days=offset).timestamp * 1000,
            end_time=end_time.replace(days=offset).timestamp * 1000,
        )

        for record in records:
            value = record[metric_field]
            if value:
                value = round(value, 2)
            data.append([record["_time_"] - offset * CONST_ONE_DAY * 1000, value])
        series.append({"name": name, "data": data})

    timezone = i18n.get_timezone()
    timezone_offset = -int(datetime.datetime.now(pytz.timezone(timezone)).utcoffset().total_seconds()) // 60

    return {
        "unit": unit.suffix,
        "chart_type": "spline",
        "title": title or item.name,
        "subtitle": item.rt_query_config.get("metric_field", ""),
        "source_timestamp": source_time.timestamp * 1000,
        "locale": i18n.get_locale().replace("_", "-"),
        "timezone": timezone,
        "series": series,
        "timezoneOffset": timezone_offset,
    }


def get_chart_image(chart_data):
    image_exporter_task = None
    try:
        template_path = os.path.join(settings.BASE_DIR, "alarm_backends", "templates", "image_exporter")
        template = get_template("image_exporter/graph.html")
        html_string = template.render({"context": json.dumps(chart_data)})
        image_exporter_task = render_html_string_to_graph.delay(html_string, template_path)
        return image_exporter_task.get(timeout=settings.IMAGE_EXPORTER_TIMEOUT)
    except Exception as e:
        logger.error("get_chart_image fail", e)
    finally:
        if image_exporter_task is not None:
            image_exporter_task.forget()


def get_chart_by_origin_alarm(bk_biz_id, item, dimensions, source_time, title=""):
    # 非时序型或实时监控不出图
    if item.data_type_label != "time_series" or item.rt_query_config["agg_method"] == AGG_METHOD_REAL_TIME:
        return None

    agg_condition = item.rt_query_config.get("agg_condition", [])
    for key in dimensions:
        if key not in item.rt_query_config["agg_dimension"]:
            continue
        agg_condition.append({"key": key, "method": "eq", "value": dimensions[key]})
    item.rt_query_config["agg_condition"] = agg_condition

    source_time = arrow.get(time_tools.localtime(source_time))
    chart_data = get_chart_data(bk_biz_id, item, dimensions, source_time, title)
    return get_chart_image(chart_data)
