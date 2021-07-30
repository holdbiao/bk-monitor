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
from __future__ import absolute_import, print_function, unicode_literals

import logging
import re
import time
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from functools import partial
from statistics import mean
from typing import Optional, List, Dict

from django.db.models import QuerySet, Q, Count
from django.forms import model_to_dict
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.cmdb.define import ServiceInstance, Host
from bkmonitor.data_source import load_data_source
from bkmonitor.utils.common_utils import number_format
from bkmonitor.utils.range import load_agg_condition_instance
from bkmonitor.utils.time_tools import parse_time_compare_abbreviation
from constants.cmdb import TargetNodeType
from constants.data_source import DATA_CATEGORY, DataSourceLabel, DataTypeLabel, TS_MAX_SLIMIT
from constants.strategy import (
    AdvanceConditionMethod,
    EVENT_QUERY_CONFIG_MAP,
    SYSTEM_EVENT_RT_TABLE_ID,
)
from core.drf_resource import Resource, api, resource
from core.errors.api import BKAPIError
from monitor_web.models import MetricListCache, CollectConfigMeta
from monitor_web.models.uptime_check import UptimeCheckTask, UptimeCheckNode
from monitor_web.strategies.constant import CORE_FILE_SIGNAL_LIST

logger = logging.getLogger(__name__)


class TargetEmptyError(Exception):
    """
    目标解析为空
    """

    pass


def get_timestamp(point: dict):
    """
    获取时间字段
    :param point: 数据点
    :return: timestamp
    """
    return point.get("_time_", point.get("time", 0))


def query_data(params):
    """
    按查询条件查询时序数据
    :param params: 查询参数
    :return: 数据列表
    """

    if params["function"].get("empty"):
        return []

    data_source_class = load_data_source(params["data_source_label"], params["data_type_label"])

    if data_source_class.data_source_label == DataSourceLabel.BK_LOG_SEARCH:
        index_set_id = params["result_table_id"]
    else:
        index_set_id = None

    metrics = [{"field": params["metric_field"], "method": params["method"]}]
    for extend_metric in params["extend_metric_fields"]:
        metrics.append({"field": extend_metric, "method": params["method"]})

    data_source = data_source_class(
        bk_biz_id=params["bk_biz_id"],
        table=params["result_table_id"],
        metrics=metrics,
        interval=params["interval"] * 60,
        where=params["agg_condition"],
        filter_dict=params["filter_dict"],
        group_by=params["group_by"],
        index_set_id=index_set_id,
        query_string=params["query_string"],
        time_field=params.get("time_field"),
    )

    slimit = None
    if params.get("slimit"):
        slimit = int(params["slimit"])

    records = data_source.query_data(start_time=params["start_time"], end_time=params["end_time"], slimit=slimit)
    return records


class BaseProcessor:
    """
    时序数据查询处理器
    """

    @classmethod
    def process_params(cls, params: dict) -> dict:
        return params

    @classmethod
    def process_origin_data(cls, params: dict, data: list) -> list:
        return data

    @classmethod
    def process_formatted_data(cls, params: dict, data: list) -> list:
        return data


class FrontProcessor(BaseProcessor):
    """
    默认处理器
    """

    @classmethod
    def parse_topo_target(cls, bk_biz_id, dimensions: List[str], target: List[Dict]):
        """
        在条件中添加目标选择
        :param bk_biz_id: 业务ID
        :param dimensions: 维度
        :param target: 监控目标
        """
        # 兼容策略目标格式
        if target and isinstance(target[0], list):
            if not target[0]:
                return []
            target = target[0][0]["value"]

        # 如果没有聚合任何目标字段，则不过滤目标
        if not {"bk_target_ip", "bk_target_service_instance_id", "ip", "service_instance_id"} & set(dimensions):
            is_service_instance = False
        else:
            is_service_instance = bool({"bk_target_service_instance_id", "service_instance_id"} & set(dimensions))

        topo_nodes = defaultdict(list)
        service_template_id = []
        set_template_id = []
        instances = []

        for node in target:
            if "bk_inst_id" in node and "bk_obj_id" in node:
                if node["bk_obj_id"].upper() == TargetNodeType.SERVICE_TEMPLATE:
                    service_template_id.append(node["bk_inst_id"])
                elif node["bk_obj_id"].upper() == TargetNodeType.SET_TEMPLATE:
                    set_template_id.append(node["bk_inst_id"])
                else:
                    topo_nodes[node["bk_obj_id"]].append(node["bk_inst_id"])
            elif ("bk_target_service_instance_id" in node or "service_instance_id" in node) and is_service_instance:
                instances.append(
                    {
                        "bk_target_service_instance_id": str(
                            node.get("bk_target_service_instance_id", node.get("service_instance_id"))
                        )
                    }
                )
            elif ("bk_target_ip" in node or "ip" in node) and not is_service_instance:
                instances.append({"bk_target_ip": node.get("bk_target_ip", node.get("ip"))})
                if "bk_target_cloud_id" in node or "bk_cloud_id" in node:
                    instances[-1]["bk_target_cloud_id"] = str(node.get("bk_target_cloud_id", node.get("bk_cloud_id")))

        # 根据实例类型设置查询方法
        if is_service_instance:
            node_query_func = api.cmdb.get_service_instance_by_topo_node
            template_query_func = api.cmdb.get_service_instance_by_template
        else:
            node_query_func = api.cmdb.get_host_by_topo_node
            template_query_func = api.cmdb.get_host_by_template

        instance_nodes: List[Optional[ServiceInstance, Host]] = []

        # 根据拓扑节点查询实例
        if topo_nodes:
            instance_nodes.extend(node_query_func(bk_biz_id=bk_biz_id, topo_nodes=topo_nodes))

        # 根据集群模版查询实例
        if set_template_id:
            instance_nodes.extend(
                template_query_func(
                    bk_biz_id=bk_biz_id, bk_obj_id=TargetNodeType.SET_TEMPLATE, template_ids=set_template_id
                )
            )

        # 根据服务模版查询实例
        if service_template_id:
            instance_nodes.extend(
                template_query_func(
                    bk_biz_id=bk_biz_id, bk_obj_id=TargetNodeType.SERVICE_TEMPLATE, template_ids=service_template_id
                )
            )

        for node in instance_nodes:
            if is_service_instance:
                instances.append({"bk_target_service_instance_id": str(node.service_instance_id)})
            else:
                instances.append({"bk_target_ip": node.bk_host_innerip, "bk_target_cloud_id": str(node.bk_cloud_id)})

        # 如果target有值但是没有返回，外部应返回空值，避免因过滤条件为空导致过滤失效
        if target and not instances:
            raise TargetEmptyError()

        return instances

    @classmethod
    def process_params(cls, params: dict) -> dict:
        # 过滤空维度
        params["group_by"] = [d for d in params["group_by"] if d]

        # 如果时间参数不全，则查询最近一小时
        interval = params["interval"] * 60 if params["interval"] else 1
        if "start_time" not in params or "end_time" not in params:
            end_time = int(datetime.now().timestamp()) // interval * interval
            start_time = int((datetime.now() - timedelta(hours=1)).timestamp()) // interval * interval
        else:
            start_time = params["start_time"] // interval * interval
            end_time = params["end_time"] // interval * interval
        start_time *= 1000
        end_time *= 1000

        condition_fields = set()
        has_advance_method = False
        for condition in params["where"]:
            # 将数值型处理为字符串
            if isinstance(condition["value"], list):
                condition["value"] = [str(value) for value in condition["value"]]

            condition_fields.add(condition["key"])
            if condition["method"] in AdvanceConditionMethod:
                has_advance_method = True

        # 如果存在高级比较方法，则需要补全维度
        if has_advance_method:
            params["group_by"] = list(set(params["group_by"]) | condition_fields)

        # 监控目标过滤
        filter_dict = params["filter_dict"].copy()
        target = cls.parse_topo_target(params["bk_biz_id"], params["group_by"], params["target"])
        if target:
            filter_dict["target"] = target

        if params["data_source_label"] == DataSourceLabel.BK_LOG_SEARCH:
            metric: MetricListCache = MetricListCache.objects.filter(
                data_source_label=params["data_source_label"],
                data_type_label=params["data_type_label"],
                bk_biz_id=params["bk_biz_id"],
                result_table_id=params["result_table_id"],
            ).first()
            if metric:
                result_table_id = metric.extend_fields.get("index_set_id")
                if not result_table_id:
                    raise ValidationError("bk_log_search metric lose index_set_id")
            else:
                result_table_id = params["result_table_id"]
        else:
            result_table_id = params["result_table_id"]

        return {
            "data_format": params["data_format"],
            "bk_biz_id": params["bk_biz_id"],
            "data_source_label": params["data_source_label"],
            "data_type_label": params["data_type_label"],
            "metric_field": params["metric_field"],
            "extend_metric_fields": params["extend_metric_fields"],
            "method": params["method"],
            "result_table_id": result_table_id,
            "group_by": params["group_by"],
            "interval": params["interval"],
            "filter_dict": filter_dict,
            "start_time": start_time,
            "end_time": end_time,
            "function": params["function"],
            "agg_condition": params["where"],
            "query_string": params["query_string"],
            "slimit": params.get("slimit"),
            "time_field": params.get("time_field"),
        }

    @classmethod
    def process_formatted_data(cls, params: dict, data: list):
        """
        1. 数据去重
        2. 小数位精度处理
        """

        def _convert(val):
            if val is None:
                return val

            val = number_format(val)
            if val:
                # 产品需求：保留4位小数
                return round(val, 4)
            else:
                return val

        for record in data:
            points = {point[1]: point[0] for point in record["datapoints"]}
            record["datapoints"] = [[_convert(value), timestamp] for timestamp, value in points.items()]

            for key, value in record["dimensions"].items():
                record["dimensions"][key] = str(value)
        return data


class RankProcessor(BaseProcessor):
    """
    TopN 处理器
    """

    @staticmethod
    def is_rank(params) -> bool:
        if "rank" not in params["function"]:
            return False

        return params["function"]["rank"].get("sort") and params["function"]["rank"].get("limit")

    @classmethod
    def process_params(cls, params: dict) -> dict:
        if not cls.is_rank(params):
            return params

        option = params["function"]["rank"]
        sort = option.get("sort")
        limit = option.get("limit")
        method = option.get("method") or params["method"]

        if not sort and not limit:
            return params

        rank_params = params.copy()
        rank_params["interval"] = 0
        rank_params["method"] = method
        data = query_data(rank_params)

        # 取出TopN或BottomN维度
        data = [point for point in data if point[params["metric_field"]] is not None]
        data.sort(key=lambda x: x[params["metric_field"]], reverse=sort == "desc")
        dimensions = [
            {key: value for key, value in record.items() if key in rank_params["group_by"]} for record in data[:limit]
        ]

        # 修改参数
        if dimensions:
            params["filter_dict"]["dimensions"] = dimensions
        else:
            params["function"]["empty"] = True
        params["target"] = []
        return params

    @classmethod
    def process_formatted_data(cls, params: dict, data: list) -> list:
        if not cls.is_rank(params):
            return data

        sort_index = {
            tuple((key, str(value)) for key, value in sorted(dimension.items(), key=lambda x: x[0])): index
            for index, dimension in enumerate(params["filter_dict"].get("dimensions", []))
        }

        if not sort_index:
            return data

        data.sort(
            key=lambda x: sort_index.get(
                tuple((key, str(value)) for key, value in sorted(x["dimensions"].items(), key=lambda d: d[0])), -1
            )
        )

        return data


class TimeCompareProcessor(BaseProcessor):
    """
    时间对比
    """

    @classmethod
    def process_origin_data(cls, params: dict, data: list) -> list:
        time_compare = params["function"].get("time_compare", [])

        # 兼容单个和多个时间对比
        if not isinstance(time_compare, list):
            time_compare = [time_compare]
        time_compare = set(time_compare)

        for offset_text in time_compare:
            time_offset = parse_time_compare_abbreviation(offset_text)

            if not time_offset:
                continue

            # 查询时间对比数据
            new_params = {}
            new_params.update(params)
            new_params.update(
                {
                    "start_time": new_params["start_time"] + time_offset * 1000,
                    "end_time": new_params["end_time"] + time_offset * 1000,
                }
            )
            extra_data = query_data(new_params)

            # 标记时间对比数据
            for record in extra_data:
                record["__time_compare"] = str(offset_text)

            data.extend(extra_data)
        return data

    @classmethod
    def process_formatted_data(cls, params: dict, data: list) -> list:
        time_compare = params["function"].get("time_compare", [])

        # 兼容单个时间对比配置
        if not isinstance(time_compare, list):
            time_compare = [time_compare]
        time_compare = [offset_text for offset_text in time_compare if re.match(r"\d+[mhdwMy]", str(offset_text))]

        # 如果存在对比配置，哪怕为空，也需要补全time_offset维度
        if not time_compare:
            if "time_compare" in params["function"]:
                for record in data:
                    record["time_offset"] = "current"
            return data

        for offset_text in time_compare:
            time_offset: int = parse_time_compare_abbreviation(offset_text)
            if not time_offset:
                continue

            for record in data:
                if not record["dimensions"].get("__time_compare"):
                    record["time_offset"] = "current"
                    record["target"] = f"current-{record['target']}"
                    continue

                if record["dimensions"]["__time_compare"] != offset_text:
                    continue

                # 调整数据描述
                record["target"] = (
                    record["target"]
                    .replace(f"__time_compare={offset_text}, ", "")
                    .replace(f"__time_compare={offset_text}", "")
                )
                record["target"] = f"{offset_text}-{record['target']}"

                # 调整时间对比数据时间
                record["time_offset"] = str(offset_text)
                for point in record["datapoints"]:
                    point[1] -= time_offset * 1000

        for record in data:
            if not record["dimensions"].get("__time_compare"):
                record["time_offset"] = "current"
                record["target"] = f"current-{record['target']}"
            else:
                del record["dimensions"]["__time_compare"]

        return data


class StatisticsProcessor(BaseProcessor):
    """
    数值统计信息
    """

    @classmethod
    def process_formatted_data(cls, params, data):
        if params["data_format"] != "time_series":
            return data

        if not params["function"].get("statistics"):
            return data

        for record in data:
            points = [point[0] for point in record["datapoints"] if point is not None]
            record["statistics"] = {
                "min": min(points) if points else None,
                "max": max(points) if points else None,
                "avg": mean(points) if points else None,
                "total": sum(points) if points else None,
            }

        return data


class UnitProcessor(BaseProcessor):
    """
    单位处理
    """

    @classmethod
    def process_formatted_data(cls, params: dict, data: list):
        # 如果参数没有单位则尝试查询指标信息获取单位
        if "unit" in params:
            unit = params["unit"]
        else:
            metric: Optional[MetricListCache] = MetricListCache.objects.filter(
                data_source_label=params["data_source_label"],
                data_type_label=params["data_type_label"],
                result_table_id=params["result_table_id"],
                metric_field=params["metric_field"],
            ).first()

            unit = metric.unit if metric else ""

        for record in data:
            record["unit"] = unit

        return data


class DownSamplingProcessor(BaseProcessor):
    """
    数据降采样
    """

    @classmethod
    def process_formatted_data(cls, params: dict, data: list):
        max_point_number: int = params["function"].get("max_point_number", 300)

        if not max_point_number or not params["interval"]:
            return data

        # 计算降采样周期
        interval = params["interval"] * 60 * 1000
        time_length = (params["end_time"] - params["start_time"]) // interval * interval
        sampling_interval = time_length // params["interval"] // max_point_number
        if sampling_interval * max_point_number * params["interval"] < time_length:
            sampling_interval += interval
        # 以三个周期为单位进行峰值采样
        sampling_interval *= 3

        for row in data:
            points = row["datapoints"]
            if not points:
                continue

            sampling_points = []
            point_block = []
            start_time = None
            for index, point in enumerate(points):
                if not start_time:
                    start_time = point[1]

                # 如果时间跨度达到了三倍的采样周期，则采用这三个周期内的最大值、最小值及中位数
                # 如果是最后一个点，则提前开始采样
                if point[1] - start_time >= sampling_interval or index + 1 == len(points):
                    if index + 1 == len(points):
                        point_block.append(point)

                    point_block.sort(key=lambda x: x[0] if x[0] is not None else 0)
                    sampling_points.extend(
                        sorted(
                            {
                                tuple(point_block[0]),
                                tuple(point_block[-1]),
                                tuple(point_block[(len(point_block) - 1) // 2]),
                            },
                            key=lambda x: x[1],
                        )
                    )

                    # 重置周期
                    point_block = []
                    start_time = point[1]

                point_block.append(point)

            row["datapoints"] = sampling_points

        return data


class AddNullDataProcessor(BaseProcessor):
    """
    根据时间范围和周期补全空数据点
    """

    @classmethod
    def process_formatted_data(cls, params: dict, data: list) -> list:
        if not params["interval"]:
            return data

        for row in data:
            time_to_value = defaultdict(lambda: None)
            for point in row["datapoints"]:
                time_to_value[point[1]] = point[0]

            row["datapoints"] = [
                [time_to_value[timestamp], timestamp]
                for timestamp in range(params["start_time"], params["end_time"], params["interval"] * 60000)
            ]
        return data


class TimeSeriesQuery(Resource):
    """
    时序数据查询
    """

    # 请注意处理顺序
    processors = [
        TimeCompareProcessor,
        FrontProcessor,
        RankProcessor,
        StatisticsProcessor,
        UnitProcessor,
        AddNullDataProcessor,
        DownSamplingProcessor,
    ]

    class RequestSerializer(serializers.Serializer):
        data_format = serializers.CharField(label=_("数据格式"), default="time_series")

        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        data_source_label = serializers.CharField(label=_("数据来源"), allow_blank=True)
        data_type_label = serializers.CharField(
            label=_("数据类型"), default="time_series", allow_null=True, allow_blank=True
        )
        metric_field = serializers.CharField(label=_("监控指标"))
        extend_metric_fields = serializers.ListField(default=[], label=_("监控指标列表"))
        result_table_id = serializers.CharField(label=_("结果表ID"), allow_blank=True)
        where = serializers.ListField(label=_("过滤条件"))
        group_by = serializers.ListField(label=_("聚合字段"))
        method = serializers.CharField(label=_("聚合方法"))
        interval = serializers.IntegerField(default=1, label=_("时间间隔"))
        target = serializers.ListField(default=[], label=_("监控目标"))
        filter_dict = serializers.DictField(default={}, label=_("过滤条件"))

        query_string = serializers.CharField(default="", allow_blank=True)
        start_time = serializers.IntegerField(required=False, label=_("开始时间"))
        end_time = serializers.IntegerField(required=False, label=_("结束时间"))

        function = serializers.DictField(label=_("功能函数"), default={})
        slimit = serializers.IntegerField(required=False, label=_("SLIMIT"))

        def validate_interval(self, value):
            return value // 60

    def time_series_format(self, params, data):
        """
        转换为Grafana TimeSeries的格式
        :param params: 请求参数
        :param data: [{
            "metric_field": 32960991004.444443,
            "bk_target_ip": "127.0.0.1",
            "minute60": 1581350400000,
            "time": 1581350400000
        }]
        :type data: list
        :return:
        :rtype: list
        """
        formatted_data = {}
        for record in data:
            dimensions = tuple(
                sorted(
                    (key, value)
                    for key, value in record.items()
                    if key in params["group_by"] or key == "__time_compare"
                )
            )
            formatted_data.setdefault(dimensions, {}).setdefault(params["metric_field"], []).append(
                [record[params["metric_field"]], get_timestamp(record)]
            )
            for other_metric in params.get("extend_metric_fields", []):
                formatted_data.setdefault(dimensions, {}).setdefault(other_metric, []).append(
                    [record[other_metric], get_timestamp(record)]
                )

        # 拼装指标信息
        extend_data = {}
        if self.metric:
            extend_data = model_to_dict(self.metric)
            extend_data.pop("dimensions")
            extend_data.pop("default_dimensions")
            extend_data.pop("bk_biz_id")
            extend_data[
                "metric_id"
            ] = f"{self.metric.data_source_label}.{self.metric.result_table_id}.{self.metric.metric_field}"
        metric_info = {
            params["metric_field"]: {
                "metric_field": params["metric_field"],
                "result_table_id": params["result_table_id"],
                "metric_field_name": self.metric.metric_field_name if self.metric else params["metric_field"],
                "extend_data": extend_data,
            }
        }
        for other_metric in params.get("extend_metric_fields", []):
            metric_info[other_metric] = {
                "metric_field": other_metric,
                "result_table_id": params["result_table_id"],
                "metric_field_name": other_metric,
            }

        result = []
        for dimensions, metric_to_data_point in formatted_data.items():
            dimension_string = ", ".join("{}={}".format(dimension[0], dimension[1]) for dimension in dimensions)
            for metric_field, value in metric_to_data_point.items():
                target = "{}({})".format(params["method"], metric_field)
                if dimension_string:
                    target += "{{{}}}".format(dimension_string)
                result.append(
                    {
                        "dimensions": {dimension[0]: dimension[1] for dimension in dimensions},
                        "target": target,
                        "datapoints": value,
                        "metric": metric_info.get(metric_field, {}),
                    }
                )

        return result

    @staticmethod
    def table_format(params, data):
        """
        转换为Grafana Table的格式
        :param params: 请求参数
        :param data: [{
            "_value_": 32960991004.444443,
            "bk_target_ip": "127.0.0.1",
            "minute60": 1581350400000,
            "time": 1581350400000
        }]
        :type data: list
        :return:
        :rtype: list
        """
        if not data:
            return []

        columns = OrderedDict()
        columns["time"] = {"text": "time", "type": "time"}
        columns["value"] = {"text": "value", "type": "number"}

        for key in data[0]:
            if key in params["group_by"] or key == "__time_compare":
                columns[key] = {"text": key, "type": "string"}

        rows = []
        for record in data:
            row = [get_timestamp(record), record[params["metric_field"]]]
            for key in columns:
                if key in ["time", "value"]:
                    continue
                row.append(record.get(key))
            rows.append(row)
        return [{"columns": list(columns.values()), "rows": rows}]

    def get_metric(self, params):
        self.metric = None
        if (params["data_source_label"], params["data_type_label"]) == (
            DataSourceLabel.BK_LOG_SEARCH,
            DataTypeLabel.LOG,
        ):
            try:
                result = resource.strategies.get_index_set_list(
                    bk_biz_id=params["bk_biz_id"], index_set_id=params["result_table_id"]
                )
                if result["metric_list"]:
                    params["time_field"] = result["metric_list"][0]["extend_fields"].get("time_field") or None
            except Exception as e:
                logger.exception(e)
        else:
            self.metric: MetricListCache = MetricListCache.objects.filter(
                data_source_label=params["data_source_label"],
                data_type_label=params["data_type_label"],
                result_table_id=params["result_table_id"],
                metric_field=params["metric_field"],
            ).first()

        if self.metric:
            params["time_field"] = self.metric.extend_fields.get("time_field")

    def perform_request(self, params):
        # 兼容grafana旧数据
        if not params["data_type_label"]:
            params["data_type_label"] = "time_series"
        if params["data_source_label"] == "log":
            params["data_source_label"] = "bk_log_search"

        if not params["result_table_id"] or not params["data_source_label"]:
            # 如果没有传结果表ID和数据源，则返回为空
            return []
        self.get_metric(params)

        # 参数处理
        for processor in self.processors:
            try:
                params = processor.process_params(params)
            except TargetEmptyError:
                # 目标解析为空，提前返回
                return []

        # 数据查询
        data = query_data(params)

        # 原始数据处理
        for processor in self.processors:
            data = processor.process_origin_data(params, data)

        # 数据格式化
        formatters = defaultdict(
            lambda: self.time_series_format, {"time_series": self.time_series_format, "table": self.table_format}
        )
        data = formatters[params["data_format"]](params, data)

        # 格式化后数据处理
        for processor in self.processors:
            data = processor.process_formatted_data(params, data)

        return data


class TimeSeriesMetric(Resource):
    """
    时序型指标
    """

    DisplayDataSource = (
        (DataSourceLabel.BK_DATA, DataTypeLabel.TIME_SERIES),
        (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.TIME_SERIES),
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES),
        (DataSourceLabel.CUSTOM, DataTypeLabel.TIME_SERIES),
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.LOG),
        (DataSourceLabel.CUSTOM, DataTypeLabel.EVENT),
    )

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        result_table_label = serializers.CharField(label=_("监控对象"), default="", allow_blank=True)
        conditions = serializers.DictField(label=_("查询条件"), default={})
        query_string = serializers.CharField(label=_("查询关键字"), default="", allow_blank=True)
        flat_format = serializers.BooleanField(label=_("是否扁平展示"), default=False)

    @staticmethod
    def handle_uptime_check_metric(metric):
        """
        处理拨测数据
        :param metric:
        :return:
        """
        if metric["result_table_id"].startswith("uptimecheck."):
            if metric["metric_field"] in ["response_code", "message"]:
                metric["method_list"] = ["COUNT"]
            else:
                metric["method_list"] = ["SUM", "AVG", "MAX", "MIN", "COUNT"]

    @staticmethod
    def get_metric_condition_methods(metric: MetricListCache):
        """
        根据指标获取可用的条件方法
        """
        return [
            {"label": "=", "value": "eq"},
            {"label": "!=", "value": "neq"},
            {"label": ">", "value": "gt"},
            {"label": ">=", "value": "gte"},
            {"label": "<", "value": "lt"},
            {"label": "<=", "value": "lte"},
            {"label": "include", "value": "include"},
            {"label": "exclude", "value": "exclude"},
            {"label": "regex", "value": "reg"},
        ]

    @staticmethod
    def filter_conditions(metrics: QuerySet, conditions: Dict):
        """
        查询过滤
        """
        if "related_id" in conditions:
            metrics = metrics.filter(related_id=conditions["related_id"])

        if "result_table_id" in conditions:
            metrics = metrics.filter(result_table_id=conditions["result_table_id"])

        if "metric_field" in conditions:
            metrics = metrics.filter(metric_field=conditions["metric_field"])

        if "data_source_label" in conditions:
            metrics = metrics.filter(data_source_label=conditions["data_source_label"])

        if "data_type_label" in conditions:
            metrics = metrics.filter(data_type_label=conditions["data_type_label"])
        return metrics

    def query_metrics(self, params):
        """
        指标查询
        """
        metrics = MetricListCache.objects.filter(bk_biz_id__in=[params["bk_biz_id"], 0])

        # 过滤指标对象
        if params["result_table_label"]:
            metrics = metrics.filter(
                Q(result_table_label=params["result_table_label"]) | Q(data_source_label=DataSourceLabel.BK_DATA)
            )

        # 条件过滤
        if params.get("query_string"):
            metrics = metrics.filter(
                Q(related_id__contains=params["query_string"])
                | Q(related_name__contains=params["query_string"])
                | Q(result_table_id__contains=params["query_string"])
                | Q(result_table_name__contains=params["query_string"])
                | Q(metric_field__contains=params["query_string"])
                | Q(metric_field_name__contains=params["query_string"])
            )
        else:
            metrics = self.filter_conditions(metrics, params["conditions"])

        return metrics

    def perform_request(self, params):
        metrics = self.query_metrics(params)

        custom_event_data_ids = set()
        data_source_dict = {}
        metric_configs: List[Dict] = []
        for metric in metrics:
            if (metric.data_source_label, metric.data_type_label) not in self.DisplayDataSource:
                continue
            if (
                params["result_table_label"]
                and metric.result_table_label != params["result_table_label"]
                and metric.data_source_label != DataSourceLabel.BK_DATA
            ):
                continue

            # 自定义事件指标需要修正
            if (metric.data_source_label, metric.data_type_label) == (DataSourceLabel.CUSTOM, DataTypeLabel.EVENT):
                if metric.result_table_id in custom_event_data_ids:
                    continue

                custom_event_data_ids.add(metric.result_table_id)
                metric.result_table_id = f"{metric.bk_biz_id}_bkmonitor_event_{metric.result_table_id}"
                metric.metric_field = "_index"
                metric.metric_field_name = _("事件统计")
                metric.dimensions.append({"id": "event_name", "name": "事件名称", "is_dimension": True, "type": "string"})

            metric_config = {
                "result_table_label": metric.result_table_label,
                "result_table_label_name": metric.result_table_label_name,
                "result_table_id": metric.result_table_id,
                "result_table_name": metric.result_table_name,
                "metric_field": metric.metric_field,
                "metric_field_name": metric.metric_field_name,
                "dimensions": metric.dimensions,
                "default_dimensions": metric.default_dimensions,
                "default_condition": metric.default_condition,
                "collect_interval": metric.collect_interval,
                "data_source_label": metric.data_source_label,
                "data_source_label_name": metric.data_source_label,
                "data_type_label": metric.data_type_label,
                "unit": metric.unit,
                "description": metric.description,
                "extend_fields": metric.extend_fields,
                "id": metric.metric_field,
                "name": metric.metric_field_name,
                "related_id": metric.related_id or "default",
                "related_name": metric.related_name,
                "condition_methods": self.get_metric_condition_methods(metric),
            }
            self.handle_uptime_check_metric(metric_config)

            if params["flat_format"]:
                metric_configs.append(metric_config)
            else:
                # 获取数据源分类
                key = "other"
                name = _("其他")
                for category in DATA_CATEGORY:
                    if (
                        category["data_source_label"] == metric.data_source_label
                        and category["data_type_label"] == metric.data_type_label
                    ):
                        name = category["name"]
                        key = f"{metric.data_source_label}.{metric.data_type_label}"
                        continue

                if key not in data_source_dict:
                    data_source_dict[key] = {"id": key, "name": name, "children": {}}

                related_metrics: dict = data_source_dict[key]["children"]
                if metric.related_id not in related_metrics:
                    related_metrics[metric.related_id] = {
                        "id": metric.related_id or "default",
                        "name": metric.related_name or metric.related_id or _("默认"),
                        "children": {},
                    }

                result_table_metrics = related_metrics[metric.related_id]["children"]
                if metric.result_table_id not in result_table_metrics:
                    result_table_metrics[metric.result_table_id] = {
                        "id": metric.result_table_id,
                        "name": metric.result_table_name,
                        "children": [],
                    }
                result_table_metrics[metric.result_table_id]["children"].append(metric_config)

        if params["flat_format"]:
            return metric_configs
        else:
            result = []
            for data_source in data_source_dict.values():
                data_source["children"] = list(data_source["children"].values())
                for related in data_source["children"]:
                    related["children"] = list(related["children"].values())
                result.append(data_source)
            return result


class TimeSeriesMetricLevel(TimeSeriesMetric):
    """
    指标分层信息
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        result_table_label = serializers.CharField(label=_("监控对象"), default="", allow_blank=True)
        conditions = serializers.DictField(label=_("查询条件"), default={})
        level = serializers.ChoiceField(choices=("data_source", "related_id", "result_table_id", "metric"))

    def perform_request(self, params):
        # 过滤指标信息
        metrics = self.query_metrics(params)

        label_mapping = {}
        if params["level"] == "data_source":
            for category in DATA_CATEGORY:
                if (category["data_source_label"], category["data_type_label"]) not in self.DisplayDataSource:
                    continue
                label_mapping[f'{category["data_source_label"]}.{category["data_type_label"]}'] = category["name"]
        elif params["level"] == "related_id":
            for metric in metrics.values("related_id", "related_name").annotate(
                id_count=Count("related_id"), name_count=Count("related_name")
            ):
                label_mapping[metric["related_id"]] = metric["related_name"]
        elif params["level"] == "result_table_id":
            for metric in metrics.values("result_table_id", "result_table_name").annotate(
                id_count=Count("result_table_id"), name_count=Count("result_table_name")
            ):
                label_mapping[metric["result_table_id"]] = metric["result_table_name"]

        return [{"id": key, params["level"]: key, "name": name or _("默认")} for key, name in label_mapping.items()]


class GetVariableField(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        type = serializers.CharField(label=_("查询类型"))

    extend_fields = {
        "host": [
            {"bk_property_id": "bk_host_id", "bk_property_name": _("主机ID")},
            {"bk_property_id": "bk_set_ids", "bk_property_name": _("集群ID")},
            {"bk_property_id": "bk_module_ids", "bk_property_name": _("模块ID")},
        ],
        "module": [
            {"bk_property_id": "bk_module_id", "bk_property_name": _("模块ID")},
            {"bk_property_id": "bk_set_id", "bk_property_name": _("集群ID")},
        ],
        "set": [{"bk_property_id": "bk_set_id", "bk_property_name": _("集群ID")}],
        "service_instance": [
            {"bk_property_id": "service_instance_id", "bk_property_name": _("服务实例ID")},
            {"bk_property_id": "name", "bk_property_name": _("服务实例名")},
            {"bk_property_id": "service_category_id", "bk_property_name": _("服务分类ID")},
            {"bk_property_id": "bk_host_id", "bk_property_name": _("主机ID")},
            {"bk_property_id": "bk_module_id", "bk_property_name": _("集群ID")},
        ],
    }

    def perform_request(self, params):
        if params["type"] not in ["host", "module", "service_instance", "set"]:
            raise ValidationError("type({}) not exists")

        properties = []
        if params["type"] != "service_instance":
            try:
                properties = api.cmdb.get_object_attribute(bk_obj_id=params["type"])
            except BKAPIError:
                pass

        data = [{"bk_property_id": p["bk_property_id"], "bk_property_name": p["bk_property_name"]} for p in properties]

        data.extend(self.extend_fields.get(params["type"], []))
        return data


class GetVariableValue(Resource):
    """
    Grafana 变量值查询
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        type = serializers.CharField(label=_("查询类型"))
        params = serializers.DictField(label=_("查询参数"))

    def query_cmdb(self, type, bk_biz_id, params):
        label_fields = [label_field for label_field in params["label_field"].split("|") if label_field]
        value_fields = [value_field for value_field in params["value_field"].split("|") if value_field]

        if type == "host":
            instances = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id)
        elif type == "module":
            instances = api.cmdb.get_module(bk_biz_id=bk_biz_id)
        elif type == "set":
            instances = api.cmdb.get_set(bk_biz_id=bk_biz_id)
        elif type == "service_instance":
            instances = api.cmdb.get_service_instance_by_topo_node(bk_biz_id=bk_biz_id)
        else:
            raise ValidationError("type({}) not exists")

        value_dict = {}

        for instance in instances:
            condition = load_agg_condition_instance(params.get("where", []))

            instance_dict = getattr(instance, "_extra_attr", {})
            instance_dict.update(instance.__dict__)
            if not condition.is_match(instance_dict):
                continue

            labels = [getattr(instance, label_field, "") for label_field in label_fields]
            values = [getattr(instance, value_field, "") for value_field in value_fields]

            if not values:
                continue

            new_labels = []
            new_values = []
            for value in values:
                if value is None:
                    value = ""
                elif isinstance(value, list):
                    value = ",".join([str(x) for x in value])
                else:
                    value = str(value)
                new_values.append(value)

            for label in labels:
                if label is None:
                    label = ""
                elif isinstance(label, list):
                    label = ",".join([str(x) for x in label])
                else:
                    label = str(label)

                new_labels.append(label)

            if not new_labels:
                new_labels = new_values

            value_dict["|".join(new_values)] = "|".join(new_labels)

        return [{"label": k, "value": v} for v, k in value_dict.items()]

    def query_dimension(self, bk_biz_id, params):
        """
        查询维度
        """
        # 兼容grafana旧数据
        if not params["data_type_label"]:
            params["data_type_label"] = "time_series"
        if params["data_source_label"] == "log":
            params["data_source_label"] = "bk_log_search"

        # 兼容没有传入data_source_label及data_type_label的情况
        if "data_source_label" in params and "data_type_label" in params:
            data_source_label = params["data_source_label"]
            data_type_label = params["data_type_label"]
        else:
            metric = MetricListCache.objects.filter(
                result_table_id=params["result_table_id"],
                metric_field=params["metric_field"],
                bk_biz_id__in=[0, bk_biz_id],
            ).first()
            if metric:
                data_source_label = metric.data_source_label
                data_type_label = metric.data_type_label
            else:
                data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
                data_type_label = DataTypeLabel.TIME_SERIES
        params = self.metric_filed_translate(params)

        # 事件型特殊处理
        if params["result_table_id"] == SYSTEM_EVENT_RT_TABLE_ID:
            # 特殊处理corefile signal的维度可选值
            if params["metric_field"] == "corefile-gse" and params["field"] == "signal":
                return [{"value": item, "label": item} for item in CORE_FILE_SIGNAL_LIST]
            elif params["metric_field"] in EVENT_QUERY_CONFIG_MAP:
                params.update(EVENT_QUERY_CONFIG_MAP[params["metric_field"]])
            else:
                return []

        # 如果指标与待查询维度相同，则返回空
        if params["metric_field"] == params["field"]:
            return []

        timestamp = int(time.time() // 60 * 60)
        start_time = params.get("start_time", timestamp - 30 * 60)
        end_time = params.get("end_time", timestamp)

        # 支持多维度值查询
        fields = [field for field in params["field"].split("|") if field]
        if not fields:
            return []

        # 日志平台使用index_set_id查询
        index_set_id = None
        if data_source_label == DataSourceLabel.BK_LOG_SEARCH:
            if params.get("index_set_id"):
                index_set_id = params["index_set_id"]
            else:
                metric = MetricListCache.objects.filter(
                    data_source_label=DataSourceLabel.BK_LOG_SEARCH,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id=params["result_table_id"],
                    bk_biz_id=bk_biz_id,
                ).first()
                if metric:
                    index_set_id = metric.extend_fields.get("index_set_id")

        # 如果是要查询"拓扑节点名称(bk_inst_id)"，则需要把"拓扑节点类型(bk_obj_id)"一并带上
        if "bk_inst_id" in fields:
            # 确保bk_obj_id在bk_inst_id之前，为后面的dimensions翻译做准备
            fields = [f for f in fields if f != "bk_obj_id"]
            fields.insert(0, "bk_obj_id")

        data_source_class = load_data_source(data_source_label, data_type_label)
        data_source = data_source_class(
            bk_biz_id=bk_biz_id,
            table=params["result_table_id"],
            metrics=[{"field": params["metric_field"], "method": "COUNT"}],
            where=params["where"],
            filter_dict=params.get("filter_dict", {}),
            group_by=fields,
            index_set_id=index_set_id,
            query_string=params.get("query_string", ""),
        )
        records = data_source.query_data(start_time * 1000, end_time * 1000, slimit=TS_MAX_SLIMIT)

        dimensions = set()
        for record in records:
            dimension_list = []
            for field in fields:
                dimension_list.append(str(record.get(field, "")))
            if dimension_list:
                dimensions.add("|".join(dimension_list))

        return self.dimension_translate(bk_biz_id, params, list(dimensions))

    @staticmethod
    def metric_filed_translate(query_params: dict):
        # http拨测，响应码和响应消息指标转换
        metric_field = query_params["metric_field"]
        result_table_id = query_params["result_table_id"]
        if str(result_table_id).startswith("uptimecheck."):
            query_params["where"] = []
            if metric_field in ["response_code", "message"]:
                query_params["metric_field"] = "available"

        return query_params

    @staticmethod
    def dimension_translate(bk_biz_id: int, params: dict, dimensions: List):
        """
        维度翻译
        """
        result = None
        dimension_field = params["field"]
        if dimension_field == "bk_collect_config_id":
            configs = CollectConfigMeta.objects.filter(bk_biz_id=bk_biz_id, id__in=dimensions)
            id_to_names = {str(config.id): config.name for config in configs}
            result = [{"label": id_to_names.get(str(v), v), "value": v} for v in dimensions]
        elif dimension_field == "bk_obj_id":
            topo_tree = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)
            obj_id_to_obj_name = {n.bk_obj_id: n.bk_obj_name for n in topo_tree.convert_to_flat_nodes()}
            result = [{"label": obj_id_to_obj_name.get(str(v), v), "value": v} for v in dimensions]
        elif dimension_field == "bk_inst_id":
            topo_tree = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)
            id_to_names = {}
            for n in topo_tree.convert_to_flat_nodes():
                # 产品需求，不要前缀bk_obj_name，即 不要"模块-consul"，只需要 "consul"名称即可
                # id_to_names[f"{n.bk_obj_id}|{n.bk_inst_id}"] = f"{n.bk_obj_name}-{n.bk_inst_name}"
                id_to_names[f"{n.bk_obj_id}|{n.bk_inst_id}"] = f"{n.bk_inst_name}"

            result = []
            for v in dimensions:
                v_split = v.split("|")
                value = v_split[1] if len(v_split) == 2 else v
                result.append({"label": id_to_names.get(str(v), value), "value": value})

        if dimension_field == "node_id":
            nodes = []
            for dimension in dimensions:
                nodes.extend(UptimeCheckNode.adapt_new_node_id(bk_biz_id, dimension))
            result = [{"label": node["name"], "value": str(node["id"])} for node in nodes]

        if str(params["result_table_id"]).startswith("uptimecheck."):
            if dimension_field == "task_id":
                task_info = UptimeCheckTask.objects.filter(id__in=dimensions).values("id", "name")
                result = [{"label": task["name"], "value": str(task["id"])} for task in task_info]

        result = result or [{"label": v, "value": v} for v in dimensions]

        return result

    @staticmethod
    def query_collect(bk_biz_id: int, params):
        """
        查询采集配置
        """
        collects = CollectConfigMeta.objects.filter(bk_biz_id=bk_biz_id).values("id", "name")
        return [{"label": str(collect.id), "value": collect.name} for collect in collects]

    def perform_request(self, params):
        query_cmdb = partial(self.query_cmdb, type=params["type"])
        query_processor = {
            "host": query_cmdb,
            "module": query_cmdb,
            "set": query_cmdb,
            "service_instance": query_cmdb,
            "dimension": self.query_dimension,
            "collect": self.query_collect,
        }

        if params["type"] not in query_processor:
            raise ValidationError("type({}) not exists")

        result = query_processor[params["type"]](bk_biz_id=params["bk_biz_id"], params=params["params"])
        return result


class Test(Resource):
    """
    Grafana数据源测试接口
    """

    def perform_request(self, params):
        return "OK"
