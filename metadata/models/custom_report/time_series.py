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
import logging

from django.db import models
from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from bkmonitor.utils import consul
from bkmonitor.utils.db.fields import JsonField
from metadata import config
from metadata.models.result_table import ResultTableField
from metadata.models.storage import ClusterInfo

from .base import CustomGroupBase

logger = logging.getLogger("metadata")


class TimeSeriesGroup(CustomGroupBase):
    time_series_group_id = models.AutoField(verbose_name=_("分组ID"), primary_key=True)
    time_series_group_name = models.CharField(verbose_name=_("自定义时序分组名"), max_length=255)

    GROUP_ID_FIELD = "time_series_group_id"
    GROUP_NAME_FIELD = "time_series_group_name"

    # 默认存储INFLUXDB
    DEFAULT_STORAGE = ClusterInfo.TYPE_INFLUXDB

    # 默认INFLUXDB存储配置
    DEFAULT_STORAGE_CONFIG = {"use_default_rp": True}

    # Event字段配置
    STORAGE_EVENT_OPTION = {}

    # target字段配置
    STORAGE_TARGET_OPTION = {}

    # dimension字段配置
    STORAGE_DIMENSION_OPTION = {}

    # dimension字段配置
    STORAGE_EVENT_NAME_OPTION = {}

    STORAGE_FIELD_LIST = [
        {
            "field_name": "target",
            "field_type": ResultTableField.FIELD_TYPE_STRING,
            "tag": ResultTableField.FIELD_TAG_DIMENSION,
            "option": STORAGE_TARGET_OPTION,
            "is_config_by_user": True,
        }
    ]

    @staticmethod
    def make_table_id(bk_biz_id, bk_data_id):
        if str(bk_biz_id) != "0":
            return "{}_bkmonitor_time_series_{}.base".format(bk_biz_id, bk_data_id)

        return "bkmonitor_time_series_{}.base".format(bk_data_id)

    @atomic(config.DATABASE_CONNECTION_NAME)
    def update_metrics(self, metric_info):
        TimeSeriesMetric.update_metrics(self.time_series_group_id, metric_info)
        tag_set = set()

        for item in metric_info:
            field_name = item["field_name"]
            tag_list = item["tag_list"]

            ResultTableField.objects.get_or_create(
                table_id=self.table_id,
                field_name=field_name,
                tag=ResultTableField.FIELD_TAG_METRIC,
                defaults={
                    "field_type": ResultTableField.FIELD_TYPE_FLOAT,
                    "creator": "system",
                    "last_modify_user": "system",
                    "default_value": 0,
                    "is_config_by_user": True,
                },
            )
            logger.info(f"table->[{self.table_id}] now make sure field->[{field_name}] metric is exists.")
            # 先遍历所有的指标维度
            tag_set = tag_set.union(tag_list)

        # 然后统一创建维度字段，防止有重复的DB请求
        for tag in tag_set:
            ResultTableField.objects.get_or_create(
                table_id=self.table_id,
                field_name=tag,
                tag=ResultTableField.FIELD_TAG_DIMENSION,
                defaults={
                    "field_type": ResultTableField.FIELD_TYPE_STRING,
                    "creator": "system",
                    "last_modify_user": "system",
                    "default_value": "",
                    "is_config_by_user": True,
                },
            )
            logger.info(f"table->[{self.table_id}] now make sure field->[{field_name}] dimension is exists.")

        logger.info(f"table->[{self.table_id}] now process metrics done.")

    @property
    def datasource_options(self):
        return [
            {"name": "metrics_report_path", "value": self.metric_consul_path},
            {"name": "disable_metric_cutter", "value": "true"},
        ]

    @property
    def metric_consul_path(self):
        return "{}/influxdb_metrics/{}/time_series_metric".format(config.CONSUL_PATH, self.bk_data_id)

    def update_time_series_metric_from_consul(self):
        """
        从consul中同步TS的指标和维度对应关系
        :return:
        """
        # 从Consul同步配置信息
        client = consul.BKConsul()
        # 一次性获取这个前缀下的所有配置信息，防止多次http请求的性能问题
        _, key_info_list = client.kv.get(key=self.metric_consul_path, recurse=True)

        if key_info_list is None:
            logger.info("no metrics found for {}->[{}]".format(self.__class__.__name__, self.time_series_group_id))
            return

        # 遍历加入到配置信息中
        metric_list = []
        for key_info in key_info_list:

            value = key_info["Value"]

            field_name = key_info["Key"].split("/")[-1]
            metric_list.append({"field_name": field_name, "tag_list": json.loads(value)})

        # save metrics
        self.update_metrics(metric_list)

    def remove_metrics(self):
        # 删除所有的metrics信息
        metrics_queryset = TimeSeriesMetric.objects.filter(group_id=self.time_series_group_id)
        logger.debug(
            "going to delete all metrics->[{}] for {}->[{}] deletion.".format(
                metrics_queryset.count(), self.__class__.__name__, self.time_series_group_id
            )
        )
        metrics_queryset.delete()
        logger.info("all metrics about {}->[{}] is deleted.".format(self.__class__.__name__, self.time_series_group_id))

    @classmethod
    @atomic(config.DATABASE_CONNECTION_NAME)
    def create_time_series_group(
        cls, bk_data_id, bk_biz_id, time_series_group_name, label, operator, metric_info_list=None, table_id=None
    ):
        """
        创建一个新的自定义分组记录
        :param bk_data_id: 数据源ID
        :param bk_biz_id: 业务ID
        :param time_series_group_name: 自定义时序组名称
        :param label: 标签，描述事件监控对象
        :param operator: 操作者
        :param metric_info_list: metric列表
        :param table_id: 需要制定的table_id，否则通过默认规则创建得到
        :return: group object
        """

        custom_group = super().create_custom_group(
            bk_data_id=bk_data_id,
            bk_biz_id=bk_biz_id,
            custom_group_name=time_series_group_name,
            label=label,
            operator=operator,
            metric_info_list=metric_info_list,
            table_id=table_id,
        )

        # 需要刷新一次外部依赖的consul，触发transfer更新
        from metadata.models import DataSource

        DataSource.objects.get(bk_data_id=bk_data_id).refresh_consul_config()

        return custom_group

    @atomic(config.DATABASE_CONNECTION_NAME)
    def modify_time_series_group(
        self, operator, time_series_group_name=None, label=None, is_enable=None, field_list=None
    ):
        """
        修改一个自定义时序组
        :param operator: 操作者
        :param time_series_group_name: 自定义时序组名
        :param label:  自定义时序组标签
        :param is_enable: 是否启用自定义时序组
        :param field_list: metric信息,
        :return: True or raise
        """
        return self.modify_custom_group(
            operator=operator,
            custom_group_name=time_series_group_name,
            label=label,
            is_enable=is_enable,
            metric_info_list=None,
            field_list=field_list,
        )

    @atomic(config.DATABASE_CONNECTION_NAME)
    def delete_time_series_group(self, operator):
        """
        删除一个指定的自定义时序组
        :param operator: 操作者
        :return: True or raise
        """
        return self.delete_custom_group(operator=operator)

    def to_json(self):
        return {
            "time_series_group_id": self.time_series_group_id,
            "time_series_group_name": self.time_series_group_name,
            "bk_data_id": self.bk_data_id,
            "bk_biz_id": self.bk_biz_id,
            "table_id": self.table_id,
            "label": self.label,
            "is_enable": self.is_enable,
            "creator": self.creator,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_modify_user": self.last_modify_user,
            "last_modify_time": self.last_modify_time.strftime("%Y-%m-%d %H:%M:%S"),
            "metric_info_list": self.get_metric_info_list(),
        }

    def to_json_self_only(self):
        return {
            "time_series_group_id": self.time_series_group_id,
            "time_series_group_name": self.time_series_group_name,
            "bk_data_id": self.bk_data_id,
            "bk_biz_id": self.bk_biz_id,
            "table_id": self.table_id,
            "label": self.label,
            "is_enable": self.is_enable,
            "creator": self.creator,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_modify_user": self.last_modify_user,
            "last_modify_time": self.last_modify_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_metric_info_list(self):
        metric_info_list = []

        orm_field_map = {}
        for orm_field in (
            ResultTableField.objects.filter(table_id=self.table_id).values(*TimeSeriesMetric.ORM_FIELD_NAMES).iterator()
        ):
            orm_field_map[orm_field["field_name"]] = orm_field

        for metric in TimeSeriesMetric.objects.filter(group_id=self.time_series_group_id).iterator():
            metric_info = metric.to_metric_info(field_map=orm_field_map)
            # 当一个指标可能某些原因被删除时，不必再追加到结果中
            if metric_info is None:
                continue

            metric_info_list.append(metric_info)

        return metric_info_list


class TimeSeriesMetric(models.Model):
    """自定义时序schema描述
    field: [tag1, tag2...]
    """

    TARGET_DIMENSION_NAME = "target"

    ORM_FIELD_NAMES = (
        "table_id",
        "field_name",
        "field_type",
        "unit",
        "tag",
        "description",
    )

    group_id = models.IntegerField(verbose_name=_("自定义时序所属分组ID"))

    field_id = models.AutoField(verbose_name=_("自定义时序字段ID"), primary_key=True)
    field_name = models.CharField(verbose_name=_("自定义时序字段名称"), max_length=255)
    tag_list = JsonField(verbose_name=_("Tag列表"), default=[])
    last_modify_time = models.DateTimeField(verbose_name=_("最后更新时间"), auto_now=True)

    class Meta:
        # 同一个事件分组下，不可以存在同样的事件名称
        unique_together = ("group_id", "field_name")
        verbose_name = _("自定义时序描述记录")
        verbose_name_plural = _("自定义时序描述记录表")

    @classmethod
    @atomic(config.DATABASE_CONNECTION_NAME)
    def update_metrics(cls, group_id, metric_info_list):
        """
        批量的修改/创建某个自定义时序分组下的metric信息
        :param group_id: 自定义分组ID
        :param metric_info_list: 具体自定义时序内容信息，[{
            "field_name": "core_file",
            "tag_list": ["module", "set", "path"]
        }, {
            "field_name": "disk_full",
            "tag_list": ["module", "set", "partition"]
        }]
        :return: True or raise
        """
        # 0. 判断是否真的存在某个group_id
        if not TimeSeriesGroup.objects.filter(time_series_group_id=group_id).exists():
            logger.info("time_series_group_id->[{}] not exists, nothing will do.".format(group_id))
            raise ValueError(_("自定义时序组ID[{}]不存在，请确认后重试").format(group_id))

        # 1. 遍历所有的事件进行处理，判断是否存在custom_event_id
        for metric_info in metric_info_list:

            # 如果存在这个custom_event_id，那么需要进行修改
            try:
                field_name = metric_info["field_name"]
                tag_list = metric_info["tag_list"]
            except KeyError as key:
                logger.error("metric_info got bad metric->[{}] which has no key->[{}]".format(metric_info, key))
                raise ValueError(_("自定义时序列表配置有误，请确认后重试"))

            # 必然会追加target这个维度内容
            tag_list.append(cls.TARGET_DIMENSION_NAME)

            try:
                # 判断是否已经存在这个事件
                metric_obj = cls.objects.get(field_name=field_name, group_id=group_id)
            except cls.DoesNotExist:
                # 如果不存在事件，创建一个新的时间
                metric_obj = cls.objects.create(field_name=field_name, group_id=group_id)
                logger.info("new metric_obj->[{}] is create for group_id->[{}].".format(metric_obj, group_id))

            # 修改已有的事件配置, 但是考虑需要保持已有的维度，需要将新旧两个维度merge
            old_tag_set = set(metric_obj.tag_list)
            new_tag_set = set(tag_list)
            metric_obj.tag_list = list(old_tag_set.union(new_tag_set))
            metric_obj.save()

            # 后续可以在此处追加其他修改内容
            logger.info(
                "time_series_group_id->[{}] has update field_name->[{}] all tags->[{}]".format(
                    group_id, metric_obj.field_name, metric_obj.tag_list
                )
            )

        return True

    @cached_property
    def group(self):
        """
        对象获得group的缓存
        :return:
        """
        return TimeSeriesGroup.objects.get(time_series_group_id=self.group_id)

    def to_json(self):

        return {"field_id": self.field_id, "field_name": self.field_name, "tag_list": self.tag_list}

    def to_metric_info(self, field_map=None):
        """
         {
            "field_name": "mem_usage",
            "description": "mem_usage_2",
            "unit": "M",
            "type": "double",
            "tag_list": [
                {
                    "field_name": "test_name",
                    "description": "test_name_2",
                    "unit": "M",
                    "type": "double",
                }
            ]
        }
        """
        group = self.group
        orm_field_map = field_map or {}
        if not orm_field_map:
            for orm_field in (
                ResultTableField.objects.filter(table_id=group.table_id).values(*self.ORM_FIELD_NAMES).iterator()
            ):
                orm_field_map[orm_field["field_name"]] = orm_field

        result = {
            "field_name": self.field_name,
            "metric_display_name": "",
            "unit": "",
            "type": "double",
            "tag_list": [],
        }

        # 填充指标信息
        if self.field_name not in orm_field_map:
            logger.warning(
                f"metric->[{self.field_name}] is not exists in table->[{group.table_id}] "
                f"not metrics info will return."
            )
            return None

        orm_field = orm_field_map[self.field_name]
        result["description"] = orm_field["description"]
        result["unit"] = orm_field["unit"]
        result["type"] = orm_field["field_type"]

        # 遍历维度填充维度信息
        for tag in self.tag_list:
            item = {"field_name": tag, "description": ""}
            # 如果维度不存在了，则表示字段可能已经被删除了
            if tag in orm_field_map:
                orm_field = orm_field_map[tag]
                item["description"] = orm_field["description"]
                item["unit"] = orm_field["unit"]
                item["type"] = orm_field["field_type"]

            result["tag_list"].append(item)

        return result
