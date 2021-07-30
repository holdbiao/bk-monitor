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
from core.drf_resource.viewsets import ResourceViewSet
from core.drf_resource.viewsets import ResourceRoute
from core.drf_resource import resource


class BusinessListOptionViewSet(ResourceViewSet):
    """
    拉去业务列表（select2）
    """

    resource_routes = [
        ResourceRoute("GET", resource.commons.business_list_option),
    ]


class FetchBusinessInfoViewSet(ResourceViewSet):
    """
    拉取业务的详细信息(业务名字, 运维, 权限申请url(权限中心), Demo业务链接)
    """

    # 去除鉴权
    permission_classes = ()
    resource_routes = [
        ResourceRoute("GET", resource.commons.fetch_business_info),
    ]
