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


import datetime
import json
import re

import pytz
from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext as _

from bkmonitor.utils.common_utils import fetch_biz_id_from_request
from common.log import logger
from common.xss_tools import check_script, html_escape, html_escape_name, url_escape


class TimeZoneMiddleware(MiddlewareMixin):
    """
    时区处理中间件
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        biz_id = fetch_biz_id_from_request(request, view_kwargs)
        if biz_id:
            try:
                from core.drf_resource import resource

                tz_name = resource.cc.get_app_by_id(biz_id)["TimeZone"]
            except Exception:
                tz_name = settings.TIME_ZONE
            request.session[settings.TIMEZONE_SESSION_KEY] = tz_name

        tz_name = request.session.get(settings.TIMEZONE_SESSION_KEY)
        if tz_name:
            timezone.activate(pytz.timezone(tz_name))
        else:
            timezone.deactivate()


class ActiveBusinessMiddleware(MiddlewareMixin):
    """
    活跃业务中间件（用来记录活跃业务以及业务的最后访问者）
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.biz_id = fetch_biz_id_from_request(request, view_kwargs)
        if request.biz_id:
            try:
                from utils import business

                business.activate(int(request.biz_id), request.user.username)
            except Exception as e:
                logger.error(_("活跃业务激活失败, biz_id:%(biz_id)s, error:%(error)s") % {"biz_id": request.biz_id, "error": e})


class RecordLoginUserMiddleware(MiddlewareMixin):
    """
    记录用户访问时间中间件
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user:
            return
        try:
            user.last_login = datetime.datetime.now()
            user.save()
        except Exception:
            pass


class CheckXssMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super(CheckXssMiddleware, self).__init__(*args, **kwargs)
        self.__escape_param_list = []

    def process_view(self, request, view, args, kwargs):
        try:
            # 判断豁免权
            if getattr(view, "escape_exempt", False):
                return None

            # 豁免GET方法
            if request.method == "GET":
                return None

            # 获取豁免参数名
            self.__escape_param_list = (
                getattr(view, "escape_exempt_param", []) if getattr(view, "escape_exempt_param", False) else []
            )

            escapeType = None
            if getattr(view, "escape_script", False):
                escapeType = "script"
            elif getattr(view, "escape_url", False):
                escapeType = "url"
            # get参数转换
            request.GET = self.__escape_data(request.path, request.GET, escapeType)
            # post参数转换
            request.POST = self.__escape_data(request.path, request.POST, escapeType)
        except Exception as e:
            logger.error(_("CheckXssMiddleware 转换失败！%s") % e)
        return None

    def __escape_data(self, path, query_dict, escape_type=None):
        """
        GET/POST参数转义
        """
        data_copy = query_dict.copy()
        for _get_key, _get_value_list in data_copy.lists():
            new_value_list = []
            for _get_value in _get_value_list:
                new_value = _get_value
                # json串不进行转义
                try:
                    json.loads(_get_value)
                    is_json = True
                except Exception:
                    is_json = False
                # 转义新数据
                if not is_json:
                    try:
                        if escape_type is None:
                            use_type = self.__filter_param(path, _get_key)
                        else:
                            use_type = escape_type

                        if use_type == "url":
                            new_value = url_escape(_get_value)
                        elif use_type == "script":
                            new_value = check_script(_get_value, 1)
                        elif use_type == "name":
                            new_value = html_escape_name(_get_value)
                        elif _get_key in self.__escape_param_list:
                            new_value = _get_value
                        else:
                            new_value = html_escape(_get_value, 1)
                    except Exception as e:
                        logger.error(_("CheckXssMiddleware GET/POST参数 转换失败！%s") % e)
                        new_value = _get_value
                else:
                    try:
                        new_value = html_escape(_get_value, 1, True)
                    except Exception as e:
                        logger.error(_("CheckXssMiddleware GET/POST参数 转换失败！%s") % e)
                        new_value = _get_value
                new_value_list.append(new_value)
            data_copy.setlist(_get_key, new_value_list)
        return data_copy

    def __filter_param(self, path, param):
        """
        特殊path处理
        @param path: 路径
        @param param: 参数
        @return: 'html/name/url/script/exempt'
        """
        use_name, use_url, use_script = self.__filter_path_list()
        try:
            result = "html"
            # name过滤
            for name_path, name_v in list(use_name.items()):
                is_path = re.match(r"^%s" % name_path, path)
                if is_path and param in name_v:
                    result = "name"
                    break
            # url过滤
            if result == "html":
                for url_path, url_v in list(use_url.items()):
                    is_path = re.match(r"^%s" % url_path, path)
                    if is_path and param in url_v:
                        result = "url"
                        break
            # script过滤
            if result == "html":
                for script_path, script_v in list(use_script.items()):
                    is_path = re.match(r"^%s" % script_path, path)
                    if is_path and param in script_v:
                        result = "script"
                        break
        except Exception as e:
            logger.error(_("CheckXssMiddleware 特殊path处理失败！%s") % e)
            result = "html"
        return result

    def __filter_path_list(self):
        """
        特殊path注册
        """
        use_name = {}
        use_url = {
            "%saccounts/login" % settings.SITE_URL: ["next"],
            "%saccounts/login_page" % settings.SITE_URL: ["req_url"],
            "%saccounts/login_success" % settings.SITE_URL: ["req_url"],
            "%s" % settings.SITE_URL: ["url"],
        }
        use_script = {}
        return (use_name, use_url, use_script)
