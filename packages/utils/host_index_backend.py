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
from collections import defaultdict
from django.conf import settings

import six

from bkmonitor.models import SnapshotHostIndex
from core.drf_resource import resource
from bkmonitor.utils.cache import CacheType, using_cache
from bkmonitor.utils.common_utils import host_key, parse_filter_condition_dict
from monitor.constants import HOST_POINT_INTERVAL
from monitor_web.core.metric import Metric
from utils.chart.front_default_processor import FrontDefaultProcessor
from utils.query_data import TSDBData


class HostIndexBackendBase(six.with_metaclass(abc.ABCMeta, object)):
    @abc.abstractmethod
    def get_query_data_class(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_net_group_field(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_host_index(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def filter_host_index(self, **kwargs):
        raise NotImplementedError

    def get_bp_graph_index(self):
        # 获取需要展示的性能指标
        index_info = defaultdict(list)
        indexs = self.filter_host_index(graph_show=True)
        for index in indexs:
            index_info[index.get_category_display()].append(index)
        return index_info

    @staticmethod
    @using_cache(CacheType.DATA)
    def data_report_info(cc_biz_id, host_id_list=None):
        """
        获取主机的数据上报状态
        return：
            {
                u'127.0.0.1|3': False,
                 u'127.0.0.1|1': False,
                 u'127.0.0.2|3': False,
            }
        """
        if host_id_list is None:
            # 这里获取业务下所有主机列表
            host_id_list = {host.host_id for host in resource.cc.hosts(cc_biz_id)}

        result_tables = ["system_cpu_summary", "system_load", "system_cpu_detail", "system_io", "system_mem"]
        result_tables = ["{}_{}".format(cc_biz_id, rt) for rt in result_tables]

        data_class = host_index_backend.get_query_data_class()
        return data_class.get_hostid_status_by_result_table(hostid_list=host_id_list, result_table_list=result_tables)

    def gen_performance_graph_data(
        self,
        data,
        value_field,
        group_field,
        group_by_field_ext,
        time_range,
        series_label_show,
        result_table_id,
        conversion,
        unit,
    ):
        point_interval = HOST_POINT_INTERVAL
        if group_by_field_ext.startswith("minute"):
            minute = int(group_by_field_ext.strip("minute"))
            if not minute:
                minute = 1
            point_interval *= minute
        if group_by_field_ext == "thedate":
            point_interval *= 60 * 24

        dp = FrontDefaultProcessor(
            data_list=data,
            dimension_fields=group_field.split(","),
            series_name_prefix=series_label_show,
            result_table_id=result_table_id,
            conversion=conversion,
            unit=unit,
        )
        dp.set_full_time(time_range, point_interval)
        return dp.make_graph(count_field=value_field)


class SnapshotHostIndexBackend(HostIndexBackendBase):
    def get_query_data_class(self):
        return TSDBData

    def prepare_query_cond(self, query_cond_dict):
        exclude_key = ("graph_show", "is_deleted")
        return {k: v for k, v in six.iteritems(query_cond_dict) if str(k).lower() not in exclude_key}

    def get_host_index(self, **kwargs):
        query_cond_dict = self.prepare_query_cond(kwargs)
        return SnapshotHostIndex.objects.get(**query_cond_dict)

    def filter_host_index(self, **kwargs):
        query_cond_dict = self.prepare_query_cond(kwargs)
        return SnapshotHostIndex.objects.filter(**query_cond_dict)

    def get_net_group_field(self):
        return "device_name"

    def get_data_by_metrics(self, bk_biz_id, metric_list):
        def get_single_data(args):
            metric, result = args
            method = "max" if metric.table_name in ["disk", "io"] else "last"
            data = TSDBData.get_data_with_cache(
                table_name=resource.commons.trans_bkcloud_rt_bizid("{}_{}".format(bk_biz_id, metric.result_table_id)),
                select_field="{}({}) as {}".format(method, metric.item, metric.item),
                filter_dict={"bk_biz_id": str(bk_biz_id)},
                group_by_field=["ip", "bk_cloud_id"],
            )

            result.insert(
                0,
                TSDBData.parse_hostindex_data_result(
                    data[::-1],
                    item_field=metric.item,
                    dimension_field=None,
                    conversion=metric.conversion,
                    unit_display=metric.conversion_unit,
                ).get(metric.item, {}),
            )

        metric_objects = [Metric(metric) for metric in metric_list]

        result = defaultdict(list)

        from bkmonitor.utils.thread_backend import InheritParentThread

        th_list = [
            InheritParentThread(target=get_single_data, args=(i,))
            for i in [(metric, result[metric.metric_id]) for metric in metric_objects]
        ]
        list([t.start() for t in th_list])
        list([t.join() for t in th_list])

        return result

    def get_data_by_host(self, ip, bk_cloud_id):
        def get_single_data(args):
            filter_dict = {"ip": ip, "bk_cloud_id": str(bk_cloud_id)}
            item, category, result_table_id, ret = args
            if settings.USE_DISK_FILTER and category == "disk":
                disk_filter_conditions = [{"method": "!=", "sql_statement": settings.FILE_SYSTEM_TYPE_IGNORE}]
                for condition_item in disk_filter_conditions:
                    filter_key, condition_val = parse_filter_condition_dict(
                        condition_item, settings.FILE_SYSTEM_TYPE_FIELD_NAME
                    )
                    if all([filter_key, condition_val]):
                        for condition in condition_val:
                            filter_dict.setdefault(filter_key, []).append(condition)
            snap_table_id = result_table_id.replace(".", "_")
            hostindex = SnapshotHostIndex.objects.get(item=item, category=category, result_table_id=snap_table_id)
            data = TSDBData.get_data_with_cache(
                table_name=result_table_id,
                select_field="MEAN({}) as {}".format(hostindex.item, hostindex.item),
                filter_dict=filter_dict,
                group_by_field=["ip", "bk_cloud_id", "minute1", hostindex.dimension_field],
                order_by_field="time asc",
            )

            ret.insert(
                0,
                TSDBData.parse_hostindex_data_result(
                    data[::-1],
                    item_field=hostindex.item,
                    dimension_field=hostindex.dimension_field,
                    conversion=hostindex.conversion,
                    unit_display=hostindex.unit_display,
                ).get(hostindex.item, {}),
            )

        cpu_usage_info = [dict()]
        io_util_info = [dict()]
        mem_usage_info = [dict()]
        net_recv_info = [dict()]
        net_sent_info = [dict()]
        component_count = [dict()]
        from bkmonitor.utils.thread_backend import InheritParentThread

        th_list = [
            InheritParentThread(target=get_single_data, args=(i,))
            for i in [
                ("usage", "cpu", "system.cpu_summary", cpu_usage_info),
                ("in_use", "disk", "system.disk", io_util_info),
                ("pct_used", "mem", "system.mem", mem_usage_info),
                ("speedRecv", "net", "system.net", net_recv_info),
                ("speedSent", "net", "system.net", net_sent_info),
                ("procs", "system_env", "system.env", component_count),
            ]
        ]
        list([t.start() for t in th_list])
        list([t.join() for t in th_list])

        host_id = host_key(ip=ip, bk_cloud_id=bk_cloud_id)
        return {
            "cpu_usage": cpu_usage_info[0][host_id] if cpu_usage_info[0] else {"unit": "%", "val": None},
            "disk_usage": io_util_info[0][host_id] if io_util_info[0] else {"unit": "%", "val": None},
            "mem_usage": mem_usage_info[0][host_id] if mem_usage_info[0] else {"unit": " %", "val": None},
            "net": {
                "speed_recv": net_recv_info[0][host_id] if net_recv_info[0] else {"unit": "KiB/s", "val": None},
                "speed_sent": net_sent_info[0][host_id] if net_sent_info[0] else {"unit": "KiB/s", "val": None},
            },
            "component_count": component_count[0][host_id] if component_count[0] else {"unit": "", "val": None},
        }


host_index_backend = SnapshotHostIndexBackend()
