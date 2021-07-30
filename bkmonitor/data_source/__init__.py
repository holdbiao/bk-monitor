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
from abc import ABCMeta
from collections import defaultdict
from typing import List, Optional, Dict, Type, Tuple

from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _lazy, gettext as _

from bkmonitor.data_source.models.query import DataQuery
from bkmonitor.utils.common_utils import to_bk_data_rt_id
from bkmonitor.utils.range import load_agg_condition_instance
from constants.data_source import DataSourceLabel, DataTypeLabel, RECOVERY


__all__ = ["DataQuery", "is_build_in_process_data_source", "load_data_source"]

from constants.strategy import AGG_METHOD_REAL_TIME, SPLIT_DIMENSIONS


def is_build_in_process_data_source(table_id: str):
    return table_id in ["process.perf", "process.port"]


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
    list_filter = {}
    single_filter = {}
    for key, value in filter_dict.items():
        if isinstance(value, list):
            list_filter[key] = value
        else:
            single_filter[key] = value

    if single_filter:
        ret = Q(**single_filter)

    for key, value in list_filter.items():
        _ret = _list_to_q(key, value)
        if not _ret.children:
            continue

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


class DataSource(metaclass=ABCMeta):
    data_source_label = ""
    data_type_label = ""

    DEFAULT_TIME_FIELD = "time"
    ADVANCE_CONDITION_METHOD = ["reg", "nreg", "include", "exclude"]

    def __init__(self, *args, name="", **kwargs):
        self.name = name

    @classmethod
    def query_data(cls, *args, **kwargs) -> List:
        return []

    @classmethod
    def query_dimensions(cls, *args, **kwargs) -> List:
        return []

    @classmethod
    def query_log(cls, *args, **kwargs) -> Tuple[List, int]:
        return [], 0

    @classmethod
    def init_by_rt_query_config(cls, rt_query_config: Dict, *args, **kwargs) -> "DataSource":
        return cls()

    @classmethod
    def _get_queryset(
        cls,
        *,
        metrics: List[Dict] = None,
        select: List[str] = None,
        table: str = None,
        agg_condition: List = None,
        where: Dict = None,
        group_by: List[str] = None,
        index_set_id: int = None,
        query_string: str = "",
        limit: int = None,
        slimit: int = None,
        order_by: List[str] = None,
        time_field: str = None,
        interval: int = None,
        start_time: int = None,
        end_time: int = None,
    ):
        from bkmonitor.data_source.handler import DataQueryHandler

        metrics = metrics or []
        select = select or []
        agg_condition = agg_condition or []
        where = where.copy() or {}
        group_by = (group_by or [])[:]
        order_by = order_by or [f"{time_field} desc"]
        time_field = time_field or cls.DEFAULT_TIME_FIELD

        # 过滤条件中添加时间字段
        time_filter = {}
        if start_time:
            time_filter[f"{time_field}__gte"] = start_time
        if end_time:
            time_filter[f"{time_field}__lt"] = end_time

        # 如果存在高级过滤条件，不再查询时提供过滤条件，并且在聚合维度中添加过滤字段
        has_advance_method = False
        condition_fields = set()
        for condition in agg_condition:
            condition_fields.add(condition["key"])
            if condition["method"] in cls.ADVANCE_CONDITION_METHOD:
                has_advance_method = True
        if has_advance_method:
            agg_condition = []
            for field in condition_fields:
                if field in group_by:
                    continue
                group_by.append(field)

        # 添加时间聚合字段
        if interval:
            group_by.append(f"minute{interval}")

        q = DataQueryHandler(cls.data_source_label, cls.data_type_label)
        if where:
            q = q.where(dict_to_q(where))

        if time_filter:
            q = q.where(**time_filter)

        return (
            q.select(*select)
            .metrics(metrics)
            .table(table)
            .agg_condition(agg_condition)
            .group_by(*group_by)
            .dsl_index_set_id(index_set_id)
            .dsl_raw_query_string(query_string)
            .order_by(*order_by)
            .limit(limit)
            .slimit(slimit)
            .time_field(time_field)
        )

    def _format_time_series_records(self, records: List[Dict]):
        """
        数据标准化
        """

        if self.interval:
            interval = self.interval * 60 * 1000
        else:
            interval = 1

        for record in records:
            # 去除时间为空的数据
            if not record.get(self.time_field):
                continue

            # 时间字段统一
            record["_time_"] = record[self.time_field] // interval * interval
            del record[self.time_field]

        return records

    def _filter_by_advance_method(self, records: List):
        """
        根据高级条件过滤数据
        """
        for condition in self.where:
            if condition["method"] not in self.ADVANCE_CONDITION_METHOD:
                continue
            condition_filter = load_agg_condition_instance(self.where)
            return [record for record in records if condition_filter.is_match(record)]
        return records


class TimeSeriesDataSource(DataSource):
    data_source_label = ""
    data_type_label = ""

    DEFAULT_TIME_FIELD = "time"

    @classmethod
    def init_by_rt_query_config(cls, rt_query_config: Dict, *args, bk_biz_id=0, name="", **kwargs):
        """
        根据查询配置实例化
        """
        extend_fields = rt_query_config.get("extend_fields", {})
        if not isinstance(extend_fields, Dict):
            extend_fields = {}

        # 过滤空维度
        agg_dimension = [dimension for dimension in rt_query_config.get("agg_dimension", []) if dimension]
        agg_method = rt_query_config["agg_method"]

        # 指标设置
        metrics = []
        if rt_query_config.get("metric_field"):
            metrics.append({"field": rt_query_config["metric_field"], "method": agg_method})
        else:
            metrics.append({"field": "_index", "method": "COUNT"})

        for extend_metric_field in extend_fields.get("values", []):
            metrics.append({"field": extend_metric_field, "method": agg_method})

        time_field = extend_fields.get("time_field")
        index_set_id = extend_fields.get("index_set_id")

        return cls(
            name=name,
            table=rt_query_config["result_table_id"],
            metrics=metrics,
            interval=rt_query_config.get("agg_interval", 60),
            group_by=agg_dimension,
            where=rt_query_config.get("agg_condition", []),
            time_field=time_field,
            index_set_id=index_set_id,
            query_string=rt_query_config.get("keywords_query_string", ""),
            bk_biz_id=bk_biz_id,
        )

    def _is_system_disk(self):
        return (
            self.table == settings.FILE_SYSTEM_TYPE_RT_ID
            and self.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR
            and self.data_type_label == DataTypeLabel.TIME_SERIES
        )

    def _is_system_net(self):
        return (
            self.table == settings.SYSTEM_NET_GROUP_RT_ID
            and self.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR
            and self.data_type_label == DataTypeLabel.TIME_SERIES
        )

    def __init__(
        self,
        *args,
        table,
        metrics: List = None,
        interval: int = 0,
        where: List = None,
        filter_dict: Dict = None,
        group_by: List[str] = None,
        order_by: List[str] = None,
        time_field: str = None,
        index_set_id: int = None,
        query_string: str = "",
        **kwargs,
    ):
        super(TimeSeriesDataSource, self).__init__(*args, **kwargs)
        self.table = table
        self.metrics = metrics or []
        self.interval = interval // 60
        self.where = where or []
        self.filter_dict = filter_dict or {}
        self.group_by = group_by or []
        self.time_field = time_field or self.DEFAULT_TIME_FIELD
        self.index_set_id = index_set_id
        self.query_string = query_string
        self.order_by = order_by or [f"{self.time_field} desc"]

        # 过滤空维度
        self.group_by = [d for d in self.group_by if d]

    def query_data(
        self,
        start_time: int = None,
        end_time: int = None,
        limit: Optional[int] = settings.SQL_MAX_LIMIT,
        slimit: Optional[int] = None,
        *args,
        **kwargs,
    ) -> List:
        filter_dict = self.filter_dict.copy()
        if self._is_system_disk():
            filter_dict[f"{settings.FILE_SYSTEM_TYPE_FIELD_NAME}__neq"] = settings.FILE_SYSTEM_TYPE_IGNORE
        elif self._is_system_net():
            value = [condition["sql_statement"] for condition in settings.ETH_FILTER_CONDITION_LIST]
            filter_dict[f"{settings.SYSTEM_NET_GROUP_FIELD_NAME}__neq"] = value

        q = self._get_queryset(
            metrics=self.metrics,
            table=self.table,
            index_set_id=self.index_set_id,
            query_string=self.query_string,
            agg_condition=self.where,
            group_by=self.group_by,
            interval=self.interval,
            where=filter_dict,
            time_field=self.time_field,
            order_by=self.order_by,
            limit=limit,
            slimit=slimit,
            start_time=start_time,
            end_time=end_time,
        )

        records = q.raw_data
        records = self._format_time_series_records(records)
        return self._filter_by_advance_method(records)

    def query_dimensions(
        self,
        dimension_field: str,
        start_time: int = None,
        end_time: int = None,
        limit: Optional[int] = None,
        slimit: Optional[int] = None,
        *args,
        **kwargs,
    ) -> List:
        q = self._get_queryset(
            metrics=self.metrics[:1],
            table=self.table,
            query_string=self.query_string,
            index_set_id=self.index_set_id,
            agg_condition=self.where,
            group_by=[dimension_field],
            where=self.filter_dict,
            limit=limit,
            slimit=slimit,
            time_field=self.time_field,
            order_by=self.order_by,
            start_time=start_time,
            end_time=end_time,
        )
        records = self._filter_by_advance_method(q.raw_data)
        return [record[dimension_field] for record in records]

    @property
    def metric_display(self):
        field = self.name or self.metrics[0]["field"]
        method = self.metrics[0].get("method", "").lower()
        if method and method != AGG_METHOD_REAL_TIME:
            return f"{method}({field})"
        else:
            return field


class BkMonitorTimeSeriesDataSource(TimeSeriesDataSource):
    """
    监控采集时序型数据源
    """

    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self, *args, **kwargs):
        super(BkMonitorTimeSeriesDataSource, self).__init__(*args, **kwargs)

        if kwargs.get("bk_biz_id"):
            self.filter_dict["bk_biz_id"] = str(kwargs["bk_biz_id"])

        if settings.IS_ACCESS_BK_DATA and self._is_cmdb_level_query(
            where=self.where, filter_dict=self.filter_dict, group_by=self.group_by
        ):
            self.time_field = BkdataTimeSeriesDataSource.DEFAULT_TIME_FIELD
            self.order_by = [f"{self.time_field} desc"]

    @classmethod
    def _is_cmdb_level_query(cls, where: List = None, filter_dict: Dict = None, group_by: List[str] = None):
        where = where or []
        filter_dict = filter_dict or {}
        group_by = group_by or []
        fields = {condition["key"] for condition in where} | set(filter_dict.keys()) | set(group_by)
        # 只要字段中包含有bk_obj_id 或者 bk_inst_id则转到计算平台查询
        return fields & set(SPLIT_DIMENSIONS)

    @classmethod
    def _get_queryset(
        cls, *, table: str = None, agg_condition: List = None, where: Dict = None, group_by: List[str] = None, **kwargs
    ):
        if settings.IS_ACCESS_BK_DATA and cls._is_cmdb_level_query(
            where=agg_condition, filter_dict=where, group_by=group_by
        ):
            raw_table, _, _ = table.partition("_cmdb_level")
            replace_table_id = to_bk_data_rt_id(raw_table, settings.BK_DATA_CMDB_SPLIT_TABLE_SUFFIX)
            return BkdataTimeSeriesDataSource._get_queryset(
                table=replace_table_id, agg_condition=agg_condition, where=where, group_by=group_by, **kwargs
            )

        return super(BkMonitorTimeSeriesDataSource, cls)._get_queryset(
            table=table, agg_condition=agg_condition, where=where, group_by=group_by, **kwargs
        )


class BkdataTimeSeriesDataSource(TimeSeriesDataSource):
    """
    计算平台时序型数据源
    """

    data_source_label = DataSourceLabel.BK_DATA
    data_type_label = DataTypeLabel.TIME_SERIES

    DEFAULT_TIME_FIELD = "dtEventTimeStamp"

    @classmethod
    def _get_queryset(cls, *, metrics: List[Dict] = None, **kwargs):
        # 计算平台查询的指标使用反引号，避免与关键字冲突
        metrics = copy.deepcopy(metrics)
        for metric in metrics:
            if not metric["field"].startswith("`"):
                metric["field"] = f"`{metric['field']}`"

            if metric.get("alias") and not metric["alias"].startswith("`"):
                metric["alias"] = f"`{metric['alias']}`"

        return super(BkdataTimeSeriesDataSource, cls)._get_queryset(metrics=metrics, **kwargs)


class CustomTimeSeriesDataSource(TimeSeriesDataSource):
    """
    自定义时序型数据源
    """

    data_source_label = DataSourceLabel.CUSTOM
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self, *args, **kwargs):
        super(CustomTimeSeriesDataSource, self).__init__(*args, **kwargs)
        if is_build_in_process_data_source(self.table) and kwargs.get("bk_biz_id"):
            self.filter_dict["bk_biz_id"] = kwargs["bk_biz_id"]


class LogSearchTimeSeriesDataSource(TimeSeriesDataSource):
    """
    日志时序型数据源
    """

    data_source_label = DataSourceLabel.BK_LOG_SEARCH
    data_type_label = DataTypeLabel.TIME_SERIES

    DEFAULT_TIME_FIELD = "dtEventTimeStamp"

    def __init__(self, *args, **kwargs):
        super(LogSearchTimeSeriesDataSource, self).__init__(*args, **kwargs)

        # 条件方法替换
        condition_mapping = {
            "eq": "is one of",
            "neq": "is not one of",
        }
        for condition in self.where:
            condition["method"] = condition_mapping.get(condition["method"]) or condition["method"]

    def query_data(
        self,
        start_time: int = None,
        end_time: int = None,
        *args,
        **kwargs,
    ) -> List:
        # 日志查询中limit仅能限制返回的原始日志数量，因此固定为1
        if "limit" in kwargs:
            kwargs.pop("limit")

        return super(LogSearchTimeSeriesDataSource, self).query_data(start_time, end_time, limit=1, *args, **kwargs)

    def query_dimensions(
        self,
        dimension_field: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        *args,
        **kwargs,
    ) -> List:
        # 日志查询中limit仅能限制返回的原始日志数量，因此固定为1
        if "limit" in kwargs:
            kwargs.pop("limit")

        return super(LogSearchTimeSeriesDataSource, self).query_dimensions(
            dimension_field, start_time, end_time, limit=1, *args, **kwargs
        )[:limit]

    def query_log(
        self,
        start_time: int = None,
        end_time: int = None,
        limit: Optional[int] = None,
        *args,
        **kwargs,
    ) -> List:
        q = self._get_queryset(
            query_string=self.query_string,
            index_set_id=self.index_set_id,
            agg_condition=self.where,
            where=self.filter_dict,
            time_field=self.time_field,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        data = q.original_data
        total = data["hits"]["total"]
        if isinstance(total, dict):
            total = total["value"]

        result = [record["_source"] for record in data["hits"]["hits"][:limit]]
        return result, total


class LogSearchLogDataSource(LogSearchTimeSeriesDataSource):
    """
    日志关键字数据源
    """

    data_source_label = DataSourceLabel.BK_LOG_SEARCH
    data_type_label = DataTypeLabel.LOG

    DEFAULT_TIME_FIELD = "dtEventTimeStamp"

    def __init__(self, *args, **kwargs):
        super(LogSearchLogDataSource, self).__init__(*args, **kwargs)
        self.metrics = [{"field": "_index", "method": "COUNT"}]

    @property
    def metric_display(self):
        return _("{}分钟内匹配到关键字次数").format(self.interval)


class BkMonitorLogDataSource(DataSource):
    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.LOG

    INNER_DIMENSIONS = ["event_name", "target"]
    DISTINCT_METHODS = {"AVG", "SUM", "COUNT"}
    METHOD_DESC = {"avg": _lazy("均值"), "sum": _lazy("总和"), "max": _lazy("最大值"), "min": _lazy("最小值"), "count": ""}

    @classmethod
    def init_by_rt_query_config(cls, rt_query_config: Dict, name="", *args, **kwargs):
        # 过滤空维度
        agg_dimension = [dimension for dimension in rt_query_config.get("agg_dimension", []) if dimension]

        # 统计聚合目标节点
        topo_nodes = defaultdict(list)
        if rt_query_config.get("target") and rt_query_config["target"][0]:
            target = rt_query_config["target"][0][0]
            if target["field"] in ["host_topo_node", "service_topo_node"]:
                for value in target["value"]:
                    topo_nodes[value["bk_obj_id"]].append(value["bk_inst_id"])

        # 指标设置
        metrics = [{"field": "event.count", "method": rt_query_config["agg_method"]}]

        extend_fields = rt_query_config.get("extend_fields", {})
        if not isinstance(extend_fields, Dict):
            extend_fields = {}
        time_field = extend_fields.get("time_field")

        return cls(
            name=name,
            table=rt_query_config["result_table_id"],
            metrics=metrics,
            interval=rt_query_config.get("agg_interval", 60),
            group_by=agg_dimension,
            where=rt_query_config.get("agg_condition", []),
            time_field=time_field,
            topo_nodes=topo_nodes,
        )

    def __init__(
        self,
        *,
        table,
        metrics: List[Dict] = None,
        interval: int = 0,
        where: List = None,
        filter_dict: Dict = None,
        group_by: List[str] = None,
        time_field: str = None,
        topo_nodes: Dict[str, List] = None,
        **kwargs,
    ):
        super(BkMonitorLogDataSource, self).__init__(**kwargs)
        self.metrics = metrics or []
        self.table = table
        self.interval = interval // 60
        self.where = where or []
        self.filter_dict = filter_dict or {}
        self.group_by = group_by or []
        self.time_field = time_field or self.DEFAULT_TIME_FIELD

        # 过滤空维度
        self.group_by = [d for d in self.group_by if d]

        # 如果维度中包含实例，则不按节点聚合
        if {"bk_target_ip", "bk_target_service_instance_id"} & set(self.group_by):
            topo_nodes = {}
        self.topo_nodes = topo_nodes or {}

    def is_dimensions_field(self, field: str) -> bool:
        """
        判断是否需要补全dimensions前缀
        """
        return field not in self.INNER_DIMENSIONS and not field.startswith("dimensions")

    def _get_metrics(self):
        """
        metric字段处理
        """
        metrics = self.metrics.copy()
        methods = {metric.get("method", "").upper() for metric in self.metrics}
        if methods & self.DISTINCT_METHODS:
            metrics.append({"field": "dimensions.bk_module_id", "method": "distinct", "alias": "distinct"})
        return metrics

    def _get_group_by(self, bk_obj_id: str = None) -> List:
        """
        聚合维度处理，判断是否需要按节点聚合
        """
        group_by = self.group_by[:]

        # 去除补全的特殊维度
        if "bk_obj_id" in group_by:
            group_by.remove("bk_obj_id")
        if "bk_inst_id" in group_by:
            group_by.remove("bk_inst_id")

        # 如果没有实例维度，则按节点聚合
        if not ({"bk_target_ip", "bk_target_service_instance_id"} & set(group_by)) and bk_obj_id:
            group_by.append(f"bk_{bk_obj_id}_id")

        # 维度补充dimensions.前缀
        return [
            f"dimensions.{dimension}" if self.is_dimensions_field(dimension) else dimension for dimension in group_by
        ]

    def _get_where(self):
        """
        非内置维度需要补充dimensions.
        """
        where = copy.deepcopy(self.where)
        for condition in where:
            if self.is_dimensions_field(condition["key"]):
                condition["key"] = f"dimensions.{condition['key']}"

        # 去除采集配置ID条件
        where = [c for c in where if c["key"] != "dimensions.bk_collect_config_id"]
        return where

    def _add_dimension_prefix(self, filter_dict: Dict) -> Dict:
        """
        为filter_dict添加维度前缀
        """
        new_filter_dict = {}

        # 将bk_inst_id和bk_obj_id过滤条件调整真实的层级维度
        if "bk_inst_id" in filter_dict and "bk_obj_id" in filter_dict:
            new_filter_dict[f"dimensions.bk_{filter_dict['bk_obj_id']}_id"] = filter_dict["bk_inst_id"]

        for key, value in filter_dict.items():
            if isinstance(value, (list, Tuple)) and value and isinstance(value[0], Dict):
                new_filter_dict[key] = [self._add_dimension_prefix(v) for v in value]
                continue

            if key in ["bk_collect_config_id", "bk_inst_id", "bk_obj_id"]:
                continue

            if self.is_dimensions_field(key):
                key = f"dimensions.{key}"
            new_filter_dict[key] = value
        return new_filter_dict

    def _get_filter_dict(self, bk_obj_id: str = None, bk_inst_ids: List = None) -> Dict:
        """
        过滤条件按target过滤及添加dimensions.前缀
        """
        filter_dict = self.filter_dict.copy() if self.filter_dict else {}
        if bk_obj_id and bk_inst_ids:
            filter_dict[f"bk_{bk_obj_id}_id"] = bk_inst_ids

        return self._add_dimension_prefix(filter_dict)

    def _distinct_calculate(self, records: List[Dict], bk_obj_id: str = None) -> List:
        """
        根据聚合方法和bk_module_id的重复数量计算实际的值
        """
        group_by = self._get_group_by(bk_obj_id)
        group_by.append(self.time_field)

        metric_values = {}
        dimension_count = defaultdict(lambda: 0)
        for record in records:
            key = tuple((dimension, record[dimension]) for dimension in group_by)
            dimension_count[key] += 1

            # 维度初始化
            if key not in metric_values:
                metric_values[key] = defaultdict(lambda: 0)

            for metric in self.metrics:
                method = metric.get("method", "")
                alias = metric.get("alias") or metric["field"]

                if method in ["COUNT", "SUM"]:
                    record[alias] /= record["distinct"] or 1

                if method in self.DISTINCT_METHODS:
                    metric_values[key][alias] += record[alias] or 0
                else:
                    metric_values[key][alias] = record[alias] or 0

        # 平均值计算
        for metric in self.metrics:
            method = metric.get("method", "")
            alias = metric.get("alias") or metric["field"]

            if method != "AVG":
                continue

            for key, value in metric_values.items():
                value[alias] /= dimension_count[key]

        # 只保留需要的维度和指标
        new_result = []
        for key, value in metric_values.items():
            record = {dimension: dimension_value for dimension, dimension_value in key}
            record.update(value)
            new_result.append(record)

        return new_result

    @staticmethod
    def _remove_dimensions_prefix(data: List, bk_obj_id=None):
        """请求结果中去除dimensions.前缀"""
        result = []
        for record in data:
            new_record = {}
            for key, value in record.items():
                if key.startswith("dimensions."):
                    key = key[11:]

                if key == f"bk_{bk_obj_id}_id":
                    new_record["bk_obj_id"] = bk_obj_id
                    new_record["bk_inst_id"] = value
                else:
                    new_record[key] = value

            result.append(new_record)
        return result

    def query_data(
        self,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        *args,
        **kwargs,
    ) -> List:
        metrics = self._get_metrics()
        where = self._get_where()

        topo_nodes = self.topo_nodes.copy()
        if not topo_nodes:
            topo_nodes[""] = []

        records = []
        for bk_obj_id, bk_inst_ids in topo_nodes.items():
            group_by = self._get_group_by(bk_obj_id)
            filter_dict = self._get_filter_dict(bk_obj_id, bk_inst_ids)

            if self.interval:
                group_by.append(f"minute{self.interval}")
            if "dimensions.bk_target_ip" not in group_by:
                group_by.append("dimensions.bk_target_ip")
            if "dimensions.bk_target_cloud_id" not in group_by:
                group_by.append("dimensions.bk_target_cloud_id")

            q = self._get_queryset(
                metrics=metrics,
                table=self.table,
                agg_condition=where,
                group_by=group_by,
                interval=self.interval,
                where=filter_dict,
                limit=1,
                time_field=self.time_field,
                start_time=start_time,
                end_time=end_time,
            )
            data = self._distinct_calculate(q.raw_data, bk_obj_id)
            data = self._remove_dimensions_prefix(data, bk_obj_id)
            records.extend(data)
        records = self._filter_by_advance_method(records)
        records = self._format_time_series_records(records)
        return records[:limit]

    def query_dimensions(
        self,
        dimension_field: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        *args,
        **kwargs,
    ) -> List:

        if self.is_dimensions_field(dimension_field):
            dimension_field = f"dimensions.{dimension_field}"

        q = self._get_queryset(
            metrics=self.metrics[:1],
            table=self.table,
            agg_condition=self._get_where(),
            group_by=[dimension_field],
            where=self._get_filter_dict(),
            limit=1,
            time_field=self.time_field,
            start_time=start_time,
            end_time=end_time,
        )
        records = self._remove_dimensions_prefix(q.raw_data)
        records = self._filter_by_advance_method(records)
        return [record[dimension_field] for record in records][:limit]

    def query_log(
        self, start_time: int = None, end_time: int = None, limit: int = None, *args, **kwargs
    ) -> Tuple[List, int]:

        q = self._get_queryset(
            table=self.table,
            agg_condition=self._get_where(),
            where=self._get_filter_dict(),
            limit=limit,
            time_field=self.time_field,
            start_time=start_time,
            end_time=end_time,
        )
        data = q.original_data
        total = data["hits"]["total"]
        if isinstance(total, dict):
            total = total["value"]

        result = [record["_source"] for record in data["hits"]["hits"][:limit]]
        return result, total

    @property
    def metric_display(self):
        method = self.metrics[0]["method"].lower()
        return _("{}分钟内接收到事件次数{}").format(self.interval, self.METHOD_DESC[method])


class CustomEventDataSource(BkMonitorLogDataSource):
    """
    自定义事件数据源
    """

    data_source_label = DataSourceLabel.CUSTOM
    data_type_label = DataTypeLabel.EVENT
    INNER_DIMENSIONS = ["target", "event_name"]

    @classmethod
    def init_by_rt_query_config(cls, rt_query_config: Dict, name="", *args, **kwargs):
        # 过滤空维度
        agg_dimension = [dimension for dimension in rt_query_config.get("agg_dimension", []) if dimension]

        extend_fields = rt_query_config.get("extend_fields", {})
        if not isinstance(extend_fields, Dict):
            extend_fields = {}
        time_fields = extend_fields.get("time_field")
        custom_event_name = extend_fields.get("custom_event_name", "")

        return cls(
            name=name,
            metrics=[{"field": "_index", "method": "COUNT"}],
            table=rt_query_config["result_table_id"],
            interval=rt_query_config.get("agg_interval", 60),
            group_by=agg_dimension,
            where=rt_query_config.get("agg_condition", []),
            time_field=time_fields,
            custom_event_name=custom_event_name,
        )

    def __init__(self, *args, **kwargs):
        super(CustomEventDataSource, self).__init__(*args, **kwargs)

        # 添加自定义事件过滤条件
        if kwargs.get("custom_event_name"):
            self.filter_dict["event_name"] = kwargs["custom_event_name"]

        # 过滤掉恢复事件
        self.filter_dict["event_type__neq"] = RECOVERY

        # 锁定指标聚合方法为Count
        for metric in self.metrics:
            if metric["field"] == "_index":
                metric["method"] = "COUNT"

    def add_recovery_filter(self, datasource):
        """
        去除原有默认的异常事件筛选，增加恢复过滤条件
        :return: 增加恢复事件筛选的DataSource
        """
        # 原有 datasource 默认不筛选恢复事件，弹出
        datasource.filter_dict.pop("event_type__neq")

        # 新增恢复事件筛选条件
        datasource.filter_dict["event_type__eq"] = RECOVERY

        return datasource

    def query_data(
        self,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        *args,
        **kwargs,
    ) -> List:
        where = self._get_where()
        filter_dict = self._get_filter_dict()
        group_by = self._get_group_by()

        q = self._get_queryset(
            metrics=self.metrics,
            table=self.table,
            agg_condition=where,
            interval=self.interval,
            group_by=group_by,
            where=filter_dict,
            limit=1,
            time_field=self.time_field,
            start_time=start_time,
            end_time=end_time,
        )

        records = self._remove_dimensions_prefix(q.raw_data)
        records = self._filter_by_advance_method(records)
        records = self._format_time_series_records(records)
        return records[:limit]


class BkMonitorEventDataSource(DataSource):
    """
    系统事件数据源
    """

    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.EVENT


def load_data_source(data_source_label: str, data_type_label: str) -> Type[DataSource]:
    """
    加载对应的DataSource
    """
    data_sources = [
        BkMonitorTimeSeriesDataSource,
        BkMonitorLogDataSource,
        BkMonitorEventDataSource,
        BkdataTimeSeriesDataSource,
        CustomEventDataSource,
        CustomTimeSeriesDataSource,
        LogSearchLogDataSource,
        LogSearchTimeSeriesDataSource,
    ]

    data_source_mapping = {
        (data_source.data_source_label, data_source.data_type_label): data_source for data_source in data_sources
    }

    return data_source_mapping[(data_source_label, data_type_label)]
