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

from bkmonitor.data_source import load_data_source
from utils.chart.front_default_processor import FrontDefaultProcessor


class MetricChart(object):
    """
    根据传入的 Metric 相关信息生成图表
    """

    def __init__(
        self,
        monitor_field,
        result_table_id,
        bk_biz_id=0,
        filter_dict=None,
        group_by_list=None,
        method="MEAN",
        unit="",
        conversion=1,
        series_name="",
        time_start=None,
        time_end=None,
        view_width=12,
        interval=1,
        time_step=0,
        use_short_series_name=False,
        # 兼容日志
        extend_fields=None,
        data_source_label=None,
        data_type_label=None,
        granularity=None,
        null_value_as=None,
    ):
        """
        :param monitor_field: 【必需】监控指标对象
        :param result_table_id: 【必须】rt表名
        :param filter_dict: 自定义过滤条件，非必填
        :param group_by_list: 聚合字段，非必填
        :param unit: 单位，非必填
        :param conversion: 转换除数，非必填，默认为1
        :param series_name: 指标名称，非必填
        :param time_start: 开始时间 （非必填，如未指定则默认展示24小时内数据）
        :param time_end: 结束时间（非必填，如未指定则默认展示24小时内数据）
        :param view_width: 宽度，非必填，默认12
        :param interval: 采集间隔，非必填，默认1
        :param time_step: 指定数据点频率 (非必填，默认为0，由系统根据所选时间范围自动计算)
        :param use_short_series_name: 是否使用短指标名（去掉维度描述）granularity
        :param granularity: 时间粒度 minute
        """
        if group_by_list:
            for field in group_by_list:
                if field.startswith("minute"):
                    group_by_list.remove(field)

        self.bk_biz_id = bk_biz_id
        self.time_start = time_start
        self.time_end = time_end
        self.dimensions = group_by_list
        self.unit = unit
        self.monitor_field = monitor_field
        self.method = method
        self.conversion = conversion
        self.series_name = series_name
        self.result_table_id = result_table_id
        self.use_short_series_name = use_short_series_name
        self.extend_fields = extend_fields or {}
        self.data_source_label = data_source_label
        self.data_type_label = data_type_label
        self.granularity = granularity
        self.filter_dict = filter_dict
        self.null_value_as = null_value_as

        self.data_source = load_data_source(data_source_label, data_type_label)(
            bk_biz_id=self.bk_biz_id,
            table=result_table_id,
            metrics=[{"field": monitor_field, "method": self.method}],
            filter_dict=filter_dict,
            group_by=group_by_list,
            interval=interval * 60,
            index_set_id=self.extend_fields.get("index_set_id"),
            time_field=self.extend_fields.get("time_field"),
        )

    def get_chart(self):
        """
        生成 highchart 出图所需配置
        """
        processor = FrontDefaultProcessor(
            self.data_source.query_data(self.time_start, self.time_end),
            dimension_fields=self.dimensions,
            series_name_prefix=self.series_name,
            unit=self.unit,
            conversion=self.conversion,
            result_table_id=self.result_table_id,
            use_short_series_name=self.use_short_series_name,
            null_value_as=self.null_value_as,
        )
        processor.set_full_time((self.time_start // 1000, self.time_end // 1000), 60 * 1000)
        return processor.make_graph(self.monitor_field)
