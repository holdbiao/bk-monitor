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

from alarm_backends.service.event.generator.translator import ResultTableTranslator, TranslationField
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestResultTableTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            ResultTableTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

        self.assertTrue(
            ResultTableTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_DATA,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="2_mysql_base",
                )
            ).is_enabled()
        )

        self.assertFalse(
            ResultTableTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.EVENT,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.result_table.ResultTableCacheManager")
    def test_translate(self, ResultTableCacheManager):
        ResultTableCacheManager.get_result_table_by_id.return_value = {
            "table_id": "system.cpu_detail",
            "table_name": "系统CPU",
            "fields": [
                {"field_name": "ip", "field_type": "string", "field_alias": "上报IP", "is_dimension": True},
                {"field_name": "bk_cloud_id", "field_type": "str", "field_alias": "云区域ID", "is_dimension": True},
            ],
        }
        translator = ResultTableTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "ip": TranslationField("ip", "10.0.0.1"),
                "bk_cloud_id": TranslationField("bk_cloud_id", 2),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["ip"].display_name, "上报IP")
        self.assertEqual(result["bk_cloud_id"].display_name, "云区域ID")
        self.assertEqual(result["ip"].display_value, "10.0.0.1")

    @mock.patch("alarm_backends.service.event.generator.translator.result_table.ResultTableCacheManager")
    def test_translate_none(self, ResultTableCacheManager):
        ResultTableCacheManager.get_result_table_by_id.return_value = None
        translator = ResultTableTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "ip": TranslationField("ip", "10.0.0.1"),
                "bk_cloud_id": TranslationField("bk_cloud_id", 2),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["ip"].display_name, "ip")
        self.assertEqual(result["bk_cloud_id"].display_name, "bk_cloud_id")
        self.assertEqual(result["ip"].display_value, "10.0.0.1")
