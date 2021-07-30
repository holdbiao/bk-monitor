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
from collections import defaultdict
from datetime import datetime

from api.job.default import (
    FastExecuteScriptResource,
    GetJobInstanceLogResource,
    GetProcResultResource,
    OperateProcessResource,
    PushConfigFileResource,
)
from core.fake_esb_api.register import register


@register
def operate_process(params=None, **kwargs):
    params = params or kwargs
    serializer = OperateProcessResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    task_id = datetime.now().strftime("GSETASK:%Y%m%d%f:00000")

    result = {}
    for process_info in params["process_infos"]:
        for ip_info in process_info["ip_list"]:
            key = "{}:{}:{}".format(ip_info["bk_cloud_id"], ip_info["ip"], process_info["value_key"])

            host_key = "{}:{}".format(ip_info["ip"], ip_info["bk_cloud_id"])
            if host_key in operate_process.result:
                error_code = operate_process[host_key]["error_code"]
                error_msg = operate_process[host_key]["error_msg"]
            else:
                error_code = 0
                error_msg = ""

            result[key] = {
                "content": {
                    "value": [
                        {
                            "instanceID": "",
                            "procName": process_info["proc_name"],
                            "setupPath": process_info["setup_path"],
                            "result": error_msg,
                            "funcID": "",
                        }
                    ]
                },
                "error_code": error_code,
                "errcode": error_code,
                "errmsg": error_msg,
                "error_msg": error_msg,
            }
    get_proc_result.tasks[task_id] = result
    return {"bk_gse_taskid": task_id}


operate_process.result = {}


@register
def get_proc_result(params=None, **kwargs):
    params = params or kwargs
    serializer = GetProcResultResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    bk_gse_taskid = params["bk_gse_taskid"]

    # 任务不存在
    if bk_gse_taskid not in get_proc_result.tasks:
        raise ValueError("gse task({}) not exists".format(bk_gse_taskid))

    return get_proc_result.tasks[bk_gse_taskid]


get_proc_result.tasks = {}


@register
def push_config_file(params=None, **kwargs):
    """
    :return: [
        {
            "status":2,
            "step_results":[
                {
                    "tag":"",
                    "ip_logs":[
                        {
                            "total_time":0,
                            "ip":"10.0.0.1",
                            "log_content":"",
                            "exit_code":0,
                            "bk_cloud_id":0,
                            "retry_count":0,
                            "error_code":0
                        }
                    ],
                    "ip_status":5
                }
            ],
            "is_finished":false,
            "step_instance_id":1003370,
            "name":"API GSE PUSH FILE1579411356494"
        }
    ]
    """
    params = params or kwargs
    serializer = PushConfigFileResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    job_instance_id = len(get_job_instance_log.tasks) + 1
    get_job_instance_log.step_instance_number += 1
    result = [
        {
            "status": push_config_file.result["status"],
            "step_results": [],
            "is_finished": push_config_file.result["is_finished"],
            "step_instance_id": get_job_instance_log.step_instance_number,
            "name": "API GSE PUSH FILE{}".format(datetime.now().strftime("%s")),
        }
    ]

    ip_status_dict = defaultdict(list)
    ip_logs = push_config_file.result["ip_logs"]
    for ip_info in params["ip_list"]:
        host_key = "{}:{}".format(ip_info["ip"], ip_info["bk_cloud_id"])
        if host_key in ip_logs:
            ip_log = json.loads(json.dumps(ip_logs[host_key]))
            del ip_log["ip_status"]
            ip_status_dict[ip_logs[host_key]["ip_status"]].append(ip_log)
        else:
            ip_status_dict[9].append(
                {
                    "total_time": 0,
                    "log_content": "",
                    "exit_code": 0,
                    "bk_cloud_id": 0,
                    "retry_count": 0,
                    "error_code": 0,
                    "status": 5,
                }
            )

    for ip_status in ip_status_dict:
        result[0]["step_results"].append({"ip_status": ip_status, "tag": "", "ip_logs": ip_status_dict[ip_status]})

    get_job_instance_log.tasks[job_instance_id] = result
    return {"job_instance_id": job_instance_id}


push_config_file.result = {"status": 3, "is_finished": True, "ip_logs": {}}


@register
def fast_execute_script(params=None, **kwargs):
    params = params or kwargs
    serializer = FastExecuteScriptResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    job_instance_id = len(get_job_instance_log.tasks) + 1
    get_job_instance_log.step_instance_number += 1
    result = [
        {
            "status": push_config_file.result["status"],
            "step_results": [],
            "is_finished": push_config_file.result["is_finished"],
            "step_instance_id": get_job_instance_log.step_instance_number,
            "name": "API Quick execution script{}".format(datetime.now().strftime("%s")),
        }
    ]

    ip_status_dict = defaultdict(list)
    ip_logs = fast_execute_script.result["ip_logs"]
    for ip_info in params["ip_list"]:
        host_key = "{}:{}".format(ip_info["ip"], ip_info["bk_cloud_id"])
        if host_key in ip_logs:
            ip_log = json.loads(json.dumps(ip_logs[host_key]))
            del ip_log["ip_status"]
            ip_status_dict[ip_logs[host_key]["ip_status"]].append(ip_log)
        else:
            ip_status_dict[9].append(
                {
                    "total_time": 0,
                    "log_content": "",
                    "exit_code": 0,
                    "bk_cloud_id": 0,
                    "retry_count": 0,
                    "error_code": 0,
                    "status": 5,
                }
            )

    for ip_status in ip_status_dict:
        result[0]["step_results"].append({"ip_status": ip_status, "tag": "", "ip_logs": ip_status_dict[ip_status]})

    get_job_instance_log.tasks[job_instance_id] = result
    return {"job_instance_id": job_instance_id}


fast_execute_script.result = {"status": 3, "is_finished": True, "ip_logs": {}}


@register
def get_job_instance_log(params=None, **kwargs):
    params = params or kwargs
    serializer = GetJobInstanceLogResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    job_instance_id = params["job_instance_id"]

    if job_instance_id not in get_job_instance_log.tasks:
        raise ValueError("job instance({}) not exists".format(job_instance_id))

    return get_job_instance_log.tasks[job_instance_id]


get_job_instance_log.tasks = {}
get_job_instance_log.step_instance_number = 0
