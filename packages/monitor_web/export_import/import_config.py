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


import copy
import logging
import re

from django.db import transaction
from django.utils.translation import ugettext as _
from six.moves import map

from core.errors.collecting import SubscriptionStatusError
from core.errors.export_import import ImportConfigError
from bkmonitor.models import NoticeGroup, StrategyModel
from core.drf_resource import resource
from bkmonitor.utils.local import local
from monitor_web.collecting.constant import OperationResult, OperationType
from monitor_web.collecting.resources import update_config_operation_result
from monitor_web.export_import.constant import ConfigType, ImportDetailStatus
from monitor_web.models import (
    CollectConfigMeta,
    CollectorPluginMeta,
    DeploymentConfigVersion,
    ImportDetail,
    ImportParse,
)
from monitor_web.plugin.manager import PluginManagerFactory
from monitor_web.plugin.resources import CreatePluginResource
from utils import count_md5

logger = logging.getLogger("monitor_web")


def import_plugin(bk_biz_id, plugin_config):
    parse_instance = ImportParse.objects.get(id=plugin_config.parse_id)
    config = parse_instance.config
    plugin_id = config["plugin_id"]
    plugin_type = config["plugin_type"]
    config["bk_biz_id"] = bk_biz_id
    exist_plugin = CollectorPluginMeta.objects.filter(plugin_id=plugin_id).first()
    if exist_plugin:
        # 避免导入包和原插件内容一致，文件名不同
        def handle_collector_json(config_value):
            for config_msg in list(config_value.get("collector_json", {}).values()):
                if isinstance(config_msg, dict):
                    config_msg.pop("file_name", None)
                    config_msg.pop("file_id", None)
            return config_value

        exist_version = exist_plugin.current_version
        now_config_data = copy.deepcopy(exist_version.config.config2dict())
        tmp_config_data = copy.deepcopy(exist_version.config.config2dict(config))
        now_config_data, tmp_config_data = list(map(handle_collector_json, [now_config_data, tmp_config_data]))
        now_info_data = exist_version.info.info2dict()
        tmp_info_data = exist_version.info.info2dict(config)
        old_config_md5, new_config_md5, old_info_md5, new_info_md5 = list(
            map(count_md5, [now_config_data, tmp_config_data, now_info_data, tmp_info_data])
        )
        if all([old_config_md5 == new_config_md5, old_info_md5 == new_info_md5, exist_version.is_release]):
            plugin_config.config_id = exist_version.plugin.plugin_id
            plugin_config.import_status = ImportDetailStatus.SUCCESS
            plugin_config.error_msg = ""
            plugin_config.save()
        else:
            plugin_config.import_status = ImportDetailStatus.FAILED
            plugin_config.error_msg = _("插件ID已存在")
            plugin_config.save()
    else:
        try:
            serializers_obj = CreatePluginResource.SERIALIZERS[config.get("plugin_type")](data=config)
            serializers_obj.is_valid(raise_exception=True)
            with transaction.atomic():
                serializers_obj.save()
                plugin_manager = PluginManagerFactory.get_manager(
                    plugin=plugin_id, plugin_type=plugin_type, operator=local.username
                )
                version, no_use = plugin_manager.create_version(config)
            result = resource.plugin.plugin_register(
                plugin_id=version.plugin.plugin_id,
                config_version=version.config_version,
                info_version=version.info_version,
            )
            plugin_manager.release(
                config_version=version.config_version, info_version=version.info_version, token=result["token"]
            )
            plugin_config.config_id = version.plugin.plugin_id
            plugin_config.import_status = ImportDetailStatus.SUCCESS
            plugin_config.error_msg = ""
            plugin_config.save()
        except Exception as e:
            plugin_config.import_status = ImportDetailStatus.FAILED
            plugin_config.error_msg = str(e)
            plugin_config.save()

    return plugin_config


def import_collect_without_plugin(data):
    result = resource.collecting.save_collect_config(data)
    collect_config = CollectConfigMeta.objects.select_related("deployment_config").get(id=result["id"])
    try:
        update_config_operation_result(collect_config)
    except SubscriptionStatusError as e:
        logger.exception(str(e))
    return result


def import_one_log_collect(data, bk_biz_id):
    data.pop("id")
    data["bk_biz_id"] = bk_biz_id
    data["plugin_id"] = "default_log"
    data["target_nodes"] = []
    return import_collect_without_plugin(data)


def import_process_collect(data, bk_biz_id):
    data.pop("id")
    data["bk_biz_id"] = bk_biz_id
    data["target_nodes"] = []
    return import_collect_without_plugin(data)


import_handler = {
    CollectConfigMeta.CollectType.PROCESS: import_process_collect,
    CollectConfigMeta.CollectType.LOG: import_one_log_collect,
}


def import_collect(bk_biz_id, import_history_instance, collect_config_list):
    def handle_collect_without_plugin(import_collect_obj, config_dict, target_bk_biz_id, handle_func):
        try:
            handle_result = handle_func(config_dict, target_bk_biz_id)
        except Exception as e:
            import_collect_obj.import_status = ImportDetailStatus.FAILED
            import_collect_obj.error_msg = str(e)
            import_collect_obj.config_id = None
            import_collect_obj.save()
        else:
            import_collect_obj.config_id = handle_result["id"]
            import_collect_obj.import_status = ImportDetailStatus.SUCCESS
            import_collect_obj.error_msg = ""
            import_collect_obj.save()

    for import_collect_config in collect_config_list:
        parse_instance = ImportParse.objects.get(id=import_collect_config.parse_id)
        config = parse_instance.config
        if config["collect_type"] in [CollectConfigMeta.CollectType.PROCESS, CollectConfigMeta.CollectType.LOG]:
            handler = import_handler[config["collect_type"]]
            handle_collect_without_plugin(import_collect_config, config, bk_biz_id, handler)
            continue

        config["bk_biz_id"] = bk_biz_id
        config["target_nodes"] = []
        plugin_instance = ImportDetail.objects.filter(
            history_id=import_history_instance.id, type=ConfigType.PLUGIN, name=config["plugin_id"]
        ).first()
        if not plugin_instance:
            import_collect_config.import_status = ImportDetailStatus.FAILED
            import_collect_config.error_msg = _("关联插件不存在")
            import_collect_config.save()
            continue

        plugin_instance = import_plugin(bk_biz_id, plugin_instance)
        if plugin_instance.import_status == ImportDetailStatus.FAILED:
            import_collect_config.import_status = ImportDetailStatus.FAILED
            import_collect_config.error_msg = _("关联插件导入失败")
            import_collect_config.save()
            continue

        plugin_obj = CollectorPluginMeta.objects.get(plugin_id=plugin_instance.config_id)
        deployment_config_params = {
            "plugin_version": plugin_obj.packaged_release_version,
            "target_node_type": config["target_node_type"],
            "params": config["params"],
            "target_nodes": [],
            "remote_collecting_host": config.get("remote_collecting_host"),
            "config_meta_id": 0,
        }
        collect_config = None
        deployment_config = None
        try:
            deployment_config = DeploymentConfigVersion.objects.create(**deployment_config_params)
            collect_config = CollectConfigMeta(
                bk_biz_id=config["bk_biz_id"],
                name=config["name"],
                last_operation=OperationType.CREATE,
                operation_result=OperationResult.PREPARING,
                collect_type=config["collect_type"],
                plugin=plugin_obj,
                target_object_type=config["target_object_type"],
                deployment_config=deployment_config,
                label=config["label"],
            )
            collect_config.deployment_config_id = deployment_config.id
            collect_config.save()
            deployment_config.config_meta_id = collect_config.id
            deployment_config.save()
            result = collect_config.create_subscription()
            if result["task_id"]:
                deployment_config.subscription_id = result["subscription_id"]
                collect_config.operation_result = OperationResult.PREPARING
                deployment_config.task_ids = [result["task_id"]]
                deployment_config.save()
                collect_config.last_operation = OperationType.STOP
                collect_config.save()
            import_collect_config.config_id = collect_config.id
            import_collect_config.import_status = ImportDetailStatus.SUCCESS
            import_collect_config.error_msg = ""
            import_collect_config.save()
        except Exception as e:
            if collect_config:
                collect_config.is_deleted = True
                collect_config.save()
            if deployment_config:
                deployment_config.is_deleted = True
                deployment_config.save()
            import_collect_config.import_status = ImportDetailStatus.FAILED
            import_collect_config.error_msg = str(e)
            import_collect_config.config_id = None
            import_collect_config.save()


def import_strategy(bk_biz_id, import_history_instance, strategy_config_list):
    # 已导入的采集配置，原有ID与创建ID映射，用于更改策略配置的监控条件中关联采集配置
    import_collect_configs = ImportDetail.objects.filter(
        type=ConfigType.COLLECT, history_id=import_history_instance.id, import_status=ImportDetailStatus.SUCCESS
    )
    import_config_id_map = dict()
    for import_config_instance in import_collect_configs:
        parse_instance = ImportParse.objects.get(id=import_config_instance.parse_id)
        import_config_id_map[parse_instance.config["id"]] = int(import_config_instance.config_id)

    for strategy_config in strategy_config_list:
        parse_instance = ImportParse.objects.get(id=strategy_config.parse_id)
        create_config = copy.deepcopy(parse_instance.config)
        create_config["bk_biz_id"] = bk_biz_id
        action_list = create_config["action_list"]
        for number, action_detail in enumerate(action_list):
            notice_group_ids = []
            for notice_detail in action_detail["notice_group_list"]:
                notice_group_name = notice_detail["name"]
                instance = NoticeGroup.objects.filter(name=notice_group_name).first()
                if not instance:
                    instance = NoticeGroup.objects.create(
                        name=notice_group_name, bk_biz_id=bk_biz_id, notice_receiver=[], notice_way={}
                    )

                notice_group_ids.append(instance.id)
            create_config["action_list"][number]["notice_group_list"] = notice_group_ids

        try:
            # 替换agg_condition中关联采集配置相关信息
            agg_condition = create_config["item_list"][0].get("rt_query_config", {}).get("agg_condition", [])
            for condition_msg in agg_condition:
                if "bk_collect_config_id" in list(condition_msg.values()):
                    old_config_id_desc = condition_msg["value"]
                    new_config_ids = []
                    # 兼容condition数据为非列表数据
                    if not isinstance(old_config_id_desc, list):
                        old_config_id_desc = [old_config_id_desc]

                    for old_config_id in old_config_id_desc:
                        # 兼容原来采集配置ID包含采集名称的情况
                        re_match = re.match(r"(\d+).*", str(old_config_id))
                        old_config_id = re_match.groups()[0] if re_match.groups() else 0
                        if not import_config_id_map.get(int(old_config_id)):
                            raise ImportConfigError({"msg": _("关联采集配置{}未导入成功").format(old_config_id)})
                        new_config_ids.append(str(import_config_id_map[int(old_config_id)]))
                    condition_msg["value"] = new_config_ids

            result = resource.strategies.backend_strategy_config(**create_config)
            StrategyModel.objects.filter(id=result["id"]).update(is_enabled=False)
            strategy_config.config_id = result["id"]
            strategy_config.import_status = ImportDetailStatus.SUCCESS
            strategy_config.error_msg = ""
            strategy_config.save()
        except Exception as e:
            logger.exception(e)
            strategy_config.import_status = ImportDetailStatus.FAILED
            strategy_config.error_msg = str(e)
            strategy_config.save()
