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
from typing import Dict

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _lazy

from core.errors.alarm_backends.detect import (
    InvalidAdvancedRingRatioConfig,
    InvalidAdvancedYearRoundConfig,
    InvalidSimpleRingRatioConfig,
    InvalidSimpleYearRoundConfig,
)

allowed_threshold_method = {
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "eq": "==",
    "neq": "!=",
}

allowed_method = {
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "eq": "==",
}


class AdvancedYearRoundSerializer(serializers.Serializer):
    """
    高级同比算法serializer
    """

    floor = serializers.FloatField(required=True, allow_null=True, min_value=0)
    floor_interval = serializers.IntegerField(required=True, allow_null=True, min_value=1)
    ceil = serializers.FloatField(required=True, allow_null=True, min_value=0)
    ceil_interval = serializers.IntegerField(required=True, allow_null=True, min_value=1)

    def validate(self, attrs):
        floor = attrs["floor"]
        floor_interval = attrs["floor_interval"]
        ceil = attrs["ceil"]
        ceil_interval = attrs["ceil_interval"]
        floor_configured = all([floor, floor_interval])
        ceil_configured = all([ceil, ceil_interval])
        if not floor_configured:
            attrs["floor"] = None
            attrs["floor_interval"] = None
        if not ceil_configured:
            attrs["ceil"] = None
            attrs["ceil_interval"] = None
        if not any([ceil_configured, floor_configured]):
            raise InvalidAdvancedYearRoundConfig(config=attrs)
        return attrs


class AdvancedRingRatioSerializer(AdvancedYearRoundSerializer):
    """
    高级环比算法serializer,复用高级同比算法serializer
    """

    def validate(self, attrs):
        try:
            return super(AdvancedRingRatioSerializer, self).validate(attrs)
        except InvalidAdvancedYearRoundConfig:
            raise InvalidAdvancedRingRatioConfig(config=attrs)


class RingRatioAmplitudeSerializer(serializers.Serializer):
    """
    环比振幅算法serializer
    """

    ratio = serializers.FloatField(required=True)
    shock = serializers.FloatField(required=True)
    threshold = serializers.FloatField(required=True)


class SimpleRingRatioSerializer(serializers.Serializer):
    """
    简单环比算法serializer
    """

    floor = serializers.FloatField(required=True, allow_null=True, min_value=0)
    ceil = serializers.FloatField(required=True, allow_null=True, min_value=0)

    def validate(self, attrs):
        floor = attrs["floor"]
        ceil = attrs["ceil"]
        if not any([floor, ceil]):
            raise InvalidSimpleRingRatioConfig(config=attrs)
        return attrs


class SimpleYearRoundSerializer(SimpleRingRatioSerializer):
    """
    简单同比算法serializer
    """

    def validate(self, attrs):
        try:
            return super(SimpleYearRoundSerializer, self).validate(attrs)
        except InvalidSimpleRingRatioConfig:
            raise InvalidSimpleYearRoundConfig(config=attrs)


class ThresholdSerializer(serializers.ListSerializer):
    """
    静态阈值算法serializer
    """

    class AndSerializer(serializers.ListSerializer):
        class UnitSerializer(serializers.Serializer):
            threshold = serializers.FloatField(required=True)
            method = serializers.ChoiceField(required=True, choices=list(allowed_threshold_method.keys()))

        child = UnitSerializer()

    child = AndSerializer(allow_empty=False)


class IntelligentDetectSerializer(serializers.Serializer):
    """
    智能异常检测算法serializer
    """

    sensitivity_value = serializers.IntegerField(required=True, min_value=0, max_value=100)
    # 异常检测方向， ceil: 向上突增检测， floor: 向下突增检测， all: 上下两个方向突增检测 (default: all)
    anomaly_detect_direct = serializers.ChoiceField(default="all", choices=["ceil", "floor", "all"])


class YearRoundAmplitudeSerializer(serializers.Serializer):
    """
    同比振幅算法
    """

    ratio = serializers.FloatField(required=True)
    shock = serializers.FloatField(required=True)
    days = serializers.IntegerField(required=True, min_value=1)
    method = serializers.ChoiceField(required=True, choices=list(allowed_method.keys()))


# 同比区间serializer与同比振幅算法配置格式一致
YearRoundRangeSerializer = YearRoundAmplitudeSerializer


class BkMonitorTimeSeriesSerializer(serializers.Serializer):
    result_table_id = serializers.CharField(label=_lazy("结果表"))
    agg_method = serializers.CharField(label=_lazy("聚合方法"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(
        label=_lazy("聚合维度"),
        allow_empty=True,
    )
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())
    metric_field = serializers.CharField(label=_lazy("指标"))
    unit = serializers.CharField(label=_lazy("单位"), allow_blank=True, default="")
    origin_config = serializers.DictField(label=_lazy("原始配置"), required=False)
    intelligent_detect = serializers.DictField(required=False)
    values = serializers.ListField(required=False)


class BkMonitorLogSerializer(serializers.Serializer):
    result_table_id = serializers.CharField(label=_lazy("结果表"))
    agg_method = serializers.CharField(label=_lazy("聚合方法"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(allow_empty=True)
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())


class BkMonitorEventSerializer(serializers.Serializer):
    result_table_id = serializers.CharField(label=_lazy("结果表"))
    metric_field = serializers.CharField(label=_lazy("指标"))
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())


class BkLogSearchTimeSeriesSerializer(serializers.Serializer):
    index_set_id = serializers.IntegerField(label=_lazy("索引集ID"))
    result_table_id = serializers.CharField(label=_lazy("索引"), allow_blank=True)
    agg_method = serializers.CharField(label=_lazy("聚合方法"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(
        label=_lazy("聚合维度"),
        allow_empty=True,
    )
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())
    metric_field = serializers.CharField(label=_lazy("指标"))
    unit = serializers.CharField(label=_lazy("单位"), allow_blank=True, default="")
    time_field = serializers.CharField(
        label=_lazy("时间字段"), default="dtEventTimeStamp", allow_blank=True, allow_null=True
    )

    def validate(self, attrs: Dict) -> Dict:
        if not attrs.get("time_field"):
            attrs["time_field"] = "dtEventTimeStamp"
        return attrs


class BkLogSearchLogSerializer(serializers.Serializer):
    query_string = serializers.CharField(label=_lazy("查询语句"))
    result_table_id = serializers.CharField(label=_lazy("索引"), allow_blank=True)
    index_set_id = serializers.IntegerField(label=_lazy("索引集ID"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(
        label=_lazy("聚合维度"),
        allow_empty=True,
    )
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())
    time_field = serializers.CharField(
        label=_lazy("时间字段"), default="dtEventTimeStamp", allow_blank=True, allow_null=True
    )

    def validate(self, attrs: Dict) -> Dict:
        if not attrs.get("time_field"):
            attrs["time_field"] = "dtEventTimeStamp"
        return attrs


class CustomEventSerializer(serializers.Serializer):
    result_table_id = serializers.CharField(label=_lazy("结果表"))
    agg_method = serializers.CharField(label=_lazy("聚合方法"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(allow_empty=True)
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())
    custom_event_name = serializers.CharField(label=_lazy("事件名"))


class CustomTimeSeriesSerializer(BkMonitorTimeSeriesSerializer):
    pass


class BkDataTimeSeriesSerializer(serializers.Serializer):
    result_table_id = serializers.CharField(label=_lazy("结果表"))
    agg_method = serializers.CharField(label=_lazy("聚合方法"))
    agg_interval = serializers.IntegerField(label=_lazy("聚合周期"), min_value=0)
    agg_dimension = serializers.ListField(
        label=_lazy("聚合维度"),
        allow_empty=True,
    )
    agg_condition = serializers.ListField(label=_lazy("查询条件"), allow_empty=True, child=serializers.DictField())
    metric_field = serializers.CharField(label=_lazy("指标"))
    unit = serializers.CharField(label=_lazy("单位"), allow_blank=True, default="")
    intelligent_detect = serializers.DictField(required=False)
    values = serializers.ListField(required=False)
    time_field = serializers.CharField(
        label=_lazy("时间字段"), default="dtEventTimeStamp", allow_blank=True, allow_null=True
    )

    def validate(self, attrs: Dict) -> Dict:
        if not attrs.get("time_field"):
            attrs["time_field"] = "dtEventTimeStamp"
        return attrs
