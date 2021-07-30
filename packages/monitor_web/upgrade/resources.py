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

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers

from core.errors.upgrade import (
    CreateDefaultStrategyError,
    ExportCollectorError,
    MakeMigrationError,
    MigrateError,
    UpgradeNotAllowedError,
)
from bkmonitor.models import StrategyModel
from bkmonitor.utils.upgrade import allow_upgrade
from core.drf_resource import Resource, resource
from monitor_web.strategies.built_in import run_build_in
from monitor_web.upgrade.data_maker import (
    CustomMonitorMaker,
    DashboardMaker,
    ExporterCollectorMaker,
    ScriptCollectorMaker,
    StrategyMaker,
    UptimecheckMaker,
)

logger = logging.getLogger(__name__)

CONFIG_MAKERS = {
    "script": ScriptCollectorMaker,
    "exporter": ExporterCollectorMaker,
}


def order_by_status(items):
    return sorted(items, key=lambda item: ["READY", "FAILED", "SUCCESS"].index(item["status"]))


class ListUpgradeItemsResource(Resource):
    """
    获取待升级项目列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, default=0, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        if not allow_upgrade():
            raise UpgradeNotAllowedError()
        bk_biz_id = validated_request_data["bk_biz_id"]
        try:
            dashboard_views = DashboardMaker.make_migrations(bk_biz_id)
            uptimecheck_tasks = UptimecheckMaker.make_migrations(bk_biz_id)
            custom_monitor_views = CustomMonitorMaker.make_migrations(bk_biz_id)
            monitor_items = StrategyMaker.make_migrations(bk_biz_id)
            script_collectors = ScriptCollectorMaker.make_migrations(bk_biz_id)
            exporter_collectors = ExporterCollectorMaker.make_migrations(bk_biz_id)
        except Exception as e:
            # 如果整体失败，说明数据库模型不匹配，可以认为是不符合升级条件，直接返回空
            logger.exception(_("获取待升级项目列表发生异常，原因：{}").format(e))
            raise MakeMigrationError({"msg": e})
        return {
            "custom_monitor_views": order_by_status(custom_monitor_views),
            "monitor_items": order_by_status(monitor_items),
            "uptimecheck_tasks": order_by_status(uptimecheck_tasks),
            "dashboard_views": order_by_status(dashboard_views),
            "script_collectors": script_collectors,
            "exporter_collectors": exporter_collectors,
        }


class ExecuteUpgradeResource(Resource):
    """
    执行升级
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, default=0, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        if not allow_upgrade():
            raise UpgradeNotAllowedError()

        bk_biz_id = validated_request_data["bk_biz_id"]
        try:
            with transaction.atomic():
                dashboard_views = DashboardMaker.migrate(bk_biz_id)
                uptimecheck_tasks = UptimecheckMaker.migrate(bk_biz_id)
                custom_monitor_migrate_result = CustomMonitorMaker.migrate(bk_biz_id)
                monitor_item_migrate_result = StrategyMaker.migrate(bk_biz_id)
                script_collectors = ScriptCollectorMaker.migrate(bk_biz_id)
                exporter_collectors = ExporterCollectorMaker.migrate(bk_biz_id)

                if bk_biz_id:
                    # 将老版仪表盘迁到新版仪表盘
                    resource.grafana.migrate_old_dashboard(bk_biz_id=bk_biz_id)

        except Exception as e:
            logger.exception(_("执行升级发生异常，原因：{}").format(e))
            raise MigrateError({"msg": e})
        return {
            "dashboard_views": order_by_status(dashboard_views),
            "custom_monitor_views": order_by_status(custom_monitor_migrate_result),
            "monitor_items": order_by_status(monitor_item_migrate_result),
            "uptimecheck_tasks": order_by_status(uptimecheck_tasks),
            "script_collectors": script_collectors,
            "exporter_collectors": exporter_collectors,
        }


class ExportCollectorAsPluginResource(Resource):
    """
    导出老配置为新版插件
    """

    class RequestSerializer(serializers.Serializer):
        config_id = serializers.IntegerField(required=True, label=_("配置ID"))
        config_type = serializers.ChoiceField(required=True, choices=list(CONFIG_MAKERS.keys()))

    def perform_request(self, validated_request_data):
        try:
            config_maker_cls = CONFIG_MAKERS[validated_request_data["config_type"]]
            config_maker = config_maker_cls(validated_request_data["config_id"])
            plugin_path = config_maker.export()
        except Exception as e:
            raise ExportCollectorError({"msg": e})
        return {
            "download_path": plugin_path.replace(settings.MEDIA_ROOT, "", 1),
        }


class CreateBuildInStrategyResource(Resource):
    """
    创建内置策略
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        if StrategyModel.objects.filter(bk_biz_id=bk_biz_id).exists():
            raise CreateDefaultStrategyError({"msg": _("当前策略列表不为空，不允许创建默认策略，请清空后重试")})
        return run_build_in(validated_request_data["bk_biz_id"], force_create=True)


class DisableOldStrategyResource(Resource):
    """
    停用所有老版本策略
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        is_enabled = serializers.BooleanField(default=False, label=_("是否停用"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        is_enabled = validated_request_data["is_enabled"]
        rows = StrategyMaker.toggle_old_monitor_strategy(bk_biz_id, is_enabled)
        return {"count": rows}


class MigrateStrategy(Resource):
    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))
        item_ids = serializers.ListField(required=True, label=_("策略项ID"), child=serializers.IntegerField())
        monitor_source_ids = serializers.ListField(
            default=[], label=_("监控源ID"), child=serializers.IntegerField(), allow_empty=True
        )

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        item_ids = validated_request_data["item_ids"]
        monitor_source_ids = validated_request_data["monitor_source_ids"]

        try:
            with transaction.atomic():
                result = StrategyMaker.migrate_items(bk_biz_id, item_ids, monitor_source_ids)
            return result
        except Exception as e:
            logger.exception(_("执行升级发生异常，原因：{}").format(e))
            raise MigrateError({"msg": e})
