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


import mock

RegisteredAPI = {}

DefaultMocker = {}

DefaultMockRule = {
    "cmdb": "api.cmdb.client",
    "job": "core.drf_resource.api.job",
    "cmsi": "core.drf_resource.api.cmsi",
    "gse": "core.drf_resource.api.gse",
    "bk_login": "core.drf_resource.api.bk_login",
    "metadata": "core.drf_resource.api.metadata",
}


def register(func):
    """
    注册
    :param func: 函数对象
    :type func: function
    :return: function
    """
    module_path = register.__module__[: -len(".register")]
    func_path = "{}.{}".format(func.__module__, func.__name__)
    if func.__module__.startswith(module_path):
        RegisteredAPI[func_path[len("{}.".format(module_path)) :]] = func
    return func


def start():
    """
    执行 mock
    """
    for source, target in list(DefaultMockRule.items()):
        api_paths = [x for x in list(RegisteredAPI.keys()) if x.startswith("{}.".format(source))]
        for api_path in api_paths:
            func = RegisteredAPI[api_path]
            DefaultMocker[api_path] = mock.patch("{}.{}".format(target, func.__name__), side_effect=func)
            DefaultMocker[api_path].start()


def stop():
    """
    停止mock
    """
    api_paths = list(DefaultMocker.keys())
    for api_path in api_paths:
        try:
            DefaultMocker[api_path].stop()
        except RuntimeError:
            pass
        del DefaultMocker[api_path]


def set_result(api, result):
    """
    设置返回值
    :param api: api名称
    :param result: 返回值
    """
    pass
