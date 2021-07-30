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


import copy
import json
import logging
from collections import defaultdict
from functools import reduce
from typing import List, Dict

from django.conf import settings
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy
from django_mysql.models.functions import JSONExtract
from rest_framework import serializers

from bkmonitor.data_source import load_data_source
from constants.view import ViewType
from core.drf_resource.base import Resource
from bkmonitor.models import QueryConfigModel
from core.drf_resource import resource
from bkmonitor.utils.request import get_request_username
from bkmonitor.utils.time_tools import date_convert, parse_time_range
from constants.data_source import DataSourceLabel, DataTypeLabel
from core.drf_resource import api
from core.errors.api import BKAPIError
from core.errors.custom_report import CustomEventNameValidationError, CustomTSNameValidationError
from monitor_web.constants import ETL_CONFIG, EVENT_TYPE
from monitor_web.custom_report.serializers import (
    CustomEventGroupDetailSerializer,
    CustomEventGroupSerializer,
    CustomTSTableSerializer,
    EventInfoSerializer,
    MetricListSerializer,
)
from monitor_web.data_explorer.resources import GetSceneViewConfig
from monitor_web.models.custom_report import CustomEventGroup, CustomEventItem, CustomTSItem, CustomTSTable
from monitor_web.tasks import append_event_metric_list_cache, append_custom_ts_metric_list_cache

logger = logging.getLogger(__name__)


def get_label_display_dict():
    label_display_dict = {}
    try:
        labels = resource.commons.get_label()
        for label in labels:
            for child in label["children"]:
                label_display_dict[child["id"]] = [label["name"], child["name"]]
    except Exception:
        pass
    return label_display_dict


class ValidateCustomEventGroupName(Resource):
    """
    校验名称是否合法
    """

    class RequestSerializer(serializers.Serializer):
        bk_event_group_id = serializers.IntegerField(required=False)
        name = serializers.CharField(required=True)

    def perform_request(self, validated_request_data):
        try:
            event_groups = api.metadata.query_event_group(event_group_name=validated_request_data["name"])
            if validated_request_data.get("bk_event_group_id"):
                event_groups = [
                    g for g in event_groups if g["bk_event_group_id"] != validated_request_data["bk_event_group_id"]
                ]
            is_exist = bool(event_groups)
        except Exception:
            # 如果接口调用失败，则使用 SaaS 配置，作为补偿机制
            queryset = CustomEventGroup.objects.filter(name=validated_request_data["name"])
            if validated_request_data.get("bk_event_group_id"):
                queryset = queryset.exclude(bk_event_group_id=validated_request_data["bk_event_group_id"])
            is_exist = queryset.exists()
        if is_exist:
            raise CustomEventNameValidationError(msg=_("事件分组名称已存在"))
        return True


class ValidateCustomTsGroupName(Resource):
    """
    校验名称是否合法
    """

    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=False)
        name = serializers.CharField(required=True)

    def perform_request(self, validated_request_data):
        try:
            custom_ts_groups = api.metadata.query_time_series_group(
                time_series_group_name=validated_request_data["name"]
            )
            if validated_request_data.get("time_series_group_id"):
                custom_ts_groups = [
                    g
                    for g in custom_ts_groups
                    if g["time_series_group_id"] != validated_request_data["time_series_group_id"]
                ]
            is_exist = bool(custom_ts_groups)
        except Exception:
            queryset = CustomTSTable.objects.filter(name=validated_request_data["name"])
            if validated_request_data.get("time_series_group_id"):
                queryset = queryset.exclude(time_series_group_id=validated_request_data["time_series_group_id"])
            is_exist = queryset.exists()
        if is_exist:
            raise CustomTSNameValidationError(msg=_("时序分组名称已存在"))
        return True


class QueryCustomEventGroup(Resource):
    """
    自定义事件列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), default=0)
        search_key = serializers.CharField(label=_lazy("名称"), required=False)
        page_size = serializers.IntegerField(default=10, label=_lazy("获取的条数"))
        page = serializers.IntegerField(default=1, label=_lazy("页数"))

    def get_strategy_count_for_each_group(self, table_ids):
        """
        获取事件分组绑定的策略数
        """
        if not table_ids:
            return {}

        query_configs = (
            QueryConfigModel.objects.annotate(result_table_id=JSONExtract("config", "$.result_table_id"))
            .filter(
                reduce(lambda x, y: x | y, (Q(result_table_id=table_id) for table_id in table_ids)),
                data_source_label=DataSourceLabel.CUSTOM,
                data_type_label=DataTypeLabel.EVENT,
            )
            .values("result_table_id", "strategy_id")
        )

        table_id_strategy_mapping = defaultdict(set)
        for query_config in query_configs:
            table_id_strategy_mapping[query_config["result_table_id"]].add(query_config["strategy_id"])

        return {key: len(value) for key, value in table_id_strategy_mapping.items()}

    def perform_request(self, validated_request_data):
        queryset = CustomEventGroup.objects.filter(type=EVENT_TYPE.CUSTOM_EVENT).order_by("-update_time")
        if validated_request_data.get("bk_biz_id"):
            queryset = queryset.filter(bk_biz_id=validated_request_data["bk_biz_id"])
        if validated_request_data.get("search_key"):
            search_key = validated_request_data["search_key"]
            conditions = models.Q(name__contains=search_key)
            try:
                search_key = int(search_key)
            except ValueError:
                pass
            else:
                conditions = conditions | models.Q(pk=search_key)
            queryset = queryset.filter(conditions)
        paginator = Paginator(queryset, validated_request_data["page_size"])
        serializer = CustomEventGroupSerializer(paginator.page(validated_request_data["page"]), many=True)
        groups = serializer.data

        table_ids = [group["table_id"] for group in groups]
        strategy_count_mapping = self.get_strategy_count_for_each_group(table_ids)

        label_display_dict = get_label_display_dict()
        for group in groups:
            group["scenario_display"] = label_display_dict.get(group["scenario"], [group["scenario"]])
            group["related_strategy_count"] = strategy_count_mapping.get(group["table_id"], 0)
        return {
            "list": groups,
            "total": queryset.count(),
        }


class GetCustomEventGroup(Resource):
    """
    获取单个自定义事件详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_event_group_id = serializers.IntegerField(required=True, label=_lazy("事件分组ID"))
        time_range = serializers.CharField(required=True, label=_("时间范围"))

    def perform_request(self, validated_request_data):
        event_group_id = validated_request_data["bk_event_group_id"]
        append_event_metric_list_cache(event_group_id)
        config = CustomEventGroup.objects.prefetch_related("event_info_list").get(pk=event_group_id)
        serializer = CustomEventGroupDetailSerializer(config)
        data = serializer.data
        event_info_list = api.metadata.get_event_group.request.refresh(event_group_id=event_group_id)
        data["event_info_list"] = list()

        #  获得每个事件的关联策略ID
        related_strategies = {
            f"{event_info_list['event_group_id']}-{item['event_id']}": list(
                QueryConfigModel.objects.filter(
                    metric_id=f"custom.event.{event_info_list['bk_data_id']}.{item['event_id']}"
                ).values_list("strategy_id", flat=True)
            )
            for item in event_info_list["event_info_list"]
        }

        for item in event_info_list["event_info_list"]:
            event_info = {
                "custom_event_name": item["event_name"],
                "bk_event_group_id": event_info_list["event_group_id"],
                "custom_event_id": item["event_id"],
                "related_strategies": related_strategies.get(f"{event_info_list['event_group_id']}-{item['event_id']}"),
                "dimension_list": [{"dimension_name": dimension} for dimension in item["dimension_list"]],
            }
            data["event_info_list"].append(event_info)

        label_display_dict = get_label_display_dict()
        data["scenario_display"] = label_display_dict.get(data["scenario"], [data["scenario"]])
        data["access_token"] = self.get_token(data["bk_data_id"])
        for event in data["event_info_list"]:
            event.update(
                self.query_event_detail(
                    data["table_id"], event["custom_event_name"], validated_request_data["time_range"]
                )
            )

            if event["last_change_time"]:
                event["last_change_time"] = date_convert(int(event["last_change_time"]), "datetime")
        return data

    @staticmethod
    def get_token(bk_data_id):
        data_id_info = api.metadata.get_data_id({"bk_data_id": bk_data_id})
        return data_id_info["token"]

    @staticmethod
    def query_event_detail(result_table_id, custom_event_name, time_range):
        start, end = parse_time_range(time_range)
        time_field = "time"
        data_source = load_data_source(DataSourceLabel.CUSTOM, DataTypeLabel.EVENT)(
            table=result_table_id,
            custom_event_name=custom_event_name,
        )
        records, event_count = data_source.query_log(start * 1000, end * 1000)
        targets = data_source.query_dimensions(dimension_field="target", start_time=start * 1000, end_time=end * 1000)
        target_count = len(targets)
        last_change_time = ""
        last_event = {}
        if event_count > 0:
            last_event = records[0]
            last_change_time = date_convert(int(last_event[time_field]) / 1000, "datetime")
            last_event["timestamp"] = int(last_event.pop(time_field))
        return {
            "event_count": event_count,
            "target_count": target_count,
            "last_change_time": last_change_time,
            "last_event_content": last_event,
        }


class CreateCustomEventGroup(Resource):
    """
    创建自定义事件
    """

    CUSTOM_EVENT_DATA_NAME = "custom_event"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        name = serializers.CharField(required=True, max_length=128, label=_lazy("名称"))
        scenario = serializers.CharField(required=True, label=_lazy("对象"))
        event_info_list = EventInfoSerializer(required=False, many=True, allow_empty=True)

    def get_custom_event_data_id(self, bk_biz_id, operator, event_group_name):
        data_name = "{}_{}_{}".format(self.CUSTOM_EVENT_DATA_NAME, event_group_name, bk_biz_id)
        try:
            data_id_info = api.metadata.get_data_id({"data_name": data_name})
        except BKAPIError:
            param = {
                "data_name": data_name,
                "etl_config": ETL_CONFIG.CUSTOM_EVENT,
                "operator": operator,
                "data_description": data_name,
                "type_label": DataTypeLabel.EVENT,
                "source_label": DataSourceLabel.CUSTOM,
                "option": {"inject_local_time": True},
            }
            data_id_info = api.metadata.create_data_id(param)
        else:
            if not CustomEventGroup.objects.filter(
                bk_data_id=data_id_info["bk_data_id"], bk_event_group_id=-data_id_info["bk_data_id"]
            ):
                raise CustomEventNameValidationError(msg=_(f"数据源名称[{data_name}]已存在"))
        bk_data_id = data_id_info["bk_data_id"]
        return bk_data_id

    def perform_request(self, validated_request_data):
        operator = get_request_username()
        # 1. 查询或创建业务的 data_id
        bk_data_id = self.get_custom_event_data_id(
            validated_request_data["bk_biz_id"], operator, validated_request_data["name"]
        )

        # 2. 创建或查询数据记录
        group, is_created = CustomEventGroup.objects.get_or_create(bk_data_id=bk_data_id, bk_event_group_id=-bk_data_id)
        # 3. 调用接口创建 event_group
        params = {
            "operator": operator,
            "bk_data_id": bk_data_id,
            "bk_biz_id": validated_request_data["bk_biz_id"],
            "event_group_name": validated_request_data["name"],
            "label": validated_request_data["scenario"],
            "event_info_list": [],
        }
        group_info = api.metadata.create_event_group(params)

        # 4. 结果回写数据库
        with transaction.atomic():
            group.delete()
            group = CustomEventGroup.objects.create(
                bk_biz_id=group_info["bk_biz_id"],
                bk_event_group_id=group_info["event_group_id"],
                scenario=group_info["label"],
                name=group_info["event_group_name"],
                bk_data_id=group_info["bk_data_id"],
                table_id=group_info["table_id"],
            )

        return {"bk_event_group_id": group.bk_event_group_id}


class ModifyCustomEventGroup(Resource):
    """
    修改自定义事件
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        bk_event_group_id = serializers.IntegerField(required=True, label=_lazy("事件分组ID"))
        name = serializers.CharField(required=False, max_length=128, label=_lazy("名称"))
        scenario = serializers.CharField(required=False, label=_lazy("对象"))
        event_info_list = EventInfoSerializer(required=False, many=True, allow_empty=True)
        is_enable = serializers.BooleanField(required=False)

    @atomic()
    def perform_request(self, validated_request_data):
        operator = get_request_username()
        group = CustomEventGroup.objects.get(
            bk_biz_id=validated_request_data["bk_biz_id"], bk_event_group_id=validated_request_data["bk_event_group_id"]
        )
        # 1. 调用接口修改 event_group
        params = {
            "operator": operator,
            "event_group_id": validated_request_data["bk_event_group_id"],
            "event_group_name": validated_request_data.get("name"),
            "label": validated_request_data.get("scenario"),
            "is_enable": validated_request_data.get("is_enable"),
            "event_info_list": [],
        }
        params = {key: value for key, value in list(params.items()) if value is not None}
        group_info = api.metadata.modify_event_group(params)

        # 2. 结果回写数据库
        group.scenario = group_info["label"]
        group.name = group_info["event_group_name"]
        group.is_enable = group_info["is_enable"]
        group.save()
        return {"bk_event_group_id": group.bk_event_group_id}


class DeleteCustomEventGroup(Resource):
    """
    删除自定义事件
    """

    class RequestSerializer(serializers.Serializer):
        bk_event_group_id = serializers.IntegerField(required=True, label=_lazy("事件分组ID"))

    @atomic()
    def perform_request(self, validated_request_data):
        operator = get_request_username()
        group = CustomEventGroup.objects.get(bk_event_group_id=validated_request_data["bk_event_group_id"])
        # 1. 调用接口删除 event_group
        api.metadata.delete_event_group(event_group_id=group.bk_event_group_id, operator=operator)
        # 2. 结果回写数据库
        group.delete()
        CustomEventItem.objects.filter(bk_event_group_id=group.bk_event_group_id).delete()
        return {"bk_event_group_id": validated_request_data["bk_event_group_id"]}


class ProxyHostInfo(Resource):
    """
    Proxy主机信息
    """

    DEFAULT_PROXY_PORT = 10205

    def perform_request(self, validated_request_data):
        port = getattr(settings, "BK_MONITOR_PROXY_LISTEN_PORT", ProxyHostInfo.DEFAULT_PROXY_PORT)
        proxy_host_info = []
        try:
            bk_biz_id = validated_request_data["bk_biz_id"]
            if settings.BK_NODEMAN_VERSION == "2.0":
                proxy_hosts = api.node_man.get_proxies_by_biz(bk_biz_id=bk_biz_id)
            else:
                proxy_hosts = api.node_man.query_hosts(node_type="PROXY", bk_biz_id=bk_biz_id)
            for host in proxy_hosts:
                bk_cloud_id = int(host["bk_cloud_id"])
                ip = host.get("conn_ip") or host.get("inner_ip")
                proxy_host_info.append({"ip": ip, "bk_cloud_id": bk_cloud_id, "port": port})
        except Exception as e:
            logger.exception(e)

        default_cloud_display = settings.CUSTOM_REPORT_DEFAULT_PROXY_IP
        if settings.CUSTOM_REPORT_DEFAULT_PROXY_DOMAIN:
            default_cloud_display = settings.CUSTOM_REPORT_DEFAULT_PROXY_DOMAIN
        for proxy_ip in default_cloud_display:
            proxy_host_info.append({"ip": proxy_ip, "bk_cloud_id": 0, "port": port})
        return proxy_host_info


class CreateCustomTimeSeries(Resource):
    """
    创建自定义时序
    """

    CUSTOM_TS_NAME = "custom_time_series"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        name = serializers.CharField(required=True, max_length=128, label=_lazy("名称"))
        scenario = serializers.CharField(required=True, label=_lazy("对象"))
        table_id = serializers.CharField(required=False, label=_lazy("表名"), default="")
        metric_info_list = serializers.ListField(required=False, default=[], label=_lazy("预定义表结构"))

    def data_name(self, bk_biz_id, ts_name):
        return "{}_{}_{}".format(bk_biz_id, self.CUSTOM_TS_NAME, ts_name)

    def table_id(self, bk_biz_id, data_id):
        database_name = "{}_{}_{}".format(bk_biz_id, self.CUSTOM_TS_NAME, data_id)
        return "{}.{}".format(database_name, "base")

    @staticmethod
    def get_data_id(data_name, operator):
        try:
            api.metadata.get_data_id({"data_name": data_name})
        except BKAPIError:
            param = {
                "data_name": data_name,
                "etl_config": ETL_CONFIG.CUSTOM_TS,
                "operator": operator,
                "data_description": data_name,
                "type_label": DataTypeLabel.TIME_SERIES,
                "source_label": DataSourceLabel.CUSTOM,
                "option": {"inject_local_time": True},
            }
            data_id_info = api.metadata.create_data_id(param)
        else:
            raise CustomTSNameValidationError(msg=_(f"数据源名称[{data_name}]已存在"))
        bk_data_id = data_id_info["bk_data_id"]
        return bk_data_id

    @atomic()
    def perform_request(self, validated_request_data):
        operator = get_request_username() or settings.COMMON_USERNAME
        if validated_request_data["bk_biz_id"] == 0 and not validated_request_data["table_id"]:
            raise CustomTSNameValidationError(msg=_("全局自定义时序数据源需要制定table_id"))

        data_name = self.data_name(validated_request_data["bk_biz_id"], validated_request_data["name"])
        bk_data_id = self.get_data_id(data_name, operator)
        # 2. 调用接口创建 event_group
        params = {
            "operator": operator,
            "bk_data_id": bk_data_id,
            "bk_biz_id": validated_request_data["bk_biz_id"],
            "time_series_group_name": validated_request_data["name"],
            "label": validated_request_data["scenario"],
            "metric_info_list": validated_request_data["metric_info_list"],
        }
        if validated_request_data["table_id"]:
            params["table_id"] = validated_request_data["table_id"]
        group_info = api.metadata.create_time_series_group(params)

        CustomTSTable.objects.create(
            bk_biz_id=group_info["bk_biz_id"],
            time_series_group_id=group_info["time_series_group_id"],
            scenario=group_info["label"],
            name=group_info["time_series_group_name"],
            bk_data_id=group_info["bk_data_id"],
            table_id=group_info["table_id"],
        )
        return {"time_series_group_id": group_info["time_series_group_id"], "bk_data_id": group_info["bk_data_id"]}


class ModifyCustomTimeSeries(Resource):
    """
    修改自定义时序
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        time_series_group_id = serializers.IntegerField(required=True, label=_lazy("自定义时序ID"))
        name = serializers.CharField(required=False, max_length=128, label=_lazy("名称"))
        metric_json = MetricListSerializer(required=False, many=True, label=_("指标配置"), default=[])

    @atomic()
    def perform_request(self, validated_request_data):
        operator = get_request_username()
        table = CustomTSTable.objects.get(
            bk_biz_id=validated_request_data["bk_biz_id"],
            time_series_group_id=validated_request_data["time_series_group_id"],
        )
        fields = []
        metric_labels = {}
        for field in validated_request_data["metric_json"][0]["fields"]:
            fields.append(
                {
                    "field_name": field["name"],
                    "tag": field["monitor_type"],
                    "field_type": field["type"],
                    "description": field["description"],
                    "unit": field["unit"],
                }
            )
            if field["monitor_type"] == "metric":
                metric_labels[field["name"]] = field.get("label", "")

        # 更新metadata指标信息
        params = {
            "operator": operator,
            "time_series_group_id": table.time_series_group_id,
            "field_list": fields,
            "time_series_group_name": validated_request_data["name"],
            "label": table.scenario,
        }
        api.metadata.modify_time_series_group(params)
        table.name = validated_request_data["name"]
        table.save()

        # 更新指标分组标签
        CustomTSItem.objects.filter(table=table).exclude(metric_name__in=list(metric_labels.keys())).delete()
        for metric in CustomTSItem.objects.filter(table=table):
            label = metric_labels.pop(metric.metric_name, "")
            if metric.label == label:
                continue

            metric.label = label
            metric.save()

        CustomTSItem.objects.bulk_create(
            [CustomTSItem(table=table, metric_name=name, label=label) for name, label in metric_labels.items()],
            batch_size=200,
        )

        return resource.custom_report.custom_time_series_detail(time_series_group_id=table.time_series_group_id)


class DeleteCustomTimeSeries(Resource):
    """
    删除自定义时序
    """

    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=True, label=_lazy("自定义时序ID"))

    @atomic()
    def perform_request(self, validated_request_data):
        table = CustomTSTable.objects.get(time_series_group_id=validated_request_data["time_series_group_id"])
        operator = get_request_username()
        params = {"operator": operator, "time_series_group_id": table.time_series_group_id}
        api.metadata.delete_time_series_group(params)

        CustomTSItem.objects.filter(table=table).delete()
        table.delete()
        return {"time_series_group_id": validated_request_data["time_series_group_id"]}


class CustomTimeSeriesList(Resource):
    """
    自定义时序列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), default=0)
        search_key = serializers.CharField(label=_lazy("名称"), required=False)
        page_size = serializers.IntegerField(default=10, label=_lazy("获取的条数"))
        page = serializers.IntegerField(default=1, label=_lazy("页数"))

    @staticmethod
    def get_strategy_count(table_ids):
        """
        获取绑定的策略数
        """
        if not table_ids:
            return {}

        query_configs = (
            QueryConfigModel.objects.annotate(result_table_id=JSONExtract("config", "$.result_table_id"))
            .filter(
                reduce(lambda x, y: x | y, (Q(result_table_id=table_id) for table_id in table_ids)),
                data_source_label=DataSourceLabel.CUSTOM,
                data_type_label=DataTypeLabel.TIME_SERIES,
            )
            .values("result_table_id", "strategy_id")
        )

        table_id_strategy_mapping = defaultdict(set)
        for query_config in query_configs:
            table_id_strategy_mapping[query_config["result_table_id"]].add(query_config["strategy_id"])
        return {key: len(value) for key, value in table_id_strategy_mapping.items()}

    def perform_request(self, validated_request_data):
        queryset = CustomTSTable.objects.all().order_by("-update_time")
        if validated_request_data.get("bk_biz_id"):
            queryset = queryset.filter(bk_biz_id=validated_request_data["bk_biz_id"])
        if validated_request_data.get("search_key"):
            search_key = validated_request_data["search_key"]
            conditions = models.Q(name__contains=search_key)
            try:
                search_key = int(search_key)
            except ValueError:
                pass
            else:
                conditions = conditions | models.Q(pk=search_key)
            queryset = queryset.filter(conditions)
        paginator = Paginator(queryset, validated_request_data["page_size"])
        serializer = CustomTSTableSerializer(paginator.page(validated_request_data["page"]), many=True)
        tables = serializer.data

        table_ids = [table["table_id"] for table in tables]
        strategy_count_mapping = self.get_strategy_count(table_ids)

        label_display_dict = get_label_display_dict()
        for table in tables:
            table["scenario_display"] = label_display_dict.get(table["scenario"], [table["scenario"]])
            table["related_strategy_count"] = strategy_count_mapping.get(table["table_id"], 0)
        return {
            "list": tables,
            "total": queryset.count(),
        }


class CustomTimeSeriesDetail(Resource):
    """
    自定义时序详情
    """

    class RequestSerializer(serializers.Serializer):
        time_series_group_id = serializers.IntegerField(required=True, label=_lazy("自定义时序ID"))

    def perform_request(self, validated_request_data):
        config = CustomTSTable.objects.get(pk=validated_request_data["time_series_group_id"])
        serializer = CustomTSTableSerializer(config)
        data = serializer.data
        label_display_dict = get_label_display_dict()
        data["scenario_display"] = label_display_dict.get(data["scenario"], [data["scenario"]])
        data["access_token"] = config.token
        metrics = copy.deepcopy(config.get_metrics())
        data["metric_json"] = [{"fields": list(metrics.values())}]
        data["target"] = config.query_target()
        append_custom_ts_metric_list_cache.delay(validated_request_data["time_series_group_id"])
        return data


class GetCustomTimeSeriesLatestDataByFields(Resource):
    """
    查询自定义时序数据最新的一条数据
    """

    class RequestSerializer(serializers.Serializer):
        result_table_id = serializers.CharField(required=True, label=_lazy("结果表ID"))
        fields_list = serializers.ListField(required=True, label=_lazy("字段列表"), allow_empty=False)

    def perform_request(self, validated_request_data):
        result_table_id = validated_request_data["result_table_id"]
        fields_list = validated_request_data["fields_list"] or []
        fields_list = [str(i) for i in fields_list]

        result = {}
        raw_data = self.get_latest_data(table_id=result_table_id, fields_list=fields_list)
        result["fields_value"] = self.get_filed_value(raw_data, fields_list)
        result["last_time"] = self.last_time(raw_data)
        result["table_id"] = result_table_id
        return result

    @classmethod
    def get_latest_data(cls, table_id, fields_list):
        data_source = load_data_source(DataSourceLabel.CUSTOM, DataTypeLabel.TIME_SERIES)(
            table=table_id,
            metrics=[{"field": field} for field in fields_list],
            filter_dict={"time__gte": "5m"},
        )
        return data_source.query_data()

    @staticmethod
    def get_filed_value(raw_data, fields_list):
        field_map = {}
        for data in raw_data:
            for key, value in data.items():
                if key not in field_map and value is not None:
                    field_map[key] = value

        result = {}
        for field_name in fields_list:
            result[field_name] = field_map.get(field_name, _("近5分钟无数据上报"))
        return result

    @staticmethod
    def last_time(raw_data):
        if raw_data:
            return date_convert(int(raw_data[0]["_time_"]) / 1000, "datetime")
        return ""


class GetCustomReportDashboardConfigResource(GetSceneViewConfig):
    """
    自定义指标图表配置
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        id = serializers.IntegerField(required=True, label=_lazy("采集ID"))
        compare_config = serializers.DictField(label=_lazy("对比配置"), default=lambda: {})
        # 视图类型：overview(总览视图)、topo_node(拓扑节点视图)、leaf_node(叶子节点，即主机或者实例视图)
        view_type = serializers.ChoiceField(
            default=ViewType.LeafNode,
            choices=[ViewType.LeafNode, ViewType.TopoNode, ViewType.Overview],
            label=_lazy("视图类型"),
        )

    DASHBOARD_TITLE = _lazy("监控图表")
    HIDE_NO_GROUP_METRIC = False

    @classmethod
    def get_order_config_key(cls, params):
        return f"panel_order_custom_report_{params['id']}"

    @classmethod
    def get_order_config(cls, params):
        table = CustomTSTable.objects.get(pk=params["id"], bk_biz_id=params["bk_biz_id"])
        fields = CustomTSItem.objects.filter(table=table).exclude(label="")

        label_fields = defaultdict(list)
        for field in fields:
            label_fields[field.label].append(field)

        return [
            {
                "id": label,
                "title": label,
                "panels": [{"id": f"{table.table_id}.{field.metric_name}", "hidden": field.hidden} for field in fields],
            }
            for label, fields in label_fields.items()
        ]

    @classmethod
    def get_query_configs(cls, params) -> List[Dict]:
        """
        获取图表查询配置
        :param params:
        :return:
        """
        config = CustomTSTable.objects.get(pk=params["id"], bk_biz_id=params["bk_biz_id"])
        metrics = config.get_metrics()

        # 查询所有维度字段
        dimensions = []
        for metric in metrics.values():
            if metric["monitor_type"] == "dimension" and metric["name"] != "target":
                dimensions.append(metric["name"])
                continue

        query_configs = []
        for metric in metrics.values():
            if metric["monitor_type"] == "dimension":
                continue

            query_config = {
                "id": f"{config.table_id}.{metric['name']}",
                "metric_field": metric["name"],
                "metric_field_name": metric["description"] or metric["name"],
                "result_table_id": config.table_id,
                "data_source_label": DataSourceLabel.CUSTOM,
                "data_type_label": DataTypeLabel.TIME_SERIES,
                "method": "AVG",
                "interval": 60,
                "group_by": dimensions,
                "where": [],
            }

            if params.get("view_type", ViewType.LeafNode) == ViewType.Overview:
                pass
            else:
                query_config["where"].append(
                    {"condition": "and", "key": "target", "method": "eq", "value": ["$target"]}
                )
            query_config["alias"] = " | ".join([f"$tag_{dimension}" for dimension in dimensions])

            query_configs.append(query_config)

        return query_configs

    @classmethod
    def add_target_condition(cls, params, targets: List) -> None:
        """
        插入目标对比条件
        """
        compare_targets = params["compare_config"].get("targets", [])

        if not compare_targets:
            return

        if not targets[0]["alias"]:
            targets[0]["alias"] = _("总览")

        if params.get("view_type", ViewType.LeafNode) == ViewType.Overview:
            targets.append(json.loads(json.dumps(targets[0])))
            targets[0]["data"]["where"] = []

        group_by = set(targets[0]["data"]["group_by"])
        group_by.add("target")
        targets[0]["data"]["group_by"] = list(group_by)
        targets[0]["alias"] = " | ".join(f"$tag_{dimension}" for dimension in targets[0]["data"]["group_by"])

        where = targets[0]["data"]["where"]
        where.append({"condition": "or", "key": "target", "method": "eq", "value": compare_targets})

        if where and "condition" in where[0]:
            del where[0]["condition"]


class CustomTimeSeriesGraphPoint(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        metric = serializers.CharField(required=True, label=_("指标名"))
        time_series_group_id = serializers.IntegerField(required=True, label=_lazy("自定义时序ID"))
        method = serializers.ChoiceField(required=True, choices=["SUM", "AVG", "MAX", "MIN"], label=_("聚合方法"))
        time_range = serializers.CharField(required=True, label=_("时间范围"))
        target = serializers.ListField(required=True, label=_("目标信息"))
        dimensions = serializers.ListField(required=False, label=_("维度信息"))
        unit = serializers.CharField(required=False, label=_("单位"))

    def perform_request(self, validated_request_data):
        config = CustomTSTable.objects.get(pk=validated_request_data["time_series_group_id"])
        metric = validated_request_data["metric"]
        target = validated_request_data["target"]
        result = resource.commons.graph_point(
            monitor_field=metric,
            method=validated_request_data["method"],
            result_table_id=config.table_id,
            filter_dict={"target": target} if target else {},
            group_by_list=validated_request_data.get("dimensions", config.query_dimensions(metric)),
            unit=validated_request_data.get("unit", ""),
            time_range=validated_request_data["time_range"],
            use_short_series_name=True,
            view_width=6,
            bk_biz_id=validated_request_data["bk_biz_id"],
            data_source_label=DataSourceLabel.CUSTOM,
            data_type_label=DataTypeLabel.TIME_SERIES,
        )
        return result
