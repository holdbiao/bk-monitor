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


import base64
import json
import time

from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy
from django.utils.translation import ungettext as _
from six.moves import range

from core.drf_resource.exceptions import CustomException
from core.drf_resource.base import Resource
from core.drf_resource import resource
from bkmonitor.views import serializers
from core.drf_resource import api


class IPListRequestSerializer(serializers.Serializer):
    ip = serializers.IPAddressField(required=True, label=_lazy("IP地址"))
    plat_id = serializers.IntegerField(required=True, label=_lazy("平台ID"), source="bk_cloud_id")

    def validate_plat_id(self, val):
        return resource.cc.plat_id_cc_to_job(val)


class IPListResponseSerializer(serializers.Serializer):
    ip = serializers.CharField(required=True, label="IP")
    plat_id = serializers.IntegerField(required=True, label=_lazy("平台ID"))
    bk_cloud_id = serializers.IntegerField(required=True, label=_lazy("云区域ID"))

    def validate_plat_id(self, val):
        return resource.cc.plat_id_job_to_cc(val)

    def validate_bk_cloud_id(self, val):
        return resource.cc.plat_id_job_to_cc(val)


class TaskResultMixin(object):
    # 重试次数
    RETRY_TIMES = 600

    # 轮询间隔
    INTERVAL = 0.5

    class RequestSerializer(serializers.Serializer):
        task_id = serializers.CharField(required=True, label=_lazy("启动任务返回的id"))
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))

    class ResponseSerializer(serializers.Serializer):
        class SuccessSerializer(IPListResponseSerializer):
            log_content = serializers.CharField(required=False, allow_null=True, allow_blank=True, label=_lazy("日志信息"))

        class PendingSerializer(IPListResponseSerializer):
            pass

        class FailedSerializer(IPListResponseSerializer):
            errmsg = serializers.CharField(required=True, allow_null=True, allow_blank=True, label=_lazy("错误信息"))
            exit_code = serializers.IntegerField(required=True, label=_lazy("返回码"))

        success = SuccessSerializer(required=True, many=True, label=_lazy("成功IP"))
        pending = PendingSerializer(required=True, many=True, label=_lazy("执行中IP"))
        failed = FailedSerializer(required=True, many=True, label=_lazy("失败IP"))


class GetInstanceLogResource(TaskResultMixin, Resource):
    """
    根据作业实例ID查询作业执行状态
    """

    class IpStatus(object):
        """
        IP状态对应的状态码
        """

        SUCCESS = 9
        WAITING = 5

    def fetch_job_task_result(self, data):
        """
        统计执行结果，分为成功，等待，失败三类
        :param data: job返回的运行结果
        :return: 执行结果
            {
                "success": [
                    {
                        "ip": ip,
                        "plat_id": plat_id,
                        'log_content': xxx
                    }],
                "pending": [{
                        "ip": ip,
                        "plat_id": plat_id
                    }],
                "failed": [{
                        "ip": ip,
                        "plat_id": plat_id
                        "errmsg": xxx
                    }]
            }
        """

        success = []
        pending = []
        failed = []

        try:
            step_results = data[0]["step_results"]
        except Exception as e:
            raise CustomException(_("【模块：job】执行任务结果查询返回格式异常 %s") % str(e))

        for tag in step_results:
            ip_status = tag["ip_status"]
            if ip_status == settings.IP_STATUS_SUCCESS:
                for ip_log in tag["ip_logs"]:
                    ip = ip_log["ip"]
                    plat_id = ip_log["bk_cloud_id"]
                    log_content = ip_log["log_content"]
                    success.append({"ip": ip, "plat_id": plat_id, "bk_cloud_id": plat_id, "log_content": log_content})
            elif ip_status == settings.IP_STATUS_WAITING:
                for ip_log in tag["ip_logs"]:
                    ip = ip_log["ip"]
                    plat_id = ip_log["bk_cloud_id"]
                    pending.append({"ip": ip, "plat_id": plat_id, "bk_cloud_id": plat_id})
            else:
                for ip_log in tag["ip_logs"]:
                    ip = ip_log["ip"]
                    plat_id = ip_log["bk_cloud_id"]
                    log_content = ip_log["log_content"]
                    exit_code = ip_log["exit_code"]
                    failed.append(
                        {
                            "ip": ip,
                            "plat_id": plat_id,
                            "bk_cloud_id": plat_id,
                            "errmsg": log_content,
                            "exit_code": exit_code,
                        }
                    )

        return {"success": success, "pending": pending, "failed": failed}

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        kwargs = {
            "bk_biz_id": bk_biz_id,
            "job_instance_id": validated_request_data["task_id"],
        }

        log_result = {
            "success": [],
            "pending": [],
            "failed": [],
        }
        for i in range(self.RETRY_TIMES):
            data = api.job.get_job_instance_log(kwargs)
            if data and data[0].get("is_finished"):
                log_result = self.fetch_job_task_result(data)
                if not log_result["pending"]:
                    break
            time.sleep(self.INTERVAL)

        for host in log_result["pending"]:
            host.update({"errmsg": _("任务执行超时"), "exit_code": 0})

        log_result["failed"] += log_result["pending"]
        log_result["pending"] = []

        return log_result


class GetGseTaskLogResource(TaskResultMixin, Resource):
    """
    查询GSE进程托管结果
    """

    class IpStatus(object):
        """
        IP状态对应的状态码
        """

        SUCCESS = 9
        WAITING = 5

    def fetch_job_task_result(self, data):
        """
        统计执行结果，分为成功，等待，失败三类
        :param data: job返回的运行结果
        :return: 执行结果
            {
                "success": [
                    {
                        "ip": ip,
                        "plat_id": plat_id,
                        'log_content': xxx
                    }],
                "pending": [{
                        "ip": ip,
                        "plat_id": plat_id
                    }],
                "failed": [{
                        "ip": ip,
                        "plat_id": plat_id
                        "errmsg": xxx
                    }]
            }
        """

        success = []
        pending = []
        failed = []

        for obj, ret in list(data["result"].items()):
            # path:cloudid:ip, path may contain ':' on Windows
            keys = obj.split(":")
            ip = keys[-1]
            plat_id = int(keys[-2])

            try:
                error_code = ret.get("errcode", ret.get("error_code", 1))
                if error_code == settings.GSE_TASK_SUCCESS:
                    success.append(
                        {
                            "ip": ip,
                            "plat_id": plat_id,
                            "bk_cloud_id": plat_id,
                            "log_content": json.dumps(ret["content"]),
                        }
                    )
                elif error_code == settings.GSE_TASK_RUNNING:
                    pending.append({"ip": ip, "bk_cloud_id": plat_id, "plat_id": plat_id})
                else:
                    failed.append(
                        {
                            "ip": ip,
                            "plat_id": plat_id,
                            "bk_cloud_id": plat_id,
                            "errmsg": ret.get("errmsg", "") or ret.get("error_msg", ""),
                            "exit_code": error_code,
                        }
                    )
            except Exception as e:
                failed.append(
                    {"ip": ip, "plat_id": plat_id, "bk_cloud_id": plat_id, "errmsg": "%s" % e, "exit_code": 1}
                )

        return {"success": success, "pending": pending, "failed": failed}

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        kwargs = {
            "bk_biz_id": bk_biz_id,
            "bk_gse_taskid": validated_request_data["task_id"],
        }

        log_result = {
            "success": [],
            "pending": [],
            "failed": [],
        }
        for i in range(self.RETRY_TIMES):
            data = api.job.get_proc_result(kwargs)
            if data and data["status"] != settings.GSE_TASK_RUNNING:
                log_result = self.fetch_job_task_result(data)
                if not log_result["pending"]:
                    break
            time.sleep(self.INTERVAL)

        for host in log_result["pending"]:
            host.update({"errmsg": _("任务执行超时"), "exit_code": 0})

        log_result["failed"] += log_result["pending"]
        log_result["pending"] = []

        return log_result


class FastExecuteScriptResource(Resource):
    """
    快速执行脚本
    """

    many_response_data = True

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        ip_list = IPListRequestSerializer(required=True, many=True)
        script_content = serializers.CharField(required=True, label=_lazy("脚本内容"))
        script_param = serializers.CharField(default="", label=_lazy("脚本参数"))
        account = serializers.CharField(default="root", label=_lazy("执行账户"))
        script_type = serializers.IntegerField(default=1, label=_lazy("脚本类型"))

        def validate_script_content(self, script_content):
            return base64.b64encode(script_content.encode("utf-8")).decode("utf-8")

        def validate_script_param(self, script_params):
            return base64.b64encode(script_params.encode("utf-8")).decode("utf-8")

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]

        task_instance_data = api.job.fast_execute_script(validated_request_data)
        task_id = task_instance_data["job_instance_id"]

        task_result = resource.commons.get_instance_log(
            task_id=task_id,
            bk_biz_id=bk_biz_id,
        )
        return task_result


class FastPushFileResource(Resource):
    """
    快速下发文件

    可一次性下发多个文件，参数格式如下：
    "file_list": [
        {
            "file_name": "a.txt",
            "content": "aGVsbG8gd29ybGQh",
        },
        {
            "file_name": "b.txt",
            "content": "aGVsbG8gd29ybGQh",
        },
    ]
    """

    many_response_data = True

    class RequestSerializer(serializers.Serializer):
        class FileSerializer(serializers.Serializer):
            file_name = serializers.CharField(required=True, label=_lazy("文件名称"))
            content = serializers.CharField(required=True, label=_lazy("文件内容"))

        bk_biz_id = serializers.IntegerField(required=True, label=_lazy("业务ID"))
        ip_list = IPListRequestSerializer(required=True, many=True)
        file_list = FileSerializer(required=True, many=True)
        file_target_path = serializers.CharField(required=True, label=_lazy("目标路径"))
        account = serializers.CharField(default="root", label=_lazy("执行账户"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        task_instance_data = api.job.push_config_file(validated_request_data)
        task_id = task_instance_data["job_instance_id"]
        task_result = resource.commons.get_instance_log(task_id=task_id, bk_biz_id=bk_biz_id)
        return task_result


class GseProcessManageResource(Resource):
    """
    GSE进程托管注册和取消注册
    """

    class RequestSerializer(serializers.Serializer):
        class ProcessInfoSerializer(serializers.Serializer):
            ip_list = IPListRequestSerializer(required=True, many=True)
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
                "进程操作类型 0:启动进程（start）, 1:停止进程（stop）, 2:进程状态查询, "
                "3:注册托管进程, 4:取消托管进程, 7:重启进程（restart）, "
                "8:重新加载进程（reload）, 9:杀死进程（kill）"
            ),
        )
        process_infos = ProcessInfoSerializer(required=True, many=True)

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        task_data = api.job.operate_process(validated_request_data)
        task_id = task_data["bk_gse_taskid"]
        task_result = resource.commons.get_gse_task_log(task_id=task_id, bk_biz_id=bk_biz_id)
        return task_result
