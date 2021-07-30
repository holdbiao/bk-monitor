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


from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.utils.i18n import TranslateDict
from bkmonitor.utils.time_tools import biz_time_zone_offset


def enum(**enums):
    return type(str("Enum"), (), enums)


# 进程端口状态
PROC_PORT_STATUS = enum(
    UNKNOWN=-1,
    LISTEN=0,
    NONLISTEN=1,
    NOT_ACCURATE_LISTEN=2,
)

# Agent状态
AGENT_STATUS = enum(UNKNOWN=-1, ON=0, OFF=1, NOT_EXIST=2, NO_DATA=3)

# 需要展示的标准属性列表
DISPLAY_STANDARD_PROPERTY_LIST = [
    "set",
    "module",
    "bk_cloud_id",
    "operator",
    "bk_bak_operator",
    "bk_host_name",
    "bk_os_name",
    "status",
    "bk_region",
    "bk_mem",
    "bk_cpu",
]

# sql查询条件映射
CONDITION_CONFIG = {"lt": "<", "gt": ">", "lte": "<=", "gte": ">=", "in": " in ", "like": " like ", "!=": "!="}

# 统计方法解释
VALUE_METHOD_DESC = TranslateDict(
    {"sum": _lazy("求和"), "max": _lazy("最大"), "min": _lazy("最小"), "avg": _lazy("平均"), "count": "count(*)"}
)

# 告警策略
STRATEGY_CHOICES = TranslateDict(
    {
        1000: _lazy("静态阈值"),
        1001: _lazy("同比策略（简易）"),
        1002: _lazy("环比策略（简易）"),
        1003: _lazy("同比策略（高级）"),
        1004: _lazy("环比策略（高级）"),
        1005: _lazy("同比振幅"),
        1006: _lazy("同比区间"),
        1007: _lazy("环比振幅"),
        4000: _lazy("关键字匹配"),
        5000: _lazy("进程端口监控检测策略"),
        5001: _lazy("系统重新启动监控策略"),
        6000: _lazy("自定义字符型告警"),
    }
)

# 通知方式小图标
NOTIRY_WAY_DICT = TranslateDict(
    {
        "mail": _lazy(
            '<i class=" text-primary data-tip" '
            'style="background:url({STATIC_URL}alert/img/mail.png) no-repeat;'
            'padding:0px 12px;display:inline-block;height:19px; background-size:22px 20px" '
            'data-html="true" data-trigger="hover" data-placement="top" '
            'data-content="邮件"></i>'
        ),
        "wechat": _lazy(
            '<i class="text-success data-tip" '
            'style="background:url({STATIC_URL}alert/img/wechat.png) no-repeat;'
            'padding:0px 12px;display:inline-block;height:19px;background-size:22px 20px"'
            'data-html="true" data-trigger="hover" data-placement="top" '
            "data-content=微信></i>"
        ),
        "sms": _lazy(
            '<i class="text-success data-tip" '
            'style="background:url({STATIC_URL}alert/img/message.png) no-repeat;'
            'padding:0px 12px;display:inline-block;height:19px;background-size:22px 20px"'
            'data-html="true" data-trigger="hover" data-placement="top" '
            "data-content=短信></i>"
        ),
        "im": _lazy(
            '<i class="text-info data-tip" '
            'style="background:url({STATIC_URL}alert/img/rtx.png) no-repeat;'
            'padding:0px 12px;display:inline-block;height:19px;background-size:22px 20px"'
            'data-html="true" data-trigger="hover" data-placement="top" '
            'data-content="RTX"></i>'
        ),
        "phone": _lazy(
            '<i class="text-info data-tip" '
            'style="background:url({STATIC_URL}alert/img/phone.png) no-repeat;'
            'padding:0px 12px;display:inline-block;height:19px;background-size:22px 20px"'
            'data-html="true" data-trigger="hover" data-placement="top" '
            "data-content=电话></i>"
        ),
    }
)

NOTIRY_WAY_NAME_DICT = {
    "mail": _lazy("邮件"),
    "wechat": _lazy("微信"),
    "sms": _lazy("短信"),
    "im": "RTX",
    "phone": _lazy("电话"),
}

# 通知方式大图标
NOTIRY_WAY_DICT_NEW = TranslateDict(
    {
        "mail": _lazy(
            """
    <img class="data-tip" src="{STATIC_URL}alert/img/mail.png"
    data-html="true" data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>邮件</span>">
    """
        ),
        "wechat": _lazy(
            """
    <img class="data-tip" src="{STATIC_URL}alert/img/wechat.png"
    data-html="true" data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>微信</span>">
    """
        ),
        "sms": _lazy(
            """
    <img class="data-tip" src="{STATIC_URL}alert/img/message.png"
    data-html="true" data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>短信</span>">
    """
        ),
        "im": """
    <img class="data-tip" src="{STATIC_URL}alert/img/im.png"
    data-html="true" data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>RTX</span>">
    """,
        "phone": _lazy(
            """
    <img class="data-tip" src="{STATIC_URL}alert/img/phone.png"
    data-html="true" data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>电话</span>">
    """
        ),
    }
)

NOTICE_GROUP_SPAN = """
    <span class="data-tip label label-success" data-html="true"
    data-trigger="hover" data-placement="top"
    data-content="<span class='word-break'>%s</span>">%s</span>
    """

# AlertInstance的告警维度(dimensions)
JUNGLE_SUBJECT_TYPE = TranslateDict(
    {
        "cc_set": _lazy("大区"),
        "set": _lazy("大区"),
        "os": _lazy("系统"),
        "plat": _lazy("平台"),
        "ip": "IP",
        "cc_module": _lazy("模块"),
        "_server_": "IP",
        "_path_": _lazy("路径"),
    }
)

# 主机性能采集间隔(毫秒)
HOST_POINT_INTERVAL = 60 * 1000

# 数据延时判定(秒)
POINT_DELAY_SECONDS = 60 * 10
POINT_DELAY_COLOR = "#f3b760"

# 告警事件类型
ALARM_EVENT_TYPE = enum(
    alwaysAlert="alwaysAlert",
    recentAlert="recentAlert",
    recentOperate="recentOperate",
)

# TSDB 仪表盘展示配置
# 仪表盘时序图最多一个指标展示10条曲线
TIME_VIEW_MAX_SERIES_COUNT = 100
TOP_VIEW_DEFAULT_SERIES_COUNT = 10

SHELL_COLLECTOR_DB = "selfscript"
UPTIME_CHECK_DB = "uptimecheck"
STRUCTURED_LOG_DB = "slog"

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

MYSQL_COMMON_RT_FIELDS = [
    {
        "field": "timestamp",
        "description": _lazy("时间戳"),
        "type": "timestamp",
        "is_dimension": False,
        "origins": None,
        "default_value": '{"value":null}',
    },
    {
        "field": "_server_",
        "description": _lazy("上报IP"),
        "type": "string",
        "is_dimension": True,
        "origins": None,
        "default_value": '{"value":null}',
    },
    {
        "field": "_delay_",
        "description": _lazy("总延迟"),
        "type": "int",
        "is_dimension": True,
        "origins": None,
        "default_value": '{"value":null}',
    },
    {
        "field": "_ab_delay_",
        "description": _lazy("净延迟"),
        "type": "int",
        "is_dimension": True,
        "origins": None,
        "default_value": '{"value":null}',
    },
]

INSTALLED_METRIC = (
    "monitor_web.core.metric.uptimecheck.UptimeCheckFactory",
    "monitor_web.core.metric.plugin.PluginMetricFactory",
    "monitor_web.core.metric.bk_data.BkDataMetricFactory",
)

# 业务ID可能的字段名称
BIZ_ID_FIELD_NAMES = ["bk_biz_id", "biz_id", "cc_biz_id", "app_id", "bizId"]


# 自定义导入规定的logo尺寸 (宽度, 高度)
class ExporterLogoSize(object):
    NORMAL = (155, 65)
    SMALL = (63, 27)


# exporter监听地址参数名称
EXPORTER_LISTEN_ADDRESS_PARAM_NAME = "_exporter_url_"

# 自定义监控 展示最近多少秒内的告警事件点
ALARM_TIME_RANGE = 60 * 10

# 查询任务状态API对应业务权限有效期
API_PERMISSION_EXPIRE = 60 * 60 * 24

# 原始数据保存周期(天)
RAW_DATA_INTERVAL = 30

# 日志采集下拉选取
LOG_COLLECTOR_SELECTION = {
    "field_type": [
        {"disabled": 0, "id": 1, "value": "string", "display": "string(512)"},
        {"disabled": 0, "id": 2, "value": "int", "display": "int"},
        {"disabled": 0, "id": 3, "value": "long", "display": "long"},
        {"disabled": 0, "id": 4, "value": "double", "display": "double"},
        {"disabled": 0, "id": 5, "value": "text", "display": "text"},
    ],
    "encoding": [
        {"disabled": 0, "id": 1, "value": "UTF-8", "display": "UTF-8"},
        {"disabled": 0, "id": 2, "value": "GBK", "display": "GBK"},
    ],
    "field_delimiter": [
        {"disabled": 0, "en_display": "|(pipeline)", "id": 1, "value": "|", "display": _lazy("|(管道线)")},
        {"disabled": 0, "en_display": ",(comma)", "id": 2, "value": ",", "display": _lazy(",(逗号)")},
    ],
    "condition_operator": [{"display": "=", "value": "="}],
    "timezone": biz_time_zone_offset(),
    "file_frequency": [
        {"disabled": 0, "en_display": "One log file per hour", "id": 1, "value": "3699", "display": _lazy("每小时1个文件")},
        {"disabled": 0, "en_display": "One log file per day", "id": 2, "value": "86400", "display": _lazy("每天1个文件")},
        {
            "disabled": 0,
            "en_display": "One log file per month",
            "id": 3,
            "value": "2678400",
            "display": _lazy("每月1个文件"),
        },
        {"disabled": 0, "en_display": "Single file", "id": 4, "value": "157680000", "display": _lazy("单文件")},
    ],
}


# 日志和脚本任务升级状态
class UpgradeStatus(object):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class UptimeCheckProtocol(object):
    HTTP = "HTTP"
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
