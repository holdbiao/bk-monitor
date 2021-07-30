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


import logging

from django.conf import settings

from alarm_backends.core.cache.cmdb import ModuleManager
from alarm_backends.core.cache.cmdb.business import BusinessManager
from alarm_backends.core.cache.cmdb.host import HostManager

logger = logging.getLogger("action")


def get_business_roles(bk_biz_id):
    """
    获取业务角色
    :param bk_biz_id: 业务ID
    :return: dict
    {
        "bk_biz_maintainer": []
        "bk_biz_productor": []
        "bk_biz_developer": []
        "bk_biz_tester": []
    }
    """
    business = BusinessManager.get(bk_biz_id)
    return {role: getattr(business, role, []) for role in settings.AUTHORIZED_ROLES}


def get_host_operator(ip, bk_cloud_id):
    """
    获取主机负责人，如果没有则尝试获取第一个模块负责人
    :param ip: IP地址
    :param bk_cloud_id: 云区域ID
    :return: list
    """
    host = HostManager.get(ip, bk_cloud_id)

    if not host:
        return []

    if host.operator:
        return host.operator

    for bk_module_id in host.bk_module_ids:
        module = ModuleManager.get(bk_module_id)
        if module:
            return module.operator
    return []


def get_host_bak_operator(ip, bk_cloud_id):
    """
    获取备份负责人，如果没有则尝试获取第一个模块备份负责人
    :param ip: IP地址
    :param bk_cloud_id: 云区域ID
    :return: list
    """
    host = HostManager.get(ip, bk_cloud_id)

    if not host:
        return []

    if host.bk_bak_operator:
        return host.bk_bak_operator

    for bk_module_id in host.bk_module_ids:
        module = ModuleManager.get(bk_module_id)
        if module:
            return module.bk_bak_operator
    return []


def collect_info_dumps(collect_info):
    """
    汇总信息转为字符串，方便日志检索
    :param collect_info: 汇总信息
    :return: str
    """
    return ";".join(["{}:{}".format(key, collect_info[key]) for key in collect_info])


def get_target_dimension_keys(agg_dimensions, scenario):
    """
    目标维度名称
    :param scenario: 监控对象
    :param agg_dimensions: 聚合维度
    :return: 目标维度
    """
    target_dimensions = []

    # 去除目标维度
    if scenario in ["os", "host_process"]:
        if "bk_target_ip" in agg_dimensions:
            target_dimensions.extend(["bk_target_ip", "bk_target_cloud_id"])
        elif "ip" in agg_dimensions:
            target_dimensions.extend(["ip", "bk_cloud_id"])
        else:
            target_dimensions.extend(["bk_obj_id", "bk_inst_id"])
    elif scenario in ["service_module", "component", "service_process"]:
        if "bk_target_service_instance_id" in agg_dimensions:
            target_dimensions.append("bk_target_service_instance_id")
        else:
            target_dimensions.extend(["bk_obj_id", "bk_inst_id"])

    return target_dimensions


def get_display_dimensions(event, strategy):
    """
    获取维度信息
    """
    agg_dimensions = strategy["item_list"][0]["rt_query_config"].get("agg_dimension", [])
    target_dimension_keys = get_target_dimension_keys(agg_dimensions, strategy["scenario"])
    display_dimensions = {
        "{}={}".format(value["display_name"], value["display_value"])
        for key, value in list(event.origin_alarm["dimension_translation"].items())
        if key not in target_dimension_keys and key in agg_dimensions
    }
    return display_dimensions


def get_display_targets(event, strategy):
    agg_dimensions = strategy["item_list"][0]["rt_query_config"].get("agg_dimension", [])
    target_dimension_keys = get_target_dimension_keys(agg_dimensions, strategy["scenario"])
    display_targets = []
    dimensions = event.origin_alarm["dimension_translation"]

    if "ip" in target_dimension_keys or "bk_target_ip" in target_dimension_keys:
        ip = dimensions.get("bk_target_ip") or dimensions.get("ip")
        if ip:
            display_targets.append(ip["display_value"])
    elif "bk_target_service_instance_id" in target_dimension_keys:
        service_instance_id = dimensions.get("bk_target_service_instance_id")
        if service_instance_id:
            display_targets.append(service_instance_id["display_value"])
    elif "bk_obj_id" in target_dimension_keys and "bk_inst_id" in target_dimension_keys:
        bk_obj_id = dimensions.get("bk_obj_id")
        bk_inst_id = dimensions.get("bk_inst_id")
        if bk_obj_id and bk_inst_id:
            display_targets.append("{}-{}".format(bk_obj_id["display_value"], bk_inst_id["display_value"]))

    return display_targets
