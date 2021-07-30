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
"""
conf.worker.development.default_settings
========================================
"""


from conf.worker.default_settings import *  # noqa

# REDIS
REDIS_HOST = ["127.0.0.1"]
REDIS_PORT = 6379
REDIS_PASSWD = ""
REDIS_MAXMEMORY = "1g"
REDIS_MAXLOG = 500
REDIS_CACHE_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 0,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
REDIS_DIMENSION_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 1,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
# monitor cache config
REDIS_MONITOR_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 5,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
REDIS_LOG_CONF = {
    "host": "localhost",
    "port": REDIS_LOG_PORT,  # noqa
    "db": 2,
    "password": REDIS_PASSWD,
    "socket_timeout": 10,
}
REDIS_CALLBACK_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 3,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
REDIS_LOCALCACHE_CONF = {
    "host": "localhost",
    "port": REDIS_PORT,
    "db": 4,
    "password": REDIS_PASSWD,
}
REDIS_CELERY_CONF = {
    "host": "localhost",
    "port": REDIS_PORT,
    "db": 6,
    "password": REDIS_PASSWD,
}
REDIS_TEST_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 15,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
REDIS_DATA_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 11,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
REDIS_ALARM_CONF = [
    {
        "host": redis_host,
        "port": REDIS_PORT,
        "db": 12,
        "password": REDIS_PASSWD,
    }
    for redis_host in REDIS_HOST
]
