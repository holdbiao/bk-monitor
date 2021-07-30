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


import hashlib
import json
import logging
import time
from abc import abstractmethod, ABC
from typing import List, Dict
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.functional import cached_property

from alarm_backends.core.cache.key import (
    NOTICE_DIMENSION_COLLECT_KEY,
    NOTICE_BIZ_COLLECT_KEY,
    NOTICE_BIZ_DIMENSIONS_KEY,
    NOTICE_VOICE_COLLECT_KEY,
    NOTICE_BIZ_COLLECT_KEY_LOCK,
    NOTICE_DIMENSION_COLLECT_KEY_LOCK,
    NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK,
    NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK,
)
from alarm_backends.service.action.tasks import (
    send_dimension_collect_notice,
    send_biz_collect_notice,
    send_collect_notice,
)
from bkmonitor.models import EventAction, AlertCollect, Alert

from .utils import get_target_dimension_keys

logger = logging.getLogger("action")


class BaseCollector(ABC):
    """
    基础通知汇总器
    """

    def __init__(self, event_action, notice_way):
        self.event_action = event_action
        self.event = event_action.event
        self.notice_way = notice_way
        self.notice_type = event_action.operate.split("_")[0].lower()

    @cached_property
    def labels(self):
        return {
            "notice_type": self.event_action.operate.split("_")[0].lower(),
            "notice_way": self.notice_way,
            "bk_biz_id": self.event.bk_biz_id,
            "level": self.event.level,
            "data_source": self.event.origin_config["item_list"][0]["data_source_label"],
            "dimension_hash": self.dimension_hash,
            "strategy_id": self.event.strategy_id,
        }

    @cached_property
    def dimension_hash(self):
        """
        维度hash
        """
        dimensions = self.event.origin_alarm["data"]["dimensions"]
        agg_dimensions = self.event.origin_config["item_list"][0]["rt_query_config"].get("agg_dimension", [])
        target_dimension_keys = get_target_dimension_keys(agg_dimensions, self.event.origin_config["scenario"])

        dimensions = {
            key: value
            for key, value in list(dimensions.items())
            if key in agg_dimensions and key not in target_dimension_keys
        }

        dimensions_str = json.dumps(dimensions, sort_keys=True)
        return hashlib.md5(dimensions_str.encode("utf-8")).hexdigest()

    def lock(self):
        pass

    def unlock(self):
        pass

    @abstractmethod
    def collect(self, receivers: List[str]) -> List[str]:
        """
        执行汇总
        :param receivers: 接收人员
        :return: 未被当前层级汇总的接收人员
        """
        ...


class VoiceCollector(BaseCollector):
    """
    电话汇总
    """

    def collect(self, receivers: List[str]) -> List[str]:
        client = NOTICE_VOICE_COLLECT_KEY.client
        labels = json.loads(json.dumps(self.labels))

        for receiver in receivers:
            labels["receiver"] = receiver
            collect_key = NOTICE_VOICE_COLLECT_KEY.get_key(**labels)

            if client.set(collect_key, self.event_action.id, ex=NOTICE_VOICE_COLLECT_KEY.ttl, nx=True):
                send_collect_notice([receiver], [self.event_action.id], self.labels, "DIMENSION")
            else:
                logger.info(
                    "event_action({}) voice alarm skip, voice alarm by event_action({}) {} second age".format(
                        self.event_action.id,
                        client.get(collect_key),
                        NOTICE_VOICE_COLLECT_KEY.ttl,
                    )
                )
                self.event_action.status = EventAction.Status.FAILED
                self.event_action.save()

                # 创建通知汇总记录
                alert_collect = AlertCollect.objects.create(
                    bk_biz_id=self.event.bk_biz_id,
                    collect_key=collect_key,
                    message=_("汇总发送"),
                    collect_type="DIMENSION",
                    extend_info={"message": ""},
                )
                Alert.objects.create(
                    method="voice",
                    username=receiver,
                    role="",
                    status="FAILED",
                    action_id=self.event_action.id,
                    event_id=self.event.event_id,
                    alert_collect_id=alert_collect.id,
                    message=_("相同通知人在两分钟内只能接收一次电话告警"),
                )

        return []


class DimensionCollector(BaseCollector):
    """
    同策略同维度多目标汇总
    相同策略的除监控目标外的维度相同的通知将会被汇总
    """

    def lock(self):
        client = NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK.client
        key = NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK.get_key(**self.labels)
        ttl = NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK.ttl

        retry_times = 0
        while not client.set(key, 1, ex=ttl, nx=True):
            time.sleep(0.1)
            retry_times += 1

            if retry_times > 20:
                break

    def unlock(self):
        client = NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK.client
        key = NOTICE_DIMENSION_COLLECT_KEY_PROCESS_LOCK.get_key(**self.labels)

        client.delete(key)

    def collect(self, receivers: List[str]) -> List[str]:
        client = NOTICE_DIMENSION_COLLECT_KEY.client
        collect_key = NOTICE_DIMENSION_COLLECT_KEY.get_key(**self.labels)
        collect_key_lock = NOTICE_DIMENSION_COLLECT_KEY_LOCK.get_key(**self.labels)

        # 查询数据
        data: Dict[bytes, bytes] = client.hgetall(collect_key)
        data: Dict[str, str] = {
            (key.decode() if isinstance(key, bytes) else key): (value.decode() if isinstance(value, bytes) else value)
            for key, value in data.items()
        }

        # 插入event_action
        mapping = {}
        for receiver in receivers:
            event_actions = data.get(receiver, "")
            if event_actions:
                event_actions = set(event_actions.split(","))
            else:
                event_actions = set()

            event_actions.add(str(self.event_action.id))
            mapping[receiver] = ",".join(sorted(event_actions))

        pipeline = client.pipeline()
        client.hmset(collect_key, mapping)
        client.expire(collect_key, NOTICE_DIMENSION_COLLECT_KEY.ttl)
        pipeline.execute()

        # 判断汇总状态
        if not data:
            send_dimension_collect_notice.apply_async((self.labels, "short"), countdown=1)
            logger.info(
                f"event_action({self.event_action.id}) start short dimension collect task for {self.notice_way}"
            )
        elif client.set(collect_key_lock, 1, nx=True, ex=NOTICE_DIMENSION_COLLECT_KEY_LOCK.ttl):
            send_dimension_collect_notice.apply_async((self.labels, "long"), countdown=60)
            logger.info(f"event_action({self.event_action.id}) start long dimension collect task for {self.notice_way}")
        else:
            logger.info(f"event_action({self.event_action.id}) collected by {collect_key} for {self.notice_way}")

        return []


class BizCollector(BaseCollector):
    """
    业务汇总器
    相同业务、数据来源、告警级别的通知将会被汇总
    """

    def lock(self):
        client = NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK.client
        key = NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK.get_key(**self.labels)
        ttl = NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK.ttl

        retry_times = 0
        while not client.set(key, 1, ex=ttl, nx=True):
            time.sleep(0.1)
            retry_times += 1

            if retry_times > 20:
                break

    def unlock(self):
        client = NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK.client
        key = NOTICE_BIZ_COLLECT_KEY_PROCESS_LOCK.get_key(**self.labels)

        client.delete(key)

    def collect(self, receivers: List[str]) -> List[str]:
        client = NOTICE_BIZ_COLLECT_KEY.client
        labels = json.loads(json.dumps(self.labels))

        no_collected_receivers = []
        for receiver in receivers:
            timestamp = time.time()
            labels["receiver"] = receiver
            collect_key = NOTICE_BIZ_COLLECT_KEY.get_key(**labels)
            collect_key_lock = NOTICE_BIZ_COLLECT_KEY_LOCK.get_key(**labels)
            dimension_key = NOTICE_BIZ_DIMENSIONS_KEY.get_key(**labels)

            # 判断是否处于汇总状态
            if client.get(collect_key_lock):
                client.lpush(collect_key, self.event_action.id)
                client.expire(collect_key, NOTICE_BIZ_COLLECT_KEY.ttl)
                logger.info(f"event_action({self.event_action.id}) collect by {collect_key}")
                continue

            # 记录维度
            client.zadd(dimension_key, f"{self.event.strategy_id}.{self.dimension_hash}", f"{timestamp}")
            client.expire(dimension_key, NOTICE_BIZ_DIMENSIONS_KEY.ttl)

            # 获取检测窗口内的告警维度
            collect_dimensions = client.zrangebyscore(
                dimension_key, f"{timestamp - settings.MULTI_STRATEGY_COLLECT_WINDOW}", "+inf"
            )
            # 如果告警维度数量大于阈值，则触发业务汇总
            if len(collect_dimensions) >= settings.MULTI_STRATEGY_COLLECT_THRESHOLD:
                if client.set(collect_key_lock, 1, nx=True, ex=NOTICE_BIZ_COLLECT_KEY_LOCK.ttl):
                    # 查询被汇总的维度的待通知的event_action_id
                    pipeline = client.pipeline()
                    for collect_dimension in collect_dimensions:
                        labels["strategy_id"], labels["dimension_hash"] = collect_dimension.split(".")
                        dimension_collect_key = NOTICE_DIMENSION_COLLECT_KEY.get_key(**labels)

                        pipeline.hget(dimension_collect_key, receiver)

                    result: List[str] = pipeline.execute()
                    event_actions = set()
                    for event_actions_str in result:
                        if not event_actions_str:
                            continue

                        event_actions.update(event_actions_str.split(","))

                    # 重置告警维度统计
                    client.delete(dimension_key)

                    event_actions.add(str(self.event_action.id))
                    client.lpush(collect_key, *event_actions)

                    send_biz_collect_notice.apply_async((labels,), countdown=60)
                    logger.info(f"event_action({self.event_action.id}) start biz collect task for {self.notice_way}")
                else:
                    client.lpush(collect_key, self.event_action.id)
                    logger.info(f"event_action({self.event_action.id}) collect by {collect_key} for {self.notice_way}")

                client.expire(collect_key, NOTICE_BIZ_COLLECT_KEY.ttl)
            else:
                no_collected_receivers.append(receiver)

        return no_collected_receivers
