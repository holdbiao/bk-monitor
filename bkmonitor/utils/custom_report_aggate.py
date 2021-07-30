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
import os
import arrow
import socket
import logging
import requests

from django.conf import settings

from metadata.models import DataSource
from bkmonitor.utils.custom_report_tools import custom_report_tool
from alarm_backends.management.commands.hash_ring import HashRing
from alarm_backends.core.lock.service_lock import share_lock

logger = logging.getLogger("monitor")


def fetch_leader_ip():
    """
    获取上报主节点
    :return: IP
    """
    command = HashRing("run_access")
    _, host_targets = command.dispatch_all_hosts(command.query_for_hosts())
    for target_host, targets in list(host_targets.items()):
        if settings.AGGREGATION_BIZ_ID in targets:
            return target_host
    return ""


def send_metrics_to_aggate_gateway(metrics):
    """
    使用UDP发送指标信息到汇聚网关

    Args:
        address (str): 汇聚网关服务器
        port (int): 汇聚网关端口
        metrics (str): 指标信息

    Example:
        send_metrics_to_aggate_gateway('http_requests_total{method="post",code="200"} 1027\n')
    """

    address = fetch_leader_ip()
    if not address:
        logger.error("Custom report aggate gate address doesn't set up.")
        return

    port = os.getenv("aggate_listen_udp", 10207)

    # 创建udp套接字,
    # AF_INET表示ip地址的类型是ipv4，
    # SOCK_DGRAM表示传输的协议类型是udp
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 要发送的ip地址和端口（元组的形式）
    send_addr = (address, port)
    # 补充换行符
    metrics += "\n"
    # 发送消息
    udp_socket.sendto(metrics.encode("utf-8"), send_addr)
    # 关闭套接字
    udp_socket.close()


@share_lock()
def fetch_aggated_metrics_data():
    """
    拉取聚合网关数据并上报到1100011
    """
    address = fetch_leader_ip()
    if not address:
        logger.error("Aggated data report 1100011 failed, because no leader node.")
        return

    port = os.getenv("aggate_listen_http", 10206)
    report_tool = custom_report_tool(settings.CUSTOM_REPORT_DEFAULT_DATAID)

    report_data = []
    metrics_json = requests.get(f"http://{address}:{port}/metrics?format=json").json()
    for metric_id, metric_data in metrics_json.items():
        for data in metric_data.get("metric"):
            single_data = {
                # 指标，必需项
                "metrics": {metric_id: data["untyped"]["value"]},
                # 来源标识
                "target": settings.BK_PAAS_INNER_HOST,
                # 数据时间，精确到毫秒，非必需项
                "timestamp": arrow.now().timestamp * 1000,
            }

            # 补充维度
            dimension = {}
            labels = data.get("label", [])
            for label in labels:
                dimension[label["name"]] = label["value"]
            single_data["dimension"] = dimension
            report_data.append(single_data)

    report_tool.send_data_by_http(
        report_data, access_token=DataSource.objects.get(bk_data_id=settings.CUSTOM_REPORT_DEFAULT_DATAID).token
    )
