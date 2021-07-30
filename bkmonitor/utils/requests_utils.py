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


import logging
import json

import requests
from django.conf import settings
from django.utils.translation import ugettext as _
from six.moves.urllib.parse import urlencode

from bkmonitor.utils.api_compat import compat_request
from bkmonitor.utils.request import get_common_headers, get_request
from bkmonitor.utils.user import make_userinfo

logger = logging.getLogger(__name__)


# 接口调用的公共参数
INTERFACE_COMMON_PARAMS = {
    "bk_app_code": settings.APP_CODE,
    "bk_app_secret": settings.SECRET_KEY,
}

# 超时
TIMEOUT_SETTING = {
    "timeout": 60,
}


class RequestsResultException(Exception):
    """
    对应返回状态非200，或者返回结果为False的异常
    """

    pass


def custom_requests(method, url, data=None, headers=None, **kwargs):
    """
    对request的封装
        1、添加公共参数到请求头
        2、请求失败统一处理
    @param data: dict
    :return:
    """
    # 公共参数处理
    if headers is None:
        headers = {}
    headers.update(get_common_headers())
    headers["content-type"] = "application/json"
    if data is None:
        data = {}
    request = get_request()
    data.update(INTERFACE_COMMON_PARAMS)
    kwargs.update(TIMEOUT_SETTING)
    kwargs.update({"username": request.user.username})
    try:
        res = requests.request(method, url, data=json.dumps(data), headers=headers, verify=False, **kwargs)
    except requests.exceptions.Timeout as e:
        logger.exception(_("接口请求超时: %s") % e)
        raise requests.exceptions.Timeout(_("接口请求网络超时"))
    except Exception as e:
        logger.exception(_("接口请求异常: %s") % e)
        raise RequestsResultException(_("接口请求异常"))
    # 请求失败，打log
    if res.status_code != 200:
        logger.warning(
            "Request exception. {method} {url}: {content}".format(method=method, url=url, content=res.content[:500])
        )
        raise RequestsResultException(_("调用接口异常，返回：%s") % res.status_code)
    res = json.loads(res.content)
    if not res["result"]:
        logger.warning(
            "Request exception. {method} {url}: {content}".format(method=method, url=url, content=res["message"])
        )
        raise RequestsResultException(_("调用接口异常：%s") % res["message"])
    return res


@compat_request
def requests_get(url, **kwargs):
    """
    requests get方法封装
    :return:
    """
    kwargs.update(INTERFACE_COMMON_PARAMS)
    kwargs.update(make_userinfo())
    headers = get_common_headers()
    url = "{}?{}".format(url, urlencode(kwargs))
    try:
        # logger.info('requests get start: %s' % url)
        res = requests.get(url, headers=headers, verify=False, **TIMEOUT_SETTING)
        # logger.info('requests get finish: %s' % url)
    except Exception as e:
        logger.exception(_("接口请求网络异常: %s") % e)
        if settings.DEBUG:
            raise e
        return {"message": _("接口请求网络异常"), "result": False, "data": None}
    res = res.json()
    if not res["result"]:
        logger.warning(
            "Request exception. {method} {url}: {content}".format(method="get", url=url, content=res["message"])
        )
    return res


@compat_request
def requests_post(url, **kwargs):
    kwargs.update(INTERFACE_COMMON_PARAMS)
    kwargs.update(make_userinfo())
    headers = get_common_headers()
    headers.update({"Content-Type": "application/json"})
    try:
        res = requests.post(url, json=kwargs, headers=headers, verify=False, **TIMEOUT_SETTING)
        # res = requests.post(url, data=kwargs, **TIMEOUT_SETTING)
    except Exception as e:
        logger.exception(_("接口请求网络异常: %s") % e)
        if settings.DEBUG:
            raise e
        return {"message": _("接口请求网络异常"), "result": False, "data": None}
    res = res.json()
    return res


def requests_delete(url, **kwargs):
    kwargs.update(INTERFACE_COMMON_PARAMS)
    kwargs.update(make_userinfo())
    headers = get_common_headers()
    try:
        res = requests.delete(url, params=kwargs, headers=headers, **TIMEOUT_SETTING)
    except Exception as e:
        logger.exception(_("接口请求网络异常: %s") % e)
        if settings.DEBUG:
            raise e
        return {"message": _("接口请求网络异常"), "result": False, "data": None}
    res = res.json()
    res["result"] = res.get("result", res.get("code") == "00")
    return res
