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
from functools import reduce

# coding: utf-8


def getitems(obj, items, default=None):
    if isinstance(items, str):
        items = (items,)

    try:
        return reduce(lambda x, i: x[i], items, obj)
    except (IndexError, KeyError, TypeError):
        return default


def dict_merge(dicts):
    """
    Merge dict list to a dict object
    :param dicts: dict list
    :return: dict
    """
    result = {}

    for d in dicts:
        for k, v in list(d.items()):
            if k not in result:
                result[k] = v

    return result
