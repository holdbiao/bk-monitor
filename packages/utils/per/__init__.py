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
from utils.per.define import define


def get_all_action_define():

    actions = set()
    tasks = [define]

    while tasks:
        task = tasks.pop()
        if task.is_action:
            actions.add(task)
        else:
            tasks += _get_children(task)

    return actions


def get_all_resource():
    pass


def _get_children(parent):
    children = set()

    for k, v in list(parent.__dict__.items()):
        if k.startswith("_"):
            continue

        if getattr(v, "parent", None) is parent and isinstance(v, define.__class__):
            children.add(v)

    return children
