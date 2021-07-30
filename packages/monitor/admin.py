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
import inspect

from django.contrib import admin

from monitor import models


class DatasourceAdmin(admin.ModelAdmin):
    list_display = (
        "cc_biz_id",
        "data_set",
        "data_desc",
        "status",
        "has_exception",
        "creator",
        "create_time",
        "update_time",
    )
    search_fields = ("data_desc", "data_set")
    list_filter = ("cc_biz_id", "status", "creator")


class AgentStatusAdmin(admin.ModelAdmin):
    list_display = ("ds_id", "ip", "status")
    search_fields = ("ds_id",)
    list_filter = ("ds_id", "status")


class ScenarioMenuAdmin(admin.ModelAdmin):
    list_display = ("SYSTEM_MENU_CHOICES", "system_menu", "biz_id", "menu_name")
    search_fields = ("system_menu", "biz_id", "menu_name")
    list_filter = ("system_menu", "biz_id", "menu_name")


class DataCollectorAdmin(admin.ModelAdmin):
    search_fields = ("biz_id",)


class HostPropertyAdmin(admin.ModelAdmin):
    list_display = ("property", "property_display", "required", "selected", "is_deleted")
    list_filter = ("is_deleted",)


class MonitorLocationAdmin(admin.ModelAdmin):
    list_display = ("menu_id", "monitor_id")
    list_filter = ("biz_id",)


class MetricConfAdmin(admin.ModelAdmin):
    list_display = ("metric", "metric_type", "description")
    list_filter = ("metric_type",)


class HostPropertyConfAdmin(admin.ModelAdmin):
    list_display = ("biz_id",)


class OperatorRecorderAdmin(admin.ModelAdmin):
    list_display = ("biz_id", "config_type", "config_id", "config_title", "operator", "operate_time")
    list_filter = ("biz_id",)


class IndexColorConfAdmin(admin.ModelAdmin):
    list_display = ("range", "color", "slug")
    list_filter = ("slug",)


class UserConfigAdmin(admin.ModelAdmin):
    list_display = ("username", "key")
    list_filter = ("username",)


class ApplicationConfigAdmin(admin.ModelAdmin):
    list_display = ("cc_biz_id", "key")
    list_filter = ("cc_biz_id",)


class GlobalConfigAdmin(admin.ModelAdmin):
    list_display = ("key",)


class ScriptCollectorConfigAdmin(admin.ModelAdmin):
    list_display = ("bk_biz_id", "name", "description", "data_id", "status")
    list_filter = ("status", "bk_biz_id")


class ScriptCollectorInstanceAdmin(admin.ModelAdmin):
    list_display = ("config", "type", "ip", "bk_cloud_id", "bk_inst_id", "bk_obj_id")
    list_filter = ("config",)


class ExporterComponentAdmin(admin.ModelAdmin):
    list_display = ("biz_id", "parent_rt_id", "data_id", "status")
    list_filter = ("status", "biz_id")


class UptimeCheckNodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bk_biz_id",
        "is_common",
        "name",
        "ip",
        "plat_id",
        "location",
        "carrieroperator",
        "is_deleted",
        "update_user",
        "update_time",
    )
    list_filter = ("bk_biz_id", "is_common", "ip", "is_deleted", "update_user", "update_time")


class UptimeCheckTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bk_biz_id",
        "protocol",
        "name",
        "location",
        "get_nodes",
        "status",
        "is_deleted",
        "update_user",
        "update_time",
    )
    list_filter = ("bk_biz_id", "protocol", "is_deleted", "update_user", "update_time")

    def get_nodes(self, obj):
        return "\n".join(["{}-{}".format(str(p.id), p.name) for p in obj.nodes.all()])


class UptimeCheckGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "bk_biz_id", "name", "get_nodes", "is_deleted", "update_user", "update_time")
    list_filter = ("bk_biz_id", "is_deleted", "update_user", "update_time")

    def get_nodes(self, obj):
        return "\n".join(["{}-{}".format(str(task.id), task.name) for task in obj.tasks.all()])


# admin.site.register(models.Datasource, DatasourceAdmin)
# admin.site.register(models.AgentStatus, AgentStatusAdmin)
admin.site.register(models.ScenarioMenu, ScenarioMenuAdmin)
admin.site.register(models.HostPropertyConf, HostPropertyConfAdmin)
admin.site.register(models.OperateRecord, OperatorRecorderAdmin)
admin.site.register(models.IndexColorConf, IndexColorConfAdmin)
admin.site.register(models.UserConfig, UserConfigAdmin)
admin.site.register(models.ApplicationConfig, ApplicationConfigAdmin)
admin.site.register(models.GlobalConfig, GlobalConfigAdmin)
admin.site.register(models.ScriptCollectorConfig, ScriptCollectorConfigAdmin)
admin.site.register(models.ScriptCollectorInstance, ScriptCollectorInstanceAdmin)
admin.site.register(models.ExporterComponent, ExporterComponentAdmin)
# admin.site.register(models.UptimeCheckNode, UptimeCheckNodeAdmin)
# admin.site.register(models.UptimeCheckTask, UptimeCheckTaskAdmin)
# admin.site.register(models.UptimeCheckGroup, UptimeCheckGroupAdmin)

# 自动导入剩余model
for name, obj in inspect.getmembers(models):
    try:
        if inspect.isclass(obj):
            admin.site.register(getattr(models, name))
    except Exception:
        pass
