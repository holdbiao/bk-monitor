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
from enum import Enum
import logging
from typing import Dict, List, Tuple

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from constants.data_source import DataSourceLabel, DataTypeLabel
from core.drf_resource import Resource, api, resource
from monitor.models import ApplicationConfig

from ..auth import GrafanaAuthSync
from ..data_migrate import BarGaugePanel, BasePanel, GrafanaDashboard, GrafanaMonitorTarget, GraphPanel, StatPanel

logger = logging.getLogger(__name__)


class MigrateStatus(Enum):
    """
    迁移状态
    """

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NOT_MIGRATE = "NOT_MIGRATE"


class MigrateOldDashboard(Resource):
    """
    迁移旧版仪表盘
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        only_show_config = serializers.BooleanField(label=_("只显示新配置但不创建"), default=False)

    @staticmethod
    def hex_color_to_rgba(code: str, alpha: float) -> Tuple[int, int, int, float]:
        """
        16进制颜色代码转rgba格式
        :param code: 16进制颜色代码
        :param alpha: α通道
        """
        r = int(code[1:3], 16)
        g = int(code[3:5], 16)
        b = int(code[5:7], 16)
        return r, g, b, alpha

    @staticmethod
    def get_old_dashboard_configs(bk_biz_id: int) -> List:
        """
        查询旧仪表盘配置
        """
        from monitor.models import DashboardMenu, DashboardMenuLocation, ApplicationConfig

        configs = []
        menus = DashboardMenu.objects.filter(biz_id=bk_biz_id)
        for menu in menus:
            configs.append({"id": menu.id, "name": menu.name, "views": []})
            views = [x.view for x in DashboardMenuLocation.objects.filter(menu=menu).select_related("view")]

            # 图表位置查询
            locations = ApplicationConfig.objects.filter(cc_biz_id=bk_biz_id, key=f"dashboard_view_config:{menu.id}")
            if locations:
                locations = json.loads(locations[0].value)
                view_locations = {
                    location["view_id"]: {
                        "x": location["x"] * 2,
                        "y": location["y"] * 2,
                        "w": location["width"] * 2,
                        "h": location["height"] * 2,
                    }
                    for location in locations
                }
            else:
                x = y = 0
                view_locations = {}
                for view in views:
                    view_locations[view.id] = {
                        "x": x,
                        "y": y,
                        "w": 12,
                        "h": 8,
                    }
                    x += 12
                    if x == 24:
                        y += 8
                        x = 0

            for view in views:
                view_location = view_locations.get(view.id)
                configs[-1]["views"].append(
                    {
                        "name": view.name,
                        "graph_type": view.graph_type,
                        "metrics": json.loads(view.metrics),
                        "symbols": json.loads(view.symbols),
                        "location": view_location,
                    }
                )

        return configs

    @classmethod
    def convert_time_graph_config(cls, config) -> BasePanel:
        """
        转换时序图表配置
        """
        bars = False
        lines = False
        fill = 0

        # 只取第一个图表类型的配置，graph图表不支持通知配置多种图表类型
        metric_config = config["metrics"][0]
        if metric_config["metric_graph_type"] == "column":
            bars = True
        else:
            lines = True

        if metric_config["metric_graph_type"] == "area":
            fill = 1

        thresholds = []
        # 解析标记配置
        for symbol_config in config["symbols"]:
            if symbol_config["plot_type"] == "band":
                # 区间配置
                if symbol_config["from"] != "":
                    thresholds.append(
                        {
                            "colorMode": "custom",
                            "fill": True,
                            "fillColor": "rgba({}, {}, {}, {})".format(
                                *cls.hex_color_to_rgba(symbol_config["color"], 0.3)
                            ),
                            "lineColor": symbol_config["color"],
                            "op": "gt",
                            "value": int(symbol_config["from"]),
                            "yaxis": "left",
                        }
                    )
                if symbol_config["to"] != "":
                    thresholds.append(
                        {
                            "colorMode": "custom",
                            "fill": True,
                            "fillColor": "rgba({}, {}, {}, {})".format(
                                *cls.hex_color_to_rgba(symbol_config["color"], 0.3)
                            ),
                            "lineColor": symbol_config["color"],
                            "op": "lt",
                            "value": int(symbol_config["to"]),
                            "yaxis": "left",
                        }
                    )
            elif symbol_config["plot_type"] == "line":
                # 线配置
                thresholds.append(
                    {
                        "colorMode": "custom",
                        "fill": False,
                        "fillColor": symbol_config["color"],
                        "lineColor": symbol_config["color"],
                        "op": "gt",
                        "value": int(symbol_config["line_value"]),
                        "yaxis": "left",
                    }
                )

        panel = GraphPanel(
            title=config["name"],
            gridPos=config["location"],
            fill=fill,
            bars=bars,
            lines=lines,
            thresholds=thresholds,
        )

        return panel

    @staticmethod
    def convert_top_graph_config(config) -> BasePanel:
        """
        转换Top排行图表配置
        """

        thresholds = [{"color": "green", "value": None}]

        if config["symbols"]:
            symbol = config["symbols"][0]
            if symbol["method"] in [">=", ">"]:
                thresholds.append({"color": symbol["color"], "value": symbol["threshold"]})
            else:
                thresholds[0]["color"] = symbol["color"]
                thresholds.append({"color": "green", "value": symbol["threshold"]})

        panel = BarGaugePanel(
            title=config["name"],
            gridPos=config["location"],
            options={
                "fieldOptions": {
                    "calcs": ["mean"],
                    "defaults": {"thresholds": {"mode": "absolute", "steps": thresholds}},
                    "values": False,
                    "overrides": [],
                },
                "orientation": "horizontal",
                "showUnfilled": True,
                "displayMode": "gradient",
            },
        )

        return panel

    @staticmethod
    def convert_stat_graph_config(config) -> BasePanel:
        """
        转换状态值图表配置
        """
        panel = StatPanel(
            id=0,
            title=config["name"],
            gridPos=config["location"],
        )

        # 默认仪表盘的状态值添加单位
        metric = config["metrics"][0]
        if metric["metric"] in ["system.disk.total", "system.mem.total"]:
            panel.options["fieldOptions"]["defaults"] = {"unit": "bytes"}

        return panel

    @staticmethod
    def convert_query_config(config) -> List[Dict]:
        """
        转换查询配置
        """
        targets = []
        for index, metric_config in enumerate(config["metrics"]):
            # 条件格式转换
            old_conditions = metric_config["where_field_list"]
            if not isinstance(old_conditions, list):
                old_conditions = json.loads(old_conditions)

            conditions = []
            for old_condition_group in old_conditions:
                for group_index, old_condition in enumerate(old_condition_group):
                    condition = {
                        "key": old_condition["field"],
                        "method": old_condition["method"],
                        "value": [old_condition["value"]],
                    }

                    if not conditions:
                        continue
                    elif group_index == 0:
                        condition["condition"] = "or"
                    else:
                        condition["condition"] = "and"

            # 维度剔除聚合周期
            dimensions = [field for field in metric_config["group_field_list"] if not field.startswith("minute")]

            method = metric_config["method"]

            # 聚合周期解析
            period = [field for field in metric_config["group_field_list"] if field.startswith("minute")] or ["minute1"]
            period = period[0][6:]
            if not period.isdigit():
                period = 60
            else:
                period = int(period) * 60

            # TopN配置
            function = None
            if metric_config.get("view_type", metric_config.get("graph_type")) == "top":
                function = {"rank": {"sort": metric_config["order"], "limit": int(metric_config["top_count"])}}

            # 提取表名
            data_source_label = metric_config.get("data_source_label", DataSourceLabel.BK_MONITOR_COLLECTOR)
            data_type_label = metric_config.get("data_type_label", DataTypeLabel.TIME_SERIES)
            if data_source_label in [
                DataSourceLabel.BK_MONITOR_COLLECTOR,
                DataSourceLabel.CUSTOM,
                DataSourceLabel.BK_LOG_SEARCH,
            ]:
                db, table = metric_config["metric"].split(".")[:-1]
                result_table_id = f"{db}.{table}"
            elif data_source_label == DataSourceLabel.BK_DATA:
                result_table_id = metric_config["metric"].split(".")[-2]
            else:
                continue

            target = GrafanaMonitorTarget.deserialize(
                GrafanaMonitorTarget(
                    data_source_label=data_source_label,
                    data_type_label=data_type_label,
                    result_table_id=result_table_id,
                    metric_field=metric_config["metric_field"],
                    period=period,
                    method=method,
                    conditions=conditions,
                    dimensions=dimensions,
                    function=function,
                ),
                index,
            )

            if target:
                targets.append(target)

        return targets

    @classmethod
    def convert_config(cls, config):
        """
        转换旧仪表盘图表配置到grafana panel配置
        """
        dashboard = GrafanaDashboard(config["name"])

        for view_config in config["views"]:
            # 转换图表配置
            if view_config["graph_type"] == "time":
                panel = cls.convert_time_graph_config(view_config)
            elif view_config["graph_type"] == "top":
                panel = cls.convert_top_graph_config(view_config)
            elif view_config["graph_type"] == "status":
                panel = cls.convert_stat_graph_config(view_config)
            else:
                continue

            # 转换查询配置
            panel.targets = cls.convert_query_config(view_config)
            dashboard.add_panel(panel)

        return dict(dashboard)

    def perform_request(self, params):
        org_id = GrafanaAuthSync.get_or_create_org_id(params["bk_biz_id"])

        # 指标详情查询
        grafana_dashboard_configs = []
        old_dashboard_configs = self.get_old_dashboard_configs(params["bk_biz_id"])
        existed_dashboards = resource.grafana.get_dashboard_list(bk_biz_id=params["bk_biz_id"])
        dashboard_names = [dashboard["name"] for dashboard in existed_dashboards]

        results = []

        migrate_result, is_create = ApplicationConfig.objects.get_or_create(
            cc_biz_id=params["bk_biz_id"], key="migrate_old_dashboard_result", defaults={"value": []}
        )
        migrate_result_value = migrate_result.value

        for old_dashboard_config in old_dashboard_configs:

            for result in migrate_result_value:
                if (
                    result["name"].replace("_Copy", "") == old_dashboard_config["name"]
                    and result["status"] == MigrateStatus.SUCCESS.value
                ):
                    # 相同的仪表盘，若已经迁移成功了，则不再进行迁移
                    results.append(result)
                    has_migrated = True
                    break
            else:
                has_migrated = False

            if has_migrated:
                continue

            while old_dashboard_config["name"] in dashboard_names:
                old_dashboard_config["name"] += "_Copy"

            try:
                grafana_dashboard_configs.append(self.convert_config(old_dashboard_config))
                if not params["only_show_config"]:
                    result = api.grafana.create_dashboard(dashboard=grafana_dashboard_configs[-1], org_id=org_id)
                    if result["result"]:
                        results.append(
                            {
                                "id": old_dashboard_config["id"],
                                "name": old_dashboard_config["name"],
                                "status": MigrateStatus.SUCCESS.value,
                                "message": "",
                            }
                        )
                    else:
                        results.append(
                            {
                                "id": old_dashboard_config["id"],
                                "name": old_dashboard_config["name"],
                                "status": MigrateStatus.FAILED.value,
                                "message": result["message"],
                            }
                        )
            except Exception as e:
                logger.exception(e)
                results.append(
                    {
                        "id": old_dashboard_config["id"],
                        "name": old_dashboard_config["name"],
                        "status": MigrateStatus.FAILED.value,
                        "message": str(e),
                    }
                )

        if params["only_show_config"]:
            return grafana_dashboard_configs
        else:
            # 保存迁移结果
            migrate_result.value = results
            migrate_result.save()
            return results


class GetOldDashboards(Resource):
    """
    老仪表盘列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))

    def perform_request(self, params):
        from monitor.models import DashboardMenu

        menus = DashboardMenu.objects.filter(biz_id=params["bk_biz_id"])

        # 获取上次迁移结果
        try:
            last_migrate_results = ApplicationConfig.objects.get(
                cc_biz_id=params["bk_biz_id"], key="migrate_old_dashboard_result"
            ).value
        except ApplicationConfig.DoesNotExist:
            last_migrate_results = []

        last_migrate_results = {result["id"]: result for result in last_migrate_results}

        results = []
        for menu in menus:
            result = last_migrate_results.get(menu.id, {"status": MigrateStatus.NOT_MIGRATE.value, "message": ""})

            results.append({"id": menu.id, "name": menu.name, "status": result["status"], "message": result["message"]})

        return results
