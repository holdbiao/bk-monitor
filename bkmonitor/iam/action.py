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

from typing import Union, List, Dict

from core.errors.iam import ActionNotExistError
from iam import Action


class ActionMeta(Action):
    """
    动作定义
    """

    def __init__(
        self,
        id: str,
        name: str,
        name_en: str,
        type: str,
        version: int,
        related_resource_types: list = None,
        related_actions: list = None,
        description: str = "",
        description_en: str = "",
    ):
        super(ActionMeta, self).__init__(id)
        self.name = name
        self.name_en = name_en
        self.type = type
        self.version = version
        self.related_resource_types = related_resource_types or []
        self.related_actions = related_actions or []
        self.description = description
        self.description_en = description_en

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "type": self.type,
            "version": self.version,
            "related_resource_types": self.related_resource_types,
            "related_actions": self.related_actions,
            "description": self.description,
            "description_en": self.description_en,
        }

    def is_read_action(self):
        """
        是否为读权限
        """
        return self.type == "view"


# CMDB 业务资源类型
CMDB_BUSINESS_RESOURCE = {
    "id": "biz",
    "system_id": "bk_cmdb",
    "selection_mode": "instance",
    "related_instance_selections": [{"system_id": "bk_cmdb", "id": "business"}],
}


class ActionEnum:

    VIEW_BUSINESS = ActionMeta(
        id="view_business",
        name="业务访问",
        name_en="View Business",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[],
        version=1,
    )

    VIEW_HOME = ActionMeta(
        id="view_home",
        name="首页查看",
        name_en="View Home",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    EXPLORE_METRIC = ActionMeta(
        id="explore_metric",
        name="指标检索",
        name_en="Explore Metric",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    VIEW_SYNTHETIC = ActionMeta(
        id="view_synthetic",
        name="拨测查看",
        name_en="View Synthetic",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_SYNTHETIC = ActionMeta(
        id="manage_synthetic",
        name="拨测管理",
        name_en="Manage Synthetic",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_SYNTHETIC.id],
        version=1,
    )

    MANAGE_PUBLIC_SYNTHETIC_LOCATION = ActionMeta(
        id="manage_public_synthetic_location",
        name="拨测公共节点管理",
        name_en="Manage Public Synthetic Location",
        type="manage",
        related_resource_types=[],
        related_actions=[VIEW_SYNTHETIC.id],
        version=1,
    )

    VIEW_HOST = ActionMeta(
        id="view_host",
        name="主机详情查看",
        name_en="View Host",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_HOST = ActionMeta(
        id="manage_host",
        name="主机详情管理",
        name_en="Manage Host",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id, VIEW_HOST.id],
        version=1,
    )

    VIEW_EVENT = ActionMeta(
        id="view_event",
        name="事件中心查看",
        name_en="View Event",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    VIEW_PLUGIN = ActionMeta(
        id="view_plugin",
        name="插件查看",
        name_en="View Plugin",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_PLUGIN = ActionMeta(
        id="manage_plugin",
        name="插件管理",
        name_en="Manage Plugin",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_PLUGIN.id],
        version=1,
    )

    MANAGE_PUBLIC_PLUGIN = ActionMeta(
        id="manage_public_plugin",
        name="公共插件管理",
        name_en="Manage Public Plugin",
        type="manage",
        related_resource_types=[],
        related_actions=[MANAGE_PLUGIN.id],
        version=1,
    )

    VIEW_COLLECTION = ActionMeta(
        id="view_collection",
        name="采集查看",
        name_en="View Collection",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_COLLECTION = ActionMeta(
        id="manage_collection",
        name="采集管理",
        name_en="Manage Collection",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_COLLECTION.id],
        version=1,
    )

    VIEW_NOTIFY_TEAM = ActionMeta(
        id="view_notify_team",
        name="告警组查看",
        name_en="View Notify Team",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_NOTIFY_TEAM = ActionMeta(
        id="manage_notify_team",
        name="告警组管理",
        name_en="Manage Notify Team",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_NOTIFY_TEAM.id],
        version=1,
    )

    VIEW_RULE = ActionMeta(
        id="view_rule",
        name="策略查看",
        name_en="View Rule",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id, VIEW_NOTIFY_TEAM.id],
        version=1,
    )

    MANAGE_RULE = ActionMeta(
        id="manage_rule",
        name="策略管理",
        name_en="Manage Rule",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_RULE.id, VIEW_NOTIFY_TEAM.id],
        version=1,
    )

    VIEW_DOWNTIME = ActionMeta(
        id="view_downtime",
        name="屏蔽查看",
        name_en="View Downtime",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_DOWNTIME = ActionMeta(
        id="manage_downtime",
        name="屏蔽管理",
        name_en="Manage Downtime",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_NOTIFY_TEAM.id, VIEW_RULE.id],
        version=1,
    )

    VIEW_CUSTOM_METRIC = ActionMeta(
        id="view_custom_metric",
        name="自定义指标上报查看",
        name_en="View Custom Metric",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_CUSTOM_METRIC = ActionMeta(
        id="manage_custom_metric",
        name="自定义指标上报管理",
        name_en="Manage Custom Metric",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_CUSTOM_METRIC.id],
        version=1,
    )

    VIEW_CUSTOM_EVENT = ActionMeta(
        id="view_custom_event",
        name="自定义事件上报查看",
        name_en="View Custom Event",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_CUSTOM_EVENT = ActionMeta(
        id="manage_custom_event",
        name="自定义事件上报管理",
        name_en="Manage Custom Event",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_CUSTOM_EVENT.id],
        version=1,
    )

    VIEW_DASHBOARD = ActionMeta(
        id="view_dashboard",
        name="仪表盘查看",
        name_en="View Dashboard",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_DASHBOARD = ActionMeta(
        id="manage_dashboard",
        name="仪表盘管理",
        name_en="Manage Dashboard",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_DASHBOARD.id],
        version=1,
    )

    EXPORT_CONFIG = ActionMeta(
        id="export_config",
        name="导出",
        name_en="Export Config",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    IMPORT_CONFIG = ActionMeta(
        id="import_config",
        name="导入",
        name_en="Import Config",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    VIEW_SERVICE_CATEGORY = ActionMeta(
        id="view_service_category",
        name="服务分类查看",
        name_en="View Service Category",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    VIEW_GLOBAL_SETTING = ActionMeta(
        id="view_global_setting",
        name="全局配置查看",
        name_en="View Global Setting",
        type="view",
        related_resource_types=[],
        version=1,
    )

    MANAGE_GLOBAL_SETTING = ActionMeta(
        id="manage_global_setting",
        name="全局配置编辑",
        name_en="Manage Global Setting",
        type="manage",
        related_resource_types=[],
        version=1,
    )

    VIEW_SELF_STATE = ActionMeta(
        id="view_self_state",
        name="自监控查看",
        name_en="View Self-state",
        type="view",
        related_resource_types=[],
        version=1,
    )

    MANAGE_UPGRADE = ActionMeta(
        id="manage_upgrade",
        name="配置升级管理",
        name_en="Manage Upgrade",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    VIEW_FUNCTION_SWITCH = ActionMeta(
        id="view_function_switch",
        name="功能设置查看",
        name_en="View Function Switch",
        type="view",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_BUSINESS.id],
        version=1,
    )

    MANAGE_FUNCTION_SWITCH = ActionMeta(
        id="manage_function_switch",
        name="功能设置管理",
        name_en="Manage Function Switch",
        type="manage",
        related_resource_types=[CMDB_BUSINESS_RESOURCE],
        related_actions=[VIEW_FUNCTION_SWITCH.id],
        version=1,
    )


_all_actions = {action.id: action for action in ActionEnum.__dict__.values() if isinstance(action, ActionMeta)}


def get_action_by_id(action_id: Union[str, ActionMeta]) -> ActionMeta:
    """
    根据动作ID获取动作实例
    """
    if isinstance(action_id, ActionMeta):
        # 如果已经是实例，则直接返回
        return action_id

    if action_id not in _all_actions:
        raise ActionNotExistError({"action_id": action_id})

    return _all_actions[action_id]


def fetch_related_actions(actions: List[Union[ActionMeta, str]]) -> Dict[str, ActionMeta]:
    """
    递归获取 action 动作依赖列表
    """
    actions = [get_action_by_id(action) for action in actions]

    def fetch_related_actions_recursive(_action: ActionMeta):
        _related_actions = {}
        for related_action_id in _action.related_actions:
            try:
                related_action = get_action_by_id(related_action_id)
            except ActionNotExistError:
                continue
            _related_actions[related_action_id] = related_action
            _related_actions.update(fetch_related_actions_recursive(related_action))
        return _related_actions

    related_actions = {}
    for action in actions:
        related_actions.update(fetch_related_actions_recursive(action))

    # 剔除根节点本身
    for action in actions:
        related_actions.pop(action.id, None)

    return related_actions


def generate_all_actions_json() -> List:
    """
    生成migrations的json配置
    """
    results = []
    for value in _all_actions.values():
        results.append({"operation": "upsert_action", "data": value.to_json()})
    return results
