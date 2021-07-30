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


import abc

import six
from django.conf import settings

from bkmonitor.utils.cache import CacheType
from bkmonitor.utils.user import get_backend_username
from core.drf_resource.contrib.api import APIResource

__all__ = [
    "search_module",
    "search_set",
    "search_cloud_area",
    "get_biz_internal_module",
    "search_biz_inst_topo",
    "get_mainline_object_topo",
    "list_service_instance_detail",
    "search_object_attribute",
    "search_business",
    "list_service_category",
    "list_biz_hosts",
    "list_biz_hosts_topo",
    "find_host_topo_relation",
]


class CMDBBaseResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url = "%s/api/c/compapi/v2/cc/" % settings.BK_PAAS_INNER_HOST
    module_name = "cmdb"

    def full_request_data(self, validated_request_data):
        setattr(self, "bk_username", get_backend_username())
        validated_request_data = super(CMDBBaseResource, self).full_request_data(validated_request_data)
        validated_request_data.update(bk_supplier_account=settings.BK_SUPPLIER_ACCOUNT)
        return validated_request_data


class SearchSet(CMDBBaseResource):
    """
    集群查询接口
    """

    cache_type = CacheType.CC_BACKEND
    action = "search_set"
    method = "POST"


class SearchModule(CMDBBaseResource):
    """
    模块查询接口
    """

    cache_type = CacheType.CC_BACKEND
    action = "search_module"
    method = "POST"


class GetBizInternalModule(CMDBBaseResource):
    """
    查询空闲模块及集群接口
    """

    cache_type = CacheType.CC_CACHE_ALWAYS
    action = "get_biz_internal_module"
    method = "GET"


class SearchBizInstTopo(CMDBBaseResource):
    """
    查询业务拓扑接口
    """

    cache_type = CacheType.CC_CACHE_ALWAYS
    action = "search_biz_inst_topo"
    method = "GET"


class GetMainlineObjectTopo(CMDBBaseResource):
    """
    查询主线模型
    """

    cache_type = CacheType.CC_BACKEND
    action = "get_mainline_object_topo"
    method = "GET"


class ListServiceInstanceDetail(CMDBBaseResource):
    """
    查询服务实例详情
    """

    cache_type = CacheType.CC_CACHE_ALWAYS
    action = "list_service_instance_detail"
    method = "POST"


class SearchObjectAttribute(CMDBBaseResource):
    """
    查询对象属性
    """

    cache_type = CacheType.CC_BACKEND
    action = "search_object_attribute"
    method = "POST"


class SearchBusiness(CMDBBaseResource):
    """
    查询对象属性
    """

    cache_type = CacheType.CC_BACKEND
    action = "search_business"
    method = "POST"


class ListServiceCategory(CMDBBaseResource):
    """
    查询服务分类列表
    """

    cache_type = CacheType.CC_CACHE_ALWAYS
    action = "list_service_category"
    method = "POST"


class ListBizHostsTopo(CMDBBaseResource):
    """
    查询业务主机及关联拓扑
    """

    cache_type = CacheType.CC_BACKEND
    action = "list_biz_hosts_topo"
    method = "POST"


class ListBizHosts(CMDBBaseResource):
    """
    查询业务主机
    """

    action = "list_biz_hosts"
    method = "POST"


class FindHostTopoRelation(CMDBBaseResource):
    """
    查询业务主机
    """

    action = "find_host_topo_relation"
    method = "POST"


class SearchCloudArea(CMDBBaseResource):
    """
    查询云区域
    """

    action = "search_cloud_area"
    method = "POST"


class ListServiceTemplate(CMDBBaseResource):
    """
    查询服务模板列表
    """

    action = "list_service_template"
    method = "POST"


class ListSetTemplate(CMDBBaseResource):
    """
    查询集群模板列表
    """

    action = "list_set_template"
    method = "POST"


class FindHostByServiceTemplate(CMDBBaseResource):
    """
    获取服务模板下的主机
    """

    action = "find_host_by_service_template"
    method = "POST"


class FindHostBySetTemplate(CMDBBaseResource):
    """
    获取集群模板下的主机
    """

    action = "find_host_by_set_template"
    method = "POST"


search_set = SearchSet()
search_module = SearchModule()
list_biz_hosts_topo = ListBizHostsTopo()
list_biz_hosts = ListBizHosts()
find_host_topo_relation = FindHostTopoRelation()
get_biz_internal_module = GetBizInternalModule()
get_mainline_object_topo = GetMainlineObjectTopo()
search_biz_inst_topo = SearchBizInstTopo()
list_service_instance_detail = ListServiceInstanceDetail()
search_object_attribute = SearchObjectAttribute()
search_business = SearchBusiness()
list_service_category = ListServiceCategory()
search_cloud_area = SearchCloudArea()
list_service_template = ListServiceTemplate()
list_set_template = ListSetTemplate()
find_host_by_set_template = FindHostBySetTemplate()
find_host_by_service_template = FindHostByServiceTemplate()
