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
from utils.per.exceptions import InvalidActionDefine, ResourceActionNotDefine, ResourceTypeNoeDefine, ScopeNotDefine


class ActionDefine(tuple):

    parent = None

    def __contains__(self, item):
        return item is not None and (self is item or item[: len(self)] == self)

    def __getattr__(self, name):
        new = ActionDefine(self + (name,))
        if len(self) >= 3:
            raise InvalidActionDefine
        setattr(self, name, new)
        new.parent = self
        return new

    def __repr__(self):
        return "define" + ("." if self else "") + ".".join(self)

    @property
    def is_action(self):
        return len(self) == 3

    @property
    def scope(self):
        if len(self) > 0:
            return self[0]

        raise ScopeNotDefine

    @property
    def resource(self):
        if len(self) > 1:
            return self[1]

        raise ResourceTypeNoeDefine

    @property
    def action(self):
        if self.is_action:
            return self[2]

        raise ResourceActionNotDefine


# action define root
define = ActionDefine()

# scope
biz = define.biz
system = define.system

# resource_type
page = define.biz.page

# action
read = page.read
write = page.write
