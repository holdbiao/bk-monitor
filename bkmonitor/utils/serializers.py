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

import re

from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from rest_framework import serializers

from core.unit import UNITS
from monitor_web.plugin.constant import RT_RESERVED_WORD_EXACT, RT_TABLE_NAME_WORD_EXACT

PATTERN = re.compile(r"^[_a-zA-Z][a-zA-Z0-9_]*$")


class StrictCharField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.update({"trim_whitespace": False})
        super(StrictCharField, self).__init__(**kwargs)


class MetricJsonSerializer(serializers.Serializer):
    class FieldsSerializer(serializers.Serializer):
        description = StrictCharField(required=True, allow_blank=True, label=_("字段描述"))
        type = serializers.ChoiceField(required=True, choices=["string", "double", "int"], label=_("字段类型"))
        monitor_type = serializers.ChoiceField(required=True, choices=["dimension", "metric"], label=_("指标类型"))
        unit = StrictCharField(required=False, allow_blank=True, label=_("单位"))
        name = serializers.CharField(required=True, label=_("字段名"))
        conversion = StrictCharField(required=False, label=_("换算单位"))
        is_diff_metric = serializers.BooleanField(default=False, label=_("是否为差值指标"))
        is_active = serializers.BooleanField(default=True, label=_("是否启用"))
        source_name = serializers.CharField(default="", allow_blank=True, label=_("原指标名"))
        dimensions = serializers.ListField(required=False, allow_empty=True, label=_("聚合维度"))

        def validate_unit(self, value):
            if value not in self.support_unit:
                return "none"
            return value

        @cached_property
        def support_unit(self):
            units = []
            for units_value in UNITS.values():
                for value in units_value.values():
                    units.append(value.gid)
            return units

    table_name = serializers.RegexField(required=True, regex=r"^[a-zA-Z][a-zA-Z0-9_]*$", label=_("表名"))
    table_desc = StrictCharField(required=True, label=_("表描述"))
    fields = FieldsSerializer(required=True, many=True, label=_("指标项"))


class MetricJsonBaseSerializer(serializers.Serializer):
    metric_json = MetricJsonSerializer(required=False, many=True, label=_("指标配置"), default=[])

    def validate_metric_json(self, value):
        if not value:
            return value
            # raise serializers.ValidationError(_("指标维度不能为空"))
        metric_name_list = []
        table_name_list = []
        for value_detail in value:
            if not value_detail.get("fields", ""):
                raise serializers.ValidationError(_("指标维度不能为空"))

            dimension_name_list = []
            for field_detail in value_detail["fields"]:
                if field_detail.get("source_name", "").upper() not in RT_RESERVED_WORD_EXACT and field_detail[
                    "name"
                ].startswith("_"):
                    raise serializers.ValidationError(_("非与保留关键字重名字段不允许以'_'开头"))
                if field_detail["name"].upper() in RT_RESERVED_WORD_EXACT:
                    raise serializers.ValidationError(_("指标维度不允许与保留关键字重名"))
                if not PATTERN.match(field_detail["name"]):
                    raise serializers.ValidationError(_("名称校验不通过:{}".format(field_detail["name"])))
                if field_detail["monitor_type"] == "metric":
                    metric_name_list.append(field_detail["name"])
                if field_detail["monitor_type"] == "dimension":
                    dimension_name_list.append(field_detail["name"])

            # 维度去重
            dimension_dict = dict().fromkeys(dimension_name_list, True)
            value_detail["fields"] = list(
                filter(
                    lambda x: dimension_dict.pop(x["name"], False) or x["monitor_type"] != "dimension",
                    value_detail["fields"],
                )
            )

            intersection = set(metric_name_list) & set(dimension_name_list)
            if intersection:
                raise serializers.ValidationError(_("指标和维度不允许重名,重名内容:{}".format(intersection)))

            if value_detail["table_name"].upper() in RT_TABLE_NAME_WORD_EXACT:
                raise serializers.ValidationError(_("表名不允许与保留关键字重名"))

            table_name_list.append(value_detail["table_name"])

        if len(metric_name_list) != len(set(metric_name_list)):
            raise serializers.ValidationError(_("指标维度中指标名不允许重名"))
        if len(table_name_list) != len(set(table_name_list)):
            raise serializers.ValidationError(_("指标维度中表名不允许重名"))

        return value
