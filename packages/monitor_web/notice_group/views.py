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
from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from core.drf_resource import resource


class NoticeGroupViewSet(IAMPermissionMixin, ResourceViewSet):
    """
    获取全部通知对象
    """

    iam_read_actions = ActionEnum.VIEW_NOTIFY_TEAM
    iam_write_actions = ActionEnum.MANAGE_NOTIFY_TEAM

    def get_iam_actions(self):
        if self.action == "get_notice_way":
            return []
        if self.action == "get_receiver":
            return []
        return super(NoticeGroupViewSet, self).get_iam_actions()

    resource_routes = [
        # 获取全部通知对象
        ResourceRoute("GET", resource.notice_group.get_receiver, endpoint="get_receiver"),
        # 获取全部通知方式
        ResourceRoute("GET", resource.notice_group.get_notice_way, endpoint="get_notice_way"),
        # 创建\修改通知组
        ResourceRoute("POST", resource.notice_group.notice_group_config, endpoint="notice_group_config"),
        # 删除通知组
        ResourceRoute("POST", resource.notice_group.delete_notice_group, endpoint="delete_notice_group"),
        # 获取通知组列表
        ResourceRoute("GET", resource.notice_group.notice_group_list, endpoint="notice_group_list"),
        # 获取通知组详情
        ResourceRoute("GET", resource.notice_group.notice_group_detail, endpoint="notice_group_detail"),
    ]
