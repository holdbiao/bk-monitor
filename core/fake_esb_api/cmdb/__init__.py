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


import json
import os
from collections import defaultdict

from core.fake_esb_api.register import register


class Data(object):
    _cache_data = {}
    dir_path = os.path.dirname(__file__)

    @staticmethod
    def copy(data):
        return json.loads(json.dumps(data))

    @classmethod
    def get(cls, name):
        if name not in cls._cache_data:
            path = os.path.join(cls.dir_path, "{}.json".format(name))
            with open(path) as f:
                cls._cache_data[name] = json.loads(f.read())

        return json.loads(json.dumps(cls._cache_data[name]))


def node_id(node):
    """
    生成拓扑实例ID
    """
    return "{}|{}".format(node["bk_obj_id"], node["bk_inst_id"])


def get_topo_links(bk_biz_id):
    queue = search_biz_inst_topo(bk_biz_id=bk_biz_id)

    data = defaultdict(list)
    while queue:
        node = queue.pop()
        queue.extend(node["child"])
        for child_node in node["child"]:
            data[node_id(child_node)] = [node_id(node)] + data[node_id(node)]

    return data


def get_topo_dict(bk_biz_id):
    def create_topo_data(topo_node):
        if topo_node["bk_obj_id"] == "module":
            return {
                "bk_biz_id": bk_biz_id,
                "bk_module_id": topo_node["bk_inst_id"],
                "service_category_id": 0,
                "default": 1,
                "bk_childid": None,
                "bk_set_id": topo_node["bk_parent_id"],
                "bk_bak_operator": "",
                "create_time": "2019-05-17T12:38:29.545+08:00",
                "bk_module_name": topo_node["bk_inst_name"],
                "bk_supplier_account": "0",
                "operator": "admin",
                "service_template_id": 0,
                "bk_parent_id": topo_node["bk_parent_id"],
                "last_time": "2019-05-17T12:38:29.545+08:00",
                "bk_module_type": "1",
                "metadata": {"label": {"bk_biz_id": str(bk_biz_id)}},
            }
        elif topo_node["bk_obj_id"] == "set":
            return {
                "bk_biz_id": bk_biz_id,
                "bk_service_status": "1",
                "description": "",
                "bk_set_env": "3",
                "default": 1,
                "bk_childid": None,
                "bk_capacity": None,
                "create_time": "2019-05-17T12:38:29.543+08:00",
                "bk_supplier_account": "0",
                "bk_set_id": topo_node["bk_inst_id"],
                "bk_set_desc": "",
                "bk_parent_id": topo_node["bk_parent_id"],
                "last_time": "2019-05-17T12:38:29.543+08:00",
                "bk_set_name": topo_node["bk_inst_name"],
            }
        elif topo_node["bk_obj_id"] == "biz":
            businesses = Data.get("business")
            for business in businesses:
                if business["bk_biz_id"] == topo_node["bk_inst_id"]:
                    return business
        else:
            return {
                "bk_biz_id": bk_biz_id,
                "bk_obj_id": topo_node["bk_obj_id"],
                "create_time": "2020-01-02T17:15:13.769+08:00",
                "bk_supplier_account": "0",
                "bk_inst_id": topo_node["bk_inst_id"],
                "bk_parent_id": topo_node["bk_parent_id"],
                "last_time": "2020-01-02T17:15:13.769+08:00",
                "bk_inst_name": topo_node["bk_inst_name"],
                "metadata": {"label": {"bk_biz_id": str(bk_biz_id)}},
            }

    queue = search_biz_inst_topo(bk_biz_id=bk_biz_id)

    data = {}
    while queue:
        node = queue.pop()
        if node_id(node) not in data:
            data[node_id(node)] = create_topo_data(node)

        children = node.pop("child")
        queue.extend(children)
        for child in children:
            child["bk_parent_id"] = node["bk_inst_id"]
            data[node_id(child)] = create_topo_data(child)

    return data


@register
def get_biz_internal_module(params=None, **kwargs):
    """
    获取业务空闲机和故障机模块
    """
    internal_topo_list = Data.get("internal_topo")

    params = params or kwargs
    # bk_supplier_account = params["bk_supplier_account"]
    bk_biz_id = str(params["bk_biz_id"])

    if bk_biz_id in internal_topo_list:
        return internal_topo_list[bk_biz_id]

    return {"bk_set_id": 0, "bk_set_name": "", "module": None}


@register
def get_mainline_object_topo(params=None, **kwargs):
    """
    获取主线模型的业务拓扑
    """
    params = params or kwargs
    bk_supplier_account = str(params["bk_supplier_account"])

    mainline_topo = Data.get("mainline_topo")
    for topo in mainline_topo:
        topo["bk_supplier_account"] = bk_supplier_account

    return mainline_topo


@register
def search_business(params=None, **kwargs):
    """
    搜索业务
    支持参数: fields, condition
    """
    businesses = Data.get("business")

    params = params or kwargs

    fields = params.get("fields", [])
    condition = params.get("condition", {})
    # page = params.get("page")

    for key, value in list(condition.items()):
        businesses = [business for business in businesses if business[key] == value]

    if fields:
        businesses = [{field: business[field] for field in fields} for business in businesses]

    return {
        "count": len(businesses),
        "info": businesses,
    }


@register
def search_biz_inst_topo(params=None, **kwargs):
    """
    查询业务实例拓扑
    """
    topo_list = Data.get("topo")

    params = params or kwargs
    bk_biz_id = params["bk_biz_id"]
    # level = params.get("level")

    for topo in topo_list:
        if bk_biz_id == topo["bk_inst_id"]:
            return [topo]

    return []


@register
def search_object_attribute(params=None, **kwargs):
    """
    查询对象模型属性
    """
    attributes = Data.get("attribute")

    params = params or kwargs
    bk_obj_id = params["bk_obj_id"]

    return attributes.get(bk_obj_id, [])


@register
def list_service_category(params=None, **kwargs):
    """
    查询服务分类列表，根据业务ID查询，共用服务分类也会返回
    """
    built_in_category = Data.get("built_in_service_category")
    categories = Data.get("service_category")

    params = params or kwargs
    bk_biz_id = str(params["bk_biz_id"])

    service_categories = built_in_category + categories.get(bk_biz_id, [])
    return {"count": len(service_categories), "info": service_categories}


@register
def list_service_instance(params=None, **kwargs):
    """
    查询服务实例列表
    支持参数: bk_biz_id, bk_module_id, search_key
    """
    service_instances = Data.get("service_instance")

    params = params or kwargs
    bk_biz_id = params["bk_biz_id"]
    bk_module_id = params.get("bk_module_id")
    search_key = params.get("search_key")

    service_instances = [
        service_instance for service_instance in service_instances if service_instance["bk_biz_id"] == bk_biz_id
    ]

    if bk_module_id:
        service_instances = [
            service_instance
            for service_instance in service_instances
            if service_instance["bk_module_id"] == bk_module_id
        ]

    if search_key:
        service_instances = [
            service_instance for service_instance in service_instances if search_key in service_instance["name"]
        ]

    return {"count": len(service_instances), "info": service_instances}


@register
def search_inst_by_object(params=None, **kwargs):
    params = params or kwargs
    bk_biz_id = params["bk_biz_id"]
    bk_obj_id = params["bk_obj_id"]
    condition = params.get("condition", {})
    fields = params.get("fields", [])

    insts = [inst for key, inst in list(get_topo_dict(bk_biz_id).items()) if key.startswith("{}|".format(bk_obj_id))]

    filtered_insts = []
    for inst in insts:
        matched = True
        for key, value in list(condition.items()):
            if inst.get(key) != value:
                matched = False
                break

        if not matched:
            continue

        if fields:
            filtered_insts.append({key: value for key, value in list(inst.items()) if key in fields})
        else:
            filtered_insts.append(inst)

    return {
        "count": len(filtered_insts),
        "info": filtered_insts,
    }


@register
def list_service_instance_detail(params=None, **kwargs):
    """
    查询服务实例列表(带进程信息)
    支持参数: bk_biz_id, bk_set_id, bk_module_id, bk_host_id, service_instance_ids
    """
    service_instance_details = Data.get("service_instance_detail")

    params = params or kwargs
    bk_biz_id = params["bk_biz_id"]
    bk_set_id = params.get("bk_set_id")
    bk_module_id = params.get("bk_module_id")
    bk_host_id = params.get("bk_host_id")
    service_instance_ids = params.get("service_instance_ids", [])

    service_instance_details = [
        service_instance for service_instance in service_instance_details if service_instance["bk_biz_id"] == bk_biz_id
    ]

    if bk_module_id:
        service_instance_details = [
            service_instance
            for service_instance in service_instance_details
            if service_instance["bk_module_id"] == bk_module_id
        ]

    if bk_set_id:
        service_instance_details = [
            service_instance
            for service_instance in service_instance_details
            if service_instance["bk_set_id"] == bk_set_id
        ]

    if bk_host_id:
        service_instance_details = [
            service_instance
            for service_instance in service_instance_details
            if service_instance["bk_host_id"] == bk_host_id
        ]

    if service_instance_ids:
        service_instance_details = [
            service_instance
            for service_instance in service_instance_details
            if service_instance["id"] in service_instance_ids
        ]

    for service_instance in service_instance_details:
        del service_instance["bk_set_id"]

    return service_instance_details
