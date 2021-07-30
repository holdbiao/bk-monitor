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


import os

from django.utils.translation import ugettext as _

from monitor.models import ScriptCollectorConfig
from monitor_web.plugin.manager import PluginManagerFactory
from monitor_web.upgrade.data_maker.base import BaseDataMaker


class ScriptCollectorMaker(BaseDataMaker):
    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        configs = ScriptCollectorConfig.objects.using("monitor_saas_3_1").all()

        if bk_biz_id:
            configs = configs.filter(bk_biz_id=bk_biz_id)

        results = []
        for config in configs:
            results.append(
                {
                    "bk_biz_id": config.bk_biz_id,
                    "id": config.id,
                    "name": config.name,
                    "display_name": config.description,
                }
            )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        # 插件数据不迁移，仅导出
        return cls.make_migrations(bk_biz_id)

    def __init__(self, config_id):
        self.config = ScriptCollectorConfig.objects.using("monitor_saas_3_1").get(id=config_id)
        self.plugin_id = self.config.name

    def make_collector_json(self):
        windows_only = self.config.script_ext in ["bat", "powershell", "vbs"]
        collector_json = {
            "windows": {
                "filename": self.config.script_name,
                "type": self.config.script_ext,
                "script_content_base64": self.config.script_content_base64 or "",
            }
        }
        if not windows_only:
            # 如果不是windows专属后缀，需要加上linux的配置
            collector_json["linux"] = collector_json["windows"]
        return collector_json

    def make_config_json(self):
        if not self.config.params_schema:
            return []
        config_json = [
            {
                "default": "",
                "mode": "pos_cmd",
                "type": "text",
                "description": item["description"],
                "name": item["name"],
            }
            for item in self.config.params_schema
        ]
        return config_json

    def make_metric_json(self):
        type_mapping = {
            "long": "int",
        }
        fields = [
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
            for field in self.config.fields
        ]

        return [
            {
                "fields": fields,
                "table_name": "base",
                "table_desc": _("默认分类"),
            }
        ]

    def export(self):
        plugin_params = {
            "bk_biz_id": self.config.bk_biz_id,
            "plugin_id": self.plugin_id,
            "plugin_display_name": self.config.description,
            "plugin_type": "Script",
            "logo": "",
            "collector_json": self.make_collector_json(),
            "config_json": self.make_config_json(),
            "metric_json": self.make_metric_json(),
            "label": "other_rt",
            "version_log": "",
            "signature": "",
            "is_support_remote": False,
            "description_md": "",
        }
        plugin_manager = PluginManagerFactory.get_manager(plugin=self.plugin_id, plugin_type="Script")
        plugin_manager.create_tmp_version_by_data(plugin_params)
        plugin_manager.make_package()

        package_path = os.path.join(plugin_manager.tmp_path, plugin_manager.plugin.plugin_id + ".tgz")
        return package_path
