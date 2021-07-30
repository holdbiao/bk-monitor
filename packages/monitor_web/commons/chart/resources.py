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

from core.drf_resource.base import Resource
from bkmonitor.utils import time_tools
from bkmonitor.views import serializers
from utils.chart.metric_chart import MetricChart


class GraphPointResource(Resource):
    """
    通用图表接口
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(default=0, label=_("业务id"))
        monitor_field = serializers.CharField(required=True, label=_("监控指标对象"))
        result_table_id = serializers.CharField(required=True, label=_("rt表名"))
        filter_dict = serializers.DictField(required=False, default=None, label=_("自定义过滤条件"))
        group_by_list = serializers.ListField(required=False, default=None, label=_("聚合字段"))
        method = serializers.CharField(required=False, default="MEAN", label=_("聚合方法"))
        unit = serializers.CharField(required=False, default="", allow_blank=True, label=_("单位"))
        conversion = serializers.FloatField(required=False, default=1, label=_("转换除数"))
        series_name = serializers.CharField(required=False, default="", allow_blank=True, label=_("指标名称"))
        view_width = serializers.IntegerField(required=False, default=12, label=_("宽度"))
        interval = serializers.IntegerField(required=False, default=1, label=_("采集间隔"))
        time_step = serializers.IntegerField(required=False, default=0, label=_("指定数据点频率"))
        use_short_series_name = serializers.BooleanField(required=False, default=False, label=_("是否使用短指标名"))
        time_range = serializers.CharField(required=False, label=_("时间范围"))
        # 兼容时间戳形式
        time_start = serializers.IntegerField(required=False, label=_("开始时间"))
        time_end = serializers.IntegerField(required=False, label=_("结束时间"))
        # 兼容日志
        extend_fields = serializers.DictField(default={}, label=_("日志需要的额外字段"))
        data_source_label = serializers.CharField(required=False, default="", allow_blank=True, label=_("数据来源"))
        data_type_label = serializers.CharField(required=False, default="", allow_blank=True, label=_("数据类型"))

    def perform_request(self, data):
        # 处理时间
        if not (data.get("time_start") and data.get("time_end")):
            data["time_start"], data["time_end"] = time_tools.parse_time_range(data.get("time_range"))
            if data.get("time_range"):
                data.pop("time_range")
        data["time_start"] *= 1000
        data["time_end"] *= 1000

        chart = MetricChart(**data)
        return chart.get_chart()
