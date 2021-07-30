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


from ..base import ComponentAPI


class CollectionsUSERMANAGE(object):
    """Collections of USERMANAGE APIS"""

    def __init__(self, client):
        self.client = client

        self.department_ancestor = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/department_ancestor/",
            description="查询部门全部祖先",
        )
        self.list_department_profiles = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/list_department_profiles/",
            description="查询部门的用户信息 (v2)",
        )
        self.list_departments = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/list_departments/",
            description="查询部门 (v2)",
        )
        self.list_profile_departments = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/list_profile_departments/",
            description="查询用户的部门信息 (v2)",
        )
        self.list_users = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/list_users/",
            description="查询用户 (v2)",
        )
        self.retrieve_department = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/retrieve_department/",
            description="查询单个部门信息 (v2)",
        )
        self.retrieve_user = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/usermanage/retrieve_user/",
            description="查询单个用户信息 (v2)",
        )
