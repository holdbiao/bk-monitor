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

import logging
import time
import os
import arrow
import six
from collections import defaultdict
from functools import wraps
from multiprocessing.pool import ThreadPool

from django.db import connections
from django.contrib.auth import get_user_model
from django.db.utils import ConnectionDoesNotExist
from django.db.models import Count
from django.utils.translation import ugettext as _

from core.drf_resource import api, resource
from bkmonitor.utils import time_tools
from bkmonitor.utils.range import TIME_MATCH_CLASS_MAP
from bkmonitor.utils.range.period import TimeMatch, TimeMatchBySingle
from bkmonitor.models import (
    Alert,
    EventAction,
    NoticeGroup,
    StrategyModel,
    Event,
    Shield,
    QueryConfigModel,
    AlgorithmModel,
)
from monitor_api.models import MonitorSource, MonitorItem
from monitor_web.models import CollectConfigMeta, CollectorPluginMeta, CustomEventGroup, MetricListCache, CustomTSTable
from monitor_web.models.uptime_check import UptimeCheckTask
from monitor_web.plugin.constant import PluginType
from utils.business import get_all_activate_business

logger = logging.getLogger(__name__)
STATISTICS_CONCURRENT_NUMBER = os.getenv("STATISTICS_CONCURRENT_NUMBER", 20)


def nodeman_sql_to_result(sql):
    """
    向节点管理请求数据，并返回结果
    :param sql: sql语句
    :return: 数组结果
    """
    with connections["nodeman"].cursor() as cursor:
        cursor.execute(sql)
        desc = cursor.description
        result = [dict(list(zip([col[0] for col in desc], row))) for row in cursor.fetchall()]
    return result


class Metric(object):
    """
    指标定义
    """

    def __init__(self, metric_name, metric_value, dimensions=None):
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.dimensions = dimensions

    def transform(self, value):
        if isinstance(value, str) and "\\" in value:
            value = value.replace("\\", "\\\\")
        if isinstance(value, str) and '"' in value:
            value = value.replace('"', r"\"")
        return value

    def to_json(self):
        return {"metric_name": self.metric_name, "metric_value": self.metric_value, "dimensions": self.dimensions}

    def to_prometheus_text(self, namespace=None, timestamp=""):
        if namespace:
            actual_metric_name = "{}_{}".format(namespace, self.metric_name)
        else:
            actual_metric_name = self.metric_name

        if self.dimensions:
            dimensions = ",".join(
                '{}="{}"'.format(key, self.transform(value)) for key, value in self.dimensions.items()
            )
            dimensions = "{" + dimensions + "}"
        else:
            dimensions = ""

        prometheus_text = "{metric_name}{dimensions} {metric_value} {timestamp}".format(
            metric_name=actual_metric_name,
            dimensions=dimensions,
            metric_value=self.metric_value,
            timestamp=timestamp * 1000,
        )
        return prometheus_text


def register_metric(namespace, description=""):
    def wrapped_view(func):
        def _wrapped_view(*args, **kwargs):
            return func(*args, **kwargs)

        _wrapped_view.namespace = namespace
        _wrapped_view.description = description
        _wrapped_view.is_metric = True
        return wraps(func)(_wrapped_view)

    return wrapped_view


class MetricCollector(object):
    def __init__(self, collect_interval=300):
        # 业务缓存
        biz_list = api.cmdb.get_business()
        self.biz_info = {business.bk_biz_id: business for business in biz_list}

        # 策略缓存
        self.strategy_mapping = {}
        for strategy in StrategyModel.objects.values("id", "bk_biz_id", "name"):
            self.strategy_mapping[strategy["id"]] = strategy
        self.strategy_label_mapping = {}
        for query_config in QueryConfigModel.objects.values("strategy_id", "data_source_label", "data_type_label"):
            self.strategy_label_mapping[query_config["strategy_id"]] = {
                "data_source_label": query_config["data_source_label"],
                "data_type_label": query_config["data_type_label"],
            }

        # 上报时间
        self.collect_interval = collect_interval
        timestamp = arrow.now().timestamp
        self.report_ts = timestamp // self.collect_interval * self.collect_interval

    @property
    def time_range(self):
        # 取整
        return arrow.get(self.report_ts - self.collect_interval).datetime, arrow.get(self.report_ts).datetime

    def get_biz_name(self, bk_biz_id):
        """
        根据业务ID获取业务名称
        """
        return self.biz_info[int(bk_biz_id)].display_name if int(bk_biz_id) in self.biz_info else bk_biz_id

    def biz_exists(self, bk_biz_id):
        """
        业务是否存在
        """
        return bool(bk_biz_id) and int(bk_biz_id) in self.biz_info

    def get_biz_by_event_id(self, event_id):
        strategy_id = int(event_id.split(".")[2])
        if strategy_id in self.strategy_mapping:
            return self.strategy_mapping[strategy_id]["bk_biz_id"]
        return 0

    def concurrent_fetch(self, metric_methods):
        """
        并发获取指标数据
        :param metric_methods: 指标数据方法
        :return: 运营数据指标列表
        """

        def func_log(func, namespace):
            """
            记录指标计算事件
            :param func: 指标函数
            :param namespace: 命名空间
            """
            begin_time = time.time()

            try:
                result = func()
            except Exception as e:
                logger.exception("[statistics_data] collect metric->[%s] failed: %s", namespace, e)
                return []
            logger.info(
                "[statistics_data] collect metric->[%s] took %s ms",
                namespace,
                int((time.time() - begin_time) * 1000),
            )
            return result

        pool = ThreadPool(STATISTICS_CONCURRENT_NUMBER)
        data = {}
        futures = []
        for func in metric_methods:
            futures.append({func: pool.apply_async(func_log, kwds={"func": func, "namespace": func.namespace})})

        pool.close()
        pool.join()

        # 取值
        for future in futures:
            for method, func in future.items():
                data[method] = func.get()
        return data

    def collect(self, namespaces=None, response_format="prometheus"):
        """
        采集入口
        """
        metric_methods = self.list_metric_methods(namespaces)
        metric_data = self.concurrent_fetch(metric_methods)
        metric_groups = []
        for method, data in metric_data.items():
            if data:
                metric_groups.append(
                    {
                        "namespace": method.namespace,
                        "description": method.description,
                        "metrics": data,
                    }
                )

        if response_format == "json":
            for metric_group in metric_groups:
                metric_group.update({"metrics": [metric.to_json() for metric in metric_group["metrics"]]})
            return metric_groups

        metric_text_list = []
        # 转换为prometheus格式
        for group in metric_groups:
            metric_text_list.append("# {}".format(group["description"] or group["namespace"]))
            for metric in group["metrics"]:
                metric_text_list.append(
                    metric.to_prometheus_text(namespace=group["namespace"], timestamp=self.report_ts)
                )
        return "\n".join(metric_text_list)

    @property
    def registered_metrics(self):
        return [
            method
            for method in dir(self)
            if method != "registered_metrics"
            and callable(getattr(self, method))
            and getattr(getattr(self, method), "is_metric", None)
        ]

    def list_metric_methods(self, namespaces=None):
        """
        获取
        :param namespaces:
        :return:
        """
        namespaces = namespaces or []
        if isinstance(namespaces, six.text_type):
            namespaces = [namespaces]

        methods = []
        for metric in self.registered_metrics:
            method = getattr(self, metric)
            if not namespaces:
                methods.append(method)
            for namespace in namespaces:
                if method.namespace.startswith(namespace):
                    methods.append(method)
        return methods

    @classmethod
    def append_total_metric(cls, metrics):
        total = sum(metric.metric_value for metric in metrics)
        metrics.append(
            Metric(
                metric_name="total",
                metric_value=total,
            )
        )
        return metrics

    @register_metric("business_active", _("活跃业务"))
    def activate_business(self):
        active_business_list = get_all_activate_business()

        metrics = [
            Metric(
                metric_name="count",
                metric_value=1,
                dimensions={"target_biz_id": int(bk_biz_id), "target_biz_name": self.get_biz_name(bk_biz_id)},
            )
            for bk_biz_id in active_business_list
            if self.biz_exists(bk_biz_id)
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("business_migrate", _("迁移业务"))
    def migrate_business(self):
        try:
            old_monitor_source_queryset = MonitorSource.objects.using("monitor_api_3_1").filter(is_deleted=False)
            old_monitor_source_queryset = set(old_monitor_source_queryset.values_list("biz_id", flat=True))
        except ConnectionDoesNotExist:
            old_monitor_source_queryset = set()

        new_monitor_source_queryset = set(StrategyModel.objects.values_list("bk_biz_id", flat=True))

        migrate_business_list = new_monitor_source_queryset & old_monitor_source_queryset

        metrics = [
            Metric(
                metric_name="count",
                metric_value=1,
                dimensions={"target_biz_id": int(bk_biz_id), "target_biz_name": self.get_biz_name(bk_biz_id)},
            )
            for bk_biz_id in migrate_business_list
            if self.biz_exists(bk_biz_id)
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("old_monitor_disabled_strategy_biz", _("老监控策略全部关闭的业务数"))
    def old_monitor_disabled_strategy(self):
        try:
            old_monitor_source_queryset = list(
                MonitorItem.objects.using("monitor_api_3_1").filter(is_deleted=False).values()
            )
        except ConnectionDoesNotExist:
            old_monitor_source_queryset = set()

        all_old_strategy = defaultdict(list)
        for queryset in old_monitor_source_queryset:
            all_old_strategy[queryset["biz_id"]].append(queryset["is_enabled"])

        business_list = [strategy_biz for strategy_biz, value in all_old_strategy.items() if not any(value)]

        metrics = [
            Metric(
                metric_name="count",
                metric_value=1,
                dimensions={"target_biz_id": int(bk_biz_id), "target_biz_name": self.get_biz_name(bk_biz_id)},
            )
            for bk_biz_id in business_list
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("use_aiops_strategy", "智能异常策略")
    def use_aiops_strategy(self):
        strategy_count = defaultdict(int)
        for algorithm_config in AlgorithmModel.objects.values("strategy_id", "type"):
            if algorithm_config["type"] == AlgorithmModel.AlgorithmChoices.IntelligentDetect:
                strategy_id = algorithm_config["strategy_id"]
                if strategy_id in self.strategy_mapping:
                    target_biz_id = self.strategy_mapping[strategy_id]["bk_biz_id"]
                    strategy_count[target_biz_id] += 1

        metrics = [
            Metric(
                metric_name="count",
                metric_value=count,
                dimensions={
                    "target_biz_id": target_biz_id,
                    "target_biz_name": self.get_biz_name(target_biz_id),
                },
            )
            for target_biz_id, count in strategy_count.items()
            if self.biz_exists(target_biz_id)
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("new_monitor_disabled_strategy_biz", _("新监控策略全部关闭的业务数"))
    def new_monitor_disabled_strategy(self):
        new_monitor_source_queryset = list(StrategyModel.objects.values())

        all_new_strategy = defaultdict(list)
        for queryset in new_monitor_source_queryset:
            all_new_strategy[queryset["bk_biz_id"]].append(queryset["is_enabled"])

        business_list = [strategy_biz for strategy_biz, value in all_new_strategy.items() if not any(value)]

        metrics = [
            Metric(
                metric_name="count",
                metric_value=1,
                dimensions={"target_biz_id": int(bk_biz_id), "target_biz_name": self.get_biz_name(bk_biz_id)},
            )
            for bk_biz_id in business_list
            if self.biz_exists(bk_biz_id)
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("user_recent_login", _("用户登陆"))
    def user(self):
        user_model = get_user_model()
        metrics = [
            Metric(
                metric_name="total", metric_value=user_model.objects.filter(last_login__gte=self.time_range[0]).count()
            )
        ]
        return metrics

    @register_metric("cmdb_host", _("主机上报"))
    def report_host(self):

        # 所有总计的metrics
        total_metrics = []

        # 1.获取主机上报总数 (正常上报数)
        biz_cnt_map = defaultdict(int)
        data_list = api.metadata.get_ts_data(
            {
                "sql": "select count(idle) as cnt from system.cpu_summary where time>'3m' "
                "group by minute1, bk_biz_id, bk_cloud_id"
            }
        )
        for item in data_list["list"]:
            bk_biz_id = item["bk_biz_id"]
            if not bk_biz_id:
                continue
            bk_cloud_id = item["bk_cloud_id"]
            cnt = item["cnt"]
            biz_cnt_map[(bk_biz_id, bk_cloud_id)] = max(biz_cnt_map[(bk_biz_id, bk_cloud_id)], cnt)

        # 2.获取节点管理Agent安装状态 正式环境测试耗时：1s+
        biz_host_status_list = nodeman_sql_to_result(
            """
            select count(a.bk_host_id)host_count, a.bk_biz_id, a.bk_cloud_id, b.status from node_man_host as a
            inner join (select name, status, bk_host_id from node_man_processstatus) as b on
            a.bk_host_id = b.bk_host_id and b.name="gseagent" group by bk_biz_id, status, bk_cloud_id;
        """
        )

        # 正常的basereport数量 正式环境测试耗时: 1s+, 结果: 11w+
        biz_basereport_count = nodeman_sql_to_result(
            """
            select bk_biz_id, count(bk_biz_id) as basereport_count, bk_cloud_id from
             (select a.bk_host_id, a.bk_biz_id, a.bk_cloud_id from node_man_host as a
             inner join (select name, status, bk_host_id from node_man_processstatus) as b
             on a.bk_host_id = b.bk_host_id and b.name="basereport" and b.status="RUNNING"
             group by bk_biz_id, status, bk_cloud_id, a.bk_host_id)c group by bk_biz_id, bk_cloud_id;
        """
        )

        try:
            clouds = api.cmdb.search_cloud_area()
            cloud_id_to_name = {cloud["bk_cloud_id"]: cloud["bk_cloud_name"] for cloud in clouds}
        except Exception:
            cloud_id_to_name = {}

        # 正常上报的主机(NORMAL)
        metrics = [
            Metric(
                metric_name="count",
                metric_value=count,
                dimensions={
                    "target_biz_id": int(biz_info[0]),
                    "target_biz_name": self.get_biz_name(biz_info[0]),
                    "target_cloud_id": biz_info[1],
                    "target_cloud_name": cloud_id_to_name.get(int(biz_info[1]), biz_info[1]),
                    "status": "NORMAL",
                },
            )
            for biz_info, count in biz_cnt_map.items()
            if self.biz_exists(biz_info[0])
        ]

        # 正常上报的总计
        total = sum(metric.metric_value for metric in metrics)
        total_metrics.append(
            Metric(
                metric_name="normal_total",
                metric_value=total,
            )
        )

        # 正常上报的业务数总计
        all_biz_id = {biz_info[0] for biz_info, _ in biz_cnt_map.items()}
        total_metrics.append(
            Metric(
                metric_name="normal_report_business_total",
                metric_value=len(all_biz_id),
            )
        )

        # Agent未知(UNKNOWN)、Agent异常(TERMINATED)、Agent正常(RUNNING)、Agent未安装(NOT_INSTALLED)的主机
        metrics.extend(
            [
                Metric(
                    metric_name="count",
                    metric_value=item["host_count"],
                    dimensions={
                        "target_biz_id": int(item["bk_biz_id"]),
                        "target_biz_name": self.get_biz_name(item["bk_biz_id"]),
                        "target_cloud_id": item["bk_cloud_id"],
                        "target_cloud_name": cloud_id_to_name.get(int(item["bk_cloud_id"]), item["bk_cloud_id"]),
                        "status": item["status"],
                    },
                )
                for item in biz_host_status_list
                if self.biz_exists(item["bk_biz_id"])
            ]
        )

        # Basereport正常的机器
        metrics.extend(
            [
                Metric(
                    metric_name="count",
                    metric_value=item["basereport_count"],
                    dimensions={
                        "target_biz_id": int(item["bk_biz_id"]),
                        "target_biz_name": self.get_biz_name(item["bk_biz_id"]),
                        "target_cloud_id": item["bk_cloud_id"],
                        "target_cloud_name": cloud_id_to_name.get(int(item["bk_cloud_id"]), item["bk_cloud_id"]),
                        "status": "BASEREPORT_RUNNING",
                    },
                )
                for item in biz_basereport_count
                if self.biz_exists(item["bk_biz_id"])
            ]
        )

        # 3.计算每个业务每个云区域无数据上报(NO_DATA_REPORT)的机器总数
        # agent正常的机器-主机上报总数
        # {bk_biz_id: {cloud_id: count}}
        no_data_report = defaultdict(dict)
        for metric in metrics:
            bk_cloud_id = int(metric.dimensions["target_cloud_id"])
            if metric.dimensions["target_biz_id"] not in no_data_report:
                no_data_report[metric.dimensions["target_biz_id"]] = {}
            if bk_cloud_id not in no_data_report[metric.dimensions["target_biz_id"]]:
                no_data_report[metric.dimensions["target_biz_id"]][bk_cloud_id] = 0

            # 无数据上报总数=agent正常的机器-主机上报总数
            if metric.dimensions["status"] in ["BASEREPORT_RUNNING"]:
                no_data_report[metric.dimensions["target_biz_id"]][bk_cloud_id] += metric.metric_value
            if metric.dimensions["status"] in ["NORMAL"]:
                no_data_report[metric.dimensions["target_biz_id"]][bk_cloud_id] -= metric.metric_value

        metrics.extend(
            [
                Metric(
                    metric_name="count",
                    metric_value=no_data_report[bk_biz_id][bk_cloud_id],
                    dimensions={
                        "target_biz_id": int(bk_biz_id),
                        "target_biz_name": self.get_biz_name(bk_biz_id),
                        "target_cloud_id": bk_cloud_id,
                        "target_cloud_name": cloud_id_to_name.get(int(bk_cloud_id), bk_cloud_id),
                        "status": "NO_DATA_REPORT",
                    },
                )
                for bk_biz_id in no_data_report
                for bk_cloud_id in no_data_report[bk_biz_id]
                if self.biz_exists(bk_biz_id)
            ]
        )

        # 计算每个业务的实际机器总数
        # 每个业务主机数：
        # (Agent未知(UNKNOWN)+Agent异常(TERMINATED)+Agent未安装(NOT_INSTALLED)+Agent正常(RUNNING))
        # {bk_biz_id: {cloud_id: count}}
        total_hosts = defaultdict(dict)
        for metric in metrics:
            bk_cloud_id = int(metric.dimensions["target_cloud_id"])
            if metric.dimensions["target_biz_id"] not in total_hosts:
                total_hosts[metric.dimensions["target_biz_id"]] = {}
            if bk_cloud_id not in total_hosts[metric.dimensions["target_biz_id"]]:
                total_hosts[metric.dimensions["target_biz_id"]][bk_cloud_id] = 0

            # 无数据上报总数=agent正常的机器-主机上报总数
            if metric.dimensions["status"] in ["UNKNOWN", "TERMINATED", "NOT_INSTALLED", "RUNNING"]:
                total_hosts[metric.dimensions["target_biz_id"]][bk_cloud_id] += metric.metric_value

        metrics.extend(
            [
                Metric(
                    metric_name="count",
                    metric_value=total_hosts[bk_biz_id][bk_cloud_id],
                    dimensions={
                        "target_biz_id": int(bk_biz_id),
                        "target_biz_name": self.get_biz_name(bk_biz_id),
                        "target_cloud_id": bk_cloud_id,
                        "target_cloud_name": cloud_id_to_name.get(int(bk_cloud_id), bk_cloud_id),
                        "status": "ALL_HOSTS",
                    },
                )
                for bk_biz_id in total_hosts
                for bk_cloud_id in total_hosts[bk_biz_id]
                if self.biz_exists(bk_biz_id)
            ]
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "BASEREPORT_RUNNING")
        total_metrics.append(
            Metric(
                metric_name="basereport_running_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "TERMINATED")
        total_metrics.append(
            Metric(
                metric_name="terminated_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "UNKNOWN")
        total_metrics.append(
            Metric(
                metric_name="unknown_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "RUNNING")
        total_metrics.append(
            Metric(
                metric_name="running_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "NOT_INSTALLED")
        total_metrics.append(
            Metric(
                metric_name="not_installed_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "NO_DATA_REPORT")
        total_metrics.append(
            Metric(
                metric_name="no_data_report_total",
                metric_value=total,
            )
        )

        total = sum(metric.metric_value for metric in metrics if metric.dimensions["status"] == "ALL_HOSTS")
        total_metrics.append(
            Metric(
                metric_name="all_hosts_total",
                metric_value=total,
            )
        )

        metrics.extend(total_metrics)
        return metrics

    @register_metric("event_action", _("事件状态"))
    def event_action(self):
        event_actions = EventAction.objects.filter(
            create_time__range=self.time_range,
            operate__in=[EventAction.Operate.CREATE, EventAction.Operate.RECOVER, EventAction.Operate.CLOSE],
        ).values("event_id", "operate", "id")

        action_count = defaultdict(int)
        for action in event_actions:
            target_biz_id = self.get_biz_by_event_id(action["event_id"])
            action_count[(target_biz_id, action["operate"])] += 1

        metrics = [
            Metric(
                metric_name="count",
                metric_value=count,
                dimensions={
                    "target_biz_id": action_info[0],
                    "target_biz_name": self.get_biz_name(action_info[0]),
                    "operate": action_info[1],
                },
            )
            for action_info, count in action_count.items()
            if self.biz_exists(action_info[0])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("event", _("未恢复事件"))
    def event(self):
        # 告警数量统计
        # https://stackoverflow.com/questions/5231907/order-by-null-in-mysql
        # order by null 在聚合条件sql下能提升性能
        groups = (
            Event.objects.filter(notify_status__gte=0, status=Event.EventStatus.ABNORMAL)
            .values("bk_biz_id", "is_shielded", "strategy_id")
            .order_by()
            .annotate(count=Count("event_id"))
        )

        event_count = defaultdict(int)
        for group in groups:
            if group["strategy_id"] not in self.strategy_label_mapping:
                continue
            label_info = self.strategy_label_mapping[group["strategy_id"]]
            key = (
                group["bk_biz_id"],
                group["is_shielded"],
                label_info["data_source_label"],
                label_info["data_type_label"],
            )
            event_count[key] += group["count"]

        metrics = [
            Metric(
                metric_name="count",
                metric_value=count,
                dimensions={
                    "target_biz_id": key[0],
                    "target_biz_name": self.get_biz_name(key[0]),
                    "is_shielded": "1" if key[1] else "0",
                    "data_source_label": key[2],
                    "data_type_label": key[3],
                },
            )
            for key, count in event_count.items()
            if self.biz_exists(key[0])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("notify", _("通知"))
    def notify(self):
        alerts = (
            Alert.objects.filter(
                create_time__range=self.time_range,
            )
            .values("method", "status", "alert_collect_id", "event_id", "username")
            .order_by()
        )

        # 使用字典，仅保留一个alert_collect_id
        alert_collects = defaultdict(list)
        for alert in alerts:
            alert_collects[alert["alert_collect_id"]].append(alert)

        metrics = [
            Metric(
                metric_name="count",
                metric_value=len(alert_collects[alert]),
                dimensions={
                    "target_biz_id": self.get_biz_by_event_id(alert_collects[alert][0]["event_id"]),
                    "target_biz_name": self.get_biz_name(
                        self.get_biz_by_event_id(alert_collects[alert][0]["event_id"])
                    ),
                    "status": alert_collects[alert][0]["status"],
                    "method": alert_collects[alert][0]["method"],
                    "alert_username": alert_collects[alert][0]["username"],
                },
            )
            for alert in alert_collects
            if self.biz_exists(self.get_biz_by_event_id(alert_collects[alert][0]["event_id"]))
        ]

        metrics = self.append_total_metric(metrics)
        return metrics

    @register_metric("plugin", "插件")
    def plugin(self):
        groups = (
            CollectorPluginMeta.objects.filter(
                plugin_type__in=[
                    PluginType.EXPORTER,
                    PluginType.DATADOG,
                    PluginType.JMX,
                    PluginType.SCRIPT,
                    PluginType.PUSHGATEWAY,
                    PluginType.SNMP,
                ]
            )
            .values("bk_biz_id", "plugin_type", "label")
            .order_by()
            .annotate(count=Count("plugin_id"))
        )

        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]) if group["bk_biz_id"] else _("全局"),
                    "plugin_type": group["plugin_type"],
                    "plugin_label": group["label"],
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)
        return metrics

    @register_metric("collect_config", "采集配置")
    def collect_config(self):
        groups = (
            CollectConfigMeta.objects.values("bk_biz_id", "plugin_id", "collect_type", "label")
            .order_by()
            .annotate(count=Count("id"))
        )

        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                    "collect_type": group["collect_type"],
                    "plugin_label": group["label"],
                    "plugin_id": group["plugin_id"],
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("strategy", "策略配置")
    def strategy(self):

        strategy_count = defaultdict(int)
        for strategy_id, label_info in self.strategy_label_mapping.items():
            if strategy_id not in self.strategy_mapping:
                continue
            target_biz_id = self.strategy_mapping[strategy_id]["bk_biz_id"]
            strategy_count[(target_biz_id, label_info["data_source_label"], label_info["data_type_label"])] += 1

        metrics = [
            Metric(
                metric_name="count",
                metric_value=count,
                dimensions={
                    "target_biz_id": strategy_info[0],
                    "target_biz_name": self.get_biz_name(strategy_info[0]),
                    "data_source_label": strategy_info[1],
                    "data_type_label": strategy_info[2],
                },
            )
            for strategy_info, count in strategy_count.items()
            if self.biz_exists(strategy_info[0])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("notice_group", "通知组")
    def notice_group(self):
        groups = NoticeGroup.objects.values("bk_biz_id").order_by().annotate(count=Count("id"))
        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("uptimecheck_task", "拨测任务")
    def uptimecheck_task(self):
        groups = UptimeCheckTask.objects.values("bk_biz_id", "protocol").order_by().annotate(count=Count("id"))
        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                    "protocol": group["protocol"],
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("grafana_dashboard", "Grafana 仪表盘")
    def grafana_dashboard(self):
        metrics = []
        all_organization = api.grafana.get_all_organization()["data"]
        for org in all_organization:
            org_name = org["name"]
            if not org_name.isdigit():
                continue
            if int(org_name) not in self.biz_info:
                continue

            dashboards = api.grafana.search_folder_or_dashboard(type="dash-db", org_id=org["id"])["data"]

            metrics.append(
                Metric(
                    metric_name="count",
                    metric_value=len(dashboards),
                    dimensions={"target_biz_id": int(org_name), "target_biz_name": self.get_biz_name(org_name)},
                )
            )

            panel_count = 0
            for dashboard in dashboards:
                dashboard_info = api.grafana.get_dashboard_by_uid(uid=dashboard["uid"], org_id=org["id"])["data"].get(
                    "dashboard", {}
                )
                for panel in dashboard_info.get("panels", []):
                    if panel["type"] == "row":
                        # 如果是行类型，需要统计嵌套数量
                        panel_count += len(panel.get("panels", []))
                    else:
                        panel_count += 1

            metrics.append(
                Metric(
                    metric_name="panel_count",
                    metric_value=panel_count,
                    dimensions={"target_biz_id": int(org_name), "target_biz_name": self.get_biz_name(org_name)},
                )
            )

        return metrics

    @register_metric("custom_report", "自定义上报")
    def custom_report(self):
        groups = list(
            CustomEventGroup.objects.values("bk_biz_id", "scenario", "type")
            .exclude(type="keywords")
            .order_by()
            .annotate(count=Count("bk_event_group_id"))
        )
        # 增加自定义时序数据
        groups += list(
            CustomTSTable.objects.all()
            .values("bk_biz_id", "scenario")
            .order_by()
            .annotate(count=Count("time_series_group_id"))
        )
        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                    "scenario": group["scenario"],
                    "group_type": group.get("type", "time_series"),
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("monitor_metric", "监控指标")
    def monitor_metric(self):
        groups = (
            MetricListCache.objects.values("bk_biz_id", "data_source_label", "data_type_label")
            .order_by()
            .annotate(count=Count("id"))
        )
        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                    "data_source_label": group["data_source_label"],
                    "data_type_label": group["data_type_label"],
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("alarm_shield", "告警屏蔽")
    def alarm_shield(self):
        groups = (
            Shield.objects.filter(is_enabled=True, is_deleted=False, failure_time__gte=time_tools.now())
            .values("bk_biz_id", "begin_time", "end_time", "cycle_config")
            .annotate(count=Count("id"))
        )
        match_groups = defaultdict(int)
        now_time = arrow.now()

        # 获取周期，判断是否match
        for group in groups:
            shield_type = int(group["cycle_config"].get("type", "-1"))
            begin_time = TimeMatch.convert_datetime_to_arrow(group.get("begin_time"))
            end_time = TimeMatch.convert_datetime_to_arrow(group.get("end_time"))

            time_match_class = TIME_MATCH_CLASS_MAP.get(shield_type, TimeMatchBySingle)
            time_check = time_match_class(group["cycle_config"], begin_time, end_time)
            if time_check.is_match(now_time):
                match_groups[group["bk_biz_id"]] += group["count"]

        metrics = [
            Metric(
                metric_name="count",
                metric_value=match_groups[group],
                dimensions={"target_biz_id": group, "target_biz_name": self.get_biz_name(group)},
            )
            for group in match_groups
            if self.biz_exists(group)
        ]

        metrics = self.append_total_metric(metrics)

        return metrics

    @register_metric("legacy_subscription", "野订阅")
    def legacy_subscription(self):
        try:
            list_legacy_subscriptions = resource.collecting.list_legacy_subscription()
        except Exception as e:
            logger.error(f"[failed get list_legacy_subscriptions] {e}")
            list_legacy_subscriptions = {"wild_subscription_ids": []}

        metrics = [
            Metric(
                metric_name="total",
                metric_value=len(list_legacy_subscriptions.get("wild_subscription_ids", [])),
            )
        ]

        return metrics

    @register_metric("strategy_alert", "采集周期内策略告警事件数")
    def strategy_alert(self):
        event_ids = EventAction.objects.filter(
            create_time__range=self.time_range,
            operate__in=[EventAction.Operate.CREATE, EventAction.Operate.RECOVER, EventAction.Operate.CLOSE],
        ).values_list("event_id")

        groups = (
            Event.objects.filter(event_id__in=event_ids)
            .values("bk_biz_id", "strategy_id", "status")
            .order_by()
            .annotate(count=Count("strategy_id"))
        )

        metrics = [
            Metric(
                metric_name="count",
                metric_value=group["count"],
                dimensions={
                    "target_biz_id": group["bk_biz_id"],
                    "target_biz_name": self.get_biz_name(group["bk_biz_id"]),
                    "status": group["status"],
                    "strategy_id": group["strategy_id"],
                    "strategy_name": self.strategy_mapping.get(group["strategy_id"], {}).get("name"),
                },
            )
            for group in groups
            if self.biz_exists(group["bk_biz_id"])
        ]

        metrics = self.append_total_metric(metrics)

        return metrics
