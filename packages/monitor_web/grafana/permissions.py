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
from typing import Tuple

from bk_dataview.grafana.permissions import BasePermission, GrafanaRole
from bkmonitor.iam import Permission, ActionEnum


class BizPermission(BasePermission):
    """
    业务权限
    """

    def has_permission(self, request, view, org_name: str) -> Tuple[bool, GrafanaRole]:
        if request.user.is_superuser:
            return True, GrafanaRole.Admin

        bk_biz_id = int(org_name)
        permission = Permission()

        if permission.is_allowed_by_biz(bk_biz_id, ActionEnum.MANAGE_DASHBOARD):
            return True, GrafanaRole.Editor

        permission.is_allowed_by_biz(bk_biz_id, ActionEnum.VIEW_DASHBOARD, raise_exception=True)
        return True, GrafanaRole.Viewer
