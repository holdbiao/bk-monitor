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

from monitor_web.custom_report.views import CustomReportViewSet


class TestCustomReportViewSet(TestCase):
    def test_view_set(self):
        custom_report_view_set_cls = CustomReportViewSet
        custom_report_view_set_cls.generate_endpoint()
        self.assertTrue(hasattr(custom_report_view_set_cls, "proxy_host_info"))
        self.assertEqual(CustomReportViewSet.proxy_host_info.bind_to_methods, ["GET"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "query_custom_event_group"))
        self.assertEqual(CustomReportViewSet.query_custom_event_group.bind_to_methods, ["GET"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "get_custom_event_group"))
        self.assertEqual(CustomReportViewSet.get_custom_event_group.bind_to_methods, ["GET"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "validate_custom_event_group_name"))
        self.assertEqual(CustomReportViewSet.validate_custom_event_group_name.bind_to_methods, ["GET"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "create_custom_event_group"))
        self.assertEqual(CustomReportViewSet.create_custom_event_group.bind_to_methods, ["POST"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "modify_custom_event_group"))
        self.assertEqual(CustomReportViewSet.modify_custom_event_group.bind_to_methods, ["POST"])

        self.assertTrue(hasattr(custom_report_view_set_cls, "delete_custom_event_group"))
        self.assertEqual(CustomReportViewSet.delete_custom_event_group.bind_to_methods, ["POST"])
