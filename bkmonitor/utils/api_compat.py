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
import importlib
import json
import os
import re
from copy import copy

import six
import six.moves.urllib.parse
from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from rest_framework.test import APIRequestFactory

from bkmonitor.utils.common_utils import underscore_to_camel
from bkmonitor.utils.request import get_request

####################
# Global Constants #
####################

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_FILE_PATH = os.path.join(BASE_DIR, "api_resource.json")
# RESOURCE_FILE_ENCODING = 'utf-8'

with open(RESOURCE_FILE_PATH) as f:
    content = f.read()
    content = content[content.index("[") : content.rindex("]") + 1]

# RESOURCES = json.loads(content, encoding=RESOURCE_FILE_ENCODING)
RESOURCES = json.loads(content)

####################
# Global Variables #
####################

dispatch_dict_cache = None
factory = APIRequestFactory()

#############
# Functions #
#############


def get_re_obj(path):
    path = path.replace("{id}", r"(?P<pk>\d+)")

    if path.endswith("/"):
        suffix = "?"
    else:
        suffix = ""

    regex = r"^/(test|prod){}{}$".format(path, suffix)
    return re.compile(regex, re.IGNORECASE)


def get_callable(method, path, dest_url):
    dest_path = dest_url[45:]
    splits = [x for x in dest_path.split("/") if x]

    viewset_name = "%sViewSet" % underscore_to_camel(splits[0])
    views = importlib.import_module("monitor_api.views")
    viewset = getattr(views, viewset_name)

    callable_ = None
    if len(splits) == 1:
        if method == "get":
            callable_ = viewset.as_view({method: "list"})
        elif method == "post":
            callable_ = viewset.as_view({method: "create"})
    elif len(splits) == 2 and splits[1] == "{id}":
        if method == "get":
            callable_ = viewset.as_view({method: "retrieve"})
        elif method == "post" and "delete" in path:
            callable_ = viewset.as_view({method: "destroy"})
        elif method == "post":
            callable_ = viewset.as_view({method: "partial_update"})
    elif len(splits) == 2:
        callable_ = viewset.as_view({method: splits[1]})

    return callable_


def get_dispatch_dict(method):
    global dispatch_dict_cache

    if not dispatch_dict_cache:
        dispatch_dict_cache = {}
        for item in RESOURCES:
            _method = item["dest_http_method"].lower()
            if _method not in ("get", "post"):
                continue

            _method_cache = dispatch_dict_cache.setdefault(_method, {})

            re_obj = get_re_obj(item["path"])
            callable_ = get_callable(_method, item["path"], item["dest_url"])
            if callable_:
                _method_cache[re_obj] = callable_

    return dispatch_dict_cache[method]


def dispatch(method, path):
    if not getattr(settings, "DISABLE_API_COMPAT", False):
        dispath_dict = get_dispatch_dict(method)

        for re_obj, callable_ in six.iteritems(dispath_dict):
            match_obj = re_obj.match(path)
            if match_obj and method in callable_.actions:
                return match_obj, callable_

    return None, None


def get_username():
    try:
        http_request = get_request()
    except Exception:
        username = settings.APP_CODE
    else:
        username = getattr(getattr(http_request, "user", None), "username", None)

    if not username:
        username = settings.APP_CODE

    return username


def format_response(response):
    formated_data = None

    if 200 <= response.status_code < 300:
        if isinstance(response.data, dict):
            if "data" in response.data:
                formated_data = response.data
            elif "results" in response.data:
                origin_data = copy(response.data)
                data = origin_data.pop("results")
                meta = origin_data
                formated_data = {
                    "data": data,
                    "_meta": meta,
                }

        if formated_data is None:
            formated_data = {
                "data": response.data,
            }

        formated_data.update(
            {
                "result": True,
                "code": response.status_code,
                "message": response.status_text,
            }
        )
    else:
        formated_data = {
            "result": False,
            "data": None,
            "code": response.status_code,
            "message": response.status_text,
        }

    return formated_data


def compat_request(func):
    @functools.wraps(func)
    def wrapper(url, **kwargs):
        kwargs.update(
            {
                "username": get_username(),
            }
        )
        if func.__name__ == "requests_get":
            method = "get"
            request = factory.get(url, data=kwargs)
        elif func.__name__ == "requests_post":
            method = "post"
            request = factory.post(
                url,
                data=json.dumps(kwargs),
                content_type="application/json",
            )
        else:
            return func(url, **kwargs)

        url_parts = six.moves.urllib.parse.urlparse(url)
        match_obj, callable_ = dispatch(method, url_parts.path)
        if match_obj and callable_:
            response = callable_(request, **match_obj.groupdict())
            return format_response(response)
        else:
            return func(url, **kwargs)

    return wrapper


def compat_viewset(url_name, data=None, **kwargs):
    basename, methodname = url_name.split("-", 1)
    origin_method = methodname

    if methodname in ("list", "create"):
        methodname = "list"
    elif methodname in ("retrieve", "update", "partial_update", "destroy"):
        methodname = "detail"

    path = reverse("monitor_api:{}-{}".format(basename, methodname.replace("_", "-")), kwargs=kwargs)

    if path.startswith(settings.SITE_URL):
        prefix_len = len(settings.SITE_URL) - 1
        path = path[prefix_len:] if prefix_len > 0 else path
    match_obj = resolve(path)

    for http_method, viewset_method in six.iteritems(match_obj.func.actions):
        if origin_method == viewset_method:
            break
    else:
        msg = "origin method: %r does not match any of available actions: " "%r" % (
            origin_method,
            match_obj.func.actions,
        )
        raise Exception(msg)

    if http_method.lower() == "get":
        request = factory.get(path, data=data)
    else:
        request = getattr(factory, http_method.lower())(
            path,
            data=json.dumps(data),
            content_type="application/json",
        )

    try:
        response = match_obj.func(request, **match_obj.kwargs)
        return json.loads(response.rendered_content)
        # return format_response(response)
    except Exception as e:
        return {
            "result": False,
            "code": 500,
            "data": None,
            "message": str(e),
        }
