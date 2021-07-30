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

from django.conf import settings
from django.utils.translation import ugettext as _

from typing import Union, List

from api.cmdb.define import Business
from bkmonitor.iam import ResourceEnum
from core.drf_resource import api
from core.errors.api import BKAPIError
from core.errors.iam import PermissionDeniedError, ActionNotExistError
from bkmonitor.iam.action import ActionMeta, get_action_by_id, _all_actions
from bkmonitor.iam.resource import _all_resources, Business as BusinessResource, get_resource_by_id
from bkmonitor.utils.request import get_request
from iam import IAM, Request, Subject, Resource, make_expression, ObjectSet, MultiActionRequest
from iam.apply.models import (
    ActionWithoutResources,
    Application,
    ActionWithResources,
    RelatedResourceType,
    ResourceInstance,
    ResourceNode,
)
from iam.exceptions import AuthAPIError
from iam.meta import setup_system, setup_resource, setup_action
from iam.utils import gen_perms_apply_data

logger = logging.getLogger(__name__)


class Permission(object):
    """
    权限中心鉴权封装
    """

    def __init__(self, username: str = "", request=None):
        if username:
            self.username = username
            self.bk_token = ""
        else:
            request = request or get_request(peaceful=True)
            if not request:
                raise ValueError("must provide `username` or `request` param to init")

            self.bk_token = request.COOKIES.get("bk_token", "")
            self.username = request.user.username

        app_info = (settings.APP_CODE, settings.SECRET_KEY)
        if settings.ROLE == "api":
            # 后台api模式下使用SaaS身份
            app_info = (settings.SAAS_APP_CODE, settings.SAAS_SECRET_KEY)

        self.iam_client = IAM(*app_info, settings.BK_IAM_INNER_HOST, settings.BK_PAAS_INNER_HOST)

        # 是否跳过权限中心校验
        self.skip_check = getattr(settings, "SKIP_IAM_PERMISSION_CHECK", False)

    def make_request(self, action: Union[ActionMeta, str], resources: List[Resource] = None) -> Request:
        """
        获取请求对象
        """
        action = get_action_by_id(action)
        resources = resources or []
        request = Request(
            system=settings.BK_IAM_SYSTEM_ID,
            subject=Subject("user", self.username),
            action=action,
            resources=resources,
            environment=None,
        )
        return request

    def make_multi_action_request(
        self, actions: List[Union[ActionMeta, str]], resources: List[Resource] = None
    ) -> MultiActionRequest:
        """
        获取多个动作请求对象
        """
        resources = resources or []
        actions = [get_action_by_id(action) for action in actions]
        request = MultiActionRequest(
            system=settings.BK_IAM_SYSTEM_ID,
            subject=Subject("user", self.username),
            actions=actions,
            resources=resources,
            environment=None,
        )
        return request

    def _make_application(
        self, action_ids: List[str], resources: List[Resource] = None, system_id: str = settings.BK_IAM_SYSTEM_ID
    ) -> Application:

        resources = resources or []
        actions = []

        for action_id in action_ids:
            # 对于没有关联资源的动作，则不传资源
            related_resources_types = []
            try:
                action = get_action_by_id(action_id)
                action_id = action.id
                related_resources_types = action.related_resource_types
            except ActionNotExistError:
                pass

            if not related_resources_types:
                actions.append(ActionWithoutResources(action_id))
            else:
                related_resources = []
                for related_resource in related_resources_types:
                    instances = []
                    for r in resources:
                        if r.system == related_resource["system_id"] and r.type == related_resource["id"]:
                            instances.append(
                                ResourceInstance(
                                    [ResourceNode(type=r.type, id=r.id, name=r.attribute.get("name", r.id))]
                                )
                            )

                    related_resources.append(
                        RelatedResourceType(
                            system_id=related_resource["system_id"],
                            type=related_resource["id"],
                            instances=instances,
                        )
                    )

                actions.append(ActionWithResources(action_id, related_resources))

        application = Application(system_id, actions=actions)
        return application

    def get_apply_url(
        self, action_ids: List[str], resources: List[Resource] = None, system_id: str = settings.BK_IAM_SYSTEM_ID
    ):
        """
        处理无权限 - 跳转申请列表
        """
        application = self._make_application(action_ids, resources, system_id)
        ok, message, url = self.iam_client.get_apply_url(application, self.bk_token, self.username)
        if not ok:
            logger.error("iam generate apply url fail: %s", message)
            return settings.BK_IAM_SAAS_HOST
        return url

    def get_apply_data(self, actions: List[Union[ActionMeta, str]], resources: List[Resource] = None):
        """
        生成本系统无权限数据
        """

        # # 获取关联的动作，如果没有权限就一同显示
        # related_actions = fetch_related_actions(actions)
        # request = self.make_multi_action_request(list(related_actions.values()), resources)
        # related_actions_result = self.iam_client.resource_multi_actions_allowed(request)
        #
        # for action_id, is_allowed in related_actions_result.items():
        #     if not is_allowed and action_id in related_actions:
        #         actions.append(related_actions[action_id])

        resources = resources or []

        action_to_resources_list = []
        for action in actions:
            action = get_action_by_id(action)

            if not action.related_resource_types:
                # 如果没有关联资源，则直接置空
                resources = []

            action_to_resources_list.append({"action": action, "resources_list": [resources]})

        self.setup_meta()

        data = gen_perms_apply_data(
            system=settings.BK_IAM_SYSTEM_ID,
            subject=Subject("user", self.username),
            action_to_resources_list=action_to_resources_list,
        )

        url = self.get_apply_url(actions, resources)
        return data, url

    @staticmethod
    def is_demo_biz_resource(resources: List[Resource] = None):
        """
        判断资源是否为demo业务的资源
        """
        if not settings.DEMO_BIZ_ID:
            return False
        if not resources:
            return False
        if not len(resources) == 1:
            return False
        if (resources[0].system, resources[0].type, str(resources[0].id)) == (
            BusinessResource.system_id,
            BusinessResource.id,
            str(settings.DEMO_BIZ_ID),
        ):
            # 业务类型资源判断资源ID
            return True
        if resources[0].attribute and resources[0].attribute.get("_bk_iam_path_", "").startswith(
            f"/biz,{settings.DEMO_BIZ_ID}/"
        ):
            # 其他类型资源，判断路径
            return True
        return False

    def is_allowed(
        self, action: Union[ActionMeta, str], resources: List[Resource] = None, raise_exception: bool = False
    ):
        """
        校验用户是否有动作的权限
        :param action: 动作
        :param resources: 依赖的资源实例列表
        :param raise_exception: 鉴权失败时是否需要抛出异常
        """
        if self.skip_check:
            return True

        resources = resources or []

        action = get_action_by_id(action)
        if not action.related_resource_types:
            resources = []

        # ===== 针对demo业务的权限豁免 开始 ===== #
        if self.is_demo_biz_resource(resources):
            # 如果是demo业务，则进行权限豁免，分为读写权限
            if settings.DEMO_BIZ_WRITE_PERMISSION or action.is_read_action():
                # 鉴权通过，直接返回。如果不通过，就走权限中心鉴权
                return True
        # ===== 针对demo业务的权限豁免 结束 ===== #

        request = self.make_request(action, resources)

        try:
            if action.is_read_action():
                # 仅对读权限做缓存
                result = self.iam_client.is_allowed_with_cache(request)
            else:
                result = self.iam_client.is_allowed(request)
        except AuthAPIError as e:
            logger.exception("[IAM AuthAPI Error]: %s", e)
            result = False

        if not result and raise_exception:

            # 对资源信息(如资源名称)进行补全
            detail_resources = []
            for resource in resources:
                resource_mata = get_resource_by_id(resource.type)
                detail_resources.append(resource_mata.create_instance(resource.id))
            apply_data, apply_url = self.get_apply_data([action], detail_resources)

            raise PermissionDeniedError(
                context={"action_name": action.name},
                data={"apply_url": apply_url},
                extra={"permission": apply_data},
            )

        return result

    def is_allowed_by_biz(self, bk_biz_id: int, action: Union[ActionMeta, str], raise_exception: bool = False):
        """
        判断用户对当前动作在该业务下是否有权限
        """
        if self.skip_check:
            return True

        resources = [ResourceEnum.BUSINESS.create_simple_instance(bk_biz_id)]
        return self.is_allowed(action, resources, raise_exception)

    def list_actions(self):
        """
        获取权限中心注册的动作列表
        """
        ok, message, data = self.iam_client._client.query(settings.BK_IAM_SYSTEM_ID)
        if not ok:
            raise BKAPIError(
                system_name=settings.BK_IAM_APP_CODE,
                url="/api/v1/model/systems/{system_id}/query".format(system_id=settings.BK_IAM_SYSTEM_ID),
                result={"message": message},
            )
        return data["actions"]

    def filter_business_list_by_action(
        self, action: Union[ActionMeta, str], business_list: List[Business] = None
    ) -> List[Business]:
        """
        根据动作过滤用户有权限的业务列表
        """

        if business_list is None:
            # 获取业务列表
            business_list = api.cmdb.get_business()

        # 对后台API进行权限豁免
        if self.skip_check:
            return business_list

        # 拉取策略
        request = self.make_request(action=action)

        try:
            policies = self.iam_client._do_policy_query(request)
        except AuthAPIError as e:
            logger.exception("[IAM AuthAPI Error]: %s", e)
            return []

        if not policies:
            # 如果策略是空，则说明没有任何权限，若存在Demo业务，返回Demo业务，否则返回空
            for business in business_list:
                if int(settings.DEMO_BIZ_ID) == business.bk_biz_id:
                    return [business]
            return []

        # 生成表达式
        expr = make_expression(policies)

        results = []
        for business in business_list:
            obj_set = ObjectSet()
            obj_set.add_object(ResourceEnum.BUSINESS.id, {"id": str(business.bk_biz_id)})

            # 计算表达式
            is_allowed = self.iam_client._eval_expr(expr, obj_set)

            # 如果是demo业务，也直接加到业务列表中
            if is_allowed or int(settings.DEMO_BIZ_ID) == business.bk_biz_id:
                results.append(business)

        return results

    @classmethod
    def setup_meta(cls):
        """
        初始化权限中心实体
        """
        if getattr(cls, "__setup", False):
            return

        # 系统
        systems = [
            {"system_id": settings.BK_IAM_SYSTEM_ID, "system_name": settings.BK_IAM_SYSTEM_NAME},
            {"system_id": "bk_cmdb", "system_name": _("配置平台")},
        ]

        for system in systems:
            setup_system(**system)

        # 资源
        for r in _all_resources.values():
            setup_resource(r.system_id, r.id, r.name)

        # 动作
        for action in _all_actions.values():
            setup_action(system_id=settings.BK_IAM_SYSTEM_ID, action_id=action.id, action_name=action.name)

        cls.__setup = True
