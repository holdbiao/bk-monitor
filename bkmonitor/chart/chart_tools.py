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


import time
from collections import defaultdict

import six
from django.utils import timezone
from django.utils.translation import ugettext as _

from bkmonitor.utils.casting import force_float
from bkmonitor.utils.common_utils import ignored
from bkmonitor.utils.time_tools import utcoffset_in_seconds


class DataPoint(object):
    """
    sql spi返回的数据列表中的一条数据实例化
    """

    def __init__(self, point_data, count_field="count", dimension_fields=None):
        """
        :param point_data: sql api返回的数据列表中的一条数据
        :return:
        """
        count_field = count_field.lower().strip()
        # 目前支持默认存储和tsdb两类
        fields = [x.lower() for x in list(point_data.keys())]
        assert "_time_" in fields, _("无效的数据点：%s") % DataPoint
        assert count_field in fields, _("无效的指标字段：%s") % count_field
        self.data = point_data

        self.timestamp = (
            self.data.get("_time_")
            or self.data.get("time")
            or self.data.get("dteventtimestamp")
            or self.data.get("dtEventTimeStamp")
        )
        with ignored(Exception):
            self.timestamp = int(self.timestamp)
        assert isinstance(self.timestamp, six.integer_types), _("数据点对应的时间点[%s]无效") % self.timestamp
        self.count = point_data.get(count_field)
        self.dimension_fields = dimension_fields or []
        self.dimension_dict = {}
        for field in self.dimension_fields:
            if field in self.data and not field.startswith("minute"):
                self.dimension_dict[field] = self.data.get(field)


class DefaultProcessor(object):
    """
    将sql api返回的数据结构通过统一的处理，以期尽量减少性能损耗
    """

    def __init__(
        self,
        data_list,
        dimension_fields=None,
        series_name_prefix="",
        result_table_id="",
        default_series_name=None,
        conversion=1.0,
        unit="",
        time_offset=0,
        use_short_series_name=False,
        null_value_as=None,
    ):
        """
        :param data_list: sql接口返回的数据列表
        :param dimension_fields: 维度字段列表
        :param series_name_prefix: 曲线名称统一前缀（用于主机监控/组件监控）
        :param result_table_id: 数据来源的结果表（用于解析字段描述）
        :param default_series_name: 默认线条名（用于只有一条线且没有维度数据的情况）
        :param conversion: 单位转换除数，用于（主机监控/组件监控）
        :param unit: 转换后单位，用于（主机监控/组件监控）
        :param time_offset: 数据点对应的事件位移值（用于一张图表展示同比环比数据）
        """
        self.origin_data = data_list or []
        self.is_full_time = False
        # cofingure
        self.dimension_fields = dimension_fields or []
        self.series_name_prefix = series_name_prefix
        self.result_table_id = result_table_id
        self.default_series_name = _(default_series_name) if default_series_name else _("总览")
        self.conversion = conversion
        self.unit = unit
        self.time_offset = time_offset
        self.use_short_series_name = use_short_series_name
        self.null_value_as = null_value_as

        # cache
        self.series_name_cache_instance = {}
        self.point_interval = None
        self.range_timestamp = ()

    def set_full_time(self, time_range, point_interval=60 * 1000):
        if point_interval < 60 * 1000:
            point_interval *= 1000
        self.is_full_time = True
        self.point_interval = point_interval
        start_timestamp = time_range[0] * 1000
        end_timestamp = time_range[1] * 1000
        self.range_timestamp = get_timestamp_range_list(start_timestamp, end_timestamp, point_interval)

    def get_none_data_series(self, start, end):
        # 获取无数据时间段
        none_data_timestamps = self.timestamp_slice(start, end)
        if len(none_data_timestamps) <= 1:
            return []

        if none_data_timestamps[-1] == end:
            none_data_timestamps = none_data_timestamps[:-1]
        return [[x, None] for x in none_data_timestamps]

    def make_graph(self, count_field="_value_"):
        start = time.time()
        series_info = defaultdict(
            lambda: (dict.fromkeys(self.range_timestamp, self.null_value_as) if self.is_full_time else dict())
        )
        # global_info 即返回给前端js处理的配置项
        global_info = {
            "min_y": 0,
            "max_y": 0,
            "chart_type": "spline",
            # 不再在后台计算并设置pointStart的值。
            # https://api.highcharts.com/highcharts/plotOptions.series.pointStart
            # pointStart: Number
            # If no x values are given for the points in a series,
            # pointStart defines on what value to start. For example,
            # if a series contains one yearly value starting from 1945,
            # set pointStart to 1945.
            "pointInterval": 5 * 1000 * 60,
            "x_axis": {"type": "datetime", "minRange": 3600 * 1000},
            "series": [],
            "unit": self.unit,
            "duration": 0,
            "timezone": timezone.get_current_timezone().zone,
            "utcoffset": utcoffset_in_seconds(),
        }

        i = 1
        tmp_min = None, float("-inf")
        tmp_max = None, float("inf")
        # 多维度时，每个维度的时间范围都会包含在self.origin_data。要计算采样率，需要用去重后的个数
        # 比较的两个值是读接口得到的数据时间点的个数和准备给前端的数据个数。如果抽样比率较小时，用
        # 三倍的比率进行保留峰值的抽样意义不大。暂定此阈值为2
        is_keep_peak = False
        if len(self.range_timestamp) * 2 < len(self.origin_data):
            timestamps = {item["_time_"] for item in self.origin_data}
            is_keep_peak = len(timestamps) > len(self.range_timestamp) * 2

        peak_per_cycle = 3

        for item in self.origin_data:
            point = DataPoint(item, count_field, self.dimension_fields)
            if self.time_offset:
                point.timestamp += self.time_offset
            count = self._get_val_display(point.count)

            if force_float(global_info["min_y"]) > force_float(count):
                global_info["min_y"] = count

            if force_float(global_info["max_y"]) < force_float(count):
                global_info["max_y"] = count

            series_name = self.gen_series_name(point.dimension_dict)
            if series_name not in series_info:
                series_info[series_name][point.timestamp] = count
                continue

            if force_float(count) >= force_float(tmp_max[1]):
                tmp_max = (point.timestamp, count)
            if force_float(count) <= force_float(tmp_min[1]):
                tmp_min = (point.timestamp, count)

            left_index = range(
                len(self.range_timestamp) // peak_per_cycle * peak_per_cycle, len(self.range_timestamp) + 1
            )
            if not self.is_full_time or point.timestamp in series_info[series_name]:
                if not is_keep_peak:
                    series_info[series_name][point.timestamp] = count
                else:
                    if i % peak_per_cycle == 1:
                        tmp_min = (point.timestamp, count)
                        tmp_max = (point.timestamp, count)
                        # 有时间戳，值却为初始化的None，会使前端出图不连续
                        series_info[series_name].pop(point.timestamp)
                    elif i % peak_per_cycle == 0:
                        series_info[series_name][point.timestamp] = count
                        series_info[series_name][tmp_max[0]] = tmp_max[1]
                        series_info[series_name][tmp_min[0]] = tmp_min[1]
                    else:
                        series_info[series_name].pop(point.timestamp)
                    # 数据量不是peak_per_cycle的倍数时，会余几个点，都添加进展示数据
                    if i in left_index:
                        series_info[series_name][point.timestamp] = count
                    i += 1

        for series_name, series in list(series_info.items()):
            s_data = []
            global_info["series"].append({"name": series_name, "data": s_data})
            last_ts = 0
            sorted_items = sorted(series.items())
            for ts, val in sorted_items:
                if val is None and ts - last_ts < self.point_interval:
                    continue
                s_data.append([ts, val])
                last_ts = ts

        if self.default_series_name and not self.origin_data:
            global_info["series"].append({"name": self.default_series_name, "data": []})
        global_info["duration"] = round(time.time() - start, 3)
        return global_info

    def timestamp_slice(self, start_timestamp, end_timestamp):
        return get_timestamp_range_list(start_timestamp, end_timestamp, self.point_interval)

    def gen_series_name(self, kv_info):
        # 优化性能, 使用将已处理过的线条名称保存下来
        cache_key = to_sorted_str(kv_info)
        if cache_key in self.series_name_cache_instance:
            return self.series_name_cache_instance[cache_key]

        prefix = self.series_name_prefix if self.series_name_prefix else ""
        if self.use_short_series_name:
            suffix = " | ".join([x for x in list(kv_info.values()) if x])
        else:
            suffix = "_".join(
                ["[{}: {}]".format(self._get_desc_by_field(field), value) for field, value in six.iteritems(kv_info)]
            )
        series_item_list = [prefix, suffix]
        series_name = self.default_series_name
        if all(series_item_list):
            series_name = " - ".join(series_item_list)
        elif any(series_item_list):
            series_name = prefix or suffix

        self.series_name_cache_instance[cache_key] = series_name
        return series_name

    def _get_val_display(self, val):
        if val is None:
            return None
        value_count = float(val) / self.conversion
        # 对于除数不为1.0的情况（如网络读写速度除数为1024.0），需要返回float型数值
        if isinstance(val, int) and int(self.conversion) == 1:
            return int(value_count)
        return round(value_count, 5) if value_count < 0.05 else round(value_count, 2)

    def _get_desc_by_field(self, field):
        raise NotImplementedError


def to_sorted_str(params):
    """
    对于用字典作为关键的时候，该方法能够一定程度保证前后计算出来的key一致
    :param params:
    :return:
    """
    if isinstance(params, dict):
        data = [(key, params[key]) for key in sorted(params.keys())]
        s = ""
        for k, v in data:
            s += "-{}:{}".format(k, to_sorted_str(v))
        return s
    elif isinstance(params, list) or isinstance(params, tuple):
        data = [to_sorted_str(x) for x in params]
        return "[%s]" % (",".join(data))
    else:
        return "%s" % params


def get_timestamp_range_list(start_time_stamp, end_time_stamp, step):
    start_time_stamp -= start_time_stamp % step
    end_time_stamp -= end_time_stamp % step
    if step > abs(time.timezone) * 1000:
        start_time_stamp += time.timezone * 1000
        end_time_stamp += time.timezone * 1000

    # todo: commit的时候总会自动导入xrange(),而xrange()又不兼容,值太大容易报错
    def temp_range(begin, stop, step):
        i = begin
        while i <= stop:
            yield i
            i += step
        yield i

    return list(temp_range(start_time_stamp, end_time_stamp + step, step))
