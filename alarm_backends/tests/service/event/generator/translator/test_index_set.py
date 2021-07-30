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

from __future__ import absolute_import, unicode_literals

import mock
from django.test import TestCase

from alarm_backends.service.event.generator.translator import IndexSetTranslator, TranslationField
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestIndexSetTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            IndexSetTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_LOG_SEARCH,
                    data_type_label=DataTypeLabel.LOG,
                    result_table_id="2_bklog_test",
                    extend_fields={
                        "index_set_id": 3,
                    },
                )
            ).is_enabled()
        )

        self.assertFalse(
            IndexSetTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.EVENT,
                    result_table_id="mysql.base",
                    extend_fields={
                        "index_set_id": 3,
                    },
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.index_set.ResultTableCacheManager")
    def test_translate(self, ResultTableCacheManager):
        ResultTableCacheManager.get_result_table_by_id.return_value = {
            "table_id": "3",
            "table_name": "测试日志索引集",
            "fields": [
                {"field_name": "ip", "field_type": "string", "field_alias": "上报IP", "is_dimension": True},
                {"field_name": "path", "field_type": "str", "field_alias": "日志路径", "is_dimension": True},
            ],
        }
        translator = IndexSetTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_LOG_SEARCH,
                data_type_label=DataTypeLabel.LOG,
                result_table_id="2_bklog_test",
                extend_fields={
                    "index_set_id": 3,
                },
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "ip": TranslationField("ip", "10.0.0.1"),
                "path": TranslationField("path", "/data/test.log"),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["ip"].display_name, "上报IP")
        self.assertEqual(result["path"].display_name, "日志路径")
        self.assertEqual(result["ip"].display_value, "10.0.0.1")

    @mock.patch("alarm_backends.service.event.generator.translator.index_set.ResultTableCacheManager")
    def test_translate_none(self, ResultTableCacheManager):
        ResultTableCacheManager.get_result_table_by_id.return_value = None
        translator = IndexSetTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_LOG_SEARCH,
                data_type_label=DataTypeLabel.LOG,
                result_table_id="2_bklog_test",
                extend_fields={
                    "index_set_id": 3,
                },
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "ip": TranslationField("ip", "10.0.0.1"),
                "path": TranslationField("path", "/data/test.log"),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["ip"].display_name, "ip")
        self.assertEqual(result["path"].display_name, "path")
        self.assertEqual(result["ip"].display_value, "10.0.0.1")
