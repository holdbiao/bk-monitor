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
import datetime
import logging
import re
from typing import Generator, Dict

from django.conf import settings
from django.db.models import Count, Q
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.data_source import is_build_in_process_data_source
from bkmonitor.models import BaseAlarm, SnapshotHostIndex, QueryConfigModel
from bkmonitor.utils.common_utils import count_md5
from constants.data_source import DataSourceLabel, DataTypeLabel, ResultTableLabelObj
from constants.strategy import DimensionFieldType
from core.drf_resource import api
from core.errors.api import BKAPIError
from monitor_web.models import (
    CollectConfigMeta,
    CustomEventGroup,
    CustomEventItem,
    DataTarget,
    DataTargetMapping,
)
from monitor_web.models.metric_list_cache import MetricListCache
from monitor_web.models.plugin import CollectorPluginMeta

# 指标维度被过滤掉的维度列表
from monitor_web.plugin.manager.process import BuildInProcessMetric, BuildInProcessDimension
from constants.strategy import SYSTEM_EVENT_RT_TABLE_ID
from monitor_web.tasks import run_metric_manager_async

FILTER_DIMENSION_LIST = ["time", "bk_supplier_id", "bk_cmdb_level", "timestamp"]
# 时序指标filed_type
TIME_SERIES_FIELD_TYPE = ["integer", "long", "float", "double", "int", "bigint"]
# 日志检索内置维度字段
LOG_SEARCH_DIMENSION_LIST = ["cloudId", "gseIndex", "iterationIndex", "container_id", "_iteration_idx"]

logger = logging.getLogger(__name__)


class DefaultDimensions(object):
    host = [{"id": "bk_target_ip", "name": _lazy("目标IP")}, {"id": "bk_target_cloud_id", "name": _lazy("云区域ID")}]
    service = [{"id": "bk_target_service_instance_id", "name": _lazy("服务实例")}]
    device = [{"id": "bk_target_device_ip", "name": _lazy("远程采集目标IP")}]
    uptime_check_response = [
        {"id": "task_id", "name": _lazy("任务ID")},
        {"id": "ip", "name": _lazy("节点地址")},
        {"id": "bk_cloud_id", "name": _lazy("节点云区域id")},
    ]
    uptime_check = [
        {"id": "task_id", "name": _lazy("任务ID")},
        {"id": "node_id", "name": _lazy("节点ID")},
        {"id": "ip", "name": _lazy("节点地址")},
        {"id": "bk_cloud_id", "name": _lazy("节点云区域id")},
    ]


class UptimeCheckMetricFuller(object):
    def full_dimension(self, task):
        if task.protocol == "HTTP":
            self.dimensions.append({"id": "url", "name": _lazy("目标")})
        if task.protocol in ["TCP", "UDP"]:
            self.dimensions.append({"id": "target_host", "name": _lazy("目标IP")})
            self.dimensions.append({"id": "target_port", "name": _lazy("目标端口")})


class AvailableMetric(UptimeCheckMetricFuller):
    """
    单点可用率
    """

    def __init__(self, task):
        self.metric_field = "available"
        self.metric_field_name = _("单点可用率")
        self.dimensions = copy.deepcopy(DefaultDimensions.uptime_check)
        self.default_condition = []
        self.unit = "percentunit"
        self.full_dimension(task)


class TaskDurationMetric(UptimeCheckMetricFuller):
    """
    响应时间
    """

    def __init__(self, task):
        self.metric_field = "task_duration"
        self.metric_field_name = _("响应时间")
        self.unit = "ms"
        self.dimensions = copy.deepcopy(DefaultDimensions.uptime_check)
        self.default_condition = []
        self.full_dimension(task)


class ResponseCodeMetric(UptimeCheckMetricFuller):
    """
    响应码
    """

    def __init__(self, task):
        self.metric_field = "response_code"
        self.metric_field_name = _("期望响应码")
        self.dimensions = copy.deepcopy(DefaultDimensions.uptime_check_response)
        self.default_condition = []
        self.full_dimension(task)


class ResponseMetric(UptimeCheckMetricFuller):
    """
    响应内容
    """

    def __init__(self, task):
        self.metric_field = "message"
        self.metric_field_name = _("期望响应内容")
        self.dimensions = copy.deepcopy(DefaultDimensions.uptime_check_response)
        self.default_condition = []
        self.full_dimension(task)


DEFAULT_DIMENSIONS_MAP = {
    "host_target": DefaultDimensions.host,
    "service_target": DefaultDimensions.service,
    "none_target": [],
    "device_target": DefaultDimensions.device,
}

UPTIMECHECK_MAP = {
    "HTTP": [AvailableMetric, TaskDurationMetric, ResponseCodeMetric, ResponseMetric],
    "UDP": [AvailableMetric, TaskDurationMetric],
    "TCP": [AvailableMetric, TaskDurationMetric],
}


class BaseMetricCacheManager:
    """
    指标缓存管理器 基类
    """

    data_source_label = ""
    data_type_label = ""

    def __init__(self, bk_biz_id=None):
        self.bk_biz_id = bk_biz_id
        self.new_metric_ids = []
        self._label_names_map = None
        self.has_exception = False
        self.metric_use_frequency = {
            metric["metric_id"]: metric["use_frequency"]
            for metric in QueryConfigModel.objects.filter(
                data_source_label=self.data_source_label, data_type_label=self.data_type_label
            )
            .values("metric_id")
            .annotate(use_frequency=Count("metric_id"))
        }

    def get_tables(self) -> Generator[Dict, None, None]:
        """
        查询表数据
        """
        raise NotImplementedError

    def get_metrics_by_table(self, table) -> Generator[Dict, None, None]:
        """
        根据表查询指标数据
        """
        raise NotImplementedError

    def get_metric_pool(self):
        return MetricListCache.objects.filter(
            data_type_label=self.data_type_label,
            data_source_label=self.data_source_label,
        )

    def _run(self):
        # 集中整理后进行差量更新
        to_be_create = []
        to_be_update = {}
        to_be_delete = []
        metric_pool = self.get_metric_pool()
        if self.bk_biz_id is not None:
            metric_pool = metric_pool.filter(bk_biz_id=self.bk_biz_id)

        # metric_hash_dict
        metric_hash_dict = {}
        for m in metric_pool:
            metric_id = ".".join(map(str, [m.bk_biz_id, m.result_table_id, m.metric_field, m.related_id]))
            if metric_id in metric_hash_dict:
                to_be_delete.append(m.id)
            else:
                metric_hash_dict[metric_id] = m

        for table in self.get_tables():
            for metric in self.get_metrics_by_table(table):
                # 补全维度字段
                dimensions = metric.get("dimensions", [])
                for dimension in dimensions:
                    if "is_dimension" not in dimension:
                        dimension["is_dimension"] = True
                    if "type" not in dimension:
                        dimension["type"] = DimensionFieldType.String

                metric.update(
                    dict(
                        use_frequency=self.metric_use_frequency.get(
                            f"{metric.get('data_source_label', '')}."
                            f"{metric.get('result_table_id', '')}.{metric['metric_field']}",
                            0,
                        )
                    )
                )
                metric_id = "{}.{}.{}.{}".format(
                    metric["bk_biz_id"],
                    metric.get("result_table_id", ""),
                    metric["metric_field"],
                    metric.get("related_id", ""),
                )
                metric_instance = metric_hash_dict.pop(metric_id, None)
                if metric_instance is None:
                    logger.info("to be created: %s" % metric_id)
                    to_be_create.append(MetricListCache(**metric))
                    continue

                for k, v in metric.items():
                    if count_md5(getattr(metric_instance, k, None)) != count_md5(v):
                        logger.info("metric_instance.{}={} != {}".format(k, getattr(metric_instance, k, None), v))
                        logger.info("to be update: %s" % metric_id)
                        metric["last_update"] = datetime.datetime.now()
                        to_be_update[metric_instance.id] = metric
                        break

        to_be_delete.extend([m.id for m in metric_hash_dict.values()])
        # create
        MetricListCache.objects.bulk_create(to_be_create, batch_size=50)
        # update
        for k, v in to_be_update.items():
            MetricListCache.objects.filter(id=k).update(**v)
        # clean
        if to_be_delete:
            logger.info("delete: {}".format(list(metric_hash_dict.keys())))
            MetricListCache.objects.filter(id__in=to_be_delete).delete()

    def run(self, delay=False):
        if delay:
            run_metric_manager_async.delay(self)
        else:
            self._run()

    def get_label_name(self, label_id: str) -> str:
        """
        获取标签名称
        """
        if self._label_names_map is None:
            try:
                result = api.metadata.get_label(include_admin_only=True)
                self._label_names_map = {
                    label["label_id"]: label["label_name"] for label in result["result_table_label"]
                }
            except Exception as e:
                logger.exception(e)
                self._label_names_map = {}

        return self._label_names_map.get(label_id, label_id)


class CustomMetricCacheManager(BaseMetricCacheManager):
    """
    自定义指标缓存
    """

    data_source_label = DataSourceLabel.CUSTOM
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self, bk_biz_id=None):
        super(CustomMetricCacheManager, self).__init__(bk_biz_id)
        self.build_process_metric_cleaned = False

    def get_tables(self):
        custom_ts_result = api.metadata.query_time_series_group()
        # 不在监控创建的策略配置均展示，除了全局data id， 该过滤在get_metrics_by_table中生效
        for result in custom_ts_result:
            self.process_logbeat_table(result)
            yield result

    @staticmethod
    def process_logbeat_table(table: Dict):
        """
        设置日志采集器指标，配置到指定业务下"
        """
        table_id = table["table_id"]

        if settings.BKUNIFYLOGBEAT_METRIC_BIZ and table_id in [
            "bkunifylogbeat_task.base",
            "bkunifylogbeat_common.base",
        ]:
            table["bk_biz_id"] = settings.BKUNIFYLOGBEAT_METRIC_BIZ
            table["label"] = "host_process"

            if table_id == "bkunifylogbeat_task.base":
                metrics = [
                    {"field_name": "crawler_dropped", "description": "需要过滤的事件数"},
                    {"field_name": "crawler_received", "description": "接收到的采集事件数"},
                    {"field_name": "crawler_send_total", "description": "正常发送事件数"},
                    {"field_name": "crawler_state", "description": "接收到的采集进度事件数"},
                    {"field_name": "gse_publish_total", "description": "按任务计算发送次数"},
                    {"field_name": "sender_received", "description": "sender接收到的事件数"},
                    {"field_name": "sender_send_total", "description": "sender发送的采集事件包数"},
                    {"field_name": "sender_state", "description": "sender发送的采集进度包数"},
                    {"field_name": "gse_publish_failed", "description": "按任务计算发送失败次数"},
                ]
            else:
                metrics = [
                    {"field_name": "beat_cpu_total_norm_pct", "description": "beat-CPU资源占比", "unit": "percentunit"},
                    {"field_name": "beat_cpu_total_pct", "description": "beat-CPU资源单核占比"},
                    {"field_name": "beat_info_uptime_ms", "description": "beat-采集器运行时间", "unit": "ms"},
                    {"field_name": "beat_memstats_rss", "description": "beat-内存使用情况", "unit": "bytes"},
                    {"field_name": "bkbeat_crawler_dropped", "description": "bkbeat-已过滤的事件数"},
                    {"field_name": "bkbeat_crawler_received", "description": "bkbeat-已接收的采集事件数"},
                    {"field_name": "bkbeat_crawler_send_total", "description": "bkbeat-已发送的事件数"},
                    {"field_name": "bkbeat_crawler_state", "description": "bkbeat-已接收的采集进度数"},
                    {"field_name": "bkbeat_task_input_failed", "description": "bkbeat-启动任务异常的次数"},
                    {"field_name": "bkbeat_task_processors_failed", "description": "bkbeat-启动processors异常的次数"},
                    {"field_name": "bkbeat_task_sender_failed", "description": "bkbeat-启动sender异常的次数"},
                    {"field_name": "bkbeat_registrar_marshal_error", "description": "bkbeat-采集DB的解析异常的次数"},
                    {"field_name": "bkbeat_gse_agent_receive_failed", "description": "gse_client-接收gse_agent异常的次数"},
                    {"field_name": "bkbeat_gse_agent_received", "description": "gse_client-接收到gse_agent的次数"},
                    {"field_name": "bkbeat_gse_client_connect_retry", "description": "gse_client-gse_agent重连次数"},
                    {"field_name": "bkbeat_gse_client_connect_failed", "description": "gse_client-gse_agent连接失败的次数"},
                    {"field_name": "bkbeat_gse_client_connected", "description": "gse_client-gse_agent连接成功的次数"},
                    {"field_name": "bkbeat_gse_client_received", "description": "gse_client-已接收的事件数"},
                    {"field_name": "bkbeat_gse_client_send_retry", "description": "gse_client-发送重试的次数"},
                    {"field_name": "bkbeat_gse_client_send_timeout", "description": "gse_client-发送超时的次数"},
                    {"field_name": "bkbeat_gse_client_send_total", "description": "gse_client-已发送的事件数"},
                    {"field_name": "bkbeat_gse_client_send_failed", "description": "gse_client-发送失败的事件数"},
                    {"field_name": "bkbeat_gse_client_server_close", "description": "gse_client-gse_agent断开次数"},
                    {"field_name": "bkbeat_gse_publish_received", "description": "publish-已接收的采集事件数"},
                    {"field_name": "bkbeat_gse_publish_total", "description": "publish-已发送的采集事件数"},
                    {"field_name": "bkbeat_gse_publish_dropped", "description": "publish-已丢弃的采集事件数"},
                    {"field_name": "bkbeat_gse_publish_failed", "description": "publish-发送失败的采集事件数"},
                    {"field_name": "bkbeat_gse_report_received", "description": "publish-已接收的心跳事件数"},
                    {"field_name": "bkbeat_gse_report_send_total", "description": "publish-已发送的心跳事件数"},
                    {"field_name": "bkbeat_gse_report_failed", "description": "publish-发送失败的心跳事件数"},
                    {"field_name": "bkbeat_gse_send_total", "description": "publish-发给gse_client的事件数"},
                    {"field_name": "bkbeat_manager_active", "description": "bkbeat-当前有效的任务数"},
                    {"field_name": "bkbeat_manager_reload", "description": "bkbeat-周期内Reload的任务数"},
                    {"field_name": "bkbeat_manager_start", "description": "bkbeat-周期内启动的任务数"},
                    {"field_name": "bkbeat_manager_stop", "description": "bkbeat-周期内停止的任务数"},
                    {"field_name": "bkbeat_manager_error", "description": "bkbeat-周期内启动异常的任务数"},
                    {"field_name": "bkbeat_registrar_files", "description": "bkbeat-采集DB注册的文件数"},
                    {"field_name": "bkbeat_registrar_flushed", "description": "bkbeat-采集DB的刷新次数"},
                    {"field_name": "bkbeat_sender_received", "description": "bkbeat-sender-已接收的采集事件数"},
                    {"field_name": "bkbeat_sender_send_total", "description": "bkbeat-sender-已发送的事件数"},
                    {"field_name": "bkbeat_sender_state", "description": "bkbeat-sender-已发送的采集进度数"},
                    {"field_name": "filebeat_harvester_closed", "description": "beat-已释放的文件数"},
                    {"field_name": "filebeat_harvester_open_files", "description": "beat-已打开的文件数"},
                    {"field_name": "filebeat_harvester_running", "description": "beat-正在采集的文件数"},
                    {"field_name": "filebeat_harvester_skipped", "description": "beat-已过滤的文件数"},
                    {"field_name": "filebeat_input_log_files_renamed", "description": "beat-renamed的文件数"},
                    {"field_name": "filebeat_input_log_files_truncated", "description": "beat-truncated的文件数"},
                    {"field_name": "libbeat_pipeline_events_active", "description": "beat-正在发送的采集事件数"},
                    {"field_name": "libbeat_pipeline_events_published", "description": "beat-已发送的采集事件数"},
                    {"field_name": "libbeat_pipeline_events_total", "description": "beat-已接收的采集事件数"},
                    {"field_name": "libbeat_pipeline_queue_acked", "description": "beat-已确认的采集事件数"},
                    {"field_name": "system_load_1", "description": "beat-采集目标1分钟负载"},
                    {"field_name": "system_load_15", "description": "beat-采集目标15分钟负载"},
                    {"field_name": "system_load_5", "description": "beat-采集目标5分钟负载"},
                ]

            tags = [
                {"field_name": "bk_biz_id", "description": "业务ID"},
                {"field_name": "target", "description": "目标"},
                {"field_name": "task_data_id", "description": "数据ID"},
                {"field_name": "type", "description": "类型"},
                {"field_name": "version", "description": "版本号"},
            ]

            for metric in metrics:
                metric["tag_list"] = tags
            table["metric_info_list"] = metrics

    def get_metrics_by_table(self, table):
        table_id = table["table_id"]
        base_dict = {
            "result_table_id": table_id,
            "result_table_name": table["time_series_group_name"],
            "result_table_label": table["label"],
            "result_table_label_name": self.get_label_name(table["label"]),
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "bk_biz_id": table["bk_biz_id"],
            "data_target": DataTargetMapping().get_data_target(
                table["label"], self.data_source_label, self.data_type_label
            ),
            "collect_config_ids": [],
            "related_name": table["time_series_group_name"],
            "related_id": table["time_series_group_id"],
            "extend_fields": {"bk_data_id": table["bk_data_id"]},
        }

        for metric_msg in table["metric_info_list"]:
            if not metric_msg:
                continue
            metric_detail = {
                "default_dimensions": [],
                "default_condition": [],
                "metric_field": metric_msg["field_name"],
                "metric_field_name": metric_msg["description"] or metric_msg["field_name"],
                "dimensions": [
                    {
                        "id": dimension["field_name"],
                        "name": BuildInProcessDimension(
                            dimension["description"] or dimension["field_name"]
                        ).field_name_description,
                    }
                    for dimension in metric_msg["tag_list"]
                ],
                "unit": metric_msg.get("unit", ""),
            }
            metric_detail.update(base_dict)
            if is_build_in_process_data_source(table_id):
                metric_detail.update(BuildInProcessMetric(f"{table_id}.{metric_msg['field_name']}").to_dict())
                metric_detail["data_source_label"] = DataSourceLabel.BK_MONITOR_COLLECTOR
                if not self.build_process_metric_cleaned:
                    MetricListCache.objects.filter(
                        result_table_id__in=BuildInProcessMetric.result_table_list()
                    ).delete()
                    self.build_process_metric_cleaned = True

            elif metric_detail["bk_biz_id"] == 0:
                # 不是内置进程采集，但又是全局自定义指标，则过滤
                continue
            yield metric_detail


class BkdataMetricCacheManager(BaseMetricCacheManager):
    data_source_label = DataSourceLabel.BK_DATA
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self, bk_biz_id):
        super(BkdataMetricCacheManager, self).__init__(bk_biz_id)

    def get_tables(self):
        if str(self.bk_biz_id) == str(settings.BK_DATA_BK_BIZ_ID):
            yield []
        else:
            yield from api.bkdata.list_result_table(bk_biz_id=self.bk_biz_id)

    def get_metrics_by_table(self, table):
        storage_list = {key for key, info in list(table["storages"].items()) if info["active"]}
        # 计算平台中支持进行监控的存储
        if not {"mysql", "tspider", "databus_tspider"} & set(storage_list):
            return []

        bk_biz_id = table["bk_biz_id"]
        result_table_id = table["result_table_id"]
        result_table_name = table["result_table_name"]

        dimensions = []
        for field in table["fields"]:
            if field["field_name"] in FILTER_DIMENSION_LIST:
                continue

            # 是否可以作为维度
            is_dimensions = field["field_type"] in ["string", "text"] or field["is_dimension"]

            if field["field_type"] in TIME_SERIES_FIELD_TYPE:
                field_type = DimensionFieldType.Number
            else:
                field_type = DimensionFieldType.String

            dimensions.append(
                {
                    "id": field["field_name"],
                    "name": field["field_alias"] if field["field_alias"] else field["field_name"],
                    "type": field_type,
                    "is_dimension": is_dimensions,
                }
            )

        result_table_label = table["result_table_type"] if table["result_table_type"] else "other_rt"

        base_dict = {
            "result_table_id": result_table_id,
            "result_table_name": result_table_name,
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "result_table_label": result_table_label,
            "result_table_label_name": self.get_label_name(result_table_label),
            "dimensions": dimensions,
            "data_target": DataTarget.NONE_TARGET,
            "bk_biz_id": bk_biz_id,
        }

        for field in table["fields"]:
            field_dict = {}
            field_dict.update(base_dict)

            if field["field_type"] in TIME_SERIES_FIELD_TYPE:
                field_dict["metric_field"] = field["field_name"]
                field_dict["metric_field_name"] = field["field_alias"] if field["field_alias"] else field["field_name"]
                field_dict["unit"] = field.get("unit", "")
                field_dict["unit_conversion"] = field.get("unit_conversion", 1.0)
                yield field_dict

    def run(self, delay=True):
        super(BkdataMetricCacheManager, self).run(delay)


class BkLogSearchCacheManager(BaseMetricCacheManager):
    """
    日志时序数据缓存
    """

    data_source_label = DataSourceLabel.BK_LOG_SEARCH
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self, bk_biz_id):
        super(BkLogSearchCacheManager, self).__init__(bk_biz_id)

        self.cluster_id_to_name = {
            cluster["cluster_config"]["cluster_id"]: cluster["cluster_config"]["cluster_name"]
            for cluster in api.metadata.query_cluster_info(cluster_type="elasticsearch")
        }

    def get_tables(self):
        index_list = api.log_search.search_index_set(bk_biz_id=self.bk_biz_id)
        for index_set_msg in index_list:
            index_set_msg["bk_biz_id"] = self.bk_biz_id
            if not index_set_msg["category_id"]:
                index_set_msg["category_id"] = ResultTableLabelObj.OthersObj.other_rt

            # 如果时间字段为空，默认使用dtEventTimeStamp
            if not index_set_msg.get("time_field"):
                index_set_msg["time_field"] = "dtEventTimeStamp"
        yield from index_list

    def get_metrics_by_table(self, table):
        return_list = []

        try:
            fields_response = api.log_search.search_index_fields(
                bk_biz_id=table["bk_biz_id"], index_set_id=table["index_set_id"]
            )
        except BKAPIError:
            self.has_exception = True
            return

        related_map = {"related_id": [], "related_name": []}
        for indices_msg in table["indices"]:
            if indices_msg["result_table_name"]:
                related_name = indices_msg["result_table_name"]
            else:
                related_name = indices_msg["result_table_id"]

            related_map["related_id"].append(indices_msg["result_table_id"])
            related_map["related_name"].append(related_name)

        # 获取维度列表
        dimension_list = []
        for fields_msg in fields_response.get("fields", []):
            field_id = field_description = fields_msg["field_name"]
            if fields_msg["description"]:
                field_description = fields_msg["description"]

            if fields_msg.get("field_type") != "date":
                temp = {"id": field_id, "name": field_description, "is_dimension": bool(fields_msg["es_doc_values"])}
                dimension_list.append(temp)

            if (
                fields_msg["es_doc_values"]
                and fields_msg.get("field_type") in TIME_SERIES_FIELD_TYPE
                and fields_msg.get("field_name") not in LOG_SEARCH_DIMENSION_LIST
            ):
                create_data = {
                    "default_dimensions": [],
                    "default_condition": [],
                    "data_target": DataTarget.NONE_TARGET,
                    "data_type_label": self.data_type_label,
                    "data_source_label": self.data_source_label,
                    "result_table_id": ",".join(related_map["related_id"]),
                    "result_table_name": ",".join(related_map["related_name"]),
                    "metric_field": field_id,
                    "metric_field_name": field_description,
                    "dimensions": [],
                    "bk_biz_id": table["bk_biz_id"],
                    "related_id": str(table["index_set_id"]),
                    "related_name": table["index_set_name"],
                    "category_display": table["index_set_name"],
                    "result_table_label": table["category_id"],
                    "result_table_label_name": self.get_label_name(table["category_id"]),
                    "extend_fields": {
                        "time_field": table.get("time_field", ""),
                        "scenario_name": table.get("scenario_name", ""),
                        "index_set_id": table.get("index_set_id", ""),
                        "scenario_id": table.get("scenario_id", ""),
                        "storage_cluster_id": table.get("storage_cluster_id", ""),
                        "storage_cluster_name": self.cluster_id_to_name.get(table.get("storage_cluster_id"), ""),
                    },
                }
                return_list.append(create_data)

        for metric_msg in return_list:
            metric_msg["dimensions"] = [
                dimension for dimension in dimension_list if dimension["id"] != metric_msg["metric_field"]
            ]

        yield from return_list

    def run(self, delay=True):
        super(BkLogSearchCacheManager, self).run(delay)


class CustomEventCacheManager(BaseMetricCacheManager):
    """
    批量缓存自定义事件指标
    """

    data_source_label = DataSourceLabel.CUSTOM
    data_type_label = DataTypeLabel.EVENT

    def get_tables(self):
        custom_event_result = api.metadata.query_event_group.request.refresh()
        logger.info("[QUERY_EVENT_GROUP] event_group_list length is {}".format(len(custom_event_result)))
        event_group_ids = [
            custom_event.bk_event_group_id for custom_event in CustomEventGroup.objects.filter(type="custom_event")
        ]
        # 增加自定义事件筛选，不在监控创建的策略配置时不展示
        for result in custom_event_result:
            if result["event_group_id"] in event_group_ids:
                yield result

    def get_metrics_by_table(self, table):
        # 将获取的自定义事件结果表信息处理成缓存表信息
        return_list = []
        base_dict = {
            "result_table_id": str(table["bk_data_id"]),
            "result_table_name": table["event_group_name"],
            "result_table_label": table["label"],
            "result_table_label_name": self.get_label_name(table["label"]),
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "bk_biz_id": table["bk_biz_id"],
            "data_target": DataTargetMapping().get_data_target(
                table["label"], self.data_source_label, self.data_type_label
            ),
            "collect_config_ids": [],
        }

        for metric_msg in table["event_info_list"]:
            metric_detail = {
                "default_dimensions": [],
                "default_condition": [],
                "metric_field": str(metric_msg["event_id"]),
                "metric_field_name": metric_msg["event_name"],
                "dimensions": [
                    {"id": dimension_name, "name": dimension_name} for dimension_name in metric_msg["dimension_list"]
                ],
                "extend_fields": {"custom_event_name": metric_msg["event_name"]},
            }
            metric_detail.update(base_dict)
            yield metric_detail
        return return_list


class BkMonitorLogCacheManager(BaseMetricCacheManager):
    """
    缓存日志关键字指标
    """

    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.LOG

    def get_tables(self):
        custom_event_result = api.metadata.query_event_group.request.refresh()
        logger.info("[QUERY_EVENT_GROUP] event_group_list length is {}".format(len(custom_event_result)))

        self.event_group_id_to_event_info = {}
        for e in custom_event_result:
            event_group_id = int(e["event_group_id"])
            self.event_group_id_to_event_info[event_group_id] = e

        yield from CollectConfigMeta.objects.filter(
            Q(collect_type=CollectConfigMeta.CollectType.SNMP_TRAP) | Q(collect_type=CollectConfigMeta.CollectType.LOG)
        )

    def get_metrics_by_table(self, table):
        version = table.deployment_config.plugin_version
        event_group_name = "{}_{}".format(version.plugin.plugin_type, version.plugin_id)
        group_info = CustomEventGroup.objects.get(name=event_group_name)
        event_info_list = CustomEventItem.objects.filter(bk_event_group=group_info)

        metric = {
            "result_table_id": group_info.table_id,
            "result_table_name": group_info.name,
            "result_table_label": version.plugin.label,
            "result_table_label_name": self.get_label_name(version.plugin.label),
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "bk_biz_id": table.bk_biz_id,
            "data_target": DataTargetMapping().get_data_target(
                version.plugin.label, self.data_source_label, self.data_type_label
            ),
            "collect_config_ids": [],
            "default_dimensions": [],
            "default_condition": [],
            "metric_field": "event.count",
            "metric_field_name": table.name,
            "related_name": table.name,
            "related_id": str(table.id),
        }

        dimensions = set()
        event_group_item = self.event_group_id_to_event_info.get(int(group_info.bk_event_group_id))
        if event_group_item:
            for event_info in event_group_item["event_info_list"]:
                for dimension in event_info["dimension_list"]:
                    dimensions.add(dimension)
        else:
            for event_info in event_info_list:
                for dimension in event_info.dimension_list:
                    dimensions.add(dimension["dimension_name"])

        metric["dimensions"] = [{"id": dimension_name, "name": dimension_name} for dimension_name in dimensions]
        yield metric


class BaseAlarmMetricCacheManager(BaseMetricCacheManager):
    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.EVENT

    def add_gse_process_event_metrics(self, result_table_label):
        """
        增加gse进程托管相关指标
        """
        gse_process_dimensions = [
            {"id": "event_name", "name": "事件名称", "is_dimension": True, "type": "string"},
            {"id": "process_name", "name": "进程名称", "is_dimension": True, "type": "string"},
            {"id": "process_group_id", "name": "进程组ID", "is_dimension": True, "type": "string"},
            {"id": "process_index", "name": "进程索引", "is_dimension": True, "type": "string"},
        ]
        gse_base_dict = {
            "bk_biz_id": 0,
            "result_table_id": SYSTEM_EVENT_RT_TABLE_ID,
            "result_table_label": "host_process",
            "result_table_label_name": self.get_label_name("host_process"),
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "data_target": DataTargetMapping().get_data_target(
                result_table_label, self.data_source_label, self.data_type_label
            ),
            "dimensions": gse_process_dimensions,
            "default_dimensions": ["process_name", "process_group_id", "process_index", "event_name"],
            "default_condition": [],
            "collect_config_ids": [],
        }
        gse_custom_report = [{"metric_field": "gse_process_event", "metric_field_name": _("Gse进程托管事件")}]
        for metric in gse_custom_report:
            metric.update(gse_base_dict)
            yield metric

    def get_tables(self):
        yield {}

    def get_metrics_by_table(self, table):
        result_table_label = "os"
        metric_list = BaseAlarm.objects.filter(is_enable=True)
        base_dict = {
            "bk_biz_id": 0,
            "result_table_id": SYSTEM_EVENT_RT_TABLE_ID,
            "result_table_label": result_table_label,
            "result_table_label_name": self.get_label_name(result_table_label),
            "data_source_label": self.data_source_label,
            "data_type_label": self.data_type_label,
            "data_target": DataTargetMapping().get_data_target(
                result_table_label, self.data_source_label, self.data_type_label
            ),
            "default_dimensions": [],
            "default_condition": [],
            "collect_config_ids": [],
        }

        for metric in metric_list:
            metric_dict = copy.deepcopy(base_dict)
            metric_dict["metric_field"] = metric.title
            metric_dict["metric_field_name"] = metric.description
            metric_dict["dimensions"] = [{"id": dimension, "name": dimension} for dimension in metric.dimensions]
            yield metric_dict

        # 增加额外的系统事件指标
        extend_metrics = [
            {"metric_field": "gse_custom_event", "metric_field_name": _("自定义字符型告警")},
            {
                "metric_field": "proc_port",
                "metric_field_name": _("进程端口"),
                "dimensions": [
                    {"id": "display_name", "name": "display_name"},
                    {"id": "protocol", "name": "protocol"},
                    {"id": "bind_ip", "name": "bind_ip"},
                ],
                "result_table_label": "host_process",
            },
            {"metric_field": "os_restart", "metric_field_name": _("主机重启")},
        ]

        for metric in extend_metrics:
            metric_dict = copy.deepcopy(base_dict)
            metric_dict.update(metric)
            yield metric_dict

        # gse进程托管事件指标
        for metric in self.add_gse_process_event_metrics(result_table_label):
            yield metric


class BkmonitorMetricCacheManager(BaseMetricCacheManager):
    data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
    data_type_label = DataTypeLabel.TIME_SERIES

    def __init__(self):
        super(BkmonitorMetricCacheManager, self).__init__()
        # 添加默认维度映射
        has_default_dimension = SnapshotHostIndex.objects.exclude(dimension_field="")
        self.dimension_map = dict()
        for dimension_instance in has_default_dimension:
            map_key = "{}.{}".format(dimension_instance.result_table_id.replace("_", ".", 1), dimension_instance.item)
            self.dimension_map[map_key] = dimension_instance.dimension_field.split(",")

    def get_metric_pool(self):
        return MetricListCache.objects.filter(
            data_type_label=self.data_type_label,
            data_source_label=self.data_source_label,
        ).filter(~Q(result_table_id__in=BuildInProcessMetric.result_table_list()))

    def get_tables(self):
        yield from api.metadata.list_monitor_result_table()

    def get_metrics_by_table(self, table, task_id=None):
        try:
            result_table_id = table["table_id"]
            influx_db_name = table["table_id"].split(".")[0]

            if "elasticsearch" == table["default_storage"] or re.match(r"_cmdb_level_split$", result_table_id):
                # 日志和拆分表的结果表不录入
                return

            if influx_db_name == "uptimecheck":
                yield from self.get_uptime_check_metric(table, task_id=task_id)
            elif influx_db_name == "pingserver":
                yield from self.get_pingserver_metric(table)
            elif influx_db_name == "system":
                if result_table_id in ["system.proc_port"]:
                    return

                yield from self.get_system_metric(table)
            else:
                yield from self.get_plugin_metric(table)
        except Exception:  # noqa
            logger.exception("get metrics error, table({})".format(table.get("table_id", "")))

    def get_base_dict(self, table):
        result_table_id = table["table_id"]
        result_table_name = table["table_name_zh"]

        dimensions = []
        for field in table["field_list"]:
            if field["tag"] == "dimension" and field["field_name"] not in FILTER_DIMENSION_LIST:
                dimensions.append(
                    {
                        "id": field["field_name"],
                        "name": field["description"] if field["description"] else field["field_name"],
                    }
                )

        data_target = DataTargetMapping().get_data_target(table["label"], table["source_label"], table["type_label"])

        default_dimensions = list([x["id"] for x in DEFAULT_DIMENSIONS_MAP[data_target]])

        return {
            "bk_biz_id": 0,
            "result_table_id": result_table_id,
            "result_table_name": result_table_name,
            "dimensions": dimensions,
            "default_dimensions": default_dimensions,
            "default_condition": [],
            "result_table_label": table["label"],
            "result_table_label_name": self.get_label_name(table["label"]),
            "data_source_label": table["source_label"],
            "data_type_label": table["type_label"],
            "data_target": data_target,
        }

    def get_field_metric_msg(self, table, base_metric):
        field_list = []
        for field in table["field_list"]:
            field_dict = {}
            field_dict.update(copy.deepcopy(base_metric))
            if field["tag"] == "metric":
                field_dict["metric_field"] = field["field_name"]
                field_dict["metric_field_name"] = field["alias_name"] if field["alias_name"] else field["field_name"]
                field_dict["unit"] = field.get("unit", "")
                field_dict["unit_conversion"] = field.get("unit_conversion", 1.0)
                field_dict["description"] = field.get("description", "")
                metric_id = "{}.{}".format(field_dict["result_table_id"], field_dict["metric_field"])
                if self.dimension_map.get(metric_id):
                    field_dict["default_dimensions"].extend(self.dimension_map.get(metric_id))

                field_list.append(field_dict)
        return field_list

    def get_uptime_check_metric(self, table, task_id=None):
        protocol = table["table_id"].split(".")[1].upper()
        base_metric = self.get_base_dict(table)
        from monitor_web.models.uptime_check import UptimeCheckTask

        if task_id:
            uptime_check_tasks = UptimeCheckTask.objects.filter(id=task_id)
        else:
            uptime_check_tasks = UptimeCheckTask.objects.filter(protocol=protocol)

        if protocol == "ICMP":
            field_metric_list = self.get_field_metric_msg(table, base_metric)
        else:
            field_metric_list = UPTIMECHECK_MAP.get(protocol, [])

        for task in uptime_check_tasks:
            for metric_model in field_metric_list:
                metric_dict = {}
                if protocol == "ICMP":
                    metric_dict = metric_model
                    metric_dict.update(
                        {
                            "default_condition": [
                                {
                                    "key": "task_id",
                                    "method": "eq",
                                    "value": str(task.id),
                                    "value_name": "{}（{}）".format(task.id, task.name),
                                }
                            ],
                        }
                    )
                else:
                    metric_dict.update(base_metric)
                    metric_obj = metric_model(task)
                    metric_obj.metric_field_name = f"{protocol} {metric_obj.metric_field_name}"
                    metric_dict.update(metric_obj.__dict__)

                metric_dict.update(
                    {
                        "category_display": _("服务拨测"),
                        "collect_interval": task.check_interval,
                        "related_name": task.name,
                        "related_id": str(task.id),
                        "bk_biz_id": task.bk_biz_id,
                        "default_dimensions": ["task_id"],
                        # 当前http/tcp/udp类型维度为给定内容
                        # icmp维度与metadata保持一致
                        # 针对拨测服务采集，过滤业务/IP/云区域ID/错误码
                        "dimensions": [
                            dimension
                            for dimension in metric_dict["dimensions"]
                            if dimension["id"] not in ["bk_biz_id", "ip", "bk_cloud_id", "error_code"]
                        ],
                    }
                )
                yield metric_dict

    def get_pingserver_metric(self, table):
        base_metric = self.get_base_dict(table)
        base_metric.update({"related_name": "pingserver", "related_id": "pingserver", "category_display": _("PING服务")})
        return self.get_field_metric_msg(table, base_metric)

    def get_system_metric(self, table):
        base_metric = self.get_base_dict(table)
        if settings.IS_ACCESS_BK_DATA and settings.IS_ENABLE_VIEW_CMDB_LEVEL:
            base_metric["dimensions"].append({"id": "bk_obj_id", "name": _("节点类型")})
            base_metric["dimensions"].append({"id": "bk_inst_id", "name": _("节点名称")})
        base_metric.update({"related_name": "system", "related_id": "system", "category_display": _("物理机")})
        return self.get_field_metric_msg(table, base_metric)

    def get_plugin_metric(self, table):
        base_metric = self.get_base_dict(table)

        base_metric["dimensions"].extend(DEFAULT_DIMENSIONS_MAP[base_metric["data_target"]])
        base_metric["dimensions"].append({"id": "bk_collect_config_id", "name": _("采集配置")})
        if settings.IS_ACCESS_BK_DATA and settings.IS_ENABLE_VIEW_CMDB_LEVEL:
            base_metric["dimensions"].append({"id": "bk_obj_id", "name": _("节点类型")})
            base_metric["dimensions"].append({"id": "bk_inst_id", "name": _("节点名称")})

        # 自建插件的插件信息
        influx_db_name = table["table_id"].split(".")[0]
        if influx_db_name in ["apache", "mysql", "nginx", "redis", "tomcat"]:
            related_id = "bkplugin_" + influx_db_name
        elif influx_db_name[0].isdigit():
            related_id = influx_db_name.split("_", 2)[2]
        else:
            names = influx_db_name.split("_", 1)
            if len(names) < 2:
                return []
            else:
                related_id = names[1]

        try:
            plugin = CollectorPluginMeta.objects.get(plugin_id=related_id)
        except CollectorPluginMeta.DoesNotExist:
            return []

        base_metric["related_id"] = related_id
        version = plugin.current_version
        related_collect_list = CollectConfigMeta.objects.filter(plugin=plugin)

        # 没有采集配置下发指标不需显示
        if len(related_collect_list) == 0:
            return []

        deploy_config_list = [config.deployment_config for config in related_collect_list]
        max_period = max([config.params["collector"]["period"] for config in deploy_config_list])
        base_metric.update(
            {
                "collect_interval": max_period // 60,
                "category_display": version.info.plugin_display_name,
                "bk_biz_id": plugin.bk_biz_id,
                "related_name": version.info.plugin_display_name,
                "plugin_type": plugin.plugin_type,
                "collect_config": ";".join([config.name for config in related_collect_list]),
                "collect_config_ids": list({config.id for config in related_collect_list}),
            }
        )

        return self.get_field_metric_msg(table, base_metric)


# 当前支持的数据来源（监控、计算平台、系统事件）
SOURCE_TYPE = {
    "BKMONITOR": BkmonitorMetricCacheManager,
    "BKDATA": BkdataMetricCacheManager,
    "BASEALARM": BaseAlarmMetricCacheManager,
    "CUSTOMEVENT": CustomEventCacheManager,
    "LOGTIMESERIES": BkLogSearchCacheManager,
    "BKMONITORLOG": BkMonitorLogCacheManager,
    "CUSTOMTIMESERIES": CustomMetricCacheManager,
}
