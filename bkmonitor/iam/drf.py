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
"""
DRF 插件
"""
from typing import Union, List

from rest_framework import permissions

from bkmonitor.iam import Permission
from bkmonitor.iam.action import ActionMeta
from core.errors.iam import PermissionDeniedError


class IAMPermissionMixin:
    """
    DRF鉴权插件集成
    """

    # 安全的HTTP请求方法使用的鉴权动作
    iam_read_actions: Union[ActionMeta, List[ActionMeta]] = []

    # 非安全的HTTP方法使用的鉴权动作
    iam_write_actions: Union[ActionMeta, List[ActionMeta]] = []

    def get_iam_actions(self):
        """
        获取IAM鉴权时所使用的动作，可由子类重写
        """
        if self.request.method in permissions.SAFE_METHODS:
            # 如果是安全方法，则使用读动作鉴权
            iam_read_actions = self.iam_read_actions
            if isinstance(iam_read_actions, ActionMeta):
                iam_read_actions = [iam_read_actions]
            return iam_read_actions

        # 否则使用写动作鉴权
        iam_write_actions = self.iam_write_actions
        if isinstance(iam_write_actions, ActionMeta):
            iam_write_actions = [iam_write_actions]
        return iam_write_actions

    class PermissionMeta(permissions.BasePermission):
        def __init__(self, actions):
            self.actions = actions

        def has_permission(self, request, view):
            """
            Return `True` if permission is granted, `False` otherwise.
            """
            if not self.actions:
                return True

            client = Permission()

            for index, action in enumerate(self.actions):
                try:
                    if request.biz_id:
                        client.is_allowed_by_biz(bk_biz_id=request.biz_id, action=action, raise_exception=True)
                    else:
                        client.is_allowed(action=action, raise_exception=True)
                except PermissionDeniedError as e:
                    # 最后一个异常才抛出，否则不处理
                    if index == len(self.actions) - 1:
                        raise e
                else:
                    # 没抛出异常，则鉴权通过
                    return True
            return True

        def has_object_permission(self, request, view, obj):
            """
            Return `True` if permission is granted, `False` otherwise.
            """
            return self.has_permission(request, view)

    def get_permissions(self):
        actions = self.get_iam_actions()
        return [self.PermissionMeta(actions)]
