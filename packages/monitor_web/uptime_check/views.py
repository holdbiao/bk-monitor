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
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from core.drf_resource import resource
from bkmonitor.utils.common_utils import safe_int
from monitor.filtersets import get_filterset
from monitor.viewsets import CountModelMixin
from monitor_web.models.uptime_check import (
    UptimeCheckGroup,
    UptimeCheckNode,
    UptimeCheckTask,
    UptimeCheckTaskCollectorLog,
)
from monitor_web.uptime_check.serializers import (
    UptimeCheckGroupSerializer,
    UptimeCheckNodeSerializer,
    UptimeCheckTaskSerializer,
)
from utils.business import get_business_id_list


class PermissionMixin(IAMPermissionMixin):
    iam_read_actions = ActionEnum.VIEW_SYNTHETIC
    iam_write_actions = ActionEnum.MANAGE_SYNTHETIC


class FrontPageDataViewSet(IAMPermissionMixin, ResourceViewSet):
    """
    监控首页 服务拨测曲线数据获取
    """

    iam_read_actions = ActionEnum.VIEW_HOME
    iam_write_actions = ActionEnum.VIEW_HOME

    resource_routes = [ResourceRoute("POST", resource.uptime_check.front_page_data)]


class GetHttpHeadersViewSet(PermissionMixin, ResourceViewSet):
    """
    获取HTTP任务允许设置的Header
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.get_http_headers)]


class GetStrategyStatusViewSet(PermissionMixin, ResourceViewSet):
    """
    获取启用/停用策略数
    """

    resource_routes = [ResourceRoute("POST", resource.uptime_check.get_strategy_status)]


class TaskDetailViewSet(PermissionMixin, ResourceViewSet):
    """
    根据任务id 获取可用率曲线或响应时长曲线
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.task_detail)]


class TaskGraphAndMapViewSet(PermissionMixin, ResourceViewSet):
    """
    根据任务id 获取可用率曲线和响应时长曲线与地区信息
    """

    iam_write_actions = ActionEnum.VIEW_SYNTHETIC

    resource_routes = [ResourceRoute("POST", resource.uptime_check.task_graph_and_map)]


class UptimeCheckNodeViewSet(PermissionMixin, viewsets.ModelViewSet, CountModelMixin):
    queryset = UptimeCheckNode.objects.all()
    filter_class = get_filterset(UptimeCheckNode)
    serializer_class = UptimeCheckNodeSerializer

    def list(self, request, *args, **kwargs):
        """
        重写list,简化节点部分数据并添加关联任务数等数据
        """
        # 如用户传入业务，同时还应该加上通用节点
        id_list = get_business_id_list()
        # 使用business_id_list过滤掉业务已经不存在的公共节点
        common_nodes = UptimeCheckNode.objects.filter(is_common=True, bk_biz_id__in=id_list)
        queryset = self.filter_queryset(self.get_queryset()) | common_nodes
        serializer = self.get_serializer(queryset, many=True)

        # 获取采集器相关信息
        bk_biz_id = request.GET.get("bk_biz_id")
        all_node_status = (
            resource.uptime_check.uptime_check_beat(bk_biz_id=bk_biz_id)
            if bk_biz_id
            else resource.uptime_check.uptime_check_beat()
        )

        result = []
        for node in serializer.data:
            task_num = UptimeCheckNode.objects.get(id=node["id"]).tasks.all().count()
            node_status = list(
                filter(lambda x: x.get("ip") == node["ip"] and x.get("bk_cloud_id") == node["plat_id"], all_node_status)
            )[0]
            result.append(
                {
                    "id": node["id"],
                    "bk_biz_id": node["bk_biz_id"],
                    "name": node["name"],
                    "ip": node["ip"],
                    "plat_id": node["plat_id"],
                    "country": node["location"].get("country"),
                    "province": node["location"].get("city"),
                    "carrieroperator": node["carrieroperator"],
                    "task_num": task_num,
                    "is_common": node["is_common"],
                    "gse_status": node_status["gse_status"],
                    "status": node_status["status"],
                    "version": node_status["version"],
                }
            )
        return Response(result)

    @list_route(methods=["GET"])
    def is_exist(self, request, *args, **kwargs):
        """
        用于给前端判断输入的IP是否属于已建节点
        """
        ip = request.GET.get("ip")
        bk_biz_id = request.GET.get("bk_biz_id")
        return Response(
            {"is_exist": True if UptimeCheckNode.objects.filter(ip=ip, bk_biz_id=bk_biz_id).exists() else False}
        )

    @list_route(methods=["GET"])
    def fix_name_conflict(self, request, *args, **kwargs):
        """
        节点重名时自动补全一个名称，如广东移动补全为广东移动2
        """
        # filter() 时, 在mysql里，‘name=’ 会忽略结尾空格，而'name__startswith'不会。故在进行校验时，将结尾空格去掉。
        name = request.GET.get("name", "").rstrip()
        bk_biz_id = request.GET.get("bk_biz_id")
        id = request.GET.get("id")

        is_exists = (
            UptimeCheckNode.objects.filter(name=name, bk_biz_id=bk_biz_id).exclude(id=id).exists()
            if id
            else UptimeCheckNode.objects.filter(name=name, bk_biz_id=bk_biz_id).exists()
        )

        if is_exists:
            all_names = UptimeCheckNode.objects.filter(name__startswith=name, bk_biz_id=bk_biz_id).values("name")
            num_suffix_list = []
            for item in all_names:
                num_suffix_list.append(safe_int(item["name"].strip(name)))
            max_num = max(num_suffix_list)
            if max_num:
                name += str(max_num + 1)
            else:
                name += "2"
        return Response({"name": name})


class UptimeCheckTaskViewSet(PermissionMixin, viewsets.ModelViewSet, CountModelMixin):
    filter_class = get_filterset(UptimeCheckTask)
    serializer_class = UptimeCheckTaskSerializer

    def get_iam_actions(self):
        if self.action == "list":
            return [ActionEnum.VIEW_HOME, ActionEnum.VIEW_SYNTHETIC]
        return super(UptimeCheckTaskViewSet, self).get_iam_actions()

    def get_queryset(self):
        """
        可用于按任务组筛选拨测任务
        """
        queryset = UptimeCheckTask.objects.all().prefetch_related("nodes", "groups")
        group_id = self.request.query_params.get("group_id")
        if group_id:
            uptime_check_group = UptimeCheckGroup.objects.get(id=group_id)
            queryset = uptime_check_group.tasks.all()
        return queryset

    def list(self, request, *args, **kwargs):
        """
        重写list，传入get_groups时整合拨测任务组卡片页数据，避免数据库重复查询
        """
        queryset = list(self.filter_queryset(self.get_queryset()))
        bk_biz_id = int(request.query_params.get("bk_biz_id", 0))
        get_groups = request.query_params.get("get_groups", False)
        get_available = request.query_params.get("get_available") == "true"
        get_task_duration = request.query_params.get("get_task_duration") == "true"
        task_data = resource.uptime_check.uptime_check_task_list(
            task_data=queryset, bk_biz_id=bk_biz_id, get_available=get_available, get_task_duration=get_task_duration
        )

        # 如果节点对应的业务id已经不存在了，则该任务状态强制显示为START_FAILED，用于给用户提示
        biz_id_list = get_business_id_list()
        for data in task_data:
            for node in data["nodes"]:
                if node["bk_biz_id"] not in biz_id_list:
                    data["status"] = UptimeCheckTask.Status.START_FAILED

        if get_groups:
            result = resource.uptime_check.uptime_check_card(bk_biz_id=bk_biz_id, task_data=task_data)
        else:
            result = task_data
        return Response(result)

    @list_route(methods=["POST"])
    def test(self, request, *args, **kwargs):
        """
        测试任务
        下发测试配置，采集器只执行一次数据采集，直接返回采集结果，不经过计算平台
        """
        config = request.data.get("config")
        protocol = request.data.get("protocol")
        node_id_list = request.data.get("node_id_list")
        return Response(
            resource.uptime_check.test_task({"config": config, "protocol": protocol, "node_id_list": node_id_list})
        )

    @detail_route(methods=["POST"])
    def deploy(self, request, *args, **kwargs):
        """
        正式创建任务
        下发正式配置，采集器托管任务，将采集结果上报至计算平台
        """
        task = self.get_object()
        return Response(task.deploy())

    @detail_route(methods=["POST"])
    def clone(self, request, *args, **kwargs):
        """
        克隆任务
        """
        task = self.get_object()
        nodes = task.nodes.all()
        task.pk = None

        # 判断重名
        new_name = name = task.name + "_copy"
        i = 1
        while task.__class__.objects.filter(name=new_name):
            new_name = f"{name}({i})"
            i += 1
        task.name = new_name

        # 克隆出的拨测任务为 ”未保存“ 状态，使用者可进行编辑后提交
        task.create_user = request.user.username
        task.update_user = request.user.username
        task.status = task.__class__.Status.NEW_DRAFT
        task.subscription_id = 0
        task.save()
        return Response(task.nodes.add(*nodes))

    @detail_route(methods=["POST"])
    def change_status(self, request, *args, **kwargs):
        """
        更改任务状态
        """
        task = self.get_object()
        status = request.data.get("status", "")
        task.change_status(status)
        return Response(data={"id": task.pk, "status": task.status})

    @detail_route(methods=["GET"])
    def running_status(self, request, *args, **kwargs):
        """
        创建拨测任务时，查询部署任务是否成功，失败则返回节点管理中部署失败错误日志
        :return:
        """
        task = self.get_object()
        if task.status == task.Status.START_FAILED:
            error_log = [
                item["error_log"]
                for item in UptimeCheckTaskCollectorLog.objects.filter(task_id=task.id, is_deleted=False).values()
            ]
            return Response(data={"status": task.Status.START_FAILED, "error_log": error_log})
        else:
            return Response(data={"status": task.status})


class UptimeCheckGroupViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = UptimeCheckGroup.objects.all()
    filter_class = get_filterset(UptimeCheckGroup)
    serializer_class = UptimeCheckGroupSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        简化返回数据
        """
        data = super(UptimeCheckGroupViewSet, self).retrieve(request, *args, **kwargs).data
        result = {
            "id": data["id"],
            "name": data["name"],
            "bk_biz_id": data["bk_biz_id"],
            "logo": data["logo"],
            "task_list": [{"id": item["id"], "name": item["name"]} for item in data["tasks"]],
        }
        return Response(result)

    @detail_route(methods=["POST"])
    def add_task(self, request, *args, **kwargs):
        """
        拨测任务拖拽进入任务组
        """
        task_id = request.data.get("task_id")
        task = UptimeCheckTask.objects.get(pk=task_id)
        group = self.get_object()
        if task in group.tasks.all():
            return Response({"msg": _("拨测分组({})已存在任务({})".format(group.name, task.name))})
        group.tasks.add(task_id)
        return Response({"msg": _("拨测分组({})添加任务({})成功".format(group.name, task.name))})


class ExportUptimeCheckConfViewSet(PermissionMixin, ResourceViewSet):
    """
    导出拨测任务配置接口
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.export_uptime_check_conf)]


class ExportUptimeCheckNodeConfViewSet(PermissionMixin, ResourceViewSet):
    """
    导出拨测节点配置接口
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.export_uptime_check_node_conf)]


class ImportUptimeCheckViewSet(PermissionMixin, ResourceViewSet):
    resource_routes = [
        ResourceRoute("GET", resource.uptime_check.file_parse, endpoint="parse"),
        ResourceRoute("POST", resource.uptime_check.file_import_uptime_check),
    ]


class SelectUptimeCheckNodeViewSet(PermissionMixin, ResourceViewSet):
    """
    节点选择器
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.select_uptime_check_node)]


class SelectCarrierOperatorViewSet(PermissionMixin, ResourceViewSet):
    """
    节点选择器
    """

    resource_routes = [ResourceRoute("GET", resource.uptime_check.select_carrier_operator)]


class UptimeCheckTargetDetailViewSet(PermissionMixin, ResourceViewSet):
    """
    获取目标详情
    """

    resource_routes = [ResourceRoute("POST", resource.uptime_check.uptime_check_target_detail)]
