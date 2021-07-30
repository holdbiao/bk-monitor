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
import re
import time


import arrow
import yaml
from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils.translation import ugettext as _
from yaml import SafeDumper
from decimal import Decimal

from bkmonitor.data_source import load_data_source
from core.drf_resource.exceptions import CustomException
from core.drf_resource.base import Resource
from bkmonitor.models import Event
from core.drf_resource import resource
from bkmonitor.utils.common_utils import host_key, logger, safe_int, parse_host_id
from bkmonitor.utils.country import ISP_LIST
from bkmonitor.utils.host import Host
from bkmonitor.utils.local import with_client_operator
from bkmonitor.utils.thread_backend import InheritParentThread, ThreadPool
from bkmonitor.utils.time_tools import get_timestamp_range_by_biz_date, localtime, parse_time_range
from bkmonitor.views import serializers
from constants.data_source import DataSourceLabel, DataTypeLabel
from core.drf_resource import api
from core.errors.api import BKAPIError
from core.errors.dataapi import EmptyQueryException
from monitor_web.collecting.constant import CollectStatus
from monitor.models import UptimeCheckTaskSubscription
from monitor_web.models.uptime_check import (
    UptimeCheckGroup,
    UptimeCheckNode,
    UptimeCheckTask,
    UptimeCheckTaskCollectorLog,
)
from monitor_web.uptime_check.collector import UptimeCheckCollector
from monitor_web.uptime_check.serializers import UptimeCheckTaskSerializer
from monitor_web.uptime_check.constants import (
    BEAT_STATUS,
    RESULT_MSG,
    UPTIME_CHECK_ALLOWED_HEADERS,
    UPTIME_CHECK_AVAILABLE_DEFAULT_VALUE,
    UPTIME_CHECK_CONFIG_TEMPLATE,
    UPTIME_CHECK_DB,
    UPTIME_CHECK_MONIT_RESPONSE,
    UPTIME_CHECK_MONIT_RESPONSE_CODE,
    UPTIME_CHECK_SUMMARY_TIME_RANGE,
    UPTIME_CHECK_TASK_DETAIL_GROUP_BY_MINUTE1_TIME_RANGE,
    UPTIME_CHECK_TASK_DETAIL_TIME_RANGE,
    UPTIME_DATA_SOURCE_LABEL,
    UPTIME_DATA_TYPE_LABEL,
)
from constants.cmdb import TargetNodeType

MAX_DISPLAY_TASK = 3


def handle_response_data_list(response_data_list):
    """
    可用率计算
    多条曲线整合
    """
    # 可用率在此计算
    if not response_data_list:
        return {}

    for line in response_data_list:
        for series in line["series"]:
            # 最新的数据点有可能会是None，在此对最新数据点进行抛弃处理，再返回给前端
            data = [point for point in series["data"]]
            if len(data):
                valid_points = [point[1] for point in data if point[1] is not None]
                sum_value = sum(valid_points)
                series["avg"] = round((sum_value / max(len(valid_points), 1)) if sum_value else 0, 2)
            else:
                series["avg"] = 0
            series["data"] = data

    # 多条曲线整合到一幅图中，计算最新的max_y
    max_y = max([line["max_y"] for line in response_data_list])
    chart_group = response_data_list.pop()
    if len(response_data_list):
        for line in response_data_list:
            chart_group["series"].extend(line["series"])
    chart_group["max_y"] = max_y

    return chart_group


class UptimeCheckTaskListResource(Resource):
    """
    获取服务拨测列表
    """

    many_response_data = True

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务id"))
        task_data = serializers.ListField(required=True, label=_("拨测任务数据"))
        get_available = serializers.BooleanField(default=False, label=_("获取可用率"))
        get_task_duration = serializers.BooleanField(default=False, label=_("获取响应时间"))

    def get_groups(self, obj):
        """获取任务分组信息"""
        return [{"id": group.id, "name": group.name} for group in obj.groups.all()]

    def get_nodes(self, obj):
        """获取任务分组信息"""
        return [model_to_dict(node) for node in obj.nodes.all()]

    def query_available_or_duration(self, metric, table_name, filter_dict, ret=None):
        ret = ret or {}
        data_source_class = load_data_source(DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES)
        data_source = data_source_class(
            table=table_name,
            metrics=[
                {"field": "available", "method": "MEAN", "alias": "_available"}
                if metric == "available"
                else {"field": "task_duration", "method": "MEAN", "alias": "_task_duration"}
            ],
            group_by=["task_id"],
            filter_dict=filter_dict,
        )
        records = data_source.query_data()

        if metric == "available":
            for item in records:
                ret[int(item["task_id"])].update(available=Decimal(item["_available"]).quantize(Decimal("0.00")) * 100)
        else:
            for item in records:
                ret[int(item["task_id"])].update(
                    task_duration=Decimal(item["_task_duration"]).quantize(Decimal("0.00"))
                )

    def perform_request(self, validated_request_data):
        task_data = validated_request_data["task_data"]
        bk_biz_id = validated_request_data["bk_biz_id"]
        query_group = {}
        task_data_mapping = {}
        for task in task_data:
            protocol_data = query_group.setdefault(task.protocol, {})
            protocol_data.setdefault(task.get_period(), []).append(str(task.id))
            task_data_mapping[task.id] = task.__dict__
            url = UptimeCheckTaskSerializer.get_url(task)
            task_data_mapping[task.id].update(
                url=url,
                nodes=self.get_nodes(task),
                groups=self.get_groups(task),
                task_duration=0,
                available=0,
            )
            if not url:
                # 空目标的情况，删除这个task
                task_data_mapping.pop(task.id)

        # 多线程接口调用
        th_list = []
        for protocol, data in query_group.items():
            result_table_id = "{}_{}_{}".format(bk_biz_id, UPTIME_CHECK_DB, protocol.lower())
            # 兼容不同版本
            table_name = resource.commons.trans_bkcloud_rt_bizid(result_table_id)
            end = arrow.utcnow().timestamp
            for period, task_id_list in data.items():
                start = end - period * 300
                filter_dict = {"time__gte": start * 1000, "time__lt": end * 1000, "task_id": task_id_list}

                if validated_request_data["get_available"]:
                    th_list.append(
                        InheritParentThread(
                            target=self.query_available_or_duration,
                            args=("available", table_name, filter_dict, task_data_mapping),
                        )
                    )

                if validated_request_data["get_task_duration"]:
                    th_list.append(
                        InheritParentThread(
                            target=self.query_available_or_duration,
                            args=("task_duration", table_name, filter_dict, task_data_mapping),
                        )
                    )

        list([t.start() for t in th_list])
        list([t.join() for t in th_list])
        return list(task_data_mapping.values())

    class ResponseSerializer(serializers.ModelSerializer):
        class ConfigSlz(serializers.Serializer):
            class HostSlz(serializers.Serializer):
                ip = serializers.CharField(required=False, allow_blank=True)
                # outer_ip设为required=False,兼容此前通过文件导入的任务hosts没有传outer_ip
                outer_ip = serializers.CharField(required=False, allow_blank=True)
                target_type = serializers.CharField(required=False, allow_blank=True)

                # 动态节点
                bk_biz_id = serializers.IntegerField(required=False)
                bk_inst_id = serializers.IntegerField(required=False)
                bk_obj_id = serializers.CharField(required=False, allow_blank=True)

            # HTTP ONLY
            method = serializers.CharField(required=False)
            urls = serializers.CharField(required=False)
            headers = serializers.ListField(required=False, default=[])
            response_code = serializers.CharField(required=False, default="", allow_blank=True)
            insecure_skip_verify = serializers.BooleanField(required=False, default=False)

            # TCP&UDP
            hosts = HostSlz(required=False, many=True)
            port = serializers.CharField(required=False)

            # HTTP&UDP
            request = serializers.CharField(required=False, allow_null=True, allow_blank=True)

            # ICMP ONLY
            max_rtt = serializers.IntegerField(required=False)
            total_num = serializers.IntegerField(required=False)
            size = serializers.IntegerField(required=False)

            # COMMON
            period = serializers.IntegerField(required=True)
            response_format = serializers.CharField(required=False)
            response = serializers.CharField(required=False, allow_null=True, allow_blank=True)
            timeout = serializers.IntegerField(required=False)

        config = ConfigSlz(required=True)
        id = serializers.IntegerField(required=True)
        location = serializers.JSONField(required=True)
        nodes = serializers.ListField()
        groups = serializers.ListField()
        available = serializers.FloatField(required=True)
        task_duration = serializers.FloatField(required=True)
        url = serializers.CharField()
        create_time = serializers.DateTimeField()
        update_time = serializers.DateTimeField()

        def validate(self, data):
            if data["protocol"] == UptimeCheckTask.Protocol.HTTP:
                if not data["config"].get("method") or not data["config"].get("urls"):
                    raise CustomException("When protocol is HTTP, method and urls is required in config.")
            elif data["protocol"] == UptimeCheckTask.Protocol.ICMP:
                if not data["config"].get("hosts"):
                    raise CustomException("When protocol is ICMP, hosts is required in config.")
            else:
                if not data["config"].get("port") or not data["config"].get("hosts"):
                    raise CustomException("When protocol is TCP/UDP, hosts and port is required in config.")

            if data["protocol"] == UptimeCheckTask.Protocol.UDP or (
                data["protocol"] == UptimeCheckTask.Protocol.HTTP and data["config"]["method"] == "POST"
            ):
                if not data["config"].get("request"):
                    raise CustomException("request is required in config.")
            return data

        class Meta:
            model = UptimeCheckTask
            fields = "__all__"


class GetHttpHeadersResource(Resource):
    """
    获取HTTP任务允许设置的Header
    """

    def perform_request(self, data):
        return UPTIME_CHECK_ALLOWED_HEADERS


class GenerateYamlConfigResource(Resource):
    """
    将object的配置转换为yaml配置
    """

    class RequestSerializer(serializers.Serializer):
        config = serializers.DictField(required=True)

    def perform_request(self, data):
        # 默认情况下 SafeDumper 会将空字符在生成的yaml文件中显示成 null
        # 需要在此进行进行处理，将 null 替换为空
        SafeDumper.add_representer(
            type(None), lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", "")
        )
        try:
            yaml_content = yaml.safe_dump(
                data["config"], default_flow_style=False, encoding="utf-8", allow_unicode=True
            )
        except Exception as e:
            logger.error(_("生成yaml配置文件时出错：%s") % e)
            raise CustomException(_("生成yaml配置文件时出错：%s") % e)

        return yaml_content


class UpdateConfigResource(Resource):
    """
    向拨测节点下发最新配置
    """

    class RequestSerializer(serializers.Serializer):
        node_id = serializers.IntegerField(required=True)

    def perform_request(self, data):
        try:
            node = UptimeCheckNode.objects.get(pk=data["node_id"])
        except UptimeCheckNode.DoesNotExist:
            raise CustomException(_("不存在的节点id:%s") % data["node_id"])

        config = ""
        collector = UptimeCheckCollector(node.bk_biz_id)
        if node.is_common:
            with with_client_operator(node.update_user):
                result = collector.deploy_config(
                    [{"ip": node.ip, "plat_id": node.plat_id}], {"|".join([node.ip, str(node.plat_id)]): config}
                )
        else:
            result = collector.deploy_config(
                [{"ip": node.ip, "plat_id": node.plat_id}], {"|".join([node.ip, str(node.plat_id)]): config}
            )

        return result


class TestTaskResource(Resource):
    """
    进行拨测任务测试
    下发测试配置，采集器只执行一次数据采集，直接返回采集结果，不经过计算平台
    """

    class RequestSerializer(serializers.Serializer):
        config = serializers.DictField(required=True)
        protocol = serializers.ChoiceField(choices=("HTTP", "TCP", "UDP", "ICMP"), required=True)
        node_id_list = serializers.ListField(required=True)

    def perform_request(self, data):
        config = data["config"]
        protocol = data["protocol"]

        # 根据node_id列表获取拨测节点信息，这些信息用于选择用于测试的目标主机
        all_nodes = UptimeCheckNode.objects.filter(id__in=data["node_id_list"])
        biz_nodes = []
        common_nodes = []
        for node in all_nodes:
            if node.is_common:
                common_nodes.append(node)
            else:
                biz_nodes.append(node)

        success = []
        # 如果是非公共业务节点，则直接对这个主机列表进行下发测试
        if biz_nodes:
            # 根据特征获得采集器对象
            collector = UptimeCheckCollector(biz_nodes[0].bk_biz_id)
            node_list = [{"ip": node.ip, "plat_id": node.plat_id} for node in biz_nodes]
            # 下发测试并获取结果
            biz_result = collector.test({"config": config, "protocol": protocol}, node_list)

            if len(biz_result["failed"]):
                err_msg = ""
                for err_obj in biz_result["failed"]:
                    err_msg += _(" 节点:") + err_obj["ip"] + " - " + err_obj["errmsg"]
                raise CustomException(_("部分节点测试失败:%s") % err_msg, data=biz_result["failed"])
            success = success + biz_result["success"]

        # 如果是公共业务节点，则有可能遇到业务权限问题，所以这里采用特殊的参数下发
        if common_nodes:
            # 与biz_nodes流程相似，区别在于使用bulk_request进行了批量分发
            common_result = resource.uptime_check.common_node_operate.bulk_request(
                [
                    {
                        "operate": "test",
                        "bk_biz_id": node.bk_biz_id,
                        "update_user": node.update_user,
                        "kwargs": {
                            "task": {"config": config, "protocol": protocol},
                            "hosts": [{"ip": node.ip, "plat_id": node.plat_id}],
                        },
                    }
                    for node in common_nodes
                ]
            )

            common_failed = [r["failed"][0] for r in common_result if len(r["failed"])]
            common_success = [r["success"][0] for r in common_result if len(r["success"])]
            if len(common_failed):
                err_msg = ""
                for err_obj in common_failed:
                    err_msg += _(" 节点:") + err_obj["ip"] + " - " + err_obj["errmsg"]
                raise CustomException(_("部分节点测试失败:%s") % err_msg, data=common_failed)
            success = success + common_success

        try:
            ok_result = []
            fail_result = []
            for success_info in success:
                # 解析log_content判断脚本是否真正执行成功
                content_list = success_info.get("log_content").split("\n")
                if protocol == UptimeCheckTask.Protocol.ICMP:
                    failed_content_list = [
                        content
                        for content in content_list
                        if int(json.loads(content).get("dimensions")["error_code"]) != 0
                    ]
                else:
                    failed_content_list = [
                        content for content in content_list if json.loads(content).get("error_code") != 0
                    ]
                error_message = []
                for failed_content in failed_content_list:
                    failed_content_dict = json.loads(failed_content)
                    error_message.append(
                        "{} {} {}".format(
                            failed_content_dict.get("target_host", ""),
                            failed_content_dict.get("message", ""),
                            RESULT_MSG[str(failed_content_dict["error_code"])],
                        )
                    )

                if not failed_content_list:
                    ok_result.append(RESULT_MSG["0"])
                else:
                    node = all_nodes.filter(ip=success_info["ip"]).first()
                    fail_result.append(
                        _("node:{node}, log:{log}".format(node=node.name, log=" | ".join(error_message)))
                    )

            if len(fail_result):
                raise CustomException("\n".join(fail_result))
            else:
                return ok_result[0]

        except KeyError:
            err_msg = success[0]["log_content"]
            raise CustomException(err_msg if err_msg else _("采集器无返回"))
        except ValueError:
            raise CustomException(_("采集器返回结果校验失败，请重试"))
        except CustomException:
            raise
        except Exception as e:
            logger.error(e)
            raise CustomException(_("校验测试结果时发生异常，请联系系统管理员"))


class CommonNodeOperateResource(Resource):
    """
    默认节点操作
    """

    class RequestSerializer(serializers.Serializer):
        operate = serializers.CharField(required=True)
        bk_biz_id = serializers.IntegerField(required=True)
        update_user = serializers.CharField(required=True)
        kwargs = serializers.DictField(required=False)

    def perform_request(self, data):
        collector = UptimeCheckCollector(data["bk_biz_id"])
        func_mapper = {
            "test": collector.test,
            "reload": collector.reload_or_restart_process,
        }
        func = func_mapper[data["operate"]]
        with with_client_operator(data["update_user"]):
            return func(**data["kwargs"])


class GenerateConfigResource(Resource):
    """
    生成正式保存任务时【最终】需要下发到节点机器上的yaml文件
        一个拨测节点上会执行多个拨测任务
        最终的yaml配置文件为：
        for task in tasks:
            final_config_dict += task.generate_sub_config()

    注意测试时下发的yaml配置文件不在此生成
    如果需要修改测试时用的yaml文件模板，请到 UptimeCheckCollector.test 中修改
    """

    class RequestSerializer(serializers.Serializer):
        ip = serializers.IPAddressField(required=True)
        output_config = serializers.DictField(required=True)

    def perform_request(self, data):
        try:
            node = UptimeCheckNode.objects.get(ip=data["ip"], is_deleted=False)
        except UptimeCheckNode.DoesNotExist:
            raise CustomException(_("不存在的节点ip=%s") % data["ip"])

        tcp_tasks = []
        udp_tasks = []
        http_tasks = []
        icmp_tasks = []
        default_max_timeout = dict().fromkeys(["tcp", "udp", "http", "icmp"], settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT)
        config = copy.deepcopy(UPTIME_CHECK_CONFIG_TEMPLATE)
        for task in node.tasks.all():
            # 只生成运行中和启动中的任务配置，测试完成未保存的任务配置不会在这里生成
            if task.status in (UptimeCheckTask.Status.RUNNING, UptimeCheckTask.Status.STARTING):
                sub_config = resource.uptime_check.generate_sub_config({"task_id": task.pk})
                if not sub_config:
                    continue
                task_conf_timeout = int(sub_config[0]["timeout"].strip("ms"))

                if task.protocol == UptimeCheckTask.Protocol.TCP:
                    tcp_tasks = tcp_tasks + sub_config
                    default_max_timeout["tcp"] = max(default_max_timeout["tcp"], task_conf_timeout)

                elif task.protocol == UptimeCheckTask.Protocol.UDP:
                    udp_tasks = udp_tasks + sub_config
                    default_max_timeout["udp"] = max(default_max_timeout["udp"], task_conf_timeout)

                elif task.protocol == UptimeCheckTask.Protocol.HTTP:
                    http_tasks = http_tasks + sub_config
                    default_max_timeout["http"] = max(default_max_timeout["http"], task_conf_timeout)

                elif task.protocol == UptimeCheckTask.Protocol.ICMP:
                    icmp_tasks = icmp_tasks + sub_config
                    default_max_timeout["icmp"] = max(default_max_timeout["icmp"], task_conf_timeout)

        # 设置拨测节点信息
        config["uptimecheckbeat"]["node_id"] = node.pk
        config["uptimecheckbeat"]["bk_cloud_id"] = node.plat_id
        config["uptimecheckbeat"]["bk_biz_id"] = node.bk_biz_id

        # 刷新任务配置
        config["uptimecheckbeat"]["tcp_task"]["tasks"] = tcp_tasks
        config["uptimecheckbeat"]["udp_task"]["tasks"] = udp_tasks
        config["uptimecheckbeat"]["http_task"]["tasks"] = http_tasks
        config["uptimecheckbeat"]["icmp_task"]["tasks"] = icmp_tasks
        # 设置各类任务最大超时
        config["uptimecheckbeat"]["tcp_task"]["max_timeout"] = "{}ms".format(default_max_timeout["tcp"])
        config["uptimecheckbeat"]["udp_task"]["max_timeout"] = "{}ms".format(default_max_timeout["udp"])
        config["uptimecheckbeat"]["http_task"]["max_timeout"] = "{}ms".format(default_max_timeout["http"])
        config["uptimecheckbeat"]["icmp_task"]["max_timeout"] = "{}ms".format(default_max_timeout["icmp"])
        # 去除测试配置参数
        del config["output.console"]

        config.pop("output.gse", None)
        config.pop("output.bkpipe", None)
        config.update(data["output_config"])

        return resource.uptime_check.generate_yaml_config({"config": config})


class GenerateSubConfigResource(Resource):
    """
    生成拨测节点所使用的yaml配置文件
    """

    class RequestSerializer(serializers.Serializer):
        task_id = serializers.IntegerField(required=False)
        test = serializers.BooleanField(required=False, default=False)
        config = serializers.DictField(required=False, default={}, label=(_("拨测任务配置")))
        protocol = serializers.ChoiceField(choices=("HTTP", "TCP", "UDP", "ICMP"), required=False)

    # 外层增加双引号，内层对有双引号的数据增加转义字符
    def add_escape(self, input_string):
        if input_string:
            temp = input_string.replace("'", "''")
            return f"'{temp}'"
        return input_string

    def perform_request(self, data):
        """
        :return: list
        """
        task_id = data.get("task_id")
        config = data.get("config")
        protocol = data.get("protocol")
        bk_biz_id = 0

        # 兼容测试和正式下发两种情况,测试需要传入config和protocol,正式下发只需传入task_id
        if task_id:
            try:
                # 若有task_id则取数据库数据作为参数，否则依赖外部传入
                task = UptimeCheckTask.objects.get(pk=data["task_id"])
                bk_biz_id = task.bk_biz_id
            except UptimeCheckNode.DoesNotExist:
                raise CustomException(_("不存在的任务id:%s") % data["task_id"])
            protocol = task.protocol
            config = task.config
        if not config:
            raise CustomException(_("任务配置为空，请检查任务参数是否正确"))
        tasks = []

        available_duration = int(config.get("timeout", config["period"] * 60000))
        if available_duration > settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT:
            timeout = available_duration + 5000
        else:
            timeout = settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT

        if (
            len(config.get("hosts", []))
            and config["hosts"][0].get("bk_obj_id")
            and protocol != UptimeCheckTask.Protocol.ICMP
        ):
            target_host = []
        else:
            target_host = config.get("hosts", [])

        # 根据不同协议提取不同的参数
        if protocol == UptimeCheckTask.Protocol.TCP:
            tasks = [
                {
                    "task_id": 0 if data["test"] else task_id,
                    "bk_biz_id": 0 if data["test"] else bk_biz_id,
                    "period": "{}m".format(config["period"]),
                    "available_duration": "{}ms".format(available_duration),
                    "timeout": "{}ms".format(timeout),
                    "target_host": addr.get("ip") if addr.get("ip") else addr.get("outer_ip") or "",
                    "target_port": config["port"],
                    "response": self.add_escape(config.get("response", "")),
                    "response_format": config.get("response_format", "in"),
                }
                for addr in target_host
            ]

        elif protocol == UptimeCheckTask.Protocol.UDP:
            tasks = [
                {
                    "task_id": 0 if data["test"] else task_id,
                    "bk_biz_id": 0 if data["test"] else bk_biz_id,
                    "period": "{}m".format(config["period"]),
                    "available_duration": "{}ms".format(available_duration),
                    "timeout": "{}ms".format(timeout),
                    "target_host": addr.get("ip") if addr.get("ip") else addr.get("outer_ip") or "",
                    "target_port": config["port"],
                    "request_format": "hex",
                    "request": self.add_escape(config.get("request", "")),
                    "response": self.add_escape(config.get("response", "")),
                }
                for addr in target_host
            ]

        elif protocol == UptimeCheckTask.Protocol.HTTP:
            headers = config.get("headers", [])
            header_dict = {}
            for item in headers:
                # 仅允许设置支持且合法的HTTP header
                if item["name"] in UPTIME_CHECK_ALLOWED_HEADERS:
                    header_dict[item["name"]] = item["value"]

            tasks = [
                {
                    "task_id": 0 if data["test"] else task_id,
                    "bk_biz_id": 0 if data["test"] else bk_biz_id,
                    "period": "{}m".format(config["period"]),
                    "proxy": "",
                    # 是否进行证书校验
                    "insecure_skip_verify": not config.get("insecure_skip_verify", False),
                    "disable_keep_alives": False,
                    "available_duration": "{}ms".format(available_duration),
                    "timeout": "{}ms".format(timeout),
                    "steps": [
                        {
                            "url": config["urls"],
                            "method": config["method"],
                            "response_format": config.get("response_format", "in"),
                            "headers": header_dict if header_dict else {},
                            "request": self.add_escape(config.get("request", "")),
                            "response": self.add_escape(config.get("response", "")),
                            "response_code": config.get("response_code", ""),
                            # available_duration 参数在step下(样例配置文件)
                            # 但从采集器代码看，还是在上层
                            "available_duration": "{}ms".format(available_duration),
                        }
                    ],
                }
            ]

        elif protocol == UptimeCheckTask.Protocol.ICMP:
            tasks = [
                {
                    "task_id": 0 if data["test"] else task_id,
                    "bk_biz_id": 0 if data["test"] else bk_biz_id,
                    "period": "{}m".format(config["period"]),
                    # 测试时减小测试参数，以保证前端不会等待太久
                    "max_rtt": "3000ms" if data["test"] else "{}ms".format(config["max_rtt"]),
                    "total_num": 1 if data["test"] else config["total_num"],
                    "size": config["size"],
                    "available_duration": "{}ms".format(available_duration),
                    "timeout": "{}ms".format(timeout),
                    # 'target_host': addr['ip'] if addr['ip'] else addr['outer_ip'],
                    # 'target_type': addr['ip'] if addr['ip'] else addr['outer_ip'],
                    "target_hosts": target_host,
                }
            ]
            if config["hosts"][0].get("bk_obj_id"):
                # 说明是动态节点或者模板下发，让 target_hosts 字段为空，由节点管理渲染
                tasks[0]["target_hosts"] = []

        return tasks


class TaskDataResource(Resource):
    """
    根据拨测任务id获取任务近一小时数据 / 可用率 / 响应时间
    """

    class RequestSerializer(serializers.Serializer):
        SELECT_CHOICE = {
            "available": _("可用率"),
            "task_duration": _("响应时间"),
        }

        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_id = serializers.CharField(required=True, label=_("拨测任务ID"))
        type = serializers.ChoiceField(required=False, label=_("数据类型"), choices=list(SELECT_CHOICE.keys()))
        node_id = serializers.CharField(required=False, label=_("节点ID"))

    @staticmethod
    def make_select_param(task, value_filed_list, node_id, bk_biz_id=0):
        kwargs_list = []
        end = arrow.utcnow().timestamp
        start = end - UPTIME_CHECK_SUMMARY_TIME_RANGE * 3600

        filter_dict = {"task_id": str(task.id)}
        # node id 已不再使用： 使用节点的ip+cloud_id
        if node_id:
            bk_target_ip, bk_cloud_id = parse_host_id(node_id)
            filter_dict.update({"bk_target_ip": bk_target_ip, "bk_cloud_id": bk_cloud_id})

        for monitor_field in value_filed_list:

            kwargs = {
                "data_source_label": UPTIME_DATA_SOURCE_LABEL,
                "data_type_label": UPTIME_DATA_TYPE_LABEL,
                "bk_biz_id": bk_biz_id,
                "time_start": start,
                "time_end": end,
                "filter_dict": filter_dict,
                "monitor_field": monitor_field,
                "time_step": 0,
                "interval": task.config["period"],
                "result_table_id": "{}_{}_{}".format(str(task.bk_biz_id), UPTIME_CHECK_DB, task.protocol.lower()),
            }

            if monitor_field == "available":
                kwargs["unit"] = " %"
                kwargs["series_name"] = _("可用率")
                kwargs["conversion"] = 0.01
            elif monitor_field == "task_duration":
                kwargs["unit"] = " ms"
                kwargs["series_name"] = _("响应时间")
                kwargs["conversion"] = 1

            kwargs_list.append(kwargs)

        return kwargs_list

    def perform_request(self, data):
        try:
            task = UptimeCheckTask.objects.get(pk=data["task_id"])
        except UptimeCheckTask.DoesNotExist:
            err_msg = _("未找到拨测任务ID=%s") % data["task_id"]
            logger.error(err_msg)
            raise CustomException(err_msg)

        if data.get("type", ""):
            value_field = [data["type"]]
        else:
            value_field = ["available", "task_duration"]

        kwargs_list = self.make_select_param(task, value_field, data.get("node_id"), data["bk_biz_id"])

        # 执行查询
        try:
            response_data_list = resource.commons.graph_point.bulk_request(kwargs_list)
        except Exception as e:
            err_msg = _("生成图表时发生异常: %s") % e
            logger.exception(err_msg)
            raise CustomException(err_msg)

        response_data_list = handle_response_data_list(response_data_list)
        for line in response_data_list["series"]:
            if line["name"] == _("响应时间"):
                line["yAxis"] = 1
                line["tooltip"] = {"valueSuffix": " ms"}
            elif line["name"] == _("可用率"):
                line["tooltip"] = {"valueSuffix": " %"}

        return response_data_list


class TaskDetailResource(Resource):
    """
    获取拨测任务详情页面数据
    """

    class RequestSerializer(serializers.Serializer):
        SELECT_CHOICE = {
            "available": _("可用率"),
            "task_duration": _("响应时间"),
        }
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_id = serializers.CharField(required=True, label=_("拨测任务ID"))
        time_range = serializers.CharField(required=False, label=_("时间范围"))
        location = serializers.JSONField(required=False, label=_("地区"))
        carrieroperator = serializers.JSONField(required=False, label=_("外网运营商"))
        type = serializers.ChoiceField(required=True, choices=list(SELECT_CHOICE.keys()), label=_("数据类型"))
        time_step = serializers.IntegerField(required=False)

    @staticmethod
    def get_nodes_by_carrieroperator(task, carrieroperator):
        """
        根据运营商划分出拨测节点列表
        """
        result = {}
        for item in carrieroperator:
            result[item] = [str(node.pk) for node in task.nodes.filter(carrieroperator=item)]
        return result

    @staticmethod
    def get_nodes_by_location(task, location):
        """
        根据国家地区划分出拨测节点列表
        """
        result = {}
        for item in location:
            result[item] = []
        for node in task.nodes.all():
            city = node.location.get("city", _("其他"))
            if city in location:
                result[city].append(str(node.pk))
        return result

    def perform_request(self, data):
        bk_biz_id = data["bk_biz_id"]
        task_id = data["task_id"]
        monitor_field = data["type"]
        try:
            task = UptimeCheckTask.objects.get(pk=task_id)
        except UptimeCheckTask.DoesNotExist:
            raise CustomException(_("拨测任务(id=%s)获取失败") % task_id)
        protocol = task.protocol.lower()

        if data.get("location"):
            location = self.get_nodes_by_location(task, data["location"])
        if data.get("carrieroperator"):
            carrieroperator = self.get_nodes_by_carrieroperator(task, data["carrieroperator"])

        # 如果任务创建时间距离当前时间小于12小时，则默认展示时间范围为创建时间到当前时间，group_by minute1
        create_time, end = get_timestamp_range_by_biz_date(localtime(task.create_time))
        task_created_passed_by_hours = (arrow.utcnow().timestamp - create_time) / 3600

        end = arrow.utcnow().timestamp
        if data.get("time_range"):
            start, end = parse_time_range(data["time_range"])
        elif task_created_passed_by_hours < UPTIME_CHECK_TASK_DETAIL_GROUP_BY_MINUTE1_TIME_RANGE:
            start = create_time
        else:
            start = end - UPTIME_CHECK_TASK_DETAIL_TIME_RANGE * 3600

        if monitor_field == "available":
            unit = "percentunit"
        elif monitor_field == "task_duration":
            unit = "ms"
        else:
            unit = ""

        kwargs_list = []
        kwargs = {
            "data_source_label": UPTIME_DATA_SOURCE_LABEL,
            "data_type_label": UPTIME_DATA_TYPE_LABEL,
            "bk_biz_id": bk_biz_id,
            "time_start": start,
            "time_end": end,
            "interval": task.get_period(),
            "filter_dict": {"task_id": task_id},
            "monitor_field": monitor_field,
            "result_table_id": "{}_{}_{}".format(str(bk_biz_id), UPTIME_CHECK_DB, protocol),
            "group_by_list": ["ip", "bk_cloud_id"],
            "use_short_series_name": True,
            "unit": unit,
            "conversion": 1,
        }

        if data.get("location") and data.get("carrieroperator"):
            for city in list(location.keys()):
                for op in list(carrieroperator.keys()):
                    kwargs = copy.deepcopy(kwargs)
                    kwargs["series_label_show"] = city + op
                    both = [i for i in location[city] if i in carrieroperator[op]]
                    if len(both):
                        nodes = UptimeCheckNode.objects.filter(id__in=both)
                        ip_list = [{"ip": i.ip, "bk_cloud_id": str(i.plat_id)} for i in nodes]
                        kwargs["filter_dict"]["ip_list"] = ip_list
                        kwargs_list.append(kwargs)

        elif data.get("location"):
            for city in list(location.keys()):
                kwargs = copy.deepcopy(kwargs)
                if len(location[city]) > 0:
                    nodes = UptimeCheckNode.objects.filter(id__in=location[city])
                    ip_list = [{"ip": i.ip, "bk_cloud_id": str(i.plat_id)} for i in nodes]
                    kwargs["filter_dict"]["ip_list"] = ip_list
                    kwargs = copy.deepcopy(kwargs)
                    kwargs["series_label_show"] = city
                    kwargs_list.append(kwargs)

        elif data.get("carrieroperator"):
            for op in list(carrieroperator.keys()):
                kwargs = copy.deepcopy(kwargs)
                if len(carrieroperator[op]) > 0:
                    nodes = UptimeCheckNode.objects.filter(id__in=carrieroperator[op])
                    ip_list = [{"ip": i.ip, "bk_cloud_id": str(i.plat_id)} for i in nodes]
                    kwargs["filter_dict"]["ip_list"] = ip_list
                    kwargs = copy.deepcopy(kwargs)
                    kwargs["series_label_show"] = op
                    kwargs_list.append(kwargs)

        else:
            kwargs_list.append(kwargs)

        for item in kwargs_list:
            item["time_step"] = data["time_step"] if data.get("time_step") else 0

        result = self.do_query(kwargs_list)
        return result

    def do_query(self, param_list):
        # 执行查询
        try:
            response_data_list = resource.commons.graph_point.bulk_request(param_list, ignore_exceptions=True)
            # 过滤请求失败的数据
            response_data_list = [response_data for response_data in response_data_list if response_data]
        except EmptyQueryException as e:
            raise EmptyQueryException(e.message)
        except Exception as e:
            err_msg = _("生成图表时发生异常: %s" % e)
            logger.exception(err_msg)
            raise CustomException(err_msg)

        # 计算该时间范围内的均值
        # 最新的数据点有可能会是None，在此对最新数据点进行抛弃处理，再返回给前端
        for response_data in response_data_list:
            for series in response_data["series"]:
                data = [point for point in series["data"]]
                if len(data):
                    value_list = [point[1] for point in data if point[1] is not None]
                    sum_value = sum(value_list)
                    series["avg"] = round((sum_value / max(len(value_list), 1)) if sum_value else 0, 2)
                    series["max"] = max(value_list) if value_list else None
                    series["min"] = min(value_list) if value_list else None
                    series["max_index"] = [item[1] for item in data].index(series["max"])
                    series["data"] = data

        # 多条曲线合到一幅图中
        if len(response_data_list):
            max_y = max([line["max_y"] for line in response_data_list])
            chart_group = response_data_list.pop()
            if len(response_data_list):
                for line in response_data_list:
                    chart_group["series"].extend(line["series"])
            chart_group["max_y"] = max_y

            return chart_group
        else:
            return response_data_list


class TaskGraphAndMapResource(Resource):
    """
    生成任务详情可用率和响应时长曲线图和地图信息
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_id = serializers.CharField(required=True, label=_("拨测任务ID"))
        time_range = serializers.CharField(allow_blank=True, required=False, label=_("时间范围"))
        location = serializers.JSONField(required=False, label=_("地区"))
        carrieroperator = serializers.JSONField(required=False, label=_("外网运营商"))

    def perform_request(self, data):
        params = {"bk_biz_id": data["bk_biz_id"], "task_id": data["task_id"]}

        for item in ["time_range", "location", "carrieroperator"]:
            if data.get(item):
                params.update({item: data[item]})

        available_param = params.copy()
        available_param.update({"type": "available"})
        task_duration_param = params.copy()
        task_duration_param.update({"type": "task_duration"})

        try:
            available_graph = resource.uptime_check.task_detail(available_param)
            task_duration_graph = resource.uptime_check.task_detail(task_duration_param)
        except EmptyQueryException:
            # 正常的无数据不报错
            return {"chart": [], "map": []}

        graph_result = {
            "available": available_graph if available_graph else {},
            "task_duration": task_duration_graph if task_duration_graph else {},
        }

        task = UptimeCheckTask.objects.get(id=data["task_id"])
        for type in list(graph_result.keys()):
            threshold_result = self.get_threshold_line(type, task)
            if threshold_result:
                # 返回数组，以后可能不止显示一条阈值线
                graph_result[type].update({"threshold_line": [threshold_result[0]]})

        # 组装节点地区平均可用率和响应时长数据
        map_dict = {}
        # 节点可用率和响应时长最值
        available_value = []
        task_duration_value = []
        for type, graph in list(graph_result.items()):
            del_nodes = []
            if not graph:
                continue

            for line in graph["series"]:
                if len(line["data"]) != 0:
                    try:
                        if "-" in line["name"]:
                            line["name"] = line["name"].split(" - ")[1]
                        ip = line["name"].split(" | ")[0]
                        bk_cloud_id = line["name"].split(" | ")[1]
                        # 反向找出node信息
                        if task.protocol.lower() == "http":
                            # 目前站点拨测上报的节点云区域不正确，只有直连区域，所以此处兼容直连区域
                            nodes = list(UptimeCheckNode.objects.filter(ip=ip, is_deleted=False))
                            if len(nodes) > 0:
                                node = None
                                # 先尝试匹配云区域正确的节点
                                for temp_node in nodes:
                                    if temp_node.plat_id == int(bk_cloud_id):
                                        node = temp_node
                                        break
                                # 如果不存在匹配的云区域，默认选择第一个节点
                                if not node:
                                    node = nodes[0]
                            else:
                                raise UptimeCheckNode.DoesNotExist
                        else:
                            qs = UptimeCheckNode.objects.filter(ip=ip, plat_id=bk_cloud_id, is_deleted=False)
                            if qs.exists():
                                node = qs.first()
                            else:
                                raise UptimeCheckNode.DoesNotExist
                    except UptimeCheckNode.DoesNotExist:
                        del_nodes.append(line)
                        continue
                    # 图例展示使用节点名称
                    line["name"] = node.name

                    # map_data用于地图和TOP5展示
                    map_dict.setdefault(node.name, {}).update(
                        {"name": node.name, "location": node.location.get("city", _("其他"))}
                    )
                    if type == "available":
                        map_dict[node.name].update({"available": line["avg"]})
                        available_value.extend([line["max"], line["min"]])
                    else:
                        map_dict[node.name].update({"task_duration": line["avg"]})
                        task_duration_value.extend([line["max"], line["min"]])

            # 删除图像中已不存在的节点
            for line in del_nodes:
                graph["series"].remove(line)

        map_data = list(map_dict.values())
        return {
            "chart": graph_result,
            "map": map_data,
            "max_and_min": {
                "available_max": max(available_value) if available_value else [],
                "available_min": min(available_value) if available_value else [],
                "task_duration_max": max(task_duration_value) if task_duration_value else [],
                "task_duration_min": min(task_duration_value) if task_duration_value else [],
            },
        }

    def get_threshold_line(self, type, task):
        # 获取监控策略的期望可用率或响应时长阈值线数据
        threshold_result = []
        # for monitor_source in task.monitors:
        #     if (_('可用率') in monitor_source.monitor_name and type == 'available') \
        #             or (_('响应时间') in monitor_source.monitor_name and type == 'task_duration'):
        #         for monitor_item in monitor_source.monitor_item_list:
        #             # 获取监控策略对应的检测算法配置
        #             detect_algorithm_config = monitor_item.condition_config
        #             # 暂时只考虑静态阈值
        #             if detect_algorithm_config and detect_algorithm_config[0].algorithm_id == 1000:
        #                 config = json.loads(detect_algorithm_config[0].strategy_option)
        #                 threshold_result.append(
        #                     {
        #                         'value': config.get('threshold'),
        #                         'name': monitor_item.title,
        #                         'level': monitor_item.monitor_level
        #                     }
        #                 )
        if threshold_result:
            # 若存在多级告警策略，显示级别高的；对于多个同高级别告警，可用率显示阈值小的，响应时长显示阈值大的
            level_sort = sorted(threshold_result, key=lambda x: x["level"])
            same_highest_level = [x for x in level_sort if x["level"] == level_sort[0]["level"]]
            if len(same_highest_level) > 1:
                if type == "available":
                    return sorted(same_highest_level, key=lambda x: x["value"])
                return sorted(threshold_result, key=lambda x: x["value"], reverse=True)
            return level_sort
        return []


class UptimeCheckBeatResource(Resource):
    """
    采集器相关信息获取
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data.get("bk_biz_id")

        if bk_biz_id:
            # 过滤业务下所有节点时，同时还应该加上通用节点
            biz_nodes = UptimeCheckNode.objects.filter(bk_biz_id=bk_biz_id)
            common_nodes = UptimeCheckNode.objects.filter(is_common=True)
            nodes = biz_nodes | common_nodes
        else:
            nodes = UptimeCheckNode.objects.all()
        result = {}

        # 获取采集器信息
        if nodes:
            heartbeats = resource.uptime_check.get_beat_data.bulk_request(
                [{"ip": node.ip, "bk_cloud_id": node.plat_id} for node in nodes]
            )
            result.update(
                {
                    host_key(ip=i[0]["ip"], bk_cloud_id=i[0]["bk_cloud_id"]): {
                        "ip": i[0]["ip"],
                        "bk_cloud_id": safe_int(i[0]["bk_cloud_id"]),
                        "status": i[0]["status"],
                        "version": i[0]["version"],
                        "gse_status": BEAT_STATUS["RUNNING"],
                    }
                    for i in heartbeats
                    if i
                }
            )

        biz_to_node = {}
        for node in nodes:
            if host_key(ip=node.ip, bk_cloud_id=node.plat_id) not in result:
                result[host_key(ip=node.ip, bk_cloud_id=node.plat_id)] = {
                    "ip": node.ip,
                    "bk_cloud_id": node.plat_id,
                    "status": BEAT_STATUS["DOWN"],
                    "version": "",
                    "gse_status": BEAT_STATUS["RUNNING"],
                }
            # 组装以业务id为key,节点为value的字典，用于以业务id为单位并发拉取gse数据
            biz_to_node.setdefault(node.bk_biz_id, []).append(
                Host(host_key(ip=node.ip, bk_cloud_id=node.plat_id), bk_biz_id)
            )

        result = list(result.values())

        # 获取gse agent信息
        params_list = [(biz_id, hosts) for biz_id, hosts in list(biz_to_node.items())]
        pool = ThreadPool()
        gse_status_list = pool.map_ignore_exception(resource.cc.agent_status, params_list)
        pool.close()
        pool.join()
        gse_status = {}
        for item in gse_status_list:
            gse_status.update(item)

        bad_agent = [host for (host, status) in gse_status.items() if status != 0]

        for r in result:
            if host_key(ip=r["ip"], plat_id=r["bk_cloud_id"]) in bad_agent:
                r["gse_status"] = BEAT_STATUS["DOWN"]

        return result


class GetBeatDataResource(Resource):
    """
    获取采集器相关数据
    """

    class RequestSerializer(serializers.Serializer):
        ip = serializers.CharField(required=True, label=_("节点IP"))
        bk_cloud_id = serializers.CharField(required=True, label=_("节点云区域ID"))

    def perform_request(self, data):
        end = arrow.utcnow().timestamp
        start = end - 180

        filter_dict = {
            "time__gte": start * 1000,
            "time__lt": end * 1000,
            "ip": data["ip"],
            "bk_cloud_id": data["bk_cloud_id"],
        }
        value_fields = ["status", "ip", "bk_cloud_id", "version", "uptime"]
        data_source_class = load_data_source(DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES)
        data_source = data_source_class(
            table="beat_monitor.heartbeat_total",
            metrics=[{"field": field} for field in value_fields],
            filter_dict=filter_dict,
        )
        data = data_source.query_data(limit=5)
        return data


class GetStrategyStatusResource(Resource):
    """
    获取指定拨测任务启用/停用状态
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True)
        task_id_list = serializers.ListField(required=True)

    def perform_request(self, data):
        return resource.uptime_check.get_strategy_status_by_task_id.bulk_request(
            [{"task_id": task_id} for task_id in data["task_id_list"]]
        )


class SwitchStrategyByTaskIDResource(Resource):
    """
    根据拨测任务id启用/停用监控策略
    封装 resource.config.list_strategy_by_monitor_id 方法
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True)
        task_id = serializers.IntegerField(required=True)
        is_enabled = serializers.BooleanField(required=True)

    def perform_request(self, data):
        # TODO：切换到新的策略配置
        pass


class GenerateDefaultStrategyResource(Resource):
    """
    创建拨测任务后，根据拨测任务自动生成告警策略
    """

    class RequestSerializer(serializers.Serializer):
        task_id = serializers.IntegerField(required=True, label=_("拨测任务id"))

    @staticmethod
    def gen_default_strategy(task, monitor_target, display_name, method, threshold, condition=""):
        """
        生成默认监控策略
        """
        # TODO：接入新的告警策略
        pass

    def perform_request(self, data):
        try:
            task = UptimeCheckTask.objects.get(pk=data["task_id"])
        except UptimeCheckNode.DoesNotExist:
            raise CustomException(_("不存在的任务id:%s") % data["task_id"])

        # 拨测任务默认生成可用率监控策略
        self.gen_default_strategy(task, "available", _("可用率"), "lt", UPTIME_CHECK_AVAILABLE_DEFAULT_VALUE)

        if task.protocol == task.Protocol.HTTP:
            # 如果HTTP任务指定了状态码
            if task.config["response_code"] and (task.protocol == task.Protocol.HTTP):
                self.gen_default_strategy(task, "response_code", _("状态码"), "gte", 1, UPTIME_CHECK_MONIT_RESPONSE_CODE)
            # 如果指定了响应内容
            if task.config["response"]:
                self.gen_default_strategy(task, "response", _("响应内容"), "gte", 1, UPTIME_CHECK_MONIT_RESPONSE)


class UpdateTaskRunningStatusResource(Resource):
    """
    周期查询拨测任务启动状态，用于后台celery任务
    """

    def __init__(self):
        super(UpdateTaskRunningStatusResource, self).__init__()

    def check_single_task_status(self, subscription_id):
        while True:
            time.sleep(3)
            error_count = 0
            try:
                status_result = api.node_man.subscription_instance_status(subscription_id_list=[subscription_id])[0][
                    "instances"
                ]
            except BKAPIError as e:
                logger.error(_("请求节点管理任务执行结果接口失败: {}").format(e))
                return
            log = []
            nodeman_task_id = ""
            for item in status_result:
                if item["status"] in [CollectStatus.RUNNING, CollectStatus.PENDING]:
                    break
                if item["status"] == CollectStatus.FAILED:
                    error_count += 1
                    params = {"subscription_id": subscription_id, "instance_id": item["instance_id"]}
                    result = api.node_man.task_result_detail(**params)
                    if result:
                        nodeman_task_id = result["task_id"]
                        for step in result.get("steps", []):
                            if step["status"] == CollectStatus.FAILED:
                                for sub_step in step["target_hosts"][0].get("sub_steps", []):
                                    if sub_step["ex_data"]:
                                        log.append(sub_step["ex_data"])
            else:
                if error_count == 0:
                    logger.info(_("celery period task: 订阅任务%s正在运行中") % subscription_id)
                    logger.info(_("error_log: %s") % log)
                    return UptimeCheckTask.Status.RUNNING, log, nodeman_task_id
                else:
                    logger.info(_("celery period task: 订阅任务%s启动失败") % subscription_id)
                    logger.info(_("error_log: %s") % log)
                    return UptimeCheckTask.Status.START_FAILED, log, nodeman_task_id

    def perform_request(self, task_id):
        logger.info("start celery period task: update uptime check task running status")
        task = UptimeCheckTask.objects.get(id=task_id)
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=task_id)
        hasFail = False
        # 遍历所有订阅，获取全部的状态
        for subscription in subscriptions:
            status, log, nodeman_task_id = self.check_single_task_status(subscription.subscription_id)
            if status == UptimeCheckTask.Status.START_FAILED:
                for item in log:
                    UptimeCheckTaskCollectorLog.objects.create(
                        task_id=task.id,
                        error_log=item,
                        subscription_id=task.subscription_id,
                        nodeman_task_id=nodeman_task_id,
                    )
                hasFail = True
        # 存在失败则判定为全部失败
        if hasFail:
            task.status = UptimeCheckTask.Status.START_FAILED
        else:
            task.status = UptimeCheckTask.Status.RUNNING

        task.save()


class FrontPageDataResource(Resource):
    """
    监控首页 服务拨测曲线数据获取
    获取规则：
        1. 在没有任务发⽣告警的前提下，默认展示最近添加的最多5个任务曲线
        2. 如果⽤户已特殊关注了N个拨测任务，将替换原有的默认5条线，只展示用户关注的N个任务数据
        3. 若有除⽤户特殊关注的任务以外的任务发⽣告警，则以”橙-红“的渐变⾊，展示用户关注任务+告警任务数据
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_id_list = serializers.ListField(required=True, label=_("拨测任务ID列表"))

    @staticmethod
    def make_select_param(tasks, bk_biz_id=0):
        """
        分组中可能包含不同协议的任务，后台HTTP、TCP、UDP三种协议的数据是分表存储
        后台需要多进程查询三个表，将结果汇总到前端展示
        """
        result = []
        end = arrow.utcnow().timestamp
        start = end - UPTIME_CHECK_TASK_DETAIL_GROUP_BY_MINUTE1_TIME_RANGE * 3600

        for task in tasks:
            kwargs = {
                "data_source_label": UPTIME_DATA_SOURCE_LABEL,
                "data_type_label": UPTIME_DATA_TYPE_LABEL,
                "bk_biz_id": bk_biz_id,
                "time_start": start,
                "time_end": end,
                "monitor_field": "available",
                "series_name": task.name,
                "result_table_id": "{}_{}_{}".format(str(task.bk_biz_id), UPTIME_CHECK_DB, task.protocol.lower()),
                "unit": "percentunit",
                "conversion": 1,
                "time_step": 0,
                "interval": task.config["period"],
                "filter_dict": {"task_id": str(task.id)},
            }
            result.append(kwargs)

        return result

    def perform_request(self, data):
        bk_biz_id = data["bk_biz_id"]
        task_id_list = data["task_id_list"]

        try:
            tasks = UptimeCheckTask.objects.filter(id__in=task_id_list)
        except UptimeCheckGroup.DoesNotExist as e:
            err_msg = _("未找到拨测任务: %s") % e
            logger.error(err_msg)
            raise CustomException(err_msg)

        params_list = self.make_select_param(tasks, bk_biz_id)

        if not len(params_list):
            raise CustomException(_("暂无数据，请在展示设置中添加拨测任务"))

        # 执行查询
        try:
            response_data_list = resource.commons.graph_point.bulk_request(params_list, ignore_exceptions=True)
            # 过滤请求失败的数据
            response_data_list = [response_data for response_data in response_data_list if response_data]
        except CustomException:
            raise
        except Exception as e:
            err_msg = _("生成图表时发生异常: %s") % e
            logger.exception(err_msg)
            raise CustomException(err_msg)

        response_data_list = handle_response_data_list(response_data_list)

        for line in response_data_list["series"]:
            line["is_ok"] = True

        return response_data_list


class ExportUptimeCheckConfResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_ids = serializers.CharField(required=False, label=_("拨测任务ID"))
        protocol = serializers.ChoiceField(required=False, choices=["TCP", "UDP", "HTTP"], label=_("协议类型"))
        node_conf_needed = serializers.ChoiceField(required=False, choices=[0, 1], default=1, label=_("是否需要导出节点配置"))

        def validate_task_ids(self, value):
            r = re.match(r"^\d+(,\d+)*$", value)
            if not r:
                raise CustomException(_("不合规的参数，请使用逗号拼接数字"))

            return value

    @property
    def target_conf(self):
        if hasattr(self, "node_conf_needed") and self.node_conf_needed:
            return {"bk_biz_id": 0, "node_list": [], "node_id_list": []}

        return {"bk_biz_id": 0, "node_id_list": []}

    def get_monitor_conf(self, task):
        # TODO: 接入新的告警策略
        monitor_conf_list = []
        del_keys = [
            "solution_task_id",
            "solution_params_replace",
            "solution_notice",
            "solution_display",
            "solution_type",
            "solution_is_enable",
            "monitor_name",
            "id",
            "monitor_item_id",
            "monitor_group_id",
            "condition_display",
            "task",
            "converge_display",
        ]
        for monitor_conf in monitor_conf_list:
            for key in del_keys:
                del monitor_conf[key]

            for config in list(monitor_conf["alarm_level_config"].values())[0]["detect_algorithm"]:
                del config["name"]
                del config["display"]

            list(monitor_conf["alarm_level_config"].values())[0]["alarm_start_time"] = list(
                monitor_conf["alarm_level_config"].values()
            )[0]["notice_start_time"]
            list(monitor_conf["alarm_level_config"].values())[0]["alarm_end_time"] = list(
                monitor_conf["alarm_level_config"].values()
            )[0]["notice_end_time"]
            del list(monitor_conf["alarm_level_config"].values())[0]["notice_start_time"]
            del list(monitor_conf["alarm_level_config"].values())[0]["notice_end_time"]
            monitor_conf["bk_biz_id"] = monitor_conf["cc_biz_id"]
            del monitor_conf["cc_biz_id"]
            monitor_conf["alarm_strategy_id"] = 0
            monitor_conf["where_sql"] = ""
            monitor_conf["monitor_id"] = 0

        return monitor_conf_list

    def get_task_conf(self, task):
        task_conf = {}
        task_conf["target_conf"] = self.target_conf
        if "node_list" in self.target_conf:
            node_list = task.nodes.all()
            for node in node_list:
                node_conf = resource.uptime_check.export_uptime_check_node_conf.get_node_conf(node)
                task_conf["target_conf"]["node_list"].append(node_conf)

        if task.protocol == "HTTP":
            real_task_config = task.config
        else:
            real_task_config = {k: v for k, v in list(task.config.items()) if k != "hosts"}
            real_task_config["ip_list"] = [i["ip"] for i in task.config["hosts"]]

        task_conf["collector_conf"] = {
            "groups": ",".join([group.name for group in task.groups.all()]),
            "protocol": task.protocol,
            "name": task.name,
            "location": task.location,
            "config": real_task_config,
        }
        task_conf["monitor_conf"] = self.get_monitor_conf(task)
        return task_conf

    def perform_request(self, data):
        self.node_conf_needed = data["node_conf_needed"]
        bk_biz_id = data["bk_biz_id"]
        task_ids = data.get("task_ids", "")
        task_protocol = data.get("protocol", "")
        task_conf_list = []
        tasks = UptimeCheckTask.objects.filter(bk_biz_id=bk_biz_id)
        if task_protocol:
            tasks = tasks.filter(protocol__iexact=task_protocol)
        if task_ids:
            task_id_list = task_ids.split(",")
            tasks = tasks.filter(id__in=task_id_list)

        for task in tasks:
            task_conf = self.get_task_conf(task)
            task_conf_list.append(task_conf)

        return task_conf_list


class ExportUptimeCheckNodeConfResource(Resource):
    TARGET_CONF = {"ip": "", "bk_cloud_id": 0, "bk_biz_id": 0}

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        node_ids = serializers.CharField(required=False, label=_("节点ID"))

        def validate_node_ids(self, value):
            r = re.match(r"^\d+(,\d+)*$", value)
            if not r:
                raise CustomException(_("不合规的参数，请使用逗号拼接数字"))

            return value

    def get_node_conf(self, node):
        node_conf = {}
        node_conf["target_conf"] = self.TARGET_CONF
        node_conf["node_conf"] = {
            "name": node.name,
            "is_common": node.is_common,
            "location": node.location,
            "carrieroperator": node.carrieroperator,
        }
        return node_conf

    def perform_request(self, data):
        node_conf_list = []
        bk_biz_id = data["bk_biz_id"]
        node_ids = data.get("node_ids", "")
        nodes = UptimeCheckNode.objects.filter(bk_biz_id=bk_biz_id)
        if node_ids:
            node_id_list = node_ids.split(",")
            nodes = nodes.filter(id__in=node_id_list)

        for node in nodes:
            node_conf = self.get_node_conf(node)
            node_conf_list.append(node_conf)

        return {"conf_list": node_conf_list}


class FileParseResource(Resource):
    """
    获取字段映射
    """

    class RequestSerializer(serializers.Serializer):
        protocol = serializers.ChoiceField(required=True, choices=["HTTP(S)", "TCP", "UDP", "ICMP"], label=_("任务类型"))

    def perform_request(self, validated_request_data):
        if validated_request_data["protocol"] == "HTTP(S)":
            result_data = [
                {"cnkey": _("任务名称（必填）"), "enkey": "name", "required": True, "regex": r"^.{1,50}$"},
                {"cnkey": _("协议（必填）"), "enkey": "protocol", "required": True, "regex": r"^HTTP\(S\)$|^http\(s\)$"},
                {"cnkey": _("方法（必填）"), "enkey": "method", "required": True, "regex": r"^GET$|^POST$"},
                {
                    "cnkey": _("地址（必填,小写）"),
                    "enkey": "urls",
                    "required": True,
                    "regex": r"(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]",
                },
                {"cnkey": _("节点（必填）"), "enkey": "node_list", "required": True},
                {"cnkey": _("提交内容（POST方法必填）"), "enkey": "body", "required": False, "default": ""},
                {
                    "cnkey": _("SSL证书校验"),
                    "enkey": "insecure_skip_verify",
                    "required": False,
                    "default": _("否"),
                    "regex": _(r"^是$|^否$"),
                },
                {
                    "cnkey": _("期望响应时间（ms）"),
                    "enkey": "timeout",
                    "required": False,
                    "default": "3000",
                    "regex": r"^[1-9]\d*$",
                },
                {"cnkey": _("任务分组"), "enkey": "groups", "required": False, "default": "", "regex": r"^.{0,50}$"},
                {"cnkey": _("周期（分钟）"), "enkey": "period", "required": False, "default": "1", "regex": r"^[1-9]\d*$"},
                {
                    "cnkey": _("期望返回码"),
                    "enkey": "response_code",
                    "required": False,
                    "default": "",
                    "regex": r"^[1-5][0-9][0-9]$",
                },
                {"cnkey": _("期望响应信息"), "enkey": "response", "required": False, "default": _("包含:")},
                {
                    "cnkey": _("地理位置"),
                    "enkey": "location",
                    "required": False,
                    "default": "",
                    "regex": "([\\u4e00-\\u9fa5]*)(-[\\u4e00-\\u9fa5]+)?",
                },
                {"cnkey": _("头信息"), "enkey": "headers", "required": False, "default": "", "is_dict": True},
            ]
        elif validated_request_data["protocol"] == "TCP":
            result_data = [
                {"cnkey": _("任务名称（必填）"), "enkey": "name", "required": True, "regex": r"^.{1,50}$"},
                {"cnkey": _("协议（必填）"), "enkey": "protocol", "required": True, "regex": r"^TCP$|^tcp$"},
                {
                    "cnkey": _("地址（必填）"),
                    "enkey": "ip_list",
                    "required": True,
                    "regex": r"(((25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}"
                    r"(25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\[[0-9+]\];?)+",
                },
                {"cnkey": _("端口（必填）"), "enkey": "port", "required": True, "regex": r"^[1-9]\d*$"},
                {"cnkey": _("节点（必填）"), "enkey": "node_list", "required": True},
                {
                    "cnkey": _("期望响应时间（ms）"),
                    "enkey": "timeout",
                    "required": False,
                    "default": "3000",
                    "regex": r"^[1-9]\d*$",
                },
                {"cnkey": _("任务分组"), "enkey": "groups", "required": False, "default": "", "regex": r"^.{0,50}$"},
                {"cnkey": _("周期（分钟）"), "enkey": "period", "required": False, "default": "1", "regex": r"[1-9]\d*"},
                {"cnkey": _("期望响应信息"), "enkey": "response", "required": False, "default": _("包含:")},
                {
                    "cnkey": _("地理位置"),
                    "enkey": "location",
                    "required": False,
                    "default": "",
                    "regex": "([\\u4e00-\\u9fa5]*)(-[\\u4e00-\\u9fa5]+)?",
                },
            ]
        elif validated_request_data["protocol"] == "UDP":
            result_data = [
                {"cnkey": _("任务名称（必填）"), "enkey": "name", "required": True, "regex": r"^.{1,50}$"},
                {"cnkey": _("协议（必填）"), "enkey": "protocol", "required": True, "regex": r"^UDP$|^udp$"},
                {
                    "cnkey": _("地址（必填）"),
                    "enkey": "ip_list",
                    "required": True,
                    "regex": r"(((25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}"
                    r"(25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\[[0-9+]\];?)+",
                },
                {"cnkey": _("端口（必填）"), "enkey": "port", "required": True, "regex": r"^[1-9]\d*$"},
                {"cnkey": _("请求内容（必填,十六进制）"), "enkey": "request", "required": True, "regex": r"^([0-9|a-f|A-F]*)$"},
                {"cnkey": _("节点（必填）"), "enkey": "node_list", "required": True},
                {
                    "cnkey": _("期望响应时间（ms）"),
                    "enkey": "timeout",
                    "required": False,
                    "default": "3000",
                    "regex": r"^[1-9]\d*$",
                },
                {"cnkey": _("任务分组"), "enkey": "groups", "required": False, "default": "", "regex": r"^.{0,50}$"},
                {"cnkey": _("周期（分钟）"), "enkey": "period", "required": False, "default": "1", "regex": r"^[1-9]\d*$"},
                {"cnkey": _("期望响应信息"), "enkey": "response", "required": False, "default": _("包含:")},
                {
                    "cnkey": _("地理位置"),
                    "enkey": "location",
                    "required": False,
                    "default": "",
                    "regex": "([\\u4e00-\\u9fa5]*)(-[\\u4e00-\\u9fa5]+)?",
                },
            ]
        elif validated_request_data["protocol"] == "ICMP":
            result_data = [
                {"cnkey": _("任务名称（必填）"), "enkey": "name", "required": True, "regex": r"^.{1,50}$"},
                {"cnkey": _("协议（必填）"), "enkey": "protocol", "required": True, "regex": r"^ICMP$|^icmp$"},
                {
                    "cnkey": _("目标（必填）"),
                    "enkey": "ip_list",
                    "required": True,
                    "regex": r"(((25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}"
                    r"(25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\[[0-9+]\];?)+",
                },
                {"cnkey": _("拨测节点（必填）"), "enkey": "node_list", "required": True},
                {
                    "cnkey": _("超时时间（ms）"),
                    "enkey": "max_rtt",
                    "required": False,
                    "default": "3000",
                    "regex": r"^[1-9]\d*$",
                },
                {"cnkey": _("任务分组"), "enkey": "groups", "required": False, "default": "", "regex": r"^.{0,50}$"},
                {"cnkey": _("周期（分钟）"), "enkey": "period", "required": False, "default": "1", "regex": r"^[1-9]\d*$"},
                {
                    "cnkey": _("周期内连续探测次数"),
                    "enkey": "total_num",
                    "required": False,
                    "default": "3",
                    "regex": r"^[1-9]\d*$",
                },
                {"cnkey": _("探测包大小"), "enkey": "size", "required": False, "default": "68", "regex": r"^[1-9]\d*$"},
            ]
        return result_data


class FileImportUptimeCheckResource(Resource):
    """
    文件模板导入拨测任务resource
    """

    http_method = ["GET", "POST"]
    response_match = {
        _("包含"): "in",
        _("不包含"): "nin",
        _("正则"): "reg",
    }
    all_uptime_check_node = []

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        task_list = serializers.ListField(required=True, label=_("任务配置列表"))

    def get_node_id_by_name(self, name_str):
        """
        根据节点名称获取节点id
        :param name_str:
        :return:
        """
        if name_str:
            name_set = set(filter(None, name_str.split(";")))
            node_lsit = [x for x in self.all_uptime_check_node if x.name in name_set]
            if len(node_lsit) != len(name_set):
                error_node = name_set - set([node.name for node in node_lsit] if len(node_lsit) > 0 else [])
                raise CustomException(_("当前业务下不存在拨测节点[%s]" % ";".join(error_node)))

            return [node.id for node in node_lsit]
        else:
            raise CustomException(_("拨测节点未填写"))

    def import_data_assemble(self, task_conf):
        """
        导入数据校验与组装
        :param task_conf:
        :return:
        """
        protocol = task_conf["protocol"].upper()
        # 根据不同协议类型生成相应的config
        if protocol == "HTTP(S)":
            task_conf["protocol"] = protocol = "HTTP"
            config = self.get_http_config(task_conf)
        elif protocol == "ICMP":
            config = self.get_icmp_config(task_conf)
        else:
            config = self.get_tcp_or_udp_config(task_conf)

        # 解析地理位置信息
        if protocol == "ICMP":
            bk_state_name = ""
            bk_province_name = ""
        else:
            try:
                location_index = task_conf["location"].index("-")
                bk_state_name = task_conf["location"][0:location_index]
                # fmt: off
                bk_province_name = task_conf["location"][location_index + 1:]
                # fmt: on
            except ValueError:
                bk_state_name = task_conf["location"]
                bk_province_name = ""

        # 基础配置
        collector_conf = {
            "config": config,
            "protocol": protocol,
            "name": task_conf["name"],
            "groups": task_conf["groups"],
            "location": {"bk_state_name": bk_state_name, "bk_province_name": bk_province_name},
        }
        # 下发配置
        node_id_list = self.get_node_id_by_name(task_conf["node_list"])
        target_conf = {
            "bk_biz_id": 0,
            "node_id_list": node_id_list,
        }
        return {
            "collector_conf": collector_conf,
            "target_conf": target_conf,
            "monitor_conf": [],  # 不传参数可自动生成默认监控配置
        }

    def get_general_config(self, conf_data):
        """
        获取通用配置
        :param conf_data:
        :return:
        """
        response = conf_data["response"]
        try:
            index = response.index(":")
            match = response[0:index]
            response_format = self.response_match[match]
            # fmt: off
            responce_content = response[index + 1:]
            # fmt: on
        except (ValueError, KeyError):
            raise CustomException(_("期望响应信息内容填写错误"))

        return {
            "period": safe_int(conf_data.get("period")),
            "timeout": safe_int(conf_data.get("timeout")),
            "response_format": response_format,
            "response": responce_content or None,
            "request": conf_data.get("request"),
        }

    def get_http_config(self, conf_data):
        if conf_data["method"] not in self.http_method:
            raise CustomException(_("方法内容填写错误"))

        headers = []
        if conf_data["headers"]:
            headers_dict = conf_data["headers"]
            if isinstance(headers_dict, dict):
                for key, value in list(headers_dict.items()):
                    headers.append({"name": key, "value": value})

            else:
                raise CustomException(_("头信息内容填写错误"))

        if conf_data["insecure_skip_verify"] in [_("是"), _("否")]:
            insecure_skip_verify = True if conf_data["insecure_skip_verify"] == _("是") else False
        else:
            raise CustomException(_("SSL证书校验内容填写错误"))

        config = {
            "insecure_skip_verify": insecure_skip_verify,
            "urls": conf_data.get("urls"),
            "response_code": conf_data.get("response_code"),
            "request": None,
            "headers": headers,
            "method": conf_data.get("method"),
        }
        config.update(self.get_general_config(conf_data))
        return config

    def get_tcp_or_udp_config(self, conf_data):
        try:
            # fmt: off
            ip_list = [ip[0: ip.index("[")] for ip in conf_data["ip_list"].split(";")]
            # fmt: on
        except SyntaxError:
            raise CustomException(_("地址内容填写错误"))

        config = {
            "ip_list": ip_list,
            "port": safe_int(conf_data.get("port")),
        }
        config.update(self.get_general_config(conf_data))
        return config

    def get_icmp_config(self, conf_data):
        try:
            # fmt: off
            ip_list = [ip[0: ip.index("[")] for ip in conf_data["ip_list"].split(";")]
            # fmt: on
        except SyntaxError:
            raise CustomException(_("地址内容填写错误"))

        config = {
            "ip_list": ip_list,
            "period": conf_data.get("period"),
            "max_rtt": conf_data.get("max_rtt"),
            "total_num": conf_data.get("total_num"),
            "size": conf_data.get("size"),
        }

        return config

    def perform_request(self, validated_request_data):
        conf_list = []
        failed_detail = []
        biz_id = validated_request_data["bk_biz_id"]
        # 取出当前业务下的所有节点
        self.all_uptime_check_node = list(UptimeCheckNode.objects.filter(Q(bk_biz_id=biz_id) | Q(is_common=1)))
        # 数据解析和组装
        for task_conf in validated_request_data["task_list"]:

            try:
                conf_list.append(self.import_data_assemble(task_conf))
            except CustomException as e:
                failed_detail.append({"task_name": task_conf["name"], "error_mes": e.message})

        result_data = {
            "success": {"total": 0, "detail": []},
            "failed": {"total": 0, "detail": []},
        }
        if conf_list:
            # 执行拨测任务导入
            result_data = ImportUptimeCheckTaskResource().request(
                request_data={"bk_biz_id": biz_id, "conf_list": conf_list}  # noqa: F405
            )

        result_data["failed"]["detail"] += failed_detail
        result_data["failed"]["total"] += len(failed_detail)
        return result_data


class UptimeCheckCardResource(Resource):
    """
    拨测任务卡片展示
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, allow_null=True, label=_("业务ID"))
        task_data = serializers.ListField(required=True, label=_("拨测任务数据"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data.get("bk_biz_id")
        bk_biz_ids = [bk_biz_id]
        all_tasks_data = validated_request_data.get("task_data")

        # 拿到2天内的服务拨测事件queryset
        uptime_check_queryset = resource.alert_events.query_events(
            bk_biz_ids=bk_biz_ids, days=2, conditions=[{"key": "scenario", "value": [UPTIME_CHECK_DB]}]
        )
        uptime_check_queryset = uptime_check_queryset.filter(status=Event.EventStatus.ABNORMAL).values("origin_alarm")

        task_alarm_info = {}
        for item in uptime_check_queryset:
            try:
                i = item["origin_alarm"]
                info = task_alarm_info.setdefault(
                    i["data"]["dimensions"]["task_id"],
                    {"alarm_num": 0, "task_duration_alarm": False, "available_alarm": False},
                )
            except KeyError:
                logger.warning(json.dumps(item))
                continue

            info["alarm_num"] += 1

            if not info["task_duration_alarm"] and "task_duration" in list(i["data"]["values"].keys()):
                info["task_duration_alarm"] = True

            if not info["available_alarm"] and "available" in list(i["data"]["values"].keys()):
                info["available_alarm"] = True

        group_task_dict = {}
        for t in all_tasks_data:
            t.update(
                task_alarm_info.get(t["id"], {"alarm_num": 0, "task_duration_alarm": False, "available_alarm": False})
            )
            # 筛选出对应拨测任务组的任务
            for g in t["groups"]:
                group_task_dict.setdefault(g["id"], []).append(t)

        # 任务组告警
        uptime_check_group = UptimeCheckGroup.objects.filter(bk_biz_id__in=[bk_biz_id, 0])
        group_data = []
        for group in uptime_check_group:
            tasks_data = []
            alarm_num = 0  # 任务组未恢复告警数
            http_num = 0
            tcp_num = 0
            udp_num = 0
            for task in group_task_dict.get(group.id, []):
                alarm_num += task["alarm_num"]
                tasks_data.append(
                    {
                        "name": task["name"],
                        "available": task["available"],
                        "task_id": task["id"],
                        "status": task["status"],
                    }
                )

                if task["protocol"] == UptimeCheckTask.Protocol.HTTP:
                    http_num += 1
                elif task["protocol"] == UptimeCheckTask.Protocol.TCP:
                    tcp_num += 1
                elif task["protocol"] == UptimeCheckTask.Protocol.UDP:
                    udp_num += 1

            # 整理各协议任务数量,任务数为0则不返回
            protocol_num = [
                x
                for x in [
                    {"name": UptimeCheckTask.Protocol.HTTP, "val": http_num},
                    {"name": UptimeCheckTask.Protocol.TCP, "val": tcp_num},
                    {"name": UptimeCheckTask.Protocol.UDP, "val": udp_num},
                ]
                if x["val"] != 0
            ]

            # 展示可用率最低top3任务(优先展示非停用任务，若非停用任务不足3个，则补充停用任务)
            top_three_tasks = sorted(
                [task for task in tasks_data if task["status"] != UptimeCheckTask.Status.STOPED],
                key=lambda x: x["available"],
            )[:MAX_DISPLAY_TASK]
            if len(top_three_tasks) < MAX_DISPLAY_TASK:
                top_three_tasks.extend(
                    [task for task in tasks_data if task["status"] == UptimeCheckTask.Status.STOPED][
                        : MAX_DISPLAY_TASK - len(top_three_tasks)
                    ]
                )
            group_data.append(
                {
                    "id": group.id,
                    "top_three_tasks": top_three_tasks,
                    "protocol_num": protocol_num,
                    "logo": group.logo,
                    "name": group.name,
                    "alarm_num": alarm_num,
                    "all_tasks": tasks_data,
                    "bk_biz_id": group.bk_biz_id,
                }
            )

        # 用于给前端判断无拨测任务时是否需要先指引用户创建拨测节点
        has_node = (
            UptimeCheckNode.objects.filter(bk_biz_id=bk_biz_id).exists()
            if bk_biz_id
            else UptimeCheckNode.objects.all().exists()
        ) or (UptimeCheckNode.objects.filter(is_common=True).exists())

        return {"group_data": group_data, "task_data": all_tasks_data, "has_node": has_node}


class LocationSerializer(serializers.Serializer):
    country = serializers.CharField(required=True, label=_("国家"))
    city = serializers.CharField(required=True, label=_("城市"))


class NodeTargetConfSerializer(serializers.Serializer):
    ip = serializers.CharField(required=True, label=_("ip"))
    bk_cloud_id = serializers.IntegerField(required=True, label=_("云区域ID"))
    bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))


class NodeConfSerializer(serializers.Serializer):
    is_common = serializers.BooleanField(required=False, default=False, label=_("是否为通用节点"))
    name = serializers.CharField(required=True, label=_("节点名称"))
    carrieroperator = serializers.ChoiceField(
        required=True, choices=[_("内网"), _("联通"), _("移动"), _("电信"), _("其他")], label=_("外网运营商")
    )
    location = LocationSerializer()


class TaskTargetConfSerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
    node_id_list = serializers.ListField(required=False, label=_("节点ID列表"))
    node_list = serializers.ListField(required=False, label=_("节点配置列表"))


class CollectorConfSerializer(serializers.Serializer):
    groups = serializers.CharField(required=False, default="", allow_blank=True, label=_("分组名称"))
    protocol = serializers.ChoiceField(required=True, choices=["TCP", "UDP", "HTTP", "ICMP"], label=_("协议类型"))
    name = serializers.CharField(required=True, label=_("任务名称"))
    location = serializers.DictField(required=True, label=_("地理位置"))
    config = serializers.DictField(required=True, label=_("采集配置信息"))


class ConfListSerializer(serializers.Serializer):
    target_conf = NodeTargetConfSerializer()
    node_conf = NodeConfSerializer()


class ImportUptimeCheckNodeResource(Resource):
    class RequestSerializer(serializers.Serializer):
        conf_list = ConfListSerializer(many=True, required=True, label=_("节点配置列表"))
        bk_biz_id = serializers.IntegerField(required=False, default=0, label=_("业务ID"))

    def import_node(self, item_data, bk_biz_id):
        if not item_data["target_conf"]["bk_biz_id"]:
            item_data["target_conf"]["bk_biz_id"] = bk_biz_id

        try:
            create_data = {k: v for k, v in list(item_data["target_conf"].items()) if k != "bk_cloud_id"}
            create_data.update(item_data["node_conf"])
            create_data["plat_id"] = item_data["target_conf"]["bk_cloud_id"]
            if not create_data["bk_biz_id"]:
                raise CustomException(_("未填写业务ID,请检查配置"))
            node = UptimeCheckNode.objects.filter(
                ip=create_data["ip"],
                plat_id=create_data["plat_id"],
                is_deleted=False,
                bk_biz_id=create_data["bk_biz_id"],
            )
            if node:
                node_obj = node[0]
            else:
                result = resource.cc.host_detail(create_data["ip"], create_data["plat_id"], create_data["bk_biz_id"])
                if not result:
                    raise CustomException(_("业务下没有该主机，请检查配置"))
                node_obj = UptimeCheckNode.objects.create(**create_data)

            node_obj.install_agent()
            return {"result": True, "detail": {"node_id": node_obj.id, "target_conf": item_data["target_conf"]}}
        except Exception as e:
            return {"result": False, "detail": {"target_conf": item_data["target_conf"], "error_mes": str(e)}}

    def perform_request(self, data):
        bk_biz_id = data["bk_biz_id"]
        results = []
        conf_list = data["conf_list"]
        for item_data in conf_list:
            result = self.import_node(item_data, bk_biz_id)
            results.append(result)

        return handel_result(results)


class ConfSerializer(serializers.Serializer):
    target_conf = TaskTargetConfSerializer()
    collector_conf = CollectorConfSerializer()
    monitor_conf = serializers.ListField(required=False, default=[], label=_("监控策略配置"))


class ImportUptimeCheckTaskResource(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        conf_list = ConfSerializer(many=True, label=_("配置列表"))

    @property
    def http_config(self):
        return {
            "urls": "",
            "method": "",
            "timeout": 3000,
            "period": 1,
            "request": None,
            "headers": [],
            "response_code": "",
            "response": None,
            "insecure_skip_verify": False,
            "response_format": "in",
        }

    @property
    def icmp_config(self):
        return {"ip_list": [], "period": 1, "max_rtt": "", "total_num": "", "size": ""}

    @property
    def tcp_udp_config(self):
        return {"ip_list": [], "port": "", "period": 1, "timeout": 3000, "response": None, "response_format": "in"}

    def get_nodes(self, data, bk_biz_id):
        node_id_list = data["target_conf"].get("node_id_list", [])
        node_list = data["target_conf"].get("node_list", [])
        if not data["target_conf"]["bk_biz_id"]:
            data["target_conf"]["bk_biz_id"] = bk_biz_id

        for i in node_list:
            if not i["target_conf"]["bk_biz_id"]:
                i["target_conf"]["bk_biz_id"] = bk_biz_id

        if not node_list and not node_id_list:
            raise CustomException(_("下发配置缺少节点信息，请填写node_list或node_id_list"))
        for i in node_id_list:
            try:
                UptimeCheckNode.objects.get(Q(id=i, bk_biz_id=bk_biz_id) | Q(id=i, is_common=True))
            except Exception:
                raise CustomException(_("节点{}不存在，请检查节点信息").format(i))

        result_id_list = []
        if node_list:
            result = ImportUptimeCheckNodeResource().request({"conf_list": node_list})
            if result["failed"]["total"] > 0:
                raise CustomException(_("节点创建失败，请检查节点创建信息，{}").format(result["failed"]["detail"]))
            result_id_list = [i["node_id"] for i in result["success"]["detail"]]

        node_id_list.extend(result_id_list)
        nodes = UptimeCheckNode.objects.filter(
            Q(bk_biz_id=data["target_conf"]["bk_biz_id"], id__in=node_id_list) | Q(id__in=node_id_list, is_common=True)
        )
        if not nodes:
            raise CustomException(_("节点不存在，请检查节点配置"))
        return nodes, node_id_list

    def get_groups(self, group_names, bk_biz_id):
        group_name_list = group_names.split(",")
        groups = UptimeCheckGroup.objects.filter(name__in=group_name_list, bk_biz_id=bk_biz_id)
        return groups

    def create_task(self, data, bk_biz_id):
        own_bk_biz_id = data["target_conf"]["bk_biz_id"] if data["target_conf"]["bk_biz_id"] else bk_biz_id
        nodes, node_id_list = self.get_nodes(data, own_bk_biz_id)
        groups = self.get_groups(data["collector_conf"]["groups"], bk_biz_id)
        task_create_data = data["collector_conf"]
        if task_create_data["protocol"] == "HTTP":
            if not task_create_data["config"].get("urls", "") or not task_create_data["config"].get("method", ""):
                raise CustomException(_("config缺少参数urls或method，请检查参数"))

            config = self.http_config
            config.update(task_create_data["config"])
            task_create_data["config"] = config
        elif task_create_data["protocol"] == "ICMP":
            if not task_create_data["config"].get("ip_list", []):
                raise CustomException(_("config缺少参数ip_list，请检查参数"))
            config = self.icmp_config
            config.update(task_create_data["config"])
            task_create_data["config"] = config
            task_create_data["config"]["hosts"] = [{"ip": i} for i in task_create_data["config"]["ip_list"]]
            del task_create_data["config"]["ip_list"]
        else:
            if not task_create_data["config"].get("ip_list", []) or not task_create_data["config"].get("port", 0):
                raise CustomException(_("config缺少参数ip_list或port，请检查参数"))
            config = self.tcp_udp_config
            config.update(task_create_data["config"])
            task_create_data["config"] = config
            task_create_data["config"]["hosts"] = [{"ip": i} for i in task_create_data["config"]["ip_list"]]
            del task_create_data["config"]["ip_list"]

        task_create_data["bk_biz_id"] = bk_biz_id
        del task_create_data["groups"]

        # 先测试任务，确定可用后才可保存
        resource.uptime_check.test_task(
            {
                "config": task_create_data["config"],
                "protocol": task_create_data["protocol"],
                "node_id_list": node_id_list,
            }
        )

        tasks = UptimeCheckTask.objects.filter(name=task_create_data["name"])
        if tasks:
            tasks.update(**task_create_data)
            task_obj = tasks[0]
        else:
            task_obj = UptimeCheckTask.objects.create(**task_create_data)
        task_obj.nodes = nodes
        task_obj.groups = groups
        task_obj.save()
        return task_obj

    def import_task(self, item_data, bk_biz_id):
        try:
            task_obj = self.create_task(item_data, bk_biz_id)

            # 如果没有传入monitor_conf则生成默认配置
            if item_data.get("monitor_conf"):
                task_obj.status = task_obj.Status.STARTING
                task_obj.save()
                monitor_conf_list = item_data["monitor_conf"]
                for monitor_conf in monitor_conf_list:
                    monitor_conf.update(
                        {
                            "solution_display": _("不处理，仅通知"),
                            "solution_notice": [],
                            "solution_params_replace": "",
                            "solution_task_id": "",
                            "solution_type": "job",
                            "solution_is_enable": False,
                            "monitor_id": 0,
                            "where_sql": "(task_id={})".format(task_obj.id),
                            "task_id": task_obj.id,
                            "bk_biz_id": task_obj.bk_biz_id,
                        }
                    )
                    resource.config.save_alarm_strategy(monitor_conf)

            # 创建下发拨测任务
            task_obj.deploy()
            return {"result": True, "detail": {"task_name": task_obj.name}}
        except Exception as e:
            return {"result": False, "detail": {"task_name": item_data["collector_conf"]["name"], "error_mes": str(e)}}

    def perform_request(self, data):
        bk_biz_id = data["bk_biz_id"]
        results = []
        for item_data in data["conf_list"]:
            result = self.import_task(item_data, bk_biz_id)
            results.append(result)

        return handel_result(results)


def handel_result(results):
    real_result = {"success": {"total": 0, "detail": []}, "failed": {"total": 0, "detail": []}}
    for i in results:
        if i["result"]:
            real_result["success"]["total"] += 1
            real_result["success"]["detail"].append(i["detail"])
        else:
            real_result["failed"]["total"] += 1
            real_result["failed"]["detail"].append(i["detail"])

    return real_result


class SelectUptimeCheckNodeResource(Resource):
    """
    节点选择器
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.CharField(required=True, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]

        host_list = resource.commons.host_region_isp_info(bk_biz_id=bk_biz_id)
        node_list = UptimeCheckNode.objects.filter(bk_biz_id=bk_biz_id)
        node_ip_list = [node.ip for node in node_list]

        # 已建节点标识is_built
        for host in host_list:
            if host["ip"] in node_ip_list:
                host["is_built"] = True
            else:
                host["is_built"] = False
        return host_list


class GetRecentTaskDataResource(Resource):
    """
    获取任务最近可用率和响应时间
    """

    class RequestSerializer(serializers.Serializer):
        # 这里id用字符串，可以直接用于get_ts_data 查询条件
        task_id = serializers.CharField(required=True, label=_("任务ID"))
        type = serializers.ChoiceField(required=True, choices=["available", "task_duration"])

    def perform_request(self, validated_request_data):
        task_id = validated_request_data["task_id"]
        type = validated_request_data["type"]
        # 通过task_id获取到任务的协议和业务id，来拼接表名
        try:
            uptime_check_task = UptimeCheckTask.objects.get(pk=task_id)
        except UptimeCheckTask.DoesNotExist:
            raise CustomException(_("不存在id为%s的拨测任务") % task_id)
        protocol = uptime_check_task.protocol
        biz_id = uptime_check_task.bk_biz_id
        result_table_id = "{}_{}_{}".format(str(biz_id), UPTIME_CHECK_DB, protocol.lower())
        # 兼容不同版本
        table_name = resource.commons.trans_bkcloud_rt_bizid(result_table_id)
        # 获取某个node_id最近一个采集周期内的可用率和响应时间，如果没有则说明不可用
        end = arrow.utcnow().timestamp
        start = end - uptime_check_task.get_period() * 60
        filter_dict = {"time__gte": start * 1000, "time__lt": end * 1000, "task_id": task_id}
        value_fields = ["task_id", "node_id", type]

        data_source_class = load_data_source(DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES)
        data_source = data_source_class(
            table=table_name,
            metrics=[{"field": field} for field in value_fields],
            filter_dict=filter_dict,
        )
        data = data_source.query_data(limit=5)

        # 当前结果为空，则表示采集器未上报数据，如果结果不是空，则选择最新的数据返回
        if len(data) == 0:
            return {}
        else:
            if type == "available":
                return min(data, key=lambda x: x["available"])
            else:
                return max(data, key=lambda x: x["task_duration"])


class SelectCarrierOperator(Resource):
    """
    自定义运营商列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.CharField(required=True, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        isp_cn_list = [item["cn"] for item in ISP_LIST]
        carrieroperator_list = (
            UptimeCheckNode.objects.filter(bk_biz_id=bk_biz_id)
            .exclude(carrieroperator__in=isp_cn_list)
            .values_list("carrieroperator", flat=True)
            .distinct()
        )
        return list(carrieroperator_list)


class UptimeCheckNodeInfoResource(Resource):
    """
    提供给kernel api使用，查询uptime_check_node表的信息
    """

    class RequestSerializer(serializers.Serializer):
        ids = serializers.ListField(label=_("拨测节点id列表"), child=serializers.IntegerField(), required=True)

    def perform_request(self, data):
        result = list(UptimeCheckNode.origin_objects.filter(id__in=data["ids"]).values())

        data = {}
        for item in result:
            data[item["id"]] = item
        return data


class UptimeCheckTaskInfoResource(Resource):
    """
    提供给kernel api使用，查询uptime_check_task表的信息
    """

    class RequestSerializer(serializers.Serializer):
        ids = serializers.ListField(label=_("拨测任务id列表"), child=serializers.IntegerField(), required=True)

    def perform_request(self, data):
        result = list(UptimeCheckTask.origin_objects.filter(id__in=data["ids"]).values())

        data = {}
        for item in result:
            data[item["id"]] = item
        return data


class TopoTemplateHostResource(Resource):
    """
    如果存在动态节点，则返回动态节点下相应的ip
    """

    def perform_request(self, hosts):
        new_hosts = []
        if len(hosts) and hosts[0].get("bk_obj_id"):

            # 目标不能混用，如果第一个元素就是模板，则可以直接批量查询
            bk_obj_id = hosts[0]["bk_obj_id"]
            bk_biz_id = hosts[0]["bk_biz_id"]

            if bk_obj_id in [TargetNodeType.SET_TEMPLATE, TargetNodeType.SERVICE_TEMPLATE]:
                bk_inst_ids = [target["bk_inst_id"] for target in hosts]
                # 模板
                new_hosts.extend(
                    api.cmdb.get_host_by_template(bk_biz_id=bk_biz_id, bk_obj_id=bk_obj_id, template_ids=bk_inst_ids)
                )
            else:
                # 动态拓扑
                biz_hosts = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id)
                # 动态拓扑可能存在多种bk_obj_id混用的情况，需要遍历获取bk_obj_id
                for host in hosts:
                    bk_obj_id = host["bk_obj_id"]
                    bk_inst_id = host["bk_inst_id"]
                    if bk_obj_id == "biz":
                        new_hosts.extend([host for host in biz_hosts])
                    elif bk_obj_id == "set":
                        new_hosts.extend([host for host in biz_hosts if bk_inst_id in set(host.bk_set_ids)])
                    elif bk_obj_id == "module":
                        new_hosts.extend([host for host in biz_hosts if bk_inst_id in set(host.bk_module_ids)])

            new_hosts = [{"ip": host.ip} for host in new_hosts]
        else:
            new_hosts = [{"ip": host["ip"]} for host in hosts]

        return [dict(target) for target in {tuple(host.items()) for host in new_hosts}]


class UptimeCheckTargetDetailResource(Resource):
    """
    拨测目标详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"), required=True)
        bk_obj_id = serializers.CharField(label=_("目标类型"), required=True)
        target_hosts = serializers.ListField(label=_("目标信息"), required=True)

    def perform_request(self, validated_data):
        info_func_map = {
            TargetNodeType.INSTANCE: resource.commons.get_host_instance_by_ip,
            TargetNodeType.TOPO: resource.commons.get_host_instance_by_node,
            TargetNodeType.SET_TEMPLATE: resource.commons.get_nodes_by_template,
            TargetNodeType.SERVICE_TEMPLATE: resource.commons.get_nodes_by_template,
        }
        bk_obj_id = validated_data["bk_obj_id"]
        bk_biz_id = validated_data["bk_biz_id"]
        target_hosts = validated_data["target_hosts"]
        params = {"bk_biz_id": bk_biz_id}
        if bk_obj_id == TargetNodeType.INSTANCE:
            params["ip_list"] = [{"ip": x["ip"]} for x in target_hosts]
            params["bk_biz_ids"] = [bk_biz_id]
        elif bk_obj_id in [TargetNodeType.SET_TEMPLATE, TargetNodeType.SERVICE_TEMPLATE]:
            params["bk_obj_id"] = bk_obj_id
            params["bk_inst_type"] = "HOST"
            params["bk_inst_ids"] = [inst["bk_inst_id"] for inst in target_hosts]
        else:
            for target_item in target_hosts:
                if "bk_biz_id" not in target_item:
                    target_item.update(bk_biz_id=bk_biz_id)
            params["node_list"] = target_hosts

        return {
            "bk_obj_type": "HOST",
            "bk_target_type": bk_obj_id,
            "bk_target_detail": info_func_map[bk_obj_id](params),
        }
