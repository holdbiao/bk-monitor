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

import copy
import logging

import arrow
from django.conf import settings
from django.db.models import Q

from bkmonitor.data_source import is_build_in_process_data_source
from bkmonitor.data_source.handler import DataQueryHandler
from core.drf_resource import resource
from constants.data_source import DataSourceLabel, DataTypeLabel
from monitor_web.models import MetricListCache

logger = logging.getLogger(__name__)


def dict_to_q(filter_dict):
    """
    把前端传过来的filter_dict的格式变成django的Q
    规则：遍历每一个key:
    #         1.当val是个列表时：
    #            a.列表的内容是dict则递归调用自身，得到条件列表，用and拼接成一个条件字符串
    #            b.列表内容不是dict则根据key op val 生成一个条件字符串
    #            用or拼接上面列表生成的条件字符串
    #         2.当val不是个列表时：则根据key op val 生成一个条件字符串
    #         用and拼接上面的条件字符串
    """
    ret = None
    # dict下都是and条件
    for key, value in list(filter_dict.items()):
        if isinstance(value, list):
            _ret = _list_to_q(key, value)
        else:
            _ret = Q(**{key: value})

        if ret:
            ret &= _ret
        else:
            ret = _ret

    return ret


def _list_to_q(key, value):
    # value是list,key是上一个循环的键
    # 用于辅助dict_to_q
    ret = Q()
    operator, operator_is_false = _operator_is_exist(key)

    # 判断value是否为空
    if operator:
        if not value:
            # 没有操作符的空列表不解析,跳过
            return Q()
    else:
        if not value:
            # 有操作符的空列表解析空字符串
            return Q(**{key: ""})

    #  # list要看下里面的元素是什么类型,list条件下的三种情况,dict,list,str
    #  双层否定会表肯定,变成and条件
    if operator_is_false:
        if isinstance(value[0], dict):
            # temp_ret用来防止第一个q是空的情况,不能让空q取或
            temp_ret = dict_to_q(value[0])
            ret = (ret | temp_ret) if temp_ret else ret
            for i in value[1:]:
                ret = ret | dict_to_q(i)
        elif isinstance(value[0], list):
            temp_ret = _list_to_q(key, value[0])
            ret = (ret | temp_ret) if temp_ret else ret
            for i in value[1:]:
                ret = ret | _list_to_q(key, i)
        else:
            temp_ret = Q(**{key: value[0]})
            ret = (ret | temp_ret) if temp_ret else ret
            for i in value[1:]:
                ret = ret | Q(**{key: i})
    else:
        if isinstance(value[0], dict):
            for i in value:
                ret = ret & dict_to_q(i)
        elif isinstance(value[0], list):
            for i in value:
                ret = ret & _list_to_q(key, i)
        else:
            for i in value:
                ret = ret & Q(**{key: i})
    return ret


def _operator_is_exist(key):
    key_split = key.split("__", 1)
    # 列表下默认or条件
    operator_is_false = True
    if len(key_split) > 1:
        operator = key_split[1]
        if operator in ["neq", "!=", "not like"]:
            operator_is_false = False
    else:
        operator = ""

    return operator, operator_is_false


class ChartDataSource(object):
    """
    获取图表数据
    """

    DEFAULT_TIME_FIELD = "time"
    BK_DATA_DEFAULT_TIME_FIELD = "dtEventTimeStamp"
    BK_LOG_SEARCH_DEFAULT_TIME_FIELD = "dtEventTimeStamp"

    def __init__(
        self,
        result_table_id,
        method,
        monitor_field,
        extend_metric_fields=None,
        bk_biz_id=None,
        filter_dict=None,
        group_by_list=None,
        limit=None,
        width=12,
        # series_name没有用了
        series_name=None,
        interval=1,
        time_start=None,
        time_end=None,
        extend_fields=None,
        agg_condition=None,
        time_step=0,
        data_source_label=None,
        data_type_label=None,
        granularity=None,
        order=None,
        query_string=None,
    ):
        """
        :param result_table_id: 【必需】结果表
        :param method: 【必需】聚合方法
        :param monitor_field: 【必需】监控字段
        :param extend_metric_fields: 监控字段列表，如果改字段有值，则需要和monitor_field一样的处理逻辑，支持多指标的查询
        :param filter_dict: 过滤条件（where）
        :param agg_condition: 过滤条件（where）
        :param group_by_list: 聚合条件
        :param limit: 查询条数限制，默认为50000
        :param width: 引用栅格系统宽度概念，默认为12
        :param series_name: 指标名，用于图表展示
        :param interval: 采集间隔
        :param time_start: 开始时间 timestamp 单位:ms（非必填，如未指定则默认展示24小时内数据）
        :param time_end: 结束时间 timestamp 单位:ms（非必填，如未指定则默认展示24小时内数据）
        :param granularity: 默认的粒度 minute,传minute0则表示没有粒度
        :param order: 按时间排序方法
        """
        # slimit 支持
        self._slimit = None
        # 触发限制
        self._slimit_conflict = False
        # 结果表
        self._result_table_id = str(result_table_id)
        # 聚合方法
        self._method = method or "avg"
        # 监控字段
        self.metric_field = monitor_field
        # 可选，监控字段列表，为了支持多指标字段查询
        self.extend_metric_fields = extend_metric_fields or []
        # 业务id
        self.bk_biz_id = bk_biz_id or "0"
        # 过滤条件
        # format:{'time__gt':'10m', 'ip':['127.0.0.1', '127.0.0.2']}
        self.filter_dict = filter_dict or {}
        # format:
        # [{u'key': u'bk_cloud_id', u'method': u'eq', u'value': u'2'},
        #  {u'condition': u'and', u'key': u'ip', u'value': u'127.0.0.1', u'method': u'eq'},
        #  {u'condition': u'or', u'key': u'bk_cloud_id', u'value': u'2', u'method': u'eq'},
        # ]
        self.agg_condition = agg_condition or []
        # 聚合字段
        self.group_by_list = set(group_by_list or []) if isinstance(group_by_list, list) else set()
        # 结果个数限制
        if (data_source_label, data_type_label) in (
            (DataSourceLabel.CUSTOM, DataTypeLabel.EVENT),
            (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.LOG),
        ):
            self.limit = None
        else:
            self.limit = limit or settings.SQL_MAX_LIMIT
        # 宽度
        self.width = width or 12
        # 指标名
        self.series_name = series_name or ""
        # 采集间隔
        self.interval = interval or 1
        # 时间粒度
        self.granularity = granularity
        # 时间排序
        self.order = order or "asc"
        # 查询语句
        self.query_string = query_string

        # 接入日志
        self.extend_fields = extend_fields or {}
        self.data_source_label = data_source_label
        self.data_type_label = data_type_label

        # 起始时间 timestamp 单位:ms
        self.time_start = time_start or None
        # 终止时间 timestamp 单位:ms
        self.time_end = time_end or None
        if not (self.time_start and self.time_end):
            # 如未指定时间范围，则默认展示近24小时数据
            self.time_end = arrow.utcnow().timestamp * 1000
            self.time_start = self.time_end - (24 * 3600 * 1000)

        # 计算出自适应的时间粒度
        time_range_minutes = (self.time_end - self.time_start) // 1000 // 60
        max_point_count = time_range_minutes // self.interval
        # 抽样倍率
        minute_ratio = max_point_count // (settings.POINT_COEFFICIENT * self.width // 12)
        # 如果前端指定了数据点的时间间隔，则以前端传入的为准
        # 如果前端未指定，则由后台根据指定的时间范围，计算出自适应的时间粒度
        minute_ratio = int(minute_ratio // self.interval * self.interval) + 1
        # cal_point_interval 仅用于生成抽样列表，不能用抽样比例去覆盖实际聚合的时间粒度，否则会造成数据失真
        self.cal_point_interval = max([minute_ratio * self.interval, self.interval])
        if not self.granularity:
            self.granularity = "minute%d" % self.interval
        #  对于某些不需要group by的情况给minute0就不会聚合了
        if self.granularity != "minute0":
            self.group_by_list.add(self.granularity)

        self.time_field = self.extend_fields.get("time_field")
        if not self.time_field:
            if self.data_source_label == DataSourceLabel.BK_DATA:
                self.time_field = self.BK_DATA_DEFAULT_TIME_FIELD
            elif self.data_source_label == DataSourceLabel.BK_LOG_SEARCH:
                self.time_field = self.BK_LOG_SEARCH_DEFAULT_TIME_FIELD
            else:
                self.time_field = self.DEFAULT_TIME_FIELD
        self.extend_filter_dict()

    def extend_filter_dict(self):
        # 计算平台和自定义时序的表不需要增加业务ID的条件
        if self.query_type not in ["bk_data", "custom_time_series"] or is_build_in_process_data_source(
            self.result_table_id
        ):
            self.filter_dict.update({"bk_biz_id": str(self.bk_biz_id)})

    @property
    def result_table_id(self):
        """
        混合云版 result_table_id 转换
        """
        if self.data_type_label == DataTypeLabel.LOG:
            rt_id = self._result_table_id
        else:
            rt_id = resource.commons.trans_bkcloud_rt_bizid(self._result_table_id)
        return rt_id

    def _get_value_fields(self):
        value_fields = []
        for field in self.values:
            if field == self.time_field:
                continue

            if self._method:
                if field == self.metric_field:
                    value_fields.append(
                        "%(method)s(%(field)s) as _value_" % dict(field=field, method=self._method.upper())
                    )
                else:
                    value_fields.append(
                        "%(method)s(%(field)s) as %(field)s" % dict(field=field, method=self._method.upper())
                    )
            else:
                value_fields.append(field)
        return value_fields

    @property
    def query_type(self):
        data_type = {
            DataSourceLabel.BK_MONITOR_COLLECTOR: {
                DataTypeLabel.LOG: "keywords",
                DataTypeLabel.TIME_SERIES: "time_series",
            },
            DataSourceLabel.BK_LOG_SEARCH: {DataTypeLabel.LOG: "log_search", DataTypeLabel.TIME_SERIES: "log_search"},
            DataSourceLabel.CUSTOM: {
                DataTypeLabel.TIME_SERIES: "custom_time_series",
                DataTypeLabel.EVENT: "custom_event",
            },
            DataSourceLabel.BK_DATA: {DataTypeLabel.LOG: "bk_data", DataTypeLabel.TIME_SERIES: "bk_data"},
        }
        return data_type.get(self.data_source_label, {}).get(self.data_type_label, None)

    def get_queryset(self):
        """
        根据DB类型，返回结果queryset数据
        """
        result_table_id = self.result_table_id
        # 缺少了信息就去缓存表查
        if (self.query_type is None) or (
            self.data_source_label == DataSourceLabel.BK_LOG_SEARCH
            and self.data_type_label == DataTypeLabel.TIME_SERIES
            and not self.extend_fields
        ):
            # result_table_id有时加了业务ID有时没有,所以统一去查
            result_table_id_backend = str(self.bk_biz_id) + "_" + result_table_id
            temp = (
                MetricListCache.objects.filter(
                    data_source_label=self.data_source_label,
                    data_type_label=self.data_type_label,
                    result_table_id__in=[result_table_id, result_table_id_backend],
                    bk_biz_id__in=[0, self.bk_biz_id],
                    metric_field=self.metric_field,
                )
                .values("data_source_label", "data_type_label", "extend_fields")
                .first()
            )
            if not temp:
                # raise EmptyQueryException(_("查询缓存表无数据"))
                # 此处是为了兼容升级到3.2之后，新链路的老结果表
                self.extend_fields = {}
                self.data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
                self.data_type_label = DataTypeLabel.TIME_SERIES
            else:
                self.extend_fields = temp["extend_fields"]
                self.data_source_label = temp["data_source_label"]
                self.data_type_label = temp["data_type_label"]

        if self.query_type == "bk_data":
            # 均值的查询方法调整
            if self._method == "MEAN":
                self._method = "avg"

        self.index_set_id = self.extend_fields.get("index_set_id")
        # 兼容日志数据查询
        if self.data_source_label == DataSourceLabel.BK_LOG_SEARCH:
            if self.data_type_label == DataTypeLabel.LOG:
                self.index_set_id = self.result_table_id
                self.metric_field = "_index"
            self.limit = 1

        if "time_field" in self.extend_fields:
            self.time_field = self.extend_fields["time_field"]
        self.values = [self.metric_field, self.time_field]
        self.values.extend(self.extend_metric_fields)
        self.values.extend(self.extend_fields.get("values", []))
        qs_list = []
        if self.query_type == "keywords":
            filter_dict_list = self.clean_filter()
            for query_dict in filter_dict_list:
                qs = self.get_query_handler(result_table_id, "ip")
                if query_dict:
                    qs = qs.filter(**query_dict)
                qs_list.append(qs)
        else:
            qs = self.get_query_handler(result_table_id)

            if self.filter_dict:
                qs = qs.filter(dict_to_q(self.filter_dict))

            if self.index_set_id:
                if self._method == "MEAN":
                    self._method = "avg"
                qs = qs.dsl_index_set_id(self.index_set_id)

            if self.query_string:
                qs = qs.dsl_raw_query_string(self.query_string)

            qs_list.append(qs)

        return qs_list

    def get_filter_dict(self):
        filter_dict = copy.deepcopy(self.filter_dict)
        filter_dict.pop("dimensions", None)
        if "where" not in filter_dict:
            return [filter_dict]
        search_list = filter_dict.pop("where")
        ret_list = []
        for search_item in search_list:
            query_dict = copy.deepcopy(filter_dict)
            query_dict.update(search_item)
            ret_list.append(query_dict)
        return ret_list

    def clean_filter(self):
        filter_list = []
        ret_list = self.get_filter_dict()
        for filter_dict in ret_list:
            tmp = {}
            for key, value in filter_dict.items():
                if key in ["bk_collect_config_id", "where"]:
                    continue
                if key in ["event_name", "target"] or key.startswith("dimensions."):
                    tmp[key] = value
                else:
                    tmp["dimensions.{}".format(key)] = value
            filter_list.append(tmp)
        return filter_list

    def get_query_handler(self, result_table_id, target_type="ip"):
        q = DataQueryHandler(self.data_source_label, self.data_type_label)
        qs = (
            q.table(result_table_id)
            .target_type(target_type)
            .time_field(self.time_field)
            .group_by(*self.group_by_list)
            .limit(self.limit)
            .order_by("{} {}".format(self.time_field, self.order))
        )

        if self.agg_condition:
            qs = qs.agg_condition(self.agg_condition)
        qs = qs.values(*self._get_value_fields())
        return qs

    def query_record(self, time_start=None, time_end=None):
        """
        不传时间默认查一天内数据
        """
        time_start = time_start or self.time_start
        time_end = time_end or self.time_end

        raw_data = []
        queryset_list = self.get_queryset()

        gte_field = "{}__gte".format(self.time_field)
        lte_field = "{}__lt".format(self.time_field)

        for queryset in queryset_list:
            qs = queryset.filter(**{gte_field: time_start, lte_field: time_end})
            if self._slimit is not None:
                qs = qs.slimit(self._slimit)
            raw_data.extend(qs.raw_data)

        # 计算平台聚合周期大于1，需要修正dtEventTimeStamp
        if self.data_source_label == DataSourceLabel.BK_DATA and self.granularity != "minute0":
            raw_data = self.post_query_handle(raw_data)

        dimension_set = set()
        # 填充统一时间字段
        for record in raw_data:
            # 统计series数量
            dimension_set.add(
                "|".join(
                    [
                        str(record.get(group_field, ""))
                        for group_field in self.group_by_list
                        if not group_field.startswith("minute")
                    ]
                )
            )
            if self.time_field not in record:
                continue
            record["_time_"] = record[self.time_field]

        if self._slimit is not None and len(dimension_set) == self._slimit:
            # 标记series超限
            self._slimit_conflict = True

        # 过滤时间字段为空的数据
        raw_data = [record for record in raw_data if record["_time_"]]

        return raw_data

    def post_query_handle(self, data_list):
        window = 60 * 1000 * self.interval
        for item in data_list:
            item[self.time_field] = item[self.time_field] // window * window
        return data_list

    def slimit(self, s):
        self._slimit = s

    @property
    def slimit_conflict(self):
        return self._slimit_conflict
