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
from __future__ import absolute_import, unicode_literals

from ..default import (
    CreateConfigTemplateResource,
    CreateSubscriptionResource,
    DeletePluginResource,
    DeleteSubscriptionResource,
    ExportQueryTaskResource,
    ExportRawPackageResource,
    PluginInfoResource,
    QueryDebugResource,
    QueryRegisterTaskResource,
    RegisterPackageResource,
    ReleaseConfigResource,
    ReleasePluginResource,
    RenderConfigTemplateResource,
    RunSubscriptionResource,
    StartDebugResource,
    StopDebugResource,
    SubscriptionInfoResource,
    SubscriptionInstanceStatusResource,
    SwitchSubscriptionResource,
    TaskResultDetailResource,
    TaskResultResource,
    UpdateSubscriptionResource,
    UploadResource,
    RevokeSubscriptionResource,
    GetProxiesResource,
    GetProxiesByBizResource,
    PluginOperate,
)

CreateConfigTemplateResource.action = "backend/api/plugin/create_config_template/"
CreateSubscriptionResource.action = "backend/api/subscription/create/"
DeletePluginResource.action = "backend/api/plugin/delete/"
DeleteSubscriptionResource.action = "backend/api/subscription/delete/"
ExportQueryTaskResource.action = "backend/api/plugin/query_export_task/"
ExportRawPackageResource.action = "backend/api/plugin/create_export_task/"
PluginInfoResource.action = "backend/api/plugin/info/"
QueryDebugResource.action = "backend/api/plugin/query_debug/"
QueryRegisterTaskResource.action = "backend/api/plugin/query_register_task/"
RegisterPackageResource.action = "backend/api/plugin/create_register_task/"
ReleaseConfigResource.action = "backend/api/plugin/release_config_template/"
ReleasePluginResource.action = "backend/api/plugin/release/"
RenderConfigTemplateResource.action = "backend/api/plugin/render_config_template/"
RunSubscriptionResource.action = "backend/api/subscription/run/"
StartDebugResource.action = "backend/api/plugin/start_debug/"
StopDebugResource.action = "backend/api/plugin/stop_debug/"
SubscriptionInfoResource.action = "backend/api/subscription/info/"
SubscriptionInstanceStatusResource.action = "backend/api/subscription/instance_status/"
SwitchSubscriptionResource.action = "backend/api/subscription/switch/"
TaskResultDetailResource.action = "backend/api/subscription/task_result_detail/"
TaskResultResource.action = "backend/api/subscription/task_result/"
UpdateSubscriptionResource.action = "backend/api/subscription/update/"
GetProxiesResource.action = "api/host/proxies/"
GetProxiesByBizResource.action = "api/host/biz_proxies/"
PluginOperate.action = "api/plugin/operate/"
UploadResource.action = UploadResource.action  # nothing to do
RevokeSubscriptionResource.action = "backend/api/subscription/revoke/"
