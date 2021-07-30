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
import collections
import copy
import json
import time
from collections import defaultdict
from typing import List, Dict

import six
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.data_source import BkMonitorTimeSeriesDataSource
from constants.cmdb import TargetNodeType
from constants.strategy import TargetFieldType
from core.drf_resource.exceptions import CustomException
from core.drf_resource.base import Resource
from core.errors.errors import SqlQueryException, TableNotExistException
from api.cmdb.define import TopoTree
from bkmonitor.models import ItemModel, SnapshotHostIndex
from constants.data_source import DataSourceLabel, DataTypeLabel
from bkmonitor.models import Event, StrategyModel
from core.drf_resource import resource
from bkmonitor.utils import time_tools
from bkmonitor.utils.cache import CacheType
from bkmonitor.utils.common_utils import host_key, parse_filter_condition_dict, parse_host_id
from bkmonitor.utils.host import Host
from bkmonitor.utils.thread_backend import ThreadPool
from bkmonitor.views import serializers
from bkmonitor.views.serializers import BusinessOnlySerializer
from common.log import logger
from core.drf_resource import api
from core.drf_resource.contrib.cache import CacheResource
from monitor.constants import PROC_PORT_STATUS
from monitor_api.models import proc_port_index
from monitor_web.constants import AGENT_STATUS, EventLevel
from monitor_web.data_explorer.resources import GetSceneViewConfig
from monitor_web.models import MetricListCache
from utils.chart.metric_chart import MetricChart
from utils.host_index_backend import host_index_backend
from utils.query_data import TSDBData
from utils.time_status import TimeStats


def get_process_port_info(bk_biz_id, display_name, ip, plat_id, event_time=None):
    """
    进程端口信息
    :param bk_biz_id: 业务ID
    :param display_name: 进程显示名称
    :param ip: IP
    :param plat_id: 云区域ID
    :param event_time: 指定时间
    :return:
    {
        "status": 0
        "ports": {
            "8000": 0,
            "8001": 1
        }
    }
    """

    filter_dict = {"display_name": display_name, "ip": ip, "bk_cloud_id": plat_id}
    if event_time:
        filter_dict["time__gte"] = event_time
        filter_dict["time__lt"] = event_time + 60 * 1000

    try:
        data = TSDBData.get_data(
            table_name="{}_{}".format(bk_biz_id, proc_port_index.result_table_id),
            select_field="*",
            filter_dict=filter_dict,
            group_by_field=[],
        )
    except (TableNotExistException, SqlQueryException) as e:
        raise CustomException("{msg}: {reason}".format(msg=_("查询组件信息失败"), reason=e))

    process_port_info = {"status": PROC_PORT_STATUS.UNKNOWN, "ports": {}}

    # 格式化数据
    if not data:
        return process_port_info

    latest_data = data[-1]

    process_port_info = {
        "status": PROC_PORT_STATUS.LISTEN if latest_data[proc_port_index.item] else PROC_PORT_STATUS.NONLISTEN,
        "ports": {},
    }

    # ports
    status_mapping = {
        "listen": PROC_PORT_STATUS.LISTEN,
        "nonlisten": PROC_PORT_STATUS.NONLISTEN,
        "not_accurate_listen": PROC_PORT_STATUS.NOT_ACCURATE_LISTEN,
    }
    for key, value in list(status_mapping.items()):
        ports = json.loads(latest_data[key])
        if not ports:
            # 适配监听端口为null的情况
            continue
        for port in ports:
            if key == "not_accurate_listen":
                # not_accurate_listen 字段格式：IP:PORT
                actual_ip, actual_port = port.rsplit(":", 1)
            else:
                actual_ip, actual_port = latest_data.get("bind_ip", ""), port
            process_port_info["ports"][actual_port] = {
                "status": value,
                "config_ip": latest_data.get("bind_ip", ""),
                "actual_ip": actual_ip,
            }
    return process_port_info


def get_process_status(cc_biz_id, host_key_id=None):
    """
    获取进程状态
    """
    report_info = dict()
    filter_dict = {"bk_biz_id": str(cc_biz_id)}
    if host_key_id is not None:
        ip, bk_cloud_id = parse_host_id(host_key_id)
        filter_dict.update({"ip": ip, "bk_cloud_id": bk_cloud_id})
    try:
        data = TSDBData.get_data(
            table_name="system.proc_port",
            select_field=["last(proc_exists) as proc_exists"],
            group_by_field=["ip", "bk_cloud_id", "display_name"],
            filter_dict=filter_dict,
            limit=1,
        )
    except Exception:
        data = []

    for point in data:
        plat_id = str(point.get("bk_cloud_id", "0"))
        key = host_key(ip=point["ip"], plat_id=plat_id)
        status = AGENT_STATUS.ON if point["proc_exists"] else AGENT_STATUS.OFF
        report_info.setdefault(key, {}).update({point["display_name"]: status})
    return report_info


class GetFieldValuesByIndexIdResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(default=0, label=_lazy("业务ID"))
        index_id = serializers.IntegerField(required=True, label=_lazy("指标ID"))
        field = serializers.CharField(required=True, label=_lazy("查询的维度字段"))
        condition = serializers.JSONField(default={}, label=_lazy("查询条件"))

    def perform_request(self, data):
        index_obj = host_index_backend.get_host_index(id=data["index_id"])
        rt_id = index_obj.result_table_id.replace("_", ".", 1)
        condition = data["condition"]
        # 查询条件中的bk_cloud_id转换成字符串类型
        if "ip_list" in condition:
            condition["ip_list"] = [
                {
                    "bk_target_ip": host.get("bk_target_ip") or host["ip"],
                    "bk_target_cloud_id": str(host.get("bk_target_cloud_id") or host["bk_cloud_id"]),
                }
                for host in condition["ip_list"]
            ]
        if "bk_cloud_id" in condition:
            condition["bk_target_cloud_id"] = str(condition["bk_cloud_id"])
            del condition["bk_cloud_id"]
        if "ip" in condition:
            condition["bk_target_ip"] = condition["ip"]
            del condition["ip"]

        data_source = BkMonitorTimeSeriesDataSource(
            table=rt_id,
            filter_dict=data["condition"],
            metrics=[{"field": index_obj.item, "method": "COUNT"}],
            bk_biz_id=data["bk_biz_id"],
        )
        values = data_source.query_dimensions(dimension_field=data["field"])

        # 过滤网络设备'lo'
        if index_obj.category == "net" and index_obj.dimension_field:
            values = [x for x in values if x != "lo"]
        values = list(set(values))
        return values


class AgentStatusResource(Resource):
    class RequestSerializer(BusinessOnlySerializer):
        host_id = serializers.CharField(required=True, label=_lazy("主机ID"))

    @staticmethod
    def get_agent_status_by_hostid(cc_biz_id, hosts):
        """
        获取agent状态信息
        agent状态详细分成4个状态：正常，离线，未安装。已安装，无数据。
        """
        agent_status_info = resource.cc.agent_status(cc_biz_id, hosts)

        from utils.host_index_backend import host_index_backend

        report_info = host_index_backend.data_report_info(cc_biz_id, hosts)

        for host_id in hosts:
            agent_status = agent_status_info.get(host_id, AGENT_STATUS.UNKNOWN)
            # 如果agent在线，检查最近上报是否有数据
            if agent_status == AGENT_STATUS.ON and not report_info.get(host_id):
                agent_status = AGENT_STATUS.NO_DATA
            agent_status_info[host_id] = agent_status
        return agent_status_info

    def perform_request(self, validated_request_data):
        host_id = validated_request_data["host_id"]
        bk_biz_id = validated_request_data["bk_biz_id"]
        agent_status = self.get_agent_status_by_hostid(bk_biz_id, Host.create_host_list(host_id)).get(host_id)
        return {"status": agent_status}


# 新的告警计数
class HostAlarmCountResource(Resource):
    class RequestSerializer(serializers.Serializer):
        host_id_list = serializers.CharField(required=True, label=_lazy("主机ID（批量）"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        days = serializers.IntegerField(required=False, default=7, label=_lazy("查询时间"))

    def perform_request(self, validated_request_data):
        host_id_list = validated_request_data["host_id_list"]
        days = validated_request_data["days"]
        host_id_list = host_id_list.split(",")
        bk_biz_id = validated_request_data["bk_biz_id"]

        events = resource.alert_events.query_events(
            bk_biz_ids=[bk_biz_id],
            days=days,
            conditions=[{"key": "event_status", "value": [Event.EventStatus.ABNORMAL]}],
        )

        alarm_count_info = {}
        for event in events:
            ip_temp = event.origin_alarm.get("data", {})
            if ip_temp["dimensions"].get("bk_target_ip", "") and ip_temp["dimensions"].get("bk_target_cloud_id", ""):
                host_ip = "{}|{}".format(
                    ip_temp["dimensions"].get("bk_target_ip", ""), ip_temp["dimensions"].get("bk_target_cloud_id", "")
                )
            else:
                host_ip = "{}|{}".format(
                    ip_temp["dimensions"].get("ip", ""), ip_temp["dimensions"].get("bk_cloud_id", "")
                )
            # 判断查询的ip是否在有错误的ip详情中 {}
            if host_ip not in alarm_count_info:
                # 不在就变成{
                #           ip:{level:{'alarm_cnt': 1}}
                #           }
                alarm_count_info[host_ip] = {
                    1: {"alarm_cnt": 0},
                    2: {"alarm_cnt": 0},
                    3: {"alarm_cnt": 0},
                }

            alarm_count_info[host_ip][event.level]["alarm_cnt"] += 1

        # 删除不在查询的主机id的信息
        for k in list(alarm_count_info.keys()):
            if k not in host_id_list:
                del alarm_count_info[k]

        return alarm_count_info


class HostIndexResource(Resource):
    def perform_request(self, validated_request_data):
        def index_to_dict(host_index_obj, dimension_field_value=""):
            metric_display = host_index_obj.metric if get_language() == "en" else host_index_obj.desc
            *result_table_id, metric_field = host_index_obj.metric.split(".")
            result_table_id = ".".join(result_table_id)

            return {
                "description": metric_display,
                "category": host_index_obj.get_category_display(),
                "dimension_field": host_index_obj.dimension_field,
                "dimension_field_value": dimension_field_value,
                "index_id": host_index_obj.id,
                "result_table_id": result_table_id,
                "metric_field": metric_field,
                "unit_display": host_index_obj.unit_display,
                "category_id": host_index_obj.category,
                "os": [x for x in ["linux", "windows", "aix"] if getattr(host_index_obj, "is_%s" % x)],
            }

        index_info = host_index_backend.get_bp_graph_index()
        bp_index_list = [_index for index_list in list(index_info.values()) for _index in index_list]

        all_graphs = [index_to_dict(bp_index) for bp_index in bp_index_list]
        categories_sorted_list = [i[1] for i in SnapshotHostIndex.CATEGORY_CHOICES]
        all_graphs = sorted(
            all_graphs,
            # 比特流量排在网络指标最前面
            key=lambda x: categories_sorted_list.index(x["category"]) - int("_bit" in x["metric_field"]) * 0.1
            if x["category"] in categories_sorted_list
            else 10000,
        )

        return all_graphs


class HostComponentInfoResource(Resource):
    class RequestSerializer(BusinessOnlySerializer):
        ip = serializers.CharField(required=True, label=_lazy("IP"))
        bk_cloud_id = serializers.CharField(required=True, label=(_lazy("云区域ID")))
        name = serializers.CharField(required=True, label=_lazy("组件名称"))
        bk_biz_id = serializers.CharField(required=True, label=_lazy("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        comp_name = validated_request_data["name"]
        ip = validated_request_data["ip"]
        bk_cloud_id = validated_request_data["bk_cloud_id"]
        host_id = host_key(ip=ip, bk_cloud_id=bk_cloud_id)
        ip, plat_id = parse_host_id(host_id)
        plat_id = resource.cc.plat_id_cc_to_gse(plat_id)
        return resource.performance.get_process_port_info(bk_biz_id, comp_name, ip, plat_id)


class HostPerformanceResource(CacheResource):
    """
    获取主机列表信息
    """

    cache_type = CacheType.HOST

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_lazy("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data.get("bk_biz_id")
        return_value = self.get_host_performance_info(bk_biz_id)
        return return_value

    def bulk_request_performance_data(self, bk_biz_id, output, pool):
        def get_single_data(item, category, result_table_id, key_name):
            hostindex = SnapshotHostIndex.objects.get(item=item, category=category, result_table_id=result_table_id)
            method = "max" if category == "disk" else "last"
            filter_dict = {}
            if settings.USE_DISK_FILTER and category == "disk" and result_table_id == "system_disk":
                disk_filter_conditions = [{"method": "!=", "sql_statement": settings.FILE_SYSTEM_TYPE_IGNORE}]
                for condition_item in disk_filter_conditions:
                    filter_key, condition_val = parse_filter_condition_dict(
                        condition_item, settings.FILE_SYSTEM_TYPE_FIELD_NAME
                    )
                    if all([filter_key, condition_val]):
                        for condition in condition_val:
                            filter_dict.setdefault(filter_key, []).append(condition)
            filter_dict.update({"bk_biz_id": str(bk_biz_id)})
            data = TSDBData.get_data_with_cache(
                table_name=hostindex.result_table_id.replace("_", ".", 1),
                select_field="{}({}) as {}".format(method, hostindex.item, hostindex.item),
                filter_dict=filter_dict,
                group_by_field=["ip", "bk_cloud_id"],
            )

            output[key_name] = TSDBData.parse_hostindex_data_result(
                data[::-1],
                item_field=hostindex.item,
                dimension_field=None,
                conversion=hostindex.conversion,
                unit_display=hostindex.unit_display,
            ).get(hostindex.item, {})

        for i in [
            ("usage", "cpu", "system_cpu_summary", "cpu_usage_info"),
            ("load5", "cpu", "system_load", "cpu_load_info"),
            ("util", "disk", "system_io", "io_util_info"),
            ("in_use", "disk", "system_disk", "disk_in_use"),
            ("psc_pct_used", "mem", "system_mem", "psc_mem_usage_info"),
            ("pct_used", "mem", "system_mem", "mem_usage_info"),
        ]:
            pool.apply_async(get_single_data, i)

    def get_host_performance_info(self, bk_biz_id):
        data = {
            "hosts": [],
            "update_time": time_tools.now(),
        }
        ts = TimeStats("get_host_info_list")
        performance_data = collections.defaultdict(dict)
        pool = ThreadPool()
        self.bulk_request_performance_data(bk_biz_id, performance_data, pool)
        hosts_process_port_status_future = pool.apply_async(resource.performance.get_process_status, (bk_biz_id,))
        # 获取所有主机信息（前台分页）
        ts.split(_("获取主机列表和对应agent状态"))
        hosts, hosts_agent_status, no_use = resource.cc.get_host_and_status(bk_biz_id)
        if not hosts:
            return data
        ts.split(_("并发拉取进程端口状态信息和性能数据"))

        # 并发拉取进程端口状态信息：（内部版无需进程端口）
        hosts_process_port_info = {}
        hosts_process_port_status = {}
        host_id_mapping_ip = {host["bk_host_id"]: host.host_id for host in hosts}
        hosts_process_port_info_future = pool.apply_async(
            resource.cc.process_port_info, (bk_biz_id, host_id_mapping_ip, 20)
        )
        pool.close()
        pool.join()

        try:
            hosts_process_port_status = hosts_process_port_status_future.get()
            hosts_process_port_info.update(hosts_process_port_info_future.get())
        except Exception as e:
            logger.exception(e)
        ts.split(_("对同一主机同名进程去重"))
        # 对同一主机同名进程去重
        for host_id, process_port_info in six.iteritems(hosts_process_port_info):
            hosts_process_port_info[host_id] = list({p.name: p for p in process_port_info}.values())
        ts.split(_("获取告警事件数量"))
        # 获取告警事件数量
        host_id_list = list(host_id_mapping_ip.values())
        alarm_count_info = resource.performance.host_alarm_count(
            host_id_list=",".join(host_id_list), bk_biz_id=bk_biz_id
        )

        try:
            ts.split(_("处理整合所有数据"))
            return self.integrate_host_data(
                data,
                hosts,
                hosts_agent_status,
                hosts_process_port_info,
                performance_data,
                alarm_count_info,
                hosts_process_port_status,
            )
        except Exception as e:
            logger.exception(_("拉取主机性能信息失败: %s") % e)
            raise CustomException(_("系统错误：请联系管理员"))
        finally:
            ts.stop()
            time_stats_info = ts.display()
            logger.warning(time_stats_info)

    def integrate_host_data(
        self,
        data,
        hosts,
        hosts_agent_status,
        hosts_process_port_info,
        performance_data,
        alarm_count_info,
        hosts_process_port_status,
    ):
        host_list = list()
        for host in hosts:
            # 基础性能数据
            host.cpu_usage = performance_data["cpu_usage_info"].get(host.host_id, {"val": None}).get("val")
            host.cpu_single_usage = (
                performance_data["cpu_single_usage_info"].get(host.host_id, {"val": None}).get("val")
            )
            host.cpu_load = performance_data["cpu_load_info"].get(host.host_id, {"val": None}).get("val")
            host.psc_mem_usage = performance_data["psc_mem_usage_info"].get(host.host_id, {"val": None}).get("val")
            host.mem_usage = performance_data["mem_usage_info"].get(host.host_id, {"val": None}).get("val")
            host.io_util = performance_data["io_util_info"].get(host.host_id, {"val": None}).get("val")
            value_disk_in_use = performance_data["disk_in_use"].get(host.host_id, {"val": None}).get("val")
            if isinstance(value_disk_in_use, list):
                # 有多个维度的情况，取所有维度的最大值
                host.disk_in_use = max([max(v.values()) for v in value_disk_in_use])
            else:
                host.disk_in_use = value_disk_in_use
            if host.io_util and isinstance(host.io_util, list):
                io_util = dict()
                for _io_util in host.io_util:
                    for k, v in six.iteritems(_io_util):
                        io_util[k] = v
                host.io_util = max(io_util.values())

            host.status = hosts_agent_status.get(host.host_id, AGENT_STATUS.UNKNOWN)
            index_list = [host.cpu_usage, host.cpu_single_usage, host.cpu_load, host.io_util]
            if host.status == AGENT_STATUS.ON and not any(index_list):
                host.status = AGENT_STATUS.NO_DATA

            # 组件服务
            host.component = []
            component_list = [
                {
                    "display_name": item.name,
                    "ports": getattr(item, "ports", []),
                    "protocol": getattr(item, "protocol", []),
                    "status": hosts_process_port_status.get(host.host_id, {}).get(item.name, item.status),
                }
                for item in hosts_process_port_info.get(host.host_id) or []
            ]
            host.component += component_list
            # 告警数
            alarm_count = []
            alarm_level = set()
            for key, value in list(alarm_count_info.get(host.host_id, {}).items()):
                alarm_count.append({"level": int(key), "count": value["alarm_cnt"]})
                alarm_level.add(int(key))
            alarm_count.sort(key=lambda x: x["level"])
            host.alarm_count = alarm_count
            host.region = host.bk_province_name

            # 删除不必返回的数据
            for key, value in list(vars(host).items()):
                if key not in [
                    "bk_host_innerip",
                    "bk_host_outerip",
                    "bk_cloud_id",
                    "bk_host_name",
                    "bk_os_type",
                    "bk_os_name",
                    "region",
                    "status",
                    "bk_biz_id",
                    "bk_biz_name",
                    "alarm_count",
                    "cpu_load",
                    "cpu_usage",
                    "cpu_single_usage",
                    "mem_usage",
                    "psc_mem_usage",
                    "io_util",
                    "module",
                    "component",
                    "bk_cloud_name",
                    "disk_in_use",
                ]:
                    delattr(host, key)

            host.bk_cloud_id = host.bk_cloud_id[0]["bk_inst_id"]
            host_list.append(host)
        host_list.sort(key=lambda x: x.status, reverse=True)
        data["hosts"] = [x.to_dict() for x in host_list]
        return data


class GraphPointResource(Resource):
    class RequestSerializer(serializers.Serializer):
        class IpListSlz(serializers.Serializer):
            ip = serializers.CharField(required=True, label=_lazy("主机IP"))
            bk_cloud_id = serializers.IntegerField(required=True, label=_lazy("云区域ID"))

            def validate_bk_cloud_id(self, value):
                return str(value)

        bk_biz_id = serializers.CharField(default=0, label=_lazy("业务ID"))
        time_range = serializers.CharField(required=False, label=_lazy("时间范围"))
        ip_list = IpListSlz(required=True, many=True, label=_lazy("主机列表"))
        index_id = serializers.IntegerField(required=True, label=_lazy("指标ID"))
        dimension_field = serializers.CharField(default="", label=_lazy("条件字段"), allow_blank=True)
        dimension_field_value = serializers.CharField(default="", label=_lazy("条件字段取值"), allow_blank=True)
        group_fields = serializers.ListField(default=[], label=_lazy("维度字段"))
        filter_dict = serializers.JSONField(default={}, label=_lazy("额外过滤参数"))
        time_step = serializers.IntegerField(required=False)

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        time_range = validated_request_data.get("time_range")
        ip_list = validated_request_data["ip_list"]
        index_id = validated_request_data["index_id"]
        group_fields = validated_request_data["group_fields"]
        dimension_field = validated_request_data["dimension_field"]
        dimension_field_value = validated_request_data["dimension_field_value"]
        filter_dict = validated_request_data["filter_dict"]

        index_obj = host_index_backend.get_host_index(id=index_id)

        # 时间解析
        start, end = time_tools.parse_time_range(time_range)

        kwargs = {"ip_list": ip_list}

        result_table_id = index_obj.result_table_id
        # 转为全业务rt_id
        rt_id = result_table_id.replace("_", ".", 1)
        if not group_fields:
            if index_obj.category == "process":
                group_fields = []
            else:
                group_fields = [index_obj.dimension_field] if index_obj.dimension_field else []

        if dimension_field and dimension_field_value:
            kwargs[dimension_field] = dimension_field_value
        if settings.USE_ETH_FILTER and index_obj.category == "net" and group_fields:
            for field in group_fields:
                for condition_item in settings.ETH_FILTER_CONDITION_LIST:
                    filter_key, condition_val = parse_filter_condition_dict(condition_item, field)
                    if all([filter_key, condition_val]):
                        kwargs.setdefault(filter_key, []).append(condition_val)

        if settings.USE_DISK_FILTER and index_obj.category == "disk" and group_fields:
            disk_filter_conditions = [{"method": "!=", "sql_statement": settings.FILE_SYSTEM_TYPE_IGNORE}]
            for condition_item in disk_filter_conditions:
                filter_key, condition_val = parse_filter_condition_dict(
                    condition_item, settings.FILE_SYSTEM_TYPE_FIELD_NAME
                )
                if all([filter_key, condition_val]):
                    kwargs.setdefault(filter_key, []).append(condition_val)

        kwargs.update(filter_dict)

        # series_name = resource.commons.get_desc_by_field(rt_id, index_obj.desc) or index_obj.desc
        time_step = validated_request_data["time_step"] if validated_request_data.get("time_step") else 0

        chart = MetricChart(
            bk_biz_id=bk_biz_id,
            method="MAX",
            monitor_field=index_obj.item,
            result_table_id=rt_id,
            filter_dict=kwargs,
            group_by_list=group_fields,
            time_start=start * 1000,
            time_end=end * 1000,
            unit=index_obj.conversion_unit,
            conversion=index_obj.conversion,
            # series_name=series_name,
            time_step=time_step,
            use_short_series_name=True,
        )
        data = chart.get_chart()

        # 使用"ip | bk_cloud_id"作为维度展示时，当不存在相同的ip，就不展示bk_cloud_id
        if set(group_fields) == {"ip", "bk_cloud_id"}:
            series_name = set()
            for item in data["series"]:
                series_name.add(item["name"])

            ip_list = [x.split(" | ")[0] for x in series_name]
            ip_set = set(ip_list)
            is_duplicate_ip = False if len(ip_list) == len(ip_set) else True

            if not is_duplicate_ip:
                for item in data["series"]:
                    item["name"] = item["name"].split(" | ")[0]

        data["series"].sort(key=lambda d: d["name"])
        data = {"data": data, "update_time": time_tools.now()}

        return data


class CCTopoTreeResource(Resource):
    RequestSerializer = BusinessOnlySerializer

    many_response_data = True

    def perform_request(self, data):
        bk_biz_id = data["bk_biz_id"]

        result = resource.cc.topo_tree(bk_biz_id)
        if result:
            return result["child"]
        else:
            return []


class HostPerformanceDetailResource(Resource):
    class RequestSerializer(serializers.Serializer):
        ip = serializers.CharField(required=True, label=_lazy("IP"))
        bk_cloud_id = serializers.IntegerField(required=False, label=_lazy("云区域ID"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务id"))

    def perform_request(self, validated_request_data):
        ip = validated_request_data["ip"]
        bk_cloud_id = validated_request_data.get("bk_cloud_id")
        bk_biz_id = validated_request_data["bk_biz_id"]
        res = self.get_performance_info(ip, bk_cloud_id, bk_biz_id)
        return res

    @classmethod
    def get_strategy_configs(cls, bk_biz_id):
        strategies = StrategyModel.objects.filter(bk_biz_id=bk_biz_id).values("id", "is_enabled")
        strategy_configs = {}
        for strategy in strategies:
            strategy_configs[strategy["id"]] = {"is_enabled": strategy["is_enabled"], "targets": []}

        items = ItemModel.objects.filter(strategy_id__in=list(strategy_configs.keys())).values("strategy_id", "target")

        for item in items:
            target = item["target"]
            if not target:
                continue
            if not target[0]:
                continue
            strategy_configs[item["strategy_id"]]["targets"].append(target)
        return strategy_configs

    def count_host_strategy(self, host, bk_biz_id):
        """
        通知含有该主机的策略
        """
        strategy_configs = self.get_strategy_configs(bk_biz_id)

        enable_count = 0
        disabled_count = 0

        # 补充拓扑信息
        host_modules = [f"module|{module}" for module in host.bk_module_ids]
        topo_tree = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)  # type: TopoTree
        topo_link = topo_tree.convert_to_topo_link()
        # 获得该主机所有拓扑模块
        topo_set = set()
        for module in host_modules:
            topo_set.update({link.id for link in topo_link[module]})

        for strategy_config in list(strategy_configs.values()):
            is_matched = False
            for target in strategy_config["targets"]:
                # 如果已经匹配，则退出
                if is_matched:
                    break

                # 如果是动态拓扑
                if target[0][0]["field"] == "host_topo_node":
                    target_topos = {f'{obj["bk_obj_id"]}|{obj["bk_inst_id"]}' for obj in target[0][0]["value"]}
                    if target_topos.intersection(topo_set):
                        is_matched = True
                        if strategy_config["is_enabled"]:
                            enable_count += 1
                        else:
                            disabled_count += 1

                # 如果是模板
                if "template" in target[0][0]["field"]:
                    template_type = (
                        TargetNodeType.SERVICE_TEMPLATE
                        if ("service_template" in target[0][0]["field"])
                        else TargetNodeType.SET_TEMPLATE
                    )
                    template_hosts = api.cmdb.get_host_by_template(
                        dict(
                            bk_biz_id=bk_biz_id,
                            bk_obj_id=template_type,
                            template_ids=[template["bk_inst_id"] for template in target[0][0]["value"]],
                        )
                    )
                    if host in template_hosts:
                        is_matched = True
                        if strategy_config["is_enabled"]:
                            enable_count += 1
                        else:
                            disabled_count += 1

                # 如果是静态IP
                target_values = target[0][0]["value"]
                for value in target_values:
                    # 非主机目标直接退出
                    if "bk_target_ip" not in value:
                        break
                    if (value["bk_target_ip"], value.get("bk_target_cloud_id", 0)) == (host.ip, host.bk_cloud_id):
                        is_matched = True
                        if strategy_config["is_enabled"]:
                            enable_count += 1
                        else:
                            disabled_count += 1
                        break
        return {"enabled": enable_count, "disabled": disabled_count}

    def get_performance_info(self, ip, bk_cloud_id, bk_biz_id):
        if bk_cloud_id is None:
            hosts = api.cmdb.get_host_by_ip(ips=[dict(ip=ip)], bk_biz_id=bk_biz_id)
        else:
            hosts = api.cmdb.get_host_by_ip(ips=[dict(ip=ip, bk_cloud_id=bk_cloud_id)], bk_biz_id=bk_biz_id)

        if not hosts:
            raise CustomException(_("查询无主机{ip}:{bk_cloud_id}，请确认主机是否存在").format(ip=ip, bk_cloud_id=bk_cloud_id))

        host = hosts[0]
        bk_cloud_id = host.bk_cloud_id

        host_id = host_key(ip=ip, bk_cloud_id=bk_cloud_id)
        api.cmdb.full_host_topo_inst(bk_biz_id, [host])

        try:
            status = api.gse.get_agent_status(hosts=[dict(ip=ip, bk_cloud_id=bk_cloud_id)])
        except Exception as e:
            logger.exception("get agent status failed: host: {}|{}, reason: {}".format(ip, bk_cloud_id, e))
            status = {}
        exist = status.get("{}:{}".format(bk_cloud_id, ip), {}).get("bk_agent_alive", AGENT_STATUS.UNKNOWN)
        host.status = AGENT_STATUS.ON if exist else AGENT_STATUS.NOT_EXIST

        alarm_count_info = resource.performance.host_alarm_count(host_id_list=host_id, bk_biz_id=bk_biz_id)
        host.alarm_count = 0

        if host_id in alarm_count_info:
            for i in EventLevel.EVENT_LEVEL:
                host.alarm_count += alarm_count_info[host_id][i[0]]["alarm_cnt"]

        host.alarm_strategy = self.count_host_strategy(host, bk_biz_id)
        host_performance_data = self.get_host_performance_data(ip, bk_cloud_id)
        cpu_usage = host_performance_data["cpu_usage"]
        mem_usage = host_performance_data["mem_usage"]
        disk_usage = host_performance_data["disk_usage"]
        speed_recv = host_performance_data["net"]["speed_recv"]
        speed_sent = host_performance_data["net"]["speed_sent"]
        component_count = host_performance_data["component_count"]
        index_list = [
            cpu_usage["val"],
            mem_usage["val"],
            disk_usage["val"],
            speed_recv["val"],
            speed_sent["val"],
            component_count["val"],
        ]
        if host.status == AGENT_STATUS.ON and not any(index_list):
            host.status = AGENT_STATUS.NO_DATA

        business = api.cmdb.get_business(bk_biz_ids=[bk_biz_id])
        if business:
            bk_biz_name = business[0].bk_biz_name
        else:
            bk_biz_name = bk_biz_id

        return_data = {
            "bk_host_id": host.bk_host_id,
            "bk_host_innerip": host.bk_host_innerip,
            "bk_host_outerip": host.bk_host_outerip,
            "bk_cloud_id": host.bk_cloud_id,
            "bk_cloud_name": host.bk_cloud_name,
            "bk_host_name": host.bk_host_name,
            "bk_os_name": host.bk_os_name,
            "bk_os_type": host.bk_os_type,
            "region": host.bk_province_name,
            "bk_biz_id": bk_biz_id,
            "bk_biz_name": bk_biz_name,
            "module": host.module,
            "status": host.status,
            "cpu_usage": cpu_usage,
            "mem_usage": mem_usage,
            "disk_usage": disk_usage,
            "net": {"speed_recv": speed_recv, "speed_sent": speed_sent},
            "component_count": component_count,
            "alarm_count": host.alarm_count,
            "alarm_strategy": host.alarm_strategy,
            "bk_state": host.bk_state,
        }

        return return_data

    def get_host_performance_data(self, ip, bk_cloud_id):
        res_data = host_index_backend.get_data_by_host(ip, bk_cloud_id)
        if res_data["disk_usage"] and isinstance(res_data["disk_usage"].get("val"), list):
            io_util = dict()
            for _io_util in res_data["disk_usage"]["val"]:
                for k, v in six.iteritems(_io_util):
                    io_util[k] = v
            res_data["disk_usage"]["val"] = max(io_util.values())

        for key, value in list(res_data["net"].items()):
            if not value.get("val"):
                continue
            # 忽略网络设备'lo'
            speed_dict = [x for x in value["val"] if list(x.keys())[0] != "lo"]
            all_speed = []
            for speed in speed_dict:
                all_speed.append(list(speed.values())[0])
            res_data["net"][key]["val"] = max(all_speed)
            res_data["net"][key] = self.convert_net_unit(res_data["net"][key])
        return res_data

    def convert_net_unit(self, net_info):
        """
        动态转换网络类型单位
        """
        unit_list = resource.strategies.get_unit_info(unit_id="kbytes")
        converted_net_unit = net_info
        for unit_info in unit_list["unit_series"][::-1]:
            converted_value = net_info["val"] / unit_info["unit_conversion"]
            converted_net_unit = {
                "unit": "{}/s".format(unit_info["unit"]),
                "val": round(converted_value, 2),
            }
            if converted_value >= 1.0:
                # 第一个大于除后大于1的单位，直接返回
                return converted_net_unit
        # 如果都没匹配上，直接返回原值
        return converted_net_unit


class HostTopoNodeDetailResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务id"))
        bk_obj_id = serializers.CharField(required=True, label=_("节点类型"))
        bk_inst_id = serializers.IntegerField(required=True, label=_("节点实例ID"))

    def get_alarm_count(self, bk_biz_id, host_list):
        if not host_list:
            return 0

        alarm_count_info = resource.performance.host_alarm_count(
            host_id_list=",".join([host.host_id for host in host_list]), bk_biz_id=bk_biz_id
        )
        if not alarm_count_info:
            return 0

        alarm_count = 0
        for no_use, alarm_info in alarm_count_info.items():
            for level, level_name in EventLevel.EVENT_LEVEL:
                alarm_count += alarm_info[level]["alarm_cnt"]
        return alarm_count

    def get_strategy_count(self, bk_biz_id, bk_obj_id, bk_inst_id):
        topo_node_id = f"{bk_obj_id}|{bk_inst_id}"

        strategy_configs = HostPerformanceDetailResource.get_strategy_configs(bk_biz_id)
        template_id = 0
        if bk_obj_id == "set":
            sets = api.cmdb.get_set(bk_set_ids=[bk_inst_id], bk_biz_id=bk_biz_id)
            if sets:
                template_id = getattr(sets[0], "set_template_id", 0)
        elif bk_obj_id == "module":
            modules = api.cmdb.get_module(bk_module_ids=[bk_inst_id], bk_biz_id=bk_biz_id)
            if modules:
                template_id = getattr(modules[0], "service_template_id", 0)

        enable_count = 0
        disabled_count = 0
        for strategy_config in list(strategy_configs.values()):
            for target in strategy_config["targets"]:
                is_matched = False

                target_type = target[0][0]["field"]
                # 如果是动态拓扑
                if target_type in [TargetFieldType.host_topo, TargetFieldType.service_topo]:
                    target_topos = {f'{obj["bk_obj_id"]}|{obj["bk_inst_id"]}' for obj in target[0][0]["value"]}
                    if topo_node_id in target_topos:
                        is_matched = True
                # 如果是服务模板 或者 集群模板
                elif (
                    target_type in [TargetFieldType.host_service_template, TargetFieldType.service_service_template]
                    and bk_obj_id == "module"
                ) or (
                    target_type in [TargetFieldType.host_set_template, TargetFieldType.service_set_template]
                    and bk_obj_id == "set"
                ):
                    template_ids = [template["bk_inst_id"] for template in target[0][0]["value"]]
                    if template_id in template_ids:
                        is_matched = True

                if not is_matched:
                    continue

                if strategy_config["is_enabled"]:
                    enable_count += 1
                else:
                    disabled_count += 1
                break

        return {"enabled": enable_count, "disabled": disabled_count}

    def perform_request(self, validated_request_data):
        bk_obj_id = validated_request_data["bk_obj_id"]
        bk_inst_id = validated_request_data.get("bk_inst_id")
        bk_biz_id = validated_request_data["bk_biz_id"]
        topo_nodes = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id).get_all_nodes_with_relation()

        node = None
        for n in topo_nodes.values():
            if n.bk_obj_id == bk_obj_id and n.bk_inst_id == bk_inst_id:
                node = n
                break

        host_list = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id, topo_nodes={bk_obj_id: [bk_inst_id]})

        return_data = {
            "bk_obj_id": bk_obj_id,
            "bk_inst_id": bk_inst_id,
            "bk_obj_name": node.bk_obj_name if node else "",
            "bk_inst_name": node.bk_inst_name if node else "",
            "operator": [],
            "bk_bak_operator": [],
            "child_count": len(host_list) if bk_obj_id == "module" else len(node.child),
            "host_count": len(host_list),
            "alarm_count": self.get_alarm_count(bk_biz_id, host_list),
            "alarm_strategy": self.get_strategy_count(bk_biz_id, bk_obj_id, bk_inst_id),
        }

        # 如果是模块，则补充"主备负责人"信息
        if bk_obj_id == "module":
            modules = api.cmdb.get_module(bk_biz_id=bk_biz_id, bk_module_ids=[bk_inst_id])
            if modules:
                m = modules[0]
                return_data.update({"operator": m.operator, "bk_bak_operator": m.bk_bak_operator})
        return return_data


class HostProcessStatusResource(Resource):
    class RequestSerializer(serializers.Serializer):
        ip = serializers.CharField(required=True, label=_lazy("IP"))
        bk_cloud_id = serializers.IntegerField(required=True, label=_lazy("云区域ID"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))

    def perform_request(self, validated_request_data):
        ip = validated_request_data["ip"]
        bk_cloud_id = validated_request_data["bk_cloud_id"]
        bk_biz_id = validated_request_data["bk_biz_id"]
        ip_info = dict(ip=ip, bk_cloud_id=bk_cloud_id)
        hosts = api.cmdb.get_host_by_ip(ips=[ip_info], bk_biz_id=bk_biz_id)
        if not hosts:
            raise CustomException(_("查询无主机{host_id}，请确认主机是否存在").format(host_id=host_key(**ip_info)))
        host = hosts[0]
        host_id = host_key(ip=ip, bk_cloud_id=bk_cloud_id)
        host_id_mapping_ip = {host.bk_host_id: host_id}
        host_process_info = self.get_process_status(host.bk_biz_id, host_id, host_id_mapping_ip)
        return host_process_info

    def get_process_status(self, bk_biz_id, host_id, host_id_mapping_ip):
        result = resource.cc.process_port_info(bk_biz_id, host_id_mapping_ip)
        host_port_info = result.get(host_id, [])
        if not host_port_info:
            return []

        process_info = resource.performance.get_process_status(bk_biz_id, host_id)
        host_process_status_info = process_info.get(host_id, {})
        if host_process_status_info:
            for comp in host_port_info:
                comp_name = comp.name
                if comp_name in host_process_status_info:
                    comp.status = host_process_status_info[comp_name]
                else:
                    comp.status = AGENT_STATUS.UNKNOWN

        return_data = list()
        for info in host_port_info:
            info = {"status": info.status, "ports": info.ports, "display_name": info.name, "protocol": info.protocol}
            return_data.append(info)

        return return_data


class TopoNodeProcessStatusResource(Resource):
    """
    获取拓扑下的进程
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务id"))
        bk_obj_id = serializers.CharField(required=True, label=_("节点类型"))
        bk_inst_id = serializers.IntegerField(required=True, label=_("节点实例ID"))

    def perform_request(self, validated_request_data):
        bk_obj_id = validated_request_data["bk_obj_id"]
        bk_inst_id = validated_request_data.get("bk_inst_id")
        bk_biz_id = validated_request_data["bk_biz_id"]

        service_instances = api.cmdb.get_service_instance_by_topo_node(
            bk_biz_id=bk_biz_id, topo_nodes={bk_obj_id: [bk_inst_id]}
        )

        processes = []
        for service_instance in service_instances:
            if service_instance and service_instance.process_instances:
                processes.extend(service_instance.process_instances)
        process_list = [process["process"] for process in processes]

        return_data = list()
        process_name_list = [process_info.get("bk_process_name", "") for process_info in process_list]
        for process_name in set(process_name_list):
            # 这里status直接置灰，ports、protocol留空，只保留display_name
            info = {"status": AGENT_STATUS.UNKNOWN, "ports": [], "display_name": process_name, "protocol": ""}
            return_data.append(info)

        return return_data


class GetHostDashboardConfigResource(GetSceneViewConfig):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        type = serializers.ChoiceField(choices=(("host", "主机"), ("process", "进程")), label=_("类型"), required=True)
        compare_config = serializers.DictField(label=_("对比配置"), default=lambda: {})

    # 默认维度
    DEFAULT_DIMENSIONS = ["bk_target_ip", "bk_target_cloud_id"]
    EXCLUDE_DIMENSIONS = []
    DEFAULT_AGG_CONDITION = [
        {"key": "bk_target_ip", "method": "eq", "value": ["$bk_target_ip"]},
        {"condition": "and", "key": "bk_target_cloud_id", "method": "eq", "value": ["$bk_target_cloud_id"]},
    ]

    # 默认主机图表排序
    DEFAULT_HOST_ORDER = [
        {
            "id": "cpu",
            "title": "CPU",
            "panels": [
                {"id": "bk_monitor.time_series.system.load.load5", "hidden": False},
                {"id": "bk_monitor.time_series.system.cpu_summary.usage", "hidden": False},
                {"id": "bk_monitor.time_series.system.cpu_detail.usage", "hidden": False},
            ],
        },
        {
            "id": "memory",
            "title": _lazy("内存"),
            "panels": [
                {"id": "bk_monitor.time_series.system.mem.free", "hidden": False},
                {"id": "bk_monitor.time_series.system.swap.used", "hidden": False},
                {"id": "bk_monitor.time_series.system.mem.psc_pct_used", "hidden": False},
                {"id": "bk_monitor.time_series.system.mem.psc_used", "hidden": False},
                {"id": "bk_monitor.time_series.system.mem.used", "hidden": False},
                {"id": "bk_monitor.time_series.system.mem.process.usage", "hidden": False},
                {"id": "bk_monitor.time_series.system.swap.pct_used", "hidden": False},
            ],
        },
        {
            "id": "network",
            "title": _lazy("网络"),
            "panels": [
                {"id": "bk_monitor.time_series.system.net.speed_recv_bit", "hidden": False},
                {"id": "bk_monitor.time_series.system.net.speed_sent_bit", "hidden": False},
                {"id": "bk_monitor.time_series.system.net.speed_recv", "hidden": False},
                {"id": "bk_monitor.time_series.system.net.speed_sent", "hidden": False},
                {"id": "bk_monitor.time_series.system.net.speed_packets_sent", "hidden": False},
                {"id": "bk_monitor.time_series.system.net.speed_packets_recv", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_estab", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_timewait", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_listen", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_lastack", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_syn_recv", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_syn_sent", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_finwait1", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_finwait2", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_closing", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_closed", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_udp_indatagrams", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_udp_outdatagrams", "hidden": False},
                {"id": "bk_monitor.time_series.system.netstat.cur_tcp_closewait", "hidden": False},
            ],
        },
        {
            "id": "disk",
            "title": _lazy("磁盘"),
            "panels": [
                {"id": "bk_monitor.time_series.system.disk.in_use", "hidden": False},
                {"id": "bk_monitor.time_series.system.io.r_s", "hidden": False},
                {"id": "bk_monitor.time_series.system.io.w_s", "hidden": False},
                {"id": "bk_monitor.time_series.system.io.util", "hidden": False},
            ],
        },
        {
            "id": "process",
            "title": _lazy("系统进程"),
            "panels": [{"id": "bk_monitor.time_series.system.env.procs", "hidden": False}],
        },
    ]

    # 默认进程图表排序
    DEFAULT_PROCESS_ORDER = [
        {
            "id": "__UNGROUP__",
            "title": _lazy("未分组的指标"),
            "panels": [
                {"id": "bk_monitor.time_series.system.proc.cpu_usage_pct", "hidden": False},
                {"id": "bk_monitor.time_series.system.proc.mem_usage_pct", "hidden": False},
                {"id": "bk_monitor.time_series.system.proc.mem_res", "hidden": False},
                {"id": "bk_monitor.time_series.system.proc.mem_virt", "hidden": False},
                {"id": "bk_monitor.time_series.system.proc.fd_num", "hidden": False},
            ],
        },
    ]

    DEFAULT_METHOD = "MAX"
    # 特殊聚合方法
    METRIC_METHOD = {
        "bk_monitor.time_series.system.proc.mem_res": "SUM",
        "bk_monitor.time_series.system.proc.mem_virt": "SUM",
        "bk_monitor.time_series.system.proc.fd_num": "SUM",
    }

    DASHBOARD_TITLE = _lazy("主机监控")

    @classmethod
    def get_order_config_key(cls, params):
        return f"panel_order_{params['type']}"

    @classmethod
    def get_default_order(cls, params):
        if params["type"] == "process":
            return cls.DEFAULT_PROCESS_ORDER
        else:
            row_result_table_ids = [
                ["system.load", "system.cpu_summary", "system.cpu_detail"],
                ["system.mem", "system.swap"],
                ["system.net"],
                ["system.disk", "system.io", "system.netstat"],
            ]

            for index, result_table_ids in enumerate(row_result_table_ids):
                exists_metric_id = []
                for panel in cls.DEFAULT_HOST_ORDER[index]["panels"]:
                    exists_metric_id.append(panel["id"])

                for metric in MetricListCache.objects.filter(
                    data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                    data_type_label=DataTypeLabel.TIME_SERIES,
                    result_table_id__in=result_table_ids,
                ).values("result_table_id", "metric_field"):
                    metric_id = f"bk_monitor.time_series.{metric['result_table_id']}.{metric['metric_field']}"

                    if metric_id in exists_metric_id:
                        continue

                    cls.DEFAULT_HOST_ORDER[index]["panels"].append({"id": metric_id, "hidden": True})
            return cls.DEFAULT_HOST_ORDER

    @classmethod
    def get_query_configs(cls, params) -> List[Dict]:
        """
        获取指标信息，包含指标信息及该指标需要使用的聚合方法、聚合维度、聚合周期等
        """
        metrics = MetricListCache.objects.filter(
            bk_biz_id__in=[0, params["bk_biz_id"]],
            result_table_label="host_process" if params["type"] == "process" else "os",
            data_source_label="bk_monitor",
            data_type_label="time_series",
        )

        metric_configs = []
        default_dimensions = cls.DEFAULT_DIMENSIONS[:]
        if params["type"] == "process":
            default_dimensions.extend(["display_name", "pid"])

        for metric in metrics:
            # 如果不包含指定维度，则不使用改指标
            if {dimension["id"] for dimension in metric.dimensions} < set(default_dimensions):
                continue

            metric_id = (
                f"{metric.data_source_label}.{metric.data_type_label}"
                f".{metric.result_table_id}.{metric.metric_field}"
            )

            # 添加默认维度
            group_by = json.loads(json.dumps(default_dimensions))
            if metric.default_dimensions:
                for dimension in metric.default_dimensions:
                    if dimension in group_by or dimension in cls.EXCLUDE_DIMENSIONS:
                        continue
                    group_by.append(dimension)

            where = copy.deepcopy(cls.DEFAULT_AGG_CONDITION)
            if params["type"] == "process":
                where.append({"condition": "and", "key": "display_name", "method": "eq", "value": ["$process_name"]})
                group_by = [dimension for dimension in group_by if dimension != "pid"]

            alias = " | ".join([f"$tag_{dimension}" for dimension in group_by if dimension not in default_dimensions])

            metric_configs.append(
                {
                    "id": metric_id,
                    "metric_field": metric.metric_field,
                    "metric_field_name": metric.metric_field_name,
                    "result_table_id": metric.result_table_id,
                    "data_source_label": metric.data_source_label,
                    "data_type_label": metric.data_type_label,
                    "method": cls.METRIC_METHOD.get(metric_id, cls.DEFAULT_METHOD),
                    "interval": 60,
                    "group_by": group_by,
                    "where": where,
                    "alias": alias,
                }
            )

        return metric_configs

    @classmethod
    def add_external_panels(cls, params, dashboard):
        """
        添加额外图表
        """
        if params["type"] != "process":
            return dashboard

        panels = [
            {
                "id": "port_status",
                "type": "status",
                "title": _("端口状态"),
                "targets": [
                    {
                        "data": {
                            "ip": "$bk_target_ip",
                            "bk_cloud_id": "$bk_target_cloud_id",
                            "process_name": "$process_name",
                            "bk_biz_id": params["bk_biz_id"],
                        },
                        "datasourceId": "process_port",
                        "name": _("进程端口"),
                    }
                ],
            },
            {
                "id": "run_time",
                "type": "text",
                "title": _("运行时长"),
                "targets": [
                    {
                        "data": {
                            "metric_field": "uptime",
                            "method": "LAST",
                            "interval": 60,
                            "result_table_id": "system.proc",
                            "data_source_label": "bk_monitor",
                            "data_type_label": "time_series",
                            "group_by": ["bk_target_ip", "bk_target_cloud_id", "display_name"],
                            "bk_biz_id": params["bk_biz_id"],
                            "where": [
                                {"key": "bk_target_ip", "method": "eq", "value": ["$bk_target_ip"]},
                                {
                                    "condition": "and",
                                    "key": "bk_target_cloud_id",
                                    "method": "eq",
                                    "value": ["$bk_target_cloud_id"],
                                },
                                {"condition": "and", "key": "display_name", "method": "eq", "value": ["$process_name"]},
                            ],
                        },
                        "datasourceId": "time_series",
                        "name": _("时序数据"),
                    }
                ],
                "calc": "MAX",
            },
        ]

        panels.extend(dashboard["panels"])
        dashboard["panels"] = panels
        return dashboard

    @classmethod
    def add_target_condition(cls, params, targets: List) -> None:
        hosts = params["compare_config"].get("hosts", [])
        where = targets[0]["data"]["where"]
        targets[0]["alias"] = " | ".join([f"$tag_{dimension}" for dimension in targets[0]["data"]["group_by"]])
        for host in hosts:
            ip = host["bk_target_ip"]
            bk_cloud_id = host["bk_target_cloud_id"]

            conditions = [
                {"condition": "or", "key": "bk_target_ip", "method": "eq", "value": [ip]},
                {"condition": "and", "key": "bk_target_cloud_id", "method": "eq", "value": [bk_cloud_id]},
            ]

            if params["type"] == "process":
                conditions.append(
                    {"condition": "and", "key": "display_name", "method": "eq", "value": ["$process_name"]}
                )

            where.extend(conditions)

    @classmethod
    def add_os_type(cls, dashboard):
        """
        增加操作系统标识
        """
        panels = dashboard["panels"]
        for row in panels:
            for panel in row.get("panels", []):
                if panel["id"] not in [
                    "bk_monitor.time_series.system.swap.pct_used",
                    "bk_monitor.time_series.system.swap.used",
                    "bk_monitor.time_series.system.load.load5",
                ]:
                    continue

                panel["os_type"] = ["linux", "aix"]

    def perform_request(self, params):
        dashboard = super(GetHostDashboardConfigResource, self).perform_request(params)
        self.add_external_panels(params, dashboard)
        self.add_os_type(dashboard)
        return dashboard


class GetTopoNodeDashboardConfigResource(GetHostDashboardConfigResource):
    """
    获取主机拓扑的视图面板
    """

    DEFAULT_DIMENSIONS = ["bk_obj_id", "bk_inst_id"]
    EXCLUDE_DIMENSIONS = ["bk_target_ip", "bk_target_cloud_id"]
    DEFAULT_AGG_CONDITION = [
        {"key": "bk_obj_id", "method": "eq", "value": ["$bk_obj_id"]},
        {"condition": "and", "key": "bk_inst_id", "method": "eq", "value": ["$bk_inst_id"]},
    ]
    DEFAULT_METHOD = "$method"
    # 特殊聚合方法
    METRIC_METHOD = {}


class SearchHostInfoResource(Resource):
    """
    主机信息查询
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        # 以下参数暂未用上
        # topo_nodes = serializers.DictField(label=_lazy("拓扑节点"), child=serializers.ListField(), required=False)
        # ips = serializers.ListField(label=_lazy("主机IP信息"), child=serializers.DictField(), required=False)
        # search_outer_ip = serializers.BooleanField(label=_lazy("是否搜索外网IP"), required=False, default=False)

    def perform_request(self, params):
        # if "ips" in params:
        #     hosts = api.cmdb.get_host_by_ip(
        #         bk_biz_id=params["bk_biz_id"], search_outer_ip=params["search_outer_ip"], ips=params.get("ips", [])
        #     )
        # else:
        #     hosts = api.cmdb.get_host_by_topo_node(
        #         bk_biz_id=params["bk_biz_id"], topo_node=params.get("topo_nodes", {})
        #     )
        hosts = api.cmdb.get_host_by_topo_node(bk_biz_id=params["bk_biz_id"])
        topo_links = api.cmdb.get_topo_tree(bk_biz_id=params["bk_biz_id"]).convert_to_topo_link()

        result = []
        for host in hosts:
            result.append(
                {
                    "bk_host_id": host.bk_host_id,
                    "bk_biz_id": host.bk_biz_id,
                    "bk_cloud_id": host.bk_cloud_id,
                    "bk_cloud_name": host.bk_cloud_name,
                    "bk_host_innerip": host.bk_host_innerip,
                    "bk_host_outerip": host.bk_host_outerip,
                    "bk_os_type": host.bk_os_type,
                    "bk_os_name": host.bk_os_name,
                    "region": host.bk_province_name,
                    "bk_host_name": host.bk_host_name,
                }
            )

            modules = []
            for bk_module_id in host.bk_module_ids:
                key = f"module|{bk_module_id}"
                if key not in topo_links:
                    continue
                topo_link = topo_links[key]

                modules.append(
                    {
                        "id": f"module|{topo_link[0].bk_inst_id}",
                        "bk_inst_id": topo_link[0].bk_inst_id,
                        "bk_inst_name": topo_link[0].bk_inst_name,
                        "topo_link": [f"{node.bk_obj_id}|{node.bk_inst_id}" for node in reversed(topo_link)],
                        "topo_link_display": [node.bk_inst_name for node in reversed(topo_link)],
                    }
                )

            result[-1]["module"] = modules

        return result


class SearchHostMetricResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        ips = serializers.ListField(label=_lazy("主机IP信息"), child=serializers.DictField(), required=False)

    @staticmethod
    def get_agent_status(params, data: Dict[str, Dict]):
        agent_statuses = api.gse.get_agent_status(bk_biz_id=params["bk_biz_id"], hosts=params["ips"])
        for agent_status in agent_statuses.values():
            host_id = f"{agent_status['ip']}|{agent_status['bk_cloud_id']}"
            if agent_status["bk_agent_alive"]:
                data[host_id]["status"] = AGENT_STATUS.ON
            else:
                data[host_id]["status"] = AGENT_STATUS.OFF

    @staticmethod
    def get_performance_data(params, data: Dict[str, Dict], pool: ThreadPool):
        now = int(time.time())

        def get_metric_data(metric, _data):
            metric_data = resource.grafana.time_series_query(
                bk_biz_id=params["bk_biz_id"],
                data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
                data_type_label=DataTypeLabel.TIME_SERIES,
                metric_field=metric["metric_field"],
                method="MAX",
                interval=0,
                result_table_id=metric["result_table_id"],
                group_by=["bk_target_ip", "bk_target_cloud_id"],
                where=metric.get("where", []),
                target=params["ips"],
                start_time=now - 3 * 60,
                end_time=now,
            )

            for row in metric_data:
                host_id = f"{row['dimensions']['bk_target_ip']}|{row['dimensions']['bk_target_cloud_id']}"
                if row["datapoints"]:
                    _data[host_id][metric["field"]] = round(row["datapoints"][0][0], 2)

        metrics = [
            {"field": "cpu_load", "result_table_id": "system.load", "metric_field": "load5"},
            {"field": "cpu_usage", "result_table_id": "system.cpu_summary", "metric_field": "usage"},
            {"field": "disk_in_use", "result_table_id": "system.disk", "metric_field": "in_use"},
            {"field": "io_util", "result_table_id": "system.io", "metric_field": "util"},
            {"field": "mem_usage", "result_table_id": "system.mem", "metric_field": "pct_used"},
            {"field": "psc_mem_usage", "result_table_id": "system.mem", "metric_field": "psc_pct_used"},
        ]

        now = int(time.time())

        # 根据请求总数并发请求
        for m in metrics:
            pool.apply_async(get_metric_data, args=(m, data))

    @staticmethod
    def full_host_processes(params, output):
        bk_host_id_to_ip = {ip["bk_host_id"]: f"{ip['ip']}|{ip['bk_cloud_id']}" for ip in params["ips"]}

        processes = api.cmdb.get_process(bk_biz_id=params["bk_biz_id"])

        for process in processes:
            if process.bk_host_id not in bk_host_id_to_ip:
                continue

            host_id = bk_host_id_to_ip[process.bk_host_id]
            output[host_id][process.bk_process_name] = AGENT_STATUS.UNKNOWN

    @staticmethod
    def get_process_status(params, output):
        now = int(time.time())
        process_data = resource.grafana.time_series_query(
            bk_biz_id=params["bk_biz_id"],
            data_source_label=DataSourceLabel.BK_MONITOR_COLLECTOR,
            data_type_label=DataTypeLabel.TIME_SERIES,
            metric_field="proc_exists",
            method="MAX",
            interval=0,
            where=[],
            result_table_id="system.proc_port",
            group_by=["bk_target_ip", "bk_target_cloud_id", "display_name"],
            target=params["ips"],
            start_time=now - 3 * 60,
            end_time=now,
        )
        output.insert(0, process_data)

    def perform_request(self, params):
        data = {
            f"{ip['ip']}|{ip['bk_cloud_id']}": {
                "status": AGENT_STATUS.UNKNOWN,
                "cpu_load": None,
                "cpu_usage": None,
                "disk_in_use": None,
                "io_util": None,
                "mem_usage": None,
                "psc_mem_usage": None,
                "component": [],
            }
            for ip in params["ips"]
        }
        host_processes = defaultdict(dict)
        process_data = [[]]
        pool = ThreadPool()
        pool.apply_async(self.get_agent_status, args=(params, data))
        self.get_performance_data(params, data, pool)
        pool.apply_async(self.full_host_processes, (params, host_processes))
        pool.apply_async(self.get_process_status, (params, process_data))
        pool.close()
        pool.join()
        process_data = process_data[0]
        for row in process_data:
            dimensions = row["dimensions"]
            host_id = f"{dimensions['bk_target_ip']}|{dimensions['bk_target_cloud_id']}"
            if host_id in host_processes and dimensions["display_name"] in host_processes[host_id]:
                host_processes[host_id][dimensions["display_name"]] = (
                    AGENT_STATUS.ON if row["datapoints"][0][0] else AGENT_STATUS.OFF
                )

        for host_id in host_processes:
            if host_id not in data:
                continue

            data[host_id]["component"] = [
                {"display_name": display_name, "status": status}
                for display_name, status in host_processes[host_id].items()
            ]

        for metric in data.values():
            if metric["cpu_usage"] is None and metric["status"] != AGENT_STATUS.OFF:
                metric["status"] = AGENT_STATUS.NO_DATA

        return data
