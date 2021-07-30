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


from django.test import TestCase

from alarm_backends.constants import NO_DATA_LEVEL, NO_DATA_TAG_DIMENSION
from alarm_backends.core.cache import key
from alarm_backends.core.control.mixins.nodata import CheckMixin
from alarm_backends.service.detect import DataPoint
from bkmonitor.utils.common_utils import count_md5

RECORDS = [
    {
        "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896740",
        "values": {"idle": 0.8, "time": 1583896740},
        "dimensions": {"bk_target_cloud_id": "0", "bk_target_ip": "127.0.0.1", "bk_topo_node": ["set|3", "module|21"]},
        "value": 0.8,
        "time": 1583896740,
    },
    {
        "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896740",
        "values": {"idle": 0.8, "time": 1583896740},
        "dimensions": {"bk_target_cloud_id": "0", "bk_target_ip": "127.0.0.2", "bk_topo_node": ["set|3", "module|21"]},
        "value": 0.8,
        "time": 1583896740,
    },
]


class TestChecker(TestCase):
    def setUp(self):
        class Strategy(object):
            id = 100

        class Item(CheckMixin):
            id = 1000
            strategy = Strategy()

        self.item_cls = Item
        self.item = self.item_cls()

    def test_process_dimensions__invalid_data(self):
        records = [
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896800",
                "values": {"idle": 0.8, "time": 1583896800},
                "dimensions": {
                    "bk_target_cloud_id": "0",
                    "bk_target_ip": "127.0.0.1",
                    "bk_topo_node": ["set|3", "module|21"],
                },
                "value": 0.8,
                "time": 1583896800,
            },
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896800",
                "values": {"idle": 0.8, "time": 1583896800},
                "dimensions": {
                    "bk_target_ip": "127.0.0.2",
                },
                "value": 0.8,
                "time": 1583896800,
            },
        ]
        no_data_dimensions = ["bk_target_ip", "bk_target_cloud_id"]
        data_points = [DataPoint(record, self.item) for record in records]
        data_dimensions = self.item._process_dimensions(no_data_dimensions, data_points)["data_dimensions"]
        assert_dimensions = {"bk_target_cloud_id": "0", "bk_target_ip": "127.0.0.1", NO_DATA_TAG_DIMENSION: True}
        self.assertEqual(data_dimensions, [assert_dimensions])

    def test_process_dimensions__dimensions_md5_timestamp(self):
        records = [
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896740",
                "values": {"idle": 0.8, "time": 1583896740},
                "dimensions": {
                    "bk_target_cloud_id": "0",
                    "bk_target_ip": "127.0.0.1",
                    "bk_topo_node": ["set|3", "module|21"],
                },
                "value": 0.8,
                "time": 1583896740,
            },
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896800",
                "values": {"idle": 0.8, "time": 1583896800},
                "dimensions": {
                    "bk_target_cloud_id": "0",
                    "bk_target_ip": "127.0.0.1",
                    "bk_topo_node": ["set|3", "module|21"],
                },
                "value": 0.8,
                "time": 1583896800,
            },
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896800",
                "values": {"idle": 0.8, "time": 1583896800},
                "dimensions": {
                    "bk_target_cloud_id": "0",
                    "bk_target_ip": "127.0.0.2",
                    "bk_topo_node": ["set|3", "module|21"],
                },
                "value": 0.8,
                "time": 1583896800,
            },
            {
                "record_id": "06c3c0cf76fddfa01db5f300ddc5ddac.1583896860",
                "values": {"idle": 0.8, "time": 1583896860},
                "dimensions": {
                    "bk_target_cloud_id": "0",
                    "bk_target_ip": "127.0.0.2",
                    "bk_topo_node": ["set|3", "module|21"],
                },
                "value": 0.8,
                "time": 1583896860,
            },
        ]
        no_data_dimensions = ["bk_target_ip", "bk_target_cloud_id"]
        data_points = [DataPoint(record, self.item) for record in records]
        result = self.item._process_dimensions(no_data_dimensions, data_points)
        data_dimensions = result["data_dimensions"]
        dimensions_md5_timestamp = result["dimensions_md5_timestamp"]
        data_dimensions_mds = result["data_dimensions_mds"]
        assert_dimensions1 = {"bk_target_cloud_id": "0", "bk_target_ip": "127.0.0.1", NO_DATA_TAG_DIMENSION: True}
        dimension1_md5 = count_md5(assert_dimensions1)
        assert_dimensions2 = {"bk_target_cloud_id": "0", "bk_target_ip": "127.0.0.2", NO_DATA_TAG_DIMENSION: True}
        dimension2_md5 = count_md5(assert_dimensions2)
        self.assertEqual([assert_dimensions1, assert_dimensions2], data_dimensions)
        self.assertEqual(dimensions_md5_timestamp, {dimension1_md5: 1583896800, dimension2_md5: 1583896860})
        self.assertEqual([dimension1_md5, dimension2_md5], data_dimensions_mds)

    def test_produce_anomaly_id(self):
        self.assertEqual(
            self.item._produce_anomaly_id(check_timestamp=10000, dimensions_md5="dimensions_md5"),
            "dimensions_md5.10000.100.1000.2",
        )

    def test_count_anomaly_period(self):
        check_timestamp = 10000
        dimensions_md5 = "test_dimensions_md5"
        setattr(self.item, "rt_query_config", {"agg_interval": 100})
        # 测试取不到无数据异常监测点的情况
        self.assertEqual(self.item._count_anomaly_period(check_timestamp, dimensions_md5), 1)

        check_timestamp = 20000
        # 测试上一次取不到无数据异常监测点时成功设置了检测时间点，这次能取到无数据异常监测点
        self.assertEqual(self.item._count_anomaly_period(check_timestamp, dimensions_md5), 101)

    def test_count_no_data_period(self):
        check_timestamp = 10000
        dimensions_md5 = "test_dimensions_md5"
        setattr(self.item, "rt_query_config", {"agg_interval": 100})
        self.assertEqual(self.item._count_no_data_period(check_timestamp, dimensions_md5), 0)

        key.LAST_CHECKPOINTS_CACHE_KEY.client.hset(
            key.LAST_CHECKPOINTS_CACHE_KEY.get_key(),
            key.LAST_CHECKPOINTS_CACHE_KEY.get_field(
                strategy_id=self.item.strategy.id,
                item_id=self.item.id,
                dimensions_md5=dimensions_md5,
                level=NO_DATA_LEVEL,
            ),
            9000,
        )
        self.assertEqual(self.item._count_no_data_period(check_timestamp, dimensions_md5), 10)
