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
import logging
from collections import defaultdict
from typing import Dict, List

import typing
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy
from rest_framework import serializers

from api.cmdb.define import _split_member_list
from bkmonitor.utils.cache import CacheType, using_cache
from bkmonitor.utils.common_utils import to_dict
from bkmonitor.utils.thread_backend import ThreadPool
from core.drf_resource import api, CacheResource
from core.drf_resource.base import Resource
from core.errors.api import BKAPIError
from constants.cmdb import TargetNodeType
from . import client
from .define import Business, Host, Module, Process, ServiceInstance, Set, TopoTree

logger = logging.getLogger(__name__)


def split_inner_host(bk_host_innerip_str):
    bk_host_innerip = _split_member_list(bk_host_innerip_str)
    if not bk_host_innerip:
        logger.warning("invalid bk_host_innerip: {}".format(bk_host_innerip_str))
        return ""
    return bk_host_innerip[0]


def batch_request(func, params, get_data=lambda x: x["info"], get_count=lambda x: x["count"], limit=1000):
    """
    并发请求接口
    :param func: 请求方法
    :param params: 请求参数
    :param get_data: 获取数据函数
    :param get_count: 获取总数函数
    :param limit: 一次请求数量
    :return: 请求结果
    """
    # 请求第一次获取总数
    result = func(page={"start": 0, "limit": 1}, **params)
    count = get_count(result)
    data = []
    start = 0

    # 根据请求总数并发请求
    pool = ThreadPool()
    futures = []
    while start < count:
        request_params = {"page": {"limit": limit, "start": start}}
        request_params.update(params)
        futures.append(pool.apply_async(func, kwds=request_params))

        start += limit

    pool.close()
    pool.join()

    # 取值
    for future in futures:
        data.extend(get_data(future.get()))

    return data


@using_cache(CacheType.CC_CACHE_ALWAYS, is_cache_func=lambda res: res)
def get_host_dict_by_biz(bk_biz_id, fields):
    """
    按业务查询主机（未实例化）
    :param bk_biz_id: 业务ID
    :type bk_biz_id: int
    :param fields: 查询字段
    :type fields: list
    :return: 主机列表
    :rtype: list
    """
    records = batch_request(client.list_biz_hosts_topo, {"bk_biz_id": bk_biz_id, "fields": fields})

    hosts = []
    for record in records:
        host = _host_from_raw(record, bk_biz_id)
        if host is not None:
            hosts.append(host)
    return hosts


def _host_from_raw(record, bk_biz_id):
    host = record["host"]

    host["bk_host_innerip"] = split_inner_host(host["bk_host_innerip"])
    if not host["bk_host_innerip"]:
        return None
    host["ip"] = host["bk_host_innerip"]
    topo = record["topo"]

    set_ids = []
    module_ids = []
    for set_info in topo:
        set_ids.append(set_info["bk_set_id"])
        for module_info in set_info["module"]:
            module_ids.append(module_info["bk_module_id"])

    host["bk_set_ids"] = set_ids
    host["bk_module_ids"] = module_ids
    host["operator"] = _split_member_list(host["operator"])
    host["bk_bak_operator"] = _split_member_list(host["bk_bak_operator"])
    host["bk_biz_id"] = bk_biz_id
    return host


def _host_full_cloud(host, clouds=None):
    # 获取云区域信息
    if clouds is None:
        clouds = api.cmdb.search_cloud_area()
    cloud_id_to_name = {cloud["bk_cloud_id"]: cloud["bk_cloud_name"] for cloud in clouds}
    host["bk_cloud_name"] = cloud_id_to_name.get(host["bk_cloud_id"], "")
    return host


@using_cache(CacheType.CC_BACKEND)
def _get_topo_tree(bk_biz_id):
    """
    获取业务拓扑树（未实例化）
    :param bk_biz_id: 业务ID
    :type bk_biz_id: int
    :return: 拓扑树
    :rtype: Dict
    """
    response_data = client.search_biz_inst_topo(bk_biz_id=bk_biz_id)
    if response_data:
        response_data = response_data[0]
    else:
        response_biz_data = api.cmdb.get_business(bk_biz_ids=[bk_biz_id])
        if response_biz_data:
            biz_data = response_biz_data[0]
            bk_inst_name = biz_data.bk_inst_name
        else:
            bk_inst_name = _("未知")

        response_data = {
            "host_count": 0,
            "default": 0,
            "bk_obj_name": _("业务"),
            "bk_obj_id": "biz",
            "service_instance_count": 0,
            "child": [],
            "service_template_id": 0,
            "bk_inst_id": bk_biz_id,
            "bk_inst_name": bk_inst_name,
        }

    # 添加空闲集群/模块
    internal_module = client.get_biz_internal_module(
        bk_biz_id=bk_biz_id, bk_supplier_account=settings.BK_SUPPLIER_ACCOUNT
    )
    if not internal_module["module"]:
        internal_module["module"] = []

    internal_module = dict(
        bk_obj_id="set",
        bk_obj_name=_("集群"),
        bk_inst_id=internal_module["bk_set_id"],
        bk_inst_name=internal_module["bk_set_name"],
        child=[
            dict(
                bk_obj_id="module",
                bk_obj_name=_("模块"),
                bk_inst_id=m["bk_module_id"],
                bk_inst_name=m["bk_module_name"],
                child=[],
            )
            for m in internal_module["module"] or []
        ],
    )

    response_data["child"] = [internal_module] + response_data["child"]
    return response_data


@using_cache(CacheType.CC_BACKEND)
def _get_service_instance_by_biz(bk_biz_id):
    """
    获取业务下所有服务实例
    :param bk_biz_id: 业务ID
    :return: 服务实例列表
    """
    return client.list_service_instance_detail(bk_biz_id=bk_biz_id)["info"]


def _trans_topo_node_to_module_ids(bk_biz_id: int, topo_nodes: Dict[str, typing.Iterable[int]]) -> typing.Set[int]:
    """
    将待查询的拓扑节点转为模块ID
    :param topo_nodes: 拓扑节点
    [
        "module": [1, 2],
        "set": [3, 4]
    ]
    :return: 模块ID列表
    :rtype: List[int]
    """

    # 取出模块ID
    module_ids = {int(module_id) for module_id in topo_nodes.pop("module", [])}

    # 如果没有待查询节点，则直接返回
    if not topo_nodes:
        return module_ids

    # 查询拓扑树
    topo_tree: Dict = _get_topo_tree(bk_biz_id)

    # 调整待查询拓扑节点结构，合并相同类型的节点
    for bk_obj_id in topo_nodes:
        topo_nodes[bk_obj_id] = {int(topo_node_id) for topo_node_id in topo_nodes[bk_obj_id]}

    # 广度优先遍历拓扑树，找到节点下所有的模块ID
    queue: List[Dict] = topo_tree["child"]
    while queue:
        node = queue.pop()

        # 如果该节点需要被查询，则标记其子节点
        if node.get("mark") or node["bk_inst_id"] in topo_nodes.get(node["bk_obj_id"], []):
            node["mark"] = True
            for child in node["child"]:
                child["mark"] = True

        if node["bk_obj_id"] == "module" and node.get("mark"):
            module_ids.add(node["bk_inst_id"])
        elif node["child"]:
            queue.extend(node["child"])

    return module_ids


class GetHostByTopoNode(CacheResource):
    """
    根据拓扑节点批量查询主机
    """

    class RequestSerializer(serializers.Serializer):
        class TopoNode(serializers.Serializer):
            bk_obj_id = serializers.CharField(label=_lazy("模型ID"), required=True)
            bk_inst_ids = serializers.ListField(label=_lazy("实例ID列表"), child=serializers.IntegerField(), default=dict)

        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        topo_nodes = serializers.DictField(label=_lazy("拓扑节点"), child=serializers.ListField(), required=False)
        # 注意，如果使用自定义fields参数，而不用默认Host.Fields参数，
        # 将可能导致缓存长时间无法刷新的情况，当前暂未发现有自定义fields的地方
        fields = serializers.ListField(label=_lazy("查询字段"), default=Host.Fields, allow_empty=True)

    def perform_request(self, params):
        hosts = get_host_dict_by_biz(params["bk_biz_id"], params["fields"])

        if params.get("topo_nodes", {}):
            # 将查询节点转换为模块ID
            module_ids = _trans_topo_node_to_module_ids(params["bk_biz_id"], params["topo_nodes"])

            # 按模块ID过滤主机
            hosts = [host for host in hosts if set(host["bk_module_ids"]) & module_ids]

        # 获取云区域信息
        clouds = api.cmdb.search_cloud_area()

        for host in hosts:
            _host_full_cloud(host, clouds)
        return [Host(host) for host in hosts if host["bk_host_innerip"]]


class GetHostByIP(CacheResource):
    class RequestSerializer(serializers.Serializer):
        class HostSerializer(serializers.Serializer):
            ip = serializers.CharField()
            bk_cloud_id = serializers.IntegerField(required=False)

        ips = HostSerializer(many=True)
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        search_outer_ip = serializers.BooleanField(label=_lazy("是否搜索外网IP"), required=False, default=False)
        fields = serializers.ListField(label=_lazy("查询字段"), allow_empty=True, default=Host.Fields)

    @staticmethod
    def process_params(params):
        cloud_dict = defaultdict(list)
        for host in params["ips"]:
            cloud_dict[host.get("bk_cloud_id", -1)].append(host["ip"])

        conditions = []
        for bk_cloud_id, ips in cloud_dict.items():
            condition = {"condition": "AND", "rules": [{"field": "bk_host_innerip", "operator": "in", "value": ips}]}
            if bk_cloud_id != -1:
                condition["rules"].append({"field": "bk_cloud_id", "operator": "equal", "value": bk_cloud_id})
            if params.get("search_outer_ip", False):
                conditions.append(
                    {"condition": "AND", "rules": [{"field": "bk_host_outerip", "operator": "in", "value": ips}]}
                )
            conditions.append(condition)

        if len(conditions) == 1:
            conditions = conditions[0]
        else:
            conditions = {"condition": "OR", "rules": conditions}

        return {"bk_biz_id": params["bk_biz_id"], "host_property_filter": conditions, "fields": params["fields"]}

    def perform_request(self, params):
        if not params["ips"]:
            return []

        # 获取云区域信息
        clouds = api.cmdb.search_cloud_area()

        # 获取主机信息
        params = self.process_params(params)
        records = batch_request(client.list_biz_hosts_topo, params)

        hosts = []
        for record in records:
            host = _host_from_raw(record, params["bk_biz_id"])
            if host is None:
                continue
            host = _host_full_cloud(host, clouds)
            hosts.append(Host(host))

        return hosts


class GetTopoTreeResource(Resource):
    """
    查询拓扑树接口
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1)

    def perform_request(self, params):
        return TopoTree(_get_topo_tree(params["bk_biz_id"]))


class GetBusiness(Resource):
    """
    查询业务详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_ids = serializers.ListField(
            label=_lazy("业务ID列表"), child=serializers.IntegerField(), required=False, default=[]
        )
        all = serializers.BooleanField(default=False)

    def perform_request(self, validated_request_data):
        # 查询全部业务
        response_data = client.search_business()["info"]

        # 按业务ID过滤出需要的业务信息
        if "bk_biz_ids" in validated_request_data:
            bk_biz_ids = set(validated_request_data["bk_biz_ids"])
            if bk_biz_ids:
                response_data = [topo for topo in response_data if topo["bk_biz_id"] in bk_biz_ids]

        business_list = [Business(**topo) for topo in self.filter_biz(response_data)]
        return business_list

    @classmethod
    def filter_biz(cls, bk_biz_list):
        return bk_biz_list


class GetModule(Resource):
    """
    查询模块详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_module_ids = serializers.ListField(label=_lazy("模块ID列表"), child=serializers.IntegerField(), required=False)
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1)
        service_template_ids = serializers.ListField(label=_lazy("服务模板ID列表"), required=False)

    def perform_request(self, params):
        # 查询业务下所有模块
        response_data = client.search_module(bk_biz_id=params["bk_biz_id"])["info"]

        # 按服务模版ID过滤
        if "service_template_ids" in params:
            service_template_ids = set(params["service_template_ids"])
            response_data = [topo for topo in response_data if topo.get("service_template_id") in service_template_ids]

        # 按模块ID过滤出需要的模块
        if "bk_module_ids" in params:
            bk_module_ids = set(params["bk_module_ids"])
            response_data = [topo for topo in response_data if topo["bk_module_id"] in bk_module_ids]

        for topo in response_data:
            topo["operator"] = _split_member_list(topo.get("operator", ""))
            topo["bk_bak_operator"] = _split_member_list(topo.get("bk_bak_operator", ""))

        return [Module(**topo) for topo in response_data]


class GetSet(Resource):
    """
    查询集群详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_set_ids = serializers.ListField(label=_lazy("集群ID列表"), child=serializers.IntegerField(), required=False)
        set_template_ids = serializers.ListField(label=_lazy("集群模板ID"), required=False)
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1)

    def perform_request(self, params):
        response_data = client.search_set(bk_biz_id=params["bk_biz_id"])["info"]

        # 按集群模块ID过滤
        if "set_template_ids" in params:
            set_template_ids = set(params["set_template_ids"])
            response_data = [topo for topo in response_data if topo["set_template_id"] in set_template_ids]

        # 按集群ID过滤
        if "bk_set_ids" in params:
            bk_set_ids = set(params["bk_set_ids"])
            response_data = [topo for topo in response_data if topo["bk_set_id"] in bk_set_ids]

        return [Set(**topo) for topo in response_data]


class GetServiceInstanceByTopoNode(Resource):
    """
    根据拓扑节点获取服务实例
    """

    class RequestSerializer(serializers.Serializer):
        class TopoNode(serializers.Serializer):
            bk_obj_id = serializers.CharField(label=_lazy("模型ID"), required=True)
            bk_inst_ids = serializers.ListField(label=_lazy("实例ID列表"), child=serializers.IntegerField(), default=dict)

        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        topo_nodes = serializers.DictField(label=_lazy("拓扑节点"), child=serializers.ListField(), required=False)

    def perform_request(self, params):
        service_instances = _get_service_instance_by_biz(params["bk_biz_id"])

        if params.get("topo_nodes", {}):
            # 将查询节点转换为模块ID
            module_ids = _trans_topo_node_to_module_ids(params["bk_biz_id"], params["topo_nodes"])
            service_instances = [instance for instance in service_instances if instance["bk_module_id"] in module_ids]

        for instance in service_instances:
            instance["service_instance_id"] = instance["id"]
        return [ServiceInstance(**instance) for instance in service_instances]


class GetServiceInstanceByID(Resource):
    """
    根据服务实例ID获取服务实例
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        service_instance_ids = serializers.ListField(label=_lazy("服务实例列表"), child=serializers.IntegerField())

    def perform_request(self, validated_request_data):
        params = {
            "bk_biz_id": validated_request_data["bk_biz_id"],
            "with_name": True,
            "service_instance_ids": validated_request_data["service_instance_ids"],
        }
        service_instances = client.list_service_instance_detail.request.cacheless(params)["info"]
        for instance in service_instances:
            instance["service_instance_id"] = instance["id"]
        return [ServiceInstance(**instance) for instance in service_instances]


class GetProcess(Resource):
    """
    根据服务实例ID获取服务实例
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        bk_host_id = serializers.IntegerField(label=_lazy("主机ID"), required=False, allow_null=True)

    def perform_request(self, validated_request_data):
        params = {
            "bk_biz_id": validated_request_data["bk_biz_id"],
        }
        if validated_request_data.get("bk_host_id"):
            params["bk_host_id"] = validated_request_data["bk_host_id"]
            response_data = client.list_service_instance_detail.request.cacheless(**params)["info"]
        else:
            response_data = client.list_service_instance_detail(**params)["info"]

        processes = []
        for service_instances in response_data:
            process_instances = service_instances["process_instances"] or []
            for process_instance in process_instances:
                process_params = {}
                # process info
                process_params.update(process_instance["process"])

                if process_params.get("bind_info"):
                    bind_info = process_params["bind_info"][0]
                    process_params.update(
                        {
                            "bind_ip": bind_info.get("ip", ""),
                            "port": bind_info.get("port", ""),
                            "bk_enable_port": bind_info.get("enable", True),
                            "protocol": bind_info.get("protocol", ""),
                        }
                    )

                if not process_params.get("bk_enable_port", True):
                    # 进程监控开关存在且状态为关闭，则不在监控平台展示和监控端口
                    process_params["port"] = ""

                # service_instance info
                process_params.update(process_instance["relation"])
                processes.append(Process(**process_params))
        return processes


class GetObjectAttribute(Resource):
    """
    查询对象属性
    """

    class RequestSerializer(serializers.Serializer):
        bk_obj_id = serializers.CharField(label=_lazy("模型ID"))

    def perform_request(self, validated_request_data):
        params = {"bk_obj_id": validated_request_data["bk_obj_id"]}
        return client.search_object_attribute(params)


class GetBluekingBiz(Resource):
    """
    查询对象属性
    """

    def perform_request(self, validated_request_data):
        try:
            bk_biz_name = getattr(settings, "BLUEKING_NAME", "蓝鲸") or "蓝鲸"
            result = client.search_business(
                dict(
                    fields=["bk_biz_id", "bk_biz_name"],
                    condition={"bk_biz_name": bk_biz_name},
                )  # noqa
            )
        except BKAPIError as e:
            logger.info("GetBluekingBiz failed: {}", e.message)
            return 2

        if result["info"]:
            for biz_info in result["info"]:
                if biz_info["bk_biz_name"] == bk_biz_name:
                    return biz_info["bk_biz_id"]

        return 2


class SearchServiceCategory(Resource):
    """
    查询服务分类列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))

    def perform_request(self, validated_request_data):
        return client.list_service_category(**validated_request_data)["info"]


class SearchCloudArea(CacheResource):
    """
    查询云区域信息
    """

    cache_type = CacheType.CC_CACHE_ALWAYS

    def perform_request(self, params):
        return batch_request(client.search_cloud_area, params, limit=200)


class GetDynamicQuery(CacheResource):
    r"""
    查询业务下 服务模板\集群模板 列表
    """

    cache_type = CacheType.CC_BACKEND

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1)
        dynamic_type = serializers.ChoiceField(
            choices=[TargetNodeType.SERVICE_TEMPLATE, TargetNodeType.SET_TEMPLATE], label=_lazy("动态类型"), required=True
        )

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        dynamic_type = validated_request_data["dynamic_type"]

        # 获取动态查询的列表
        params = dict(bk_biz_id=bk_biz_id)
        response_data = []
        if dynamic_type == TargetNodeType.SERVICE_TEMPLATE:
            response_data = batch_request(client.list_service_template, params, limit=200)
        elif dynamic_type == TargetNodeType.SET_TEMPLATE:
            response_data = batch_request(client.list_set_template, params, limit=200)

        # 获取业务名称
        response_biz_data = api.cmdb.get_business(bk_biz_ids=[bk_biz_id])
        if response_biz_data:
            biz_data = response_biz_data[0]
            bk_inst_name = biz_data.bk_inst_name
        else:
            bk_inst_name = _("未知")

        # 结果保存变量
        result = {"bk_biz_id": bk_biz_id, "bk_biz_name": bk_inst_name, "children": []}

        # 获取id和名称
        for dynamic_query in response_data:
            result["children"].append(dict(id=dynamic_query["id"], name=dynamic_query["name"]))

        return result


class GetHostByTemplate(Resource):
    """
    获取模板下的主机
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1, required=True)
        bk_obj_id = serializers.ChoiceField(
            required=True, choices=[TargetNodeType.SERVICE_TEMPLATE, TargetNodeType.SET_TEMPLATE], label=_("查询对象")
        )
        template_ids = serializers.ListField(label=_lazy("模板ID"), required=True)
        fields = serializers.ListField(label=_lazy("查询字段"), allow_empty=True, default=Host.Fields)

    def perform_request(self, params):
        bk_biz_id = params["bk_biz_id"]
        bk_obj_id = params["bk_obj_id"]
        template_ids = params["template_ids"]

        # 按模板查询节点
        if bk_obj_id == TargetNodeType.SERVICE_TEMPLATE:
            modules = api.cmdb.get_module(bk_biz_id=bk_biz_id, service_template_ids=template_ids)
            topo_nodes = {"module": [m.bk_module_id for m in modules]}
        elif bk_obj_id == TargetNodeType.SET_TEMPLATE:
            sets = api.cmdb.get_set(bk_biz_id=bk_biz_id, set_template_ids=template_ids)
            topo_nodes = {"set": [s.bk_set_id for s in sets]}
        else:
            topo_nodes = []

        return api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id, topo_nodes=topo_nodes, fields=params["fields"])


class GetServiceInstanceByTemplate(Resource):
    """
    获取模板下的服务实例
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"), min_value=1, required=True)
        bk_obj_id = serializers.ChoiceField(
            required=True, choices=[TargetNodeType.SERVICE_TEMPLATE, TargetNodeType.SET_TEMPLATE], label=_("查询对象")
        )
        template_ids = serializers.ListField(label=_lazy("模板ID"), required=True)

    def perform_request(self, params):
        bk_biz_id = params["bk_biz_id"]
        bk_obj_id = params["bk_obj_id"]
        template_ids = params["template_id"]

        # 按模板查询节点
        if bk_obj_id == TargetNodeType.SERVICE_TEMPLATE:
            modules = api.cmdb.get_module(bk_biz_id=bk_biz_id, service_template_ids=template_ids)
            topo_nodes = {"module": [m.bk_module_id for m in modules]}
        elif bk_obj_id == TargetNodeType.SET_TEMPLATE:
            sets = api.cmdb.get_set(bk_biz_id=bk_biz_id, set_template_ids=template_ids)
            topo_nodes = {"set": [s.bk_set_id for s in sets]}
        else:
            topo_nodes = []

        return api.cmdb.get_service_instance_by_topo_node(bk_biz_id=bk_biz_id, topo_nodes=topo_nodes)


class GetMainlineObjectTopo(Resource):
    """
    获取主线模型的业务拓扑
    """

    def perform_request(self, params):
        return client.get_mainline_object_topo()


def raw_hosts(cc_biz_id):
    """Do not use me，Please use `hosts` func"""

    hosts = get_host_dict_by_biz(cc_biz_id, Host.Fields)
    # 获取云区域信息
    clouds = api.cmdb.search_cloud_area()
    for host in hosts:
        _host_full_cloud(host, clouds)

    full_host_topo_inst(cc_biz_id, hosts)
    return hosts


# 获取主机所有拓扑信息
# to be legacy
def full_host_topo_inst(bk_biz_id, host_list):
    topo_tree_dict = to_dict(api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id))
    if not topo_tree_dict:
        return

    queue = [copy.deepcopy(topo_tree_dict)]
    inst_obj_dict = {}
    topo_link_dict = {}

    while queue:
        node = queue.pop()
        inst_obj_dict["{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])] = node
        if not node.get("topo_link"):
            node["topo_link"] = ["{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])]
            node["topo_link_display"] = [node["bk_inst_name"]]
        topo_link_dict["{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])] = node["topo_link"]
        for child in node["child"]:
            child["topo_link"] = node["topo_link"] + ["{}|{}".format(child["bk_obj_id"], child["bk_inst_id"])]
            child["topo_link_display"] = node["topo_link_display"] + [child["bk_inst_name"]]

        queue = queue + node["child"]
        del node["child"]

    for host in host_list:
        module_list = ["module|%s" % x for x in host["bk_module_ids"]]
        topo_dict = {"module": [], "set": []}
        for module_key in module_list:
            for inst_key in topo_link_dict.get(module_key, []):
                bk_obj_id, _ = inst_key.split("|")
                if bk_obj_id not in topo_dict:
                    topo_dict[bk_obj_id] = []
                if inst_key not in ["{}|{}".format(x["bk_obj_id"], x["bk_inst_id"]) for x in topo_dict[bk_obj_id]]:
                    topo_dict[bk_obj_id].append(inst_obj_dict[inst_key])
        for bk_obj_id in topo_dict:
            host[bk_obj_id] = topo_dict[bk_obj_id]
