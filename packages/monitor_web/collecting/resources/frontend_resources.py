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
from typing import List, Dict

from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

from constants.view import ViewType
from core.drf_resource.base import Resource
from core.errors.collecting import CollectConfigNotExist
from core.drf_resource import resource
from bkmonitor.views import serializers
from constants.data_source import DataSourceLabel, DataTypeLabel
from monitor_web.collecting.constant import CollectStatus, OperationType
from constants.cmdb import TargetNodeType, TargetObjectType
from monitor_web.commons.cc.utils import foreach_topo_tree
from monitor_web.data_explorer.resources import GetSceneViewConfig
from monitor_web.models import CustomEventGroup, CollectorPluginMeta
from monitor_web.models.collecting import CollectConfigMeta, DeploymentConfigVersion
from monitor_web.plugin.constant import PluginType
from monitor_web.plugin.manager import PluginManagerFactory


class FrontendCollectConfigDetailResource(Resource):
    """
    获取采集配置详细信息，供前端展示用
    """

    class RequestSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=True, label=_("采集配置ID"))

    def perform_request(self, validated_request_data):
        id = validated_request_data["id"]
        config_detail = resource.collecting.collect_config_detail({"id": id})

        # 基本信息
        basic_info = {
            "name": config_detail["name"],
            "target_object_type": config_detail["target_object_type"],  # SERVICE, HOST
            "collect_type": config_detail["collect_type"],
            "plugin_display_name": config_detail["plugin_info"]["plugin_display_name"],
            "plugin_id": config_detail["plugin_info"]["plugin_id"],
            "period": config_detail["params"]["collector"]["period"],
            "bk_biz_id": config_detail["bk_biz_id"],
            "label_info": config_detail["label_info"],
            "create_time": config_detail["create_time"],
            "create_user": config_detail["create_user"],
            "update_time": config_detail["update_time"],
            "update_user": config_detail["update_user"],
        }

        # 运行参数
        runtime_params = []
        config_json = config_detail["plugin_info"]["config_json"]
        if config_detail["collect_type"] == PluginType.SNMP:
            for key, item in enumerate(config_json):
                if item.get("auth_json"):
                    config_json.extend(config_json.pop(key).pop("auth_json"))
                    break
        for item in config_json:
            if item["mode"] != "collector":
                item["mode"] = "plugin"
            runtime_params.append(
                {
                    "name": item["description"] or item["name"],
                    "value": config_detail["params"].get(item["mode"]).get(item.get("key", item["name"]))
                    if config_detail["params"].get(item["mode"], {}).get(item.get("key", item["name"]))
                    else item["default"],
                    "type": item["type"],
                }
            )

        # 指标预览
        metric_list = []
        for item in config_detail["plugin_info"]["metric_json"]:
            field_list = []
            for field in item["fields"]:
                field_list.append(
                    {
                        "metric": field["monitor_type"],
                        "englishName": field["name"],
                        "aliaName": field["description"],
                        "type": field["type"],
                        "unit": field["unit"],
                    }
                )
            metric_list.append({"id": item["table_name"], "name": item["table_desc"], "list": field_list})

        # 采集目标
        table_data = []
        if config_detail["target_node_type"] == TargetNodeType.INSTANCE:
            for item in config_detail["target"]:
                table_data.append(
                    {"ip": item["ip"], "agent_status": item["agent_status"], "bk_cloud_name": item["bk_cloud_name"]}
                )
        elif config_detail["target_node_type"] in [TargetNodeType.SET_TEMPLATE, TargetNodeType.SERVICE_TEMPLATE]:
            template_ids = [target["bk_inst_id"] for target in config_detail["target"]]
            nodes = resource.commons.get_nodes_by_template(
                dict(
                    bk_biz_id=config_detail["bk_biz_id"],
                    bk_obj_id=config_detail["target_node_type"],
                    bk_inst_ids=template_ids,
                    bk_inst_type=config_detail["target_object_type"],
                )
            )
            for item in nodes:
                table_data.append(
                    {"bk_inst_name": item["bk_inst_name"], "count": item["count"], "labels": item["labels"]}
                )
        else:
            for item in config_detail["target"]:
                table_data.append(
                    {"bk_inst_name": item["bk_inst_name"], "count": item["count"], "labels": item["labels"]}
                )

        target_info = {"target_node_type": config_detail["target_node_type"], "table_data": table_data}

        result = {
            "basic_info": basic_info,
            "runtime_params": runtime_params,
            "metric_list": metric_list,
            "target_info": target_info,
            "subscription_id": config_detail["subscription_id"],
            "extend_info": config_detail["params"],
        }
        return result


class FrontendTargetStatusTopoResource(Resource):
    """
    获取检查视图页左侧topo树
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        id = serializers.IntegerField(required=True, label=_("采集配置ID"))

    def get_instance_status(self, instance):
        if instance["status"] == CollectStatus.SUCCESS:
            return CollectStatus.SUCCESS
        elif instance["status"] == CollectStatus.NODATA:
            return CollectStatus.NODATA
        else:
            return CollectStatus.FAILED

    def handle_node(self, node, node_link, other_param):
        child = node.pop("child", None)
        if child:
            node["children"] = []
            for item in child:
                # 去除没有不包含实例的节点
                if item.get("children") or item.get("ip"):
                    node["children"].append(item)

        node["bk_biz_id"] = other_param["bk_biz_id"]
        other_param["index"] += 1
        node["id"] = str(other_param["index"])
        if node.get("service_instance_id"):
            node["name"] = node.get("instance_name")
            node["status"] = self.get_instance_status(node)
        elif node.get("ip"):
            node["name"] = node["ip"]
            node["status"] = self.get_instance_status(node)
        elif node.get("bk_inst_name"):
            node["name"] = node["bk_inst_name"]
        else:
            node["name"] = _("无法识别节点")

    def perform_request(self, validated_request_data):
        topo_tree = resource.collecting.collect_target_status_topo(validated_request_data)
        config = CollectConfigMeta.objects.select_related("deployment_config").get(id=validated_request_data["id"])
        if config.deployment_config.target_node_type == TargetNodeType.INSTANCE:
            list([x.update(status=self.get_instance_status(x)) for x in topo_tree])
            return topo_tree

        other_param = {
            "index": 0,
            "bk_biz_id": validated_request_data["bk_biz_id"],
        }
        foreach_topo_tree(topo_tree, self.handle_node, order="desc", other_param=other_param)
        return [topo for topo in topo_tree if topo.get("children")]


class DeploymentConfigDiffResource(Resource):
    """
    用于列表页重新进入执行中的采集配置
    """

    class RequestSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=True, label=_("采集配置id"))

    def perform_request(self, validated_request_data):
        try:
            collect_config = CollectConfigMeta.objects.get(id=validated_request_data["id"])
        except CollectConfigMeta.DoesNotExist:
            raise CollectConfigNotExist({"msg": validated_request_data["id"]})

        # 获得采集配置的上一份部署配置
        if collect_config.last_operation == OperationType.ROLLBACK:
            last_version = DeploymentConfigVersion.objects.filter(parent_id=collect_config.deployment_config.id).last()
        else:
            last_version = collect_config.deployment_config.last_version

        # 返回两份配置的diff_node差异信息
        if last_version:
            diff_node = last_version.show_diff(collect_config.deployment_config)["nodes"]
        else:
            diff_node = {
                "is_modified": True,
                "added": collect_config.deployment_config.target_nodes,
                "updated": [],
                "removed": [],
                "unchanged": [],
            }
        return diff_node


class GetCollectVariablesResource(Resource):
    def perform_request(self, validated_request_data):
        data = [
            ["{{ target.host.bk_host_innerip }}", _("主机内网IP"), "127.0.0.1"],
            ["{{ target.host.bk_cloud_id }}", _("主机云区域ID"), "0"],
            ["{{ target.host.bk_cloud_name }}", _("主机云区域名称"), "default area"],
            ["{{ target.host.bk_host_id }}", _("主机ID"), "1"],
            ["{{ target.host.operator }}", _("主机负责人"), "user1,user2"],
            ["{{ target.host.bk_bak_operator }}", _("主机备份负责人"), "user1,user2"],
            ["{{ target.host.bk_host_name }}", _("主机名"), "VM_centos"],
            ["{{ target.host.bk_isp_name }}", _("ISP名称"), _("联通")],
            ["{{ target.host.bk_os_name }}", _("操作系统名称"), "linux centos"],
            ["{{ target.host.bk_os_version }}", _("操作系统版本"), "7.4.1700"],
            ["{{ target.service.id }}", _("服务实例ID"), "1"],
            ["{{ target.service.name }}", _("服务实例名称"), "test"],
            ["{{ target.service.bk_module_id }}", _("模块ID"), "1"],
            ["{{ target.service.bk_host_id }}", _("主机ID"), "1"],
            ["{{ target.service.service_category_id }}", _("服务分类ID"), "1"],
            ['{{ target.service.labels["label_name"] }}', _("标签"), "test"],
            ['{{ target.process["process_name"].bk_process_id }}', _("进程ID"), "1"],
            ['{{ target.process["process_name"].bk_process_name }}', _("进程别名"), "1"],
            ['{{ target.process["process_name"].bk_func_name }}', _("进程名称"), "1"],
            ['{{ target.process["process_name"].port }}', _("进程端口"), "80,81-85"],
            ['{{ target.process["process_name"].bind_ip }}', _("绑定IP"), "127.0.0.1"],
            ['{{ target.process["process_name"].bk_func_id }}', _("功能ID"), "123"],
            ['{{ target.process["process_name"].user }}', _("启动用户"), "root"],
            ['{{ target.process["process_name"].work_path }}', _("工作路径"), "/data/bkee"],
            ['{{ target.process["process_name"].proc_num }}', _("进程数量"), "4"],
            ['{{ target.process["process_name"].pid_file }}', _("PID文件路径"), "/data/bkee/a.pid"],
            ['{{ target.process["process_name"].auto_start }}', _("自动启动"), "false"],
        ]
        return [{"name": record[0], "description": record[1], "example": record[2]} for record in data]


class GetCollectDashboardConfigResource(GetSceneViewConfig):
    """
    采集视图配置
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        id = serializers.IntegerField(required=True, label=_lazy("采集ID"))
        compare_config = serializers.DictField(label=_lazy("对比配置"), default=lambda: {})
        # 视图类型：overview(总览视图)、topo_node(拓扑节点视图)、leaf_node(叶子节点，即主机或者实例视图)
        view_type = serializers.ChoiceField(
            default=ViewType.LeafNode,
            choices=[ViewType.LeafNode, ViewType.TopoNode, ViewType.Overview],
            label=_lazy("视图类型"),
        )

    DASHBOARD_TITLE = _lazy("监控图表")
    HIDE_NO_GROUP_METRIC = False

    @classmethod
    def get_order_config_key(cls, params):
        return f"panel_order_collect_config_{params['id']}"

    @classmethod
    def get_query_configs(cls, params) -> List[Dict]:
        try:
            collect_config: CollectConfigMeta = CollectConfigMeta.objects.get(
                id=params["id"], bk_biz_id=params["bk_biz_id"]
            )
            plugin = collect_config.plugin
        except CollectConfigMeta.DoesNotExist:
            return []

        metrics = []
        interval = collect_config.deployment_config.params.get("collector", {}).get("period", 60)
        metric_json = collect_config.deployment_config.metrics
        data_source_label = DataSourceLabel.BK_MONITOR_COLLECTOR
        if plugin.plugin_type == CollectorPluginMeta.PluginType.PROCESS:
            # 进程采集上层表现为监控采集，实际未自定义指标
            # data_source_label = DataSourceLabel.CUSTOM
            metric_json = PluginManagerFactory.get_manager(
                plugin=plugin.plugin_id, plugin_type=plugin.plugin_type
            ).gen_metric_info()

        view_type = params.get("view_type", ViewType.LeafNode)
        for table in metric_json:
            dimensions = [field["name"] for field in table["fields"] if field["monitor_type"] != "metric"]

            for field in table["fields"]:
                if field["monitor_type"] != "metric":
                    continue

                metric = {
                    "id": f"{table['table_name']}.{field['name']}",
                    "metric_field": field["name"],
                    "metric_field_name": field["description"] or field["name"],
                    "result_table_id": cls.get_result_table_id(plugin, table["table_name"]),
                    "data_source_label": data_source_label,
                    "data_type_label": DataTypeLabel.LOG
                    if plugin.plugin_type == PluginType.LOG or plugin.plugin_type == PluginType.SNMP_TRAP
                    else DataTypeLabel.TIME_SERIES,
                    "method": "AVG",
                    "interval": interval,
                    "group_by": dimensions[:],
                    "where": [{"key": "bk_collect_config_id", "method": "eq", "value": [f"{params['id']}"]}],
                }

                if view_type == ViewType.Overview:
                    metric["alias"] = " | ".join([f"$tag_{d}" for d in metric["group_by"]])
                elif view_type == ViewType.TopoNode:
                    metric["alias"] = " | ".join(
                        [
                            f"$tag_{d}"
                            for d in metric["group_by"]
                            if d not in ["bk_target_service_instance_id", "bk_target_ip", "bk_target_cloud_id"]
                        ]
                    )
                    metric["method"] = "$method"
                    metric["where"].extend(
                        [
                            {"condition": "and", "key": "bk_obj_id", "method": "eq", "value": ["$bk_obj_id"]},
                            {
                                "condition": "and",
                                "key": "bk_inst_id",
                                "method": "eq",
                                "value": ["$bk_inst_id"],
                            },
                        ]
                    )
                else:
                    if collect_config.target_object_type == TargetObjectType.SERVICE:
                        metric["alias"] = " | ".join(
                            [f"$tag_{d}" for d in metric["group_by"] if d not in ["bk_target_service_instance_id"]]
                        )
                        metric["where"].append(
                            {
                                "condition": "and",
                                "key": "bk_target_service_instance_id",
                                "method": "eq",
                                "value": ["$bk_target_service_instance_id"],
                            }
                        )
                    else:
                        metric["alias"] = " | ".join(
                            [f"$tag_{d}" for d in metric["group_by"] if d not in ["bk_target_ip", "bk_target_cloud_id"]]
                        )
                        metric["where"].extend(
                            [
                                {"condition": "and", "key": "bk_target_ip", "method": "eq", "value": ["$bk_target_ip"]},
                                {
                                    "condition": "and",
                                    "key": "bk_target_cloud_id",
                                    "method": "eq",
                                    "value": ["$bk_target_cloud_id"],
                                },
                            ]
                        )

                metrics.append(metric)

        return metrics

    @classmethod
    def get_result_table_id(cls, plugin: CollectorPluginMeta, table_name: str):
        """
        根据插件生成结果表名
        """
        if plugin.plugin_type == PluginType.LOG or plugin.plugin_type == PluginType.SNMP_TRAP:
            name = "{}_{}".format(plugin.plugin_type, plugin.plugin_id)
            table_id = CustomEventGroup.objects.get(name=name).table_id
            return table_id
        else:
            db_name = ("{}_{}".format(plugin.plugin_type, plugin.plugin_id)).lower()
            if plugin.plugin_type == PluginType.PROCESS:
                db_name = "process"
            return "{}.{}".format(db_name, table_name)

    @classmethod
    def add_target_condition(cls, params, targets: List) -> None:
        collect_config: CollectConfigMeta = CollectConfigMeta.objects.get(
            id=params["id"], bk_biz_id=params["bk_biz_id"]
        )

        if not targets[0]["alias"]:
            targets[0]["alias"] = _("总览")

        if collect_config.target_object_type == TargetObjectType.HOST:
            hosts = params["compare_config"].get("hosts", [])
            if hosts:
                if params.get("view_type", ViewType.LeafNode) == ViewType.Overview:
                    targets.append(json.loads(json.dumps(targets[0])))
                    targets[0]["data"]["where"] = []
                group_by = set(targets[0]["data"]["group_by"])
                group_by.update(("bk_target_ip", "bk_target_cloud_id"))
                targets[0]["data"]["group_by"] = list(group_by)
                targets[0]["alias"] = " | ".join(f"$tag_{dimension}" for dimension in targets[0]["data"]["group_by"])

            where = targets[0]["data"]["where"]
            for host in hosts:
                ip = host["bk_target_ip"]
                bk_cloud_id = host["bk_target_cloud_id"]

                conditions = [
                    {"condition": "or", "key": "bk_collect_config_id", "method": "eq", "value": [f"{params['id']}"]},
                    {"condition": "and", "key": "bk_target_ip", "method": "eq", "value": [ip]},
                    {"condition": "and", "key": "bk_target_cloud_id", "method": "eq", "value": [bk_cloud_id]},
                ]
                where.extend(conditions)
        else:
            service_instances = params["compare_config"].get("service_instances", [])
            if service_instances:
                if params.get("view_type", ViewType.LeafNode) == ViewType.Overview:
                    targets.append(json.loads(json.dumps(targets[0])))
                    targets[0]["data"]["where"] = []
                group_by = set(targets[0]["data"]["group_by"])
                group_by.add("bk_target_service_instance_id")
                targets[0]["data"]["group_by"] = list(group_by)
                targets[0]["alias"] = " | ".join(f"$tag_{dimension}" for dimension in targets[0]["data"]["group_by"])

            where = targets[0]["data"]["where"]
            for service_instance in service_instances:
                service_instance_id = service_instance.get("service_instance_id")
                if not service_instance_id:
                    continue

                conditions = [
                    {"condition": "or", "key": "bk_collect_config_id", "method": "eq", "value": [f"{params['id']}"]},
                    {
                        "condition": "or",
                        "key": "bk_target_service_instance_id",
                        "method": "eq",
                        "value": [service_instance_id],
                    },
                ]
                where.extend(conditions)

        if where and "condition" in where[0]:
            del where[0]["condition"]
