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


import abc
import datetime

import six
from django.db.models import Q
from django.utils.translation import ugettext as _

from bkmonitor.data_source import load_data_source
from bkmonitor.models import StrategyModel
from core.drf_resource import resource
from bkmonitor.utils.common_utils import host_key
from bkmonitor.utils.time_tools import hms_string, localtime, now
from common.log import logger
from constants.data_source import DataSourceLabel, DataTypeLabel
from monitor.models import ComponentInstance
from monitor_web.core.metric import Metric
from monitor_web.models import CollectConfigMeta
from monitor_web.models.uptime_check import UptimeCheckNode, UptimeCheckTask
from utils.query_data import TSDBData


class ComponentHealthChecker(six.with_metaclass(abc.ABCMeta, object)):
    """
    组件监控健康检查
    """

    def __init__(self, bk_biz_id):
        self.bk_biz_id = bk_biz_id

    def detect(self):
        """
        组件健康检查逻辑，由子类实现
        :returns list[str]
        """
        raise NotImplementedError

    def run_detect(self):
        try:
            return self.detect()
        except Exception as e:
            logger.exception(e)
            return []


class MysqlHealthChecker(ComponentHealthChecker):
    component_name = "mysql"

    def detect(self):
        hostid_dict = {}
        component_instances = ComponentInstance.objects.filter(biz_id=self.bk_biz_id, component=self.component_name)
        for instance in component_instances:
            host_id = host_key(ip=instance.ip, plat_id=resource.cc.plat_id_job_to_cc(instance.plat_id))
            hostid_dict[host_id] = instance

        metric = Metric("mysql.performance.slow_queries_cnt")
        series = TSDBData.get_data_with_cache(
            table_name=resource.commons.trans_bkcloud_rt_bizid("{}_{}".format(self.bk_biz_id, metric.result_table_id)),
            select_field="MAX({}) as {}".format(metric.item, metric.item),
            filter_dict={"bk_biz_id": str(self.bk_biz_id)},
            group_by_field=["ip", "bk_cloud_id"],
        )

        suggestions = []

        for data in series:
            hostid = host_key(ip=data["ip"], plat_id=data["plat_id"])
            if hostid in hostid_dict and data["slow_queries_cnt"] > 1:
                suggestions.append(
                    {
                        "component": "mysql",
                        "content": _("检测到 %s 实例的MySQL有慢查询产生，建议查看并优化SQL语句") % hostid_dict[hostid].instance_name,
                    }
                )

        return suggestions


class MonitorStatus(object):
    UNSET = "unset"
    SLIGHT = "slight"
    SERIOUS = "serious"
    NORMAL = "normal"


class BaseMonitorInfo(object):
    SCENARIO = []

    @classmethod
    def check_event(cls, event):
        """校验event是否属于当前模块"""
        scenario = event.origin_config.get("scenario", "")
        return scenario in cls.SCENARIO

    def __init__(self, bk_biz_id, events):
        self.bk_biz_id = bk_biz_id
        self.events = events
        self.event_count = len(events)
        self.status = self.get_status()

    def get_status(self):
        """获取模块状态：未接入，无告警，有告警"""
        raise NotImplementedError

    @property
    def get_abnormal_status(self):
        """获取告警是属于普通告警，还是严重告警状态"""
        for e in self.events:
            if e.level == 1:
                return MonitorStatus.SERIOUS

        # 轻微告警
        return MonitorStatus.SLIGHT

    def get_info(self):
        status_mapping = {
            MonitorStatus.UNSET: self.no_access_info,
            MonitorStatus.SLIGHT: self.abnormal_info,
            MonitorStatus.SERIOUS: self.abnormal_info,
            MonitorStatus.NORMAL: self.normal_info,
        }
        info = status_mapping[self.status]()
        info.update(status=self.status)
        return info

    def no_access_info(self):
        """
        获取未接入时的数据
        :return:
        """
        raise NotImplementedError

    def normal_info(self):
        """
        获取无告警时的数据
        :return:
        """
        raise NotImplementedError

    def abnormal_info(self):
        """
        获取有告警时的数据
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def get_anomaly_msg(event):
        return event.origin_alarm["anomaly"].get(str(event.level), {}).get("anomaly_message", "")


class ServiceMonitorInfo(BaseMonitorInfo):
    SCENARIO = ["component", "service_module"]

    def get_status(self):
        """获取模块状态：未接入，无告警，有告警"""
        if self.event_count > 0:
            return self.get_abnormal_status

        has_collect = CollectConfigMeta.objects.filter(label__in=self.SCENARIO, bk_biz_id=self.bk_biz_id).exists()
        if has_collect > 0:
            # 无告警
            return MonitorStatus.NORMAL

        # 未接入
        return MonitorStatus.UNSET

    def no_access_info(self):
        return {"step": 1}

    def normal_info(self):
        strategy_count = StrategyModel.objects.filter(bk_biz_id=self.bk_biz_id, scenario__in=self.SCENARIO).count()
        return {"no_monitor_target": strategy_count > 0}

    def abnormal_info(self):
        self.events.sort(key=lambda x: x.level)
        now_time = now()
        search_time = now_time + datetime.timedelta(minutes=-10)
        strategies = StrategyModel.objects.filter(
            bk_biz_id=self.bk_biz_id, update_time__gte=search_time, scenario__in=self.SCENARIO
        )

        abnormal_events = []
        for e in self.events:
            abnormal_events.append(
                {
                    "event_id": e.id,
                    "content": self.get_anomaly_msg(e),
                    "strategy_name": e.origin_config["name"],
                    "level": e.level,
                }
            )

        operations = []
        for s in strategies:
            total_seconds = (now_time - s.update_time).total_seconds()
            time_str = hms_string(
                total_seconds, day_unit=_("天"), hour_unit=_("小时"), minute_unit=_("分钟"), second_unit=_("秒")
            )
            operations.append(_("{}前{}修改了告警策略：{}").format(time_str, s.update_user, s.name))

        return {"abnormal_events": abnormal_events, "operations": operations}


class ProcessMonitorInfo(BaseMonitorInfo):
    SCENARIO = ["host_process"]

    def get_status(self):
        if self.event_count > 0:
            return self.get_abnormal_status
        api_result = resource.cc.get_process(bk_biz_id=self.bk_biz_id)
        # 如果cmdb没有配置进程视为未接入

        if len(api_result) > 0:
            return MonitorStatus.NORMAL

        return MonitorStatus.UNSET

    def no_access_info(self):
        return {"step": 1}

    def abnormal_info(self):
        abnormal_events = []
        level_count = {
            1: 0,
            2: 0,
            3: 0,
        }
        for e in self.events:
            if sum(level_count.values()) < 8:
                items = e.origin_config["item_list"]
                try:
                    if e.origin_alarm["data"]["dimensions"].get("bk_target_ip", ""):
                        ip = e.origin_alarm["data"]["dimensions"]["bk_target_ip"]
                    else:
                        ip = e.origin_alarm["data"]["dimensions"]["ip"]
                except KeyError:
                    continue

                process = items[0]["item_name"]
                anomaly_message = self.get_anomaly_msg(e)
                content = _("主机“{}”的{}{}").format(ip, process, anomaly_message)
                abnormal_events.append(
                    {"event_id": e.id, "content": content, "type": "serious" if e.level == 1 else "warning"}
                )

            level_count[e.level] += 1

        return {
            "abnormal_events": abnormal_events,
            "serious_count": level_count[1],
            "warning_count": level_count[2],
            "notice_count": level_count[3],
            "has_more": self.event_count > 8,
        }

    def normal_info(self):
        strategy_count = StrategyModel.objects.filter(bk_biz_id=self.bk_biz_id, scenario=self.SCENARIO).count()
        return {"has_monitor": strategy_count > 0}


class OsMonitorInfo(BaseMonitorInfo):
    SCENARIO = ["os"]

    def get_status(self):
        if self.event_count > 0:
            return self.get_abnormal_status

        # 判断CPU使用率，如果有则视为接入了
        data_source = load_data_source(DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES)(
            table="system.cpu_summary",
            metrics=[{"field": "usage", "method": "COUNT", "alias": "count"}],
            filter_dict={"time__gt": "5m", "bk_biz_id": str(self.bk_biz_id)},
        )
        api_result = data_source.query_data(limit=1)
        return MonitorStatus.NORMAL if api_result and api_result[0]["count"] > 0 else MonitorStatus.UNSET

    def no_access_info(self):
        return {
            "step": 1,
        }

    def normal_info(self):
        strategy_count = StrategyModel.objects.filter(bk_biz_id=self.bk_biz_id, scenario__in=self.SCENARIO).count()
        return {"strategy_count": strategy_count}

    def abnormal_info(self):
        high_risk_label = {
            "bk_monitor.system.load.load5": _("5分钟平均负载"),
            "bk_monitor.system.cpu_summary.usage": _("CPU总使用率"),
            "bk_monitor.system.mem.pct_used": _("应用内存使用占比"),
            "bk_monitor.system.disk.in_use": _("磁盘使用率"),
            "bk_monitor.disk-readonly-gse": _("磁盘只读"),
            "bk_monitor.disk-full-gse": _("磁盘写满"),
            "bk_monitor.ping-gse": _("PING不可达"),
            "bk_monitor.os_restart": _("系统重新启动"),
        }
        serious_count = 0
        temp_count = 0

        high_risk = []
        other = []
        for e in self.events:
            metric_id = e.origin_config["item_list"][0]["metric_id"]
            if temp_count < 8:
                try:
                    if e.origin_alarm["data"]["dimensions"].get("bk_target_ip", ""):
                        ip = e.origin_alarm["data"]["dimensions"]["bk_target_ip"]
                    else:
                        ip = e.origin_alarm["data"]["dimensions"]["ip"]
                except KeyError:
                    continue

                content = _("主机“{}”的{}").format(ip, self.get_anomaly_msg(e))

                if metric_id in high_risk_label:
                    high_risk.append({"event_id": e.id, "content": content, "type": "serious"})
                    serious_count += 1
                else:
                    other.append({"event_id": e.id, "content": content, "type": "warning"})
            else:
                if metric_id in high_risk_label:
                    serious_count += 1

            temp_count += 1

        return {
            "high_risk": high_risk,
            "other": other,
            "has_more": self.event_count > 8,
            "high_risk_count": serious_count,
            "other_count": temp_count - serious_count,
        }


class UptimeCheckMonitorInfo(BaseMonitorInfo):
    SCENARIO = ["uptimecheck"]

    def get_status(self):
        if self.event_count > 0:
            return self.get_abnormal_status

        if UptimeCheckTask.objects.filter(bk_biz_id=self.bk_biz_id).exists():
            return MonitorStatus.NORMAL

        return MonitorStatus.UNSET

    def no_access_info(self):
        node_exist = UptimeCheckNode.objects.filter(Q(bk_biz_id=self.bk_biz_id) | Q(is_common=True)).exists()
        return {"step": 2 if node_exist else 1}

    def normal_info(self):
        task_list = UptimeCheckTask.objects.filter(bk_biz_id=self.bk_biz_id)
        notice_task = []
        warning_task = []
        for task in task_list:
            available = resource.uptime_check.get_recent_task_data({"task_id": task.id, "type": "available"})
            task_dict = {"task_id": task.id, "task_name": task.name, "available": available.get("available")}
            if task_dict["available"] is not None:
                task_dict["available"] = task_dict["available"] * 100
                if task_dict["available"] < 60:
                    warning_task.append(task_dict)
                elif task_dict["available"] < 80:
                    notice_task.append(task_dict)

        carrieroperator_count = (
            UptimeCheckNode.objects.filter(Q(bk_biz_id=self.bk_biz_id) | Q(is_common=True))
            .values("carrieroperator")
            .distinct()
            .count()
        )

        return {"notice_task": notice_task, "warning_task": warning_task, "single_supplier": carrieroperator_count == 1}

    def get_task_id(self, event):
        rt_query_config = event.origin_config["item_list"][0]["rt_query_config"]
        for condition in rt_query_config.get("agg_condition", []):
            if condition["key"] == "task_id":
                task_id = condition["value"]
                return int(task_id[0])

    def abnormal_info(self):
        abnormal_events_dick = {}
        for e in self.events:
            try:
                task_id = self.get_task_id(e)
            except Exception:
                continue
            else:
                abnormal_events_dick[task_id] = {
                    "event_id": e.id,
                    "task_id": task_id,
                    "title": e.origin_config["item_list"][0]["name"],
                }

        task_list = UptimeCheckTask.objects.filter(id__in=[e["task_id"] for e in list(abnormal_events_dick.values())])
        for task in task_list:
            title = abnormal_events_dick[task.id]["title"]
            title = "{}{}".format(task.name, title)
            abnormal_events_dick[task.id].update(title=title)

        now_time = now()
        search_time = now_time + datetime.timedelta(minutes=-10)
        strategies = StrategyModel.objects.filter(
            bk_biz_id=self.bk_biz_id, update_time__gte=search_time, scenario__in=self.SCENARIO
        )
        operations = []
        for s in strategies:
            total_seconds = (localtime(now_time) - s.update_time).total_seconds()
            time_str = hms_string(
                total_seconds, day_unit=_("天"), hour_unit=_("小时"), minute_unit=_("分钟"), second_unit=_("秒")
            )
            operations.append(_("{}前{}修改了告警策略：{}").format(time_str, s.update_user, s.name))

        all_node_status = resource.uptime_check.uptime_check_beat(bk_biz_id=self.bk_biz_id)
        node_status_mapping = {}
        for node_status in all_node_status:
            node_status_mapping[host_key(ip=node_status["ip"], bk_cloud_id=node_status["bk_cloud_id"])] = node_status

        node_list = UptimeCheckNode.objects.filter(Q(bk_biz_id=self.bk_biz_id) | Q(is_common=True))
        abnormal_node = []
        for node in node_list:
            status = int(node_status_mapping.get(host_key(ip=node.ip, bk_cloud_id=node.plat_id), {}).get("status"))
            if status is not None and status != 0:
                abnormal_node.append(
                    {
                        "ip": node.ip,
                        "bk_cloud_id": node.plat_id,
                        "name": node.name,
                        "status": status,
                        "isp": node.carrieroperator,
                    }
                )

        return {
            "task": {"abnormal_events": list(abnormal_events_dick.values()), "operations": operations},
            "node": {"abnormal_nodes": abnormal_node},
        }
