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


import abc

import six
from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy
from rest_framework import serializers

from bkmonitor.utils.request import get_request
from core.drf_resource.contrib.api import APIResource


class IPSerializer(serializers.Serializer):
    """
    IP参数
    """

    ip = serializers.IPAddressField(required=True, label=_lazy("IP地址"))
    bk_cloud_id = serializers.IntegerField(required=True, label=_lazy("云区域ID"))


class JobBaseResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url = "%s/api/c/compapi/v2/job/" % settings.BK_PAAS_INNER_HOST
    module_name = "job"

    def perform_request(self, params):
        try:
            params["_origin_user"] = get_request().user.username
        except Exception:
            pass
        self.bk_username = settings.COMMON_USERNAME
        return super(JobBaseResource, self).perform_request(params)


class GetJobListResource(JobBaseResource):
    """
    作业列表
    """

    action = "get_job_list"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))


class GetJobDetailResource(JobBaseResource):
    """
    作业详情
    """

    action = "get_job_detail"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        bk_job_id = serializers.IntegerField(label=_lazy("作业模板ID"))


class FastExecuteScriptResource(JobBaseResource):
    """
    快速执行脚本
    """

    action = "fast_execute_script"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        script_content = serializers.CharField(label=_lazy("脚本内容"))
        script_param = serializers.CharField(label=_lazy("脚本参数"), default="", allow_blank=True)
        ip_list = IPSerializer(label=_lazy("IP列表"), many=True)
        script_type = serializers.IntegerField(label=_lazy("脚本类型"), default=1)
        account = serializers.CharField(label=_lazy("执行账户"))


class GetJobInstanceLogResource(JobBaseResource):
    """
    获取IP的任务状态
    """

    action = "get_job_instance_log"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        job_instance_id = serializers.IntegerField(label=_lazy("任务ID"))


class PushConfigFileResource(JobBaseResource):
    """
    分发配置文件
    """

    action = "push_config_file"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class FileSerializer(serializers.Serializer):
            file_name = serializers.CharField(required=True, label=_lazy("文件名称"))
            content = serializers.CharField(required=True, label=_lazy("文件内容"))

        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        ip_list = IPSerializer(required=True, many=True)
        file_list = FileSerializer(required=True, many=True)
        file_target_path = serializers.CharField(required=True, label=_lazy("目标路径"))
        account = serializers.CharField(default="root", label=_lazy("执行账户"))

    class ResponseSerializer(serializers.Serializer):
        job_instance_id = serializers.IntegerField(label=_lazy("任务ID"))


class GetProcResultResource(JobBaseResource):
    """
    查询GSE进程托管结果
    """

    action = "get_proc_result"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        bk_gse_taskid = serializers.CharField(required=True)


class OperateProcessResource(JobBaseResource):
    """
    GSE进程操作
    """

    action = "operate_process"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ProcessInfoSerializer(serializers.Serializer):
            ip_list = IPSerializer(required=True, many=True)
            account = serializers.CharField(required=True, label=_lazy("进程启动的用户名"))
            proc_name = serializers.CharField(required=True, label=_lazy("进程名"))
            setup_path = serializers.CharField(required=True, label=_lazy("进程路径"))
            cfg_path = serializers.CharField(required=False, label=_lazy("进程配置文件路径"))
            log_path = serializers.CharField(required=False, label=_lazy("进程日志路径"))
            pid_path = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程日志所在路径"))
            contact = serializers.CharField(default="monitor", label=_lazy("联系人"))
            start_cmd = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程启动命令"))
            stop_cmd = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程停止命令"))
            restart_cmd = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程重启命令"))
            reload_cmd = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程reload命令"))
            kill_cmd = serializers.CharField(required=False, allow_blank=True, label=_lazy("进程kill命令"))
            value_key = serializers.CharField(required=False, label=_lazy("Agent管理进程索引key"))
            type = serializers.ChoiceField(
                required=False, choices=[0, 1, 2], label=_lazy("进程托管类型。0为周期执行进程，1为常驻进程，2为单次执行进程")
            )
            cpu_lmt = serializers.IntegerField(required=False, label=_lazy("进程使用cpu限制，取值范围[0, 100]"))
            mem_lmt = serializers.IntegerField(required=False, label=_lazy("进程使用mem限制，取值范围[0, 100]"))
            cycle_time = serializers.IntegerField(required=False, label=_lazy("定期调度时间"))
            instance_num = serializers.IntegerField(required=False, label=_lazy("进程实例个数"))
            op_timeout = serializers.IntegerField(required=False, label=_lazy("超时执行时间"))
            start_check_begin_time = serializers.IntegerField(required=False, label=_lazy("进程启动后开始检查时间"))
            start_check_end_time = serializers.IntegerField(required=False, label=_lazy("进程启动后结束检查时间"))

        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        op_type = serializers.ChoiceField(
            required=True,
            choices=[0, 1, 2, 3, 4, 7, 8, 9],
            label=_lazy(
                "进程操作类型 0:启动进程（start）, 1:停止进程（stop）, "
                "2:进程状态查询, 3:注册托管进程, 4:取消托管进程, 7:重启进程（restart）, "
                "8:重新加载进程（reload）, 9:杀死进程（kill）"
            ),
        )
        process_infos = ProcessInfoSerializer(required=True, many=True)

    class ResponseSerializer(serializers.Serializer):
        bk_gse_taskid = serializers.CharField(required=True)
