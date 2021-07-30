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


from django.db import models
from django.utils.translation import ugettext_lazy as _

from bkmonitor.utils.db import JsonField
from core.drf_resource import api
from monitor_web.constants import EVENT_TYPE
from monitor_web.models import OperateRecordModelBase


class CustomEventGroup(OperateRecordModelBase):
    """
    自定义事件组
    """

    PLUGIN_TYPE_CHOICES = (
        (EVENT_TYPE.CUSTOM_EVENT, EVENT_TYPE.CUSTOM_EVENT),
        (EVENT_TYPE.KEYWORDS, EVENT_TYPE.KEYWORDS),
    )

    bk_event_group_id = models.IntegerField(_("事件分组ID"), primary_key=True)
    bk_data_id = models.IntegerField(_("数据ID"))
    bk_biz_id = models.IntegerField(_("业务ID"), default=0, db_index=True)
    name = models.CharField(_("名称"), max_length=128)
    scenario = models.CharField(_("监控场景"), max_length=128, db_index=True)
    is_enable = models.BooleanField(_("是否启用"), default=True)
    table_id = models.CharField(_("结果表ID"), max_length=128, default="")
    type = models.CharField(_("事件组类型"), max_length=128, choices=PLUGIN_TYPE_CHOICES, default="custom_event")

    def __str__(self):
        return f"{self.name}"  # noqa


class CustomEventItem(models.Model):
    """
    自定义事件定义
    """

    bk_event_group = models.ForeignKey(CustomEventGroup, verbose_name=_("事件分组ID"), related_name="event_info_list")
    custom_event_id = models.IntegerField(_("事件ID"), primary_key=True)
    custom_event_name = models.CharField(_("名称"), max_length=128)
    dimension_list = JsonField(_("维度"), default=[])


class CustomTSTable(OperateRecordModelBase):
    """
    自定义时序
    """

    time_series_group_id = models.IntegerField(_("时序分组ID"), primary_key=True)
    bk_data_id = models.IntegerField(_("数据ID"))
    bk_biz_id = models.IntegerField(_("业务ID"), default=0, db_index=True)
    name = models.CharField(_("名称"), max_length=128)
    scenario = models.CharField(_("监控场景"), max_length=128, db_index=True)
    table_id = models.CharField(_("结果表ID"), max_length=128, default="")

    def __str__(self):
        return f"[{self.bk_biz_id}]{self.table_id}-{self.bk_data_id}"

    @property
    def token(self):
        data_id_info = api.metadata.get_data_id({"bk_data_id": self.bk_data_id})
        return data_id_info["token"]

    def metric_detail(self):
        custom_ts_items = []
        params = {
            "time_series_group_id": self.time_series_group_id,
        }
        result = api.metadata.get_time_series_group(params)
        # 查询数据库记录以确定指标的分组标签
        old_metrics = CustomTSItem.objects.filter(table=self).exclude(label="").only("metric_name", "label")
        metric_labels = {metric.metric_name: metric.label for metric in old_metrics}

        metric_names = []
        for metric in result["metric_info_list"]:
            if not metric:
                continue

            metric_names.append(metric["field_name"])
            group_info = {
                "table": self,
                "metric_name": metric["field_name"],
                "unit": metric["unit"],
                "type": metric["type"],
                "metric_display_name": metric["description"],
                "dimension_list": metric["tag_list"],
                "label": metric_labels.get(metric["field_name"], ""),
            }

            custom_ts_items.append(group_info)

        # 清理不存在的指标记录
        need_clean_metric_names = set(metric_labels.keys()) - set(metric_names)
        CustomTSItem.objects.filter(table=self, metric_name__in=need_clean_metric_names).delete()

        return custom_ts_items

    def get_metrics(self):
        field_map = {}
        for metric_info in self.metric_detail():
            if metric_info["metric_name"] not in field_map:
                field_map[metric_info["metric_name"]] = {
                    "name": metric_info["metric_name"],
                    "monitor_type": "metric",
                    "unit": metric_info["unit"],
                    "description": metric_info["metric_display_name"],
                    "type": metric_info["type"],
                    "label": metric_info["label"],
                }
            for dimension in metric_info["dimension_list"]:
                if dimension["field_name"] not in field_map:
                    field_map[dimension["field_name"]] = {
                        "name": dimension["field_name"],
                        "monitor_type": "dimension",
                        "unit": "",
                        "description": dimension["description"],
                        "type": "string",
                    }
        return field_map

    def query_target(self):
        tag_values = api.metadata.query_tag_values(table_id=self.table_id, tag_name="target")
        return tag_values["tag_values"]

    def query_dimensions(self, metric):
        metric_info = self.metric_list.filter(metric_name=metric).first()
        if not metric_info:
            for field in self.metric_detail():
                if field["metric_name"] == metric:
                    dimension_list = field["dimension_list"]
                    break
            else:
                dimension_list = []
        else:
            dimension_list = metric_info.dimension_list
        dimensions = [dimension["field_name"] for dimension in dimension_list if dimension["field_name"] != "target"]
        return dimensions


class CustomTSItem(models.Model):
    """
    自定义时序指标
    """

    table = models.ForeignKey(CustomTSTable, verbose_name=_("自定义时序ID"), related_name="metric_list", default=0)
    metric_name = models.CharField(_("指标名称"), max_length=128)
    type = models.CharField(_("类型"), max_length=16, default="")
    unit = models.CharField(_("字段单位"), max_length=16, default="")
    metric_display_name = models.CharField(_("指标别名"), max_length=128, default="")
    dimension_list = JsonField(_("维度"), default=[])
    label = models.CharField(_("分组标签"), max_length=32, default="", blank=True)
    hidden = models.BooleanField(_("隐藏图表"), default=False)
