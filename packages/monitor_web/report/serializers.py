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

from bkmonitor.views import serializers
from constants.report import StaffChoice, GROUPS


class StaffSerializer(serializers.Serializer):
    id = serializers.CharField(required=True, max_length=512, label=_("用户名或组ID"))
    name = serializers.CharField(required=False, max_length=512, label=_("用户名或组名"))
    group = serializers.ChoiceField(required=False, allow_null=True, choices=GROUPS, label=_("所属组别"))
    type = serializers.ChoiceField(required=True, choices=[StaffChoice.user, StaffChoice.group])


class ReceiverSerializer(StaffSerializer):
    is_enabled = serializers.BooleanField(required=True, label=_("是否启动订阅"))


class FrequencySerializer(serializers.Serializer):
    type = serializers.IntegerField(required=True, label=_("频率类型"))
    day_list = serializers.ListField(required=True, label=_("几天"))
    week_list = serializers.ListField(required=True, label=_("周几"))
    run_time = serializers.CharField(required=True, label=_("运行时间"))


class ReportContentSerializer(serializers.Serializer):
    content_title = serializers.CharField(required=True, max_length=512, label=_("子内容标题"))
    content_details = serializers.CharField(required=True, max_length=512, label=_("字内容说明"), allow_blank=True)
    row_pictures_num = serializers.IntegerField(required=True, label=_("一行几幅图"))
    graphs = serializers.ListField(required=True, label=_("图表"))
