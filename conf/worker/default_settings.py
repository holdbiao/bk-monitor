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
conf.worker.default_settings
============================
"""
import multiprocessing

from jinja2 import DebugUndefined

from conf.default_settings import *  # noqa
import os

# load platform config
BKAPP_DEPLOY_PLATFORM = os.environ.get("DJANGO_CONF_MODULE", "").split(".")[-1]
if not BKAPP_DEPLOY_PLATFORM:
    try:
        local_module = __import__("local_settings", globals(), locals(), ["*"])
        BKAPP_DEPLOY_PLATFORM = getattr(local_module, "BKAPP_DEPLOY_PLATFORM")
    except ImportError:
        pass
    BKAPP_DEPLOY_PLATFORM = BKAPP_DEPLOY_PLATFORM or "tencent"

_platform_module = __import__("conf.platform.%s" % BKAPP_DEPLOY_PLATFORM, globals(), locals(), ["*"])

for _setting in dir(_platform_module):
    locals()[_setting] = getattr(_platform_module, _setting)

ROOT_PATH = BASE_DIR  # noqa: F405
LOG_PATH = os.path.join(ROOT_PATH, "logs/")
BAK_PATH = os.path.join(ROOT_PATH, "data/")

# SUPERVISOR 配置
SUPERVISOR_PORT = 9001
SUPERVISOR_SERVER = "127.0.0.1:%s" % SUPERVISOR_PORT
SUPERVISOR_USERNAME = ""
SUPERVISOR_PASSWORD = ""
SUPERVISOR_SOCK = "supervisor.sock"

INSTALLED_APPS += (  # noqa: F405
    "django_jinja",
    "bkmonitor",
    "alarm_backends",
    "core.drf_resource",
)

# 系统名称
BACKEND_NAME = "BK Monitor Backend"

# 当第一次拉取或者距离上次拉取时间很久了，则以下面这个值为准
MIN_DATA_ACCESS_CHECKPOINT = 30 * 60  # unit: seconds

NUM_OF_COUNT_FREQ_ACCESS = 1  # 每次往前多拉取1个周期的数据
EXPIRE_TIME_OF_DUPLICATE_KEY = 10 * 60

DATA_ACCESS_PROCESS_INTERVAL = "monitor.data.access.process.interval"
DATA_DETECT_PROCESS_INTERVAL = "monitor.data.detect.process.interval"

# 当连接redis或beanstalkd失败之后多少秒内不尝试重连
RECONNECT_INTERVAL = 60

# redis queue name / beanstalk tube name
QUEUE_RECOVERY = "ALARMS_TO_RECOVERY"
QUEUE_CONVERGE = "ALARMS_TO_CONVERGE"
QUEUE_JOB = "ALARMS_TO_JOB"
QUEUE_SOLUTION = "ALARMS_TO_SOLUTION"  # 叫 NEW 是因为升级过一次
QUEUE_COLLECT = "ALARMS_TO_COLLECT"
QUEUE_SCHEDULER = "ALARMS_TO_SCHEDULER"
QUEUE_POLLING = "ALARMS_TO_POLLING"
QUEUE_MATCH = "ALARMS_TO_MATCH"

# beanstalk block args
BLOCK_CHECK_INTERVAL = 60
BLOCK_TIME_THRESHOLD = 5  # More than this num jobs in queue, means blocked

LOG_LOGFILE_MAXSIZE = 1024 * 1024 * 1024 * 10  # 10GB
LOG_LOGFILE_BACKUP_COUNT = 5
LOG_LOGFILE_BACKUP_GZIP = True
LOG_PROCESS_CHECK_TIME = 60 * 60 * 4

LOGGER_HANDLERS = ["file", "sentry"]
if os.getenv("LOGGER_WITHOUT_CONSOLE") != "1":
    LOGGER_HANDLERS.append("console")
if os.getenv("LOGGER_WITHOUT_REDIS") != "1":
    LOGGER_HANDLERS.append("redis")

# LOGGING
LOGGER_LEVEL = "DEBUG"
LOGGER_DEFAULT = {
    "level": LOGGER_LEVEL,
    "propagate": False,
    "handlers": LOGGER_HANDLERS,
}

LOG_FILE_PATH = os.path.join(LOG_PATH, "kernel.log")
LOG_IMAGE_EXPORTER_FILE_PATH = os.path.join(LOG_PATH, "kernel_image_exporter.log")
LOGGING = LOGGER_CONF = {
    "version": 1,
    "loggers": {
        "": {"level": "ERROR", "handlers": LOGGER_HANDLERS},
        "poll_alarm": LOGGER_DEFAULT,
        "poll_data": LOGGER_DEFAULT,
        "match_alarm": LOGGER_DEFAULT,
        "cron": LOGGER_DEFAULT,
        "report_cron": LOGGER_DEFAULT,
        "collect": LOGGER_DEFAULT,
        "nodata": LOGGER_DEFAULT,
        "alarm": LOGGER_DEFAULT,
        "recovery": LOGGER_DEFAULT,
        "converge": LOGGER_DEFAULT,
        "solution": LOGGER_DEFAULT,
        "job": LOGGER_DEFAULT,
        "monitor": LOGGER_DEFAULT,
        "stat": LOGGER_DEFAULT,
        "qos": LOGGER_DEFAULT,
        "scheduler": LOGGER_DEFAULT,
        "polling": LOGGER_DEFAULT,
        "webserver": LOGGER_DEFAULT,
        "apiserver": LOGGER_DEFAULT,
        "utils": LOGGER_DEFAULT,
        "advice": LOGGER_DEFAULT,
        "event": LOGGER_DEFAULT,
        "watchdog": LOGGER_DEFAULT,
        "test": LOGGER_DEFAULT,
        "adapter": LOGGER_DEFAULT,
        "data_access": LOGGER_DEFAULT,
        "component": LOGGER_DEFAULT,
        "kernel": LOGGER_DEFAULT,
        "project": LOGGER_DEFAULT,
        "bkmonitor": LOGGER_DEFAULT,
        "packages": LOGGER_DEFAULT,
        "metadata": LOGGER_DEFAULT,
        "file-only": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["file"]},
        "console-only": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["console"]},
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

QOS_MATCH_QUEUE_MAX_SIZE = 1000  # queue size to start pull alarm qos
QOS_MATCH_QUEUE_MIN_SIZE = 300  # queue size to stop pull alarm qos

QOS_CONVERGE_QUEUE_MAX_SIZE = 10000  # queue size to start pull alarm qos
QOS_CONVERGE_QUEUE_MIN_SIZE = 5000  # queue size to stop pull alarm qos

QOS_COLLECT_QUEUE_MAX_SIZE = 1000  # queue size to start pull alarm qos
QOS_COLLECT_QUEUE_MIN_SIZE = 500  # queue size to stop pull alarm qos

QOS_PULL_ALARM_FLOW_CONTROL_KEY = "QOS_PULL_ALARM_FLOW_CONTROL_KEY"
QOS_DROP_ALARM_THREADHOLD = 3
QOS_FLOW_CONTROL_WINDOW = 30  # 30 minutes
COLLECT_ALARM_THRESHOLD = 2  # collect alarm threshold

CONVERGE_INCIDENT_DEF_LIST_CACHE_EXPIRES = 60  # 60 seconds

CRITICAL_LOG_CONVERGE_THREADHOLD = 5  # number to converge
CRITICAL_LOG_EXPIRE = 10 * 60  # seconds

ERROR_LOG_CONVERGE_THREADHOLD = 3  # number to converge
ERROR_LOG_EXPIRE = 20 * 60  # seconds

DIMENSION_ZSET_KEY_LIST = "zset_key_list"

CELERY_REDIS_DB = 6

CELERY_MAX_TASKS_PER_CHILD = 100

TRACE_KEY_EXPIRES = 3600
TRACE_LOG_MAX_ITEMS = 50

TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": ["django.template.context_processors.i18n"],
            "undefined": DebugUndefined,
        },
    },
    {"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True},
]

DATA_SOURCE_TYPE_CLASSES = {
    "TSPIDER": "kernel.data_detect.source.tsp_data_source.TspDataSource",
    "TSDB": "kernel.data_detect.source.ts_data_source.TsDataSource",
    "ES": "kernel.data_detect.source.es_data_source.EsDataSource",
}

STORAGE_SOURCE_TYPE_CLASSES = {
    "TSPIDER": "kernel.data_detect.source.tsp_data_source.TspDataSource",
    "TSDB": "kernel.data_detect.source.ts_data_source.TsDataSource",
    "ES": "kernel.data_detect.source.es_data_source.EsDataSource",
}

PLATFORM_QUERY_METHOD = {
    "BK": "project.utils.query_bk_data.get_data",
    "MONITOR": "kernel.utils.kernel_api.get_data",
}

SOURCE_TYPE_TO_STORAGE_TYPE_AND_PLATFORM = {
    "TSDATA": ("TSDB", "MONITOR"),
    "BKDATA": ("TSPIDER", "BK"),
    "BKTSDB": ("TSDB", "BK"),
    "BKTSPIDER": ("TSPIDER", "BK"),
    "ESDATA": ("ES", "BK"),
}

DEFAULT_LOCALE = "zh_Hans"
DEFAULT_TIMEZONE = "Asia/Shanghai"
LOCALE_PATHS = (os.path.join(ROOT_PATH, "locale"),)

SENTRY_DSN = ""

# 自定义上报服务器IP
CUSTOM_REPORT_DEFAULT_PROXY_IP = []
CUSTOM_REPORT_DEFAULT_PROXY_DOMAIN = []

RT_TABLE_PREFIX_VALUE = 0
GRAPH_RENDER_SERVICE_API = ""
GRAPH_RENDER_SERVICE_APP_CODE = ""
GRAPH_RENDER_SERVICE_ENABLED = True
GRAPH_RENDER_SERVICE_DEFAULT_DELAY = 0.3
ALARM_CHART_BIZ_IDS = []

BKMONITOR_WORKER_INCLUDE_LIST = []
WECHAT_URL = ""
EVENT_CENTER_URL = ""
HEALTHZ_DETAIL_URL = ""

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# 告警检测范围动态关联开关
DETECT_RANGE_DYNAMIC_ASSOCIATE = True

ENABLE_PING_ALARM = True
ENABLE_AGENT_ALARM = True
ENABLE_DIRECT_AREA_PING_COLLECT = True  # 是否开启直连区域的PING采集

REDIS_LOG_PORT = 6379

try:
    # os.getuid()在windows系统下会报错
    REDIS_LOG_PORT = os.getuid() + REDIS_LOG_PORT
except Exception:
    pass

ALARM_SAVE_DAYS = 730

HEALTHZ_ALARM_CONFIG = {}

# CRONTAB
DEFAULT_CRONTAB = [
    # eg:
    # (module_name, every) like: ("fta.poll_alarm.main start", "* * * * *")
    # Notice Notice Notice:
    # Use UTC's time zone to set your crontab instead of the local time zone
    # cmdb cache
    ("alarm_backends.core.cache.cmdb.host", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.module", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.business", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.service_instance", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.topo", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.service_template", "*/10 * * * *"),
    ("alarm_backends.core.cache.cmdb.set_template", "*/10 * * * *"),
    # model cache
    ("alarm_backends.core.cache.strategy", "* * * * *"),
    ("alarm_backends.core.cache.shield", "* * * * *"),
    ("alarm_backends.core.cache.models.collect_config", "* * * * *"),
    ("alarm_backends.core.cache.models.uptimecheck", "* * * * *"),
    # api cache
    ("alarm_backends.core.cache.result_table", "*/10 * * * *"),
    # hash ring result
    ("alarm_backends.core.cache.hash_ring", "* * * * *"),
    # delay queue
    ("alarm_backends.core.cache.delay_queue", "* * * * *"),
    # notice
    ("alarm_backends.service.action.notice.scheduler.create_notice_action", "* * * * *"),
    ("alarm_backends.service.action.notice.scheduler.collect_anomaly_record", "*/30 * * * *"),
    ("alarm_backends.service.action.shield.tasks.check_and_send_shield_notice", "* * * * *"),
    ("alarm_backends.service.action.shield.tasks.update_event_shield_status", "*/3 * * * *"),
    ("alarm_backends.service.event.manager.tasks.check_abnormal_event", "* * * * *"),
    ("alarm_backends.service.event.generator.tasks.update_event_action_from_cache", "*/5 * * * *"),
    ("alarm_backends.service.event.generator.tasks.sync_event_cache", "*/10 * * * *"),
    ("alarm_backends.service.trigger.tasks.clean_anomaly_records", "* * * * *"),
    # clean detect result cache
    ("alarm_backends.core.detect_result.tasks.clean_disabled_strategies", "*/10 * * * *"),
    ("alarm_backends.core.detect_result.tasks.clean_expired_detect_result", "0 */2 * * *"),
    ("alarm_backends.core.detect_result.tasks.clean_md5_to_dimension_cache", "0 23 * * *"),
    # metadata
    # metadata更新每个influxdb的存储RP，UTC时间的22点进行更新，待0点influxdb进行清理
    ("metadata.task.refresh_default_rp", "0 22 * * *"),
    # metadata同步自定义事件维度及事件，每三分钟将会从ES同步一次
    ("metadata.task.custom_report.check_event_update", "*/3 * * * *"),
    # metadata同步pingserver配置，下发iplist到proxy机器，每10分钟执行一次
    ("metadata.task.ping_server.refresh_ping_server_config_to_node_man", "*/10 * * * *"),
    # metadata同步自定义上报配置到节点管理，完成配置订阅，理论上，在配置变更的时候，会执行一次，所以这里运行周期可以放大
    ("metadata.task.custom_report.refresh_custom_report_config_to_node_man", "*/5 * * * *"),
    # metadata同步自定义时序维度信息, 每5分钟将会从consul同步一次
    ("metadata.task.custom_report.check_update_time_series_metric_update", "*/5 * * * *"),
    # metadata自动部署bkmonitorproxy
    ("metadata.task.auto_deploy_proxy", "30 */2 * * *"),
    # 刷新metadata相关配置，10分钟一次
    ("metadata.task.config_refresh.refresh_influxdb_route", "*/10 * * * *"),
    ("metadata.task.config_refresh.refresh_datasource", "*/10 * * * *"),
    ("metadata.task.config_refresh.refresh_kafka_storage", "*/10 * * * *"),
    ("metadata.task.config_refresh.refresh_es_storage", "*/10 * * * *"),
    # mail_report 配置管理和告警接收人信息缓存
    ("alarm_backends.core.cache.mail_report", "*/30 * * * *"),
]

SELF_MONITORING_NODES = [
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

SELF_MONITORING_SWITCH = True

# Timeout for image exporter service, default set to 10 seconds
IMAGE_EXPORTER_TIMEOUT = 10

AES_X_KEY_FIELD = "SAAS_SECRET_KEY"

GSE_BASE_ALARM_DATAID = 1000
GSE_CUSTOM_EVENT_DATAID = 1100000

TRANSFER_HOST = ""
TRANSFER_PORT = ""
INFLUXDB_HOST = ""
INFLUXDB_PORT = ""

TOPO_DIMENSIONS = {
    "cc_app_module",
    "bk_topo_node",
    "cc_topo_module",
    "cc_topo_set",
}

BKMONITOR_WORKER_INET_DEV = ""

BKMONITOR_WORKER_MIN_INTERVAL = 0.1  # seconds
BKMONITOR_WORKER_MAX_CYCLES = 1000
BKMONITOR_WORKER_MAX_UPTIME = 60 * 60  # seconds
BKMONITOR_WORKER_CONSUL_SESSION_TTL = 60

BKMONITOR_WORKER_INCLUDE_LIST = []
BKMONITOR_WORKER_EXCLUDE_LIST = []

RUN_DATA_ACCESS_MIDDLWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
)

DATABASE_ROUTERS = ("bkmonitor.db_routers.BackendRouter",)

# ACTION
MESSAGE_QUEUE_MAX_LENGTH = 0

# SELF-MONITOR
SUPERVISOR_PROCESS_UPTIME = 10

# 特别的AES加密配置信息
SPECIFY_AES_KEY = ""

SELFMONITOR_PORTS = {"gse-data": 58625}

# 计算平台localTime与UTC时间的差值
BKDATA_LOCAL_TIMEZONE_OFFSET = -8
# 计算平台数据的localTime与当前时间比较的阈值，小于该值时下次再拉取数据
BKDATA_LOCAL_TIME_THRESHOLD = 10

# 跳过权限中心检查
SKIP_IAM_PERMISSION_CHECK = True

# event 模块最大容忍无数据周期数
EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE = 5

ANOMALY_RECORD_COLLECT_WINDOW = 100
ANOMALY_RECORD_CONVERGED_ACTION_WINDOW = 3

# access模块策略拉取耗时限制（每10分钟）
ACCESS_TIME_PER_WINDOW = 30

# 聚合网关默认业务ID
AGGREGATION_BIZ_ID = 2
