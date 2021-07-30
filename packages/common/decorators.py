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
装饰器
1.权限pad装饰器，permission_required(已经写好装饰器，可自行定义验证逻辑)
"""
import time

from django.http import HttpResponse
from django.utils.decorators import available_attrs
from django.shortcuts import redirect
from django.conf import settings

from common.log import logger

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.


# ===============================================================================
# 转义装饰器
# ===============================================================================
def escape_exempt(view_func):
    """
    转义豁免，被此装饰器修饰的action可以不进行中间件escape
    """

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.escape_exempt = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


def escape_script(view_func):
    """
    被此装饰器修饰的action会对GET与POST参数进行javascript escape
    """

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.escape_script = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


def escape_url(view_func):
    """
    被此装饰器修饰的action会对GET与POST参数进行url escape
    """

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.escape_url = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


def escape_exempt_param(*param_list, **param_list_dict):
    """
    此装饰器用来豁免某个view函数的某个参数
    @param param_list: 参数列表
    @return:
    """

    def _escape_exempt_param(view_func):
        def wrapped_view(*args, **kwargs):
            return view_func(*args, **kwargs)

        if param_list_dict.get("param_list"):
            wrapped_view.escape_exempt_param = param_list_dict["param_list"]
        else:
            wrapped_view.escape_exempt_param = list(param_list)
        return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)

    return _escape_exempt_param


def _response_for_failure(request, _result, message, is_ajax):
    """
    内部通用方法: 请求敏感权限出错时的处理(1和2)
    @param _result: 结果标志位
    @param message: 结果信息
    @param is_ajax: 是否是ajax请求
    """
    if _result == 1:
        # 登陆失败，需要重新登录,跳转至登录页
        if is_ajax:
            return HttpResponse(status=402)
        return redirect(message)
    elif _result == 2:
        # error(包括exception)
        return _redirect_403(request)


def _redirect_403(request):
    """
    转到403权限不足的提示页面
    """
    url = settings.SITE_URL + "accounts/check_failed/?code=403"
    if request.is_ajax():
        resp = HttpResponse(status=403, content=url)
        return resp
    return redirect(url)


def record_slow_query(func):
    """
    记录慢查询
    """

    def wrapper(sql):
        start = time.time()
        ret = func(sql)
        duration = time.time() - start
        if duration > 2:
            logger.warning("slow query[duration: {:.3f}]: {}".format(duration, sql))
        return ret

    return wrapper
