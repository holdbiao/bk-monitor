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

from bkmonitor.utils.db.fields import JsonField
from constants.data_source import DataSourceLabel, DataTypeLabel


class MetricListCache(models.Model):
    """
    指标选择器缓存表
    """

    bk_biz_id = models.IntegerField(verbose_name=_("业务ID"), db_index=True)
    result_table_id = models.CharField(max_length=256, default="", verbose_name=_("sql查询表"))
    result_table_name = models.CharField(max_length=256, default="", verbose_name=_("表别名"))
    metric_field = models.CharField(max_length=256, default="", verbose_name=_("指标名"))
    metric_field_name = models.CharField(max_length=256, default="", verbose_name=_("指标别名"))
    unit = models.CharField(max_length=256, default="", verbose_name=_("单位"))
    unit_conversion = models.FloatField(default=1.0, verbose_name=_("单位换算"))
    dimensions = JsonField(default=[], verbose_name=_("维度名"))
    plugin_type = models.CharField(max_length=256, default="", verbose_name=_("插件类型"))
    related_name = models.CharField(max_length=256, default="", verbose_name=_("插件名、拨测任务名"))
    related_id = models.CharField(max_length=256, default="", verbose_name=_("插件id、拨测任务id"))
    collect_config = models.TextField(default="", verbose_name=_("插件采集关联采集配置"))
    collect_config_ids = JsonField(verbose_name=_("插件采集关联采集配置id"))
    result_table_label = models.CharField(max_length=128, verbose_name=_("表标签"))
    data_source_label = models.CharField(max_length=128, verbose_name=_("数据源标签"))
    data_type_label = models.CharField(max_length=128, verbose_name=_("数据类型标签"))
    data_target = models.CharField(max_length=128, verbose_name=_("数据目标标签"))
    default_dimensions = JsonField(verbose_name=_("默认维度列表"))
    default_condition = JsonField(verbose_name=_("默认监控条件"))
    description = models.TextField(default="", verbose_name=_("指标含义"))
    collect_interval = models.IntegerField(default=1, verbose_name=_("指标采集周期"))
    category_display = models.CharField(max_length=128, default="", verbose_name=_("分类显示名"))
    result_table_label_name = models.CharField(max_length=255, default="", verbose_name=_("表标签别名"))
    extend_fields = JsonField(default={}, verbose_name=_("额外字段"))
    use_frequency = models.IntegerField(default=0, verbose_name=_("使用频率"))
    last_update = models.DateTimeField(auto_now=True, verbose_name=_("最近更新时间"), db_index=True)

    class Meta:
        index_together = (
            ("result_table_id", "metric_field", "bk_biz_id"),
            ("data_type_label", "data_source_label", "bk_biz_id"),
        )

    @classmethod
    def item_description(cls, item):
        """
        策略监控项说明
        """
        templates = {
            DataSourceLabel.BK_MONITOR_COLLECTOR: {
                DataTypeLabel.TIME_SERIES: "{item_name}({result_table_id}.{metric_field})",
                DataTypeLabel.EVENT: "{item_name}",
                DataTypeLabel.LOG: "{item_name}",
            },
            DataSourceLabel.BK_DATA: {
                DataTypeLabel.TIME_SERIES: "{metric_field_name}({result_table_id}.{metric_field})",
            },
            DataSourceLabel.BK_LOG_SEARCH: {
                DataTypeLabel.TIME_SERIES: "{metric_field}(索引集:{item_name})",
                DataTypeLabel.LOG: "{keywords_query_string}(索引集:{item_name})",
            },
            DataSourceLabel.CUSTOM: {
                DataTypeLabel.EVENT: "{item_name}(数据ID:{result_table_id})",
                DataTypeLabel.TIME_SERIES: "{item_name}({result_table_id}.{metric_field})",
            },
        }

        params = {
            "metric_field": item.get("metric_field", ""),
            "metric_field_name": item.get("metric_field_name", ""),
            "result_table_id": item.get("result_table_id", ""),
            "item_name": item.get("item_name", ""),
            "keywords_query_string": item.get("keywords_query_string", ""),
        }

        return templates[item["data_source_label"]][item["data_type_label"]].format(**params)

    @classmethod
    def metric_description(cls, item=None, metric=None):
        """
        指标说明
        :param item: 监控指标配置
        :type item: dict
        :return: 指标说明
        :type: str
        """
        templates = {
            DataSourceLabel.BK_MONITOR_COLLECTOR: {
                DataTypeLabel.TIME_SERIES: _(
                    "指标：{metric_field}；指标分类：{result_table_name}；" "插件名：{related_name}；数据来源：监控采集"
                ),
                DataTypeLabel.EVENT: _("数据来源：系统事件"),
                DataTypeLabel.LOG: _("数据来源：采集配置"),
            },
            DataSourceLabel.BK_DATA: {
                DataTypeLabel.TIME_SERIES: _("指标：{metric_field}；结果表：{result_table_name}；数据来源：计算平台"),
            },
            DataSourceLabel.BK_LOG_SEARCH: {
                DataTypeLabel.TIME_SERIES: _("索引：{result_table_name}；索引集：{related_name}；数据来源：日志平台"),
                DataTypeLabel.LOG: _("数据来源：日志平台"),
            },
            DataSourceLabel.CUSTOM: {
                DataTypeLabel.EVENT: _("数据ID：{result_table_id}；数据名称：{result_table_name}；数据来源：自定义事件"),
                DataTypeLabel.TIME_SERIES: _("指标：{metric_field_name}；数据名称：{related_name}；数据来源：自定义时序"),
            },
        }

        if item:
            template = templates.get(item["data_source_label"], {}).get(item["data_type_label"], "")

            if (item["data_source_label"], item["data_type_label"]) in [
                (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.LOG),
                (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.LOG),
                (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.EVENT),
            ]:
                return template
            if not item.get("result_table_id"):
                rt_id = ".".join(item["metric_id"].split(".")[-2:])
            else:
                rt_id = item.get("result_table_id", "")
            metric = cls.objects.filter(
                data_source_label=item["data_source_label"],
                data_type_label=item["data_type_label"],
                result_table_id=rt_id,
                metric_field=item["metric_id"].split(".")[-1],
            )

            if not metric:
                return ""
            metric = metric[0]
        elif metric:
            template = templates.get(metric.data_source_label, {}).get(metric.data_type_label, "")
        else:
            return ""

        if (
            metric.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR
            and metric.data_type_label == DataTypeLabel.TIME_SERIES
            and metric.result_table_label == "uptimecheck"
        ):
            template = _("指标：{metric_field}；指标分类：{result_table_name}；数据来源：监控采集")

        return template.format(**metric.__dict__)
