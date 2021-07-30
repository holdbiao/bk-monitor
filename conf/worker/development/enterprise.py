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


import sys

from conf.worker.production.default_settings import *  # noqa

ALLOWED_HOSTS = ["*"]

# 环境变量
ROOT_PATH = "."  # 项目目录

LOG_PATH = "./logs/bkmonitor"  # 日志目录
BAK_PATH = "./logs/bkmonitor"  # 运行时数据及缓存落地目录

PYTHON_HOME = os.path.dirname(sys.executable)  # noqa virtualenv path

PYTHON = os.path.join(PYTHON_HOME, "python")  # noqa python bin
GUNICORN = os.path.join(PYTHON_HOME, "gunicorn")  # noqa gunicorn bin

LOG_LOGFILE_MAXSIZE = 1024 * 1024 * 200  # 200m
LOG_LOGFILE_BACKUP_COUNT = 12
LOG_PROCESS_CHECK_TIME = 60 * 60 * 4

# LOGGING
LOGGER_LEVEL = "DEBUG"
LOGGER_DEFAULT = {
    "level": LOGGER_LEVEL,
    "handlers": ["console", "file", "sentry"],
}

# add kafka client connect log
LOGGER_KAFKA_CLIENT = {
    "level": "WARNING",
    "handlers": ["console", "file", "redis"],
}

LOG_FILE_PATH = os.path.join(LOG_PATH, "kernel.log")  # noqa
LOG_IMAGE_EXPORTER_FILE_PATH = os.path.join(LOG_PATH, "kernel_image_exporter.log")  # noqa
LOG_METADATA_FILE_PATH = os.path.join(LOG_PATH, "kernel_metadata.log")  # noqa

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
VERIFIER = [""]

# 本机内网IP地址
INTRANET_IP_ADDR = "127.0.0.1"

# 运行环境: PRODUCT or TEST or DEVELOP
ENV = "DEVELOP"

# 运营平台
PLATFORM = "enterprise"

# SIGNATURE FOR MESSAGE
SIGNATURE = ""

# SUPERVISOR_AUTO_START
START_KERNEL = False
START_COMMON = False

# SUPERVISOR Servers
JOBSERVER_URL = "http://127.0.0.1"
JOBSERVER_MAX = 40
JOBSERVER_TIMEOUT = 60

# BEANSTALKD
BEANSTALKD_HOST = ["127.0.0.1"]
BEANSTALKD_PORT = 11300

CACHE_BACKEND_TYPE = "RedisCache"  # noqa

# redis 集群sentinel模式
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_PASSWD = ""
REDIS_MAXMEMORY = "4gb"
REDIS_MAXLOG = 10000

# redis中的db分配[7，8，9，10]，共4个db
# 7.[不重要，可清理] 日志相关数据使用log配置
# 8.[一般，可清理]   配置相关缓存使用cache配置，例如：cmdb的数据、策略、屏蔽等配置数据
# 9.[重要，不可清理] 各个services之间交互的队列，使用queue配置
# 9.[重要，不可清理] celery的broker，使用celery配置
# 10.[重要，不可清理] service自身的数据，使用service配置
REDIS_LOG_CONF = {"host": REDIS_HOST, "port": REDIS_PORT, "db": 7, "password": REDIS_PASSWD}
REDIS_CACHE_CONF = {"host": REDIS_HOST, "port": REDIS_PORT, "db": 8, "password": REDIS_PASSWD}
REDIS_QUEUE_CONF = REDIS_CELERY_CONF = {
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

# ELASTICSEARCH
ES_HOST = [
    # {"host": "es host address", "port": "es bulk port"},
]

# KAFKA
KAFKA_HOST = ["127.0.0.1"]
KAFKA_CONSUMER_GROUP = "{}-monitor-alert-{}".format(PLATFORM.lower(), ENV.lower())
COMMON_KAFKA_CLUSTER_INDEX = 0
KAFKA_PORT = 9092

# TRANSFER
TRANSFER_HOST = ""
TRANSFER_PORT = ""

# INFLUXDB
INFLUXDB_HOST = ""
INFLUXDB_PORT = ""

# zookeeper
ZK_HOST = "127.0.0.1"
ZK_PORT = 2181

########################## esb url ############################### noqa

# 蓝鲸根域名(不含主机名)
BK_DOMAIN = "replace.me"

# paas url
PAAS_URL = "http://paas.replace.me:80"

# cmdb url
CMDB_URL = "http://cmdb.replace.me:80"

# job url
JOB_URL = "http://job.replace.me:80"

# esb组件地址
ESB_COMPONENT_URL = "http://paas.replace.me:80"
COMMON_USERNAME = "admin"

# 配置库
MYSQL_NAME = "bkdata_monitor_alert"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": MYSQL_NAME,
        "USER": MYSQL_USER,
        "PASSWORD": MYSQL_PASSWORD,
        "HOST": MYSQL_HOST,
        "PORT": MYSQL_PORT,
        "TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"},
    },
    "monitor_api": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": MYSQL_NAME,
        "USER": MYSQL_USER,
        "PASSWORD": MYSQL_PASSWORD,
        "HOST": MYSQL_HOST,
        "PORT": MYSQL_PORT,
        "TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"},
    },
}

########################## new alarm settings ############################ noqa
APP_CODE = str(os.environ.get("APP_ID", "bk_monitor"))  # noqa
SECRET_KEY = APP_SECRET_KEY = str(os.environ.get("APP_TOKEN", "******"))  # noqa

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
MONITOR_APP_CODE = APP_CODE
MONITOR_APP_SECRET_KEY = APP_SECRET_KEY

# base monitor config
MONITOR_HANDLE_DURATION = 60
MONITOR_HANDLE_COUNT = 10000
MONITOR_PROC_COUNT = 6
MONITOR_DATA_OVERTIME = 30 * 60

MONITOR_SRC_TYPE = ["BKMONITOR"]
BASE_ALARM_LIST = [2, 3, 6, 7, 8]

PROC_PORT_USE_TSDB = True

# queue config
MONITOR_ALERT_TOPIC = "0bkmonitor_backend0"

QUEUE_POP_COUNT = 20000

COLLECT_DEFAULT_COUNT = 10

ACCESS_PUSH_QUEUE_MAX_LENGTH = 100000

DEFAULT_LOCALE = "zh_Hans"

DEFAULT_TIMEZONE = "Asia/Shanghai"

CERT_PATH = "cert"
LICENSE_HOST = "license.service.consul"
LICENSE_PORT = "8443"
LICENSE_REQ_INTERVAL = [20, 60, 120]  # 连续请求n次，每次请求间隔(单位：秒)

# SUPERVISOR 配置
SUPERVISOR_PORT = 9001
SUPERVISOR_SERVER = "unix:///var/run/bkmonitor/monitor-supervisor.sock"
SUPERVISOR_USERNAME = ""
SUPERVISOR_PASSWORD = ""
SUPERVISOR_SOCK = "unix:///var/run/bkmonitor/monitor-supervisor.sock"

CELERY_CONF_TYPE = "redis_conf"

EVENT_CENTER_URL = "%s/o/bk_monitorv3/?bizId={bk_biz_id}&routeHash=event-center/?collectId={collect_id}#/" % PAAS_URL
HEALTHZ_DETAIL_URL = "%s/o/bk_monitor/{biz_id}/healthz/dashboard/" % PAAS_URL

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

# 异常记录保留天数
ANOMALY_RECORD_SAVE_DAYS = 30

BK_MONITOR_PROXY_LISTEN_PORT = 10205  # bk_monitor_proxy 自定义上报服务监听的端口

# event 模块最大容忍无数据周期数
EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE = 5

ANOMALY_RECORD_COLLECT_WINDOW = 100
ANOMALY_RECORD_CONVERGED_ACTION_WINDOW = 3
