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


import logging

import arrow

from alarm_backends.constants import LATEST_NO_DATA_CHECK_POINT, LATEST_POINT_WITH_ALL_KEY, NO_DATA_LEVEL
from alarm_backends.core.cache import key
from alarm_backends.core.cache.key import OLD_MD5_TO_DIMENSION_CACHE_KEY, MD5_TO_DIMENSION_CACHE_KEY
from alarm_backends.core.control.strategy import StrategyCacheManager
from alarm_backends.core.detect_result import CheckResult, CONST_MAX_LEN_CHECK_RESULT
from bkmonitor.models import Event

DUMMY_DIMENSIONS_MD5 = "dummy_dimensions_md5"
CLEAN_EXPIRED_ARROW_REPLACE_TIME = {"hours": -5}

logger = logging.getLogger("core.detect_result")


class CleanResult(object):
    @staticmethod
    def clean_disabled_strategies():
        redis_pipeline = CheckResult.pipeline()
        strategies = StrategyCacheManager.get_strategies()
        enabled_check_result_key_prefix_to_levels = {}
        enabled_no_data_check_result_key_prefix = []
        for strategy in strategies:
            for item in strategy["item_list"]:
                for algorithm in item["algorithm_list"]:
                    algorithm_level = algorithm["level"]
                    # 不包含 md5 和 level 的部分
                    enabled_check_result_key_prefix = (
                        key.LAST_CHECKPOINTS_CACHE_KEY.get_field(
                            strategy_id=strategy["id"],
                            item_id=item["item_id"],
                            dimensions_md5=DUMMY_DIMENSIONS_MD5,
                            level=algorithm_level,
                        )
                        .rpartition(".")[0]
                        .rpartition(".")[0]
                    )
                    enabled_check_result_key_prefix_to_levels.setdefault(enabled_check_result_key_prefix, []).append(
                        str(algorithm_level)
                    )

                    if item["no_data_config"]["is_enabled"]:
                        enabled_no_data_check_result_key_prefix.append(enabled_check_result_key_prefix)

        all_last_checkpoints_cache_key = CheckResult.get_all_last_checkpoints_cache_key()
        disabled_cleaned_last_checkpoints_cache_key = 0
        disabled_cleaned_check_result_cache_key = 0
        no_data_last_checkpoints_cache_key = 0
        for last_checkpoints_cache_key in all_last_checkpoints_cache_key:
            # prefix: 去掉 level 的部分
            prefix, _, level = last_checkpoints_cache_key.rpartition(".")
            # prefix: 去掉 md5 的部分
            prefix, _, dimensions_md5 = prefix.rpartition(".")

            # 特殊标记 md5，先不处理
            if dimensions_md5 in [LATEST_POINT_WITH_ALL_KEY, LATEST_NO_DATA_CHECK_POINT]:
                continue

            # 如果策略监控项不存在，直接删除
            if prefix not in enabled_check_result_key_prefix_to_levels:
                check_result = CheckResult(check_result_cache_key=last_checkpoints_cache_key)
                check_result.clean_last_checkpoints_cache_key()
                # 尝试做无数据维度缓存处理
                check_result.clean_no_data_last_checkpoints_cache_key()
                disabled_cleaned_last_checkpoints_cache_key += 1
                continue

            # 如果业务监控该级别不存在了，删除该 level 缓存
            if level not in enabled_check_result_key_prefix_to_levels[prefix] and level != Event.EVENT_LEVEL_WARNING:
                check_result = CheckResult(check_result_cache_key=last_checkpoints_cache_key)
                check_result.clean_check_result_cache_key()
                disabled_cleaned_check_result_cache_key += 1
                continue

            # 分别假定是业务维度和无数据告警维度处理
            if level == Event.EVENT_LEVEL_WARNING:
                cr1 = CheckResult(check_result_cache_key=last_checkpoints_cache_key, service_type="detect")
                if cr1.md5_to_dimension_key and level not in enabled_check_result_key_prefix_to_levels[prefix]:
                    cr1.clean_check_result_cache_key()
                    disabled_cleaned_check_result_cache_key += 1
                    continue

                cr2 = CheckResult(check_result_cache_key=last_checkpoints_cache_key, service_type="nodata")
                if (
                    cr2.md5_to_dimension_key
                    and last_checkpoints_cache_key not in enabled_no_data_check_result_key_prefix
                ):
                    cr2.clean_no_data_last_checkpoints_cache_key()
                    no_data_last_checkpoints_cache_key += 1
                    continue

        redis_pipeline.execute()
        logger.info(
            "clean disabled strategy last_checkpoints_cache_key total: ({})".format(
                disabled_cleaned_last_checkpoints_cache_key
            )
        )
        logger.info(
            "clean disabled strategy check_result_cache_key total: ({})".format(disabled_cleaned_check_result_cache_key)
        )
        logger.info(
            "clean disabled strategy no_data_last_checkpoints_cache_key total: ({})".format(
                no_data_last_checkpoints_cache_key
            )
        )

    @staticmethod
    def clean_expired_detect_result(expired_timestamp=None):
        # 按照策略配置的触发条件和恢复条件清理
        point_remain_map = {}
        strategies = StrategyCacheManager.get_strategies()
        for strategy in strategies:
            strategy_id = strategy["strategy_id"]
            if strategy_id not in point_remain_map:
                point_remain_map.update(detect_result_point_required(strategy))

        redis_pipeline = CheckResult.pipeline()
        if expired_timestamp is None:
            expired_timestamp = arrow.utcnow().replace(**CLEAN_EXPIRED_ARROW_REPLACE_TIME).timestamp
        all_last_checkpoints_cache_key = CheckResult.get_all_last_checkpoints_cache_key()
        expired_cleaned_total = 0
        for last_checkpoints_cache_key in all_last_checkpoints_cache_key:
            # 去掉 md5 的部分
            prefix, _, dimensions_md5 = last_checkpoints_cache_key.rpartition(".")[0].rpartition(".")
            if dimensions_md5 not in [LATEST_POINT_WITH_ALL_KEY, LATEST_NO_DATA_CHECK_POINT]:
                check_result = CheckResult(check_result_cache_key=last_checkpoints_cache_key)
                s_id = "{}.{}.{}".format(check_result.strategy_id, check_result.item_id, check_result.level)
                check_result.remove_old_check_result_cache(point_remain_map.get(s_id))
                expired_cleaned_total += 1

            if expired_cleaned_total % 10000 == 9999:
                redis_pipeline.execute()

        # 从未检测到数据的无数据维度清理
        all_no_data_checkpoint_cache_key = key.NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY.client.hkeys(
            key.NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY.get_key()
        )
        last_checkpoints_prefix = "{prefix}.detect.result".format(prefix=key.KEY_PREFIX)
        for no_data_cache_key in all_no_data_checkpoint_cache_key:
            last_checkpoints_cache_key = "{}.{}.{}".format(last_checkpoints_prefix, no_data_cache_key, NO_DATA_LEVEL)
            # 只处理从未检测到上报数据的维度集合
            if last_checkpoints_cache_key not in all_last_checkpoints_cache_key:
                all_last_checkpoints_cache_key.append(last_checkpoints_cache_key)
                check_result = CheckResult(check_result_cache_key=last_checkpoints_cache_key, service_type="nodata")
                check_result.remove_expired_check_result_cache(expired_timestamp)
                expired_cleaned_total += 1

            if expired_cleaned_total % 10000 == 9999:
                redis_pipeline.execute()

        redis_pipeline.execute()
        logger.info("clean expired detect result result_cache_key total: ({})".format(expired_cleaned_total))

        client = key.CHECK_RESULT_CACHE_KEY.client
        for last_checkpoints_cache_key in all_last_checkpoints_cache_key:
            # bkmonitorv3.ee.detect.result.2.2.0f8bae5e9a2950b67395d87b4bbec722.2
            # ->
            # prefix, strategy_id, item_id, md5, level
            _, strategy_id, _, _, _ = last_checkpoints_cache_key.rsplit(".", 4)
            check_result_key = key.SimilarStr(last_checkpoints_cache_key)
            check_result_key.strategy_id = int(strategy_id)
            if not client.exists(check_result_key):
                client.hdel(key.LAST_CHECKPOINTS_CACHE_KEY.get_key(), last_checkpoints_cache_key)

    @staticmethod
    def clean_md5_to_dimension_cache():
        # MD5_TO_DIMENSION_CACHE_KEY 用于 nodata 模块
        OLD_MD5_TO_DIMENSION_CACHE_KEY.client.delete(OLD_MD5_TO_DIMENSION_CACHE_KEY.get_key())
        strategies = StrategyCacheManager.get_strategies()
        for strategy in strategies:
            if not is_nodata_enabled(strategy):
                continue
            strategy_id = strategy["strategy_id"]
            key_pattern = MD5_TO_DIMENSION_CACHE_KEY.get_key(service_type="*", strategy_id=strategy_id, item_id="*")
            keys = MD5_TO_DIMENSION_CACHE_KEY.client.keys(key_pattern)
            if keys:
                first_key = key.SimilarStr(keys.pop(0))
                first_key.strategy_id = strategy_id
                MD5_TO_DIMENSION_CACHE_KEY.client.delete(first_key, *keys)


def is_nodata_enabled(strategy):
    """
    判断是否开启无数据告警配置
    :param strategy:
    :return:
    """
    for item in strategy["item_list"]:
        no_data_config = item.get("no_data_config", {})
        return no_data_config.get("is_enabled", False)


def detect_result_point_required(strategy):
    """
    策略需要保留多少个检测结果点
    :param strategy:
    :return:
    """
    DEFAULT_CHECK_WINDOW_SIZE = 5
    DEFAULT_TRIGGER_COUNT = 5

    detect_result_key_tpl = "{strategy_id}.{item_id}.{level}"

    point_with_key = {}

    for item in strategy["item_list"]:
        # 计算恢复窗口时间偏移量
        try:
            recovery_window_size = item["algorithm_list"][0]["recovery_config"]["check_window"]
        except Exception:
            recovery_window_size = DEFAULT_CHECK_WINDOW_SIZE

        trigger_configs = {
            algorithm_config["level"]: {"check_window_size": algorithm_config["trigger_config"]["check_window"]}
            for algorithm_config in item["algorithm_list"]
        }

        for level in trigger_configs:
            dr_key = detect_result_key_tpl.format(
                strategy_id=strategy["strategy_id"], item_id=item["item_id"], level=level
            )
            if dr_key not in point_with_key:
                try:
                    trigger_window_size = trigger_configs[level]["check_window_size"]
                except Exception:
                    trigger_window_size = DEFAULT_TRIGGER_COUNT
                point_with_key[dr_key] = max(
                    [(trigger_window_size + recovery_window_size) * 2, CONST_MAX_LEN_CHECK_RESULT]
                )
    return point_with_key
