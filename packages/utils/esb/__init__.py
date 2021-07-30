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


import abc
from collections import defaultdict

import six
from blueapps.utils.esbclient import CustomComponentAPI, client, get_client_by_user
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import APIException

from core.drf_resource.base import Resource
from bkmonitor.utils.common_utils import camel_to_underscore
from common.log import logger


class EsbAPIException(APIException):
    default_detail = "An ESB API exception occurred."
    default_code = "esb_api_exception"


class EsbResource(six.with_metaclass(abc.ABCMeta, Resource)):
    """
    ESB类型的Resource
    """

    system = None
    method = None

    def __init__(self, **kwargs):
        super(EsbResource, self).__init__(**kwargs)
        if settings.RUN_MODE == "DEVELOP":
            user_model = get_user_model()
            last_login_user = user_model.objects.all().order_by("-last_login")[0]
            self.client = get_client_by_user(last_login_user.username)
        else:
            self.client = client

        component_api = getattr(getattr(self.client, self.system), self.method)

        if isinstance(component_api, CustomComponentAPI):
            raise AttributeError("ESB API '{}/{}' does not exist!".format(self.system, self.method))

        self.component_api = component_api

    def perform_request(self, validated_request_data):
        """
        发起http请求
        """

        result_json = self.component_api(validated_request_data)

        if not result_json["result"]:
            msg = result_json.get("message", "")
            logger.exception(msg)
            raise EsbAPIException(msg)

        return result_json["data"]


class EsbResourceManager(object):
    def __init__(self):
        self.registry = defaultdict(dict)

    def register(self, system, method, resource_cls):
        """
        注册单个esb resource
        :param system: 系统名称，如cc, jobs
        :param method: 方法名称，如get_application, get_host_info
        :param resource_cls: EsbResource的子类
        """

        self.registry[system][method] = resource_cls

    def register_module(self, system, module):
        for attr, resource_cls in six.iteritems(module.__dict__):
            # 全小写的属性不是类，忽略
            if attr[0].islower():
                continue
            if isinstance(resource_cls, type) and issubclass(resource_cls, EsbResource):
                method = camel_to_underscore(resource_cls.get_resource_name())
                self.register(system, method, resource_cls)

    def search_resource(self, system, method, *args):
        if method in self.registry[system]:
            resource_cls = self.registry[system][method]
            resource_cls.system = system
            resource_cls.method = method
        else:
            resource_cls = type("DummyResource", (EsbResource,), {"system": system, "method": method})
        return resource_cls()


class EsbResourceDispatcher(object):
    def __init__(self, name="", parent=None):
        self.name = name
        self.parent = parent

    def __getattr__(self, name):
        path = self.get_path()
        if len(path) == 1:
            system, method = path[0], name
            return esb_resource_manager.search_resource(system, method)
        return self.__class__(name, self)

    def get_path(self):
        path = []
        current = self
        while True:
            if current.parent is None:
                break
            else:
                path.append(current.name)
                current = current.parent

        path.reverse()
        return path


esb_resource_manager = EsbResourceManager()

esb = EsbResourceDispatcher()
