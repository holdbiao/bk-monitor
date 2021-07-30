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
from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from core.drf_resource import resource

# from monitor_web.permissions import SuperuserWritePermission


class UpgradeViewSet(IAMPermissionMixin, ResourceViewSet):

    iam_read_actions = ActionEnum.MANAGE_UPGRADE
    iam_write_actions = ActionEnum.MANAGE_UPGRADE

    resource_routes = [
        ResourceRoute("GET", resource.upgrade.list_upgrade_items, endpoint="list_upgrade_items"),
        ResourceRoute("POST", resource.upgrade.execute_upgrade, endpoint="execute_upgrade"),
        ResourceRoute("POST", resource.upgrade.export_collector_as_plugin, endpoint="export_collector_as_plugin"),
        ResourceRoute("POST", resource.upgrade.create_build_in_strategy, endpoint="create_build_in_strategy"),
        ResourceRoute("POST", resource.upgrade.disable_old_strategy, endpoint="disable_old_strategy"),
        ResourceRoute("POST", resource.upgrade.migrate_strategy, endpoint="migrate_strategy"),
    ]
