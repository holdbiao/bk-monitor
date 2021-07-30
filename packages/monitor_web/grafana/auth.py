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
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

import six
from django.conf import settings
from django.utils.translation import ugettext as _
from rest_framework import authentication

from core.drf_resource import api
from core.errors.dashboard import (
    CreateOrganizationError,
    CreateUserError,
    GetOrganizationError,
    GetOrganizationUserError,
    GetUserError,
)

logger = logging.getLogger(__name__)

Organizations = {}
Users = {}


class GrafanaAuthSync(object):
    """
    Grafana权限同步
    """

    @classmethod
    def sync(cls, username, bk_biz_id):
        """
        权限同步
        :param username: 用户名
        :param bk_biz_id: 业务ID
        """
        user_id = cls.get_or_create_user_id(username)

        if bk_biz_id:
            org_id = cls.get_or_create_org_id(bk_biz_id)

            user_ids = cls.get_user_id_in_org(org_id)
            if user_id not in user_ids:
                cls.add_user_in_org(org_id, username)
                cls.create_default_user_folder(org_id, user_id, username)

            return org_id

    @staticmethod
    def get_or_create_user_id(username):
        """
        根据用户名获取grafana的用户ID，没有则创建
        :param username: 用户名
        :type username: str or unicode
        :return: 用户ID
        :rtype: int
        """
        if username in Users:
            return Users[username]

        user = api.grafana.get_user_by_login_or_email(loginOrEmail=username)

        if user["result"]:
            user_id = user["data"]["id"]
        elif user["code"] == 404:
            user = api.grafana.create_user(name=username, login=username)
            if user["result"]:
                user_id = user["data"]["id"]
            else:
                raise CreateUserError(**user)
        else:
            raise GetUserError(**user)

        Users[username] = user_id
        return user_id

    @classmethod
    def get_or_create_org_id(cls, bk_biz_id):
        """
        根据业务ID获取grafana的组织ID，没有则创建
        :param bk_biz_id: 业务ID
        :type bk_biz_id: int
        :return: 组织ID
        :rtype: int
        """
        if bk_biz_id in Organizations:
            return Organizations[bk_biz_id]

        org = api.grafana.get_organization_by_name(name=six.text_type(bk_biz_id))
        if org["result"]:
            org_id = org["data"]["id"]
        elif org["code"] == 404:
            org = api.grafana.create_organization(name=six.text_type(bk_biz_id))
            if org["result"]:
                org_id = org["data"]["orgId"]
                cls.create_default_data_source(org_id)
                cls.create_default_dashboard(org_id)
            else:
                raise CreateOrganizationError(**org)
        else:
            raise GetOrganizationError(**org)

        Organizations[bk_biz_id] = org_id
        return org_id

    @staticmethod
    def get_user_id_in_org(org_id):
        """
        获取组织中的全部用户ID
        :param org_id: 组织ID
        :type org_id: int
        :return: {1: "Admin"}
        """
        result = api.grafana.get_all_user_in_organization(org_id=org_id)
        if result["result"]:
            return {user["userId"]: user["role"] for user in result["data"]}
        raise GetOrganizationUserError(**result)

    @staticmethod
    def add_user_in_org(org_id, username):
        """
        在组织中添加用户
        :param org_id: 组织ID
        :type org_id: int
        :param username: 用户名
        :type username: str
        """
        api.grafana.add_user_in_organization(org_id=org_id, loginOrEmail=username, role="Editor")

    @staticmethod
    def create_default_data_source(org_id):
        """
        创建监控数据源
        :param org_id: 组织ID
        :type org_id: int
        """
        api.grafana.create_data_source(
            org_id=org_id,
            name=_("蓝鲸监控 - 指标数据"),
            type="bkmonitor-timeseries-datasource",
            isDefault=True,
            jsonData={"baseUrl": "/{}rest/v2/grafana/".format(settings.SITE_URL)},
        )

    @staticmethod
    def create_default_dashboard(org_id):
        """
        创建仪表盘，并且设置为组织默认仪表盘
        :param org_id: 组织ID
        :type org_id: int
        """
        try:
            with open("packages/monitor_web/grafana/default_dashboard.json", encoding="utf-8") as f:
                dashboard_config = json.loads(f.read())

            result = api.grafana.create_dashboard(dashboard=dashboard_config, org_id=org_id)

            if not result["result"] and result["data"]["status"] == "success":
                return

            api.grafana.update_organization_preference(org_id=org_id, homeDashboardId=result["data"]["id"])
        except Exception as e:
            logger.exception(e)
            logger.error(_("组织({})创建默认仪表盘失败").format(org_id))

    @staticmethod
    def create_default_user_folder(org_id, user_id, username):
        """
        创建用户文件夹
        :param org_id: 组织ID
        :param user_id: 用户ID
        """
        result = api.grafana.create_folder(org_id=org_id, title=f"{username} " + _("私人仪表盘"))

        uid = result["data"]["uid"]

        api.grafana.update_folder_permission(uid=uid, org_id=org_id, items=[{"userId": user_id, "permission": 4}])


class GrafanaTokenAuthentication(authentication.BaseAuthentication):
    """
    Grafana Token权限校验
    """

    def authenticate(self, request):
        return None, None
