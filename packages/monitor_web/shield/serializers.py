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


from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class BaseSerializer(serializers.Serializer):
    class CycleConfigSlz(serializers.Serializer):
        type = serializers.IntegerField(required=True)
        week_list = serializers.ListField(required=False, default=[])
        day_list = serializers.ListField(required=False, default=[])
        begin_time = serializers.CharField(required=False, default="", allow_blank=True)
        end_time = serializers.CharField(required=False, default="", allow_blank=True)

    class NoticeConfigSlz(serializers.Serializer):
        notice_way = serializers.ListField(required=False)
        notice_receiver = serializers.ListField(required=False)
        notice_time = serializers.IntegerField(required=False)

    bk_biz_id = serializers.IntegerField(required=True, label=_("业务id"))
    category = serializers.ChoiceField(required=True, choices=["scope", "strategy", "event"], label=_("屏蔽类型"))
    begin_time = serializers.CharField(required=True, label=_("屏蔽开始时间"))
    end_time = serializers.CharField(required=True, label=_("屏蔽结束时间"))
    dimension_config = serializers.DictField(required=True, label=_("维度配置"))
    cycle_config = CycleConfigSlz(required=False, label=_("周期配置"))
    shield_notice = serializers.BooleanField(required=True, label=_("是否有屏蔽通知"))
    notice_config = NoticeConfigSlz(required=False, label=_("通知配置"))
    description = serializers.CharField(required=False, label=_("屏蔽原因"), allow_blank=True)
    is_quick = serializers.BooleanField(required=False, label=_("是否是快捷屏蔽"), default=False)


class ScopeSerializer(BaseSerializer):
    class DimensionConfig(serializers.Serializer):
        scope_type = serializers.CharField(required=True)
        target = serializers.ListField(required=False)
        metric_id = serializers.ListField(required=False)

    dimension_config = DimensionConfig(required=True, label=_("维度配置"))


class StrategySerializer(BaseSerializer):
    class DimensionConfig(serializers.Serializer):
        id = serializers.ListField(required=True)
        level = serializers.ListField(required=False)
        scope_type = serializers.CharField(required=False)
        target = serializers.ListField(required=False)

    dimension_config = DimensionConfig(required=True, label=_("维度配置"))


class EventSerializer(BaseSerializer):
    class DimensionConfig(serializers.Serializer):
        id = serializers.CharField(required=True)

    dimension_config = DimensionConfig(required=True, label=_("维度配置"))


SHIELD_SERIALIZER = {"scope": ScopeSerializer, "strategy": StrategySerializer, "event": EventSerializer}
