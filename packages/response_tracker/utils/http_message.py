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
response_tracker.utils.http_message
===================================
"""
import re
from collections import OrderedDict

from django.template import Context
from django.template.loader import get_template

re_http_header = re.compile(r"^HTTP(_[A-Z]+)+$")


def format_header(name):
    """
    >>> format_header('HTTP_USER_AGENT')
    >> 'User-Agent'
    """
    return "-".join([x.capitalize() for x in name.split("_")[1:]])


def build_request_headers(request):
    headers = []
    to_be_sorted = []

    for k, v in request.META.items():
        if re_http_header.match(k):
            name = format_header(k)
            if name == "Host":
                headers.append((name, v))
            else:
                to_be_sorted.append((name, v))

    headers.extend(sorted(to_be_sorted))

    return OrderedDict(headers)


def render_request_message(request):
    tmpl = get_template("response_tracker/request.tmpl")
    context = Context(
        {
            "request": request,
            "headers": build_request_headers(request),
        }
    )
    return tmpl.render(context)


def render_response_message(response):
    tmpl = get_template("response_tracker/response.tmpl")
    context = Context(
        {
            "response": response,
            "headers": OrderedDict(sorted(response.items())),
        }
    )
    return tmpl.render(context)
