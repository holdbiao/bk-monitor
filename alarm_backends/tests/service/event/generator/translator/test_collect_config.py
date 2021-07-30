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

from alarm_backends.service.event.generator.translator import CollectingConfigTranslator, TranslationField
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestCollectingConfigTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            CollectingConfigTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

        self.assertFalse(
            CollectingConfigTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_DATA,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

        self.assertTrue(
            CollectingConfigTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.EVENT,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.collect_config.CollectConfigCacheManager")
    def test_translate(self, CollectConfigCacheManager):
        CollectConfigCacheManager.get.return_value = {"name": "测试配置"}
        translator = CollectingConfigTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="mysql.base",
            )
        )
        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_collect_config_id": TranslationField("bk_collect_config_id", 3),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["bk_collect_config_id"].display_name, "采集配置名称")
        self.assertEqual(result["bk_collect_config_id"].display_value, "测试配置")

    @mock.patch("alarm_backends.service.event.generator.translator.collect_config.CollectConfigCacheManager")
    def test_translate_none(self, CollectConfigCacheManager):
        CollectConfigCacheManager.get.return_value = None
        translator = CollectingConfigTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="mysql.base",
            )
        )
        result = translator.translate(
            {
                "xxx": TranslationField("xxx", "yyy"),
                "bk_collect_config_id": TranslationField("bk_collect_config_id", 3),
            }
        )

        self.assertEqual(result["xxx"].display_value, "yyy")
        self.assertEqual(result["bk_collect_config_id"].display_name, "采集配置ID")
        self.assertEqual(result["bk_collect_config_id"].display_value, 3)
