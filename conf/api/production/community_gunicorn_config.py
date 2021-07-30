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

import os

bind = f"{os.environ['LAN_IP']}:{os.environ.get('BK_MONITOR_KERNELAPI_PORT', '10204')}"
workers = 8
# worker_class = 'gevent'
raw_env = [
    "DJANGO_SETTINGS_MODULE=settings",
    f"BK_PAAS_HOST={os.environ['BK_PAAS_PRIVATE_URL']}",
    "DJANGO_CONF_MODULE=conf.api.production.community",
    "BKAPP_DEPLOY_PLATFORM=community",
    "BKAPP_DEPLOY_ENV=api",
]
