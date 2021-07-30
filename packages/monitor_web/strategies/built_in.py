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
"""
内置策略
"""


import logging
from datetime import datetime, timedelta

import six
from django.conf import settings
from django.db.models import Count
from django.utils.translation import ugettext as _

from bkmonitor.models import NoticeGroup, StrategyModel
from constants.data_source import DataTypeLabel
from core.drf_resource import resource, api
from monitor_web.models import MetricListCache
from constants.strategy import EVENT_DETECT_LIST, EVENT_QUERY_CONFIG_MAP
from bkmonitor.strategy.new_strategy import get_metric_id
from monitor_web.models.custom_report import CustomEventGroup

__all__ = ["run_build_in"]


logger = logging.getLogger(__name__)

_CACHE = {"cache_time": datetime.min, "data": set()}


def build_in_biz_list():
    """
    已内置业务集合
    :return: Set
    """
    if datetime.now() - _CACHE["cache_time"] > timedelta(minutes=30):
        biz_strategy_count = StrategyModel.objects.values("bk_biz_id").annotate(count=Count("bk_biz_id"))
        _CACHE["data"] = {record["bk_biz_id"] for record in biz_strategy_count}
        _CACHE["cache_time"] = datetime.now()
    return _CACHE["data"]


def run_build_in(bk_biz_id, force_create=False):
    """
    执行内置操作[entry]
    :param bk_biz_id: 业务ID
    :param force_create: 强制创建
    """
    if not settings.ENABLE_DEFAULT_STRATEGY:
        return

    if not force_create and bk_biz_id in build_in_biz_list():
        return

    if force_create and StrategyModel.objects.filter(bk_biz_id=bk_biz_id).exists():
        # 如果是强制创建，检验当前策略是否为空即可
        _CACHE["data"].add(bk_biz_id)
        return
    elif not force_create and StrategyModel.objects.filter(bk_biz_id=bk_biz_id).exists():
        _CACHE["data"].add(bk_biz_id)
        return

    try:
        _run_build_in(bk_biz_id)
        run_gse_process_build_in(bk_biz_id)
    except Exception as e:
        logging.error("create default host strategy failed")
        logging.exception(e)


def get_or_create_gse_manager_group(bk_biz_id):
    """
    获取GSE 管理员通知组
    """
    if not getattr(settings, "GSE_MANAGERS", ""):
        return None
    receivers = [{"type": "user", "id": user} for user in settings.GSE_MANAGERS]

    group_name = "【蓝鲸】GSE管理员"
    if not NoticeGroup.objects.filter(name=group_name, bk_biz_id=bk_biz_id).exists():
        resource.notice_group.backend_save_notice_group(
            bk_biz_id=bk_biz_id,
            name="【蓝鲸】GSE管理员",
            notice_receiver=receivers,
            notice_way={1: ["rtx"], 2: ["rtx"], 3: ["rtx"]},
            message="",
        )

    try:
        return NoticeGroup.objects.get(bk_biz_id=bk_biz_id, name=group_name).id
    except NoticeGroup.DoesNotExist:
        pass


def _run_build_in(bk_biz_id):
    """
    执行内置操作
    :param bk_biz_id:
    :return: ret, msg
    """
    notice_group_id = create_default_notice_group(bk_biz_id)

    # 查询监控内置的主机指标
    metrics = []
    metrics.extend(
        MetricListCache.objects.filter(
            result_table_label__in=["os", "host_process"],
            data_source_label="bk_monitor",
            related_id="system",
        )
    )
    metrics.extend(
        MetricListCache.objects.filter(
            result_table_label__in=["os", "host_process"],
            data_source_label="bk_monitor",
            data_type_label="event",
        )
    )

    metric_dict = {
        get_metric_id(
            **{
                "data_type_label": metric.data_type_label,
                "data_source_label": metric.data_source_label,
                "result_table_id": metric.result_table_id,
                "metric_field": metric.metric_field,
            }
        ): metric
        for metric in metrics
    }

    for default_config in settings.DEFAULT_OS_STRATEGIES:
        metric_id = get_metric_id(
            **{
                "data_type_label": default_config["data_type_label"],
                "data_source_label": default_config["data_source_label"],
                "result_table_id": default_config.get("result_table_id", ""),
                "metric_field": default_config["metric_field"],
            }
        )

        metric = metric_dict.get(metric_id)
        if not metric:
            continue

        strategy_config = {
            "bk_biz_id": bk_biz_id,
            "name": str(default_config.get("name", metric.metric_field_name)),
            "scenario": default_config["result_table_label"],
            "item_list": [
                {
                    "metric_id": metric_id,
                    "name": _(metric.metric_field_name),
                    "data_type_label": metric.data_type_label,
                    "data_source_label": metric.data_source_label,
                    "no_data_config": {
                        "is_enabled": default_config.get("no_data_enabled", False),
                        "continuous": default_config.get("no_data_continuous", 5),
                    },
                    "algorithm_list": [
                        {
                            "level": default_config.get("level", 2),
                            "algorithm_config": [],
                            "trigger_config": {
                                "count": default_config["trigger_count"],
                                "check_window": default_config["trigger_check_window"],
                            },
                            "algorithm_type": "",
                            "recovery_config": {"check_window": default_config["recovery_check_window"]},
                        }
                    ],
                    "rt_query_config": {
                        "result_table_id": metric.result_table_id,
                        "agg_condition": default_config.get("agg_condition", metric.default_condition),
                        "agg_dimension": default_config.get("agg_dimension", metric.default_dimensions),
                        "agg_interval": default_config.get("agg_interval", metric.collect_interval * 60),
                        "agg_method": default_config.get("agg_method", "AVG"),
                        "metric_field": metric.metric_field,
                        "unit": _(metric.unit),
                        "unit_conversion": metric.unit_conversion,
                        "extend_fields": {},
                    },
                    "target": [
                        [
                            {
                                "field": "host_topo_node",
                                "method": "eq",
                                "value": [{"bk_inst_id": bk_biz_id, "bk_obj_id": "biz"}],
                            }
                        ]
                    ],
                }
            ],
            "action_list": [
                {
                    "notice_template": {
                        "anomaly_template": (
                            "{{content.level}}\n"
                            "{{content.begin_time}}\n"
                            "{{content.time}}\n"
                            "{{content.duration}}\n"
                            "{{content.target_type}}\n"
                            "{{content.data_source}}\n"
                            "{{content.content}}\n"
                            "{{content.current_value}}\n"
                            "{{content.biz}}\n"
                            "{{content.target}}\n"
                            "{{content.dimension}}\n"
                            "{{content.detail}}\n"
                            "{{content.related_info}}\n"
                        ),
                        "recovery_template": "",
                    },
                    "notice_group_list": [notice_group_id],
                    "action_type": "notice",
                    "config": {
                        "alarm_start_time": "00:00:00",
                        "alarm_end_time": "23:59:59",
                        "alarm_interval": default_config.get("alarm_interval", 1440),
                        "send_recovery_alarm": default_config.get("send_recovery_alarm", False),
                    },
                }
            ],
        }

        item = strategy_config["item_list"][0]
        # 非事件性策略配置阈值
        if metric.data_type_label != DataTypeLabel.EVENT:
            item["algorithm_list"][0]["algorithm_config"].append(
                [{"threshold": default_config["threshold"], "method": default_config["method"]}]
            )
            item["algorithm_list"][0]["algorithm_type"] = "Threshold"
            item["rt_query_config"]["extend_fields"] = {
                "data_source_label": item["data_source_label"],
                "related_id": metric.related_id,
                "result_table_name": metric.result_table_name,
            }

        # 主机重启、进程端口、PING不可达、实际上是时序性指标，需要做特殊处理
        if metric.metric_field in EVENT_DETECT_LIST:
            event_detect_config = EVENT_DETECT_LIST[metric.metric_field]
            item["rt_query_config"].update(EVENT_QUERY_CONFIG_MAP.get(metric.metric_field, {}))
            item["data_type_label"] = DataTypeLabel.TIME_SERIES
            item["algorithm_list"][0]["algorithm_type"] = event_detect_config[0]["algorithm_type"]
            item["algorithm_list"][0]["algorithm_config"] = event_detect_config[0]["algorithm_config"]

        # GSE失联事件追加GSE管理员
        if metric.metric_field == "agent-gse":
            gse_notice_group_id = get_or_create_gse_manager_group(bk_biz_id)
            if gse_notice_group_id is not None:
                strategy_config["action_list"][0]["notice_group_list"].append(gse_notice_group_id)

        resource.strategies.backend_strategy_config(**strategy_config)


def run_gse_process_build_in(bk_biz_id):
    """
    执行进程托管类策略的内置操作
    5种事件，2种创建类型：
    1. 用户侧的进程托管类策略，创建5种事件对应的策略, 通知组默认使用主备负责人
    2. 平台侧的进程托管类策略，创建1种统一进程事件策略，通知组通知插件负责人
    """
    bk_event_group = CustomEventGroup.objects.filter(bk_data_id=settings.GSE_PROCESS_REPORT_DATAID).first()
    for default_config in settings.DEFAULT_GSE_PROCESS_EVENT_STRATEGIES:
        if default_config["type"] == "business":
            notice_group_id = create_default_notice_group(bk_biz_id)
        else:
            notice_group_id = get_or_create_plugins_managers_group(bk_biz_id)
        strategy_config = {
            "bk_biz_id": bk_biz_id,
            "name": str(default_config.get("name")),
            "scenario": default_config["result_table_label"],
            "source": "gse_process_deposit",
            "item_list": [
                {
                    "metric_id": default_config["metric_id"],
                    "name": str(default_config.get("name")),
                    "data_type_label": default_config.get("data_type_label"),
                    "data_source_label": default_config.get("data_source_label"),
                    "no_data_config": {
                        "is_enabled": default_config.get("no_data_enabled", False),
                        "continuous": default_config.get("no_data_continuous", 5),
                    },
                    "algorithm_list": [
                        {
                            "level": default_config.get("level", 2),
                            "algorithm_config": [],
                            "trigger_config": {
                                "count": default_config["trigger_count"],
                                "check_window": default_config["trigger_check_window"],
                            },
                            "algorithm_type": "",
                            "recovery_config": {"check_window": default_config["recovery_check_window"]},
                        }
                    ],
                    "result_table_id": default_config.get("result_table_id"),
                    "rt_query_config": {
                        "bk_event_group_id": bk_event_group.bk_event_group_id,
                        "custom_event_id": -1,
                        "result_table_id": default_config.get("result_table_id"),
                        "agg_condition": default_config.get("agg_condition"),
                        "agg_dimension": default_config.get("agg_dimension", []),
                        "agg_interval": default_config.get("agg_interval", 60),
                        "agg_method": default_config.get("agg_method", "AVG"),
                        "metric_field": default_config.get("metric_field"),
                        "unit": "",
                        "unit_conversion": "1.0",
                        "extend_fields": {},
                    },
                    "target": [
                        [
                            {
                                "field": "host_topo_node",
                                "method": "eq",
                                "value": [{"bk_inst_id": bk_biz_id, "bk_obj_id": "biz"}],
                            }
                        ]
                    ],
                }
            ],
            "action_list": [
                {
                    "notice_template": {
                        "anomaly_template": (
                            "{{content.level}}\n"
                            "{{content.begin_time}}\n"
                            "{{content.time}}\n"
                            "{{content.duration}}\n"
                            "{{content.target_type}}\n"
                            "{{content.data_source}}\n"
                            "{{content.content}}\n"
                            "{{content.current_value}}\n"
                            "{{content.biz}}\n"
                            "{{content.target}}\n"
                            "{{content.dimension}}\n"
                            "{{content.detail}}\n"
                            "{{content.related_info}}\n"
                        ),
                        "recovery_template": "",
                    },
                    "notice_group_list": [notice_group_id],
                    "action_type": "notice",
                    "config": {
                        "alarm_start_time": "00:00:00",
                        "alarm_end_time": "23:59:59",
                        "alarm_interval": default_config.get("alarm_interval", 1440),
                        "send_recovery_alarm": default_config.get("send_recovery_alarm", False),
                    },
                }
            ],
        }

        resource.strategies.backend_strategy_config(**strategy_config)


def create_default_notice_group(bk_biz_id):
    """
    获取或创建默认通知组
    :param bk_biz_id: 业务ID
    :return: 通知组ID
    """
    if not NoticeGroup.objects.filter(bk_biz_id=bk_biz_id).exists():
        for notice_group in settings.DEFAULT_NOTICE_GROUPS:
            resource.notice_group.backend_save_notice_group(
                bk_biz_id=bk_biz_id,
                name=six.text_type(notice_group["name"]),
                notice_receiver=notice_group["notice_receiver"],
                notice_way=notice_group["notice_way"],
                message=notice_group["message"],
            )

    try:
        return NoticeGroup.objects.get(
            bk_biz_id=bk_biz_id, name=six.text_type(settings.DEFAULT_NOTICE_GROUPS[0]["name"])
        ).id
    except NoticeGroup.DoesNotExist:
        pass

    notice_group = settings.DEFAULT_NOTICE_GROUPS[0]
    return resource.notice_group.backend_save_notice_group(
        bk_biz_id=bk_biz_id,
        name=six.text_type(notice_group["name"]),
        notice_receiver=notice_group["notice_receiver"],
        notice_way=notice_group["notice_way"],
        message=notice_group["message"],
    )["id"]


def get_or_create_plugins_managers_group(bk_biz_id):
    """
    获取或创建插件管理员组
    :param bk_biz_id: 业务ID
    """
    if getattr(settings, "OFFICIAL_PLUGINS_MANAGERS", ""):
        receivers = [{"type": "user", "id": user} for user in settings.OFFICIAL_PLUGINS_MANAGERS]
    else:
        blueking_maintainers = api.cmdb.get_business(all=True, bk_biz_ids=[api.cmdb.get_blueking_biz()])[
            0
        ].bk_biz_maintainer
        receivers = [{"type": "user", "id": user} for user in blueking_maintainers]

    group_name = "【蓝鲸】官方插件管理员"
    if not NoticeGroup.objects.filter(name=group_name, bk_biz_id=bk_biz_id).exists():
        resource.notice_group.backend_save_notice_group(
            bk_biz_id=bk_biz_id,
            name="【蓝鲸】官方插件管理员",
            notice_receiver=receivers,
            notice_way={1: ["mail"], 2: ["mail"], 3: ["mail"]},
            message="",
        )

    try:
        return NoticeGroup.objects.get(bk_biz_id=bk_biz_id, name=group_name).id
    except NoticeGroup.DoesNotExist:
        pass
