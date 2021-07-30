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
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model

from bkmonitor.views import serializers
from core.drf_resource.viewsets import ResourceViewSet
from core.drf_resource.viewsets import ResourceRoute
from core.drf_resource import Resource, resource
from bkmonitor.utils.common_utils import to_dict
from bkmonitor.models import ReportItems
from alarm_backends.service.report.handler import ReportHandler
from alarm_backends.service.report.tasks import render_mails
from constants.report import StaffChoice, GROUPS
from alarm_backends.core.cache.mail_report import MailReportCacheManager


class GetStatisticsByJson(Resource):
    """
    获取json格式的运营数据
    """

    def perform_request(self, params):
        result = resource.statistics.get_statistics_data(response_format="json")

        return to_dict(result)


class GetSettingAndNotifyGroup(Resource):
    """
    获取配置管理员及其业务、告警接收人及其业务
    """

    def perform_request(self, params):
        result = MailReportCacheManager().fetch_groups_and_user_bizs()

        return result


class IsSuperuser(Resource):
    """
    判断用户是否超级管理员
    """

    class RequestSerializer(serializers.Serializer):
        username = serializers.ListField(required=True)

    def perform_request(self, params):
        users_is_superuser = {}
        user_model = get_user_model()
        bkuser = user_model.objects.filter(username__in=params["username"])
        for user in bkuser:
            users_is_superuser[str(user)] = user.is_superuser
        return users_is_superuser


class TestReportMail(Resource):
    """
    发送订阅报表测试
    """

    class RequestSerializer(serializers.Serializer):
        class StaffSerializer(serializers.Serializer):
            id = serializers.CharField(required=True, max_length=512, label=_("用户名或组ID"))
            name = serializers.CharField(required=False, max_length=512, label=_("用户名或组名"))
            group = serializers.ChoiceField(required=False, allow_null=True, choices=GROUPS, label=_("所属组别"))
            type = serializers.ChoiceField(required=True, choices=[StaffChoice.user, StaffChoice.group])

        class ReceiverSerializer(StaffSerializer):
            is_enabled = serializers.BooleanField(required=True, label=_("是否启动订阅"))

        class ReportContentSerializer(serializers.Serializer):
            content_title = serializers.CharField(required=True, max_length=512, label=_("子内容标题"))
            content_details = serializers.CharField(required=True, max_length=512, label=_("字内容说明"), allow_blank=True)
            row_pictures_num = serializers.IntegerField(required=True, label=_("一行几幅图"))
            graphs = serializers.ListField(required=True, label=_("图表"))

        class FrequencySerializer(serializers.Serializer):
            type = serializers.IntegerField(required=True, label=_("频率类型"))
            day_list = serializers.ListField(required=True, label=_("几天"))
            week_list = serializers.ListField(required=True, label=_("周几"))
            run_time = serializers.CharField(required=True, label=_("运行时间"))

        creator = serializers.CharField(required=True, max_length=512)
        mail_title = serializers.CharField(required=True, max_length=512)
        receivers = ReceiverSerializer(many=True)
        report_contents = ReportContentSerializer(many=True)
        frequency = FrequencySerializer(required=False)

    def perform_request(self, params):
        # 测试邮件只发送给当前用户
        report_handler = ReportHandler()

        # 是否超管
        is_superuser = False
        user_model = get_user_model()
        try:
            bkuser = user_model.objects.get(username=params["creator"])
            if bkuser.is_superuser:
                is_superuser = True
        except user_model.DoesNotExist:
            is_superuser = False

        # 获取当前用户有权限的业务列表
        item = ReportItems(
            mail_title=params["mail_title"],
            receivers=[{"id": params["creator"], "is_enabled": True, type: "user"}],
            managers=[params["creator"]],
            frequency=params["frequency"],
        )
        # 赋予一个缺省值
        report_handler.item_id = -1

        render_mails.apply_async(
            args=(report_handler, item, params["report_contents"], [params["creator"]], is_superuser)
        )
        return "success"


class MailReportViewSet(ResourceViewSet):
    """
    邮件订阅
    """

    resource_routes = [
        ResourceRoute("GET", GetStatisticsByJson, endpoint="get_statistics_by_json"),
        ResourceRoute("GET", GetSettingAndNotifyGroup, endpoint="get_setting_and_notify_group"),
        ResourceRoute("POST", TestReportMail, endpoint="test_report_mail"),
        ResourceRoute("GET", resource.report.group_list, endpoint="group_list"),
        ResourceRoute("POST", IsSuperuser, endpoint="is_superuser"),
    ]
