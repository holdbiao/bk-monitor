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
from collections import defaultdict

from django.conf import settings
from django.db.models import Max
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.models import AnomalyRecord
from bkmonitor.utils import time_tools
from bkmonitor.utils.event_related_info import get_event_relation_info
from bkmonitor.utils.template import NoticeRowRenderer
from constants.data_source import DataTypeLabel
from core.unit import load_unit

from . import BaseContextObject


logger = logging.getLogger("action")


class DefaultContent(BaseContextObject):
    """
    通知内容对象
    """

    Fields = (
        "level",
        "time",
        "begin_time",
        "duration",
        "target_type",
        "data_source",
        "content",
        "biz",
        "target",
        "dimension",
        "detail",
        "current_value",
        "related_info",
    )

    def __getattribute__(self, item):
        """
        取值时自动获取相应通知类型的值
        """
        if item in object.__getattribute__(self, "Fields"):
            notice_way = self.parent.notice_way
            if hasattr(self, "{}_{}".format(item, notice_way)):
                value = object.__getattribute__(self, "{}_{}".format(item, notice_way))
            else:
                value = super(DefaultContent, self).__getattribute__(item)

            if value is None:
                return ""
            else:
                return NoticeRowRenderer.format(notice_way, self.Labels[item][notice_way], value)

        return super(DefaultContent, self).__getattribute__(item)

    # 告警级别
    @cached_property
    def level(self):
        return None

    # 首次异常时间
    @cached_property
    def time(self):
        return self.parent.alarm.time.strftime(settings.DATETIME_FORMAT)

    # 最近一次时间
    @cached_property
    def begin_time(self):
        return self.parent.alarm.begin_time.strftime(settings.DATETIME_FORMAT)

    # 持续时间
    @cached_property
    def duration(self):
        return None

    # 监控目标类型
    @cached_property
    def target_type(self):
        return None

    # 监控数据来源
    @cached_property
    def data_source(self):
        return None

    # 告警内容
    @cached_property
    def content(self):
        anomaly_record = self.parent.event.latest_anomaly_record

        duration_message = ""
        if self.parent.alarm.duration_string:
            duration_message = _("已持续{}, ").format(self.parent.alarm.duration_string)

        message = "{}{}".format(
            duration_message, list(anomaly_record.origin_alarm["anomaly"].values())[0]["anomaly_message"]
        )
        return message

    # 所属业务
    @cached_property
    def biz(self):
        return None

    # 监控目标
    @property
    def target(self):
        if not self.parent.alarm.display_targets:
            return self.parent.target.business.bk_biz_name

        return "{} {}".format(
            self.parent.target.business.bk_biz_name,
            self.parent.alarm.target_string,
        )

    # 维度
    @cached_property
    def dimension(self):
        if not self.parent.alarm.display_dimensions:
            return None

        return self.parent.alarm.dimension_string

    # 告警详情
    @cached_property
    def detail(self):
        return self.parent.alarm.detail_url

    # 当前值
    @cached_property
    def current_value(self):
        return None

    # 关联信息
    @cached_property
    def related_info(self):
        related_info = ""
        if self.parent.target.host:
            host = self.parent.target.host

            related_info += "{}({}) {}({})".format(_("集群"), host.set_string, _("模块"), host.module_string)
        try:
            related_info += get_event_relation_info(self.parent.event)
        except Exception as err:
            logger.exception("Get anomaly content err, msg is {}".format(err))
        return related_info


class DimensionCollectContent(DefaultContent):
    """
    同纬度汇总告警内容
    """

    Labels = {
        "begin_time": defaultdict(lambda: _lazy("首次异常")),
        "time": defaultdict(lambda: _lazy("最近异常")),
        "level": defaultdict(lambda: _lazy("级别"), {"mail": _lazy("告警级别")}),
        "duration": defaultdict(lambda: _lazy("持续时间")),
        "target_type": defaultdict(lambda: _lazy("告警对象")),
        "data_source": defaultdict(lambda: _lazy("数据来源")),
        "content": defaultdict(lambda: _lazy("内容"), {"mail": _lazy("告警内容")}),
        "biz": defaultdict(lambda: _lazy("告警业务")),
        "target": defaultdict(lambda: _lazy("目标"), {"mail": _lazy("告警目标")}),
        "dimension": defaultdict(lambda: _lazy("维度"), {"mail": _lazy("告警维度")}),
        "detail": defaultdict(lambda: _lazy("详情"), {"sms": _lazy("告警汇总ID")}),
        "current_value": defaultdict(lambda: _lazy("当前值")),
        "related_info": defaultdict(lambda: _lazy("关联信息")),
    }

    # 短信
    @cached_property
    def time_sms(self):
        return None

    @cached_property
    def begin_time_sms(self):
        return None

    @cached_property
    def detail_sms(self):
        return self.parent.alert_collect.id

    # 邮件
    @cached_property
    def duration_mail(self):
        return self.parent.alarm.duration_string

    @cached_property
    def target_type_mail(self):
        return self.parent.alarm.target_type_name

    @cached_property
    def data_source_mail(self):
        return self.parent.alarm.data_source_name

    @cached_property
    def content_mail(self):
        anomaly_record = self.parent.event.latest_anomaly_record
        return list(anomaly_record.origin_alarm["anomaly"].values())[0]["anomaly_message"]

    @cached_property
    def biz_mail(self):
        return self.parent.target.business.bk_biz_name

    @cached_property
    def target_mail(self):
        if not self.parent.alarm.display_targets:
            return None

        target_message = ",".join(self.parent.alarm.display_targets)
        return target_message

    @cached_property
    def detail_mail(self):
        return None

    @cached_property
    def current_value_mail(self):
        is_event = self.parent.strategy.items[0].data_type_label == DataTypeLabel.EVENT
        if self.parent.alarm.current_value is None or is_event:
            return None
        unit = load_unit(self.parent.strategy.items[0].unit)
        value, suffix = unit.fn.auto_convert(self.parent.alarm.current_value)
        return "{}{}".format(value, suffix)

    @cached_property
    def level_mail(self):
        return self.parent.event.level_name


class MultiStrategyCollectContent(DefaultContent):
    """
    多维度多策略汇总告警内容
    """

    Labels = {
        "begin_time": defaultdict(lambda: _lazy("首次异常")),
        "time": defaultdict(lambda: _lazy("最近异常"), {"mail": _lazy("时间范围")}),
        "level": defaultdict(lambda: _lazy("级别"), {"mail": _lazy("告警级别")}),
        "duration": defaultdict(lambda: _lazy("持续时间")),
        "target_type": defaultdict(lambda: _lazy("告警对象")),
        "data_source": defaultdict(lambda: _lazy("数据来源")),
        "content": defaultdict(lambda: _lazy("内容"), {"sms": _lazy("代表")}),
        "biz": defaultdict(lambda: _lazy("告警业务")),
        "target": defaultdict(lambda: _lazy("目标")),
        "dimension": defaultdict(lambda: _lazy("维度")),
        "detail": defaultdict(lambda: _lazy("详情"), {"sms": _lazy("告警汇总ID")}),
        "current_value": defaultdict(lambda: _lazy("当前值")),
        "related_info": defaultdict(lambda: _lazy("关联信息")),
    }

    # 微信
    @cached_property
    def detail_weixin(self):
        return None

    # 短信
    @cached_property
    def time_sms(self):
        return None

    @cached_property
    def begin_time_sms(self):
        return None

    @cached_property
    def detail_sms(self):
        return self.parent.alert_collect.id

    @cached_property
    def content_sms(self):
        duration_message = ""
        if self.parent.alarm.duration_string:
            duration_message = _("已持续{},")

        return _("[{}]{} {}告警,{}{}").format(
            self.parent.event.level_name,
            self.strategy.strategy_name,
            time_tools.localtime(self.parent.event.latest_anomaly_record.source_time).time().strftime("%H:%M"),
            duration_message,
            list(self.parent.anomaly_record.origin_alarm["anomaly"].values())[0]["anomaly_message"],
        )

    # 邮件
    @cached_property
    def level_mail(self):
        return self.parent.event.level_name

    @cached_property
    def time_mail(self):
        event_ids = {event_action["event_id"] for event_action in self.parent.event_actions}

        # 获取事件最近异常点的时间
        latest_anomaly_records = (
            AnomalyRecord.objects.filter(event_id__in=event_ids).values("event_id").annotate(max_id=Max("id"))
        )
        latest_anomaly_records = AnomalyRecord.objects.filter(
            id__in=[record["max_id"] for record in latest_anomaly_records]
        ).values("source_time")
        source_times = [record["source_time"] for record in latest_anomaly_records]

        # 统计最大最小时间
        max_time = time_tools.localtime(max(source_times))
        min_time = time_tools.localtime(min(source_times))

        time_range = "{min_time} ~ {max_time}".format(
            min_time=min_time.strftime(settings.DATETIME_FORMAT),
            max_time=max_time.strftime(settings.DATETIME_FORMAT),
        )
        return time_range

    @cached_property
    def begin_time_mail(self):
        return None

    @cached_property
    def biz_mail(self):
        return self.parent.target.business.bk_biz_name

    @cached_property
    def data_source_mail(self):
        return self.parent.alarm.data_source_name

    @cached_property
    def content_mail(self):
        return None

    @cached_property
    def dimension_mail(self):
        return None

    @cached_property
    def detail_mail(self):
        return None

    @cached_property
    def target_mail(self):
        return None

    @cached_property
    def related_info(self):
        return None
