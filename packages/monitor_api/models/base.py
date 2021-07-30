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
import re

import arrow
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from six.moves import map, range

from bkmonitor import models as base_models
from core.drf_resource import resource
from bkmonitor.utils import time_tools
from bkmonitor.utils.common_utils import DatetimeEncoder, DictObj, ignored, safe_int
from common.xss_tools import html_escape
from monitor.constants import STRATEGY_CHOICES

INT_REG = re.compile(r"\d+")


class Component(DictObj):
    """
    组件
    """


class ProcessPort(Component):
    """
    进程端口组件
    """

    def __init__(self, kwargs):
        super(ProcessPort, self).__init__(kwargs)
        self.ports = ProcessPort.extract_ports(self.ports)

    @staticmethod
    def extract_ports(ports):
        """
        解析从 CC 返回的进程端口信息
        """
        if isinstance(ports, list):
            return ports

        if not ports:
            return []

        arr_ports = []
        for port in ports.split(","):
            with ignored(ValueError):
                if "-" in port:
                    start_port = int(port.split("-")[0])
                    end_port = int(port.split("-")[1])
                    arr_ports.extend(list(range(start_port, end_port + 1)))
                else:
                    arr_ports.append(int(port))
        return arr_ports


class CustomStringIndex(DictObj):
    # 自定义字符型告警
    _ID = "gse_custom_event"

    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = dict()
        kwargs.update(
            dict(
                alarm_type=self._ID,
                result_table_id=self._ID,
                title="",
                description=_("自定义字符型"),
                unit="",
            )
        )
        super(CustomStringIndex, self).__init__(kwargs)

    @property
    def id(self):
        return self.alarm_type

    @property
    def category(self):
        return self.alarm_type

    @property
    def dummy_category(self):
        return "base_alarm"

    @property
    def real_id(self):
        return self.alarm_type

    @property
    def item(self):
        return self.title

    @property
    def desc(self):
        return _(self.description)

    def gen_select2_option(self):
        return dict(id=self.alarm_type, metric_id=self.alarm_type, item=self.title, text=self.desc, unit="")

    @staticmethod
    def get_custom_str_data_id(cc_biz_id, operator):
        return settings.GSE_CUSTOM_EVENT_DATAID


custom_str_index = CustomStringIndex()


class ProcessPortIndex(DictObj):
    # 进程端口监控
    _ID = "proc_port"

    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = dict()
        kwargs.update(
            dict(
                alarm_type=self._ID,
                result_table_id=settings.PROC_PORT_TABLE_NAME,
                title=settings.PROC_PORT_METRIC_NAME,
                description=_("进程端口"),
                unit="",
            )
        )
        super(ProcessPortIndex, self).__init__(kwargs)

    @property
    def id(self):
        return self.alarm_type

    @property
    def category(self):
        return self.alarm_type

    @property
    def dummy_category(self):
        return "base_alarm"

    @property
    def real_id(self):
        return self.alarm_type

    @property
    def item(self):
        return self.title

    @property
    def desc(self):
        return _(self.description)

    def gen_select2_option(self):
        return dict(id=self.alarm_type, metric_id=self.alarm_type, item=self.title, text=self.desc, unit="")

    @staticmethod
    def parse_cc_ports(ports):
        """
        解析从 CC 返回的进程端口信息
        """
        arr_ports = []
        if not ports:
            return []
        for port in ports.split(","):
            with ignored(ValueError):
                if "-" in port:
                    start_port = int(port.split("-")[0])
                    end_port = int(port.split("-")[1])
                    arr_ports.extend(list(range(start_port, end_port + 1)))
                else:
                    arr_ports.append(int(port))
        return arr_ports

    def get_proc_port_snap(self, alarm_instance):
        """
        根据告警实例获取当时进程端口信息
        """
        dimensions = alarm_instance.dimensions
        return resource.performance.get_process_port_info(
            bk_biz_id=alarm_instance.monitor.biz_id,
            display_name=dimensions.get("display_name", dimensions.get("name")),
            ip=dimensions["ip"],
            plat_id=resource.cc.plat_id_cc_to_gse(dimensions.get("plat_id", dimensions.get("cloud_id"))),
            event_time=arrow.get(time_tools.localtime(alarm_instance.source_time)).timestamp * 1000,
        )


proc_port_index = ProcessPortIndex()


class OSRestartIndex(DictObj):
    # 系统重启监控
    _ID = "os_restart"

    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = dict()
        kwargs.update(
            dict(
                alarm_type=self._ID,
                result_table_id="system_env",
                title=_("系统重新启动"),
                description=_("系统重新启动"),
                unit="",
            )
        )
        super(OSRestartIndex, self).__init__(kwargs)

    @property
    def id(self):
        return self.alarm_type

    @property
    def category(self):
        return "system_env"

    @property
    def dummy_category(self):
        return "base_alarm"

    @property
    def real_id(self):
        return self.alarm_type

    @property
    def item(self):
        return "uptime"

    @property
    def desc(self):
        return _(self.description)

    def gen_select2_option(self):
        return dict(id=self.alarm_type, metric_id=self.alarm_type, item=self.item, text=self.desc, unit="")


os_restart_index = OSRestartIndex()


AbstractRecordModel = base_models.AbstractRecordModel


class MonitorSource(AbstractRecordModel):
    biz_id = models.IntegerField(verbose_name=_("业务ID"))
    title = models.CharField(max_length=256, verbose_name=_("监控源名称"))
    description = models.TextField(blank=True, default="", null=True, verbose_name=_("备注"))
    src_type = models.CharField(blank=True, default="JA", max_length=64, verbose_name=_("监控源分类"))
    scenario = models.CharField(blank=True, default="custom", max_length=64, verbose_name=_("监控场景"))
    monitor_type = models.CharField(blank=True, default="online", max_length=64, verbose_name=_("监控分类"))
    monitor_target = models.CharField(blank=True, default="custom", max_length=50, verbose_name=_("监控指标"))
    stat_source_type = models.CharField(blank=True, default="BKDATA", max_length=64, verbose_name=_("统计源分类"))
    stat_source_info = models.TextField(blank=True, default="", verbose_name=_("统计源信息（JSON）"))

    class Meta:
        managed = False
        db_table = "ja_monitor"

    @property
    def stat_source_info_dict(self):
        try:
            stat_source_info = json.loads(self.stat_source_info)
            if not isinstance(stat_source_info, dict):
                stat_source_info = {}
        except Exception:
            stat_source_info = {}
        return stat_source_info

    @property
    def generate_config_id(self):
        return self.stat_source_info_dict.get("generate_config_id", 0)

    @property
    def aggregator(self):
        return self.stat_source_info_dict.get("aggregator", "")

    @property
    def monitor_item_list(self):
        return MonitorItem.objects.filter(monitor_id=self.id)

    @property
    def monitor_name(self):
        return self.title

    @property
    def monitor_field_show_name(self):
        """监控指标，页面输出
        TODO
        """
        if self.scenario in ["performance", "base_alarm"]:
            return _(self.monitor_name)
        return resource.commons.get_desc_by_field(self.monitor_result_table_id, self.monitor_field)

    @property
    def monitor_result_table_id(self):
        return self.stat_source_info_dict.get("monitor_result_table_id", "")

    @property
    def original_config(self):
        if "original_config" in self.stat_source_info_dict:
            return self.stat_source_info_dict["original_config"]

    @property
    def conversion(self):
        return self.stat_source_info_dict.get("unit_conversion", 1)

    @property
    def monitor_field(self):
        return self.stat_source_info_dict.get("monitor_field", "")

    @property
    def backend_id(self):
        return self.id

    @property
    def monitor_desc(self):
        return self.description

    @property
    def count_method(self):
        _count_method = self.stat_source_info_dict.get("aggregator", "")
        return _count_method

    @property
    def count_freq(self):
        _count_freq = self.stat_source_info_dict.get("count_freq", "")
        return safe_int(_count_freq)

    @property
    def where_sql(self):
        return self.stat_source_info_dict.get("where_sql", "")


class MonitorItemGroup(AbstractRecordModel):
    biz_id = models.IntegerField(verbose_name=_("业务ID"))
    monitor_id = models.IntegerField(blank=True, default=0, verbose_name=_("监控源ID"))
    monitor_level = models.IntegerField(blank=True, default=3, verbose_name=_("监控等级"))
    monitor_item_id = models.IntegerField(verbose_name=_("告警策略ID"))
    monitor_group_id = models.IntegerField(verbose_name=_("告警策略组ID"))

    class Meta:
        managed = False
        db_table = "ja_monitor_item_group"

    @classmethod
    def get_by_monitor_id(cls, monitor_id):
        group_list = cls.objects.filter(monitor_id=monitor_id)
        group_id_set = set()
        for group in group_list:
            group_id_set.add(group.monitor_group_id)
        return group_id_set

    @classmethod
    def toggle_monitor_group(cls, monitor_group_ids, is_enabled):
        monitor_item_id_list = [x.monitor_item_id for x in cls.objects.filter(monitor_group_id__in=monitor_group_ids)]
        monitor_items = MonitorItem.origin_objects.filter(id__in=monitor_item_id_list)
        for monitor_item in monitor_items:
            cls.toggle_monitor_item(monitor_item, is_enabled)

    @classmethod
    def toggle_monitor_item(cls, monitor_item, is_enabled):
        monitor_item.is_enabled = is_enabled
        monitor_item.save()

        alarm_source = AlarmSource.origin_objects.get(id=monitor_item.alarm_def_id)
        alarm_source.is_enabled = is_enabled
        alarm_source.save()

    @classmethod
    def get_monitor_group(cls, monitor_group_id, monitor=None):
        monitor_group_list = cls.objects.filter(monitor_group_id=monitor_group_id)

        if not monitor:
            monitor = MonitorSource.objects.get(id=monitor_group_list[0].monitor_id)

        monitor_item_id_list = [x.monitor_item_id for x in monitor_group_list]
        result = cls.merge_monitor_item(MonitorItem.objects.filter(id__in=monitor_item_id_list), monitor)
        result["monitor_group_id"] = monitor_group_id
        result["id"] = monitor_group_id
        return result

    @classmethod
    def merge_monitor_item(cls, monitor_item_list, monitor):
        """
        合并MonitorItem，生成前端参数
        :param monitor_item_list: list(MonitorItem)
        :param monitor MonitorSource
        :return:
        """

        monitor_item = monitor_item_list[0]
        alarm_source = monitor_item.alarm_def
        notify_dict = alarm_source.notify_dict

        solution_dict = json.loads(alarm_source.alarm_solution_config)
        solution_config = json.loads(solution_dict.get("config", "{}"))

        params = {
            "monitor_name": monitor.monitor_name,
            "cc_biz_id": monitor.biz_id,
            "bk_biz_id": monitor.biz_id,
            "scenario": monitor.scenario,
            "monitor_target": monitor.monitor_target,
            "condition": json.loads(monitor_item.condition),
            "condition_display": cls.gen_condition_display(json.loads(monitor_item.condition)),
            "rules": json.loads(alarm_source.converge),
            "converge_display": cls.gen_converge_display(json.loads(alarm_source.converge)),
            "display_name": monitor_item.title,
            "is_enabled": monitor_item.is_enabled,
            "nodata_alarm": json.loads(monitor_item.is_none_option).get("continuous", 0),
            "monitor_id": monitor.id,
            "monitor_item_id": [x.id for x in monitor_item_list],
            "monitor_type": monitor.monitor_type,
            "is_recovery": monitor_item.is_recovery,
            "is_classify_notice": monitor_item.is_classify_notice,
            "solution_is_enable": solution_dict.get("is_enabled", False),
            "solution_type": solution_dict.get("solution_type", "job"),
            "solution_task_id": solution_config.get("job_task_id", ""),
            "solution_params_replace": "replace" if solution_config.get("replace_ip") else "",
            "solution_display": _("不处理，仅通知"),
            "solution_notice": [],
            "alarm_level_config": {},
            "where_sql": monitor.where_sql,
            "unit": monitor.stat_source_info_dict.get("unit", ""),
        }

        # solution_display 处理
        solution_type = solution_dict.get("solution_type", "job")
        if solution_type and solution_dict.get("is_enabled", False):
            display_name = _("作业平台") if solution_type == "job" else "job"
            params["solution_display"] = "【{}】{}".format(display_name, solution_config["job_task_name"])

        # solution_notice 处理
        for key in list(notify_dict.keys()):
            for word in ["begin", "end"]:
                if key.startswith("%s_notify_" % word) and notify_dict[key] and word not in params["solution_notice"]:
                    params["solution_notice"] += [word]

        # 不同告警级别的参数
        for monitor_item in monitor_item_list:
            condition_config = monitor_item.condition_config
            alarm_source = monitor_item.alarm_def
            notify_dict = alarm_source.notify_dict

            params["alarm_level_config"][monitor_item.monitor_level] = {
                "monitor_level": monitor_item.monitor_level,
                "phone_receiver": notify_dict.get("phone_receiver").replace(";", ",").split(",")
                if notify_dict.get("phone_receiver")
                else [],
                "role_list": notify_dict.get("role_list", []) + notify_dict.get("group_list", []),
                "notify_way": [],
                "responsible": notify_dict.get("responsible").replace(";", ",").split(",")
                if notify_dict.get("responsible")
                else [],
                "detect_algorithm": [],
                "notice_start_time": notify_dict.get("alarm_start_time", "00:00"),
                "notice_end_time": notify_dict.get("alarm_end_time", "23:59"),
                "is_recovery": monitor_item.is_recovery,
            }

            if params["alarm_level_config"][monitor_item.monitor_level]["responsible"]:
                params["alarm_level_config"][monitor_item.monitor_level]["role_list"].append("other")

            # notify_way 处理
            for method in ["mail", "wechat", "sms", "im", "phone", "rtx", "weixin", "voice"]:
                for status in ["begin_", "success_", "failure_", ""]:
                    if notify_dict.get("{}notify_{}".format(status, method)):
                        if method == "rtx":
                            params["alarm_level_config"][monitor_item.monitor_level]["notify_way"].append("im")
                        else:
                            params["alarm_level_config"][monitor_item.monitor_level]["notify_way"].append(method)
                        break

            # 检测算法处理
            for config in condition_config:
                params["alarm_level_config"][monitor_item.monitor_level]["detect_algorithm"].append(
                    {
                        "algorithm_id": config.algorithm_id,
                        "config": json.loads(config.strategy_option),
                        "display": config.gen_strategy_desc(params["unit"]),
                        "name": config.gen_strategy_name(),
                    }
                )

        return params

    @staticmethod
    def gen_condition_display(condition):
        expr_display = {
            "eq": _("等于"),
            "gte": _("大于等于"),
            "lte": _("小于等于"),
            "gt": _("大于"),
            "lt": _("小于"),
            "reg": _("正则"),
            "neq": _("不等于"),
        }

        try:
            con_str_list = []
            if isinstance(condition[0], dict):
                condition = [condition]
            for con_list in condition:
                if con_list:
                    sub_con_str_list = []
                    for con in con_list:
                        method = con.get("method", "")
                        expr_str = expr_display.get(method, method)
                        val = con.get("value", "")
                        if isinstance(val, list):
                            val = ",".join(map(str, val))
                        con_str = "{} {} {}".format(con.get("field", ""), expr_str, html_escape(val))
                        sub_con_str_list.append(con_str)
                    con_str_list.append("(" + " and ".join(sub_con_str_list) + ")")
            return " or ".join(con_str_list) if con_str_list else _("当前所有维度")
        except Exception:
            return _("筛选条件异常")

    @staticmethod
    def gen_converge_display(rules):
        desc = _("{check_window}个周期内，满足{count}次检测算法, 且告警产生后未恢复，{alarm_window}小时内不再告警")
        alarm_window = int(rules.get("alarm_window", 1440))
        if 1 <= alarm_window < 60:
            alarm_window_str = "%s/60" % alarm_window
        else:
            alarm_window_str = "%s" % (alarm_window // 60)
        return desc.format(
            check_window=rules.get("check_window", 5), count=rules.get("count", 1), alarm_window=alarm_window_str
        )


class MonitorItem(AbstractRecordModel):
    biz_id = models.IntegerField(verbose_name=_("业务ID"))
    title = models.CharField(max_length=256, verbose_name=_("监控项名称"))
    description = models.TextField(blank=True, default="", verbose_name=_("备注"))
    condition = models.TextField(blank=True, default="", verbose_name=_("监控范围"))
    monitor_level = models.IntegerField(blank=True, default=3, verbose_name=_("监控等级"))
    is_none = models.IntegerField(blank=True, default=0, verbose_name=_("无数据告警开关"))
    is_none_option = models.TextField(blank=True, default="", verbose_name=_("无数据配置"))
    is_recovery = models.BooleanField(default=False, verbose_name=_("恢复告警开关"))
    is_classify_notice = models.BooleanField(default=False, verbose_name=_("分级告警开关"))
    monitor_id = models.IntegerField(blank=True, default=0, verbose_name=_("监控源ID"))
    alarm_def_id = models.IntegerField(blank=True, default=0, verbose_name=_("告警源ID"))

    class Meta:
        managed = False
        db_table = "ja_monitor_item"

    @property
    def condition_config(self):
        return DetectAlgorithmConfig.objects.filter(monitor_item_id=self.id)

    @property
    def monitor(self):
        return MonitorSource.objects.get(id=self.monitor_id)

    @property
    def alarm_def(self):
        return AlarmSource.objects.get(id=self.alarm_def_id)

    @property
    def condition_dict(self):
        # 主机监控相关，用于拿告警范围，慎用！！！
        _condition_dict = dict()
        condition = json.loads(self.condition or "[[]]")[0]
        for c in condition:
            if c["method"] != "eq":
                continue
            val = c["value"]
            if isinstance(val, list):
                if c["field"] == "ip":
                    val = [
                        host if isinstance(host, str) else "{}|{}".format(host["ip"], host["bk_cloud_id"])
                        for host in val
                    ]
            else:
                val = [val]
            _condition_dict[c["field"]] = val
        return _condition_dict


class AlarmSource(AbstractRecordModel):
    """
    告警源
    关联
        1个清洗配置
        多个屏蔽策略
        多个收敛策略
        1个汇总策略
        1个处理策略
        1个通知策略
    """

    default_timeout = 40
    biz_id = models.IntegerField(verbose_name=_("业务ID"))
    title = models.CharField(max_length=256, verbose_name=_("告警名称"))
    description = models.TextField(blank=True, default="", verbose_name=_("备注"))
    src_type = models.CharField(blank=True, default="JA", max_length=64, verbose_name=_("告警源分类"))
    alarm_type = models.CharField(blank=True, default="Custom", max_length=64, verbose_name=_("告警分类"))
    scenario = models.CharField(blank=True, default="custom", max_length=64, verbose_name=_("监控场景"))
    monitor_target = models.CharField(blank=True, default="", max_length=64, verbose_name=_("监控对象"))
    source_info = models.TextField(blank=True, default="", verbose_name=_("告警来源信息"))
    condition = models.TextField(blank=True, default="", verbose_name=_("告警范围"))
    timeout = models.IntegerField(blank=True, default=40, verbose_name=_("超时时间"))
    alarm_attr_id = models.CharField(blank=True, default="", max_length=128, verbose_name=_("监控系统内的监控ID"))
    monitor_level = models.IntegerField(blank=True, default=3, verbose_name=_("监控等级"))
    alarm_cleaning_id = models.IntegerField(blank=True, default=0, verbose_name=_("清洗策略ID"))
    alarm_collect_id = models.IntegerField(blank=True, default=0, verbose_name=_("汇总策略ID"))
    alarm_solution_id = models.IntegerField(blank=True, default=0, verbose_name=_("处理策略ID"))
    alarm_notice_id = models.IntegerField(blank=True, default=0, verbose_name=_("通知策略ID"))

    class Meta:
        managed = False
        db_table = "ja_alarm_source"

    @property
    def converge(self):
        try:
            return ConvergeConfig.objects.get(alarm_source_id=self.id).config
        except ConvergeConfig.DoesNotExist:
            return "{}"
        except ConvergeConfig.MultipleObjectsReturned:
            return ConvergeConfig.objects.filter(alarm_source_id=self.id)[0].config

    @property
    def notify(self):
        return self.alarm_notice_config.notify_config

    @property
    def notify_dict(self):
        return json.loads(self.notify or "{}")

    @property
    def monitor_item(self):
        return MonitorItem.objects.get(alarm_def_id=self.id)

    @property
    def alarm_notice_config(self):
        return NoticeConfig.objects.get(id=self.alarm_notice_id)

    @property
    def alarm_solution_config(self):
        try:
            return json.dumps(SolutionConfig.objects.get(id=self.alarm_solution_id).to_dict(), cls=DatetimeEncoder)
        except SolutionConfig.DoesNotExist:
            return "{}"


class DetectAlgorithmConfig(AbstractRecordModel):
    """
    监控算法配置
    与监控项相关的监控算法配置
    """

    config = models.TextField(blank=True, default="", verbose_name=_("算法配置"))
    algorithm_id = models.IntegerField(blank=True, default=0, verbose_name=_("算法ID"))
    monitor_item_id = models.IntegerField(blank=True, default=0, verbose_name=_("监控项ID"))

    class Meta:
        managed = False
        db_table = "ja_detect_algorithm_config"

    @property
    def strategy_option(self):
        return self.config

    @property
    def biz_id(self):
        monitor_item = MonitorItem.objects.get(id=self.monitor_item_id)
        alarm_def = monitor_item.alarm_def
        biz_id = alarm_def.biz_id
        return biz_id

    def get_title(self):
        try:
            condition = MonitorItem.objects.get(id=self.monitor_item_id)
            alarm_def = AlarmSource.objects.filter(id=condition.alarm_def_id)[0]
        except Exception:
            return _("检测算法")
        return _("告警策略(%s)的检测算法") % alarm_def.title

    def gen_strategy_desc(self, unit=""):
        try:
            strategy_id = "%s" % self.algorithm_id
            strategy_option = json.loads(self.config)

            method_dict = {"eq": "=", "gte": "≥", "gt": ">", "lt": "<", "lte": "≤", "neq": "!="}
            if strategy_id == "1000":
                return _("当前值%(cur_val)s阈值:%(threshold)s%(unit)s") % {
                    "cur_val": method_dict.get(strategy_option.get("method", "eq")),
                    "threshold": strategy_option.get("threshold", ""),
                    "unit": unit,
                }
            span_html = _(" 或 ")
            desc = _("指标当前值")
            strategy_desc = {
                "1001": _("较上周同一时刻值"),
                "1002": _("较前一时刻值"),
                "1003": _("较%s天内同一时刻绝对值的均值"),
                "1004": _("较%s个时间点的均值"),
            }
            if strategy_id in ["1001", "1002"]:
                if not (strategy_option.get("ceil", "") or strategy_option.get("floor", "")):
                    return
                desc += strategy_desc[strategy_id]
                if strategy_option.get("ceil", ""):
                    desc += _("上升%s%%") % strategy_option.get("ceil", "")
                    if strategy_option.get("floor", ""):
                        desc += span_html
                if strategy_option.get("floor", ""):
                    desc += _("下降%s%%") % strategy_option.get("floor", "")
            elif strategy_id in ["1003", "1004"]:
                if not (strategy_option.get("ceil", "") or strategy_option.get("floor", "")):
                    return
                if strategy_option.get("ceil", ""):
                    desc += strategy_desc[strategy_id] % strategy_option.get("ceil_interval", "")
                    desc += _("上升%s%%") % strategy_option.get("ceil", "")
                    if strategy_option.get("floor", ""):
                        desc += span_html
                if strategy_option.get("floor", ""):
                    desc += strategy_desc[strategy_id] % strategy_option.get("floor_interval", "")
                    desc += _("下降%s%%") % strategy_option.get("floor", "")
            elif strategy_id == "1005":
                desc += _("-前一时刻值%(method)s过去%(num_of_day)s天内任一天同时刻差值* %(times)s + (%(shock)s)") % {
                    "method": method_dict.get(strategy_option.get("method", "eq")),
                    "num_of_day": strategy_option["interval"],
                    "times": strategy_option["times"],
                    "shock": strategy_option["shock"],
                }
            elif strategy_id == "1006":
                desc += _("%(method)s过去%(num_of_day)s天内同一时刻绝对值* %(ratio)s%% + (%(shock)s)") % {
                    "method": method_dict.get(strategy_option.get("method", "eq")),
                    "num_of_day": strategy_option["interval"],
                    "ratio": strategy_option["ratio"],
                    "shock": strategy_option["shock"],
                }
            elif strategy_id == "1007":
                desc += _("和前一时刻均>=%(threshold)s,且之间差值>=前一时刻值 *%(ratio)s%% + (%(shock)s)") % {
                    "threshold": strategy_option["threshold"],
                    "ratio": strategy_option["ratio"],
                    "shock": strategy_option["shock"],
                }
            elif strategy_id == "4000":
                desc = _("%(num)s分钟内%(method)s%(threshold)s次") % {
                    "num": strategy_option.get("range", ""),
                    "method": method_dict.get(strategy_option.get("method", "eq")),
                    "threshold": strategy_option.get("threshold", ""),
                }
            return desc
        except Exception:
            return _("默认参数")

    def gen_strategy_name(self):
        strategy_id = safe_int(self.algorithm_id)
        strategy_name = STRATEGY_CHOICES.get(strategy_id, "-")
        return strategy_name


class SolutionConfig(AbstractRecordModel):
    """
    关联告警源的告警汇总配置
    """

    title = models.CharField(blank=True, default="", max_length=256, verbose_name=_("名称"))
    description = models.TextField(blank=True, default="", null=True, verbose_name=_("备注"))
    config = models.TextField(blank=True, default="", null=True, verbose_name=_("配置"))
    alarm_source_id = models.IntegerField(blank=True, default=0, verbose_name=_("告警源id"))
    solution_id = models.IntegerField(blank=True, default=0, verbose_name=_("处理id"))
    solution_type = models.CharField(max_length=128, verbose_name=_("处理类型"))
    biz_id = models.IntegerField(blank=True, default=0, verbose_name=_("业务ID"))
    creator = models.CharField(max_length=255, verbose_name=_("作业创建者"))

    class Meta:
        managed = False
        db_table = "ja_alarm_solution_config"


class ConvergeConfig(AbstractRecordModel):
    """
    关联告警源的告警收敛配置
    """

    config = models.TextField(blank=True, default="", null=True, verbose_name=_("配置"))
    alarm_source_id = models.IntegerField(blank=True, default=0, verbose_name=_("告警源id"))
    converge_id = models.IntegerField(blank=True, default=0, verbose_name=_("收敛id"))

    class Meta:
        managed = False
        db_table = "ja_alarm_converge_config"

    @cached_property
    def converge(self):
        return AlarmCollectDef.objects.filter(id=self.converge_id).last()


class AlarmCollectDef(models.Model):
    """
    告警收敛策略
    """

    is_enabled = models.BooleanField(
        _("是否启用"),
        default=True,
        blank=True,
    )
    is_deleted = models.BooleanField(
        _("是否删除"),
        default=False,
        blank=True,
    )
    title = models.CharField(max_length=256, verbose_name=_("名称"))
    description = models.TextField(blank=True, default="", null=True, verbose_name=_("备注"))
    config = models.TextField(blank=True, default="", null=True, verbose_name=_("配置"))

    class Meta:
        managed = False
        db_table = "ja_alarm_converge_def"


class NoticeConfig(AbstractRecordModel):
    """
    告警通知策略
    """

    title = models.CharField(max_length=256, verbose_name=_("名称"))
    description = models.CharField(blank=True, default="", max_length=256, null=True, verbose_name=_("备注"))
    notify_config = models.TextField(blank=True, default="{}", verbose_name=_("配置"))
    alarm_start_time = models.TimeField(max_length=32, verbose_name=_("开始时间"))
    alarm_end_time = models.TimeField(max_length=32, verbose_name=_("结束时间"))
    alarm_source_id = models.IntegerField(blank=True, default=0, verbose_name=_("告警源id"))

    class Meta:
        managed = False
        db_table = "ja_alarm_notice_config"


class NoticeGroup(AbstractRecordModel):
    """
    告警通知组
    """

    title = models.CharField(max_length=256, verbose_name=_("名称"))
    description = models.CharField(blank=True, default="", max_length=256, verbose_name=_("备注"))
    biz_id = models.IntegerField(blank=True, default=0, verbose_name=_("业务"))
    group_type = models.IntegerField(blank=True, default=0, verbose_name=_("通知组类型"))
    group_receiver = models.TextField(blank=True, default="", verbose_name=_("通知组收件人"))

    class Meta:
        managed = False
        db_table = "ja_alarm_notice_group"
