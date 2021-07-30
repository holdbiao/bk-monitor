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

from alarm_backends.service.event.generator.translator import ServiceInstanceTranslator, TranslationField
from alarm_backends.tests.service.event.generator.translator.utils import generate_test_strategy
from api.cmdb.define import ServiceInstance
from constants.data_source import DataSourceLabel, DataTypeLabel


class TestServiceInstanceTranslator(TestCase):
    def test_is_enabled(self):
        self.assertTrue(
            ServiceInstanceTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="mysql.base",
                )
            ).is_enabled()
        )

        self.assertFalse(
            ServiceInstanceTranslator(
                **generate_test_strategy(
                    data_source_label=DataSourceLabel.BK_DATA,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id="2_mysql_base",
                )
            ).is_enabled()
        )

    @mock.patch("alarm_backends.service.event.generator.translator.service_instance.ServiceInstanceManager")
    def test_translate(self, ServiceInstanceManager):
        ServiceInstanceManager.get.return_value = ServiceInstance(1, "mysql", 1, 1)
        translator = ServiceInstanceTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "bk_target_service_instance_id": TranslationField("bk_target_service_instance_id", 1),
                "xxx": TranslationField("xxx", "yyy"),
            }
        )

        self.assertEqual(result["bk_target_service_instance_id"].display_name, "服务实例名称")
        self.assertEqual(result["bk_target_service_instance_id"].display_value, "mysql")
        self.assertEqual(result["xxx"].display_name, "xxx")
        self.assertEqual(result["xxx"].display_value, "yyy")

    @mock.patch("alarm_backends.service.event.generator.translator.service_instance.ServiceInstanceManager")
    def test_translate_none(self, ServiceInstanceManager):
        ServiceInstanceManager.get.return_value = None
        translator = ServiceInstanceTranslator(
            **generate_test_strategy(
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                result_table_id="system.cpu_detail",
            )
        )

        result = translator.translate(
            {
                "bk_target_service_instance_id": TranslationField("bk_target_service_instance_id", 1),
                "xxx": TranslationField("xxx", "yyy"),
            }
        )

        self.assertEqual(result["bk_target_service_instance_id"].display_name, "服务实例ID")
        self.assertEqual(result["bk_target_service_instance_id"].display_value, 1)
        self.assertEqual(result["xxx"].display_name, "xxx")
        self.assertEqual(result["xxx"].display_value, "yyy")

        result = translator.translate({"xxx": TranslationField("xxx", "yyy")})
        self.assertEqual(result["xxx"].display_value, "yyy")
