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
==============================
"""

import os

from conf.api.production.default_settings import *  # noqa

APP_CODE = os.environ.get("BK_MONITOR_APP_CODE", "bk_bkmonitorv3")
SECRET_KEY = APP_SECRET_KEY = os.environ["BK_MONITOR_APP_SECRET"]

# esb组件地址
BK_PAAS_INNER_HOST = ESB_COMPONENT_URL = os.environ["BK_PAAS_PRIVATE_URL"]
COMMON_USERNAME = os.environ.get("BK_ESB_SUPER_USER", "admin")

BACKEND_MYSQL_NAME = "bkmonitorv3_alert"
BACKEND_MYSQL_HOST = os.environ.get("BK_MONITOR_MYSQL_HOST", None) or os.environ.get("BK_PAAS_MYSQL_HOST", None)
BACKEND_MYSQL_PORT = int(os.environ.get("BK_MONITOR_MYSQL_PORT", None) or os.environ.get("BK_PAAS_MYSQL_PORT", None))
BACKEND_MYSQL_USER = os.environ.get("BK_MONITOR_MYSQL_USER", None) or os.environ.get("BK_PAAS_MYSQL_USER", None)
BACKEND_MYSQL_PASSWORD = os.environ.get("BK_MONITOR_MYSQL_PASSWORD", None) or os.environ.get(
    "BK_PAAS_MYSQL_PASSWORD", None
)

SAAS_MYSQL_NAME = "bk_monitorv3"
SAAS_MYSQL_HOST = os.environ.get("BK_PAAS_MYSQL_HOST", None) or os.environ.get("BK_PAAS_MYSQL_HOST", None)
SAAS_MYSQL_PORT = int(os.environ.get("BK_PAAS_MYSQL_PORT", None) or os.environ.get("BK_PAAS_MYSQL_PORT", None))
SAAS_MYSQL_USER = os.environ.get("BK_PAAS_MYSQL_USER", None) or os.environ.get("BK_PAAS_MYSQL_USER", None)
SAAS_MYSQL_PASSWORD = os.environ.get("BK_PAAS_MYSQL_PASSWORD", None) or os.environ.get("BK_PAAS_MYSQL_PASSWORD", None)

DATABASES = {
    # SaaS DB 写死SaaS app code
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": SAAS_MYSQL_NAME,
        "USER": SAAS_MYSQL_USER,
        "PASSWORD": SAAS_MYSQL_PASSWORD,
        "HOST": SAAS_MYSQL_HOST,
        "PORT": SAAS_MYSQL_PORT,
    },
    BACKEND_DATABASE_NAME: {
        "ENGINE": "django.db.backends.mysql",
        "NAME": BACKEND_MYSQL_NAME,
        "USER": BACKEND_MYSQL_USER,
        "PASSWORD": BACKEND_MYSQL_PASSWORD,
        "HOST": BACKEND_MYSQL_HOST,
        "PORT": BACKEND_MYSQL_PORT,
    },
}

# 节点管理数据库，仅当监控SaaS与节点管理公用DB实例时适用
DATABASES["nodeman"] = {}
DATABASES["nodeman"].update(DATABASES["default"])
DATABASES["nodeman"]["NAME"] = os.environ.get("BKAPP_NODEMAN_DB_NAME", "bk_nodeman")

BK_HOME = os.environ["BK_HOME"]

LOG_PATH = f"{BK_HOME}/logs/bkmonitorv3"  # 日志目录

LOG_LOGFILE_MAXSIZE = 1024 * 1024 * 200  # 200m
LOG_LOGFILE_BACKUP_COUNT = 4
LOG_PROCESS_CHECK_TIME = 60 * 60 * 4

LOG_FILE_PATH = os.path.join(LOG_PATH, "kernel_api.log")
LOGGING = LOGGER_CONF = get_logging(LOG_FILE_PATH)  # noqa

# KAFKA
KAFKA_HOST = [os.environ.get("BK_MONITOR_KAFKA_HOST", "kafka.service.consul")]
KAFKA_PORT = int(os.environ.get("BK_MONITOR_KAFKA_PORT", 9092))

# INFLUXDB
INFLUXDB_HOST = os.environ.get("BK_INFLUXDB_PROXY_HOST", "influxdb-proxy.bkmonitorv3.service.consul")
INFLUXDB_PORT = int(os.environ.get("BK_INFLUXDB_PROXY_PORT", 10203))

# zookeeper
ZK_HOST = os.environ.get("BK_GSE_ZK_HOST", "zk.service.consul")
ZK_PORT = int(os.environ.get("BK_GSE_ZK_PORT", 2181))

# METADATA环境依赖配置
METADATA_DEFAULT_DATABASE_NAME = BACKEND_DATABASE_NAME  # noqa

CONSUL_CLIENT_CERT_FILE = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CLIENT_CERT_FILE', '')}"
CONSUL_CLIENT_KEY_FILE = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CLIENT_KEY_FILE', '')}"
CONSUL_SERVER_CA_CERT = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CA_FILE', '')}"
CONSUL_HTTPS_PORT = os.environ.get("BK_CONSUL_HTTPS_PORT", "")

BK_MONITOR_PROXY_LISTEN_PORT = 10205  # bk_monitor_proxy 自定义上报服务监听的端口

CELERY_CONF_TYPE = "rabbitmq_conf"

# RedisCache: 单实例
# SentinelRedisCache: 哨兵模式

BK_MONITOR_REDIS_MODE = os.environ.get("BK_MONITOR_REDIS_MODE", "sentinel")

CACHE_BACKEND_TYPE = {"sentinel": "SentinelRedisCache", "standalone": "RedisCache"}.get(
    BK_MONITOR_REDIS_MODE, "SentinelRedisCache"
)


if CACHE_BACKEND_TYPE == "SentinelRedisCache":
    # redis 集群sentinel模式
    REDIS_HOST = os.environ.get("BK_MONITOR_REDIS_SENTINEL_HOST", "redis_cluster.service.consul")
    REDIS_PORT = int(os.environ.get("BK_MONITOR_REDIS_SENTINEL_PORT", 16379))
if CACHE_BACKEND_TYPE == "RedisCache":
    # redis 集群sentinel模式
    REDIS_HOST = os.environ.get("BK_MONITOR_REDIS_HOST", "redis.service.consul")
    REDIS_PORT = int(os.environ.get("BK_MONITOR_REDIS_PORT", 6379))

REDIS_MASTER_NAME = os.environ.get("BK_MONITOR_REDIS_SENTINEL_MASTER_NAME", "mymaster")
REDIS_SENTINEL_PASS = os.environ.get("BK_MONITOR_REDIS_SENTINEL_PASSWORD", "")
REDIS_PASSWD = os.environ.get("BK_MONITOR_REDIS_PASSWORD", "")

# redis中的db分配[7，8，9，10]，共4个db
# 7.[不重要，可清理] 日志相关数据使用log配置
# 8.[一般，可清理]   配置相关缓存使用cache配置，例如：cmdb的数据、策略、屏蔽等配置数据
# 9.[重要，不可清理] 各个services之间交互的队列，使用queue配置
# 9.[重要，不可清理] celery的broker，使用celery配置
# 10.[重要，不可清理] service自身的数据，使用service配置
REDIS_LOG_CONF = {"host": REDIS_HOST, "port": REDIS_PORT, "db": 7, "password": REDIS_PASSWD}
REDIS_CACHE_CONF = {"host": REDIS_HOST, "port": REDIS_PORT, "db": 8, "password": REDIS_PASSWD}
REDIS_CELERY_CONF = REDIS_QUEUE_CONF = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 9,
    "password": REDIS_PASSWD,
}

REDIS_SERVICE_CONF = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 10,
    "password": REDIS_PASSWD,
    "socket_timeout": 10,
}

RABBITMQ_HOST = os.environ.get("BK_MONITOR_RABBITMQ_HOST", "rabbitmq.service.consul")
RABBITMQ_PORT = int(os.environ.get("BK_MONITOR_RABBITMQ_PORT", 5672))
RABBITMQ_VHOST = os.environ.get("BK_MONITOR_RABBITMQ_VHOST", APP_CODE)
RABBITMQ_USER = os.environ.get("BK_MONITOR_RABBITMQ_USERNAME", APP_CODE)
RABBITMQ_PASS = os.environ.get("BK_MONITOR_RABBITMQ_PASSWORD", "")
