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
import json
import logging
import re
from collections import defaultdict
from typing import List, Dict, Optional

from django.utils.translation import ugettext as _
from rest_framework import serializers

from bkmonitor.utils.range import load_agg_condition_instance
from constants.strategy import AdvanceConditionMethod
from constants.data_source import TS_MAX_SLIMIT
from core.drf_resource import resource, Resource, api
from monitor.models import ApplicationConfig
from monitor_web.grafana.auth import GrafanaAuthSync
from monitor_web.grafana.data_migrate import GraphPanel, GrafanaMonitorTarget
from monitor_web.models import MetricListCache, CustomTSItem, CustomTSTable

logger = logging.getLogger(__name__)


class GetGraphQueryConfig(Resource):
    class RequestSerializer(serializers.Serializer):
        class QueryConfigSerializer(serializers.Serializer):
            metric_field = serializers.CharField()
            method = serializers.CharField()
            interval = serializers.IntegerField()
            result_table_id = serializers.CharField()
            data_source_label = serializers.CharField()
            data_type_label = serializers.CharField()
            group_by = serializers.ListField(child=serializers.CharField())
            where = serializers.ListField(child=serializers.DictField())

        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        query_configs = serializers.ListField(label=_("查询配合"), allow_empty=False, child=QueryConfigSerializer())
        target = serializers.ListField(label=_("监控目标"))
        start_time = serializers.IntegerField(required=True, label=_("开始时间"))
        end_time = serializers.IntegerField(required=True, label=_("结束时间"))
        compare_config = serializers.DictField(required=True, label=_("对比配置"))

    def __init__(self, context=None):
        super(GetGraphQueryConfig, self).__init__(context=context)
        self._metric_cache = {}

    @staticmethod
    def create_where_with_dimensions(where: list, dimensions: dict) -> List[Dict]:
        """
        在where条件中插入维度条件
        """
        default_condition = []
        for key, value in dimensions.items():
            default_condition.append({"condition": "and", "key": key, "method": "eq", "value": [value]})

        new_where = []
        and_conditions = []
        for index, condition in enumerate(where.copy()):
            # 如果条件是and，则直接保存
            if condition.get("condition") != "or":
                and_conditions.append(condition)
                if index < len(where) - 1:
                    continue

            instance = load_agg_condition_instance(and_conditions)
            # 判断这组条件是否符合当前维度
            if and_conditions and instance.is_match(dimensions):
                and_conditions.extend(default_condition)
                if new_where:
                    and_conditions[0]["condition"] = "or"
                else:
                    and_conditions[0].pop("condition", None)
                new_where.extend(and_conditions)

            and_conditions = []
            if condition.get("condition") == "or":
                and_conditions.append(condition)

        if and_conditions:
            instance = load_agg_condition_instance(and_conditions)
            if instance.is_match(dimensions):
                and_conditions.extend(default_condition)
            if new_where:
                and_conditions[0]["condition"] = "or"
            else:
                and_conditions[0].pop("condition", None)
            new_where.extend(and_conditions)

        # 如果没有任何条件，则需要补全维度条件
        if not new_where:
            new_where = default_condition

        # 去除第一个条件的and/or
        if new_where and new_where[0].get("condition"):
            del new_where[0]["condition"]

        return new_where

    def create_target_compare_config(self, params):
        """
        目标对比
        - 同指标不同维度
        """
        params = json.loads(json.dumps(params))
        query_configs = params["query_configs"]
        panels = []
        for index, query_config in enumerate(query_configs):
            params["query_configs"] = [query_config]
            configs = self.get_query_configs_with_dimension(params, show_nodata_target=False)
            metric = self.get_metric_info(query_config)
            if metric:
                title = f"{query_config['method']}({metric.metric_field_name})"
            else:
                title = f"{query_config['method']}({query_config['metric_field']})"

            sub_title = f"{query_config['result_table_id']}.{query_config['metric_field']}"

            if query_config["group_by"]:
                alias = " | ".join(f"$tag_{dimension}" for dimension in query_config["group_by"])
            else:
                alias = "$metric_metric_field"

            panels.append(
                {
                    "id": index,
                    "type": "graph",
                    "title": title,
                    "subTitle": sub_title,
                    "targets": [
                        {"data": query_config, "datasourceId": "time_series", "name": _("时序数据"), "alias": alias}
                        for query_config in configs
                    ],
                }
            )

        return panels

    def create_metric_compare_config(self, params):
        """
        指标对比
        - 同维度不同指标
        """
        query_configs = self.get_query_configs_with_dimension(params)

        query_config_groups = defaultdict(list)
        for query_config in query_configs:
            key = json.dumps(query_config["dimensions"], sort_keys=True)
            query_config_groups[key].append(query_config)

        panels = []
        for index, query_config_group in enumerate(query_config_groups.values()):
            dimensions = query_config_group[0]["dimensions"]
            title = self.get_dimension_string(dimensions)
            panels.append(
                {
                    "id": index,
                    "type": "graph",
                    "title": title,
                    "subTitle": "",
                    "targets": [
                        {
                            "data": query_config,
                            "datasourceId": "time_series",
                            "name": _("时序数据"),
                            "alias": "$formula($metric_metric_field_name)",
                        }
                        for query_config in query_config_group
                    ],
                }
            )
        return panels

    def create_time_compare_config(self, params):
        """
        时间对比
        - 添加一个历史时间查询
        """
        query_configs = self.get_query_configs_with_dimension(params)
        time_offset = params["compare_config"].get("time_offset", [])

        # 兼容单个时间对比配置
        if not isinstance(time_offset, list):
            time_offset = [time_offset]
        time_offset = [offset_text for offset_text in time_offset if re.match(r"\d+[mhdwMy]", str(offset_text))]

        panels = []
        for index, query_config in enumerate(query_configs):
            query_config["function"] = {"time_compare": time_offset}
            metric = self.get_metric_info(query_config)
            if metric:
                title = f"{query_config['method']}({metric.metric_field_name})"
            else:
                title = f"{query_config['method']}({query_config['metric_field']})"
            sub_title = f"{query_config['result_table_id']}.{query_config['metric_field']}"

            alias = "$time_offset"
            if query_config["group_by"]:
                alias += " - " + " | ".join(f"$tag_{dimension}" for dimension in query_config["group_by"])

            panels.append(
                {
                    "id": index,
                    "type": "graph",
                    "title": title,
                    "subTitle": sub_title,
                    "targets": [
                        {"data": query_config, "datasourceId": "time_series", "name": _("时序数据"), "alias": alias}
                    ],
                }
            )
        return panels

    def create_no_compare_config(self, params):
        """
        不对比
        """
        panels = []

        query_configs = params["query_configs"]
        # 是否做视图拆解
        if params["compare_config"].get("split"):
            query_configs = self.get_query_configs_with_dimension(params)

            for index, query_config in enumerate(query_configs):
                metric = self.get_metric_info(query_config)
                if metric:
                    title = f"{query_config['method']}({metric.metric_field_name})"
                else:
                    title = f"{query_config['method']}({query_config['metric_field']})"

                if query_config["group_by"]:
                    alias = " | ".join(f"$tag_{dimension}" for dimension in query_config["group_by"])
                else:
                    alias = "$metric_metric_field"

                sub_title = f"{query_config['result_table_id']}.{query_config['metric_field']}"

                panels.append(
                    {
                        "id": index,
                        "type": "graph",
                        "title": title,
                        "subTitle": sub_title,
                        "targets": [
                            {"data": query_config, "datasourceId": "time_series", "name": _("时序数据"), "alias": alias}
                        ],
                    }
                )
        else:
            targets = []
            metric_names = set()
            for query_config in query_configs:
                alias = ""
                if query_config["group_by"]:
                    alias = " | ".join(f"$tag_{dimension}" for dimension in query_config["group_by"])
                query_config["target"] = params["target"]
                targets.append({"data": query_config, "datasourceId": "time_series", "name": _("时序数据"), "alias": alias})

                metric = self.get_metric_info(query_config)
                if metric:
                    metric_field_name = metric.metric_field_name
                else:
                    metric_field_name = query_config["metric_field"]
                metric_names.add(metric_field_name)

            title = " | ".join(list(metric_names))
            panels.append({"id": 1, "type": "graph", "title": title, "targets": targets})
        return panels

    def get_query_configs_with_dimension(self, params, show_nodata_target: bool = True) -> List[Dict]:
        """
        将查询配置按维度派生出多个查询配置
        """
        from monitor_web.grafana.resources import FrontProcessor

        query_configs = []
        for query_config in params["query_configs"]:
            records = resource.grafana.time_series_query(
                bk_biz_id=params["bk_biz_id"],
                data_source_label=query_config["data_source_label"],
                data_type_label=query_config["data_type_label"],
                metric_field=query_config["metric_field"],
                method="MAX",
                interval=0,
                result_table_id=query_config["result_table_id"],
                group_by=query_config["group_by"],
                where=query_config["where"],
                target=params["target"],
                start_time=params["start_time"],
                end_time=params["end_time"],
                slimit=TS_MAX_SLIMIT,
            )

            where = query_config.pop("where")

            target_set = set()
            for record in records:
                query_config = json.loads(json.dumps(query_config))
                query_config["where"] = self.create_where_with_dimensions(where, record["dimensions"])
                query_config["dimensions"] = record["dimensions"]
                query_configs.append(query_config)

                if len({"bk_target_ip", "bk_target_cloud_id"} & set(record["dimensions"].keys())) == 2:
                    target_set.add((record["dimensions"]["bk_target_ip"], record["dimensions"]["bk_target_cloud_id"]))

            if (
                len({"bk_target_ip", "bk_target_cloud_id"} & set(query_config["group_by"])) < 2
                or not show_nodata_target
            ):
                continue

            # 展示无数据的目标
            if not params["target"] or not params["target"][0]:
                continue
            hosts = FrontProcessor.parse_topo_target(
                params["bk_biz_id"], query_config["group_by"], params["target"][0][0]["value"]
            )
            for host in hosts:
                if (host["bk_target_ip"], str(host["bk_target_cloud_id"])) in target_set:
                    continue

                host = {"bk_target_ip": host["bk_target_ip"], "bk_target_cloud_id": str(host["bk_target_cloud_id"])}

                query_config = json.loads(json.dumps(query_config))
                query_config["where"] = self.create_where_with_dimensions(where, host)
                query_config["dimensions"] = host
                query_configs.append(query_config)

        return query_configs

    def get_metric_info(self, params) -> Optional[MetricListCache]:
        """
        查询指标信息
        """
        data_source_label = params["data_source_label"]
        data_type_label = params["data_type_label"]
        result_table_id = params["result_table_id"]
        metric_field = params["metric_field"]

        metric_key = f"{data_source_label}.{data_type_label}.{result_table_id}.{metric_field}"
        if metric_key in self._metric_cache:
            return self._metric_cache[metric_key]

        metric = MetricListCache.objects.filter(
            data_source_label=data_source_label,
            data_type_label=data_type_label,
            result_table_id=result_table_id,
            metric_field=metric_field,
        ).first()

        self._metric_cache[metric_key] = metric
        return metric

    @staticmethod
    def get_dimension_string(dimensions: dict, without_target: bool = False) -> str:
        """
        拼接维度字符串
        """
        if without_target:
            if "bk_target_service_instance_id" in dimensions:
                target_dimensions = ["bk_target_service_instance_id"]
            else:
                target_dimensions = ["bk_target_ip", "bk_target_cloud_id"]
        else:
            target_dimensions = []

        return " | ".join(
            f"{dimensions[key]}" for key in sorted(list(dimensions.keys())) if key not in target_dimensions
        )

    def perform_request(self, params):
        compare_type = params["compare_config"].get("type")

        compare_func = defaultdict(
            lambda: self.create_no_compare_config,
            {
                "time": self.create_time_compare_config,
                "metric": self.create_metric_compare_config,
                "target": self.create_target_compare_config,
            },
        )

        for query_config in params["query_configs"]:
            query_config["bk_biz_id"] = params["bk_biz_id"]

            condition_fields = set()
            has_advance_method = False
            for condition in query_config["where"]:
                # 将数值型处理为字符串
                if isinstance(condition["value"], list):
                    condition["value"] = [str(value) for value in condition["value"]]

                if condition["method"] in AdvanceConditionMethod:
                    has_advance_method = True
                condition_fields.add(condition["key"])
            if has_advance_method:
                query_config["group_by"] = list(set(query_config["group_by"]) | condition_fields)

        panels = compare_func[compare_type](params)
        ret = {
            "title": _("数据检索"),
            "timepicker": {"refresh_intervals": ["1m", "5m", "15m", "30m", "1h", "2h", "1d"]},
            "panels": panels,
        }
        if len(panels) == TS_MAX_SLIMIT:
            tips = f"结果只显示了{TS_MAX_SLIMIT}个维度组合的数据，可以调整查询条件缩小范围。"
            ret = {"data": ret, "message": "", "tips": tips, "result": True, "code": 200}
        return ret


class SaveToDashboard(Resource):
    class RequestSerializer(serializers.Serializer):
        class PanelSerializer(serializers.Serializer):
            class QueryConfigSerializer(serializers.Serializer):
                metric_field = serializers.CharField()
                method = serializers.CharField()
                interval = serializers.IntegerField()
                result_table_id = serializers.CharField()
                data_source_label = serializers.CharField()
                data_type_label = serializers.CharField()
                group_by = serializers.ListField(child=serializers.CharField())
                where = serializers.ListField(child=serializers.DictField())
                alias = serializers.CharField(default="", allow_blank=True)
                function = serializers.DictField(default=dict)

            name = serializers.CharField(label=_("图表名称"))
            queries = serializers.ListField(label=_("查询配合"), allow_empty=False, child=QueryConfigSerializer())
            fill = serializers.BooleanField(default=False)
            min_y_zero = serializers.BooleanField(default=False)

        bk_biz_id = serializers.IntegerField()
        panels = serializers.ListField(allow_empty=False, child=PanelSerializer())
        dashboard_uids = serializers.ListField(allow_empty=True, child=serializers.CharField())

    @classmethod
    def get_panel(cls, panel_config: dict) -> GraphPanel:
        """
        获取图表配置
        """
        panel = GraphPanel(
            title=panel_config["name"],
            fill=int(panel_config["fill"]),
            bars=False,
            lines=True,
            gridPos={"x": 0, "y": 0, "w": 0, "h": 0},
            yaxes=[{"min": 0 if panel_config["min_y_zero"] else None}, {"min": None}],
        )

        for index, query_config in enumerate(panel_config["queries"]):
            time_compare = query_config["function"].get("time_compare", [])
            if not isinstance(time_compare, list):
                time_compare = [time_compare]
            time_compare = [offset_text for offset_text in time_compare if re.match(r"\d+[mhdwMy]", str(offset_text))]

            if time_compare:
                for offset_text in time_compare:
                    alias = query_config["alias"].replace("$time_offset", offset_text)
                    target = GrafanaMonitorTarget.deserialize(
                        GrafanaMonitorTarget(
                            data_source_label=query_config["data_source_label"],
                            data_type_label=query_config["data_type_label"],
                            result_table_id=query_config["result_table_id"],
                            metric_field=query_config["metric_field"],
                            period=query_config["interval"],
                            method=query_config["method"],
                            conditions=query_config["where"],
                            dimensions=query_config["group_by"],
                            function={},
                            offset=offset_text,
                            alias=alias,
                        ),
                        index,
                    )
                    if target:
                        panel.targets.append(target)

                alias = query_config["alias"].replace("$time_offset", "current")
            else:
                alias = query_config["alias"].replace("$time_offset - ", "").replace("$time_offset", "")

            target = GrafanaMonitorTarget.deserialize(
                GrafanaMonitorTarget(
                    data_source_label=query_config["data_source_label"],
                    data_type_label=query_config["data_type_label"],
                    result_table_id=query_config["result_table_id"],
                    metric_field=query_config["metric_field"],
                    period=query_config["interval"],
                    method=query_config["method"],
                    conditions=query_config["where"],
                    dimensions=query_config["group_by"],
                    function={},
                    alias=alias,
                ),
                index,
            )
            if target:
                panel.targets.append(target)

        return panel

    @classmethod
    def location_generator(cls, dashboard: dict, w: int, h: int) -> Dict:
        """
        在仪表盘中搜索大小合适的空位
        """
        assert w <= 24

        panels = dashboard.get("panels", [])

        # 计算最大高度
        max_y = 0
        for panel in panels:
            if max_y < panel["gridPos"]["y"] + panel["gridPos"]["h"]:
                max_y = panel["gridPos"]["y"] + panel["gridPos"]["h"]

            for inner_panel in panel.get("panels", []):
                if max_y < inner_panel["gridPos"]["y"] + inner_panel["gridPos"]["h"]:
                    max_y = inner_panel["gridPos"]["y"] + inner_panel["gridPos"]["h"]

        # 初始化矩阵
        max_y += h + 1
        grid = []
        for i in range(25):
            grid.append([])
            for j in range(max_y):
                grid[i].append([0, (0, 0)])

        # 记录已存在的图表
        for panel in panels:
            location = panel["gridPos"]
            for x in range(location["x"], location["x"] + location["w"] + 1):
                for y in range(location["y"], location["y"] + location["h"] + 1):
                    grid[x][y] = [1, (0, 0)]

        # 搜索大小合适的空位
        for y in range(max_y):
            for x in range(25):
                if grid[x][y][0] == 1:
                    continue

                if x > 0:
                    grid[x][y][1] = max((grid[x - 1][y][1][0] + 1, grid[x - 1][y][1][1]), grid[x][y][1])

                if y > 0:
                    grid[x][y][1] = max((grid[x][y - 1][1][0], grid[x][y - 1][1][1] + 1), grid[x][y][1])

                if grid[x][y][1][0] >= w and grid[x][y][1][1] >= h:
                    # 记录使用的区域
                    for _x in range(x - w + 1, x + 1):
                        for _y in range(y - h + 1, y + 1):
                            grid[_x][_y] = [1, (0, 0)]
                    yield {"x": x - w, "y": y - h, "w": w, "h": h}

        del grid

        while True:
            for x in [0, 12]:
                yield {"x": x, "y": max_y, "w": w, "h": h}

            max_y += h

    @classmethod
    def panel_id_generator(cls, dashboard):
        index = 1
        for panel in dashboard.get("panels", []):
            if index < panel["id"]:
                index = panel["id"]

        while True:
            index += 1
            yield index

    def perform_request(self, params):
        org_id = GrafanaAuthSync.get_or_create_org_id(params["bk_biz_id"])

        # 获取仪表盘配置
        dashboards = []
        for dashboard_uid in params["dashboard_uids"]:
            result = api.grafana.get_dashboard_by_uid(uid=dashboard_uid, org_id=org_id)
            if result["result"] and result["data"].get("dashboard"):
                dashboard = result["data"]["dashboard"]
                dashboard["folderId"] = result["data"]["meta"]["folderId"]
                dashboards.append(dashboard)

        panels = []
        for panel_config in params["panels"]:
            panels.append(self.get_panel(panel_config))

        # 更新仪表盘配置
        for dashboard in dashboards:
            location_generator = self.location_generator(dashboard, 12, 6)
            panel_id_generator = self.panel_id_generator(dashboard)
            for panel in panels:
                panel.gridPos = next(location_generator)
                panel.id = next(panel_id_generator)
                if not dashboard.get("panels"):
                    dashboard["panels"] = []
                dashboard["panels"].append(dict(panel))

        results = []

        # 更新仪表盘
        for dashboard in dashboards:
            results.append(
                api.grafana.create_or_update_dashboard_by_uid(
                    org_id=org_id, overwrite=True, dashboard=dashboard, folderId=dashboard.pop("folderId")
                )
            )

        return results


class SavePanelOrder(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        order = serializers.ListField(label=_("排序配置"))
        id = serializers.CharField(label=_("配置ID"))

    @classmethod
    def save_custom_report_order(cls, time_series_group_id, order):
        """
        自定义上报需要特殊处理
        """
        table = CustomTSTable.objects.get(time_series_group_id=time_series_group_id)
        metric_labels = {}
        for row in order:
            label = row["title"]

            if row["id"] == "__UNGROUP__":
                label = ""

            for panel in row["panels"]:
                metric_labels[".".join(panel["id"].split(".")[2:])] = [label, panel.get("hidden", False)]
        CustomTSItem.objects.filter(table=table).delete()
        CustomTSItem.objects.bulk_create(
            [
                CustomTSItem(table=table, metric_name=name, label=label[0], hidden=label[1])
                for name, label in metric_labels.items()
            ],
            batch_size=200,
        )

    def perform_request(self, params):
        if params["id"].startswith("custom_report_"):
            # fmt: off
            self.save_custom_report_order(int(params["id"][len("custom_report_"):]), order=params["order"])
            # fmt: on
        ApplicationConfig.objects.update_or_create(
            cc_biz_id=params["bk_biz_id"], key=f"panel_order_{params['id']}", defaults={"value": params["order"]}
        )


class DeletePanelOrder(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        id = serializers.CharField(label=_("配置ID"))

    def perform_request(self, params):
        ApplicationConfig.objects.filter(cc_biz_id=params["bk_biz_id"], key=f"panel_order_{params['id']}").delete()


class GetSceneViewConfig(Resource):
    """
    场景视图基类
    """

    DASHBOARD_TITLE = ""
    HIDE_NO_GROUP_METRIC = True

    @classmethod
    def get_query_configs(cls, params) -> List[Dict]:
        """
        [{
            "metric_field": "",
            "metric_field_name": "",
            "result_table_id": "",
            "data_source_label": "",
            "data_type_label": "",

            "method": "",
            "interval": "",
            "group_by": "",
            "where": []
        }]
        """
        raise NotImplementedError

    @classmethod
    def add_target_condition(cls, params, targets: List) -> None:
        raise NotImplementedError

    @classmethod
    def get_default_order(cls, params):
        """
        默认图表排序
        """
        return []

    @classmethod
    def get_order_config_key(cls, params):
        raise NotImplementedError

    @classmethod
    def generate_panel_config(cls, params):
        """
        生成图表配置
        """
        metrics = cls.get_query_configs(params)
        panels = []

        for metric in metrics:
            panel = {
                "id": metric["id"],
                "type": "graph",
                "title": metric["metric_field_name"],
                "subTitle": f"{metric['result_table_id']}.{metric['metric_field']}"
                if metric["metric_field_name"] != metric["metric_field"]
                else "",
                "targets": [
                    {
                        "data": {
                            "metric_field": metric["metric_field"],
                            "metric_field_name": metric["metric_field_name"],
                            "method": metric["method"],
                            "interval": metric["interval"],
                            "result_table_id": metric["result_table_id"],
                            "data_source_label": metric["data_source_label"],
                            "data_type_label": metric["data_type_label"],
                            "group_by": metric["group_by"],
                            "bk_biz_id": params["bk_biz_id"],
                            "where": metric["where"],
                        },
                        "alias": metric["alias"],
                        "datasourceId": "time_series",
                        "name": _("时序数据"),
                    }
                ],
            }
            panels.append(panel)

        return panels

    @classmethod
    def get_order_config(cls, params):
        """
        获取图表排序配置
        """
        default_order = cls.get_default_order(params)

        for row in default_order:
            row["title"] = str(row["title"])

        # 查询图表排序配置
        config, is_created = ApplicationConfig.objects.get_or_create(
            cc_biz_id=params["bk_biz_id"], key=cls.get_order_config_key(params), defaults={"value": default_order}
        )
        return config.value

    @classmethod
    def order(cls, params, dashboard):
        """
        分组排序
        """
        panels = {panel["id"]: panel for panel in dashboard["panels"]}
        order_config = cls.get_order_config(params)

        ordered_panels = []
        exists_panel_ids = set()
        no_group_row = None
        no_group_panels = []
        for row in order_config:
            # 过滤掉排序配置中不存在的图表
            row["panels"] = [panel for panel in row["panels"] if panel["id"] in panels]

            row_panels = []
            for panel in row["panels"]:
                # 补全排序配置信息
                panel["title"] = panels[panel["id"]]["title"]

                # 记录排序配置中存在的图表
                exists_panel_ids.add(panel["id"])

                # 是否隐藏图表
                if panel.get("hidden", False):
                    continue
                row_panels.append(panels[panel["id"]])

            if row["id"] == "__UNGROUP__":
                no_group_row = row
                no_group_panels = row_panels

            ordered_panels.append({"id": row["id"], "title": row["title"], "type": "row", "panels": row_panels})

        # 如果不存在未分组row，则创建
        if not no_group_row:
            no_group_row = {"id": "__UNGROUP__", "title": _("未分组的指标"), "panels": []}
            order_config.append(no_group_row)
            ordered_panels.append(
                {"id": no_group_row["id"], "title": no_group_row["title"], "type": "row", "panels": no_group_panels}
            )

        for panel in panels.values():
            if panel["id"] not in exists_panel_ids:
                no_group_row["panels"].append(
                    {"title": panel["title"], "id": panel["id"], "hidden": cls.HIDE_NO_GROUP_METRIC}
                )

                if not cls.HIDE_NO_GROUP_METRIC:
                    no_group_panels.append(panel)

        dashboard["panels"] = ordered_panels
        dashboard["order"] = order_config

    @classmethod
    def time_compare(cls, params, dashboard):
        """
        时间对比
        """
        time_offset = params["compare_config"].get("time_offset", [])

        # 兼容单个时间对比配置
        if not isinstance(time_offset, list):
            time_offset = [time_offset]
        time_offset = [offset_text for offset_text in time_offset if re.match(r"\d+[mhdwMy]", str(offset_text))]

        # 判断是否合法
        for offset_text in time_offset:
            if not offset_text or not re.match(r"\d+[mhdwMy]", offset_text):
                return dashboard

        for row in dashboard["panels"]:
            for panel in row["panels"]:
                panel["targets"][0]["data"]["function"] = {"time_compare": time_offset}
                if panel["targets"][0]["alias"]:
                    panel["targets"][0]["alias"] = "$time_offset - " + panel["targets"][0]["alias"]
                else:
                    panel["targets"][0]["alias"] = "$time_offset"

        return dashboard

    @classmethod
    def target_compare(cls, params, dashboard):
        """
        目标对比
        """
        for row in dashboard["panels"]:
            for panel in row["panels"]:
                cls.add_target_condition(params, panel["targets"])
        return dashboard

    @classmethod
    def no_compare(cls, params, dashboard):
        """
        不对比
        """
        for row in dashboard["panels"]:
            for panel in row["panels"]:
                if panel["targets"][0]["alias"]:
                    continue
                panel["targets"][0]["alias"] = panel["targets"][0]["data"]["metric_field"]
        return dashboard

    @classmethod
    def handle_compare(cls, params, dashboard):
        compare_config = params["compare_config"]
        compare_type = compare_config.get("type")

        if compare_type == "time":
            cls.time_compare(params, dashboard)
        elif compare_type == "target":
            cls.target_compare(params, dashboard)
        else:
            cls.no_compare(params, dashboard)
        return dashboard

    def perform_request(self, params):
        dashboard = {
            "title": str(self.DASHBOARD_TITLE),
            "timepicker": {"refresh_intervals": ["1m", "5m", "15m", "30m", "1h", "2h", "1d"]},
            "panels": self.generate_panel_config(params),
        }

        self.order(params, dashboard)
        self.handle_compare(params, dashboard)

        return dashboard
