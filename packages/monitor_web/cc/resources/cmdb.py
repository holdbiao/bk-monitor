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
import logging
from collections import defaultdict

from bkmonitor.utils.thread_backend import InheritParentThread
from core.drf_resource import resource
from bkmonitor.utils.cache import CacheType, using_cache
from bkmonitor.utils.common_utils import DictObj, to_dict
from bkmonitor.utils.country import CHINESE_PROVINCE_MAP, COUNTRY_MAP, ISP_LIST
from bkmonitor.utils.host import Host
from core.drf_resource import api
from monitor.constants import AGENT_STATUS


logger = logging.getLogger(__name__)


def topo_inst_dict(bk_biz_id):
    queue = [copy.deepcopy(topo_tree(bk_biz_id))]
    inst_obj_dict = {}

    while queue:
        node = queue.pop()
        inst_obj_dict["{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])] = node
        if not node.get("topo_link"):
            node["topo_link"] = ["{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])]
            node["topo_link_display"] = [node["bk_inst_name"]]
        for child in node["child"]:
            child["topo_link"] = node["topo_link"] + ["{}|{}".format(child["bk_obj_id"], child["bk_inst_id"])]
            child["topo_link_display"] = node["topo_link_display"] + [child["bk_inst_name"]]

        queue = queue + node["child"]
        del node["child"]
    return inst_obj_dict


def hosts(cc_biz_id):
    data = api.cmdb.raw_hosts(cc_biz_id)
    host_list = Host.create_host_list(data)
    _code_replace(host_list)
    return host_list


def agent_status(cc_biz_id, host_list, ip_info_list=None):
    """获取agent状态信息
    agent状态详细分成4个状态：正常，离线，未安装。已安装，无数据。
    """
    result = collections.defaultdict(int)
    if ip_info_list is None:
        ip_info_list = list()
    for host in host_list:
        if host.bk_host_innerip:
            ip_info_list.append({"ip": host.bk_host_innerip, "bk_cloud_id": host.bk_cloud_id[0]["bk_inst_id"]})
    if not ip_info_list:
        return {}

    def batch_get_agent_status(ips, output_dict):
        try:
            api_result = api.gse.get_agent_status(hosts=ips)
            output_dict.update(api_result)
        except Exception:
            pass

    status_dict = dict()
    bath_size = 1000
    # fmt: off
    th_list = [
        InheritParentThread(target=batch_get_agent_status, args=(ip_info_list[i: (i + bath_size)], status_dict))
        for i in range(0, len(ip_info_list), bath_size)
    ]
    # fmt: on
    list([t.start() for t in th_list])
    list([t.join() for t in th_list])

    for key, value in list(status_dict.items()):
        host_id = Host(dict(ip=value["ip"], bk_cloud_id=value["bk_cloud_id"]), cc_biz_id).host_id
        exist = bool(value["bk_agent_alive"])
        if not exist:
            result[host_id] = AGENT_STATUS.NOT_EXIST
            continue
        else:
            result[host_id] = AGENT_STATUS.ON

    return result


def hosts_and_status(cc_biz_id, host_list_info=None, agent_dict_info=None):
    host_list = hosts(cc_biz_id)
    hosts_agent_status = agent_status(cc_biz_id, host_list)
    if (host_list_info and agent_dict_info) is not None:
        host_list_info.extend(host_list)
        agent_dict_info.update(hosts_agent_status)
    return host_list, hosts_agent_status


def get_host_and_status(cc_biz_id=None):
    if cc_biz_id:
        biz_ids = [cc_biz_id]
    else:
        result = api.cmdb.get_business()
        biz_ids = [biz.bk_biz_id for biz in result]

    host_list = list()
    agent_dict = dict()
    th_list = [InheritParentThread(target=hosts_and_status, args=(i, host_list, agent_dict)) for i in biz_ids]
    list([t.start() for t in th_list])
    list([t.join() for t in th_list])

    return host_list, agent_dict, biz_ids


def process_port_info(cc_biz_id, host_id_mapping_ip, limit_port_num=None):
    pp_info = defaultdict(list)
    bk_host_id = None
    if len(host_id_mapping_ip) == 1:
        bk_host_id = list(host_id_mapping_ip.keys())[0]
    result = resource.cc.get_process(cc_biz_id, bk_host_id=bk_host_id)

    for pp in result:
        if pp["bk_host_id"] not in host_id_mapping_ip:
            continue

        host_id = host_id_mapping_ip[pp["bk_host_id"]]
        from monitor_api.models import ProcessPortIndex

        pp_instance = DictObj(
            {
                "host_id": host_id,
                "name": pp["bk_process_name"],
                "protocol": pp["protocol"],
                "ports": ProcessPortIndex.parse_cc_ports(pp["port"]),
                "status": AGENT_STATUS.UNKNOWN,
            }
        )
        if limit_port_num:
            pp_instance.ports = pp_instance.ports[:limit_port_num]
        pp_info[host_id].append(pp_instance)
    return pp_info


def _code_replace(host_list):
    """地理位置、运营商、系统类型等枚举信息替换"""
    for host in host_list:
        if "bk_state_name" not in host:
            host["bk_province_name"] = ""
            host["bk_state_name"] = ""
            host["Region"] = ""
            continue

        country_ch_name = host["bk_state_name"]
        province_ch_name = ""
        isp_name = host["bk_isp_name"]

        if host["bk_province_name"] in CHINESE_PROVINCE_MAP:
            province_ch_name = "{}".format(CHINESE_PROVINCE_MAP[host["bk_province_name"]]["cn"])

        if host["bk_state_name"] in COUNTRY_MAP:
            country_ch_name = "{}".format(COUNTRY_MAP[host["bk_state_name"]]["cn"])

        for isp in ISP_LIST:
            if host["bk_isp_name"] == isp["code"]:
                isp_name = "{}".format(isp["cn"])
                break

        host["bk_province_name"] = province_ch_name
        host["bk_state_name"] = country_ch_name
        host["Region"] = province_ch_name
        host["bk_isp_name"] = isp_name

    return host_list


# @using_cache(CacheType.CC)
def topo_tree(bk_biz_id):
    result = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)
    return to_dict(result)


def plat_id_gse_to_cc(plat_id):
    """
    （deprecated）将gse的plat_id转换成cc的plat_id
    """
    return plat_id


def plat_id_cc_to_gse(plat_id):
    """
    （deprecated）将cc的plat_id转换成gse的plat_id
    """
    return plat_id


def plat_id_cc_to_job(plat_id):
    """
    将cc的plat_id转换成job的plat_id
    """
    return plat_id


def plat_id_job_to_cc(plat_id):
    """
    将job的plat_id转换成cc的plat_id
    """
    return plat_id


def host_detail(ip, bk_cloud_id, bk_biz_id):
    host_objects = hosts(bk_biz_id)
    for host in host_objects:
        if host.bk_host_innerip == ip and host.bk_cloud_id[0]["bk_inst_id"] == bk_cloud_id:
            host["cc_app_module"] = [x["bk_inst_id"] for x in host["module"]]
            host["cc_topo_set"] = [x["bk_inst_id"] for x in host["set"]]
            return host


@using_cache(CacheType.BIZ, user_related=False)
def get_blueking_biz_id():
    """
    获取蓝鲸业务所属的业务ID
    """
    result = api.cmdb.get_business()
    for biz in result:
        if biz.bk_biz_name == "蓝鲸":
            return biz.bk_biz_id
    return None


def get_monitor_biz_id():
    """
    获取蓝鲸监控所属业务ID
    """
    return get_blueking_biz_id()


def get_bkdata_biz_id():
    """
    获取计算平台业务ID
    """
    return get_blueking_biz_id()


# TODO: 以下函数内部版逻辑需要用到，接口暂时不做改动
def get_process(bk_biz_id, bk_host_id=None):
    """
    查询进程信息
    """
    result = api.cmdb.get_process(bk_biz_id=bk_biz_id, bk_host_id=bk_host_id)
    return to_dict(result)
