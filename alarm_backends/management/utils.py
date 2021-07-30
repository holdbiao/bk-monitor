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


import socket

import netifaces
from django.conf import settings


def get_host_addr(inet_dev=settings.BKMONITOR_WORKER_INET_DEV, safe=True):
    try:
        if not inet_dev:
            gateways = netifaces.gateways()
            gateway = gateways["default"]
            inet_dev = gateway[netifaces.AF_INET][1]

        return netifaces.ifaddresses(inet_dev)[netifaces.AF_INET][0]["addr"]
    except Exception as err:
        if not safe:
            raise err
        return socket.gethostbyname(socket.gethostname())
