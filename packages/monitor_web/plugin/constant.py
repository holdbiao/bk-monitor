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

from django.utils.translation import ugettext_lazy as _

BUILT_IN_TAGS = [_("主机"), _("消息中间件"), _("HTTP服务"), _("数据库"), _("办公应⽤"), _("其他")]

HEARTBEAT_MESSAGE_ID = 101178

BEAT_RUN_ERR = 4001  # 脚本运行报错
BEAT_PARAMS_ERR = 4002  # 脚本命令不合法
BEAT_FORMAT_OUTPUT_ERR = 4003  # 解析脚本标准输出报错

BEAT_ERR = {
    BEAT_RUN_ERR: _("脚本运行报错,原因是{}"),
    BEAT_PARAMS_ERR: _("脚本命令不合法,原因是{}"),
    BEAT_FORMAT_OUTPUT_ERR: _("解析脚本标准输出报错,原因是{}"),
}

OS_TYPE_TO_DIRNAME = {
    "windows": "external_plugins_windows_x86_64",
    "linux": "external_plugins_linux_x86_64",
    "linux_aarch64": "external_plugins_linux_aarch64",
    "aix": "external_plugins_aix_powerpc",
}
OS_TYPE_TO_SCRIPT_SUFFIX = {"shell": ".sh", "bat": ".bat", "custom": ""}

INNER_DIMENSIONS = [
    "bk_biz_id",
    "bk_target_ip",
    "bk_target_cloud_id",
    "bk_target_topo_level",
    "bk_target_topo_id",
    "bk_target_service_category_id",
    "bk_target_service_instance_id",
    "bk_collect_config_id",
]

PLUGIN_TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin_templates")


# config_json 字段类型选项
class ParamMode(object):
    # 采集器参数
    COLLECTOR = "collector"
    # 命令行选项参数
    OPT_CMD = "opt_cmd"
    # 命令行位置参数
    POS_CMD = "pos_cmd"
    # 环境变量
    ENV = "env"


PARAM_MODE_CHOICES = [
    ParamMode.COLLECTOR,
    ParamMode.OPT_CMD,
    ParamMode.POS_CMD,
    ParamMode.ENV,
]

SCRIPT_TYPE_CHOICES = (
    "shell",
    "bat",
    "python",
    "perl",
    "powershell",
    "vbs",
    "custom",
)

PROCESS_MATCH_TYPE_CHOICES = (
    "pid",
    "command",
)


class NodemanRegisterStatus(object):
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"


class DebugStatus(object):
    INSTALL = "INSTALL"
    FETCH_DATA = "FETCH_DATA"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"


class PluginType(object):
    EXPORTER = "Exporter"
    SCRIPT = "Script"
    JMX = "JMX"
    DATADOG = "DataDog"
    PUSHGATEWAY = "Pushgateway"
    BUILT_IN = "Built-In"
    LOG = "Log"
    PROCESS = "Process"
    SNMP_TRAP = "SNMP_Trap"
    SNMP = "SNMP"


class ConflictMap(object):
    """用于插件导入的冲突提示，此处国际化在调用方进行"""

    class VersionBelow(object):
        id = 1
        info = "导入版本不大于当前版本"

    class PluginType(object):
        id = 2
        info = "插件类型冲突"

    class RemoteCollectorConfig(object):
        id = 3
        info = "远程采集配置项冲突"

    class RelatedCollectorConfig(object):
        id = 4
        info = "插件已关联%s个采集配置"

    class DuplicatedPlugin(object):
        id = 5
        info = "导入插件与当前插件内容完全一致"


SUPPORT_REMOTE_LIST = [PluginType.PUSHGATEWAY, PluginType.JMX, PluginType.SNMP]

# 结果表保留字精确匹配列表
RT_RESERVED_WORD_EXACT = [
    "SERVER",
    "REPO",
    "VIEW",
    "TAGKEY",
    "ILLEGAL",
    "EOF",
    "WS",
    "IDENT",
    "BOUNDPARAM",
    "NUMBER",
    "INTEGER",
    "DURATIONVAL",
    "STRING",
    "BADSTRING",
    "BADESCAPE",
    "TRUE",
    "FALSE",
    "REGEX",
    "BADREGEX",
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "AND",
    "OR",
    "EQ",
    "NEQ",
    "EQREGEX",
    "NEQREGEX",
    "LT",
    "LTE",
    "GT",
    "GTE",
    "LPAREN",
    "RPAREN",
    "COMMA",
    "COLON",
    "DOUBLECOLON",
    "SEMICOLON",
    "DOT",
    "ALL",
    "ALTER",
    "ANY",
    "AS",
    "ASC",
    "BEGIN",
    "BY",
    "CREATE",
    "CONTINUOUS",
    "DATABASE",
    "DATABASES",
    "DEFAULT",
    "DELETE",
    "DESC",
    "DESTINATIONS",
    "DIAGNOSTICS",
    "DISTINCT",
    "DROP",
    "DURATION",
    "END",
    "EVERY",
    "EXISTS",
    "EXPLAIN",
    "FIELD",
    "FOR",
    "FROM",
    "GROUP",
    "GROUPS",
    "IF",
    "IN",
    "INF",
    "INSERT",
    "INTO",
    "KEY",
    "KEYS",
    "KILL",
    "LIMIT",
    "MEASUREMENT",
    "MEASUREMENTS",
    "NAME",
    "NOT",
    "OFFSET",
    "ON",
    "ORDER",
    "PASSWORD",
    "POLICY",
    "POLICIES",
    "PRIVILEGES",
    "QUERIES",
    "QUERY",
    "READ",
    "REPLICATION",
    "RESAMPLE",
    "RETENTION",
    "REVOKE",
    "SELECT",
    "SERIES",
    "SET",
    "SHOW",
    "SHARD",
    "SHARDS",
    "SLIMIT",
    "SOFFSET",
    "STATS",
    "SUBSCRIPTION",
    "SUBSCRIPTIONS",
    "TAG",
    "TO",
    "TIME",
    "VALUES",
    "WHERE",
    "WITH",
    "WRITE",
    "TIMESTAMP",
    "TIME",
    # 内置字段
    "BK_BIZ_ID",
    "IP",
    "PLAT_ID",
    "BK_CLOUD_ID",
    "CLOUD_ID",
    "COMPANY_ID",
    "BK_SUPPLIER_ID",
]

# 结果表保留字模糊匹配列表
RT_RESERVED_WORD_FUZZY = [
    "DELETE",
    "DROP",
    "GRANT",
    "REVOKE",
]

# 结果表表名保留字匹配列表
RT_TABLE_NAME_WORD_EXACT = [
    "ALL",
    "ALTER",
    "ANALYZE",
    "ANY",
    "AS",
    "ASC",
    "BEGIN",
    "BY",
    "CREATE",
    "CONTINUOUS",
    "DATABASE",
    "DATABASES",
    "DEFAULT",
    "DELETE",
    "DESC",
    "DESTINATIONS",
    "DIAGNOSTICS",
    "DISTINCT",
    "DROP",
    "DURATION",
    "END",
    "EVERY",
    "EXPLAIN",
    "FIELD",
    "FOR",
    "FROM",
    "GRANT",
    "GRANTS",
    "GROUP",
    "GROUPS",
    "IN",
    "INF",
    "INSERT",
    "INTO",
    "KEY",
    "KEYS",
    "KILL",
    "LIMIT",
    "SHOW",
    "MEASUREMENT",
    "MEASUREMENTS",
    "NAME",
    "OFFSET",
    "ON",
    "ORDER",
    "PASSWORD",
    "POLICY",
    "POLICIES",
    "PRIVILEGES",
    "QUERIES",
    "QUERY",
    "READ",
    "REPLICATION",
    "RESAMPLE",
    "RETENTION",
    "REVOKE",
    "SELECT",
    "SERIES",
    "SET",
    "SHARD",
    "SHARDS",
    "SLIMIT",
    "SOFFSET",
    "STATS",
    "SUBSCRIPTION",
    "SUBSCRIPTIONS",
    "TAG",
    "TO",
    "USER",
    "USERS",
    "VALUES",
    "WHERE",
    "WITH",
    "WRITE",
]

# SNMP Trap插件默认运行参数
DEFAULT_TRAP_CONFIG = {
    "server_port": "162",
    "listen_ip": "0.0.0.0",
    "yaml": {"filename": "", "value": ""},
    "community": "",
    "aggregate": True,
}
DEFAULT_TRAP_V3_CONFIG = {
    "version": "v3",
    "auth_info": [
        {
            "security_level": "noAuthNoPriv",
            "security_name": "",
            "context_name": "",
            "authentication_protocol": "MD5",
            "authentication_passphrase": "",
            "privacy_protocol": "DES",
            "privacy_passphrase": "",
            "authoritative_engineID": "",
        }
    ],
}

MAX_METRIC_NUM = 500
