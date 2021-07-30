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


import json
import logging

from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from alarm_backends.constants import CONST_ONE_HOUR
from alarm_backends.core.cache import key
from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.control.item import Item
from core.errors.alarm_backends import StrategyItemNotFound

logger = logging.getLogger("core.control")


class Strategy(object):
    def __init__(self, strategy_id):
        self.id = self.strategy_id = strategy_id

    @cached_property
    def config(self):
        return StrategyCacheManager.get_strategy_by_id(self.strategy_id) or {}

    @cached_property
    def is_service_target(self):
        """
        判断是否是"服务"层
        """
        return self.config.get("scenario") in ("component", "service_module", "service_process")

    @cached_property
    def is_host_target(self):
        """
        判断是否为"主机"层
        """
        return self.config.get("scenario") in ("os", "host_process")

    @cached_property
    def bk_biz_id(self):
        return self.config.get("bk_biz_id", "0")

    @cached_property
    def scenario(self):
        return self.config.get("scenario", "")

    @cached_property
    def name(self):
        return self.config.get("name")

    @cached_property
    def items(self):
        results = []
        item_list = self.config.get("item_list") or []
        for item_config in item_list:
            results.append(Item(item_config, self))
        return results

    def gen_strategy_snapshot(self):
        """
        创建当前策略配置缓存快照， 返回快照存储的key
        """
        # 基于策略更新时间，判断策略是否有变更
        client = key.STRATEGY_SNAPSHOT_KEY.client
        update_time = self.config.get("update_time")
        snapshot_key = key.STRATEGY_SNAPSHOT_KEY.get_key(strategy_id=self.id, update_time=update_time)
        client.set(snapshot_key, json.dumps(self.config), ex=CONST_ONE_HOUR)
        setattr(self, "snapshot_key", snapshot_key)
        return snapshot_key

    @classmethod
    def get_strategy_snapshot_by_key(cls, snapshot_key, strategy_id=None):
        client = key.STRATEGY_SNAPSHOT_KEY.client
        if strategy_id:
            snapshot_key = key.SimilarStr(snapshot_key)
            snapshot_key.strategy_id = strategy_id
        snapshot = client.get(snapshot_key)
        if not snapshot:
            return None
        return json.loads(snapshot)

    @classmethod
    def get_item_in_strategy(cls, strategy, item_id):
        """
        提取策略中对应item_id的监控项
        """
        # 获取产生了异常的监控项信息
        for item in strategy["item_list"]:
            if item["item_id"] == item_id:
                return item

        # 找不到对应的监控项，忽略这个异常点
        error_message = _("strategy({}), item({}) 监控项在快照数据中找不到").format(strategy["id"], item_id)
        logger.warning(error_message)
        raise StrategyItemNotFound({"strategy_id": strategy["id"], "item_id": item_id})

    @staticmethod
    def get_trigger_configs(item):
        """
        获取不同级别算法的触发配置
        :return {
            '1': {
                'check_windows_size': 5,
                'trigger_count': 3,
            }
        }
        """
        trigger_config = {}
        for algorithm_config in item["algorithm_list"]:
            trigger_config[str(algorithm_config["level"])] = {
                "check_window_size": algorithm_config["trigger_config"]["check_window"],
                "trigger_count": algorithm_config["trigger_config"]["count"],
            }
        return trigger_config

    @staticmethod
    def get_no_data_configs(item):
        """
        :summary: 获取无数据告警的触发配置
        :param item:
        :return:
        """
        return {
            "check_window_size": item["no_data_config"]["continuous"],
            "trigger_count": item["no_data_config"]["continuous"],
        }

    def __getattr__(self, item):
        if item == "snapshot_key":
            return self.gen_strategy_snapshot()
        return super(Strategy, self).__getattribute__(item)
