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


from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext as _

from bkmonitor.data_source import load_data_source
from bkmonitor.iam import Permission, ActionEnum
from core.drf_resource.exceptions import CustomException
from core.errors.uptime_check import UptimeCheckProcessError
from core.drf_resource import resource
from bkmonitor.views import serializers
from common.log import logger
from constants.data_source import DataSourceLabel, DataTypeLabel
from monitor_web.models.uptime_check import UptimeCheckGroup, UptimeCheckNode, UptimeCheckTask


class UptimeCheckNodeSerializer(serializers.ModelSerializer):
    # 地区和运营商可选
    location = serializers.JSONField(required=False)
    carrieroperator = serializers.CharField(required=False, allow_blank=True)

    def node_beat_check(self, validated_data):
        """
        检查当前节点心跳
        """
        filter_dict = {
            "time__gt": "3m",
            "ip": validated_data["ip"],
            "bk_cloud_id": str(validated_data["plat_id"]),
        }

        data_source_class = load_data_source(DataSourceLabel.BK_MONITOR_COLLECTOR, DataTypeLabel.TIME_SERIES)
        data_source = data_source_class(
            table="beat_monitor.heartbeat_total",
            filter_dict=filter_dict,
        )
        data = data_source.query_data(limit=5)
        if len(data):
            return True

        raise UptimeCheckProcessError()

    def update(self, instance, validated_data):
        """
        更新节点
        """
        self.node_beat_check(validated_data)
        if instance.is_common and not validated_data.get("is_common"):
            # 校验公共节点管理权限
            Permission().is_allowed(action=ActionEnum.MANAGE_PUBLIC_SYNTHETIC_LOCATION, raise_exception=True)

            other_biz_task = []
            for task in instance.tasks.all():
                if task.bk_biz_id != instance.bk_biz_id:
                    other_biz_task.append(_("{}(业务id:{})").format(task.name, task.bk_biz_id))
            if other_biz_task:
                raise CustomException(_("不能取消公共节点勾选，若要取消，请先删除以下任务的当前节点：%s") % "，".join(other_biz_task))
        for attr, value in list(validated_data.items()):
            setattr(instance, attr, value)
        instance.save(update=True)
        return instance

    def create(self, validated_data):
        if validated_data.get("is_common"):
            # 校验公共节点管理权限
            Permission().is_allowed(action=ActionEnum.MANAGE_PUBLIC_SYNTHETIC_LOCATION, raise_exception=True)
        self.node_beat_check(validated_data)
        instance = UptimeCheckNode(**validated_data)
        instance.save()
        return instance

    class Meta:
        model = UptimeCheckNode
        exclude = ("carrieroperator",)


class UptimeCheckTaskSerializer(serializers.ModelSerializer):
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
            node_path = serializers.CharField(required=False, allow_blank=True)

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
        request = serializers.CharField(required=False, allow_null=True)

        # ICMP ONLY
        max_rtt = serializers.IntegerField(required=False)
        total_num = serializers.IntegerField(required=False)
        size = serializers.IntegerField(required=False)

        # COMMON
        period = serializers.IntegerField(required=True)
        response_format = serializers.CharField(required=False)
        response = serializers.CharField(required=False, allow_null=True)
        # 这里timeout 对应 采集器配置项: available_duration
        timeout = serializers.IntegerField(
            required=False, min_value=1000, max_value=settings.MAX_AVAILABLE_DURATION_LIMIT
        )

    config = ConfigSlz(required=True)
    location = serializers.JSONField(required=True)
    nodes = UptimeCheckNodeSerializer(many=True, read_only=True)
    groups = serializers.SerializerMethodField(read_only=True)
    available = serializers.SerializerMethodField(read_only=True)
    task_duration = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    node_id_list = serializers.ListField(required=True, write_only=True)
    group_id_list = serializers.ListField(required=False, write_only=True)

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

    @staticmethod
    def get_url(obj):
        """
        拼接拨测地址
        """

        if obj.protocol == UptimeCheckTask.Protocol.HTTP:
            # 针对HTTP协议
            return obj.config["urls"]
        else:
            # 针对其他协议
            if len(obj.config["hosts"]) and obj.config["hosts"][0].get("bk_obj_id"):
                # 如果是动态拓扑，拿到所有的IP
                target_host = resource.uptime_check.topo_template_host(obj.config["hosts"])
            else:
                target_host = obj.config["hosts"]

            # 拼接拨测地址
            if obj.protocol == UptimeCheckTask.Protocol.ICMP:
                target_list = []
                for host in target_host:
                    target_list.append("{}".format(host["ip"] if host["ip"] else host["outer_ip"]))
                return ",".join(target_list)
            else:
                target_list = []
                for host in target_host:
                    target_list.append(
                        "{}:{}".format(host["ip"] if host["ip"] else host["outer_ip"], obj.config["port"])
                    )
                return ",".join(target_list)

    def get_groups(self, obj):
        """获取任务分组信息"""
        return [{"id": group.id, "name": group.name} for group in obj.groups.all()]

    def get_available(self, obj):
        """计算任务可用率，如异常则按0计算，不可影响任务列表的获取"""
        # 只有拨测任务列表列需要展示每个拨测任务的可用率情况
        # 需要展示每个任务可用率时，则调用 list() 方法时指定 get_available=True
        if (
            self.context.get("request").query_params.get("get_available", False)
            and obj.status != UptimeCheckTask.Status.STOPED
        ):
            try:
                task_data = resource.uptime_check.get_recent_task_data({"task_id": obj.id, "type": "available"})
                return task_data["available"] * 100
            except Exception as e:
                logger.exception("get available failed: %s" % str(e))
                return 0
        else:
            return None

    def get_task_duration(self, obj):
        """
        计算任务响应时长
        """
        if (
            self.context.get("request").query_params.get("get_task_duration", False)
            and obj.status != UptimeCheckTask.Status.STOPED
        ):
            try:
                task_data = resource.uptime_check.get_recent_task_data({"task_id": obj.id, "type": "task_duration"})
                return task_data["task_duration"]
            except Exception as e:
                logger.exception("get task duration failed:%s" % str(e))
                return None
        else:
            return None

    def create(self, validated_data):
        # 处理节点信息
        nodes = validated_data.pop("node_id_list", [])
        groups = validated_data.pop("group_id_list", [])

        with transaction.atomic():
            if UptimeCheckTask.objects.filter(
                name=validated_data["name"], bk_biz_id=validated_data["bk_biz_id"]
            ).first():
                raise CustomException(_("已存在相同名称的拨测任务"))
            task = UptimeCheckTask.objects.create(**validated_data)
            for node in nodes:
                if node:
                    task.nodes.add(node)
            for group in groups:
                group = UptimeCheckGroup.objects.get(id=group)
                group.tasks.add(task.id)
                group.save()

            task.save()

        return task

    def update(self, instance, validated_data):
        nodes = validated_data.pop("node_id_list", [])
        groups = validated_data.pop("group_id_list", [])

        for attr, value in list(validated_data.items()):
            setattr(instance, attr, value)
        with transaction.atomic():
            instance.nodes.clear()
            for node in nodes:
                instance.nodes.add(node)

            instance.groups.clear()
            for group in groups:
                group = UptimeCheckGroup.objects.get(id=group)
                # 编辑任务时，若分组下已关联此任务，则不需要重复添加任务id
                task_id_list = [task.id for task in group.tasks.all()]
                if instance.id not in task_id_list:
                    group.tasks.add(instance.id)
                    group.save()

            task_ids = [
                task.id
                for task in UptimeCheckTask.objects.filter(
                    name=validated_data["name"], bk_biz_id=validated_data["bk_biz_id"]
                )
            ]

            if task_ids and instance.id not in task_ids:
                raise CustomException(_("已存在相同名称的拨测任务"))

            instance.save()

            # monitors = instance.monitors
            # for monitor in monitors:
            #     target_name = re.split(r'[_"]', monitor.title)
            #     monitor.title = instance.name
            #     if len(target_name) >= 2:
            #         monitor.title += '_' + target_name[-1]
            #     monitor.save()

            # TODO: 接入新的策略
            # # 重新保存策略以同
            # alarm_strategies = resource.config.list_alarm_strategy({
            #     "task_id": instance.id,
            #     "bk_biz_id": instance.bk_biz_id
            # })
            # for alarm_strategy in alarm_strategies:
            #     alarm_strategy["task_id"] = instance.id
            #     resource.config.save_alarm_strategy(alarm_strategy)

        return instance

    class Meta:
        model = UptimeCheckTask
        fields = "__all__"


class UptimeCheckGroupSerializer(serializers.ModelSerializer):
    tasks = UptimeCheckTaskSerializer(many=True, read_only=True)
    task_id_list = serializers.ListField(required=True, write_only=True)

    def create(self, validated_data):
        tasks = validated_data.pop("task_id_list")
        if UptimeCheckGroup.objects.filter(name=validated_data["name"], bk_biz_id=validated_data["bk_biz_id"]).exists():
            raise serializers.ValidationError(_("分组 %s 已存在！") % validated_data["name"])

        with transaction.atomic():
            group = UptimeCheckGroup.objects.create(**validated_data)
            for task in tasks:
                group.tasks.add(task)
            group.save()

        return group

    def update(self, instance, validated_data):
        tasks = validated_data.pop("task_id_list")
        if (
            UptimeCheckGroup.objects.filter(name=validated_data["name"], bk_biz_id=validated_data["bk_biz_id"])
            .exclude(id=instance.id)
            .exists()
        ):
            raise serializers.ValidationError(_("分组 %s 已存在！") % validated_data["name"])

        for attr, value in list(validated_data.items()):
            setattr(instance, attr, value)
        with transaction.atomic():
            instance.tasks.clear()
            for task in tasks:
                instance.tasks.add(task)
            instance.save()

        return instance

    class Meta:
        model = UptimeCheckGroup
        fields = "__all__"
