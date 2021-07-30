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
from collections import OrderedDict, defaultdict

from django.db import models
from django.db.models import Count, Q, Subquery
from django.utils import timezone
from django.utils.translation import ugettext as _

from bkmonitor.models import ItemModel, StrategyModel, QueryConfigModel
from core.drf_resource.exceptions import CustomException
from bkmonitor.models.base import Action, Event, NoticeGroup
from core.drf_resource import resource
from bkmonitor.utils.cache import CacheType
from bkmonitor.utils.common_utils import parse_host_id
from bkmonitor.utils.time_tools import get_datetime_range, localtime
from bkmonitor.views import serializers
from bkmonitor.views.serializers import BusinessOnlySerializer
from core.drf_resource import api
from core.drf_resource.contrib.cache import CacheResource
from monitor_web.overview.tools import (
    MonitorStatus,
    OsMonitorInfo,
    ProcessMonitorInfo,
    ServiceMonitorInfo,
    UptimeCheckMonitorInfo,
)
from utils.host_index_backend import host_index_backend


class AlarmRankResource(CacheResource):
    """
    告警类型排行
    """

    cache_type = CacheType.OVERVIEW

    class RequestSerializer(BusinessOnlySerializer):
        days = serializers.IntegerField(default=7, label=_("统计天数"))

    def get_alarm_item(self, begin_time, end_time, bk_biz_id, strategy_name):
        # 记录当前告警项
        # todo use event_archive
        this_date_event = (
            Event.objects.filter(
                Q(bk_biz_id__in=[bk_biz_id]) & (Q(end_time__range=(begin_time, end_time)) | Q(end_time__isnull=True))
            )
            .filter(is_shielded=False)
            .values(
                "strategy_id",
            )
            .annotate(total=models.Count("strategy_id"))
            .order_by("-total")[:10]
        )

        ret = {}
        for event in this_date_event:
            # 如果被删除了
            if not strategy_name.get(event["strategy_id"], None):
                continue
            if strategy_name[event["strategy_id"]] not in ret:
                ret[strategy_name[event["strategy_id"]]] = event["total"]
            else:
                ret[strategy_name[event["strategy_id"]]] += event["total"]
        # ->{name:total,...}
        return ret

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        days = validated_request_data["days"]

        # 策略和监控维度名字的映射
        query_configs = QueryConfigModel.objects.values("metric_id", "strategy_id")
        items = ItemModel.objects.values("name", "strategy_id")

        strategy_id_items = defaultdict(dict)
        for query_config in query_configs:
            strategy_id_items[query_config["strategy_id"]]["metric_id"] = query_config["metric_id"]
        for item in items:
            strategy_id_items[item["strategy_id"]]["name"] = item["name"]

        strategy_names = {}
        for strategy_id, strategy_name in strategy_id_items.items():
            if "metric_id" not in strategy_name or "name" not in strategy_name:
                continue
            strategy_names[strategy_id] = "{}|{}".format(strategy_name["metric_id"], strategy_name["name"])

        # 判断是否有数据
        days_list = [1, 7, 30]
        for day in days_list:
            if days < day:
                days = day
            begin_time, end_time = get_datetime_range(
                "day",
                days,
                rounding=False,
            )
            this_monitor_item_set = self.get_alarm_item(begin_time, end_time, bk_biz_id, strategy_names)
            if this_monitor_item_set:
                break
        else:
            return {"data": [], "using_example_data": True, "days": days}
        # 记录上次告警项,现在的时间减去days周期的时间
        last_begin_time, last_end_time = get_datetime_range(
            "day", days, rounding=False, now=localtime(timezone.now()) - datetime.timedelta(days=days)
        )
        last_monitor_item_set = self.get_alarm_item(last_begin_time, last_end_time, bk_biz_id, strategy_names)

        default_list = []
        for k, v in list(this_monitor_item_set.items()):
            last_default_count = last_monitor_item_set.get(k, 0)
            # 上次有记录,判断增加还是减少
            if not last_default_count:
                if v > last_default_count:
                    status = 2
                elif k < last_default_count:
                    status = 0
                else:
                    status = 1
            # 上次没有记录,所以肯定是增加
            else:
                status = 2
            text = k.split("|", 1)
            default_list.append({"status": status, "text": text[1], "times": v, "metric_id": text[0]})
        data = sorted(default_list, key=lambda x: -x["times"])

        return {"data": data, "using_example_data": False, "days": days}


class AlarmCountInfoResource(CacheResource):
    """
    告警数量信息
    """

    RequestSerializer = BusinessOnlySerializer

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        events = resource.alert_events.query_events(
            bk_biz_ids=[bk_biz_id], days=7, conditions=[{"key": "event_status", "value": [Event.EventStatus.ABNORMAL]}]
        ).filter(is_shielded=False)

        level_dict = {1: 0, 2: 0, 3: 0}

        levels = events.values("level").annotate(count=Count("level"))
        for level in levels:
            level_dict[level["level"]] = level["count"]

        result = {
            "levels": [{"level": level, "count": count} for level, count in list(level_dict.items())],
            "unrecovered_count": sum([level["count"] for level in levels]),
        }
        return result


class HostPerformanceDistributionResource(CacheResource):
    """
    主机性能分布
    """

    cache_type = CacheType.OVERVIEW

    RequestSerializer = BusinessOnlySerializer

    @staticmethod
    def generate_range_dict():
        return OrderedDict([("0 ~ 20%", []), ("20 ~ 40%", []), ("40 ~ 60%", []), ("60 ~ 80%", []), ("80 ~ 100%", [])])

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]

        distribution_dict = OrderedDict(
            [
                ("system.cpu_summary.usage", {"name": _("CPU使用率"), "value": self.generate_range_dict()}),
                ("system.mem.pct_used", {"name": _("应用内存使用率"), "value": self.generate_range_dict()}),
                ("system.disk.in_use", {"name": _("磁盘空间使用率"), "value": self.generate_range_dict()}),
                ("system.io.util", {"name": _("磁盘I/O利用率"), "value": self.generate_range_dict()}),
            ]
        )

        hosts = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id)

        if not hosts:
            # 该业务下没有主机，就使用样例数据
            using_example_data = True
        else:
            using_example_data = False
            performance_data = host_index_backend.get_data_by_metrics(
                bk_biz_id, metric_list=list(distribution_dict.keys())
            )

            for metric_id, data in list(performance_data.items()):
                range_dict = distribution_dict[metric_id]["value"]
                if not data:
                    raise CustomException(_("主机性能数据获取失败"))
                for host_id, origin_value in list(data[0].items()):
                    value = origin_value["val"]
                    if isinstance(value, list):
                        # 有多个维度的情况，取所有维度的最大值
                        value = max([max(v.values()) for v in value])
                    if value >= 80:
                        key = "80 ~ 100%"
                    elif value >= 60:
                        key = "60 ~ 80%"
                    elif value >= 40:
                        key = "40 ~ 60%"
                    elif value >= 20:
                        key = "20 ~ 40%"
                    else:
                        key = "0 ~ 20%"
                    ip, bk_cloud_id = parse_host_id(host_id)
                    range_dict[key].append(ip)

        result_data = []

        for metric_id, data in list(distribution_dict.items()):
            result_data.append(
                {
                    "metric_id": metric_id,
                    "name": data["name"],
                    "data": [
                        {"name": name, "y": len(ip_list), "ip_list": ip_list}
                        for name, ip_list in list(data["value"].items())
                    ],
                }
            )
        return {
            "using_example_data": using_example_data,
            "data": result_data,
        }


class MonitorInfoResource(CacheResource):
    """
    业务监控状态总览
    """

    cache_type = CacheType.OVERVIEW

    RequestSerializer = BusinessOnlySerializer

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]

        modules = {
            "uptimecheck": UptimeCheckMonitorInfo,
            "service": ServiceMonitorInfo,
            "process": ProcessMonitorInfo,
            "os": OsMonitorInfo,
        }

        # 拉取未恢复的事件
        module_event = {}
        abnormal_events = resource.alert_events.query_events(
            bk_biz_ids=[bk_biz_id], days=7, conditions=[{"key": "event_status", "value": [Event.EventStatus.ABNORMAL]}]
        )

        for event in abnormal_events:
            # 判断当条数据属于哪个模块
            for key, module in list(modules.items()):
                if module.check_event(event):
                    module_key = key
                    module_event.setdefault(module_key, []).append(event)
                    break

        # 获取每个模块的监控信息
        result_data = {}
        for key, module in list(modules.items()):
            events = module_event.get(key, [])
            info = module(bk_biz_id, events).get_info()
            info.update(name=key)
            result_data[key] = info

        # 如果所有模块均正常，返回综合描述
        if all([item["status"] == MonitorStatus.NORMAL for item in list(result_data.values())]):
            time_warning_strategies = []
            notice_warning_strategies = []
            disabled_strategies = []
            no_target_strategies = []
            # 检查策略
            all_strategies = StrategyModel.objects.filter(bk_biz_id=bk_biz_id)
            strategy_mapping = {}
            for strategy in all_strategies:
                strategy_mapping[strategy.id] = strategy
                # 检车策略是否禁用
                if not strategy.is_enabled:
                    disabled_strategies.append({"strategy_id": strategy.id, "strategy_name": strategy.name})

            # 检查无监控目标策略
            strategies = StrategyModel.objects.filter(bk_biz_id=bk_biz_id)
            items = ItemModel.objects.filter(strategy_id__in=Subquery(strategies.values("id")))
            for item in items:
                if (item.target and item.target[0]) or item.strategy_id not in strategy_mapping:
                    continue
                no_target_strategies.append(
                    {"strategy_id": item.strategy_id, "strategy_name": strategy_mapping[item.strategy_id].name}
                )

            # 检查通知时间
            action_list = Action.objects.filter(strategy_id__in=list(strategy_mapping.keys())).values(
                "strategy_id", "config"
            )
            for action in action_list:
                action_config = action["config"]
                if action_config.get("alarm_start_time", "") == action_config.get("alarm_end_time", ""):
                    strategy_id = action["strategy_id"]
                    time_warning_strategies.append(
                        {"strategy_id": action["strategy_id"], "strategy_name": strategy_mapping[strategy_id].name}
                    )

            # 检查通知方式
            notice_groups = NoticeGroup.objects.filter(bk_biz_id=bk_biz_id).values("id", "name", "notice_way")
            for group in notice_groups:
                # 导入可能导致通知方式为空的情况出现
                if group["notice_way"]:
                    serious_notice = set(group["notice_way"]["1"])
                    if not ({"sms", "voice"} & serious_notice):
                        notice_warning_strategies.append({"group_id": group["id"], "group_name": group["name"]})

            result_data.update(
                summary={
                    "time_warning_strategies": time_warning_strategies,
                    "notice_warning_strategies": notice_warning_strategies,
                    "disabled_strategies": disabled_strategies,
                    "no_target_strategies": no_target_strategies,
                }
            )

        return result_data
