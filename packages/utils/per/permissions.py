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
import functools
import inspect

from utils.per.define import define


def enum(**enums):
    return type("Enum", (), enums)


class PermissionMaker(object):
    """
    权限管理
    """

    def __init__(self, action_obj):
        self.action = action_obj

    def __call__(self, func):
        if inspect.isclass(func):
            return self.decorate_class(func)
        return self.decorate_callable(func)

    def decorate_class(self, klass):
        pass

    def decorate_callable(self, func):
        if hasattr(func, "decorating"):
            func.decorating.append(self)
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args += tuple(func.decorating)
            return func(*args, **kwargs)

        wrapper.decorating = [self]
        return wrapper


require = PermissionMaker
