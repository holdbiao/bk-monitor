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
# flake8: noqa

import datetime
import json
import logging
import re
from collections import defaultdict

import six
from django.db import transaction
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.db_routers import using_db
from bkmonitor.strategy.upgrade import get_metric_suffix_mapping, get_metric_unit_mapping
from core.errors.notice_group import NoticeGroupNameExist
from bkmonitor.models import NoticeGroup
from bkmonitor.utils.common_utils import count_md5
from constants.data_source import DataSourceLabel
from core.drf_resource import resource, api
from monitor.models import DashboardView, MetricMonitor
from monitor_api.models import MonitorItemGroup, MonitorSource
from monitor_api.models import NoticeGroup as OldNoticeGroup
from monitor_web.models import MetricListCache
from monitor_web.upgrade.data_maker.base import BaseDataMaker
from monitor_web.upgrade.data_maker.commons import ResultTableType, classify_result_table

logger = logging.getLogger(__name__)


class StrategyMaker(BaseDataMaker):
    """
    监控策略迁移
    """

    # 日志关键字特殊字符
    ES_SPECIAL_STR_RE = re.compile(r"[\\+\-=&|><!(){}\[\]^\"~*?:/]")

    # 全局配置的KEY
    GLOBAL_CONFIG_KEY = "strategy_migrate_record"

    # 存储已经创建的告警组，具有相同配置的告警组将被复用
    notice_groups_cache = defaultdict(dict)

    # 索引集缓存
    index_set_cache = defaultdict(dict)

    DEFAULT_NOTICE_GROUPS = [
        {
            "alias": "operator",
            "name": _lazy("主备负责人"),
            "notice_receiver": [{"id": "operator", "type": "group"}, {"id": "bk_bak_operator", "type": "group"}],
            "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
            "message": "",
        },
        {
            "alias": "bk_biz_maintainer",
            "name": _lazy("运维"),
            "notice_receiver": [{"id": "bk_biz_maintainer", "type": "group"}],
            "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
            "message": "",
        },
        {
            "alias": "bk_biz_developer",
            "name": _lazy("开发"),
            "notice_receiver": [{"id": "bk_biz_developer", "type": "group"}],
            "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
            "message": "",
        },
        {
            "alias": "bk_biz_tester",
            "name": _lazy("测试"),
            "notice_receiver": [{"id": "bk_biz_tester", "type": "group"}],
            "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
            "message": "",
        },
        {
            "alias": "bk_biz_productor",
            "name": _lazy("产品"),
            "notice_receiver": [{"id": "bk_biz_productor", "type": "group"}],
            "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
            "message": "",
        },
    ]

    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        monitor_source_queryset = MonitorSource.objects.using("monitor_api_3_1").filter(is_deleted=False)
        if bk_biz_id:
            monitor_source_queryset = monitor_source_queryset.filter(biz_id=bk_biz_id)
        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value
        results = []
        # 获取老监控策略列表
        for old_monitor_source in monitor_source_queryset:
            with using_db("monitor_api_3_1"):
                monitor_group_id_list = MonitorItemGroup.get_by_monitor_id(old_monitor_source.id)
            for monitor_group_id in monitor_group_id_list:
                with using_db("monitor_api_3_1"):
                    old_monitor_item = MonitorItemGroup.get_monitor_group(monitor_group_id, old_monitor_source)
                if str(old_monitor_item["id"]) in migrate_record_value:
                    results.append(migrate_record_value[str(old_monitor_item["id"])])
                else:
                    results.append(
                        {
                            "status": "READY",
                            "message": _("等待迁移"),
                            "bk_biz_id": old_monitor_source.biz_id,
                            "origin_strategy": {
                                "monitor_id": old_monitor_source.id,
                                "monitor_name": old_monitor_source.monitor_name,
                                "item_id": old_monitor_item["id"],
                                "item_name": old_monitor_item["display_name"],
                            },
                            "new_strategy": {},
                        }
                    )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        monitor_source_queryset = MonitorSource.objects.using("monitor_api_3_1").filter(is_deleted=False)
        if bk_biz_id:
            monitor_source_queryset = monitor_source_queryset.filter(biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value

        results = []
        # 获取老监控策略列表
        for old_monitor_source in monitor_source_queryset:
            cls.migrate_notice_group(old_monitor_source.biz_id)

            with using_db("monitor_api_3_1"):
                monitor_group_id_list = MonitorItemGroup.get_by_monitor_id(old_monitor_source.id)
            for monitor_group_id in monitor_group_id_list:
                with using_db("monitor_api_3_1"):
                    old_monitor_item = MonitorItemGroup.get_monitor_group(monitor_group_id, old_monitor_source)

                if migrate_record_value.get(str(old_monitor_item["id"]), {}).get("status") == "SUCCESS":
                    # 如果成功就不再迁移了，直接返回结果
                    results.append(migrate_record_value[str(old_monitor_item["id"])])
                    continue

                strategy_maker = StrategyMaker(old_monitor_source, old_monitor_item)
                result = strategy_maker.create()
                results.append(result)

                migrate_record_value.update({str(result["origin_strategy"]["item_id"]): result})
        migrate_record.value = migrate_record_value
        migrate_record.save()

        return results

    @classmethod
    def migrate_items(cls, bk_biz_id, item_ids, monitor_source_ids=None):
        migrate_record = cls.get_migrate_record()

        monitor_source_queryset = MonitorSource.objects.using("monitor_api_3_1").filter(
            is_deleted=False, biz_id=bk_biz_id
        )

        if monitor_source_ids:
            monitor_source_queryset = monitor_source_queryset.filter(id__in=monitor_source_ids)

        results = []

        for old_monitor_source in monitor_source_queryset:
            cls.migrate_notice_group(old_monitor_source.biz_id)

            with using_db("monitor_api_3_1"):
                monitor_group_id_list = MonitorItemGroup.get_by_monitor_id(old_monitor_source.id)
            for monitor_group_id in monitor_group_id_list:
                with using_db("monitor_api_3_1"):
                    old_monitor_item = MonitorItemGroup.get_monitor_group(monitor_group_id, old_monitor_source)

                if old_monitor_item["id"] not in item_ids:
                    continue

                if migrate_record.value.get(str(old_monitor_item["id"]), {}).get("status") == "SUCCESS":
                    # 如果成功就不再迁移了，直接返回结果
                    results.append(migrate_record.value[str(old_monitor_item["id"])])
                    continue

                strategy_maker = StrategyMaker(old_monitor_source, old_monitor_item)
                result = strategy_maker.create()
                results.append(result)

                migrate_record.value.update({str(result["origin_strategy"]["item_id"]): result})
        migrate_record.save()
        return results

    @classmethod
    def migrate_notice_group(cls, bk_biz_id):
        if NoticeGroup.objects.filter(bk_biz_id=bk_biz_id).exists():
            if not cls.notice_groups_cache[bk_biz_id]:
                for notice_group in NoticeGroup.objects.filter(bk_biz_id=bk_biz_id):
                    for default_notice_group in cls.DEFAULT_NOTICE_GROUPS:
                        if notice_group.name == six.text_type(default_notice_group["name"]):
                            cls.notice_groups_cache[bk_biz_id][default_notice_group["alias"]] = notice_group.id
                            break
            return

        for notice_group in cls.DEFAULT_NOTICE_GROUPS:
            result = resource.notice_group.backend_save_notice_group(
                bk_biz_id=bk_biz_id,
                name=six.text_type(notice_group["name"]),
                notice_receiver=notice_group["notice_receiver"],
                notice_way=notice_group["notice_way"],
                message=notice_group["message"],
            )
            cls.notice_groups_cache[bk_biz_id][notice_group["alias"]] = result["id"]

        for notice_group in OldNoticeGroup.objects.using("monitor_api_3_1").filter(biz_id=bk_biz_id).all():
            notice_receivers = [{"id": user, "type": "user"} for user in notice_group.group_receiver.split(",")]

            notice_group_config = {
                "bk_biz_id": bk_biz_id,
                "name": notice_group.title,
                "notice_receiver": notice_receivers,
                "notice_way": {1: ["weixin", "mail"], 2: ["weixin", "mail"], 3: ["weixin", "mail"]},
                "message": notice_group.description,
            }

            index = 1
            while True:
                try:
                    notice_group_id = resource.notice_group.backend_save_notice_group(notice_group_config)["id"]
                    cls.notice_groups_cache[bk_biz_id][notice_group.id] = notice_group_id
                    break
                except NoticeGroupNameExist:
                    # 不断重命名，直到成功为止
                    notice_group_config["name"] = "{}({})".format(notice_group.title, index)
                    index += 1

    def __init__(self, old_monitor_source, old_monitor_item):
        self.old_monitor_source = old_monitor_source
        self.old_monitor_item = old_monitor_item
        self.bk_biz_id = old_monitor_source.biz_id
        self.metric_suffix_mapping = get_metric_suffix_mapping()
        self.metric_unit_mapping = get_metric_unit_mapping()

    @classmethod
    def calc_notice_groups_md5(cls, notice_group_config):
        return count_md5(
            {
                "notice_way": notice_group_config["notice_way"],
                "notice_receiver": notice_group_config["notice_receiver"],
            }
        )

    @classmethod
    def generate_notice_group_name(cls, notice_group_config):
        group_name_translation = {
            "operator": _("主负责人"),
            "bk_bak_operator": _("备份负责人"),
            "bk_biz_productor": _("产品人员"),
            "bk_biz_developer": _("开发人员"),
            "bk_biz_maintainer": _("运维"),
            "bk_biz_tester": _("测试人员"),
        }

        # 使用角色的摘要作为组名
        group_name = ""
        for receiver in notice_group_config["notice_receiver"]:
            receiver_name = group_name_translation.get(receiver["id"], receiver["id"])
            if len(group_name) + len(receiver_name) >= 120:
                # 超过了120个字符，省略后面的
                group_name += "..."
                break
            if group_name:
                group_name += ","
            group_name += receiver_name
        return group_name

    def generate_notice_config_params(self):
        # 通知配置
        notice_group_config = {
            "bk_biz_id": self.old_monitor_source.biz_id,
            "notice_way": {1: None, 2: None, 3: None},
            "notice_receiver": [],
        }

        notice_ways_mapping = {
            "phone": "voice",
            "wechat": "weixin",
            "sms": "sms",
            "mail": "mail",
            "im": "rtx",
        }

        # 主备负责人、运维、用户旧分组等可复用的ID列表
        group_role_ids = set()
        default_notice_way = None
        for level_id, level_config in list(self.old_monitor_item["alarm_level_config"].items()):
            current_notice_way = [notice_ways_mapping.get(way, way) for way in level_config["notify_way"]]
            # 插入通知方式
            notice_group_config["notice_way"][level_id] = current_notice_way
            if not default_notice_way:
                default_notice_way = current_notice_way

            # 插入通知人员，多个等级的通知角色取并集
            for role in level_config["role_list"]:
                role_translate = {
                    "Maintainers": "bk_biz_maintainer",
                    "Developer": "bk_biz_developer",
                    "Tester": "bk_biz_tester",
                    "ProductPm": "bk_biz_productor",
                    "Operator": "operator",
                    "BakOperator": "bk_bak_operator",
                }

                if not isinstance(role, int):
                    role_name = role_translate.get(role)
                    if not role_name:
                        continue

                    if role_name in ["operator", "bk_bak_operator"]:
                        group_role_ids.add(self.notice_groups_cache[self.bk_biz_id]["operator"])
                    else:
                        group_role_ids.add(self.notice_groups_cache[self.bk_biz_id][role_name])
                else:
                    # 如果角色是数字，说明是老的告警组
                    group_id = self.notice_groups_cache[self.bk_biz_id].get(role)
                    if not group_id:
                        continue
                    group_role_ids.add(group_id)

            # 额外通知人和电话通知人员也加进去
            for user in level_config["responsible"] + level_config["phone_receiver"]:
                single_notice_config = {
                    "id": user,
                    "type": "user",
                }
                if single_notice_config not in notice_group_config["notice_receiver"]:
                    notice_group_config["notice_receiver"].append(single_notice_config)

        # 补全缺失的通知等级
        for level, config in list(notice_group_config["notice_way"].items()):
            if config is None:
                notice_group_config["notice_way"][level] = default_notice_way

        return group_role_ids, notice_group_config

    def generate_detect_algorithm_params(self, algorithm_unit_prefix):
        detect_algorithm_list = []
        algorithm_id_mapping = {
            1000: "Threshold",
            1001: "SimpleYearRound",
            1002: "SimpleRingRatio",
            1003: "AdvancedYearRound",
            1004: "AdvancedRingRatio",
            1005: "YearRoundAmplitude",
            1006: "YearRoundRange",
            1007: "RingRatioAmplitude",
            4000: "Threshold",
            # 5000: "进程端口监控检测策略",
            # 5001: "系统重新启动监控策略",
            # 6000: "自定义字符型告警",
        }
        for level_id, level_config in list(self.old_monitor_item["alarm_level_config"].items()):
            algorithm_list = []

            detect_algorithm_list.append({"level": level_id, "algorithm_list": algorithm_list})

            # 事件类型算法不填
            if self.old_monitor_source.monitor_type == "base_alarm" or self.old_monitor_source.monitor_target in [
                "gse_custom_event",
                "os_restart",
                "proc_port",
            ]:
                continue

            for algorithm in level_config["detect_algorithm"]:
                algorithm_id = algorithm["algorithm_id"]
                if algorithm_id not in algorithm_id_mapping:
                    continue

                if algorithm_id in [1000, 4000]:
                    # 静态阈值需要特殊处理
                    algorithm_config = [
                        [{"method": algorithm["config"]["method"], "threshold": algorithm["config"]["threshold"]}]
                    ]
                elif algorithm_id in [1001, 1002]:
                    algorithm_config = {
                        "ceil": algorithm["config"].get("ceil") or "",
                        "floor": algorithm["config"].get("floor") or "",
                    }
                elif algorithm_id in [1003, 1004]:
                    algorithm_config = {
                        "ceil": algorithm["config"].get("ceil") or "",
                        "floor": algorithm["config"].get("floor") or "",
                        "ceil_interval": algorithm["config"].get("ceil_interval") or "",
                        "floor_interval": algorithm["config"].get("floor_interval") or "",
                    }
                elif algorithm_id in [1005]:
                    algorithm_config = {
                        "ratio": algorithm["config"]["times"],
                        "shock": algorithm["config"]["shock"],
                        "days": algorithm["config"]["interval"],
                        "method": algorithm["config"]["method"],
                    }
                elif algorithm_id in [1006]:
                    algorithm_config = {
                        "ratio": float(algorithm["config"]["ratio"]) / 100,
                        "shock": algorithm["config"]["shock"],
                        "days": algorithm["config"]["interval"],
                        "method": algorithm["config"]["method"],
                    }
                elif algorithm_id in [1007]:
                    algorithm_config = {
                        "ratio": float(algorithm["config"]["ratio"]) / 100,
                        "shock": algorithm["config"]["shock"],
                        "threshold": algorithm["config"]["threshold"],
                    }
                else:
                    continue

                algorithm_list.append(
                    {
                        "algorithm_type": algorithm_id_mapping[algorithm_id],
                        "algorithm_config": algorithm_config,
                        "algorithm_unit": algorithm_unit_prefix,
                    }
                )

        return detect_algorithm_list

    def create_notice_group(self):
        # 通知配置
        group_role_ids, notice_group_config = self.generate_notice_config_params()
        notice_group_name = self.generate_notice_group_name(notice_group_config)
        notice_group_config["name"] = notice_group_name

        md5sum = self.calc_notice_groups_md5(notice_group_config)

        if not notice_group_config["notice_receiver"]:
            # 人员列表为空，无需创建
            return group_role_ids

        if md5sum in self.notice_groups_cache[self.bk_biz_id]:
            # 缓存已存在，直接复用
            group_role_ids.add(self.notice_groups_cache[self.bk_biz_id][md5sum])
            return group_role_ids

        # 创建通知
        index = 1
        while True:
            try:
                notice_group_id = resource.notice_group.backend_save_notice_group(notice_group_config)["id"]
                group_role_ids.add(notice_group_id)
                break
            except NoticeGroupNameExist:
                # 不断重命名，直到成功为止
                notice_group_config["name"] = "{}({})".format(notice_group_name, index)
                index += 1
        self.notice_groups_cache[self.bk_biz_id][md5sum] = notice_group_id
        return group_role_ids

    @property
    def strategy_name(self):
        # 创建新版监控项
        strategy_name = self.old_monitor_item["display_name"]
        return strategy_name

    @classmethod
    def _convert_log_keywords(cls, rule, conditions):
        """
        关键字过滤条件转换
        :param rule:
        :param conditions:
        :return:
        """
        _conditions = []
        for condition in conditions:
            field = condition.get("field")
            method = condition.get("method")
            value = condition.get("value")
            if method == "match":
                v = str(value)
                if not cls.ES_SPECIAL_STR_RE.search(value):
                    v = "*%s*" % v
                condition = "{}: {}".format(field, v)

            elif method == "term":
                condition = '{}: "{}"'.format(field, str(value))

            elif method == "gt":
                condition = "{}: >{}".format(field, str(value))

            elif method == "gte":
                condition = "{}: >={}".format(field, str(value))

            elif method == "lt":
                condition = "{}: <{}".format(field, str(value))

            elif method == "lte":
                condition = "{}: <={}".format(field, str(value))

            elif method == "neq":
                condition = 'NOT {}: "{}"'.format(field, str(value))
            else:
                continue
            _conditions.append(condition)
        return {"must": " AND ", "should": " OR "}[rule].join(_conditions)

    def generate_create_params(self):
        stat_source_info = self.old_monitor_source.stat_source_info_dict

        keywords_query_string = ""
        extend_fields = {}

        if self.old_monitor_source.monitor_type == "base_alarm" or self.old_monitor_source.monitor_target in [
            "gse_custom_event",
            "os_restart",
            "proc_port",
        ]:
            # 事件类型需要特殊处理

            data_type_label = "event"
            data_source_label = "bk_monitor"
            unit = ""
            unit_conversion = 1
            metric_field = stat_source_info.get("monitor_field") or stat_source_info["monitor_dataset"]
            agg_dimension = []
            agg_method = ""
            agg_interval = 60
            scenario = "os"
            metric_id_prefix = ""
            if self.old_monitor_source.monitor_target == "os_restart":
                metric_field = "os_restart"
            if self.old_monitor_source.monitor_target == "proc_port":
                metric_field = "proc_port"
        elif self.old_monitor_source.scenario == "log":
            rt_id = stat_source_info["monitor_result_table_id"]
            if stat_source_info.get("monitor_field") == "rate":
                raise Exception(_("不支持监控指标为“次数占比”的策略项"))

            if rt_id in self.index_set_cache:
                index_set_info = self.index_set_cache[rt_id]
            else:
                try:
                    # 如果在缓存中不存在，则尝试请求日志平台，get or create 一个新的索引集
                    index_set_info = api.log_search.replace_index_set(
                        {
                            "index_set_name": f"bkmonitor_{rt_id}",
                            "scenario_id": "bkdata",
                            "indexes": [
                                {
                                    "bk_biz_id": self.old_monitor_source.biz_id,
                                    "result_table_id": rt_id,
                                    "time_field": "",
                                }
                            ],
                            "category_id": "other_rt",
                            "bk_biz_id": self.old_monitor_source.biz_id,
                        }
                    )
                    self.index_set_cache[rt_id] = index_set_info
                except Exception as e:
                    logger.warning("[replace_index_set] 调用失败，原因：{}".format(e))
                    raise Exception(_("不支持日志类型的策略迁移"))

            try:
                # 统计周期可能有多个，取第一个
                algo_config = list(self.old_monitor_item["alarm_level_config"].values())[0]["detect_algorithm"][0]
                agg_interval = 60 * algo_config["config"]["range"]
            except Exception:
                agg_interval = 60

            # 日志关键字类型的监控策略
            metric_id_prefix = ""
            scenario = "other_rt"
            data_source_label = "bk_log_search"
            data_type_label = "log"
            agg_method = "COUNT"
            agg_dimension = stat_source_info.get("dimensions") or []
            if isinstance(agg_dimension, str):
                # 做个兼容，如果维度是字符串，则转换为列表
                agg_dimension = [agg_dimension]
            unit = ""
            unit_conversion = 1
            metric_field = index_set_info["index_set_name"]
            keywords_query_string = self._convert_log_keywords(stat_source_info["rule"], stat_source_info["keywords"])
            keywords_query_string = keywords_query_string or "*"
            extend_fields.update(
                {
                    "time_field": index_set_info.get("time_field", ""),
                    "scenario_name": index_set_info.get("scenario_name", ""),
                    "index_set_id": index_set_info.get("index_set_id", ""),
                    "scenario_id": index_set_info.get("scenario_id", ""),
                    # bkdata类型的日志数据源一定没有集群信息
                    "storage_cluster_id": "",
                    "storage_cluster_name": "",
                }
            )
        else:
            rt_id = stat_source_info["monitor_result_table_id"]

            rt_type, metric_id_prefix = classify_result_table(rt_id)
            if rt_type == ResultTableType.NEW_BK_MONITOR:
                if metric_id_prefix.startswith("uptimecheck"):
                    # 拨测
                    scenario = "uptimecheck"
                elif metric_id_prefix.startswith("system.proc"):
                    # 主机进程
                    scenario = "host_process"
                else:
                    # 其余都为主机操作系统
                    scenario = "os"
            elif rt_type == ResultTableType.BK_DATA:
                # 计算平台
                scenario = "other_rt"
            else:
                raise Exception(_("不支持迁移。该监控项使用了不支持的数据源类型。RT({})".format(rt_id)))

            # 数据来源
            data_type_label = "time_series"
            data_source_label = (
                DataSourceLabel.BK_DATA if rt_type == ResultTableType.BK_DATA else DataSourceLabel.BK_MONITOR_COLLECTOR
            )
            agg_method = stat_source_info["aggregator"].upper()
            agg_interval = stat_source_info.get("count_freq") or 60
            agg_dimension = stat_source_info.get("dimensions") or []
            if isinstance(agg_dimension, str):
                # 做个兼容，如果维度是字符串，则转换为列表
                agg_dimension = [agg_dimension]

            # 旧的维度字段转换
            if data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR:
                dimension_translate = {"ip": "bk_target_ip", "plat_id": "bk_target_cloud_id", "company_id": ""}
                agg_dimension = [
                    dimension_translate.get(dimension, dimension)
                    for dimension in agg_dimension
                    if dimension_translate.get(dimension, dimension)
                ]

            # 如果是主机操作系统类型指标，需要保证有ip和bk_cloud_id 字段
            if scenario in ["os", "host_process"]:
                agg_dimension = list(set(agg_dimension + ["bk_target_ip", "bk_target_cloud_id"]))

            metric_field = stat_source_info["monitor_field"]
            unit = stat_source_info.get("unit", "")
            unit_conversion = stat_source_info.get("unit_conversion") or 1

        # 无数据告警，大于0为开启
        no_data_alarm = int(self.old_monitor_item.get("nodata_alarm", 0))
        no_data_config = {
            "continuous": no_data_alarm if no_data_alarm > 0 else 5,
            "is_enabled": no_data_alarm > 0,
        }

        # 对内置指标进行单位转换，并且添加算法单位前缀
        metric_id = f"{metric_id_prefix}.{metric_field}"
        algorithm_unit_prefix = self.metric_suffix_mapping.get(metric_id, "")
        unit = self.metric_unit_mapping.get(metric_id, unit)

        notice_group_ids = sorted(list(self.create_notice_group()))
        # 检测算法配置
        try:
            detect_algorithm_list = self.generate_detect_algorithm_params(algorithm_unit_prefix)
        except Exception as e:
            logger.exception("检测算法配置不正确：{}".format(e))
            raise Exception("检测算法配置不正确：{}".format(e))

        is_algorithm_empty = True
        for algorithm in detect_algorithm_list:
            if algorithm["algorithm_list"]:
                is_algorithm_empty = False
                break

        if data_type_label == "time_series" and is_algorithm_empty:
            raise Exception("检测算法配置为空，不支持迁移")

        # 监控目标
        target = []
        has_target_host = self.old_monitor_source.scenario in ["base_alarm", "performance", "component"]

        task_ids = re.findall(r"task_id\s*=\s*'(\d+)'", self.old_monitor_item["where_sql"])

        if scenario == "uptimecheck" and not task_ids:
            # 没有任务ID的拨测策略，是通过自定义监控或仪表盘创建的，不能转换为标准的拨测策略
            scenario = "other_rt"

        # 监控条件
        where_sql_conditions = []
        if scenario == "uptimecheck":
            task_id = int(task_ids[0])
            where_sql_conditions.append({"key": "task_id", "method": "eq", "value": [str(task_id)]})
            agg_dimension = ["task_id"]

            if self.old_monitor_item["condition"][0]:
                condition = self.old_monitor_item["condition"][0][0]
                where_sql_conditions.append(
                    {
                        "condition": "and",
                        "key": condition["field"],
                        "method": condition["method"],
                        "value": condition["value"],
                    }
                )

        else:
            if self.old_monitor_source.scenario == "dashboard-custom" and stat_source_info.get("where_sql"):
                # 如果配置的是仪表盘监控，那么需要根据where_sql进行补全
                metric_monitor = (
                    MetricMonitor.objects.using("monitor_saas_3_1")
                    .filter(monitor_id=self.old_monitor_source.id)
                    .first()
                )
                if metric_monitor:
                    dashboard_view = DashboardView.objects.using("monitor_saas_3_1").get(id=metric_monitor.view_id)
                    # 从仪表盘中找出配置
                    filter_condition = None
                    for metric_info in json.loads(dashboard_view.metrics):
                        if metric_info["id"] == metric_monitor.metric_id:
                            # 转换运算符
                            method_translations = {
                                "=": "eq",
                                "!=": "neq",
                                ">": "gt",
                                "<": "lt",
                                ">=": "gte",
                                "<=": "lte",
                                "like": "like",
                            }
                            for conditions in metric_info["where_field_list"]:
                                for sub_cond in conditions:
                                    sub_cond_copy = {
                                        "method": method_translations.get(sub_cond["method"], sub_cond["method"]),
                                        "value": sub_cond["value"],
                                        "key": sub_cond["field"],
                                    }
                                    if filter_condition:
                                        sub_cond_copy["condition"] = filter_condition
                                    where_sql_conditions.append(sub_cond_copy)
                                    filter_condition = "and"

                                filter_condition = "or"

                            break

            filter_condition = "and" if where_sql_conditions else None
            for conditions in self.old_monitor_item["condition"]:
                sub_target = []
                for sub_condition in conditions:
                    if has_target_host and sub_condition["field"] in [
                        "ip",
                        "bk_topo_node",
                        "cc_set",
                        "cc_module",
                        "cc_topo_set",
                        "cc_app_module",
                    ]:
                        # 主机类型包含这些字段，需要单独处理
                        if sub_condition["field"] == "ip":
                            values = []
                            for sub_condition_value in sub_condition["value"]:
                                if isinstance(sub_condition_value, str):
                                    # 格式1: ["10.0.0.1"] 只有IP的字符串
                                    values.append({"bk_target_ip": sub_condition_value, "bk_target_cloud_id": 0})
                                else:
                                    # 格式2: [{"ip": "10.0.0.1", "bk_cloud_id": 0}]
                                    values.append(
                                        {
                                            "bk_target_ip": sub_condition_value["ip"],
                                            "bk_target_cloud_id": sub_condition_value.get("bk_cloud_id", 0),
                                        }
                                    )

                            sub_target.append({"field": "bk_target_ip", "method": "eq", "value": values})
                        elif sub_condition["field"] == "bk_topo_node":
                            sub_target.append(
                                {
                                    "field": "host_topo_node",
                                    "method": "eq",
                                    "value": [
                                        {
                                            "bk_obj_id": sub_condition_value.split("|")[0],
                                            "bk_inst_id": int(sub_condition_value.split("|")[1]),
                                        }
                                        for sub_condition_value in sub_condition["value"]
                                    ],
                                }
                            )
                        # 老版本集群模块选择器的数据
                        elif sub_condition["field"] in ["cc_set", "cc_module"]:
                            if not sub_condition["value"]:
                                continue

                            if sub_target and sub_target[0]["field"] == "host_topo_node":
                                sub_target[0]["value"].append(
                                    {
                                        "bk_obj_id": sub_condition["field"][3:],
                                        "bk_inst_id": [int(v) for v in sub_condition["value"]],
                                    }
                                )
                        elif sub_condition["field"] in ["cc_topo_set", "cc_app_module"]:
                            # CC1.0的业务模块
                            raise Exception(_("暂不支持迁移监控范围为业务模块的策略项"))
                    else:
                        sub_condition_method = sub_condition["method"]

                        if self.old_monitor_source.scenario == "log":
                            # 针对日志关键字的运算符转换
                            if sub_condition_method in ["eq", "include"]:
                                sub_condition_method = "is"
                            elif sub_condition_method in ["exclude"]:
                                sub_condition_method = "is not"
                            elif sub_condition_method == "reg":
                                raise Exception(_("该策略的监控条件使用了正则表达式，不支持迁移"))
                        sub_cond_copy = {
                            "method": sub_condition_method,
                            "value": sub_condition["value"],
                            "key": sub_condition["field"],
                        }
                        if filter_condition:
                            sub_cond_copy["condition"] = filter_condition

                        where_sql_conditions.append(sub_cond_copy)

                    filter_condition = "and"

                filter_condition = "or"

                if sub_target:
                    target.append(sub_target)

        if not target:
            if not has_target_host:
                target.append([])
            else:
                # 目标为空的，则加上业务节点
                target.append(
                    [
                        {
                            "field": "host_topo_node",
                            "method": "eq",
                            "value": [{"bk_obj_id": "biz", "bk_inst_id": self.old_monitor_source.biz_id}],
                        }
                    ]
                )

        first_notice_config = list(self.old_monitor_item["alarm_level_config"].values())[0]
        for current_notice_config in list(self.old_monitor_item["alarm_level_config"].values())[1:]:
            if (
                datetime.datetime.strptime(first_notice_config["notice_end_time"], "%H:%M")
                - datetime.datetime.strptime(first_notice_config["notice_start_time"], "%H:%M")
            ) < (
                datetime.datetime.strptime(current_notice_config["notice_end_time"], "%H:%M")
                - datetime.datetime.strptime(current_notice_config["notice_start_time"], "%H:%M")
            ):
                # 选择时间差最大的那个通知时间段作为最终的通知时间段
                first_notice_config = current_notice_config

        metric_display_name = metric_field
        try:
            # 尝试寻找指标中文名
            metric = MetricListCache.objects.filter(result_table_id=metric_id_prefix, metric_field=metric_field).first()
            if metric:
                metric_display_name = metric.metric_field_name
                extend_fields.update(
                    {
                        "result_table_name": metric.result_table_name,
                        "data_source_label": metric.data_source_label,
                        "related_id": metric.related_id,
                    }
                )
        except Exception:
            pass

        create_params = {
            "is_enabled": self.old_monitor_item["is_enabled"],
            "name": self.strategy_name[:50],
            "bk_biz_id": self.old_monitor_source.biz_id,
            "source_type": "BKMONITOR",  # TODO 需要确定还有没有用
            "scenario": scenario,
            "data_target": "HOST" if has_target_host else "NONE",
            "no_data_config": no_data_config,
            "message_template": "",
            "item_list": [
                {
                    "id": 0,
                    "name": metric_display_name,
                    "data_type_label": data_type_label,
                    "data_source_label": data_source_label,
                    "result_table_id": metric_id_prefix,
                    "result_table_label": scenario,
                    "agg_method": agg_method,
                    "agg_interval": agg_interval,
                    "agg_dimension": agg_dimension,
                    "agg_condition": where_sql_conditions,
                    "metric_field": metric_field,
                    "unit": unit,
                    "unit_conversion": unit_conversion,
                    "trigger_config": {
                        "count": min(
                            int(self.old_monitor_item["rules"].get("count") or 1),
                            int(self.old_monitor_item["rules"].get("check_window") or 5),
                        ),
                        "check_window": int(self.old_monitor_item["rules"].get("check_window") or 5),
                    },
                    "recovery_config": {"check_window": int(self.old_monitor_item["rules"].get("check_window") or 5)},
                    "detect_algorithm_list": detect_algorithm_list,
                    "extend_fields": extend_fields,
                    "target": target,
                    "keywords_query_string": keywords_query_string,
                }
            ],
            "action_list": [
                {
                    "id": 0,
                    "action_type": "notice",
                    "config": {
                        "alarm_interval": self.old_monitor_item["rules"].get("alarm_window", 1440) or 1,
                        "alarm_end_time": first_notice_config["notice_end_time"] + ":00",
                        "alarm_start_time": first_notice_config["notice_start_time"] + ":00",
                        "send_recovery_alarm": first_notice_config["is_recovery"],
                    },
                    "notice_group_list": notice_group_ids,
                }
            ],
        }
        # print(json.dumps(target))
        # print(json.dumps(where_sql_conditions))
        return create_params

    def create(self):
        # 创建监控策略
        result = {
            "status": "READY",
            "message": _("等待迁移"),
            "bk_biz_id": self.old_monitor_source.biz_id,
            "origin_strategy": {
                "monitor_id": self.old_monitor_source.id,
                "monitor_name": self.old_monitor_source.monitor_name,
                "item_id": self.old_monitor_item["id"],
                "item_name": self.old_monitor_item["display_name"],
            },
            "new_strategy": {},
        }
        try:
            with transaction.atomic():
                strategy_params = self.generate_create_params()
                strategy = resource.strategies.strategy_config(strategy_params)
            result["message"] = _("迁移成功")
            result["status"] = "SUCCESS"
            result["new_strategy"] = {"id": strategy["id"], "name": strategy_params["name"]}
        except Exception as e:
            result["status"] = "FAILED"
            logger.exception(e)
            result["message"] = _("迁移失败，原因：{}").format(e)
        return result

    @classmethod
    def toggle_old_monitor_strategy(cls, bk_biz_id, is_enabled):
        count = 0
        with using_db("monitor_api_3_1"):
            monitor_sources_queryset = MonitorSource.objects.filter(is_deleted=False, biz_id=bk_biz_id)
            for monitor_source in monitor_sources_queryset:
                group_id_set = MonitorItemGroup.get_by_monitor_id(monitor_source.id)
                MonitorItemGroup.toggle_monitor_group(group_id_set, is_enabled=is_enabled)
                count += len(group_id_set)
        return count
