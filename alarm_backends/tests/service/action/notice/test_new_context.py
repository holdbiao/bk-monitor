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


import arrow
import pytest
from django.utils import translation

from alarm_backends.service.action.notice.context import NoticeContext
from bkmonitor.models import AlertCollect
from bkmonitor.utils.template import AlarmNoticeTemplate

from ..fixtures.strategy import strategy  # noqa

pytestmark = pytest.mark.django_db


class TestContext(object):
    def test_base_notice_context(self, strategy):  # noqa
        event_action = strategy
        alert_collect = AlertCollect.objects.create(
            bk_biz_id=2,
            collect_key="123456",
            message="test",
            collect_time=arrow.now().datetime,
        )
        context = NoticeContext("weixin", [{"id": event_action.id, "event_id": event_action.event_id}], alert_collect)

        # 测试基本数据结构
        assert context.event
        assert len(context.events) == 1
        assert len(context.event_actions) == 1

    def test_context_params(self, strategy):  # noqa
        event_action = strategy
        alert_collect = AlertCollect.objects.create(
            bk_biz_id=2,
            collect_key="123456",
            message="test",
            collect_time=arrow.now().datetime,
        )
        for notice_way in ["weixin", "sms", "mail"]:
            print("\n\n\nnotice_way: {}".format(notice_way))
            alert_collect.collect_type = "DIMENSION"
            context = NoticeContext(
                notice_way, [{"id": event_action.id, "event_id": event_action.event_id}], alert_collect
            )

            # 测试Alarm取值是否存在异常
            alarm_fields = [
                "collect_count",
                "display_dimensions",
                "display_targets",
                "target_string",
                "dimension_string",
                "time",
                "begin_time",
                "duration",
                "current_value",
                "detail_url",
                "notice_from",
                "company",
                "data_source_name",
                "target_type",
                "target_type_name",
            ]
            assert context.alarm.collect_count == 1
            for field in alarm_fields:
                print(field + ": ", getattr(context.alarm, field))

            # 测试Content取值是否存在异常
            assert context.content
            for field in context.content.Fields:
                value = getattr(context.content, field)
                if value:
                    print(value)

            # 测试跨策略汇总
            alert_collect.collect_type = "MULTI_STRATEGY"
            context = NoticeContext(
                notice_way, [{"id": event_action.id, "event_id": event_action.event_id}], alert_collect
            )

            # 测试Content取值是否存在异常
            assert context.content
            for field in context.content.Fields:
                value = getattr(context.content, field)
                if value:
                    print(value)

            print(context.event_infos)

    def test_dimension_collect_message(self, strategy):  # noqa
        translation.activate("en")
        event_action = strategy
        alert_collect = AlertCollect.objects.create(
            bk_biz_id=2,
            collect_key="123456",
            message="test",
            collect_time=arrow.now().datetime,
            collect_type="DIMENSION",
        )

        for notice_way in ["weixin", "sms", "mail"]:
            alert_collect.collect_type = "DIMENSION"
            context = NoticeContext(
                notice_way, [{"id": event_action.id, "event_id": event_action.event_id}], alert_collect
            )
            template = AlarmNoticeTemplate(
                "notice/anomaly/{}/{}_content.jinja".format(alert_collect.collect_type, notice_way)
            )
            print(template.render(context.get_dictionary()))

            alert_collect.collect_type = "MULTI_STRATEGY"
            context = NoticeContext(
                notice_way, [{"id": event_action.id, "event_id": event_action.event_id}], alert_collect
            )
            template = AlarmNoticeTemplate(
                "notice/anomaly/{}/{}_content.jinja".format(alert_collect.collect_type, notice_way)
            )
            print(template.render(context.get_dictionary()))

        translation.deactivate()
