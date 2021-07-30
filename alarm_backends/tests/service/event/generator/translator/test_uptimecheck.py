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
import json
from django.test import TestCase

from alarm_backends.core.cache.models.uptimecheck import UptimecheckCacheManager
from alarm_backends.service.event.generator.translator import TranslationField, UptimecheckConfigTranslator
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestTopoTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            UptimecheckConfigTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="uptimecheck.base",
                )
            ).is_enabled()
        )

        self.assertFalse(
            UptimecheckConfigTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_DATA,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="2_mysql_base",
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.uptimecheck.UptimecheckCacheManager")
    def test_translate(self, UptimecheckCacheManager):
        UptimecheckCacheManager.get_node.return_value = {"name": "测试节点"}
        UptimecheckCacheManager.get_task.return_value = {
            "name": "测试任务",
            "config": {"response_code": "404", "response": "test_response"},
        }
        UptimecheckCacheManager.cache.mget.return_value = {"id": "3", "name": "测试节点"}
        translator = UptimecheckConfigTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="uptimecheck.base",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")

        result = translator.translate(
            {
                "node_id": TranslationField("node_id", "3"),
                "task_id": TranslationField("node_id", "4"),
            }
        )
        self.assertEqual(result["node_id"].display_name, "节点名称")
        self.assertEqual(result["node_id"].display_value, "测试节点")
        self.assertEqual(result["task_id"].display_name, "任务名称")
        self.assertEqual(result["task_id"].display_value, "测试任务")

        result = translator.translate(
            {
                "task_id": TranslationField("task_id", "3"),
                "error_code": TranslationField("error_code", "3303"),
            }
        )
        self.assertEqual(result["task_id"].display_name, "任务名称")
        self.assertEqual(result["task_id"].display_value, "测试任务")
        self.assertEqual(result["error_code"].display_name, "响应状态码")
        self.assertEqual(result["error_code"].display_value, "404")

        result = translator.translate(
            {
                "task_id": TranslationField("task_id", "3"),
                "error_code": TranslationField("error_code", "3302"),
            }
        )
        self.assertEqual(result["task_id"].display_name, "任务名称")
        self.assertEqual(result["task_id"].display_value, "测试任务")
        self.assertEqual(result["error_code"].display_name, "响应消息")
        self.assertEqual(result["error_code"].display_value, "test_response")

    @mock.patch("alarm_backends.service.event.generator.translator.uptimecheck.UptimecheckCacheManager")
    def test_translate_none(self, UptimecheckCacheManager):
        UptimecheckCacheManager.get_node.return_value = None
        UptimecheckCacheManager.get_task.return_value = None
        translator = UptimecheckConfigTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="uptimecheck.base",
            )
        )
        result = translator.translate(
            {
                "node_id": TranslationField("node_id", "3"),
                "task_id": TranslationField("node_id", "4"),
            }
        )
        self.assertEqual(result["node_id"].display_name, "节点名称")
        self.assertEqual(result["node_id"].display_value, "3")
        self.assertEqual(result["task_id"].display_name, "任务ID")
        self.assertEqual(result["task_id"].display_value, "4 (任务不存在)")
