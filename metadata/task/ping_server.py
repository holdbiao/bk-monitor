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

from __future__ import absolute_import, print_function, unicode_literals

import logging
from collections import defaultdict

from django.conf import settings

from core.drf_resource import api
from metadata.models.ping_server import PingServerSubscriptionConfig

logger = logging.getLogger("metadata")


def refresh_ping_server_config_to_node_man():
    """
    刷新Ping Server的ip列表配置

    1. 获取CMDB下的所有主机ip
    2. 获取云区域下的所有ProxyIP
    3. 根据Hash环，将同一云区域下的ip分配到不同的Proxy
    4. 通过节点管理订阅任务将分配好的ip下发到机器
    """
    # metadata模块不应该引入alarm_backends下的文件，这里通过函数内引用，避免循环引用问题
    from alarm_backends.management.hashring import HashRing
    from alarm_backends.core.cache.cmdb.host import HostManager

    # 1. 获取CMDB下的所有主机ip
    try:
        all_hosts = HostManager.all()
    except Exception:  # noqa
        logger.exception("CMDB的主机缓存获取失败。获取不到主机，有可能会导致pingserver不执行")
        return

    cloud_to_hosts = defaultdict(list)
    for h in all_hosts:
        if h.ignore_monitoring or not h.bk_host_innerip:
            continue
        cloud_to_hosts[h.bk_cloud_id].append(
            {"ip": h.bk_host_innerip, "bk_cloud_id": h.bk_cloud_id, "bk_biz_id": h.bk_biz_id}
        )

    # 2. 获取云区域下的所有ProxyIP
    for bk_cloud_id, target_ips in cloud_to_hosts.items():
        if int(bk_cloud_id) == 0:
            proxies = [{"inner_ip": ip} for ip in settings.CUSTOM_REPORT_DEFAULT_PROXY_IP]
            target_hosts = [
                {"ip": proxy_ip, "bk_cloud_id": 0, "bk_supplier_id": 0}
                for proxy_ip in settings.CUSTOM_REPORT_DEFAULT_PROXY_IP
            ]
        else:
            try:
                proxy_list = api.node_man.get_proxies(bk_cloud_id=bk_cloud_id)
                proxies = []
                target_hosts = []
                for p in proxy_list:
                    if p["status"] != "RUNNING":
                        logger.warning(
                            "proxy({}) can not be use with pingserver, it's not running".format(p["inner_ip"])
                        )
                    else:
                        proxies.append(p)
                        target_hosts.append(
                            {"ip": p["inner_ip"], "bk_cloud_id": p.get("bk_cloud_id", 0), "bk_supplier_id": 0}
                        )
            except Exception:  # noqa
                logger.exception("从节点管理获取云区域({})下的ProxyIP列表失败".format(bk_cloud_id))
                continue
        if not proxies:
            logger.error("云区域({})下无可用proxy节点，相关pingserver服务不可用".format(bk_cloud_id))
            continue
        proxies_ips = {p["inner_ip"]: 1 for p in proxies}

        # 3. 根据Hash环，将同一云区域下的ip分配到不同的Proxy。
        host_targets = defaultdict(list)
        if settings.ENABLE_PING_ALARM:
            # 如果开启了PING服务，则按hash分配给不同的server执行
            host_ring = HashRing(proxies_ips)
            for target in target_ips:
                ip = target["ip"]
                host = host_ring.get_node(ip)
                host_targets[host].append(
                    {"target_ip": ip, "target_cloud_id": target["bk_cloud_id"], "target_biz_id": target["bk_biz_id"]}
                )
        else:
            # 如果关闭了PING服务，则清空目标Proxy上的任务iplist
            host_targets = {p["inner_ip"]: [] for p in proxies}

        # 针对直连区域做一定处理，如果关闭直连区域的PING采集，则清空目标Proxy上的任务iplist
        if int(bk_cloud_id) == 0 and not settings.ENABLE_DIRECT_AREA_PING_COLLECT:
            host_targets = {p["inner_ip"]: [] for p in proxies}

        # 4. 通过节点管理订阅任务将分配好的ip下发到机器
        try:
            PingServerSubscriptionConfig.create_subscription(bk_cloud_id, host_targets, target_hosts)
        except Exception:  # noqa
            logger.exception("下发pingserver订阅任务失败，bk_cloud_id({}), proxies_ips({})".format(bk_cloud_id, proxies_ips))
