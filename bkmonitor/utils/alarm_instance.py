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
import re

RT_REGEX = re.compile(r"(?P<biz_id>\d+)_(?P<category>[a-zA-Z0-9\-]+)(?:_(?P<name>[a-zA-Z0-9\-]+))?")


def parse_result_table(rt):
    match = RT_REGEX.match(rt)
    info = {"biz_id": None, "category": None, "name": None}
    if match:
        match_info = match.groupdict()
        info["biz_id"] = match_info.get("biz_id")
        info["name"] = match_info.get("name")
        category = match_info.get("category")
        if category == "exporter":
            info["category"] = "component"
        elif category in ["apache", "mysql", "tomcat", "redis", "nginx"]:  # 5个默认采集器
            info["name"] = category
            info["category"] = "component"
        else:
            info["category"] = category
    return info


def get_alarm_type_info(alarm_instance):
    type_info = dict.fromkeys(
        [
            "category",  # 监控场景
            "type",  # 监控场景类型（主机：performance/组件：component/拨测：uptimecheck/自定义：custom）
        ]
    )
    origin_alarm = json.loads(alarm_instance["origin_alarm"])
    category = origin_alarm.get("_match_info").get("category")
    type_info["category"] = category
    if category in ["performance", "base_alarm"]:
        type_info["type"] = "performance"
    elif category in ["custom", "dashboard-custom"]:
        type_info["type"] = "custom"
        monitor_source_info = origin_alarm.get("monitor_source_info")
        if monitor_source_info:
            monitor_result_table_id = monitor_source_info["monitor_result_table_id"]  # try to parse rt id
            rt_info = parse_result_table(monitor_result_table_id)
            if rt_info["category"] == "component":
                type_info["type"] = "component"

    return type_info  # 主机监控
