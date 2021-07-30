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


from django.conf import settings

from alarm_backends.constants import CONST_MINUTES, CONST_ONE_DAY, CONST_ONE_HOUR, CONST_ONE_WEEK
from alarm_backends.core.storage.redis_cluster import RedisProxy
from bkmonitor.utils.text import underscore_to_camel

TTL_NOT_SET = CONST_ONE_WEEK

prefix_tpl = "{app_code}.{platform}{env}"

# 环境缩写
platform_abbreviation = {"enterprise": "ee", "community": "ce"}


def get_cache_key_prefix():
    env = "[{}]".format(settings.ENVIRONMENT)
    if settings.ENVIRONMENT == "production":
        env = ""

    platform = platform_abbreviation.get(settings.PLATFORM, settings.PLATFORM)
    return prefix_tpl.format(app_code=settings.APP_CODE, platform=platform, env=env)


KEY_PREFIX = get_cache_key_prefix()


class RedisDataKey(object):
    """
    redis 的Key对象
    """

    key_prefix = KEY_PREFIX

    def __init__(self, key_tpl=None, ttl=None, backend=None, **extra_config):
        self._cache = None
        if not all([key_tpl, ttl, backend]):
            raise ValueError
        # key 模板
        self.key_tpl = key_tpl
        # 过期时间
        self.ttl = ttl
        # 对应cache backend
        self.backend = backend
        for k, v in list(extra_config.items()):
            setattr(self, k, v)

    @property
    def client(self):
        if self._cache is None:
            self._cache = RedisProxy(self.backend)
        return self._cache

    def get_key(self, **kwargs):
        key = self.key_tpl.format(**kwargs)
        if not key.startswith(self.key_prefix):
            key = ".".join([self.key_prefix, key])
        strategy_id = int(kwargs.get("strategy_id", 0))
        key = SimilarStr(key)
        key.strategy_id = strategy_id
        return key

    def expire(self, **key_kwargs):
        # 注意在pipeline中使用pipeline调用expire方法，不要调用该对象自身的expire方法
        self.client.expire(self.get_key(**key_kwargs), self.ttl)


class SimilarStr(str):
    _strategy_id = 0

    @property
    def strategy_id(self):
        return self._strategy_id

    @strategy_id.setter
    def strategy_id(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = 0
        self._strategy_id = value


class StringKey(RedisDataKey):
    """
    String 数据结构的Key对象
    """


class HashKey(RedisDataKey):
    """
    Hash 数据结构的Key对象
    extra_config:
        field_tpl=""
    """

    def __init__(self, key_tpl=None, ttl=None, backend=None, **extra_config):
        super(HashKey, self).__init__(key_tpl, ttl, backend, **extra_config)
        if "field_tpl" not in extra_config:
            raise ValueError("keyword argument 'field_tpl' is required")

    def get_field(self, **kwargs):
        return self.field_tpl.format(**kwargs)


class SetKey(RedisDataKey):
    """
    Set 数据结构的Key对象
    """


class ListKey(RedisDataKey):
    """
    List 数据结构的Key对象
    """


class SortedSetKey(RedisDataKey):
    """
    SortedSet 数据结构的Key对象
    """


def register_key_with_config(config):
    """
    支持的类型： hash、set、list、sorted_set
    :param config:
    :rtype: RedisDataKey
    """
    key_type = config["key_type"]
    key_cls = globals().get("{}Key".format(underscore_to_camel(key_type)))
    if not key_cls:
        raise TypeError("unsupported key type: {}".format(key_type))
    return key_cls(**config)


##################################################
#           Definition of key in redis           #
#                                                #
# Contains:                                      #
# - key_type:  hash, set, list, sorted_set, etc. #
# - key_tpl:   Key generation rule.              #
# - field_tpl: Field generation rule, if any.    #
# - ttl:       10(unit:seconds).                 #
# - backend:   "queue", "service", "log", etc.   #
# - label:     Description of the key.           #
##################################################

##################################################
# queue(db:9)[重要，不可清理] services之间交互的队列   #
##################################################
DATA_LIST_KEY = register_key_with_config(
    {
        "label": "[access]待检测数据队列",
        "key_type": "list",
        "key_tpl": "access.data.{strategy_id}.{item_id}",
        "ttl": 10 * CONST_MINUTES,
        "backend": "queue",
    }
)


DATA_SIGNAL_KEY = register_key_with_config(
    {
        "label": "[access]待检测数据信号队列",
        "key_type": "list",
        "key_tpl": "access.data.signal",
        "ttl": 30 * CONST_MINUTES,
        "backend": "queue",
    }
)


NO_DATA_LIST_KEY = register_key_with_config(
    {
        "label": "[access]无数据告警待检测队列",
        "key_type": "list",
        "key_tpl": "access.nodata.{strategy_id}.{item_id}",
        "ttl": 10 * CONST_MINUTES,
        "backend": "queue",
    }
)


HISTORY_DATA_KEY = register_key_with_config(
    {
        "label": "[detect]待检测数据对应历史数据",
        "key_type": "hash",
        "key_tpl": "detect.history.data.{strategy_id}.{item_id}.{timestamp}",
        "field_tpl": "{dimensions_md5}",
        "ttl": 30 * CONST_MINUTES,
        "backend": "service",
    }
)


ANOMALY_LIST_KEY = register_key_with_config(
    {
        "label": "[detect]检测结果详情队列",
        "key_type": "list",
        "key_tpl": "detect.anomaly.list.{strategy_id}.{item_id}",
        "ttl": 30 * CONST_MINUTES,
        "backend": "queue",
    }
)


ANOMALY_SIGNAL_KEY = register_key_with_config(
    {
        "label": "[detect]异常信号队列",
        "key_type": "list",
        "key_tpl": "detect.anomaly.signal",
        "ttl": 30 * CONST_MINUTES,
        "backend": "queue",
    }
)


TRIGGER_EVENT_LIST_KEY = register_key_with_config(
    {
        "label": "[trigger]异常触发信号队列",
        "key_type": "list",
        "key_tpl": "trigger.event",
        "ttl": 30 * CONST_MINUTES,
        "backend": "queue",
    }
)

RECOVERY_CHECK_EVENT_ID_KEY = register_key_with_config(
    {
        "label": "[recovery]等待恢复检测的事件ID集合",
        "key_type": "set",
        "key_tpl": "recovery.event_id",
        "ttl": 30 * CONST_MINUTES,
        "backend": "queue",
    }
)

ACTION_LIST_KEY = register_key_with_config(
    {
        "label": "[action]待执行队列",
        "key_type": "list",
        "key_tpl": "action.{action_type}",
        "ttl": CONST_ONE_WEEK,
        "backend": "queue",
    }
)


#####################################################
# service(db:10) [重要，不可清理] service自身的数据      #
#####################################################
STRATEGY_SNAPSHOT_KEY = register_key_with_config(
    {
        "label": "[detect]异常检测使用的策略快照",
        "key_type": "string",
        "key_tpl": "cache.strategy.snapshot.{strategy_id}.{update_time}",
        "ttl": CONST_ONE_HOUR,
        "backend": "service",
    }
)

STRATEGY_CHECKPOINT_KEY = register_key_with_config(
    {
        "label": "[access]策略数据拉取到的最后一条数据的时间",
        "key_type": "string",
        "key_tpl": "checkpoint.strategy_group_{strategy_group_key}",
        "ttl": CONST_ONE_HOUR,
        "backend": "service",
    }
)

ACCESS_DUPLICATE_KEY = register_key_with_config(
    {
        "label": "[access]数据拉取去重",
        "key_type": "set",
        "key_tpl": "access.data.duplicate.strategy_group_{strategy_group_key}.{dt_event_time}",
        "ttl": 10 * CONST_MINUTES,
        "backend": "service",
    }
)

# 每个group，在每10分钟内允许占用的worker时间上限： 50秒。当key不存在时，新的token周期或者新的策略，初始化token。
# 每次占用资源后，对token进行削减。token不足时，不能再拉取数据了，必须等到key过期后，重新发token。
STRATEGY_TOKEN_BUCKET_KEY = register_key_with_config(
    {
        "label": "[access]数据拉取token桶",
        "key_type": "string",
        "key_tpl": "access.data.token.strategy_group_{strategy_group_key}",
        "ttl": 10 * CONST_MINUTES,
        "backend": "service",
    }
)

QOS_CONTROL_KEY = register_key_with_config(
    {
        "label": "[access]QOS控制开关",
        "key_type": "hash",
        "key_tpl": "access.event.qos.control",
        "ttl": 30 * CONST_MINUTES,
        "backend": "service",
        "field_tpl": "{dimensions_md5}",
    }
)

OLD_MD5_TO_DIMENSION_CACHE_KEY = register_key_with_config(
    {
        "label": "[detect]维度信息缓存(type:Hash)(key: dimensions_md5, value: 维度字典 json(dict))",
        "key_type": "hash",
        "key_tpl": "dimensions.cache.key",
        "ttl": TTL_NOT_SET,
        "backend": "service",
        "field_tpl": ".{service_type}.{strategy_id}.{item_id}.{dimensions_md5}",
    }
)


MD5_TO_DIMENSION_CACHE_KEY = register_key_with_config(
    {
        "label": "[detect]维度信息缓存(type:Hash)(key: dimensions_md5, value: 维度字典 json(dict))",
        "key_type": "hash",
        "key_tpl": "dimensions.cache.key.{service_type}.{strategy_id}.{item_id}",
        "ttl": CONST_ONE_DAY,
        "backend": "service",
        "field_tpl": "{dimensions_md5}",
    }
)


LAST_CHECKPOINTS_CACHE_KEY = register_key_with_config(
    {
        "label": "[detect|nodata]最后检测时间点(type:Hash)(key: (strategy_id, item_id, dimensions_md5), "
        "value: 最后检测点时间戳(int))",
        "key_type": "hash",
        "key_tpl": "detect.last.checkpoint.cache.key",
        "ttl": TTL_NOT_SET,
        "backend": "service",
        # 这里的field_tpl需要保持和CHECK_RESULT_CACHE_KEY的key_tpl一致
        "field_tpl": "{prefix}.detect.result.{{strategy_id}}.{{item_id}}."
        "{{dimensions_md5}}.{{level}}".format(prefix=KEY_PREFIX),
    }
)


NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY = register_key_with_config(
    {
        "label": "[nodata]最后检测异常点(type:Hash)(key: (strategy_id, item_id, dimensions_md5), value: 最后异常点时间戳(int))",
        "key_type": "hash",
        "key_tpl": "nodata.last.anomaly.checkpoint.cache.key",
        "ttl": TTL_NOT_SET,
        "backend": "service",
        "field_tpl": "{strategy_id}.{item_id}.{dimensions_md5}",
    }
)


CHECK_RESULT_CACHE_KEY = register_key_with_config(
    {
        "label": "[detect]检测结果缓存: (type:SortedSet)"
        "(score: 数据时间戳(int), name：正常->'timestamp|value' 异常: 'timestamp|{ANOMALY_LABEL}')",
        "key_type": "sorted_set",
        # 这里的key_tpl修改后，需要同步修改LAST_CHECKPOINTS_CACHE_KEY的field_tpl
        "key_tpl": "{prefix}.detect.result.{{strategy_id}}.{{item_id}}."
        "{{dimensions_md5}}.{{level}}".format(prefix=KEY_PREFIX),
        "ttl": CONST_ONE_HOUR,
        "backend": "service",
    }
)

EVENT_ID_CACHE_KEY = register_key_with_config(
    {
        "label": "[event]当前策略与维度正在发生的事件ID",
        "key_type": "string",
        "key_tpl": "event.event_id.{strategy_id}.{item_id}.{dimensions_md5}",
        "ttl": TTL_NOT_SET,
        "backend": "service",
    }
)

EVENT_EXTEND_ID_CACHE_KEY = register_key_with_config(
    {
        "label": "[event]需要更新附加信息的id",
        "key_type": "set",
        "key_tpl": "event.event_id.extend_info",
        "ttl": TTL_NOT_SET,
        "backend": "service",
    }
)

EVENT_EXTEND_CACHE_KEY = register_key_with_config(
    {
        "label": "[event]异常持续时间和异常点数量",
        "key_type": "string",
        "key_tpl": "event.event_id.extend_info.{id}",
        "ttl": 30 * CONST_MINUTES,
        "backend": "service",
    }
)

NOTICE_DIMENSION_COLLECT_KEY = register_key_with_config(
    {
        "label": "[notice]单维度汇总待发送池",
        "key_type": "hash",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}."
        "{bk_biz_id}.{level}.{strategy_id}.{dimension_hash}",
        "ttl": CONST_ONE_WEEK,
        "backend": "service",
        "field_tpl": "{receiver}",
    }
)

NOTICE_DIMENSION_COLLECT_KEY_LOCK = register_key_with_config(
    {
        "label": "[notice]单维度汇总发送锁",
        "key_type": "string",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}."
        "{bk_biz_id}.{level}.{strategy_id}.{dimension_hash}.lock",
        "ttl": CONST_MINUTES * 2,
        "backend": "service",
    }
)

NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK = register_key_with_config(
    {
        "label": "[notice]单维度汇总发送锁",
        "key_type": "string",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}."
        "{bk_biz_id}.{level}.{strategy_id}.{dimension_hash}.process.lock",
        "ttl": 4,
        "backend": "service",
    }
)

NOTICE_BIZ_COLLECT_KEY = register_key_with_config(
    {
        "label": "[notice]业务汇总汇总待发送池",
        "key_type": "list",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}.{bk_biz_id}.{level}.{receiver}",
        "ttl": CONST_ONE_WEEK,
        "backend": "service",
        "field_tpl": "{receiver}",
    }
)

NOTICE_BIZ_COLLECT_KEY_LOCK = register_key_with_config(
    {
        "label": "[notice]业务汇总汇总发送锁",
        "key_type": "string",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}.{bk_biz_id}.{level}.{receiver}.lock",
        "ttl": CONST_MINUTES * 2,
        "backend": "service",
    }
)

NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK = register_key_with_config(
    {
        "label": "[notice]业务汇总汇总发送锁",
        "key_type": "string",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}.{bk_biz_id}.{level}.process.lock",
        "ttl": 4,
        "backend": "service",
    }
)

NOTICE_BIZ_DIMENSIONS_KEY = register_key_with_config(
    {
        "label": "[notice]业务汇总维度记录",
        "key_type": "sorted_set",
        "key_tpl": "action.notice.collect.{notice_type}.{notice_way}.{bk_biz_id}.{level}.{receiver}.dimensions",
        "ttl": 2 * CONST_MINUTES,
        "backend": "service",
    }
)

NOTICE_VOICE_COLLECT_KEY = register_key_with_config(
    {
        "label": "[notice]电话单维度通知汇总",
        "key_type": "string",
        "key_tpl": "action.notice.phone_collect.{receiver}",
        "ttl": 2 * CONST_MINUTES,
        "backend": "service",
    }
)

NOTICE_SHIELD_KEY_LOCK = register_key_with_config(
    {
        "label": "[notice]屏蔽通知锁",
        "key_type": "string",
        "key_tpl": "action.notice.shield.{shield_id}",
        "ttl": CONST_ONE_DAY,
        "backend": "service",
    }
)

SERVICE_LOCK_ACCESS = register_key_with_config(
    {
        "label": "access.lock.strategy_{strategy_group_key}",
        "key_type": "string",
        "key_tpl": "access.lock.{strategy_group_key}",
        "ttl": 3 * CONST_MINUTES,
        "backend": "service",
    }
)


SERVICE_LOCK_DETECT = register_key_with_config(
    {
        "label": "detect.lock.strategy_{strategy_id}",
        "key_type": "string",
        "key_tpl": "detect.lock.{strategy_id}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)

SERVICE_LOCK_NODATA = register_key_with_config(
    {
        "label": "nodata.lock.strategy_{strategy_id}",
        "key_type": "string",
        "key_tpl": "detect.lock.{strategy_id}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


SERVICE_LOCK_TRIGGER = register_key_with_config(
    {
        "label": "[trigger]进程处理锁",
        "key_type": "string",
        "key_tpl": "trigger.lock.{strategy_id}_{item_id}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


SERVICE_LOCK_EVENT = register_key_with_config(
    {
        "label": "[event]进程处理锁",
        "key_type": "string",
        "key_tpl": "event.lock.{strategy_id}_{dimensions_md5}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


SERVICE_LOCK_RECOVERY = register_key_with_config(
    {
        "label": "[recovery]进程处理锁",
        "key_type": "string",
        "key_tpl": "recovery.lock.{strategy_id}_{dimensions_md5}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


SERVICE_LOCK_PULL_TRIGGER = register_key_with_config(
    {
        "label": "[event]trigger 结果拉取",
        "key_type": "string",
        "key_tpl": "trigger.event.pull",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


ACCESS_END_TIME_KEY = register_key_with_config(
    {
        "label": "[access]数据拉取的结束时间",
        "key_type": "string",
        "key_tpl": "access.data.last_end_time.group_key_{group_key}",
        "ttl": 5 * CONST_MINUTES,
        "backend": "service",
    }
)

ACCESS_EVENT_LOCKS = register_key_with_config(
    {
        "label": "[access]自定义上报事件不同Data ID的拉取锁",
        "key_type": "string",
        "key_tpl": "access.event.custom_event.lock_{data_id}",
        "ttl": CONST_MINUTES,
        "backend": "service",
    }
)


MAIL_REPORT_GROUP_CACHE_KEY = register_key_with_config(
    {
        "label": "[mail_report]订阅报表组别信息保存",
        "key_type": "hash",
        "key_tpl": "service.mail_report.group",
        "ttl": CONST_ONE_WEEK,
        "backend": "service",
        "field_tpl": "",
    }
)
