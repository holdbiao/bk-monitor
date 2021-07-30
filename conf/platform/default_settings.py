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
conf.platform.default_settings
=========================
"""


import ntpath
import os
import posixpath

from django.utils.translation import ugettext_lazy as _

from bkmonitor.utils.i18n import TranslateDict

RUN_VER_DICT = {
    "qcloud": "qcloud",
    "enterprise": "open",
    "community": "open",
    "bkclouds": "clouds",
    "tencent": "ieod",
}

BKAPP_DEPLOY_PLATFORM = os.getenv("BKAPP_DEPLOY_PLATFORM", "ieod")

RUN_VER = RUN_VER_DICT.get(BKAPP_DEPLOY_PLATFORM, BKAPP_DEPLOY_PLATFORM)

APP_ID = APP_CODE = str(os.getenv("APP_ID", "bk_monitorv3"))

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = str(os.getenv(
#     "APP_TOKEN",
#     'ebf4462e-5c7b-47fd-b7a1-295388c3b8eb')
# )
# BK_PAAS_HOST = os.getenv('BK_PAAS_HOST', 'https://replace.me')
APP_TOKEN = SECRET_KEY = str(os.getenv("APP_TOKEN", "e7af1845-d05d-4e6b-8419-e8476f7f620f"))
BK_PAAS_HOST = os.getenv("BK_PAAS_HOST", "http://replace.me")
BK_PAAS_INNER_HOST = os.getenv("BK_PAAS_INNER_HOST", BK_PAAS_HOST)


# monitor api base url:
MONITOR_API_BASE_URL = ""  # placeholder
BKDATA_API_BASE_URL = ""  # placeholder
BKLOGSEARCH_API_BASE_URL = ""  # placeholder
BKNODEMAN_API_BASE_URL = ""  # placeholder
BKDOCS_API_BASE_URL = ""  # placeholder


BK_NODEMAN_VERSION = "2.0"  # 节点管理版本，默认是2.0，如果还是老的版本，需要在全局配置页面修改为1.3
BK_NODEMAN_HOST = os.getenv("BKAPP_NODEMAN_OUTER_HOST", BK_PAAS_HOST.rstrip("/") + "/o/bk_nodeman/")
BK_NODEMAN_INNER_HOST = os.getenv("BKAPP_NODEMAN_HOST") or os.getenv(
    "BKAPP_NODEMAN_INNER_HOST", "http://nodeman.bknodeman.service.consul"
)

BKLOGSEARCH_HOST = BK_PAAS_HOST.rstrip("/") + "/o/bk_log_search/"

SITE_URL = os.getenv("BK_SITE_URL", "/")

# SDK CLIENT

# sdk的最低版本要求
ESB_SDK_VERSION = ""
# sdk模块路径
ESB_SDK_NAME = "blueking.component"
# sdk的api请求前缀
ESB_API_PREFIX = "/api/c/compapi/"

#
# DataPlatform Settings
#
PROJECT_ID = 1
IS_ACCESS_BK_DATA = False  # 是否接入计算平台
IS_ENABLE_VIEW_CMDB_LEVEL = False  # 是否开启前端视图部分的CMDB预聚合

# 数据接入相关
BK_DATA_PROJECT_ID = 1  # 监控平台数据接入到计算平台 & 异常检测模型所在项目
BK_DATA_BK_BIZ_ID = 2  # 监控平台数据接入到计算平台的指定业务下
BK_DATA_PROJECT_MAINTAINER = ""  # 计算平台项目的维护人员
BK_DATA_RT_ID_PREFIX = ""  # 计算平台的表名前缀
BK_DATA_DATA_EXPIRES_DAYS = 30  # 接入到计算平台后，数据保留天数
BK_DATA_TSPIDER_STORAGE_CLUSTER_NAME = "jungle_alert"  # 监控专属tspider存储集群名称
BK_DATA_DRUID_STORAGE_CLUSTER_NAME = "monitor"  # 监控专属druid存储集群名称
BK_DATA_KAFKA_BROKER_URL = "127.0.0.1:9092"
BK_DATA_INTELLIGENT_DETECT_DELAY_WINDOW = 5

# 模型检测相关
BK_DATA_INTELLIGENT_DETECT_MODEL_ID = ""

# 表后缀(字母或数字([A-Za-z0-9]), 不能有下划线"_", 且最好不超过10个字符)
BK_DATA_RAW_TABLE_SUFFIX = "raw"  # 数据接入
BK_DATA_CMDB_FULL_TABLE_SUFFIX = "full"  # 补充cmdb节点信息后的表后缀
BK_DATA_CMDB_SPLIT_TABLE_SUFFIX = "cmdb"  # 补充表拆分后的表后缀


#
# Csrf_cookie
#
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_PATH = SITE_URL

#
# Session
#
SESSION_COOKIE_AGE = 60 * 60 * 24  # 单位--秒   60 * 60 * 24

# 作业平台url
JOB_URL = BK_PAAS_HOST.replace("paas", "job")
JOB_URL = os.getenv("BK_JOB_HOST", JOB_URL)

# 配置平台URL
BK_CC_URL = BK_PAAS_HOST.replace("paas", "cmdb")
BK_CC_URL = os.getenv("BK_CC_HOST", BK_CC_URL)

# agent安装url
AGENT_SETUP_URL = "%s/o/bk_nodeman/" % BK_PAAS_HOST

# ESB组件用户名称
ESB_USER_FIELD_NAME = "username"

#
# Cache
#
CACHE_CC_TIMEOUT = 60 * 10  # 缓存时间：CC集群、模块信息相关
CACHE_BIZ_TIMEOUT = 60 * 10  # 缓存时间：业务、人员信息相关
CACHE_HOST_TIMEOUT = 60 * 2  # 缓存时间：主机信息相关
CACHE_DATA_TIMEOUT = 60 * 2  # 缓存时间：计算平台接口相关
CACHE_OVERVIEW_TIMEOUT = 60 * 2  # 缓存时间：首页接口相关


# SaaS访问读写权限
ROLE_WRITE_PERMISSION = "w"
ROLE_READ_PERMISSION = "r"


# GSE SERVER IP 列表，以逗号分隔
GSE_SERVER_LAN_IP = os.getenv("BKAPP_GSE_SERVER_LAN_IP", "$GSE_IP")
GSE_SERVER_PORT = os.getenv("BKAPP_GSE_SERVER_PORT", "58629")

DEFAULT_BK_API_VER = locals().get("DEFAULT_BK_API_VER", "v2")

# 用户反馈地址
CE_URL = os.getenv("BKAPP_CE_URL", "https://bk.tencent.com/s-mart/community")

# 进程端口结果表名称
PROC_PORT_TABLE_NAME = "system_proc_port"
# 进程端口指标字段名称
PROC_PORT_METRIC_NAME = "proc_exists"
# 新版主机默认维度
NEW_DEFAULT_HOST_DIMENSIONS = ["bk_target_ip", "bk_cloud_id"]
# 仪表盘默认隐藏维度
IGNORED_DASHBOARD_DIMENSIONS = ["bk_biz_id"]
# 不同系统类型的信息
# windows系统配置
WINDOWS_SCRIPT_EXT = "bat"
WINDOWS_JOB_EXECUTE_ACCOUNT = "system"
WINDOWS_GSE_AGENT_PATH = "C:\\gse\\"
WINDOWS_FILE_DOWNLOAD_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "download")

WINDOWS_COLLECTOR_PLUGINS_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "plugins")

WINDOWS_PLUGINS_SETUP_PATH = ntpath.join(WINDOWS_COLLECTOR_PLUGINS_PATH, "bin")
WINDOWS_PLUGINS_CONF_PATH = ntpath.join(WINDOWS_COLLECTOR_PLUGINS_PATH, "etc")
WINDOWS_PLUGINS_PID_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "logs")
WINDOWS_PLUGINS_LOG_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "logs")
WINDOWS_PLUGINS_DATA_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "data")

WINDOWS_SCRIPT_COLLECTOR_CONF_PATH = WINDOWS_PLUGINS_CONF_PATH
WINDOWS_SCRIPT_COLLECTOR_CONF_NAME = "uptimecheckbeat_script.conf"
WINDOWS_SCRIPT_COLLECTOR_SETUP_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "scripts")
WINDOWS_EXPORTER_COLLECTOR_SETUP_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "external_collector")
WINDOWS_EXTERNAL_PLUGINS_PATH = ntpath.join(WINDOWS_GSE_AGENT_PATH, "external_plugins")
WINDOWS_EXTERNAL_PLUGINS_CONF_PATH = ntpath.join(WINDOWS_EXTERNAL_PLUGINS_PATH, "etc")

# datadog配置
WINDOWS_DATADOG_COLLECTOR_SETUP_PATH = ntpath.join(WINDOWS_EXTERNAL_PLUGINS_PATH, "datadog")
WINDOWS_DATADOG_COLLECTOR_CONF_NAME = "datadog.yml"
WINDOWS_DATADOG_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "datadog.pid")
WINDOWS_DATADOG_COLLECTOR_CONF_PATH = WINDOWS_EXTERNAL_PLUGINS_CONF_PATH
WINDOWS_DATADOG_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH
WINDOWS_DATADOG_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
# JMX采集配置
WINDOWS_JMX_COLLECTOR_SETUP_PATH = ntpath.join(WINDOWS_EXTERNAL_PLUGINS_PATH, "jmx_exporter")
WINDOWS_JMX_COLLECTOR_CONF_NAME = "jmx_exporter.yml"
WINDOWS_JMX_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "jmx_exporter.pid")
WINDOWS_JMX_COLLECTOR_CONF_PATH = WINDOWS_EXTERNAL_PLUGINS_CONF_PATH
WINDOWS_JMX_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH
WINDOWS_JMX_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
# SNMP采集配置
WINDOWS_SNMP_COLLECTOR_SETUP_PATH = ntpath.join(WINDOWS_EXTERNAL_PLUGINS_PATH, "snmp_exporter")
WINDOWS_SNMP_COLLECTOR_CONF_NAME = "snmp_exporter.yml"
WINDOWS_SNMP_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "snmp_exporter.pid")
WINDOWS_SNMP_COLLECTOR_CONF_PATH = WINDOWS_EXTERNAL_PLUGINS_CONF_PATH
WINDOWS_SNMP_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH
WINDOWS_SNMP_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
# 组件采集配置
WINDOWS_METRIC_BEAT_COLLECTOR_SETUP_PATH = WINDOWS_PLUGINS_SETUP_PATH
WINDOWS_METRIC_BEAT_COLLECTOR_CONF_NAME = "bkmetricbeat.conf"
WINDOWS_METRIC_BEAT_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "bkmetricbeat.pid")
WINDOWS_METRIC_BEAT_COLLECTOR_CONF_PATH = WINDOWS_PLUGINS_CONF_PATH
WINDOWS_METRIC_BEAT_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH
WINDOWS_METRIC_BEAT_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
# 拨测配置
WINDOWS_UPTIME_CHECK_COLLECTOR_SETUP_PATH = WINDOWS_PLUGINS_SETUP_PATH
WINDOWS_UPTIME_CHECK_COLLECTOR_CONF_NAME = "uptimecheckbeat.conf"
WINDOWS_UPTIME_CHECK_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "uptimecheckbeat.pid")
WINDOWS_UPTIME_CHECK_COLLECTOR_CONF_PATH = WINDOWS_PLUGINS_CONF_PATH
WINDOWS_UPTIME_CHECK_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH
WINDOWS_UPTIME_CHECK_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
# 日志配置
WINDOWS_LOG_COLLECTOR_SETUP_PATH = WINDOWS_PLUGINS_SETUP_PATH
WINDOWS_LOG_COLLECTOR_CONF_PATH = WINDOWS_PLUGINS_CONF_PATH
WINDOWS_LOG_COLLECTOR_CONF_NAME = "filebeat.conf"
WINDOWS_LOG_COLLECTOR_PID_PATH = ntpath.join(WINDOWS_PLUGINS_PID_PATH, "filebeat.pid")
WINDOWS_LOG_COLLECTOR_LOG_PATH = WINDOWS_PLUGINS_LOG_PATH
WINDOWS_LOG_COLLECTOR_DATA_PATH = WINDOWS_PLUGINS_DATA_PATH

WINDOWS_GSE_AGENT_IPC_PATH = "127.0.0.1:47000"

# linux系统配置
LINUX_SCRIPT_EXT = "sh"
LINUX_JOB_EXECUTE_ACCOUNT = "root"
LINUX_FILE_DOWNLOAD_PATH = "/tmp/bkdata/download/"
LINUX_GSE_AGENT_PATH = "/usr/local/gse/"

LINUX_COLLECTOR_PLUGINS_PATH = posixpath.join(LINUX_GSE_AGENT_PATH, "plugins")
LINUX_PLUGIN_SETUP_PATH = posixpath.join(LINUX_COLLECTOR_PLUGINS_PATH, "bin")
LINUX_PLUGIN_CONF_PATH = posixpath.join(LINUX_COLLECTOR_PLUGINS_PATH, "etc")
LINUX_PLUGIN_DATA_PATH = "/var/lib/gse"
LINUX_PLUGIN_PID_PATH = "/var/run/gse"
LINUX_PLUGIN_LOG_PATH = "/var/log/gse"
LINUX_SCRIPT_COLLECTOR_CONF_PATH = LINUX_PLUGIN_CONF_PATH
LINUX_SCRIPT_COLLECTOR_CONF_NAME = "uptimecheckbeat_script.conf"
LINUX_SCRIPT_COLLECTOR_SETUP_PATH = posixpath.join(LINUX_GSE_AGENT_PATH, "scripts")
LINUX_EXPORTER_COLLECTOR_SETUP_PATH = posixpath.join(LINUX_GSE_AGENT_PATH, "external_collector")
LINUX_EXTERNAL_PLUGINS_PATH = posixpath.join(LINUX_GSE_AGENT_PATH, "external_plugins")
LINUX_EXTERNAL_PLUGINS_CONF_PATH = posixpath.join(LINUX_EXTERNAL_PLUGINS_PATH, "etc")
# datadog配置
LINUX_DATADOG_COLLECTOR_SETUP_PATH = posixpath.join(LINUX_EXTERNAL_PLUGINS_PATH, "datadog")
LINUX_DATADOG_COLLECTOR_CONF_NAME = "datadog.yml"
LINUX_DATADOG_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "datadog.pid")
LINUX_DATADOG_COLLECTOR_CONF_PATH = LINUX_EXTERNAL_PLUGINS_CONF_PATH
LINUX_DATADOG_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_DATADOG_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH
# JMX采集配置
LINUX_JMX_COLLECTOR_SETUP_PATH = posixpath.join(LINUX_EXTERNAL_PLUGINS_PATH, "jmx_exporter")
LINUX_JMX_COLLECTOR_CONF_NAME = "jmx_exporter.yml"
LINUX_JMX_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "jmx_exporter.pid")
LINUX_JMX_COLLECTOR_CONF_PATH = LINUX_EXTERNAL_PLUGINS_CONF_PATH
LINUX_JMX_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_JMX_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH
# SNMP采集配置
LINUX_SNMP_COLLECTOR_SETUP_PATH = posixpath.join(LINUX_EXTERNAL_PLUGINS_PATH, "snmp_exporter")
LINUX_SNMP_COLLECTOR_CONF_NAME = "snmp_exporter.yml"
LINUX_SNMP_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "snmp_exporter.pid")
LINUX_SNMP_COLLECTOR_CONF_PATH = LINUX_EXTERNAL_PLUGINS_CONF_PATH
LINUX_SNMP_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_SNMP_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH
# 组件采集配置
LINUX_METRIC_BEAT_COLLECTOR_SETUP_PATH = LINUX_PLUGIN_SETUP_PATH
LINUX_METRIC_BEAT_COLLECTOR_CONF_NAME = "bkmetricbeat.conf"
LINUX_METRIC_BEAT_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "bkmetricbeat.pid")
LINUX_METRIC_BEAT_COLLECTOR_CONF_PATH = LINUX_PLUGIN_CONF_PATH
LINUX_METRIC_BEAT_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_METRIC_BEAT_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH
# 拨测配置
LINUX_UPTIME_CHECK_COLLECTOR_SETUP_PATH = LINUX_PLUGIN_SETUP_PATH
LINUX_UPTIME_CHECK_COLLECTOR_CONF_NAME = "uptimecheckbeat.conf"
LINUX_UPTIME_CHECK_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "uptimecheckbeat.pid")
LINUX_UPTIME_CHECK_COLLECTOR_CONF_PATH = LINUX_PLUGIN_CONF_PATH
LINUX_UPTIME_CHECK_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_UPTIME_CHECK_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH
# 日志配置
LINUX_LOG_COLLECTOR_SETUP_PATH = LINUX_PLUGIN_SETUP_PATH
LINUX_LOG_COLLECTOR_CONF_PATH = LINUX_PLUGIN_CONF_PATH
LINUX_LOG_COLLECTOR_CONF_NAME = "filebeat.conf"
LINUX_LOG_COLLECTOR_PID_PATH = posixpath.join(LINUX_PLUGIN_PID_PATH, "filebeat.pid")
LINUX_LOG_COLLECTOR_DATA_PATH = LINUX_PLUGIN_DATA_PATH
LINUX_LOG_COLLECTOR_LOG_PATH = LINUX_PLUGIN_LOG_PATH

LINUX_GSE_AGENT_IPC_PATH = "/var/run/ipc.state.report"

# aix系统配置
AIX_SCRIPT_EXT = "sh"
AIX_JOB_EXECUTE_ACCOUNT = "root"
AIX_FILE_DOWNLOAD_PATH = "/tmp/bkdata/download/"
AIX_GSE_AGENT_PATH = "/usr/local/gse/"

AIX_COLLECTOR_PLUGINS_PATH = posixpath.join(AIX_GSE_AGENT_PATH, "plugins")
AIX_PLUGIN_SETUP_PATH = posixpath.join(AIX_COLLECTOR_PLUGINS_PATH, "bin")
AIX_PLUGIN_CONF_PATH = posixpath.join(AIX_COLLECTOR_PLUGINS_PATH, "etc")
AIX_PLUGIN_DATA_PATH = "/var/lib/gse"
AIX_PLUGIN_PID_PATH = "/var/run/gse"
AIX_PLUGIN_LOG_PATH = "/var/log/gse"
AIX_SCRIPT_COLLECTOR_CONF_PATH = AIX_PLUGIN_CONF_PATH
AIX_SCRIPT_COLLECTOR_CONF_NAME = "uptimecheckbeat_script.conf"
AIX_SCRIPT_COLLECTOR_SETUP_PATH = posixpath.join(AIX_GSE_AGENT_PATH, "scripts")
AIX_EXPORTER_COLLECTOR_SETUP_PATH = posixpath.join(AIX_GSE_AGENT_PATH, "external_collector")
AIX_EXTERNAL_PLUGINS_PATH = posixpath.join(AIX_GSE_AGENT_PATH, "external_plugins")
AIX_EXTERNAL_PLUGINS_CONF_PATH = posixpath.join(AIX_EXTERNAL_PLUGINS_PATH, "etc")
# datadog配置
AIX_DATADOG_COLLECTOR_SETUP_PATH = posixpath.join(AIX_EXTERNAL_PLUGINS_PATH, "datadog")
AIX_DATADOG_COLLECTOR_CONF_NAME = "datadog.yml"
AIX_DATADOG_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "datadog.pid")
AIX_DATADOG_COLLECTOR_CONF_PATH = AIX_EXTERNAL_PLUGINS_CONF_PATH
AIX_DATADOG_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_DATADOG_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH
# JMX采集配置
AIX_JMX_COLLECTOR_SETUP_PATH = posixpath.join(AIX_EXTERNAL_PLUGINS_PATH, "jmx_exporter")
AIX_JMX_COLLECTOR_CONF_NAME = "jmx_exporter.yml"
AIX_JMX_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "jmx_exporter.pid")
AIX_JMX_COLLECTOR_CONF_PATH = AIX_EXTERNAL_PLUGINS_CONF_PATH
AIX_JMX_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_JMX_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH
# SNMP采集配置
AIX_SNMP_COLLECTOR_SETUP_PATH = posixpath.join(AIX_EXTERNAL_PLUGINS_PATH, "snmp_exporter")
AIX_SNMP_COLLECTOR_CONF_NAME = "snmp_exporter.yml"
AIX_SNMP_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "snmp_exporter.pid")
AIX_SNMP_COLLECTOR_CONF_PATH = AIX_EXTERNAL_PLUGINS_CONF_PATH
AIX_SNMP_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_SNMP_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH
# 组件采集配置
AIX_METRIC_BEAT_COLLECTOR_SETUP_PATH = AIX_PLUGIN_SETUP_PATH
AIX_METRIC_BEAT_COLLECTOR_CONF_NAME = "bkmetricbeat.conf"
AIX_METRIC_BEAT_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "bkmetricbeat.pid")
AIX_METRIC_BEAT_COLLECTOR_CONF_PATH = AIX_PLUGIN_CONF_PATH
AIX_METRIC_BEAT_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_METRIC_BEAT_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH
# 拨测配置
AIX_UPTIME_CHECK_COLLECTOR_SETUP_PATH = AIX_PLUGIN_SETUP_PATH
AIX_UPTIME_CHECK_COLLECTOR_CONF_NAME = "uptimecheckbeat.conf"
AIX_UPTIME_CHECK_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "uptimecheckbeat.pid")
AIX_UPTIME_CHECK_COLLECTOR_CONF_PATH = AIX_PLUGIN_CONF_PATH
AIX_UPTIME_CHECK_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_UPTIME_CHECK_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH
# 日志配置
AIX_LOG_COLLECTOR_SETUP_PATH = AIX_PLUGIN_SETUP_PATH
AIX_LOG_COLLECTOR_CONF_PATH = AIX_PLUGIN_CONF_PATH
AIX_LOG_COLLECTOR_CONF_NAME = "filebeat.conf"
AIX_LOG_COLLECTOR_PID_PATH = posixpath.join(AIX_PLUGIN_PID_PATH, "filebeat.pid")
AIX_LOG_COLLECTOR_DATA_PATH = AIX_PLUGIN_DATA_PATH
AIX_LOG_COLLECTOR_LOG_PATH = AIX_PLUGIN_LOG_PATH

AIX_GSE_AGENT_IPC_PATH = "/var/run/ipc.state.report"

# cmdb 开发商ID
BK_SUPPLIER_ACCOUNT = "0"

# 全局系统开关
OS_GLOBAL_SWITCH = ["linux", "windows", "linux_aarch64"]

# --角色管理--

# 告警通知角色
NOTIRY_MAN_DICT = TranslateDict(
    {
        "bk_biz_maintainer": _("运维"),
        "bk_biz_productor": _("产品人员"),
        "bk_biz_tester": _("测试人员"),
        "bk_biz_developer": _("开发人员"),
        "operator": _("主负责人"),
        "bk_bak_operator": _("备份负责人"),
    }
)

AUTHORIZED_ROLES = ("bk_biz_maintainer", "bk_biz_developer", "bk_biz_tester", "bk_biz_productor")

DEFAULT_ROLE_PERMISSIONS = {
    "bk_biz_maintainer": ROLE_WRITE_PERMISSION,  # noqa
    "bk_biz_productor": ROLE_READ_PERMISSION,  # noqa
    "bk_biz_developer": ROLE_READ_PERMISSION,  # noqa
    "bk_biz_tester": ROLE_READ_PERMISSION,  # noqa
}

# 预设dataid
# 注意：所有的DATAID配置都必须是以【_DATAID】结尾，否则会导致元数据模块无法识别
SNAPSHOT_DATAID = 1001
MYSQL_METRIC_DATAID = 1002
REDIS_METRIC_DATAID = 1003
APACHE_METRIC_DATAID = 1004
NGINX_METRIC_DATAID = 1005
TOMCAT_METRIC_DATAID = 1006
PROCESS_PERF_DATAID = 1007
PROCESS_PORT_DATAID = 1013

# 拨测预设dataid
UPTIMECHECK_HEARTBEAT_DATAID = 1008
UPTIMECHECK_TCP_DATAID = 1009
UPTIMECHECK_UDP_DATAID = 1010
UPTIMECHECK_HTTP_DATAID = 1011
UPTIMECHECK_ICMP_DATAID = 1100003

# ping server dataid
PING_SERVER_DATAID = 1100005

GSE_CUSTOM_EVENT_DATAID = 1100000

# 拨测任务默认最大请求超时设置(ms)
UPTIMECHECK_DEFAULT_MAX_TIMEOUT = 15000
# 拨测 配置模板
UPTIME_CHECK_CONFIG_TEMPLATE = {
    "logging.level": "error",
    "max_procs": 1,
    "output.console": None,
    "path.data": "/var/lib/gse",
    "path.logs": "/var/log/gse",
    "path.pid": "/var/run/gse",
    "uptimecheckbeat": {
        "ip": None,
        "clean_up_timeout": "1s",
        "event_buffer_size": 10,
        "mode": "daemon",
        "node_id": 0,
        "bk_biz_id": 0,
        "bk_cloud_id": 0,
        "heart_beat": {"dataid": UPTIMECHECK_HEARTBEAT_DATAID, "period": "60s"},
        # 下面三个max_timeout值控制对应任务最大执行超时时间。当子任务配置的available_duration超过该值时
        # 需要更新max_timeout -> available_duration + 5s
        # 这里默认15s可以满足大部分的场景。 15000 ms
    },
}

# 日志采集器配置文件模板
LOG_CONF_TEMPLATE = {
    "max_procs": 1,
    "enabled": True,
    "tail_files": True,
    "logging.level": "error",
    "filebeat.prospectors": [],
}

CACHE_USER_TIMEOUT = 60 * 5


HEADER_FOOTER_CONFIG = {
    "header": [{"zh": "监控平台 | 蓝鲸智云", "en": "BK Monitor | BlueKing"}],
    "footer": [
        {
            "zh": [
                {
                    "text": "QQ咨询(800802001)",
                    "link": "http://wpa.b.qq.com/cgi/wpa.php?ln=1&key=XzgwMDgwMjAwMV80NDMwOTZfODAwODAyMDAxXzJf",
                },
                {"text": "蓝鲸论坛", "link": "https://bk.tencent.com/s-mart/community"},
                {"text": "蓝鲸官网", "link": "https://bk.tencent.com/"},
                {"text": "蓝鲸智云桌面", "link": BK_PAAS_HOST},
            ],
            "en": [
                {
                    "text": "QQ(800802001)",
                    "link": "http://wpa.b.qq.com/cgi/wpa.php?ln=1&key=XzgwMDgwMjAwMV80NDMwOTZfODAwODAyMDAxXzJf",
                },
                {"text": "BlueKing Forum", "link": "https://bk.tencent.com/s-mart/community"},
                {"text": "Blueking Official", "link": "https://bk.tencent.com/"},
                {"text": "BlueKing Desktop", "link": BK_PAAS_HOST},
            ],
        }
    ],
    "copyright": "Copyright © 2012-2020 Tencent BlueKing. All Rights Reserved.",
}


# 数据平台数据查询TOKEN
ENABLE_BKDATA_TOKEN_AUTH = False
BKDATA_DATA_TOKEN = os.getenv("BKAPP_BKDATA_DATA_TOKEN", "")

BKDOCS_API_BASE_URL = ""

# IAM
BK_IAM_SYSTEM_ID = "bk_monitorv3"
BK_IAM_SYSTEM_NAME = _("监控平台")

BK_IAM_INNER_HOST = os.getenv("BK_IAM_HOST", os.getenv("BK_IAM_V3_INNER_HOST") or "http://bkiam.service.consul:5001")

BK_IAM_RESOURCE_API_HOST = os.getenv("BKAPP_IAM_RESOURCE_API_HOST", f"{BK_PAAS_HOST}/o/{APP_CODE}/")

# 权限中心 SaaS host
BK_IAM_APP_CODE = os.getenv("BK_IAM_V3_APP_CODE", "bk_iam")
BK_IAM_SAAS_HOST = os.environ.get("BK_IAM_V3_SAAS_HOST", f"{BK_PAAS_HOST}/o/{BK_IAM_APP_CODE}/")

# 文档中心地址
BK_DOCS_SITE_URL = BK_PAAS_HOST + "/o/bk_docs_center/"

# 监控SAAS的HOST
MONITOR_SAAS_URL = f'{os.environ.get("BK_PAAS_PUBLIC_URL", BK_PAAS_HOST)}/o/bk_monitorv3'

# 采集配置文件参数最大值(M)
COLLECTING_CONFIG_FILE_MAXSIZE = 2

GSE_MANAGERS = []
