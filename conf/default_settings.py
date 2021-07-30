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
conf.default_settings
=====================
"""

import os
import time

from django.utils.translation import ugettext_lazy as _lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(BASE_DIR, "USERRES")
MEDIA_URL = "/media/"

INSTALLED_APPS = ("metadata",)

MIDDLEWARE = tuple()
ENV = ""

#
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
#

DATABASES = {}

#
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
#

TIME_ZONE = "Etc/GMT%+d" % ((time.altzone if time.daylight else time.timezone) / 3600)

LANGUAGE_CODE = "zh-hans"

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_LOCALE = "zh_Hans"

DEFAULT_TIMEZONE = "Asia/Shanghai"

INIT_SUPERUSER = []

# auto clean DB connection
DATABASE_CONNECTION_AUTO_CLEAN_INTERVAL = 600

# ==================
# 前后台通用配置
# ==================

MIGRATE_MONITOR_API = False

# 是否开启网络设备忽略
USE_ETH_FILTER = True

SYSTEM_NET_GROUP_RT_ID = "system.net"
SYSTEM_NET_GROUP_FIELD_NAME = "device_name"

# 网络设备忽略条件列表
ETH_FILTER_CONDITION_LIST = [
    {"method": "!=", "sql_statement": "lo", "condition_regex": "^(?!lo$)"},
]

# 是否开启磁盘设备忽略
USE_DISK_FILTER = True

# 磁盘设备忽略条件列表
# method字段由SaaS在图形展示、策略配置的sql中作为where字段条件使用，
# 无 method 字段则为后台磁盘事件型告警进行过滤使用
DISK_FILTER_CONDITION_LIST_V1 = [
    {"method": "not like", "sql_statement": "%dev\\/loop%", "file_system_regex": r"/?dev/loop.*"},
    {"method": "not like", "sql_statement": "%dev\\/sr%", "file_system_regex": r"/?dev/sr.*"},
    {"method": "not like", "sql_statement": "%.iso", "file_system_regex": r".*?\.iso$"},
]

# SQL最大查询条数
SQL_MAX_LIMIT = 50000

# 数据点密度
# 单位宽度 每分钟图表点个数系数
POINT_COEFFICIENT = 300.0

FILE_SYSTEM_TYPE_RT_ID = "system.disk"
FILE_SYSTEM_TYPE_FIELD_NAME = "device_type"
FILE_SYSTEM_TYPE_IGNORE = ["iso9660", "tmpfs", "udf"]

AUTHENTICATION_BACKENDS = ()

RSA_PRIVATE_KEY = ""

# 是否开启默认策略
ENABLE_DEFAULT_STRATEGY = True

DEFAULT_OS_STRATEGIES = [
    {
        "name": _lazy("CPU总使用率"),
        "data_type_label": "time_series",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "usage",
        "result_table_id": "system.cpu_summary",
        "threshold": 95,
        "method": "gte",
        "trigger_count": 3,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("磁盘I/O使用率"),
        "data_type_label": "time_series",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "util",
        "result_table_id": "system.io",
        "threshold": 0.8,
        "method": "gte",
        "trigger_count": 3,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("磁盘使用率"),
        "data_type_label": "time_series",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "in_use",
        "result_table_id": "system.disk",
        "threshold": 95,
        "method": "gte",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("应用内存使用率"),
        "data_type_label": "time_series",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "pct_used",
        "result_table_id": "system.mem",
        "threshold": 95,
        "method": "gte",
        "trigger_count": 3,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("Agent心跳丢失"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "agent-gse",
        "trigger_count": 1,
        "trigger_check_window": 10,
        "recovery_check_window": 10,
    },
    {
        "name": _lazy("磁盘只读"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "disk-readonly-gse",
        "trigger_count": 1,
        "trigger_check_window": 20,
        "recovery_check_window": 20,
    },
    {
        "name": _lazy("Corefile产生"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "corefile-gse",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("PING不可达告警"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "ping-gse",
        "trigger_count": 3,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("OOM异常告警"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "oom-gse",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("主机重启"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "os_restart",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
        "agg_dimension": ["bk_target_ip", "bk_target_cloud_id"],
        "agg_method": "MAX",
    },
    {
        "name": _lazy("自定义字符型告警"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "os",
        "metric_field": "gse_custom_event",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
    },
    {
        "name": _lazy("进程端口"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "host_process",
        "metric_field": "proc_port",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
        "agg_dimension": [
            "bk_target_ip",
            "bk_target_cloud_id",
            "display_name",
            "protocol",
            "listen",
            "nonlisten",
            "not_accurate_listen",
            "bind_ip",
        ],
    },
]

DEFAULT_GSE_PROCESS_EVENT_STRATEGIES = [
    {
        "type": "business",
        "name": _lazy("Gse进程托管事件告警(业务侧)"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "host_process",
        "metric_id": "bk_monitor.gse_process_event",
        "metric_field": "gse_process_event",
        "result_table_id": "system.event",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
        "agg_condition": [
            {
                "key": "process_name",
                "method": "neq",
                "value": [
                    "basereport",
                    "processbeat",
                    "exceptionbeat",
                    "bkmonitorbeat",
                    "bkmonitorproxy",
                    "bkunifylogbeat",
                    "unifyTlogc",
                    "unifytlogc",
                    "gseAgent",
                ],
            },
        ],
    },
    {
        "type": "blueking",
        "name": _lazy("Gse进程托管事件告警(平台侧)"),
        "data_type_label": "event",
        "data_source_label": "bk_monitor",
        "result_table_label": "host_process",
        "metric_id": "bk_monitor.gse_process_event",
        "metric_field": "gse_process_event",
        "result_table_id": "system.event",
        "trigger_count": 1,
        "trigger_check_window": 5,
        "recovery_check_window": 5,
        "agg_condition": [
            {
                "key": "process_name",
                "method": "eq",
                "value": [
                    "basereport",
                    "processbeat",
                    "exceptionbeat",
                    "bkmonitorbeat",
                    "bkmonitorproxy",
                    "bkunifylogbeat",
                    "unifyTlogc",
                    "unifytlogc",
                    "gseAgent",
                ],
            },
        ],
    },
]

DEFAULT_NOTICE_GROUPS = [
    {
        "name": _lazy("主备负责人"),
        "notice_receiver": [{"id": "operator", "type": "group"}, {"id": "bk_bak_operator", "type": "group"}],
        "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
        "message": "",
    },
    {
        "name": _lazy("运维"),
        "notice_receiver": [{"id": "bk_biz_maintainer", "type": "group"}],
        "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
        "message": "",
    },
    {
        "name": _lazy("开发"),
        "notice_receiver": [{"id": "bk_biz_developer", "type": "group"}],
        "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
        "message": "",
    },
    {
        "name": _lazy("测试"),
        "notice_receiver": [{"id": "bk_biz_tester", "type": "group"}],
        "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
        "message": "",
    },
    {
        "name": _lazy("产品"),
        "notice_receiver": [{"id": "bk_biz_productor", "type": "group"}],
        "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
        "message": "",
    },
]

KERNEL_API_PORT = 28802
SAAS_APP_CODE = ""
SAAS_SECRET_KEY = ""
AES_X_KEY_FIELD = "SECRET_KEY"

# Resource Config
RESOURCE_CONFIG = {
    "overview": "monitor_web.overview.resources",
    "performance": "monitor_web.performance.resources",
    "config": "monitor_web.config.resources",
    "uptime_check": "monitor_web.uptime_check.resources",
    "plugin": "monitor_web.plugin.resources",
    "collecting": "monitor_web.collecting.resources",
    "notice_group": "monitor_web.notice_group.resources",
    "strategies": "monitor_web.strategies.resources",
    "alert_events": "monitor_web.alert_events.resources",
    "service_classify": "monitor_web.service_classify.resources",
    "shield": "monitor_web.shield.resources",
    "export_import": "monitor_web.export_import.resources",
    "custom_report": "monitor_web.custom_report.resources",
    "upgrade": "monitor_web.upgrade.resources",
    "healthz": "healthz.resources",
    "commons": "monitor_web.commons.resources",
    "cc": "monitor_web.cc.resources",
    "grafana": "monitor_web.grafana.resources",
    "data_explorer": "monitor_web.data_explorer.resources",
}

# 需要扫描的视图
ACTIVE_VIEWS = {
    "monitor_adapter": {"healthz": "healthz.views"},
    "monitor_api": {"monitor_api": "monitor_api.views"},
    "monitor_web": {
        "uptime_check": "monitor_web.uptime_check.views",
        "plugin": "monitor_web.plugin.views",
        "collecting": "monitor_web.collecting.views",
        "commons": "monitor_web.commons.views",
        "overview": "monitor_web.overview.views",
        "performance": "monitor_web.performance.views",
        "notice_group": "monitor_web.notice_group.views",
        "strategies": "monitor_web.strategies.views",
        "service_classify": "monitor_web.service_classify.views",
        "shield": "monitor_web.shield.views",
        "alert_events": "monitor_web.alert_events.views",
        "export_import": "monitor_web.export_import.views",
        "config": "monitor_web.config.views",
        "custom_report": "monitor_web.custom_report.views",
        "upgrade": "monitor_web.upgrade.views",
        "grafana": "monitor_web.grafana.views",
        "function_switch": "monitor_web.function_switch.views",
        "iam": "monitor_web.iam.views",
        "data_explorer": "monitor_web.data_explorer.views",
        "report": "monitor_web.report.views",
    },
    "weixin": {"mobile_event": "weixin.event.views"},
}

# 是否使用动态配置特性
if os.getenv("USE_DYNAMIC_SETTINGS", "").lower() in ["0", "false"]:
    USE_DYNAMIC_SETTINGS = False
else:
    USE_DYNAMIC_SETTINGS = True

# 告警通知消息队列配置
ENABLE_MESSAGE_QUEUE = True
MESSAGE_QUEUE_DSN = ""

# 采集数据存储天数
TS_DATA_SAVED_DAYS = 30

ENABLE_RESOURCE_DATA_COLLECT = False
RESOURCE_DATA_COLLECT_RATIO = 0

# 告警汇总配置
DIMENSION_COLLECT_THRESHOLD = 2
DIMENSION_COLLECT_WINDOW = 120
MULTI_STRATEGY_COLLECT_THRESHOLD = 3
MULTI_STRATEGY_COLLECT_WINDOW = 120

# 主机监控开关配置
HOST_DISABLE_MONITOR_STATES = ["备用机", "测试中", "故障中"]
HOST_DISABLE_NOTICE_STATES = ["运营中[无告警]", "开发中[无告警]"]

# Webhook配置
WEBHOOK_TIMEOUT = 3

RT_TABLE_PREFIX_VALUE = 0

# 文件存储是否使用CEPH
USE_CEPH = False

# 移动端告警带上移动端访问链接
ALARM_MOBILE_NOTICE_WAY = []
ALARM_MOBILE_URL = ""
PLUGIN_AES_KEY = "bk_monitorv3_enterprise"
ENTERPRISE_CODE = ""
SAAS_VERSION = ""
BACKEND_VERSION = ""

# 后台api默认用户
COMMON_USERNAME = "admin"

# 是否允许所有数据源配置CMDB聚合
IS_ALLOW_ALL_CMDB_LEVEL = False

# 与计算平台结合功能开关，
IS_ACCESS_BK_DATA = False  # 是否接入计算平台
AIOPS_BIZ_WHITE_LIST = []  # 是否开启AIOPS功能，业务ID白名单

# 是否由GSE分配dataid，默认是False，由监控自身来负责分配
IS_ASSIGN_DATAID_BY_GSE = False

DEMO_BIZ_ID = 0
DEMO_BIZ_WRITE_PERMISSION = False
DEMO_BIZ_APPLY = ""
BK_DOCS_VERSION = ""

# 企业微信群通知webhook_url
WXWORK_BOT_WEBHOOK_URL = ""
WXWORK_BOT_NAME = ""
WXWORK_BOT_SEND_IMAGE = True

# 执行流控的 APP 白名单
THROTTLE_APP_WHITE_LIST = []

# 邮件订阅默认业务ID，当ID为0时关闭邮件订阅
MAIL_REPORT_BIZ = 0
# 订阅报表运营数据内置指标UID
REPORT_DASHBOARD_UID = "CzhKanwtf"
# 订阅报表内部链接
MAIL_REPORT_URL = "{PAAS_URL}/o/bk_monitorv3/#/email-subscriptions"

# celery worker进程数量
CELERY_WORKERS = 0

# celery 默认禁用事件队列
CELERY_SEND_EVENTS = False
CELERY_SEND_TASK_SENT_EVENT = False
CELERY_TRACK_STARTED = False

# 当 ES 存在不合法别名时，是否保留该索引
ES_RETAIN_INVALID_ALIAS = True

# 监控SAAS的HOST
MONITOR_SAAS_URL = ""

# gse进程托管DATA ID
GSE_PROCESS_REPORT_DATAID = 1100008

# 日志采集器所属业务
BKUNIFYLOGBEAT_METRIC_BIZ = 0

# 跳过插件的调试
SKIP_PLUGIN_DEBUG = False

# bkmonitorbeat 升级支持新版节点ID(bk_cloud_id:ip)的版本
BKMONITORBEAT_SUPPORT_NEW_NODE_ID_VERSION = "1.13.95"

# 事件关联信息截断长度
EVENT_RELATED_INFO_LENGTH = 4096
NOTICE_MESSAGE_MAX_LENGTH = {}

CUSTOM_REPORT_DEFAULT_DATAID = 1100011
MAIL_REPORT_DATA_ID = 1100012

# 通知配置
ENABLED_NOTICE_WAYS = ["weixin", "mail", "sms", "voice"]
