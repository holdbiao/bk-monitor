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

from django.db import migrations, models

from monitor.models import HostProperty, HostPropertyConf

host_property_data = [
    {
        "property": "InnerIP",
        "property_display": "主机名/IP",
        "required": True,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "status",
        "property_display": "采集状态",
        "required": True,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "alarm",
        "property_display": "告警事件（今日）",
        "required": False,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "cpu_usage",
        "property_display": "CPU使用率",
        "required": False,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "io_util",
        "property_display": "磁盘IO使用率",
        "required": False,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "cpu_load",
        "property_display": "CPU5分钟负载",
        "required": False,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "component",
        "property_display": "组件服务",
        "required": True,
        "selected": True,
        "is_deleted": False,
    },
    {
        "property": "SetName",
        "property_display": "集群名",
        "required": False,
        "selected": False,
        "is_deleted": False,
    },
    {
        "property": "ModuleName",
        "property_display": "模块名",
        "required": False,
        "selected": False,
        "is_deleted": False,
    },
]


def run_repair(*args):
    # update property_display for meta data
    HostProperty.objects.filter(property="status").update(property_display="采集状态")
    # update user config for property_display
    items = HostPropertyConf.objects.filter(is_deleted=False)
    for item in items:
        property_list = HostPropertyConf.objects.parse_conf(item.property_list)
        for p in property_list:
            if p["id"] == "status":
                p["name"] = "采集状态"
        item.property_list = json.dumps(property_list)
        models.Model.save(item)


class Migration(migrations.Migration):

    dependencies = [
        ("monitor", "0018_auto_20170630_1801"),
    ]

    operations = [migrations.RunPython(run_repair)]
