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


import logging
import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import ugettext as _

from core.errors.upgrade import SyncHistoryFileError
from bkmonitor.utils.dns_resolve import resolve_domain
from bkmonitor.utils.local import local
from bkmonitor.utils.request import get_request
from core.drf_resource import api, resource
from monitor.models import ExporterComponent, UploadedFile
from monitor_web.commons.job import JobTaskClient
from monitor_web.plugin.constant import ParamMode
from monitor_web.plugin.manager import PluginManagerFactory
from monitor_web.upgrade.data_maker.base import BaseDataMaker

logger = logging.getLogger(__name__)


class ExporterCollectorMaker(BaseDataMaker):
    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        configs = ExporterComponent.objects.using("monitor_saas_3_1").filter(is_internal=False).all()

        if bk_biz_id:
            configs = configs.filter(biz_id=bk_biz_id)

        results = []
        for config in configs:
            results.append(
                {
                    "bk_biz_id": config.biz_id,
                    "id": config.id,
                    "name": config.component_name,
                    "display_name": config.component_name_display,
                }
            )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        # 插件数据不迁移，仅导出
        return cls.make_migrations(bk_biz_id)

    def __init__(self, config_id):
        self.config = ExporterComponent.objects.using("monitor_saas_3_1").get(id=config_id)
        self.plugin_id = self.config.component_name

    @classmethod
    def job_sync_exporter_files(cls):
        """
        将旧版本的exporter文件同步到新版本的media目录下
        """
        blueking_biz_id = api.cmdb.get_blueking_biz()
        appo_ip = resolve_domain("appo.service.consul")
        if appo_ip:
            appo_ip = appo_ip[0]
        elif settings.APPO_IP:
            appo_ip = settings.APPO_IP
        else:
            logger.info("appo_ip not found, skip to sync exporter files")
            # 如果都没有配置IP，忽略
            return
        hosts = api.cmdb.get_host_by_ip(ips=[{"ip": appo_ip}], bk_biz_id=blueking_biz_id)
        if not hosts:
            # 找不到主机，忽略
            return
        host = hosts[0]
        with open(os.path.join(os.path.dirname(__file__), "sync_history_files.sh"), "r") as fd:
            script_content = fd.read()

        # 临时提权
        request = get_request(peaceful=True)
        if request:
            origin_username = request.user.username
            request.user.username = settings.COMMON_USERNAME
        else:
            origin_username = getattr(local, "username", None)
            local.username = settings.COMMON_USERNAME

        job_client = JobTaskClient(host.bk_biz_id, settings.COMMON_USERNAME)
        result = job_client.fast_execute_script(
            hosts=[{"ip": host.ip, "plat_id": host.bk_cloud_id, "bk_cloud_id": host.bk_cloud_id}],
            script_content=script_content,
        )

        # 将local变量重置回初试状态
        if request:
            request.user.username = origin_username
        else:
            local.username = origin_username

        if result["failed"]:
            raise SyncHistoryFileError(result["failed"][0]["errmsg"])

    def make_collector_json(self):
        collector_json = {}
        exporter_file_infos = {
            "linux": self.config.exporter_file_info,
            "windows": self.config.windows_exporter_file_info,
        }
        for os_type, file_info in list(exporter_file_infos.items()):
            if not file_info:
                continue
            uploaded_file = UploadedFile.objects.using("monitor_saas_3_1").get(id=file_info["file_id"])
            if not os.path.exists(uploaded_file.file_data.path):
                # 文件不存在，尝试从 JOB 同步
                self.job_sync_exporter_files()
            file_data = SimpleUploadedFile(uploaded_file.file_data.name, uploaded_file.file_data.read())
            result = resource.plugin.plugin_file_upload(file_data=file_data)
            collector_json[os_type] = result
        return collector_json

    def make_config_json(self):
        config_json = [
            {
                "description": _("监听IP"),
                "default": "127.0.0.1",
                "visible": False,
                "mode": "collector",
                "type": "text",
                "name": "host",
            },
            {
                "description": _("监听端口"),
                "default": "",
                "visible": False,
                "mode": "collector",
                "type": "text",
                "name": "port",
            },
        ]
        for item in self.config.config_schema:
            if item["mode"] == "collector":
                continue
            config_json.append(
                {
                    "default": item["default"],
                    "mode": ParamMode.OPT_CMD if item["mode"] == "cmd" else ParamMode.ENV,
                    "type": "password" if item["type"] == "password" else "text",
                    "description": item["description"],
                    "name": item["name"],
                }
            )
        return config_json

    def make_metric_json(self):
        type_mapping = {
            "long": "int",
        }
        metric_json = []
        for table in self.config.indices:
            fields = []
            for field in table["fields"]:
                fields.append(
                    {
                        "type": type_mapping.get(field["type"], field["type"]),
                        "monitor_type": field["monitor_type"],
                        "unit": field["unit"],
                        "name": field["name"],
                        "source_name": "",
                        "description": field["description"],
                        "is_active": True,
                        "is_diff_metric": False,
                    }
                )
            metric_json.append({"table_name": table["table_name"], "table_desc": table["table_desc"], "fields": fields})

        return metric_json

    def export(self):
        plugin_params = {
            "bk_biz_id": self.config.biz_id,
            "plugin_id": self.plugin_id,
            "plugin_display_name": self.config.component_name_display,
            "plugin_type": "Exporter",
            "logo": self.config.logo,
            "collector_json": self.make_collector_json(),
            "config_json": self.make_config_json(),
            "metric_json": self.make_metric_json(),
            "label": "component",
            "version_log": "",
            "signature": "",
            "is_support_remote": False,
            "description_md": self.config.component_desc,
        }
        plugin_manager = PluginManagerFactory.get_manager(plugin=self.plugin_id, plugin_type="Exporter")
        plugin_manager.create_tmp_version_by_data(plugin_params)
        plugin_manager.make_package()

        package_path = os.path.join(plugin_manager.tmp_path, plugin_manager.plugin.plugin_id + ".tgz")
        return package_path
