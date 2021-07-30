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


import mock
from django.test import TestCase

from alarm_backends.service.event.generator.translator import TopoNodeTranslator, TranslationField
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from api.cmdb.define import TopoNode
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestTopoTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            TopoNodeTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

        self.assertFalse(
            TopoNodeTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_DATA,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="2_mysql_base",
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.topo.TopoManager")
    def test_translate_nodes(self, TopoManager):
        TopoManager.multi_get.return_value = [
            TopoNode(
                bk_inst_id=2,
                bk_inst_name="蓝鲸",
                bk_obj_id="biz",
                bk_obj_name="业务",
            ),
            None,
            TopoNode(
                bk_inst_id=3,
                bk_inst_name="作业平台",
                bk_obj_id="set",
                bk_obj_name="集群",
            ),
            None,
        ]
        translator = TopoNodeTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_topo_node": TranslationField(
                    "bk_topo_node",
                    [
                        "biz|2",
                        "biz|3",
                        "set|3",
                        "module|4",
                    ],
                ),
            }
        )

        self.assertListEqual(
            result["bk_topo_node"].display_value,
            [
                {
                    "bk_obj_name": "业务",
                    "bk_inst_name": "蓝鲸",
                },
                {
                    "bk_obj_name": "biz",
                    "bk_inst_name": "3",
                },
                {
                    "bk_obj_name": "集群",
                    "bk_inst_name": "作业平台",
                },
                {
                    "bk_obj_name": "module",
                    "bk_inst_name": "4",
                },
            ],
        )

        self.assertEqual(result["xxx"].display_value, "yyy")

    @mock.patch("alarm_backends.service.event.generator.translator.topo.TopoManager")
    def test_translate_inst(self, TopoManager):
        TopoManager.get.return_value = TopoNode(
            bk_inst_id=2,
            bk_inst_name="蓝鲸",
            bk_obj_id="biz",
            bk_obj_name="业务",
        )
        translator = TopoNodeTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_inst_id": TranslationField("bk_inst_id", 2),
                "bk_obj_id": TranslationField("bk_obj_id", "biz"),
            }
        )

        self.assertIn("bk_inst_id", result)
        self.assertIn("bk_obj_id", result)

        self.assertEqual(result["bk_inst_id"].display_value, "蓝鲸")
        self.assertEqual(result["bk_obj_id"].display_value, "业务")
        self.assertEqual(result["xxx"].display_value, "yyy")

    @mock.patch("alarm_backends.service.event.generator.translator.topo.TopoManager")
    def test_translate_inst_none(self, TopoManager):
        TopoManager.get.return_value = None
        translator = TopoNodeTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_inst_id": TranslationField("bk_inst_id", 2),
            }
        )

        self.assertIn("bk_inst_id", result)

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_inst_id": TranslationField("bk_inst_id", 2),
                "bk_obj_id": TranslationField("bk_obj_id", "biz"),
            }
        )
        self.assertIn("bk_inst_id", result)
        self.assertIn("bk_obj_id", result)

        self.assertEqual(result["bk_inst_id"].display_value, 2)
        self.assertEqual(result["bk_inst_id"].display_name, "模型实例名称")
        self.assertEqual(result["bk_obj_id"].display_value, "biz")
        self.assertEqual(result["bk_obj_id"].display_name, "模型名称")

    def test_translate_host(self):
        translator = TopoNodeTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "bk_target_ip": TranslationField("bk_target_ip", "10.0.0.1"),
                "bk_target_cloud_id": TranslationField("bk_target_cloud_id", 1),
                "bk_cloud_id": TranslationField("bk_cloud_id", 1),
            }
        )

        self.assertEqual(result["bk_target_ip"].display_value, "10.0.0.1")
        self.assertEqual(result["bk_target_ip"].display_name, "目标IP")
        self.assertEqual(result["bk_target_cloud_id"].display_name, "云区域ID")
        self.assertEqual(result["bk_target_cloud_id"].display_name, "云区域ID")
