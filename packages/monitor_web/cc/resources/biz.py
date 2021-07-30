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
业务相关（业务，人员，角色，权限）
"""


import logging

import six
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from bkmonitor.iam import Permission, ActionEnum
from core.drf_resource.exceptions import CustomException
from bkmonitor.utils.cache import CacheType, using_cache
from bkmonitor.utils.common_utils import to_dict
from bkmonitor.utils.request import get_request
from core.drf_resource import api

logger = logging.getLogger(__name__)


class Business(object):
    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = dict()
        self.__dict__.update(kwargs)

    def _get(self, key):
        return self.__dict__.get(key)

    def __getitem__(self, item):
        return self._get(item)

    @property
    def id(self):
        # 这里id是字符串
        return str(self._get("bk_biz_id"))

    @property
    def name(self):
        return self._get("bk_biz_name")

    @property
    def display_name(self):
        return "[{}] {}".format(self.id, self.name)

    @property
    def operation_planning(self):
        return self._get("OperationPlanning")

    @property
    def company_id(self):
        return self._get("CompanyID")

    @property
    def maintainers(self):
        return self._get("bk_biz_maintainer")

    def select_fields(self, field_list):
        """
        获取字段值
        :param field_list: 查询的字段列表
        """
        result = {}
        for field in field_list:
            result[field] = getattr(self, field, None)
        return result

    def get_user_dict_by_roles(self, role_list, show_detail=False):
        """
        根据角色名称获取用户列表
        """
        user_info = self.select_fields(role_list)
        user_list = []
        for user_list_str in list(user_info.values()):
            if user_list_str:
                for user in user_list_str.split(";"):
                    if user:
                        user_list.append(user)
        user_dict = self.get_nick_by_uin(set(user_list), show_detail)
        return user_dict

    def get_nick_by_uin(self, uin_list=None, show_detail=False, get_all=False):
        """
        根据uin获取用户昵称
        :param uin_list: 用户id列表
        :param show_detail: 是否使用详细昵称
        :param get_all: 是否获取全业务的用户
        """
        if not uin_list:
            uin_list = []

        if isinstance(uin_list, str):
            sep_list = [",", ";"]
            for sep in sep_list:
                if sep in uin_list:
                    uin_list = uin_list.split(sep)
                    break
            else:
                uin_list = [uin_list]
        default_user_dict = {uin: ("{}({})".format(uin, uin) if show_detail else uin) for uin in uin_list}
        user_dict = {}
        userinfo_list = get_owner_info()
        for userinfo in userinfo_list:
            if get_all or str(userinfo["username"]) in uin_list:
                if userinfo["chname"] == "":
                    userinfo["chname"] = userinfo["username"]
                user_dict[str(userinfo["username"])] = (
                    "{}({})".format(userinfo["chname"], userinfo["username"]) if show_detail else userinfo["chname"]
                )
        # 如果查找不到昵称，则仍然输出原Q号
        default_user_dict.update(user_dict)
        return default_user_dict

    @property
    def phone_receiver(self):
        """
        获取业务电话接收人
        混合云版：获取业务所属的开发商人员
        """
        phone_receiver = self.get_nick_by_uin(show_detail=True, get_all=True)
        return phone_receiver


def _init(biz_info):
    return Business(biz_info)


@using_cache(CacheType.BIZ, is_cache_func=lambda res: res)
def _get_application():
    """
    拉取全部业务信息，超级权限
    """
    business_list = api.cmdb.get_business()

    data = [to_dict(biz) for biz in business_list]
    return data


def _get_user(user_or_userobj=None):
    """
    获取用户对象
    """
    if user_or_userobj is None:
        try:
            request = get_request()
            user_or_userobj = request.user
        except Exception:
            logger.exception("get_request failed.")

    user_model = get_user_model()
    if isinstance(user_or_userobj, six.string_types):
        user_or_userobj = user_model.objects.get(username=user_or_userobj)

    assert isinstance(user_or_userobj, user_model), "get_request failed."
    return user_or_userobj


@using_cache(CacheType.BIZ)
def get_owner_info():
    """获取开发商人员信息"""
    return api.bk_login.get_all_user() or []


def get_biz_map(use_cache=True):
    """
    获取所有业务信息
    :return: dict
    """
    if use_cache:
        biz_list = _get_application()
    else:
        biz_list = _get_application.refresh()

    data = {}
    for biz_info in biz_list:
        biz = _init(biz_info)
        data[biz.id] = biz

    return data


@using_cache(CacheType.BIZ)
def get_role_list(username, cc_biz_id):
    """
    获取人员在该业务下的角色
    :return: list
    """
    data = []

    biz_info = get_app_by_id(cc_biz_id)

    for role_name in settings.AUTHORIZED_ROLES:
        if username in getattr(biz_info, role_name, []):
            data.append(role_name)

    return data


def get_app_by_user(user=None, use_cache=True):
    """
    获取用户拥有的业务列表
    :return: list
    """
    user = _get_user(user)
    biz_map = get_biz_map(use_cache)

    # 根据权限中心的【业务访问】权限，对业务列表进行过滤
    perm_client = Permission(user.username)
    business_list = perm_client.filter_business_list_by_action(ActionEnum.VIEW_BUSINESS, list(biz_map.values()))

    return business_list


def get_app_ids_by_user(user=None, use_cache=True):
    """
    获取用户拥有的业务id列表
    :return: list
    """
    biz_list = get_app_by_user(user, use_cache)
    biz_id_list = [biz.id for biz in biz_list]
    return biz_id_list


@using_cache(CacheType.BIZ)
def _get_app_by_id(bk_biz_id):
    """
    调用CC接口获取业务信息
    """
    res = api.cmdb.get_business(bk_biz_ids=[bk_biz_id])
    if not res:
        raise CustomException(_("业务信息获取失败: %s") % bk_biz_id)
    return to_dict(res[0])


def get_app_by_id(bk_biz_id):
    """
    根据业务ID获取App，ID不存在则抛出异常
    :param bk_biz_id: 业务ID
    :rtype: Business
    """
    return _init(_get_app_by_id(bk_biz_id))


def get_company_id(bk_biz_id):
    """
    根据业务ID获取业务的company id
    :param bk_biz_id:
    :return:
    """
    return get_app_by_id(bk_biz_id)["CompanyID"]


@using_cache(CacheType.BIZ)
def get_member_data(bk_biz_id):
    """
    获取人员选择器选项数据
    """
    member_list = []
    user_dict = get_app_by_id(bk_biz_id).get_nick_by_uin(show_detail=False, get_all=True)
    for uid, nick in list(user_dict.items()):
        member_list.append({"english_name": uid, "chinese_name": nick})
    return member_list


@using_cache(CacheType.BIZ)
def get_all_user():
    """
    获取PaaS平台全部用户信息
    """
    member_list = []
    result = api.bk_login.get_all_user()

    if result:
        for user in result:
            member_list.append({"english_name": user["username"], "chinese_name": user["chname"]})
    return member_list
