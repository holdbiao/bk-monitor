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

from conf.worker.production.default_settings import *  # noqa

ALLOWED_HOSTS = ["*"]

BK_HOME = os.environ["BK_HOME"]

# 环境变量
ROOT_PATH = f"{BK_HOME}/bkmonitorv3/monitor"  # 项目目录
LOG_PATH = f"{BK_HOME}/logs/bkmonitorv3"  # 日志目录
BAK_PATH = f"{BK_HOME}/logs/bkmonitorv3"  # 运行时数据及缓存落地目录
PYTHON_HOME = f"{BK_HOME}/.envs/bkmonitorv3-monitor/bin"  # virtualenv path
PYTHON = PYTHON_HOME + "/python"  # python bin
GUNICORN = PYTHON_HOME + "/gunicorn"  # gunicorn bin

LOG_LOGFILE_MAXSIZE = 1024 * 1024 * 200  # 200m
LOG_LOGFILE_BACKUP_COUNT = 12
LOG_PROCESS_CHECK_TIME = 60 * 60 * 4

# LOGGING
LOGGER_LEVEL = "INFO"
LOGGER_DEFAULT = {
    "level": LOGGER_LEVEL,
    "handlers": ["console", "file", "sentry"],
}

# add kafka client connect log
LOGGER_KAFKA_CLIENT = {
    "level": "WARNING",
    "handlers": ["console", "file", "redis"],
}

LOG_FILE_PATH = os.path.join(LOG_PATH, "kernel.log")
LOG_IMAGE_EXPORTER_FILE_PATH = os.path.join(LOG_PATH, "kernel_image_exporter.log")
LOG_METADATA_FILE_PATH = os.path.join(LOG_PATH, "kernel_metadata.log")

LOGGING = LOGGER_CONF = {
    "version": 1,
    "loggers": {
        "root": LOGGER_DEFAULT,
        "core": LOGGER_DEFAULT,
        "cron": LOGGER_DEFAULT,
        "cache": LOGGER_DEFAULT,
        "service": LOGGER_DEFAULT,
        "detect": LOGGER_DEFAULT,
        "nodata": LOGGER_DEFAULT,
        "access": LOGGER_DEFAULT,
        "trigger": LOGGER_DEFAULT,
        "event": LOGGER_DEFAULT,
        "recovery": LOGGER_DEFAULT,
        "action": LOGGER_DEFAULT,
        "bkmonitor": LOGGER_DEFAULT,
        "data_source": LOGGER_DEFAULT,
        "alarm_backends": LOGGER_DEFAULT,
        "self_monitor": LOGGER_DEFAULT,
        "celery": LOGGER_DEFAULT,
        "metadata": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["metadata"]},
        "image_exporter": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["image_exporter"]},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "DEBUG", "formatter": "standard"},
        "file": {
            "class": "logging.handlers.WatchedFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": LOG_FILE_PATH,
            "encoding": "utf-8",
        },
        "redis": {"class": "bkmonitor.utils.log.handlers.RedisHandler", "level": "DEBUG"},
        "sentry": {"class": "bkmonitor.utils.log.handlers.SentryHandler", "level": "WARNING"},
        "image_exporter": {
            "class": "logging.handlers.WatchedFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": LOG_IMAGE_EXPORTER_FILE_PATH,
            "encoding": "utf-8",
        },
        "metadata": {
            "class": "logging.handlers.WatchedFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": LOG_METADATA_FILE_PATH,
            "encoding": "utf-8",
        },
    },
    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s %(levelname)-8s %(process)-8d" "%(name)-15s %(filename)20s[%(lineno)03d] %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
}

########################## 通用配置 settings ############################## noqa
# 通知人 测试环境告警仅发送给VERIFIER列表中的用户 如果为空则不发送告警
# VERIFIER = [""]

# 本机内网IP地址
LAN_IP = INTRANET_IP_ADDR = os.environ["LAN_IP"]

# 运行环境: product or test or local
ENV = "product"

# 运营平台
PLATFORM = "community"

# SIGNATURE FOR MESSAGE
SIGNATURE = ""

# SUPERVISOR_AUTO_START
START_KERNEL = False
START_COMMON = False

# SUPERVISOR Servers
JOBSERVER_URL = f"http://{LAN_IP}"
JOBSERVER_MAX = 40
JOBSERVER_TIMEOUT = 60

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

# KAFKA
KAFKA_HOST = [os.environ.get("BK_MONITOR_KAFKA_HOST", "kafka.service.consul")]
KAFKA_CONSUMER_GROUP = "{}-bkmonitorv3-alert-{}".format(PLATFORM.lower(), ENV.lower())
COMMON_KAFKA_CLUSTER_INDEX = 0
KAFKA_PORT = int(os.environ.get("BK_MONITOR_KAFKA_PORT", 9092))

# TRANSFER
TRANSFER_HOST = os.environ.get("BK_TRANSFER_HOST", "transfer.bkmonitorv3.service.consul")
TRANSFER_PORT = os.environ.get("BK_TRANSFER_HTTP_PORT", 10202)

# INFLUXDB
INFLUXDB_HOST = os.environ.get("BK_INFLUXDB_PROXY_HOST", "influxdb-proxy.bkmonitorv3.service.consul")
INFLUXDB_PORT = int(os.environ.get("BK_INFLUXDB_PROXY_PORT", 10202))

# zookeeper
ZK_HOST = os.environ.get("BK_GSE_ZK_HOST", "zk.service.consul")
ZK_PORT = int(os.environ.get("BK_GSE_ZK_PORT", 2181))

# ES7 config
ES7_HOST = os.environ.get("BK_MONITOR_ES7_HOST", "es7.service.consul")
ES7_REST_PORT = os.environ.get("BK_MONITOR_ES7_REST_PORT", "9200")
ES7_TRANSPORT_PORT = os.environ.get("BK_MONITOR_ES7_TRANSPORT_PORT", "9301")
ES7_USER = os.environ.get("BK_MONITOR_ES7_USER", "")
ES7_PASSWORD = os.environ.get("BK_MONITOR_ES7_PASSWORD", "")

########################## esb url ############################### noqa

# 蓝鲸根域名(不含主机名)
BK_DOMAIN = os.environ["BK_DOMAIN"]

# paas url
PAAS_URL = os.environ["BK_PAAS_PUBLIC_URL"]

# cmdb url
CMDB_URL = os.environ["BK_CMDB_PUBLIC_URL"]

# job url
JOB_URL = os.environ["BK_JOB_PUBLIC_URL"]

# esb组件地址
BK_PAAS_INNER_HOST = ESB_COMPONENT_URL = os.environ["BK_PAAS_PRIVATE_URL"]
COMMON_USERNAME = os.environ["BK_ESB_SUPER_USER"]

# 配置库
BACKEND_MYSQL_NAME = "bkmonitorv3_alert"
BACKEND_MYSQL_HOST = os.environ.get("BK_MONITOR_MYSQL_HOST", None) or os.environ.get("BK_PAAS_MYSQL_HOST", None)
BACKEND_MYSQL_PORT = int(os.environ.get("BK_MONITOR_MYSQL_PORT", None) or os.environ.get("BK_PAAS_MYSQL_PORT", None))
BACKEND_MYSQL_USER = os.environ.get("BK_MONITOR_MYSQL_USER", None) or os.environ.get("BK_PAAS_MYSQL_USER", None)
BACKEND_MYSQL_PASSWORD = os.environ.get("BK_MONITOR_MYSQL_PASSWORD", None) or os.environ.get(
    "BK_PAAS_MYSQL_PASSWORD", None
)

SAAS_MYSQL_NAME = "bk_monitorv3"
SAAS_MYSQL_HOST = os.environ["BK_PAAS_MYSQL_HOST"]
SAAS_MYSQL_PORT = os.environ.get("BK_PAAS_MYSQL_PORT", 3306)
SAAS_MYSQL_USER = os.environ["BK_PAAS_MYSQL_USER"]
SAAS_MYSQL_PASSWORD = os.environ.get("BK_PAAS_MYSQL_PASSWORD", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": BACKEND_MYSQL_NAME,
        "USER": BACKEND_MYSQL_USER,
        "PASSWORD": BACKEND_MYSQL_PASSWORD,
        "HOST": BACKEND_MYSQL_HOST,
        "PORT": BACKEND_MYSQL_PORT,
    }
}
DATABASES["monitor_api"] = DATABASES["default"]


#
# Cache
#

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 100000, "CULL_FREQUENCY": 10},
    },
    "db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 100000, "CULL_FREQUENCY": 10},
    },
    "locmem": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
########################## new alarm settings ############################ noqa
APP_CODE = os.environ.get("BK_MONITOR_APP_CODE", "bk_bkmonitorv3")
SECRET_KEY = APP_SECRET_KEY = os.environ["BK_MONITOR_APP_SECRET"]

# POLL_ALARM
POLL_CRON_TAG = "{}_alert_cron_{}".format(PLATFORM.lower(), ENV.lower())
POLL_INTERVAL = 1  # minutes
POLL_LIST = [
    # "simulate",
    "gse_base_alarm",
    "jungle_alert",
    "gse_custom_out_str",
]

# SOLUTION
WCB_DUMMY = False
SOLUTION_DUMMY = False

########################## new monitor settings ########################## noqa
MONITOR_APP_CODE = os.environ.get("BK_MONITOR_APP_CODE", "bk_bkmonitorv3")
MONITOR_APP_SECRET_KEY = os.environ["BK_MONITOR_APP_SECRET"]

# base monitor config
MONITOR_HANDLE_DURATION = 60
MONITOR_HANDLE_COUNT = 10000
MONITOR_PROC_COUNT = 6
MONITOR_DATA_OVERTIME = 30 * 60

MONITOR_SRC_TYPE = ["BKMONITOR"]
BASE_ALARM_LIST = [2, 3, 6, 7, 8]

PROC_PORT_USE_TSDB = True

# queue config
MONITOR_ALERT_TOPIC = "0bkmonitorv3__backend0"

QUEUE_POP_COUNT = 20000

COLLECT_DEFAULT_COUNT = 10

ACCESS_PUSH_QUEUE_MAX_LENGTH = 100000

DEFAULT_LOCALE = "zh_Hans"

DEFAULT_TIMEZONE = "Asia/Shanghai"

CERT_PATH = os.environ.get("BK_CERT_PATH", "")
LICENSE_HOST = os.environ.get("BK_LICENSE_HOST", "license.service.consul")
LICENSE_PORT = os.environ.get("BK_LICENSE_PORT", "8443")
LICENSE_REQ_INTERVAL = [20, 60, 120]  # 连续请求n次，每次请求间隔(单位：秒)

# SUPERVISOR 配置
SUPERVISOR_PORT = 9001
SUPERVISOR_SERVER = "unix:///var/run/bkmonitorv3/monitor-supervisor.sock"
SUPERVISOR_USERNAME = ""
SUPERVISOR_PASSWORD = ""
SUPERVISOR_SOCK = "unix:///var/run/bkmonitorv3/monitor-supervisor.sock"

RABBITMQ_HOST = os.environ.get("BK_MONITOR_RABBITMQ_HOST", "rabbitmq.service.consul")
RABBITMQ_PORT = int(os.environ.get("BK_MONITOR_RABBITMQ_PORT", 5672))
RABBITMQ_VHOST = os.environ.get("BK_MONITOR_RABBITMQ_VHOST", APP_CODE)
RABBITMQ_USER = os.environ.get("BK_MONITOR_RABBITMQ_USERNAME", APP_CODE)
RABBITMQ_PASS = os.environ.get("BK_MONITOR_RABBITMQ_PASSWORD", "")

EVENT_CENTER_URL = "%s/o/bk_monitorv3/?bizId={bk_biz_id}&routeHash=event-center/?collectId={collect_id}#/" % PAAS_URL
HEALTHZ_DETAIL_URL = "%s/o/bk_monitorv3/{biz_id}/healthz/dashboard/" % PAAS_URL

SELF_MONITORING_NODES = [
    "gse_data",
    "pre_kafka",
    "etl",
    "post_kafka",
    "shipper",
    "tsdb_proxy",
    "influxdb",
    "data_access",
    "detect",
    "poll_alarm",
    "match_alarm",
    "converge_alarm",
    "collect_alarm",
    "kafka",
    "mysql",
    "beanstalk",
    "supervisor",
    "redis",
    "celery",
]

# METADATA环境依赖配置
METADATA_DEFAULT_DATABASE_NAME = "monitor_api"

CONSUL_CLIENT_CERT_FILE = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CLIENT_CERT_FILE', '')}"
CONSUL_CLIENT_KEY_FILE = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CLIENT_KEY_FILE', '')}"
CONSUL_SERVER_CA_CERT = f"{BK_HOME}/cert/{os.environ.get('BK_CONSUL_CA_FILE', '')}"
CONSUL_HTTPS_PORT = os.environ.get("BK_CONSUL_HTTPS_PORT", "")

BK_MONITOR_PROXY_LISTEN_PORT = 10205  # bk_monitor_proxy 自定义上报服务监听的端口

# 异常记录保留天数
ANOMALY_RECORD_SAVE_DAYS = 30

# event 模块最大容忍无数据周期数
EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE = 5

ANOMALY_RECORD_COLLECT_WINDOW = 100
ANOMALY_RECORD_CONVERGED_ACTION_WINDOW = 3
