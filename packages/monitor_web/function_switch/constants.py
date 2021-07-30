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
from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _

# 当前支持的插件功能列表
from rest_framework import serializers

PLUGIN_FUNCTIONS = {
    "basereport": {
        "display_name": _("主机监控-操作系统"),
        "plugin_id": "basereport",
        "params": OrderedDict([("net_interface_black_list", serializers.ListField(label=_("网卡黑名单"), default=True))]),
    },
    # "exceptionbeat": {
    #     "display_name": _("主机监控-系统事件"),
    #     "plugin_id": "exceptionbeat",
    # },
    "processbeat": {
        "display_name": _("进程监控"),
        "plugin_id": "processbeat",
    },
    "bkmonitorbeat": {
        "display_name": _("插件采集"),
        "plugin_id": "bkmonitorbeat",
    },
}
