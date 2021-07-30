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


import datetime
import time

import arrow
from django.utils.translation import ugettext as _
from six import text_type
from six.moves import range

from bkmonitor.utils import time_tools
from monitor.constants import CONDITION_CONFIG, POINT_DELAY_COLOR

TIME_OFFSET = -time.timezone * 1000 * 0
SECONDS_OF_A_DAY = 24 * 60 * 60
SECONDS_OF_A_WEEK = 7 * SECONDS_OF_A_DAY


def cmp(a, b):
    return (a > b) - (a < b)


class DataProcessor(object):
    @staticmethod
    def get_splw_time_range(time_range):
        # 根据时间范围计算出同比的时间范围
        start, end = time_range
        # 上周同比
        return start - SECONDS_OF_A_WEEK, end - SECONDS_OF_A_WEEK

    @staticmethod
    def get_lp_time_range(time_range):
        # 根据时间范围计算出环比的时间范围
        start, end = time_range
        date_difference = (end - start) / SECONDS_OF_A_DAY
        if date_difference == 0:
            date_difference += 1
        return (start - date_difference * SECONDS_OF_A_DAY, end - date_difference * SECONDS_OF_A_DAY)

    @staticmethod
    def make_time_range_filter_dict(time_range, time_field, filter_dict=None):
        # 根据时间范围，更新过滤字典
        if filter_dict is None:
            filter_dict = {}
        if time_field == "time":
            filter_dict.update({"time__gte": time_range[0] * 1000, "time__lt": time_range[1] * 1000 + 60 * 1000})
        else:
            filter_dict["dteventtimestamp__gte"] = time_range[0] * 1000
            filter_dict["dteventtimestamp__lt"] = time_range[1] * 1000
        return filter_dict

    @staticmethod
    def thedate_first(a, b):
        a = str(a)
        a_value = 0
        b = str(b)
        b_value = 0
        if a.startswith("thedate"):
            a_value += 10
        if b.startswith("thedate"):
            b_value += 10
        return cmp(a_value, b_value)

    @staticmethod
    def make_where_list(filter_dict):
        where_list = []
        for k, v in list(filter_dict.items()):
            _k = k.split("__")
            if len(_k) > 2:
                raise Exception(_("无效的查询参数%s") % k)
            condition = "=" if len(_k) == 1 else CONDITION_CONFIG.get(_k[1])
            if condition is None:
                raise Exception(_("无效的过滤条件%s") % k)
            if isinstance(v, list):
                v = ["'%s'" % x for x in v]
                v = "(%s)" % ",".join(v)
            elif isinstance(v, text_type):
                v = "'%s'" % v
            where_list.append("{}{}{}".format(_k[0], condition, v))
        return where_list


class SeriesHandleManage(object):
    """
    series 列表数据处理
    """

    @staticmethod
    def make_full_datetime_series(
        series_list, start_timestamp, end_timestamp, step, _format="%Y%m%d%H%M", real_time=True, off_set=True
    ):
        range_iter = get_timestamp_range_list(start_timestamp, end_timestamp, step)
        time_offset = TIME_OFFSET if off_set else 0
        # 将series变成全天时间series，未到的时间点用None填充
        for series in series_list:
            new_data_list = []
            new_x_axis_list = []
            i = 0
            series_count = len(series["x_axis_list"])
            while i < series_count:
                # 将百分比变成y轴
                x_axis = str(series["x_axis_list"][i])
                y = series["data"][i]
                if isinstance(y, list):
                    y = y[1]
                if isinstance(x_axis, datetime.datetime):
                    x_axis = x_axis.strftime(_format)
                new_x_axis_list.append(time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(x_axis, _format)))
                _datetime = datetime.datetime.strptime(x_axis, _format)
                x_axis = arrow.get(time_tools.localtime(_datetime)).timestamp * 1000 + time_offset
                new_data_list.append([x_axis, y])
                i += 1
            # 插入未出现的时间序列
            none_date_list = list()
            none_x_axis_list = list()
            for point in range_iter:
                x_axis_str = time_tools.localtime(arrow.get(point // 1000).datetime).strftime("%Y-%m-%d %H:%M:%S")
                if x_axis_str not in new_x_axis_list:
                    none_x_axis_list.append(x_axis_str)
                    none_date_list.append([point + time_offset, None])
            new_data_list += none_date_list
            new_x_axis_list += none_x_axis_list
            new_x_axis_list.sort()
            series["data"] = sorted(new_data_list, key=lambda x: x[0])
            series["x_axis_list"] = new_x_axis_list
            if "percent" in series:
                del series["percent"]
        return series_list

    @staticmethod
    def make_zones_option(zones):
        zone_list = []
        for zone in zones:
            zone_list.append({"value": zone[0] * 1000})
            zone_list.append({"value": zone[1] * 1000, "color": POINT_DELAY_COLOR})
        return zone_list


def get_timestamp_range_list(start_time_stamp, end_time_stamp, step):
    start_time_stamp -= start_time_stamp % step
    end_time_stamp -= end_time_stamp % step
    if step > abs(time.timezone) * 1000:
        start_time_stamp += time.timezone * 1000
        end_time_stamp += time.timezone * 1000
    return list(range(start_time_stamp, end_time_stamp + step, step))
