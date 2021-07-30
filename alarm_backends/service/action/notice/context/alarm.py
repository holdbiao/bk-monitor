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

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from alarm_backends.constants import NO_DATA_TAG_DIMENSION
from bkmonitor.utils import time_tools
from bkmonitor.utils.time_tools import hms_string
from constants.data_source import DATA_CATEGORY, DataSourceLabel, DataTypeLabel

from ..chart import get_chart_by_origin_alarm
from ..utils import get_target_dimension_keys
from . import BaseContextObject

logger = logging.getLogger("action")


class Alarm(BaseContextObject):
    """
    告警信息对象
    """

    @cached_property
    def collect_count(self):
        """
        汇总的告警数量
        """
        return len({event_action["event_id"] for event_action in self.parent.event_actions})

    @cached_property
    def is_no_data_alarm(self):
        """
        :summary: 是否无数据告警
        :return:
        """
        return self.parent.event.is_no_data

    @cached_property
    def display_type(self):
        if self.is_no_data_alarm:
            return _("发生无数据告警")
        return _("发生告警")

    @cached_property
    def display_dimensions(self):
        """
        非目标维度
        """
        event = self.parent.event
        strategy = self.parent.strategy
        # 无数据告警，直接从异常信息获取维度
        if self.is_no_data_alarm:
            # 过滤掉无数标记维度
            target_dimension_keys = [NO_DATA_TAG_DIMENSION]
            agg_dimensions = list(event.origin_alarm["data"]["dimensions"].keys())
        else:
            target_dimension_keys = []
            item = strategy.items[0]
            agg_dimensions = item.rt_query_config.get("agg_dimension", [])
            if (
                item.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR
                and item.data_type_label == DataTypeLabel.EVENT
            ):
                agg_dimensions = ["bk_target_ip", "bk_target_cloud_id"]
            elif item.data_source_label == DataSourceLabel.CUSTOM and item.data_type_label == DataTypeLabel.EVENT:
                agg_dimensions = list(event.origin_alarm["data"]["dimensions"].keys())

        target_dimension_keys += get_target_dimension_keys(agg_dimensions, strategy.scenario)

        return {
            value["display_name"]: value["display_value"]
            for key, value in list(event.origin_alarm["dimension_translation"].items())
            if key not in target_dimension_keys and key in agg_dimensions
        }

    @cached_property
    def display_targets(self):
        """
        监控目标
        """

        events = self.parent.events
        target_type = self.target_type

        targets = []

        for event in events:
            dimensions = event.origin_alarm["dimension_translation"]

            if target_type == "IP":
                ip = dimensions.get("bk_target_ip") or dimensions.get("ip")
                if ip:
                    targets.append(ip["display_value"])
            elif target_type == "INSTANCE":
                service_instance_id = dimensions.get("bk_target_service_instance_id")
                if service_instance_id:
                    targets.append(service_instance_id["display_value"])
            elif target_type == "TOPO":
                bk_obj_id = dimensions.get("bk_obj_id")
                bk_inst_id = dimensions.get("bk_inst_id")
                if bk_obj_id and bk_inst_id:
                    targets.append("{}-{}".format(bk_obj_id["display_value"], bk_inst_id["display_value"]))

        return targets

    @cached_property
    def target_string(self):
        """
        告警目标字符串
        """
        if not self.display_targets:
            return ""

        target_string = ",".join(self.display_targets)

        if self.parent.limit:
            limit_target_string = "{}...({})".format(self.display_targets[0], len(self.display_targets))
            if len(limit_target_string.encode("utf-8")) < len(target_string.encode("utf-8")):
                target_string = limit_target_string

        return target_string

    @cached_property
    def dimensions(self):
        """
        维度字典
        """
        return self.parent.event.origin_alarm["dimension_translation"]

    @cached_property
    def dimension_string(self):
        """
        告警维度字符串
        """
        if not self.display_dimensions:
            return ""

        # 拓扑维度特殊处理
        dimension_string_list = []
        ignore_topo_dimension = False
        if "bk_obj_id" in self.display_dimensions and "bk_inst_id" in self.display_dimensions:
            ignore_topo_dimension = True
            dimension_string_list.append(
                "{}={}".format(
                    self.display_dimensions["bk_obj_id"],
                    self.display_dimensions["bk_inst_id"],
                )
            )

        for key, value in list(self.display_dimensions.items()):
            if key in ["bk_obj_id", "bk_inst_id"] and ignore_topo_dimension:
                continue
            dimension_string_list.append("{}={}".format(key, value))

        dimension_string = ",".join(dimension_string_list)

        if self.parent.limit:
            limit_dimension_string = "{}...".format(self.display_dimensions[0])
            if len(limit_dimension_string.encode("utf-8")) < len(dimension_string.encode("utf-8")):
                dimension_string = [limit_dimension_string]

        return dimension_string

    @cached_property
    def chart_image(self):
        """
        邮件出图
        """
        if not settings.GRAPH_RENDER_SERVICE_ENABLED:
            return None

        if self.parent.alert_collect.collect_type != "DIMENSION":
            return None

        strategy = self.parent.strategy
        event = self.parent.event

        # 无数据告警，不需要出图
        if self.is_no_data_alarm:
            return None

        chart = None

        if self.parent.notice_way == "wxwork-bot":
            title = f"{self.parent.strategy.name} - {self.parent.alert_collect.id}"
        else:
            title = strategy.items[0].name

        try:
            chart = get_chart_by_origin_alarm(
                strategy.bk_biz_id,
                strategy.items[0],
                event.origin_alarm["data"]["dimensions"],
                event.latest_anomaly_record.source_time,
                title,
            )
        except Exception as e:
            logger.exception("event_action({}) create alarm chart error, {}".format(self.parent.event_action.id, e))

        if chart:
            logger.info("event_action({}) create alarm chart success".format(self.parent.event_action.id))

        return chart

    @cached_property
    def chart_name(self):
        """
        图片名
        """
        if self.chart_image:
            return "alarm_chart_%s.png" % self.parent.event_action.id
        return ""

    @cached_property
    def attachments(self):
        attachment = []
        if self.chart_image:
            attachment.append(
                {
                    "filename": f"__INLINE__{self.chart_name}",
                    "content_id": f"__INLINE__{self.chart_name}",
                    "content": self.chart_image,
                }
            )
        return attachment

    @cached_property
    def time(self):
        return time_tools.localtime(self.parent.event.latest_anomaly_record.source_time)

    @cached_property
    def begin_time(self):
        return time_tools.localtime(self.parent.event.begin_time)

    @cached_property
    def duration(self):
        """
        事件持续时间
        """
        return self.parent.event.duration

    @cached_property
    def duration_string(self):
        """
        持续时间字符串
        :return:
        """
        return hms_string(self.duration.total_seconds())

    @cached_property
    def current_value(self):
        """
        事件当前异常值
        """
        # 无数据告警不返回当前值
        if self.is_no_data_alarm:
            return None

        return self.parent.event.latest_anomaly_record.origin_alarm["data"]["value"]

    @cached_property
    def detail_url(self):
        """
        告警详情链接
        """
        if self.parent.notice_way in settings.ALARM_MOBILE_NOTICE_WAY and settings.ALARM_MOBILE_URL:
            url = settings.ALARM_MOBILE_URL
        else:
            url = settings.EVENT_CENTER_URL
        return url.format(bk_biz_id=self.parent.business.bk_biz_id, collect_id=self.parent.alert_collect.id)

    @cached_property
    def notice_from(self):
        return _("蓝鲸监控")

    @cached_property
    def company(self):
        return ""

    @cached_property
    def data_source_name(self):
        """
        数据来源名称
        """
        item = self.parent.strategy.items[0]

        data_source_label = item.data_source_label
        data_type_label = item.data_type_label

        for category in DATA_CATEGORY:
            if category["data_source_label"] == data_source_label and category["data_type_label"] == data_type_label:
                return category["name"]

        return "{}_{}".format(data_source_label, data_type_label)

    @cached_property
    def target_type(self):
        """
        监控目标类型
        """
        strategy = self.parent.strategy
        item = strategy.items[0]

        agg_dimensions = item.rt_query_config.get("agg_dimension", [])
        # 事件型默认维度
        if (
            item.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR
            and item.data_type_label == DataTypeLabel.EVENT
        ):
            agg_dimensions = ["bk_target_ip", "bk_target_cloud_id"]

        target_dimension_keys = get_target_dimension_keys(agg_dimensions, strategy.scenario)

        if "ip" in target_dimension_keys or "bk_target_ip" in target_dimension_keys:
            return "IP"
        elif "bk_obj_id" in target_dimension_keys and "bk_inst_id" in target_dimension_keys:
            return "TOPO"
        elif "bk_target_service_instance_id" in target_dimension_keys:
            return "INSTANCE"

        return ""

    @cached_property
    def target_type_name(self):
        """
        监控目标名称
        """
        return {"IP": "IP", "INSTANCE": _("实例"), "TOPO": _("节点")}.get(self.target_type, self.target_type)
