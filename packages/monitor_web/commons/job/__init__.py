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
import logging
import ntpath
import posixpath
from collections import namedtuple

import six
from django.conf import settings
from django.utils.translation import ugettext as _

from core.drf_resource import resource
from bkmonitor.utils.common_utils import host_key

logger = logging.getLogger(__name__)


# 系统信息
SystemInfo = namedtuple("SystemInfo", ["bk_os_type", "script_ext", "job_execute_account", "script_type"])

windows_system_info = SystemInfo(
    bk_os_type="windows",
    script_ext=settings.WINDOWS_SCRIPT_EXT,
    job_execute_account=settings.WINDOWS_JOB_EXECUTE_ACCOUNT,
    script_type=settings.SCRIPT_TYPE_BAT,
)

linux_system_info = SystemInfo(
    bk_os_type="linux",
    script_ext=settings.LINUX_SCRIPT_EXT,
    job_execute_account=settings.LINUX_JOB_EXECUTE_ACCOUNT,
    script_type=settings.SCRIPT_TYPE_SHELL,
)

aix_system_info = SystemInfo(
    bk_os_type="aix",
    script_ext=settings.AIX_SCRIPT_EXT,
    job_execute_account=settings.AIX_JOB_EXECUTE_ACCOUNT,
    script_type=settings.SCRIPT_TYPE_SHELL,
)


class JobTaskClient(object):
    """
    JOB任务执行客户端
    """

    def __init__(self, bk_biz_id, operator=None):
        self.bk_biz_id = bk_biz_id
        self.operator = operator or settings.COMMON_USERNAME

    @staticmethod
    def _get_system_info_dict():
        """
        JOB执行需要用到的关于系统的信息
        """
        return {
            "linux": linux_system_info,
            "windows": windows_system_info,
            "aix": aix_system_info,
        }

    def execute_task_by_system(self, hosts, task_func):
        """
        根据系统类型执行用户给定的JOB任务并返回结果
        :param hosts: IP列表
        :param task_func: 任务定义
        :return:
        """
        task_results = []

        hosts_info, error_hosts = self.separate_hosts_by_system(hosts)
        # 按系统类型分别执行任务
        for system_info, ip_list in hosts_info:
            task_result = task_func(system_info, ip_list)
            task_results.append(task_result)

        # 任务结果合并
        merged_result = {
            "success": [],
            "pending": [],
            "failed": error_hosts,
        }

        for task_result in task_results:
            for status, ip_list in six.iteritems(merged_result):
                ip_list += task_result[status]

        return merged_result

    def separate_hosts_by_system(self, hosts):
        """
        将主机按系统类型进行分组，以便进行差异化的处理
        :rtype: dict[str, dict]
        """
        supported_systems = list(self._get_system_info_dict().keys())

        hosts_by_system = {
            key: {"hosts": [], "system": value} for key, value in list(self._get_system_info_dict().items())
        }
        error_hosts = []

        # 实时获取当前主机的操作系统
        all_hosts = resource.cc.hosts(self.bk_biz_id)

        # 给业务下的所有主机建立索引，便于查找
        ip_os_dict = {}
        for host in all_hosts:
            ip_os_dict[host.host_id] = host.bk_os_type_name

        for host in hosts:
            ip = host["ip"]
            bk_cloud_id = host.get("bk_cloud_id") or host.get("plat_id", 0)
            host_id = host_key(ip=ip, plat_id=resource.cc.plat_id_job_to_cc(bk_cloud_id))
            if host_id not in ip_os_dict:
                error_hosts.append(
                    {
                        "ip": ip,
                        "bk_cloud_id": bk_cloud_id,
                        "errmsg": _("{bk_cloud_id}:{ip} 主机不属于该业务").format(bk_cloud_id=bk_cloud_id, ip=ip),
                    }
                )
                continue
                # raise CustomException(_(u"%(bk_cloud_id)s:%(ip)s 主机不属于该业务") % {'bk_cloud_id': bk_cloud_id, 'ip': ip})
            bk_os_type = ip_os_dict[host_id]
            if bk_os_type in supported_systems:
                hosts_by_system[bk_os_type]["hosts"].append({"ip": ip, "plat_id": bk_cloud_id})
            elif not bk_os_type:
                error_hosts.append(
                    {
                        "ip": ip,
                        "bk_cloud_id": bk_cloud_id,
                        "errmsg": _("{bk_cloud_id}:{ip} 操作系统类型不能为空").format(bk_cloud_id=bk_cloud_id, ip=ip),
                    }
                )
                # raise CustomException(
                #     _(u"%(bk_cloud_id)s:%(ip)s 操作系统类型不能为空") % {'bk_cloud_id': bk_cloud_id, 'ip': ip})
            else:
                error_hosts.append(
                    {
                        "ip": ip,
                        "bk_cloud_id": bk_cloud_id,
                        "errmsg": _("{bk_cloud_id}:{ip} 不支持的操作系统类型：{bk_os_type}").format(
                            bk_cloud_id=bk_cloud_id, ip=ip, bk_os_type=bk_os_type
                        ),
                    }
                )
                # raise CustomException(
                #     _(u"%(bk_cloud_id)s:%(ip)s 不支持的操作系统类型： %(bk_os_type)s") % {
                #         'bk_cloud_id': bk_cloud_id,
                #         'ip': ip,
                #         'bk_os_type': bk_os_type})

        # 删除主机列表为空的系统信息
        for k in list(hosts_by_system.keys()):
            if not hosts_by_system[k]["hosts"]:
                del hosts_by_system[k]

        return [(info["system"], info["hosts"]) for info in list(hosts_by_system.values())], error_hosts

    @staticmethod
    def render_context(system_info, system_special, attr_name, default):
        """
        :param attr_name: 属性名称
        :param system_info: 系统信息
        :param system_special: 上下文字典信息，格式 {"linux": {"attr": "1"}, "windows": {"attr": "2"}
        :param default: 默认值
        :return:
        """
        if not system_special:
            return default
        if system_info.bk_os_type in system_special:
            return system_special[system_info.bk_os_type].get(attr_name, default)
        return default

    def fast_execute_script(self, hosts, script_content, system_special=None):
        """
        快速执行脚本
        :param hosts: IP列表
        :param script_content: 脚本内容
        :param system_special: 系统上下文
        :return:
        """
        result = self.execute_task_by_system(
            hosts=hosts,
            task_func=lambda system_info, ip_list: resource.commons.fast_execute_script(
                ip_list=ip_list,
                bk_biz_id=self.bk_biz_id,
                account=system_info.job_execute_account,
                script_content=self.render_context(system_info, system_special, "script_content", script_content),
                script_type=system_info.script_type,
            ),
        )
        return result

    def test_fast_execute_script(self, hosts, script_content, system_special=None):
        """
        快速执行脚本，仅用于测试之用，不要用于其他场景
        :param hosts: IP列表
        :param script_content: 脚本内容
        :param system_special: 系统上下文
        :return:
        """
        result = self.execute_task_by_system(
            hosts=hosts,
            task_func=lambda system_info, ip_list: resource.commons.test_fast_execute_script(
                operator=self.operator,
                ip_list=ip_list,
                bk_biz_id=self.bk_biz_id,
                account=system_info.job_execute_account,
                script_content=self.render_context(system_info, system_special, "script_content", script_content),
                type=system_info.script_type,
            ),
        )
        return result

    def gse_process_operate(self, hosts, proc_name, setup_path, pid_path, operate_type, system_special=None):
        """
        进程操作
        :param hosts: IP列表
        :param proc_name: 可执行文件的名称
        :param setup_path: 脚本执行路径
        :param pid_path: pid文件所在路径
        :param operate_type: 操作类型
        :param system_special
        :return:
        """

        def gse_process_operate_single(system_info, ip_list):
            _proc_name = self.render_context(system_info, system_special, "proc_name", proc_name)
            _setup_path = self.render_context(system_info, system_special, "setup_path", setup_path)
            _pid_path = self.render_context(system_info, system_special, "pid_path", pid_path)

            if system_info.bk_os_type == "windows":
                # windows
                cmd_tpl = "cd {setup_path} && {{cmd}}.bat {proc_name}".format(
                    setup_path=_setup_path,
                    proc_name=_proc_name,
                )
                value_key = ntpath.join(_setup_path, _proc_name)
            else:
                # linux
                cmd_tpl = "cd {setup_path} && ./{{cmd}}.sh {proc_name} &".format(
                    setup_path=_setup_path,
                    proc_name=_proc_name,
                )
                value_key = posixpath.join(_setup_path, _proc_name)

            task_results = resource.commons.gse_process_manage(
                bk_username=self.operator,
                op_type=operate_type,
                bk_biz_id=self.bk_biz_id,
                process_infos=[
                    {
                        "ip_list": ip_list,
                        "account": system_info.job_execute_account,
                        "proc_name": _proc_name,
                        "setup_path": _setup_path,
                        "pid_path": _pid_path,
                        "type": settings.PROC_RUN_TYPE_PERMANENT,
                        "cpu_lmt": settings.COLLECTOR_DEFAULT_CPU_LIMIT,
                        "mem_lmt": settings.COLLECTOR_DEFAULT_MEM_LIMIT,
                        "start_cmd": cmd_tpl.format(cmd="start"),
                        "stop_cmd": cmd_tpl.format(cmd="stop"),
                        "restart_cmd": cmd_tpl.format(cmd="restart"),
                        "reload_cmd": cmd_tpl.format(cmd="reload"),
                        "value_key": value_key,
                        "start_check_begin_time": 2,
                    }
                ],
            )

            # TODO: 当前AIX系统进程托管存在问题，使用特殊判断绕过报错，问题修复后需要把此处的代码删除！！！
            if system_info.bk_os_type == "aix":
                task_results["success"] = task_results["success"] + task_results["pending"] + task_results["failed"]
                task_results["pending"] = []
                task_results["failed"] = []
            # TODO: 特殊逻辑结束

            return task_results

        result = self.execute_task_by_system(hosts=hosts, task_func=gse_process_operate_single)
        return result

    def gse_process_manage(
        self,
        hosts,
        operate_type,
        proc_name,
        setup_path,
        run_type,
        start_cmd="",
        cycle=0,
        op_timeout=0,
        system_special=None,
    ):
        """
        进程管理
        :param hosts: IP列表
        :param operate_type: 操作类型
        :param proc_name: 进程名称
        :param setup_path: 启动路径
        :param start_cmd: 启动命令
        :param run_type: 启动类型
        :param cycle: 调度周期
        :param op_timeout: 程序执行超时
        :param system_special
        :return:
        """
        result = self.execute_task_by_system(
            hosts=hosts,
            task_func=lambda system_info, ip_list: resource.commons.gse_process_manage(
                bk_username=self.operator,
                op_type=operate_type,
                bk_biz_id=self.bk_biz_id,
                process_infos=[
                    {
                        "ip_list": ip_list,
                        "account": system_info.job_execute_account,
                        "proc_name": self.render_context(system_info, system_special, "proc_name", proc_name),
                        "setup_path": self.render_context(system_info, system_special, "setup_path", setup_path),
                        "start_cmd": self.render_context(system_info, system_special, "start_cmd", start_cmd),
                        "type": self.render_context(system_info, system_special, "run_type", run_type),
                        "cpu_lmt": settings.COLLECTOR_DEFAULT_CPU_LIMIT,
                        "mem_lmt": settings.COLLECTOR_DEFAULT_MEM_LIMIT,
                        "cycle_time": self.render_context(system_info, system_special, "cycle", cycle),
                        "op_timeout": self.render_context(system_info, system_special, "op_timeout", op_timeout),
                    }
                ],
            ),
        )
        return result

    def gse_push_file(self, hosts, path, file_list, system_special=None):
        """
        下发文件
        :param hosts: IP列表
        :param path: 下发路径
        :param file_list: 文件列表，每个元素是file_name和content的字典
        :param system_special
        :return:
        """

        def covert_file_content(files):
            for file_info in files:
                file_info["content"] = base64.b64encode(file_info["content"].encode("utf-8")).decode("utf-8")
            return files

        result = self.execute_task_by_system(
            hosts=hosts,
            task_func=lambda system_info, ip_list: resource.commons.fast_push_file(
                ip_list=ip_list,
                bk_biz_id=self.bk_biz_id,
                account=system_info.job_execute_account,
                file_target_path=self.render_context(system_info, system_special, "path", path),
                file_list=covert_file_content(self.render_context(system_info, system_special, "file_list", file_list)),
            ),
        )
        return result

    @staticmethod
    def label_failed_ip(task_result, label):
        """
        对JOB失败的任务进行标记，用于定位出错所处的步骤
        :param task_result: 任务结果, dict
        :param label: 标签, str
        """
        for host in task_result["failed"]:
            host["errmsg"] = "{}: {}".format(label, host.get("errmsg", ""))
        return task_result
