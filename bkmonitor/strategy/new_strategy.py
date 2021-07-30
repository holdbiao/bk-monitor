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
import abc
import copy
import logging
import traceback
from collections import defaultdict
from datetime import datetime
from itertools import chain
from typing import Dict, List, Union, Type

from django.conf import settings
from django.db import transaction
from django.db.models import Model, QuerySet
from rest_framework import serializers

from bkmonitor.models.strategy import (
    StrategyModel,
    ItemModel,
    DetectModel,
    AlgorithmModel,
    QueryConfigModel,
    StrategyHistoryModel,
)
from bkmonitor.strategy.serializers import (
    BkMonitorTimeSeriesSerializer,
    BkMonitorLogSerializer,
    BkLogSearchLogSerializer,
    BkLogSearchTimeSeriesSerializer,
    CustomEventSerializer,
    CustomTimeSeriesSerializer,
    BkMonitorEventSerializer,
    BkDataTimeSeriesSerializer,
)
from bkmonitor.models import Action as ActionModel, ActionNoticeMapping, NoticeTemplate, NoticeGroup
from constants.data_source import DataSourceLabel, DataTypeLabel
from constants.strategy import (
    TargetFieldType,
    AdvanceConditionMethod,
    SYSTEM_EVENT_RT_TABLE_ID,
)
from core.errors.strategy import StrategyNotExist

logger = logging.getLogger(__name__)


def get_metric_id(data_source_label, data_type_label, result_table_id="", index_set_id="", metric_field="", **kwargs):
    """
    生成metric_id
    """
    metric_id_map = {
        DataSourceLabel.BK_MONITOR_COLLECTOR: {
            DataTypeLabel.TIME_SERIES: "{}.{}.{}".format(data_source_label, result_table_id, metric_field),
            DataTypeLabel.EVENT: "{}.{}".format(data_source_label, metric_field),
            DataTypeLabel.LOG: "{}.{}.{}".format(data_source_label, data_type_label, metric_field),
        },
        DataSourceLabel.CUSTOM: {
            DataTypeLabel.EVENT: "{}.{}.{}.{}".format(
                data_source_label, data_type_label, result_table_id, metric_field
            ),
            DataTypeLabel.TIME_SERIES: "{}.{}.{}".format(data_source_label, result_table_id, metric_field),
        },
        DataSourceLabel.BK_LOG_SEARCH: {
            DataTypeLabel.LOG: "{}.index_set.{}".format(data_source_label, index_set_id),
            DataTypeLabel.TIME_SERIES: "{}.index_set.{}.{}".format(data_source_label, index_set_id, metric_field),
        },
        DataSourceLabel.BK_DATA: {
            DataTypeLabel.TIME_SERIES: "{}.{}.{}".format(data_source_label, result_table_id, metric_field),
        },
    }
    return metric_id_map.get(data_source_label, {}).get(data_type_label, "")


class AbstractConfig(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_dict(self, *args, **kwargs) -> Dict:
        raise NotImplementedError

    @classmethod
    def delete_useless(cls, *args, **kwargs):
        return

    @classmethod
    def reuse_exists_records(cls, model: Type[Model], objs: List[Model], configs: List["AbstractConfig"]):
        """
        重用存量的数据库记录，删除多余的记录
        :param model: 模型
        :param objs: 数据库记录
        :param configs: 配置对象
        """
        for config, obj in zip(configs, objs):
            config.id = obj.id
        # fmt: off
        for config in configs[len(objs):]:
            config.id = 0
        if objs[len(configs):]:
            obj_ids = [obj.id for obj in objs[len(configs):]]
            model.objects.filter(id__in=obj_ids).delete()
            configs[0].__class__.delete_useless(obj_ids)
        # fmt: on

    @staticmethod
    def _get_username():
        try:
            from blueapps.utils import get_request

            username = get_request().user.username
        except IndexError:
            username = "system"
        return username

    @abc.abstractmethod
    def save(self):
        raise NotImplementedError


class Action(AbstractConfig):
    """
    动作配置
    """

    class Serializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        type = serializers.CharField()
        config = serializers.DictField()
        notice_group_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

    def __init__(
        self,
        strategy_id: int,
        type: str,
        config: Dict = None,
        notice_group_ids: List[int] = None,
        notice_template: Dict = None,
        id: int = 0,
        **kwargs,
    ):
        self.id = id
        self.strategy_id = strategy_id
        self.type = type
        self.config: Dict = config
        self.notice_group_ids: List[int] = notice_group_ids or []
        self.notice_template = notice_template or {"anomaly_template": "", "recovery_template": ""}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "config": self.config,
            "notice_group_ids": self.notice_group_ids,
            "notice_template": self.notice_template,
        }

    @classmethod
    def delete_useless(cls, useless_action_ids: List[int]):
        """
        删除策略下多余的Action记录
        """
        ActionNoticeMapping.objects.filter(action_id__in=useless_action_ids).delete()
        NoticeTemplate.objects.filter(action_id__in=useless_action_ids).delete()

    def _create(self):
        """
        新建Action记录
        """
        action = ActionModel.objects.create(action_type=self.type, config=self.config, strategy_id=self.strategy_id)
        self.id = action.id

        action_notices = []
        for notice_group_id in self.notice_group_ids:
            action_notices.append(ActionNoticeMapping(action_id=self.id, notice_group_id=notice_group_id))
        ActionNoticeMapping.objects.bulk_create(action_notices)

        NoticeTemplate.objects.create(
            action_id=self.id,
            anomaly_template=self.notice_template.get("anomaly_template", ""),
            recovery_template=self.notice_template.get("recovery_template", ""),
        )

    def save(self):
        """
        根据配置新建或更新Action记录
        """
        try:
            if self.id > 0:
                action = ActionModel.objects.get(id=self.id, strategy_id=self.strategy_id)
            else:
                self._create()
                return
        except ActionModel.DoesNotExist:
            self._create()
            return
        else:
            action.action_type = self.type
            action.config = self.config
            action.save()

        action_notices = ActionNoticeMapping.objects.filter(action_id=self.id)
        exists_notice_group_ids = {notice_group.notice_group_id for notice_group in action_notices}
        current_notice_group_ids = set(self.notice_group_ids)

        # 删除多余的关联记录
        delete_notice_group_ids = exists_notice_group_ids - current_notice_group_ids
        if delete_notice_group_ids:
            ActionNoticeMapping.objects.filter(action_id=self.id, notice_group_id__in=delete_notice_group_ids).delete()

        # 新增关联记录
        new_notice_group_ids = current_notice_group_ids - exists_notice_group_ids
        if new_notice_group_ids:
            ActionNoticeMapping.objects.bulk_create(
                [
                    ActionNoticeMapping(action_id=self.id, notice_group_id=notice_group_id)
                    for notice_group_id in new_notice_group_ids
                ]
            )

        # 更新通知模板
        NoticeTemplate.objects.filter(action_id=self.id).update(
            anomaly_template=self.notice_template.get("anomaly_template", ""),
            recovery_template=self.notice_template.get("recovery_template", ""),
        )

    @classmethod
    def from_models(cls, actions: List["ActionModel"], notice_templates: Dict[int, NoticeTemplate]) -> List["Action"]:
        """
        数据模型转换为监控项对象
        """
        action_ids = [action.id for action in actions]
        notice_group_ids = defaultdict(list)
        for record in ActionNoticeMapping.objects.filter(action_id__in=action_ids):
            notice_group_ids[record.action_id].append(record.notice_group_id)

        return [
            Action(
                strategy_id=action.strategy_id,
                id=action.id,
                type=action.action_type,
                config=action.config,
                notice_group_ids=notice_group_ids[action.id],
                notice_template={
                    "anomaly_template": notice_templates[action.id].anomaly_template,
                    "recovery_template": notice_templates[action.id].recovery_template,
                },
            )
            for action in actions
        ]


class Algorithm(AbstractConfig):
    """
    检测算法
    """

    class Serializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        type = serializers.CharField()
        level = serializers.IntegerField()
        unit_prefix = serializers.CharField()
        config = serializers.JSONField()

    def __init__(
        self,
        strategy_id: int,
        item_id: int,
        type: str,
        config: Union[Dict, List[List[Dict]]],
        level: int,
        unit_prefix: str = "",
        id: int = 0,
        **kwargs,
    ):
        self.id = id
        self.type = type
        self.config = config
        self.level = level
        self.unit_prefix = unit_prefix
        self.strategy_id = strategy_id
        self.item_id = item_id

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "level": self.level,
            "config": self.config,
            "unit_prefix": self.unit_prefix,
        }

    def _create(self):
        algorithm = AlgorithmModel.objects.create(
            type=self.type,
            config=self.config,
            unit_prefix=self.unit_prefix,
            strategy_id=self.strategy_id,
            item_id=self.item_id,
            level=self.level,
        )
        self.id = algorithm.id

    def save(self):
        try:
            if self.id > 0:
                algorithm: AlgorithmModel = AlgorithmModel.objects.get(
                    id=self.id, strategy_id=self.strategy_id, item_id=self.item_id
                )
            else:
                self._create()
                return
        except AlgorithmModel.DoesNotExist:
            self._create()
        else:
            algorithm.type = self.type
            algorithm.config = self.config
            algorithm.unit_prefix = self.unit_prefix
            algorithm.level = self.level
            algorithm.save()

    @classmethod
    def from_models(cls, algorithms: List[AlgorithmModel]) -> List["Algorithm"]:
        """
        根据数据模型生成算法配置对象
        """
        return [
            Algorithm(
                id=algorithm.id,
                strategy_id=algorithm.strategy_id,
                item_id=algorithm.item_id,
                type=algorithm.type,
                config=algorithm.config,
                level=algorithm.level,
                unit_prefix=algorithm.unit_prefix,
            )
            for algorithm in algorithms
        ]


class Detect(AbstractConfig):
    """
    检测配置
    """

    class Serializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        level = serializers.IntegerField()
        expression = serializers.CharField()
        trigger_config = serializers.DictField()
        recovery_config = serializers.DictField()
        connector = serializers.CharField()

    def __init__(
        self,
        strategy_id: int,
        level: Union[int, str],
        trigger_config: Dict,
        recovery_config: Dict,
        expression: str = "",
        connector: str = "and",
        id: int = 0,
        **kwargs,
    ):
        self.id = id
        self.level = int(level)
        self.expression = expression
        self.strategy_id = strategy_id
        self.trigger_config = trigger_config
        self.recovery_config = recovery_config
        self.connector = connector

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "level": self.level,
            "expression": self.expression,
            "trigger_config": self.trigger_config,
            "recovery_config": self.recovery_config,
            "connector": self.connector,
        }

    def _create(self):
        detect = DetectModel.objects.create(
            strategy_id=self.strategy_id,
            level=self.level,
            expression=self.expression,
            trigger_config=self.trigger_config,
            recovery_config=self.recovery_config,
            connector=self.connector,
        )
        self.id = detect.id

    def save(self):
        try:
            if self.id > 0:
                detect: DetectModel = DetectModel.objects.get(id=self.id, strategy_id=self.strategy_id)
            else:
                self._create()
                return
        except DetectModel.DoesNotExist:
            self._create()
        else:
            detect.level = self.level
            detect.trigger_config = self.trigger_config
            detect.recovery_config = self.recovery_config
            detect.expression = self.expression
            detect.connector = self.connector
            detect.save()

    @classmethod
    def from_models(cls, detects: List["DetectModel"]) -> List["Detect"]:
        """
        数据模型转换为监控项对象
        """
        return [
            Detect(
                id=detect.id,
                strategy_id=detect.strategy_id,
                level=detect.level,
                expression=detect.expression,
                trigger_config=detect.trigger_config,
                recovery_config=detect.recovery_config,
                connector=detect.connector,
            )
            for detect in detects
        ]


class QueryConfig(AbstractConfig):
    """
    查询配置
    """

    index_set_id: int
    result_table_id: str
    agg_method: str
    agg_interval: int
    agg_dimension: List[str]
    agg_condition: List[Dict]
    metric_field: str
    unit: str
    time_field: str
    custom_event_name: str
    origin_config: Dict
    intelligent_detect: Dict
    values: List[str]

    QueryConfigSerializerMapping = {
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES): BkMonitorTimeSeriesSerializer,
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.LOG): BkMonitorLogSerializer,
        (DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.EVENT): BkMonitorEventSerializer,
        (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.TIME_SERIES): BkLogSearchTimeSeriesSerializer,
        (DataSourceLabel.BK_LOG_SEARCH, DataTypeLabel.LOG): BkLogSearchLogSerializer,
        (DataSourceLabel.CUSTOM, DataTypeLabel.TIME_SERIES): CustomTimeSeriesSerializer,
        (DataSourceLabel.CUSTOM, DataTypeLabel.EVENT): CustomEventSerializer,
        (DataSourceLabel.BK_DATA, DataTypeLabel.TIME_SERIES): BkDataTimeSeriesSerializer,
    }

    def __init__(
        self,
        strategy_id: int,
        item_id: int,
        data_source_label: str,
        data_type_label: str,
        alias: str,
        id: int = 0,
        metric_id: str = "",
        **kwargs,
    ):
        self.strategy_id = strategy_id
        self.item_id = item_id
        self.data_source_label = data_source_label
        self.data_type_label = data_type_label
        self.alias = alias
        self.id = id
        self.metric_id = metric_id or ""
        serializer_class = self._get_serializer(data_source_label, data_type_label)
        serializer = serializer_class(data=kwargs)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(self, field, value)

    @classmethod
    def _get_serializer(cls, data_source_label: str, data_type_label: str) -> Type[serializers.Serializer]:
        return cls.QueryConfigSerializerMapping[(data_source_label, data_type_label)]

    def get_metric_id(self):
        return get_metric_id(
            data_source_label=self.data_source_label,
            data_type_label=self.data_type_label,
            result_table_id=getattr(self, "result_table_id", ""),
            index_set_id=getattr(self, "index_set_id", ""),
            metric_field=getattr(self, "metric_field", ""),
        )

    def to_dict(self):
        # 自动生成metric_id
        if not self.metric_id:
            self.metric_id = self.get_metric_id()

        result = {
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "alias": self.alias,
            "metric_id": self.metric_id,
            "id": self.id,
        }

        for field in self._get_serializer(self.data_source_label, self.data_type_label)().fields.keys():
            if hasattr(self, field):
                result[field] = getattr(self, field)
        return result

    def _create(self):
        serializer = self._get_serializer(self.data_source_label, self.data_type_label)(data=self.to_dict())
        serializer.is_valid(raise_exception=True)
        obj = QueryConfigModel.objects.create(
            strategy_id=self.strategy_id,
            item_id=self.item_id,
            data_source_label=self.data_source_label,
            data_type_label=self.data_type_label,
            metric_id=self.metric_id,
            alias=self.alias,
            config=serializer.validated_data,
        )
        self.id = obj.id

    def save(self):
        self._clean_empty_dimension()
        self._supplement_advance_condition_dimension()

        try:
            if self.id > 0:
                query_config: QueryConfigModel = QueryConfigModel.objects.get(
                    id=self.id, item_id=self.item_id, strategy_id=self.strategy_id
                )
            else:
                self._create()
                return
        except QueryConfigModel.DoesNotExist:
            self._create()
            return

        serializer = self._get_serializer(self.data_source_label, self.data_type_label)(data=self.to_dict())
        serializer.is_valid(raise_exception=True)
        data = {
            "alias": self.alias,
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "metric_id": self.metric_id,
            "config": serializer.validated_data,
        }
        for field, value in data.items():
            setattr(query_config, field, value)
        query_config.save()

    @classmethod
    def from_models(cls, query_configs: List[QueryConfigModel]) -> List["QueryConfig"]:
        """
        根据数据模型获取查询配置对象
        """
        records = []
        for query_config in query_configs:
            serializer_class = cls._get_serializer(query_config.data_source_label, query_config.data_type_label)
            serializer = serializer_class(data=query_config.config)
            serializer.is_valid()
            record = QueryConfig(
                id=query_config.id,
                strategy_id=query_config.strategy_id,
                item_id=query_config.item_id,
                alias=query_config.alias,
                data_source_label=query_config.data_source_label,
                data_type_label=query_config.data_type_label,
                **serializer.validated_data,
            )

            records.append(record)
        return records

    def _supplement_advance_condition_dimension(self):
        """
        高级条件补全维度
        """
        if not hasattr(self, "agg_dimension"):
            return

        has_advance_method = False
        dimensions = set()
        for condition in self.agg_condition:
            if condition["method"] in AdvanceConditionMethod:
                has_advance_method = True
            dimensions.add(condition["key"])

        if has_advance_method:
            self.agg_dimension = list(set(self.agg_dimension) | dimensions)

    def _clean_empty_dimension(self):
        """
        清理空维度
        """
        if not hasattr(self, "agg_dimension"):
            return

        self.agg_dimension = [dimension for dimension in self.agg_dimension if dimension]


class Item(AbstractConfig):
    """
    监控项配置
    """

    class Serializer(serializers.Serializer):
        id = serializers.IntegerField(default=0)
        name = serializers.CharField()
        expression = serializers.CharField(allow_blank=True, default="")
        origin_sql = serializers.CharField(allow_blank=True, default="")
        target = serializers.ListField(allow_empty=True)
        no_data_config = serializers.DictField()

        query_configs = serializers.ListField()
        algorithms = Algorithm.Serializer(many=True)

    def __init__(
        self,
        strategy_id: int,
        name: str,
        no_data_config: Dict,
        target: List = None,
        expression: str = "",
        origin_sql: str = "",
        id: int = 0,
        query_configs: List[Dict] = None,
        algorithms: List[Dict] = None,
        **kwargs,
    ):
        self.name = name
        self.no_data_config = no_data_config
        self.target: List[List[Dict]] = target or [[]]
        self.expression = expression
        self.origin_sql = origin_sql
        self.query_configs: List[QueryConfig] = [QueryConfig(strategy_id, id, **c) for c in query_configs or []]
        self.algorithms: List[Algorithm] = [Algorithm(strategy_id, id, **c) for c in algorithms or []]
        self.strategy_id = strategy_id
        self.id = id

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        for obj in chain(self.query_configs, self.algorithms):
            obj.item_id = value

    @property
    def strategy_id(self):
        return self._strategy_id

    @strategy_id.setter
    def strategy_id(self, value):
        self._strategy_id = value
        for obj in chain(self.query_configs, self.algorithms):
            obj.strategy_id = value

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "no_data_config": self.no_data_config,
            "target": self.target,
            "expression": self.expression,
            "origin_sql": self.origin_sql,
            "query_configs": [query_config.to_dict() for query_config in self.query_configs],
            "algorithms": [algorithm.to_dict() for algorithm in self.algorithms],
        }

    @classmethod
    def delete_useless(cls, useless_item_ids: List[int]):
        """
        删除策略下多余的Item记录
        """
        AlgorithmModel.objects.filter(item_id__in=useless_item_ids).delete()
        QueryConfigModel.objects.filter(item_id__in=useless_item_ids).delete()

    def _create(self):
        data = self.to_dict()
        data.pop("id", None)
        data.pop("query_configs", None)
        data.pop("algorithms", None)
        item = ItemModel.objects.create(strategy_id=self.strategy_id, **data)
        self.id = item.id
        return item

    def save(self):
        try:
            if self.id > 0:
                item: ItemModel = ItemModel.objects.get(id=self.id, strategy_id=self.strategy_id)
                item.name = self.name
                item.no_data_config = self.no_data_config
                item.target = self.target
                item.expression = self.expression
                item.origin_sql = self.origin_sql
                item.save()
            else:
                item = self._create()
        except ItemModel.DoesNotExist:
            item = self._create()

        # 复用旧的记录
        model_mapping: Dict[Type[Model], List[AbstractConfig]] = defaultdict(list)
        model_mapping[QueryConfigModel] = self.query_configs
        model_mapping[AlgorithmModel] = self.algorithms

        for model, configs in model_mapping.items():
            objs = model.objects.filter(strategy_id=self.strategy_id, item_id=self.id).only("id")
            self.reuse_exists_records(model, objs, configs)

        self._supplement_instance_target_dimension()

        # 保存子配置
        for obj in chain(self.algorithms, self.query_configs):
            obj.save()

        item.save()

    @classmethod
    def from_models(
        cls,
        items: List["ItemModel"],
        algorithms: Dict[int, List[AlgorithmModel]],
        query_configs: Dict[int, List[QueryConfigModel]],
    ) -> List["Item"]:
        """
        数据模型转换为监控项对象
        """
        records = []
        for item in items:
            record = Item(
                id=item.id,
                strategy_id=item.strategy_id,
                name=item.name,
                expression=item.expression,
                origin_sql=item.origin_sql,
                no_data_config=item.no_data_config,
                target=item.target,
            )
            record.algorithms = Algorithm.from_models(algorithms[item.id])
            record.query_configs = QueryConfig.from_models(query_configs[item.id])
            records.append(record)

        return records

    def _supplement_instance_target_dimension(self):
        """
        静态目标补全静态维度
        """
        if not self.target or not self.target[0]:
            return

        target = self.target[0][0]
        if target["field"] not in [TargetFieldType.host_target_ip, TargetFieldType.host_ip]:
            return

        for query_config in self.query_configs:
            if (
                query_config.data_source_label != DataSourceLabel.BK_MONITOR_COLLECTOR
                or query_config.data_type_label != DataTypeLabel.TIME_SERIES
            ):
                continue

            query_config.agg_dimension = list(set(query_config.agg_dimension) | {"bk_target_ip", "bk_target_cloud_id"})


class Strategy(AbstractConfig):
    """
    策略 数据结构
    """

    version = "v2"

    ExtendFields = [
        "index_set_id",
        "time_field",
        "values",
        "custom_event_name",
        "origin_config",
        "intelligent_detect",
    ]

    class Serializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        name = serializers.CharField()
        source = serializers.CharField()
        scenario = serializers.CharField()

        items = Item.Serializer(many=True)
        actions = Action.Serializer(many=True)
        detect_configs = Detect.Serializer(many=True)

    def __init__(
        self,
        bk_biz_id: int,
        name: str,
        scenario: str,
        source: str = settings.APP_CODE,
        type: str = StrategyModel.StrategyType.Monitor,
        id: int = 0,
        items: List[Dict] = None,
        actions: List[Dict] = None,
        detects: List[Dict] = None,
        is_enabled: bool = True,
        update_user: str = "",
        update_time: datetime = None,
        create_user: str = "",
        create_time: datetime = None,
        **kwargs,
    ):
        """
        :param id: 策略ID
        :param name: 策略名称
        :param source: 来源应用
        :param scenario: 监控对象类型
        """
        self.bk_biz_id = bk_biz_id
        self.name = name
        self.source = source
        self.scenario = scenario
        self.type = type
        self.items: List[Item] = [Item(id, **item) for item in items or []]
        self.detects: List[Detect] = [Detect(id, **detect) for detect in detects or []]
        self.actions: List[Action] = [Action(id, **action) for action in actions or []]
        self.is_enabled = is_enabled
        self.id = id
        self.update_user = update_user
        self.update_time = update_time or datetime.now()
        self.create_user = create_user
        self.create_time = create_time or datetime.now()

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        for obj in chain(self.actions, self.items, self.detects):
            obj.strategy_id = value

    def to_dict(self) -> Dict:
        """
        转换为JSON字典
        """
        return {
            "id": self.id,
            "bk_biz_id": self.bk_biz_id,
            "name": self.name,
            "source": self.source,
            "scenario": self.scenario,
            "type": self.type,
            "items": [item.to_dict() for item in self.items],
            "detects": [detect.to_dict() for detect in self.detects],
            "actions": [action.to_dict() for action in self.actions],
            "is_enabled": self.is_enabled,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S%z"),
            "update_user": self.update_user,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S%z"),
            "create_user": self.create_user,
        }

    @classmethod
    def fill_notice_group(cls, configs: List[Dict]):
        """
        补充通知组配置详情
        """
        action_ids = []
        notice_group_ids = set()
        for config in configs:
            for action in config.get("action_list") or config["actions"]:
                action_ids.append(action["id"])
                notice_group_ids.update(action["notice_group_list"])

        notice_action_id_to_group_id = {}
        for notice_relation in ActionNoticeMapping.objects.filter(action_id__in=action_ids).values(
            "action_id",
            "notice_group_id",
        ):
            if notice_relation["action_id"] in notice_action_id_to_group_id:
                notice_action_id_to_group_id[notice_relation["action_id"]].append(notice_relation["notice_group_id"])
            else:
                notice_action_id_to_group_id[notice_relation["action_id"]] = [notice_relation["notice_group_id"]]

        notice_groups = defaultdict(list)
        for notice_group in NoticeGroup.objects.filter(id__in=notice_group_ids).values(
            "notice_receiver",
            "name",
            "notice_way",
            "message",
            "id",
            "create_time",
            "update_time",
        ):
            notice_group["notice_group_id"] = notice_group["id"]
            notice_group["notice_group_name"] = notice_group["name"]
            notice_group["notice_receiver"] = [
                {"type": receiver.split("#")[0], "id": receiver.split("#")[-1]}
                for receiver in notice_group["notice_receiver"]
            ]
            for action_id, notice_group_id_list in list(notice_action_id_to_group_id.items()):
                if notice_group["id"] in notice_group_id_list:
                    notice_groups[action_id].append(notice_group)

        for config in configs:
            for action_config in config.get("action_list") or config["actions"]:
                action_config["notice_group_list"] = notice_groups.get(action_config["id"], [])

    def to_dict_v1(self, config_type: str = "frontend"):
        """
        转换为旧版策略JSON字典
        """
        item_list = []
        for item in self.items:
            query_config = item.query_configs[0].to_dict()

            if (
                item.query_configs[0].data_source_label == DataSourceLabel.BK_LOG_SEARCH
                and item.query_configs[0].data_type_label == DataTypeLabel.LOG
            ):
                query_config["keywords_query_string"] = query_config["query_string"]
                del query_config["query_string"]
                query_config["agg_method"] = "COUNT"

            item_config = {
                "id": item.id,
                "item_id": item.id,
                "name": item.name,
                "item_name": item.name,
                "strategy_id": self.id,
                "update_time": self.update_time,
                "create_time": self.create_time,
                "metric_id": item.query_configs[0].metric_id,
                "no_data_config": item.no_data_config,
                "target": item.target,
                "rt_query_config_id": query_config["id"],
                "data_source_label": query_config.pop("data_source_label"),
                "data_type_label": query_config.pop("data_type_label"),
                "algorithm_list": [
                    {
                        "id": algorithm.id,
                        "algorithm_id": algorithm.id,
                        "algorithm_type": algorithm.type,
                        "algorithm_unit": algorithm.unit_prefix,
                        "algorithm_config": algorithm.config,
                        "trigger_config": self.detects[0].trigger_config,
                        "recovery_config": self.detects[0].recovery_config,
                        "level": algorithm.level,
                    }
                    for algorithm in item.algorithms
                ],
            }

            # 查询配置
            rt_query_config = {
                "unit_conversion": 1,
                "extend_fields": {},
            }
            for field, value in query_config.items():
                if field in self.ExtendFields:
                    rt_query_config["extend_fields"][field] = value
                else:
                    rt_query_config[field] = value

            # frontend和backend两种格式
            if config_type == "frontend":
                rt_query_config.pop("id", None)
                item_config.update(rt_query_config)
            else:
                rt_query_config["rt_query_config_id"] = query_config["id"]
                item_config["rt_query_config"] = rt_query_config

            item_list.append(item_config)

        result = {
            "id": self.id,
            "strategy_id": self.id,
            "name": self.name,
            "strategy_name": self.name,
            "bk_biz_id": self.bk_biz_id,
            "scenario": self.scenario,
            "is_enabled": self.is_enabled,
            "update_time": self.update_time,
            "update_user": self.update_user,
            "create_time": self.create_time,
            "create_user": self.create_user,
            "action_list": [
                {
                    "id": action.id,
                    "action_id": action.id,
                    "config": action.config,
                    "action_type": action.type,
                    "notice_template": action.notice_template,
                    "notice_group_list": action.notice_group_ids,
                }
                for action in self.actions
            ],
            "item_list": item_list,
        }

        for item in result["item_list"]:
            item.pop("alias", None)
        return result

    def convert(self):
        """
        特殊逻辑转换
        """
        from bkmonitor.strategy.convert import Convertors

        for convertor in Convertors:
            convertor.convert(self)

    def restore(self):
        """
        特殊逻辑重置
        """
        from bkmonitor.strategy.convert import Convertors

        for convertor in Convertors:
            convertor.restore(self)

    @classmethod
    def from_dict_v1(cls, config: Dict, config_type="frontend") -> "Strategy":
        """
        由旧策略配置JSON字典生成对象
        """
        config = copy.deepcopy(config)
        item_list = config.pop("item_list")
        action_list = config.pop("action_list")
        algorithm_list = item_list[0].pop("algorithm_list")

        levels = set()
        item: Dict = item_list[0]

        # 展开rt_query_config
        if "rt_query_config" in item:
            item["rt_query_config"].pop("id", None)
            item.update(item.pop("rt_query_config"))

        # 系统事件指标提取
        if (
            item["data_source_label"] == DataSourceLabel.BK_MONITOR_COLLECTOR
            and item["data_type_label"] == DataTypeLabel.EVENT
        ):
            item["result_table_id"] = SYSTEM_EVENT_RT_TABLE_ID
            item["metric_field"] = item["metric_id"].split(".")[-1]

        # 算法字段名转换
        algorithm_field_mapping = {
            "algorithm_unit": "unit_prefix",
            "algorithm_type": "type",
            "algorithm_config": "config",
        }
        for algorithm in algorithm_list:
            for field in algorithm_field_mapping:
                algorithm[algorithm_field_mapping[field]] = algorithm.get(field, "")
            levels.add(int(algorithm["level"]))

        # 动作配置字段转换
        action_field_mapping = {
            "action_type": "type",
            "notice_group_list": "notice_group_ids",
        }
        for action in action_list:
            for field in action_field_mapping:
                action[action_field_mapping[field]] = action[field]

        # 日志平台查询参数转换
        if "keywords_query_string" in item:
            item["query_string"] = item["keywords_query_string"]

        return Strategy(
            **{
                "type": "monitor",
                **config,
                "detects": [
                    {
                        "level": level,
                        "trigger_config": algorithm_list[0]["trigger_config"],
                        "recovery_config": algorithm_list[0]["recovery_config"],
                    }
                    for level in levels
                ],
                "items": [
                    {
                        "algorithms": algorithm_list,
                        "query_configs": [{"alias": "a", **item, **item.get("extend_fields", {})}],
                        **item,
                    }
                ],
                "actions": action_list,
            }
        )

    def _create(self):
        strategy = StrategyModel.objects.create(
            name=self.name,
            scenario=self.scenario,
            source=self.source,
            bk_biz_id=self.bk_biz_id,
            type=self.type,
            is_enabled=self.is_enabled,
            create_user=self._get_username(),
            update_user=self._get_username(),
        )
        self.id = strategy.id

    @transaction.atomic
    def save(self, rollback=False):
        """
        保存策略配置
        """

        if not rollback:
            history = StrategyHistoryModel.objects.create(
                create_user=self._get_username(),
                strategy_id=self.id,
                operate="create" if self.id == 0 else "update",
                content=self.to_dict(),
            )
        else:
            history = None

        old_strategy = None
        try:
            if self.id > 0:
                strategy = StrategyModel.objects.get(id=self.id, bk_biz_id=self.bk_biz_id)

                # 记录原始配置
                old_strategy = Strategy.from_models([strategy])[0]

                strategy.name = self.name
                strategy.scenario = self.scenario
                strategy.source = self.source
                strategy.type = self.type
                strategy.is_enabled = self.is_enabled
                strategy.update_user = self._get_username()
                strategy.save()
            else:
                self._create()

            # 复用当前存在的记录
            model_mapping = {
                ItemModel: self.items,
                ActionModel: self.actions,
                DetectModel: self.detects,
            }
            for model, configs in model_mapping.items():
                objs = model.objects.filter(strategy_id=self.id).only("id")
                self.reuse_exists_records(model, objs, configs)

            # 保存子配置
            for obj in chain(self.items, self.actions, self.detects):
                obj.save()

            if history and history.strategy_id == 0:
                history.strategy_id = self.id
                history.save()
        except StrategyModel.DoesNotExist:
            if history:
                history.message = f"策略({self.id})不存在"
                history.save()
            raise StrategyNotExist()
        except Exception as e:
            # 回滚失败直接报错
            if rollback:
                raise e

            # 清空或回滚配置
            if history.operate == "create":
                self.delete()
            elif old_strategy:
                try:
                    old_strategy.save(rollback=True)
                except Exception as rollback_exception:
                    logger.error(f"策略({self.id})回滚失败")
                    logger.exception(rollback_exception)

            # 记录错误信息
            history.message = traceback.format_exc()
            history.save()
            raise e

        history.status = True
        history.save()

    def delete(self):
        if id == 0:
            return

        StrategyModel.objects.filter(id=self.id).delete()
        actions = ActionModel.objects.filter(strategy_id=self.id)
        action_ids = [action.id for action in actions]
        ActionNoticeMapping.objects.filter(action_id__in=action_ids).delete()
        NoticeTemplate.objects.filter(action_id__in=action_ids).delete()
        actions.delete()

        DetectModel.objects.filter(strategy_id=self.id).delete()
        ItemModel.objects.filter(strategy_id=self.id).delete()
        AlgorithmModel.objects.filter(strategy_id=self.id).delete()
        QueryConfigModel.objects.filter(strategy_id=self.id).delete()

    @classmethod
    def delete_by_strategy_ids(cls, strategy_ids: List[int]):
        """
        批量删除策略
        """
        histories = []
        for strategy_id in strategy_ids:
            histories.append(
                StrategyHistoryModel(
                    create_user=cls._get_username(),
                    strategy_id=strategy_id,
                    operate="delete",
                )
            )
        StrategyHistoryModel.objects.bulk_create(histories, batch_size=100)

        StrategyModel.objects.filter(id__in=strategy_ids).delete()
        actions = ActionModel.objects.filter(strategy_id__in=strategy_ids)
        action_ids = [action.id for action in actions]
        ActionNoticeMapping.objects.filter(action_id__in=action_ids).delete()
        NoticeTemplate.objects.filter(action_id__in=action_ids).delete()
        actions.delete()

        DetectModel.objects.filter(strategy_id__in=strategy_ids).delete()
        ItemModel.objects.filter(strategy_id__in=strategy_ids).delete()
        AlgorithmModel.objects.filter(strategy_id__in=strategy_ids).delete()
        QueryConfigModel.objects.filter(strategy_id__in=strategy_ids).delete()

    @classmethod
    def from_models(cls, strategies: Union[List[StrategyModel], QuerySet]) -> List["Strategy"]:
        """
        数据模型转换为策略对象
        """
        strategy_ids = [s.id for s in strategies]

        items: Dict[int, List[ItemModel]] = defaultdict(list)
        for item in ItemModel.objects.filter(strategy_id__in=strategy_ids):
            items[item.strategy_id].append(item)

        actions: Dict[int, List[ActionModel]] = defaultdict(list)
        for action in ActionModel.objects.filter(strategy_id__in=strategy_ids):
            actions[action.strategy_id].append(action)

        detects: Dict[int, List[DetectModel]] = defaultdict(list)
        for detect in DetectModel.objects.filter(strategy_id__in=strategy_ids):
            detects[detect.strategy_id].append(detect)

        algorithms: Dict[int, List[AlgorithmModel]] = defaultdict(list)
        for algorithm in AlgorithmModel.objects.filter(strategy_id__in=strategy_ids):
            algorithms[algorithm.item_id].append(algorithm)

        notice_templates: Dict[int, NoticeTemplate] = defaultdict(
            lambda: NoticeTemplate(anomaly_template="", recovery_template="")
        )
        action_ids = list(chain(*[[action.id for action in action_list] for action_list in actions.values()]))
        for notice_template in NoticeTemplate.objects.filter(action_id__in=action_ids):
            notice_templates[notice_template.action_id] = notice_template

        query_configs: Dict[int, List[QueryConfigModel]] = defaultdict(list)
        for query_config in QueryConfigModel.objects.filter(strategy_id__in=strategy_ids):
            query_configs[query_config.item_id].append(query_config)

        records = []
        for strategy in strategies:
            record = Strategy(
                bk_biz_id=strategy.bk_biz_id,
                id=strategy.id,
                name=strategy.name,
                scenario=strategy.scenario,
                is_enabled=strategy.is_enabled,
                source=strategy.source,
                type=strategy.type,
                update_time=strategy.update_time,
                update_user=strategy.update_user,
                create_user=strategy.create_user,
                create_time=strategy.create_time,
            )

            record.items = Item.from_models(items[strategy.id], algorithms, query_configs)
            record.actions = Action.from_models(actions[strategy.id], notice_templates)
            record.detects = Detect.from_models(detects[strategy.id])
            records.append(record)

        return records
