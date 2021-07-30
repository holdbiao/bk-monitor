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

from django.conf import settings

# META配置的Consul路径
CONSUL_PATH = "{}_{}_{}/{}".format(settings.APP_CODE, settings.PLATFORM, settings.ENVIRONMENT, "metadata")
# consul data_id 路径模板
CONSUL_DATA_ID_PATH_FORMAT = "{consul_path}/v1/{{transfer_cluster_id}}/data_id/{{data_id}}".format(
    consul_path=CONSUL_PATH
)

# 配置CRONTAB任务定时任务锁的路径
CONSUL_CRON_LOCK_PATH = "%s/cron_lock" % CONSUL_PATH
# 配置CONSUL定时更新的间隔时间, 单位秒
CONSUL_UPDATE_GAP = 60

# 获取各个Data ID
config_settings = "conf.platform.%s" % settings.PLATFORM
_platform_module = __import__(config_settings, globals(), locals(), ["config_settings"])

for config in dir(_platform_module):

    if config.endswith("_DATAID"):
        locals()[config] = getattr(_platform_module, config)

# GSE 信息同步的ZK配置信息
try:
    ZK_GSE_HOST_INFO = "{}:{}".format(settings.ZK_HOST, settings.ZK_PORT)
    ZK_GSE_HOST_INFO_LIST = getattr(settings, "ZK_GSE_HOST_INFO_LIST", [ZK_GSE_HOST_INFO])

except AttributeError:
    # 如果是SaaS状态下，没有这个配置，符合预期
    if settings.ROLE == "web":
        ZK_GSE_HOST_INFO = ""
        ZK_GSE_HOST_INFO_LIST = []

# GSE同步信息的path路径信息
ZK_GSE_DATA_ID_INFO_PREFIX = "/gse/config/etc/dataserver/data/"
# 监控ID区间为 [500, 600)
ZK_GSE_DATA_CLUSTER_ID = 500
ZK_GSE_DATA_CLUSTER_PATH = "/gse/config/etc/dataserver/storage/all/0_%s" % ZK_GSE_DATA_CLUSTER_ID

# 调用GSE的'接收端配置接口'以及'路由接口'时使用
DEFAULT_GSE_API_PLAT_NAME = "bkmonitor"  # GSE分配给监控的平台名称，不随APP_CODE变更，请不要修改

# kafka的topic前缀
# 与gse对接的kafka topic，由于会存在data_id隔离，因此前缀一致可以接受
# 保持一致，是为了使得3.1和3.2可以并存同样的topic，降低基础性能上报占用kafka空间
KAFKA_TOPIC_PREFIX = "0bkmonitor_"
# 自行存储的topic需要区别，主要是因为topic拼接与table_id相关
# 3.1与3.2环境可能存在table_id冲突，因此需要增加app_code隔离
KAFKA_TOPIC_PREFIX_STORAGE = "0{}_storage_".format(settings.APP_CODE)

# Redis的key前缀
# 配置理由，同KAFKA_TOPIC_PREFIX_STORAGE
REDIS_KEY_PREFIX = settings.APP_CODE

# GSE DATA_ID最大值和最小值的判断
MIN_DATA_ID = 1500000  # 3.2版本将该值增大20w，防止与3.1版本冲突
MAX_DATA_ID = 2097151


def is_built_in_data_id(bk_data_id):
    return 1000 <= bk_data_id <= 1020 or 1100000 <= bk_data_id <= 1199999


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
    # CMDB拆分字段
    "bk_cmdb_level_name",
    "bk_cmdb_level_id",
]

# 结果表保留字模糊匹配列表
RT_RESERVED_WORD_FUZZY = [
    "DELETE",
    "DROP",
    "GRANT",
    "REVOKE",
]

# CMDB层级拆分的公共配置项内容
# 源结果表输出的数据源名称
RT_CMDB_LEVEL_DATA_SOURCE_NAME = "{}_cmdb_level_split"
# CMDB层级拆分的ETL配置名
RT_CMDB_LEVEL_ETL_CONFIG = "bk_cmdb_level_split"
# CMDB层级差费的RT分配名
RT_CMDB_LEVEL_RT_NAME = "{}_cmdb_level"

# 获取需要增加事务的DB链接名
DATABASE_CONNECTION_NAME = getattr(settings, "METADATA_DEFAULT_DATABASE_NAME", "monitor_api")

# ES存储默认版本
ES_CLUSTER_VERSION_DEFAULT = 7

ES_SHARDS_CONFIG = os.environ.get("ES_SHARDS_NUMBER", 4)
ES_REPLICAS_CONFIG = os.environ.get("ES_REPLICAS_CONFIG", 1)
