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
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework_condition import condition

from core.drf_resource.base import Resource


"""
Resource的ViewSet定义
"""


class ResourceViewSet(viewsets.GenericViewSet):
    # 用于执行请求的Resource类
    resource_routes = []

    @classmethod
    def generate_endpoint(cls):
        for resource_route in cls.resource_routes:
            # 生成方法模版
            function = cls._generate_function_template(
                method=resource_route.method,
                resource_class=resource_route.resource_class,
                enable_paginate=resource_route.enable_paginate,
                content_encoding=resource_route.content_encoding,
            )

            # 为Viewset设置方法
            if not resource_route.endpoint:
                # 默认方法无需加装饰器，否则会报错
                if resource_route.method == "GET":
                    cls.list = function
                elif resource_route.method == "POST":
                    cls.create = function
                else:
                    raise AssertionError(_("不支持的请求方法: %s，请确认resource_routes配置是否正确!") % resource_route.method)
            else:
                function = method_decorator(cache_control(max_age=0, private=True))(function)
                function = list_route(methods=[resource_route.method])(function)
                function = condition(
                    etag_func=resource_route.resource_class.etag,
                    last_modified_func=resource_route.resource_class.last_modified,
                )(function)
                setattr(cls, resource_route.endpoint, function)

    @classmethod
    def _generate_function_template(cls, method, resource_class, enable_paginate, content_encoding):
        """
        生成方法模版
        """

        def template(self, request):
            resource = resource_class()
            params = request.query_params if method == "GET" else request.data
            is_async_task = "HTTP_X_ASYNC_TASK" in request.META
            if is_async_task:
                # 执行异步任务
                data = resource.delay(params)
                response = Response(data)
            else:
                data = resource.request(params)
                if enable_paginate:
                    page = self.paginate_queryset(data)
                    response = self.get_paginated_response(page)
                else:
                    response = Response(data)
            if content_encoding:
                response.content_encoding = content_encoding
            return response

        return template


class ResourceRoute(object):
    """
    Resource的视图配置，应用于viewsets
    """

    def __init__(self, method, resource_class, endpoint="", enable_paginate=False, content_encoding=None):
        """
        :param method: 请求方法，目前仅支持GET和POST
        :param resource_class: 所用到的Resource类
        :param endpoint: 端点名称，不提供则为list或create
        :param enable_paginate: 是否对结果进行分页
        :param content_encoding: 返回数据内容编码类型
        """
        if method.upper() not in ["GET", "POST"]:
            raise ValueError(_("method参数错误，目前仅支持GET或POST方法"))

        self.method = method.upper()

        if isinstance(resource_class, Resource):
            resource_class = resource_class.__class__
        if not issubclass(resource_class, Resource):
            raise ValueError(_("resource_class参数必须提供Resource的子类, 当前类型: %s" % resource_class))

        self.resource_class = resource_class

        self.endpoint = endpoint

        self.enable_paginate = enable_paginate

        self.content_encoding = content_encoding
