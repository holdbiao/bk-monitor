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

from django.utils.translation import ugettext as _

from bkmonitor.utils.common_utils import uniqid4
from constants.data_source import DataSourceLabel
from core.drf_resource import api, resource
from monitor.models import MonitorLocation, ScenarioMenu
from monitor_api.models import MonitorSource
from monitor_web.grafana.auth import GrafanaAuthSync
from monitor_web.grafana.resources import MigrateOldDashboard
from monitor_web.upgrade.data_maker.base import BaseDataMaker
from monitor_web.upgrade.data_maker.commons import ResultTableType, classify_result_table


class CustomMonitorMaker(BaseDataMaker):
    """
    根据自定义监控配置，生成仪表盘视图配置
    """

    # 全局配置的KEY
    GLOBAL_CONFIG_KEY = "custom_monitor_migrate_record"

    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        # 列出待升级的项
        menus = (
            ScenarioMenu.objects.using("monitor_saas_3_1")
            .filter(is_deleted=False)
            .exclude(system_menu="favorite")
            .order_by("menu_index")
        )
        if bk_biz_id:
            menus = menus.filter(biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value

        results = []
        for menu in menus:
            locations = (
                MonitorLocation.objects.using("monitor_saas_3_1")
                .filter(menu_id=menu.id, biz_id=menu.biz_id)
                .order_by("graph_index")
            )

            for location in locations:
                monitor = MonitorSource.objects.using("monitor_api_3_1").filter(id=location.monitor_id).first()
                location.monitor = monitor
                if not monitor or monitor.is_deleted:
                    # 对应监控项已经删掉的，不处理
                    continue
                if str(monitor.id) in migrate_record_value:
                    # 如果已经有迁移记录了，则显示上次的迁移结果
                    results.append(migrate_record_value[str(monitor.id)])
                else:
                    results.append(
                        {
                            "status": "READY",
                            "message": _("等待迁移"),
                            "bk_biz_id": menu.biz_id,
                            "origin_menu": {"id": menu.id, "name": menu.name},
                            "new_menu": {},
                            "origin_view": {"id": monitor.id, "name": monitor.monitor_name},
                            "new_view": {},
                        }
                    )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        """
        迁移自定义监控
        """
        # 1. 将自定义视图迁移到仪表盘视图
        menus = (
            ScenarioMenu.objects.using("monitor_saas_3_1")
            .filter(is_deleted=False)
            .exclude(system_menu="favorite")
            .order_by("menu_index")
        )
        if bk_biz_id:
            menus = menus.filter(biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()

        results = []
        for menu in menus:
            view_maker = cls(menu)
            result = view_maker.create()
            results += result

            for item in result:
                migrate_record.value.update({str(item["origin_view"]["id"]): item})

        migrate_record.save()

        results = [r for r in migrate_record.value.values() if int(r["bk_biz_id"]) == int(bk_biz_id)]
        return results

    def __init__(self, scenario_menu):
        self.scenario_menu = scenario_menu
        self.bk_biz_id = scenario_menu.biz_id
        self.org_id = GrafanaAuthSync.get_or_create_org_id(self.bk_biz_id)

    def create(self):
        dashboard_config, records = self.get_dashboard_config()

        if not dashboard_config:
            return []

        dashboard_config = MigrateOldDashboard.convert_config(dashboard_config)

        # 增加昨天和上周的曲线
        for panel in dashboard_config["panels"]:
            if not panel["targets"]:
                continue
            target = panel["targets"][0]
            target["data"]["alias"] = _("今日")

            target_yesterday = copy.deepcopy(target)
            target_yesterday["refId"] = "B"
            target_yesterday["data"]["alias"] = _("昨日")
            target_yesterday["data"]["offset"] = "1d"
            panel["targets"].append(target_yesterday)

            target_last_week = copy.deepcopy(target)
            target_last_week["refId"] = "C"
            target_last_week["data"]["alias"] = _("上周")
            target_last_week["data"]["offset"] = "1w"
            panel["targets"].append(target_last_week)

        result = api.grafana.create_dashboard(dashboard=dashboard_config, org_id=self.org_id)

        if result["result"]:
            for r in records:
                if r["status"] == "READY":
                    r["status"] = "SUCCESS"
                    r["message"] = _("迁移成功")
        else:
            for r in records:
                if r["status"] == "READY":
                    r["status"] = "FAILED"
                    r["message"] = result["message"]

        return records

    def get_dashboard_config(self):

        # 获取当前分组对应的监控视图
        locations = (
            MonitorLocation.objects.using("monitor_saas_3_1")
            .filter(menu_id=self.scenario_menu.id, biz_id=self.bk_biz_id)
            .order_by("graph_index")
        )
        menu_name = _("自定义监控-{}").format(self.scenario_menu.menu_name)

        existed_dashboards = resource.grafana.get_dashboard_list(bk_biz_id=self.bk_biz_id)
        dashboard_names = [dashboard["name"] for dashboard in existed_dashboards]
        if menu_name in dashboard_names:
            # 已经迁移过则无需迁移
            return None, []

        dashboard_config = {"id": self.scenario_menu.id, "name": menu_name, "views": []}

        records = []
        x = y = 0

        for location in locations:

            monitor = MonitorSource.objects.using("monitor_api_3_1").filter(id=location.monitor_id).first()
            location.monitor = monitor
            if not location.monitor or location.monitor.is_deleted:
                # 对应监控项已经删掉的，不处理
                continue

            record = {
                "status": "READY",
                "message": _("等待迁移"),
                "bk_biz_id": self.bk_biz_id,
                "origin_view": {"id": monitor.id, "name": monitor.monitor_name},
                "origin_menu": {"id": self.scenario_menu.id, "name": self.scenario_menu.name},
                "new_menu": {},
                "new_view": {},
            }

            try:
                if location.monitor.scenario == "log" and location.monitor.monitor_type == "keyword":
                    raise Exception(_("不支持迁移日志关键字类型的策略项"))

                # 创建仪表盘视图
                stat_source_info = location.monitor.stat_source_info_dict

                # 仪表盘的周期单位为分钟，需要转换
                collect_interval = int(stat_source_info.get("count_freq") or 60) // 60
                rt_id = stat_source_info["monitor_result_table_id"]

                rt_type, metric_id_prefix = classify_result_table(rt_id)
                if rt_type == ResultTableType.BK_DATA:
                    data_source_label = DataSourceLabel.BK_DATA
                    metric_id_prefix = "{}.{}".format(data_source_label, metric_id_prefix)
                elif rt_type == ResultTableType.OLD_BK_MONITOR:
                    raise Exception(_("不支持迁移。该配置使用了不支持的数据源类型。RT({})".format(rt_id)))
                else:
                    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR

                # metric_id
                # 计算平台: bkdata.system_cpu.field
                # 新链路老表: bkmonitor.system_cpu.field
                # 新链路新表: system.cpu.idle

                # 根据布局推算每个图表的位置
                graph_location = {
                    "x": x,
                    "y": y,
                    "w": 12,
                    "h": 8,
                }
                x += 12
                if x == 24:
                    y += 8
                    x = 0

                dashboard_config["views"].append(
                    {
                        "name": location.monitor.monitor_name,
                        "graph_type": "time",
                        "metrics": [
                            {
                                "bk_biz_id": self.bk_biz_id,
                                "id": uniqid4(),
                                "metric": "{}.{}".format(metric_id_prefix, stat_source_info["monitor_field"]),
                                "where_field_list": [[]],
                                "method": stat_source_info["aggregator"].upper(),
                                "metric_field": stat_source_info["monitor_field"],
                                "alis": "",
                                # "group_field_list": stat_source_info['dimensions'],
                                "group_field_list": [],  # 多维度组合会产生大量数据，造成性能问题，故不再迁移维度
                                "metric_graph_type": "spline",
                                "graph_type": "time",
                                "metric_index": "2",  # TODO 用途未知
                                "rt_id": rt_id,
                                "top_count": "5",
                                "order": "asc",
                                "data_source_label": data_source_label,
                                "data_type_label": "time_series",  # 固定
                                "collect_interval": collect_interval if collect_interval > 0 else 1,
                            }
                        ],
                        "symbols": [],
                        "location": graph_location,
                    }
                )
            except Exception as e:
                record["status"] = "FAILED"
                record["message"] = _("迁移失败，原因：{}").format(e)

            records.append(record)

        return dashboard_config, records
