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


from django.utils.translation import ugettext as _
from rest_framework import serializers

from core.drf_resource import Resource
from core.drf_resource import resource
from monitor_web.commons.cc.utils import foreach_topo_tree


class GetTopoTree(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务id"))
        instance_type = serializers.ChoiceField(required=False, choices=["host", "service"], label=_("实例类型"))
        remove_empty_nodes = serializers.BooleanField(required=False, default=False, label=_("是否删除空节点"))

    @staticmethod
    def handle_node(node, node_link, other_param):
        if node.get("child", None) is not None:
            node["children"] = node.pop("child")

        node["bk_biz_id"] = other_param["bk_biz_id"]
        other_param["index"] += 1
        node["id"] = str(other_param["index"])
        if node.get("ip"):
            node["name"] = node["ip"]
        elif node.get("bk_inst_name"):
            node["name"] = node["bk_inst_name"]
        elif node.get("service_instance_id"):
            pass
        else:
            node["name"] = _("无法识别节点")

    @staticmethod
    def remove_empty_nodes(node, node_link, ignore_obj):
        # 忽视处理的节点类型。主机数：忽略主机和模块，实例数：忽略实例和主机
        if not node.get("bk_obj_id") or node["bk_obj_id"] in ignore_obj:
            return True

        # 对其他节点，看它的子节点的child为空，如果为空，则从树里面移除
        childs = node.get("child", [])
        new_child = []
        for child in childs:
            if child.get("child"):
                new_child.append(child)

        node["child"] = new_child

    @staticmethod
    def get_node_mapping(topo_tree):
        # 获得节点的路径映射
        node_mapping = {}

        def mapping(node, node_link, node_mapping):
            node.update(node_link=node_link)
            node_mapping[node_link[-1]] = node

        foreach_topo_tree(topo_tree, mapping, node_mapping=node_mapping)
        return node_mapping

    def perform_request(self, validated_request_data):
        topo_tree = resource.commons.cc_topo_tree(validated_request_data)

        # 如果传了remove_empty_nodes参数，则过滤掉空节点
        if validated_request_data.get("remove_empty_nodes"):
            foreach_topo_tree(topo_tree, self.remove_empty_nodes, order="desc", ignore_obj=["module"])

        other_param = {"bk_biz_id": validated_request_data["bk_biz_id"], "index": 0}
        foreach_topo_tree(topo_tree, self.handle_node, order="desc", other_param=other_param)

        return [topo_tree]


class HostAgentStatusResource(Resource):
    """
    主机Agent状态
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(min_value=0, required=True)
        search_condition = serializers.CharField(required=False)

    def perform_request(self, validated_request_data):
        biz_id = validated_request_data["bk_biz_id"]

        host_agent_status_list = []

        if biz_id == "0":
            biz_id = None

        hosts, agent_status, biz_ids = resource.cc.get_host_and_status(biz_id)
        agent_status_dict = {
            -1: _("未知"),
            0: _("Agent正常"),
            2: _("Agent未安装"),
        }

        for host in hosts:
            host.agent_status = agent_status.get(host.host_id, -1)
            host.agent_status_display = agent_status_dict[host.agent_status]
            # 条件过滤
            search_condition = validated_request_data.get("search_condition")
            if search_condition:
                for value in [host.bk_host_innerip, host.bk_os_type_name, host.bk_host_name]:
                    if search_condition.lower() in value.lower():
                        break
                else:
                    continue

            host_agent_status_list.append(host.__dict__)
            host_agent_status_list[-1]["bk_cloud_id"] = host_agent_status_list[-1]["bk_cloud_id"][0]["bk_inst_id"]

        return host_agent_status_list
