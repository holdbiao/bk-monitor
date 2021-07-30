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
策略核心数据模型V2
"""

from django.contrib import admin
from django.db.models import Model
from django.utils.translation import gettext_lazy as _lazy
from django.db import models
from django_mysql.models import JSONField

from bkmonitor.middlewares.source import get_source_app_code
from core.drf_resource import resource


__all__ = [
    "StrategyModel",
    "ItemModel",
    "DetectModel",
    "AlgorithmModel",
    "QueryConfigModel",
    "StrategyLabel",
    "StrategyHistoryModel",
    "StrategyModelAdmin",
    "StrategyHistoryModelAdmin",
    "ItemModelAdmin",
    "DetectModelAdmin",
    "AlgorithmModelAdmin",
    "QueryConfigModelAdmin",
]


def default_target():
    return [[]]


def no_data_config():
    return {"is_enabled": True, "continuous": 5, "agg_dimension": []}


class ItemModelAdmin(admin.ModelAdmin):
    """
    监控项表展示
    """

    list_display = ("id", "strategy_id", "name", "expression", "no_data_config")
    search_fields = ("expression", "name", "origin_sql")


class ItemModel(Model):
    """
    监控项模型
    """

    strategy_id = models.IntegerField(_lazy("关联策略ID"), db_index=True)
    name = models.CharField(_lazy("监控项名称"), max_length=256)
    expression = models.TextField(_lazy("计算公式"))
    origin_sql = models.TextField(_lazy("原始查询语句"))
    no_data_config = JSONField(_lazy("无数据配置"), default=no_data_config)
    target = JSONField(_lazy("监控目标"), default=default_target)
    meta = JSONField(_lazy("查询配置元数据"), default=list)

    class Meta:
        verbose_name = _lazy("监控项配置V2")
        verbose_name_plural = _lazy("监控项配置V2")
        db_table = "alarm_item_v2"


class DetectModelAdmin(admin.ModelAdmin):
    """
    配置表展示
    """

    list_display = ("strategy_id", "level", "connector", "expression", "trigger_config", "recovery_config")
    search_fields = ("expression",)
    list_filter = ("level", "connector")


class DetectModel(Model):
    """
    检测配置模型
    """

    strategy_id = models.IntegerField(_lazy("关联策略ID"), db_index=True)
    level = models.IntegerField(
        _lazy("告警级别"),
        default=3,
        choices=(
            (1, _lazy("致命")),
            (2, _lazy("预警")),
            (3, _lazy("提醒")),
        ),
    )
    expression = models.TextField(_lazy("计算公式"), default="")
    trigger_config = JSONField(_lazy("触发条件配置"))
    recovery_config = JSONField(_lazy("恢复条件配置"))
    connector = models.CharField(_lazy("同级别算法连接符"), choices=(("and", "AND"), ("or", "OR")), max_length=4, default="and")

    class Meta:
        verbose_name = _lazy("检测配置V2")
        verbose_name_plural = _lazy("检测配置V2")
        db_table = "alarm_detect_v2"


class AlgorithmModelAdmin(admin.ModelAdmin):
    """
    算法配置表展示
    """

    list_display = ("strategy_id", "item_id", "level", "type", "unit_prefix")
    search_fields = ("unit_prefix",)
    list_filter = ("level", "type")


class AlgorithmModel(Model):
    """
    检测算法模型
    常用查询：
        1. 基于监控项ID
        2. 基于算法类型
    """

    class AlgorithmChoices(object):
        Threshold = "Threshold"
        SimpleRingRatio = "SimpleRingRatio"
        AdvancedRingRatio = "AdvancedRingRatio"
        SimpleYearRound = "SimpleYearRound"
        AdvancedYearRound = "AdvancedYearRound"
        PartialNodes = "PartialNodes"
        OsRestart = "OsRestart"
        ProcPort = "ProcPort"
        PingUnreachable = "PingUnreachable"
        YearRoundAmplitude = "YearRoundAmplitude"
        YearRoundRange = "YearRoundRange"
        RingRatioAmplitude = "RingRatioAmplitude"
        IntelligentDetect = "IntelligentDetect"

    ALGORITHM_CHOICES = (
        (AlgorithmChoices.Threshold, _lazy("静态阈值算法")),
        (AlgorithmChoices.SimpleRingRatio, _lazy("简易环比算法")),
        (AlgorithmChoices.AdvancedRingRatio, _lazy("高级环比算法")),
        (AlgorithmChoices.SimpleYearRound, _lazy("简易同比算法")),
        (AlgorithmChoices.AdvancedYearRound, _lazy("高级同比算法")),
        (AlgorithmChoices.PartialNodes, _lazy("部分节点数算法")),
        (AlgorithmChoices.OsRestart, _lazy("主机重启算法")),
        (AlgorithmChoices.ProcPort, _lazy("进程端口算法")),
        (AlgorithmChoices.PingUnreachable, _lazy("Ping不可达算法")),
        (AlgorithmChoices.YearRoundAmplitude, _lazy("同比振幅算法")),
        (AlgorithmChoices.YearRoundRange, _lazy("同比区间算法")),
        (AlgorithmChoices.RingRatioAmplitude, _lazy("环比振幅算法")),
        (AlgorithmChoices.IntelligentDetect, _lazy("智能异常检测算法")),
    )

    strategy_id = models.IntegerField(_lazy("关联策略ID"), db_index=True)
    item_id = models.IntegerField(_lazy("关联监控项ID"), db_index=True)
    level = models.IntegerField(
        _lazy("告警级别"),
        default=3,
        choices=(
            (1, _lazy("致命")),
            (2, _lazy("预警")),
            (3, _lazy("提醒")),
        ),
    )
    type = models.CharField(_lazy("算法类型"), max_length=64, choices=ALGORITHM_CHOICES, db_index=True)
    unit_prefix = models.CharField(_lazy("算法单位前缀"), max_length=32, default="", blank=True)
    config = JSONField(_lazy("算法配置"))

    class Meta:
        verbose_name = _lazy("检测算法配置V2")
        verbose_name_plural = _lazy("检测算法配置V2")
        db_table = "alarm_algorithm_v2"


class QueryConfigModelAdmin(admin.ModelAdmin):
    """
    查询配置表展示
    """

    list_display = ("strategy_id", "item_id", "alias", "metric_id", "data_source_label", "data_type_label")
    search_fields = ("metric_id", "alias")
    list_filter = ("data_source_label", "data_type_label")


class QueryConfigModel(Model):
    """
    查询配置基类
    """

    strategy_id = models.IntegerField(_lazy("关联策略ID"), db_index=True)
    item_id = models.IntegerField(_lazy("关联监控项ID"), db_index=True)
    alias = models.CharField(_lazy("别名"), max_length=12)
    data_source_label = models.CharField(_lazy("数据来源标签"), max_length=32)
    data_type_label = models.CharField(_lazy("数据类型标签"), max_length=32)
    metric_id = models.CharField(_lazy("指标ID"), max_length=128)
    config = JSONField(_lazy("查询配置"))

    class Meta:
        verbose_name = _lazy("查询配置表V2")
        verbose_name_plural = _lazy("查询配置表V2")
        db_table = "alarm_query_config_v2"

    def to_obj(self):
        from bkmonitor.strategy.new_strategy import QueryConfig

        return QueryConfig.from_models([self])[0]


class StrategyLabel(Model):
    """
    策略全局标签
    tag_name： /a/b/c/  - 3级标签 /a/b/
    全局标签：bk_biz_id: 0 , strategy_id: 0
    """

    label_name = models.CharField(max_length=128, verbose_name=_lazy("策略名称"))
    bk_biz_id = models.IntegerField(verbose_name=_lazy("业务ID"), default=0, blank=True, db_index=True)
    strategy_id = models.IntegerField(verbose_name=_lazy("业务ID"), default=0, blank=True)

    class Meta:
        verbose_name = _lazy("策略标签")
        verbose_name_plural = _lazy("策略标签")
        db_table = "alarm_strategy_label"
        index_together = (("label_name", "strategy_id"),)

    @classmethod
    def get_label_dict(cls, strategy_id=None):
        # global mem_cache
        label_dict = {}
        queryset = cls.objects
        if strategy_id is not None:
            queryset = queryset.filter(strategy_id=strategy_id)
        for strategy_id, label_name in queryset.values_list("strategy_id", "label_name"):
            label_dict.setdefault(strategy_id, []).append(label_name.strip("/"))
        return label_dict

    @classmethod
    def save_strategy_label(cls, bk_biz_id, strategy_id, labels):
        resource.strategies.delete_strategy_label(strategy_id=strategy_id)
        for label in labels:
            resource.strategies.strategy_label(label_name=label, strategy_id=strategy_id, bk_biz_id=bk_biz_id)


class StrategyModelAdmin(admin.ModelAdmin):
    """
    策略表展示
    """

    list_display = ("id", "name", "bk_biz_id", "scenario", "source", "type", "is_enabled")
    search_fields = ("name", "create_user", "bk_biz_id", "update_user")
    list_filter = ("source", "scenario", "type", "is_enabled")


class StrategyModel(Model):
    """
    策略表
    """

    class StrategyType:
        Monitor = "monitor"
        FTASolution = "fta_solution"

    name = models.CharField(_lazy("策略名称"), max_length=128, db_index=True)
    bk_biz_id = models.IntegerField(_lazy("业务ID"))
    source = models.CharField(_lazy("来源系统"), default=get_source_app_code, max_length=32)
    scenario = models.CharField(_lazy("监控场景"), max_length=32)
    type = models.CharField(
        _lazy("策略类型"),
        max_length=12,
        db_index=True,
        choices=((StrategyType.Monitor, _lazy("监控")), (StrategyType.FTASolution, _lazy("故障自愈"))),
    )
    is_enabled = models.BooleanField(_lazy("是否启用"), default=True)
    create_user = models.CharField(_lazy("创建人"), max_length=32, default="")
    create_time = models.DateTimeField(_lazy("创建时间"), auto_now_add=True)
    update_user = models.CharField(_lazy("最后修改人"), max_length=32, default="")
    update_time = models.DateTimeField(_lazy("最后修改时间"), auto_now=True)

    class Meta:
        verbose_name = _lazy("策略配置V2")
        verbose_name_plural = _lazy("策略配置V2")
        db_table = "alarm_strategy_v2"
        index_together = (("is_enabled", "bk_biz_id", "scenario"),)

    @property
    def labels(self):
        # global mem_cache
        # labels = mem_cache.get(self.id)
        # if labels is None:
        labels = StrategyLabel.get_label_dict(self.id).get(self.id)
        return labels or []

    @property
    def target_type(self):
        from constants.strategy import DataTarget
        from monitor_web.models import DataTargetMapping

        data_target_map = dict(
            [(DataTarget.HOST_TARGET, "HOST"), (DataTarget.SERVICE_TARGET, "SERVICE"), (DataTarget.NONE_TARGET, None)]
        )
        result_table_label = self.scenario
        item_instance = QueryConfigModel.objects.filter(strategy_id=self.id).first()
        target_type = DataTargetMapping().get_data_target(
            result_table_label, item_instance.data_source_label, item_instance.data_type_label
        )
        return data_target_map[target_type]


class StrategyHistoryModel(Model):
    """
    策略历史表
    """

    strategy_id = models.IntegerField(_lazy("关联策略ID"), db_index=True)
    create_time = models.DateTimeField(_lazy("创建时间"), auto_now_add=True)
    create_user = models.CharField(_lazy("创建者"), max_length=32)
    content = JSONField(_lazy("保存内容"))
    operate = models.CharField(
        _lazy("操作"),
        choices=(
            ("delete", _lazy("删除")),
            ("create", _lazy("创建")),
            ("update", _lazy("更新")),
        ),
        db_index=True,
        max_length=12,
    )
    status = models.BooleanField(_lazy("操作状态"), default=False)
    message = models.TextField(_lazy("错误信息"), default="", blank=True)

    class Meta:
        verbose_name = _lazy("策略配置操作历史")
        verbose_name_plural = _lazy("策略配置操作历史")
        db_table = "alarm_strategy_history"
        ordering = ("-create_time",)


class StrategyHistoryModelAdmin(admin.ModelAdmin):
    """
    策略历史表展示
    """

    list_display = ("operate", "strategy_id", "create_user", "status", "create_time")
    search_fields = ("strategy_id", "create_user")
    list_filter = ("operate", "status")
