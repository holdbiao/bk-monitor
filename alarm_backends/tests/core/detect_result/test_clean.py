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


import copy

import arrow
from django.test import TestCase

from alarm_backends.constants import LATEST_POINT_WITH_ALL_KEY
from alarm_backends.core.cache import key
from alarm_backends.core.detect_result import CheckResult, clean
from alarm_backends.tests.core.detect_result.mock import *  # noqa
from alarm_backends.tests.core.detect_result.mock_settings import *  # noqa

STRATEGIES = [
    {
        "id": 1,
        "name": "test_strategy1",
        "strategy_id": 1,
        "strategy_name": "test_strategy1",
        "item_list": [
            {
                "id": 11,
                "name": "test_item11",
                "item_id": 11,
                "item_name": "test_item11",
                "algorithm_list": [
                    {"id": 111, "algorithm_id": 111, "level": "1", "dimensions_md5": "dummy_dimensions_md5_111"},
                    {"id": 112, "algorithm_id": 112, "level": "2", "dimensions_md5": "dummy_dimensions_md5_112"},
                ],
                "no_data_config": {"is_enabled": False, "continuous": 5},
            },
            {
                "id": 12,
                "name": "test_item12",
                "item_id": 12,
                "item_name": "test_item12",
                "algorithm_list": [
                    {"id": 121, "algorithm_id": 121, "level": "1", "dimensions_md5": "dummy_dimensions_md5_121"},
                    {"id": 122, "algorithm_id": 122, "level": "2", "dimensions_md5": "dummy_dimensions_md5_122"},
                ],
                "no_data_config": {"is_enabled": True, "continuous": 5},
            },
        ],
    },
    {
        "id": 2,
        "name": "test_strategy2",
        "strategy_id": 2,
        "strategy_name": "test_strategy2",
        "item_list": [
            {
                "id": 21,
                "name": "test_item21",
                "item_id": 21,
                "item_name": "test_item21",
                "algorithm_list": [
                    {"id": 211, "algorithm_id": 211, "level": "1", "dimensions_md5": "dummy_dimensions_md5_211"},
                    {"id": 212, "algorithm_id": 212, "level": "2", "dimensions_md5": "dummy_dimensions_md5_212"},
                ],
                "no_data_config": {"is_enabled": False, "continuous": 5},
            },
            {
                "id": 22,
                "name": "test_item22",
                "item_id": 22,
                "item_name": "test_item22",
                "algorithm_list": [
                    {"id": 221, "algorithm_id": 221, "level": "1", "dimensions_md5": "dummy_dimensions_md5_221"},
                    {"id": 222, "algorithm_id": 222, "level": "2", "dimensions_md5": "dummy_dimensions_md5_222"},
                ],
                "no_data_config": {"is_enabled": True, "continuous": 5},
            },
        ],
    },
]


class TestCleanResult(TestCase):
    @staticmethod
    def get_all_last_checkpoints_cache_key(strategies):
        all_last_checkpoints_cache_key = set()
        for strategy in strategies:
            for item in strategy["item_list"]:
                level_list = set()
                for index, algorithm in enumerate(item["algorithm_list"]):
                    level_list.add(algorithm["level"])
                    cr = CheckResult(
                        strategy_id=strategy["strategy_id"],
                        item_id=item["item_id"],
                        dimensions_md5=algorithm["dimensions_md5"],
                        level=algorithm["level"],
                    )
                    all_last_checkpoints_cache_key.add(cr.last_check_point_field)
                for l in level_list:
                    all_last_checkpoints_cache_key.add(
                        key.LAST_CHECKPOINTS_CACHE_KEY.get_field(
                            strategy_id=strategy["strategy_id"],
                            item_id=item["item_id"],
                            dimensions_md5=LATEST_POINT_WITH_ALL_KEY,
                            level=l,
                        )
                    )
        return all_last_checkpoints_cache_key

    def setUp(self):
        self.redis_patcher = patch(ALARM_BACKENDS_REDIS, return_value=fakeredis.FakeRedis(decode_responses=True))
        self.redis_patcher.start()
        redis_pipeline = CheckResult.pipeline()

        self.strategy_cache_patcher = patch(
            "alarm_backends.core.detect_result.clean.StrategyCacheManager.get_strategies",
            MagicMock(return_value=STRATEGIES),
        )
        self.strategy_cache_patcher.start()

        self.strategies = STRATEGIES
        self.now_timestamp = arrow.utcnow().timestamp
        self.three_hours_ago = arrow.utcnow().replace(hours=-3).timestamp
        self.two_hours_ago = arrow.utcnow().replace(hours=-2).timestamp
        check_result_data = {
            "{}|{}".format(self.three_hours_ago, "ANOMALY"): self.three_hours_ago,
            "{}|{}".format(self.now_timestamp, "ANOMALY"): self.now_timestamp,
        }
        timestamps = [self.now_timestamp, self.three_hours_ago]
        for strategy in self.strategies:
            for item in strategy["item_list"]:
                last_checkpoints = {}
                level_list = set()
                for index, algorithm in enumerate(item["algorithm_list"]):
                    level_list.add(algorithm["level"])
                    cr = CheckResult(
                        strategy_id=strategy["strategy_id"],
                        item_id=item["item_id"],
                        dimensions_md5=algorithm["dimensions_md5"],
                        level=algorithm["level"],
                    )
                    # clean old data
                    key.CHECK_RESULT_CACHE_KEY.client.zremrangebyscore(cr.check_result_cache_key, 0, float("inf"))
                    cr.add_check_result_cache(**check_result_data)
                    cr.update_key_to_dimension(dimensions={})
                    last_checkpoints[(algorithm["dimensions_md5"], algorithm["level"])] = timestamps[index]
                for l in level_list:
                    last_checkpoints[(LATEST_POINT_WITH_ALL_KEY, l)] = self.now_timestamp

                for check_point_key_tuple, point_timestamp in list(last_checkpoints.items()):
                    _dimensions_md5, level = check_point_key_tuple
                    CheckResult.update_last_checkpoint_by_dimensions_md5(
                        strategy["strategy_id"], item["item_id"], _dimensions_md5, point_timestamp, level
                    )
                CheckResult.expire_last_checkpoint_cache()

        redis_pipeline.execute()

    def tearDown(self):
        self.redis_patcher.stop()
        self.strategy_cache_patcher.stop()

    def before_assert(self):
        self.assertEqual(
            set(CheckResult.get_all_last_checkpoints_cache_key()),
            self.get_all_last_checkpoints_cache_key(self.strategies),
        )

    @patch(ALARM_BACKENDS_CLEAN_STRATEGY_CACHE_MANAGER_REFRESH, MagicMock(return_value=True))
    def test_clean_disabled_strategies__disable_strategy(self):
        new_strategies = copy.deepcopy(self.strategies)
        # disable second strategy
        new_strategies = new_strategies[0:1]
        new_all_last_checkpoints_cache_key = self.get_all_last_checkpoints_cache_key(new_strategies)

        with mock.patch(
            ALARM_BACKENDS_CLEAN_STRATEGY_CACHE_MANAGER_GET_STRATEGIES, MagicMock(return_value=new_strategies)
        ):
            clean.CleanResult.clean_disabled_strategies()
            self.assertEqual(set(CheckResult.get_all_last_checkpoints_cache_key()), new_all_last_checkpoints_cache_key)

    @patch(ALARM_BACKENDS_CLEAN_STRATEGY_CACHE_MANAGER_REFRESH, MagicMock(return_value=True))
    def test_clean_disabled_stragegies__disable_item(self):
        new_strategies = copy.deepcopy(self.strategies)
        # disable second strategy
        new_strategies = new_strategies[0:1]
        new_strategies[0]["item_list"] = new_strategies[0]["item_list"][0:1]
        new_all_last_checkpoints_cache_key = self.get_all_last_checkpoints_cache_key(new_strategies)

        with mock.patch(
            ALARM_BACKENDS_CLEAN_STRATEGY_CACHE_MANAGER_GET_STRATEGIES, MagicMock(return_value=new_strategies)
        ):
            clean.CleanResult.clean_disabled_strategies()
            self.assertEqual(set(CheckResult.get_all_last_checkpoints_cache_key()), new_all_last_checkpoints_cache_key)

    @patch(ALARM_BACKENDS_CLEAN_STRATEGY_CACHE_MANAGER_REFRESH, MagicMock(return_value=True))
    @patch(
        "alarm_backends.core.detect_result.clean.detect_result_point_required", MagicMock(return_value={"1.11.1": 1})
    )
    def test_clean_expired_detect_result(self):
        check_result_cache_key = key.CHECK_RESULT_CACHE_KEY.get_key(
            strategy_id=self.strategies[0]["strategy_id"],
            item_id=self.strategies[0]["item_list"][0]["item_id"],
            dimensions_md5=self.strategies[0]["item_list"][0]["algorithm_list"][0]["dimensions_md5"],
            level=self.strategies[0]["item_list"][0]["algorithm_list"][0]["level"],
        )
        all_members = key.CHECK_RESULT_CACHE_KEY.client.zrangebyscore(check_result_cache_key, 0, float("inf"))
        self.assertEqual(
            all_members,
            ["{}|{}".format(self.three_hours_ago, "ANOMALY"), "{}|{}".format(self.now_timestamp, "ANOMALY")],
        )

        # FakeRedis的zremrangebyrank存在问题，0, -1参数会清空所有数据
        # clean.CleanResult.clean_expired_detect_result(expired_timestamp=self.two_hours_ago)
        # all_members = key.CHECK_RESULT_CACHE_KEY.client.zrangebyscore(check_result_cache_key, 0, float("inf"))
        # self.assertEqual(all_members, ["{}|{}".format(self.now_timestamp, "ANOMALY")])
