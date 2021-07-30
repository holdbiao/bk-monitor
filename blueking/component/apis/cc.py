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


class CollectionsCC(object):
    """Collections of CC APIS"""

    def __init__(self, client):
        self.client = client

        self.add_host_lock = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/add_host_lock/", description="新加主机锁"
        )
        self.add_host_to_resource = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/add_host_to_resource/",
            description="新增主机到资源池",
        )
        self.add_instance_association = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/add_instance_association/",
            description="新建模型实例之间的关联关系",
        )
        self.add_label_for_service_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/add_label_for_service_instance/",
            description="为服务实例添加标签",
        )
        self.batch_create_proc_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/batch_create_proc_template/",
            description="批量创建进程模板",
        )
        self.batch_delete_inst = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/batch_delete_inst/",
            description="批量删除实例",
        )
        self.batch_delete_set = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/batch_delete_set/",
            description="批量删除集群",
        )
        self.batch_update_host = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/batch_update_host/",
            description="批量更新主机属性",
        )
        self.batch_update_inst = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/batch_update_inst/",
            description="批量更新对象实例",
        )
        self.bind_role_privilege = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/bind_role_privilege/",
            description="绑定角色权限",
        )
        self.clone_host_property = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/clone_host_property/",
            description="克隆主机属性",
        )
        self.create_business = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/create_business/", description="新建业务"
        )
        self.create_classification = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_classification/",
            description="添加模型分类",
        )
        self.create_cloud_area = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_cloud_area/",
            description="创建云区域",
        )
        self.create_custom_query = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_custom_query/",
            description="添加自定义查询",
        )
        self.create_inst = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/create_inst/", description="创建实例"
        )
        self.create_module = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/create_module/", description="创建模块"
        )
        self.create_object = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/create_object/", description="创建模型"
        )
        self.create_object_attribute = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_object_attribute/",
            description="创建模型属性",
        )
        self.create_process_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_process_instance/",
            description="创建进程实例",
        )
        self.create_service_category = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_service_category/",
            description="新建服务分类",
        )
        self.create_service_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_service_instance/",
            description="创建服务实例",
        )
        self.create_service_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/create_service_template/",
            description="新建服务模板",
        )
        self.create_set = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/create_set/", description="创建集群"
        )
        self.delete_business = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_business/", description="删除业务"
        )
        self.delete_classification = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_classification/",
            description="删除模型分类",
        )
        self.delete_cloud_area = ComponentAPI(
            client=self.client,
            method="DELETE",
            path="/api/c/compapi{bk_api_ver}/cc/delete_cloud_area/",
            description="删除云区域",
        )
        self.delete_custom_query = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_custom_query/",
            description="删除自定义查询",
        )
        self.delete_host = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_host/", description="删除主机"
        )
        self.delete_host_lock = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_host_lock/",
            description="删除主机锁",
        )
        self.delete_inst = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_inst/", description="删除实例"
        )
        self.delete_instance_association = ComponentAPI(
            client=self.client,
            method="DELETE",
            path="/api/c/compapi{bk_api_ver}/cc/delete_instance_association/",
            description="删除模型实例之间的关联关系",
        )
        self.delete_module = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_module/", description="删除模块"
        )
        self.delete_object = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_object/", description="删除模型"
        )
        self.delete_object_attribute = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_object_attribute/",
            description="删除对象模型属性",
        )
        self.delete_proc_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_proc_template/",
            description="删除进程模板",
        )
        self.delete_process_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_process_instance/",
            description="删除进程实例",
        )
        self.delete_service_category = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_service_category/",
            description="删除服务分类",
        )
        self.delete_service_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_service_instance/",
            description="删除服务实例",
        )
        self.delete_service_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/delete_service_template/",
            description="删除服务模板",
        )
        self.delete_set = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/delete_set/", description="删除集群"
        )
        self.find_host_by_module = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/find_host_by_module/",
            description="根据模块查询主机",
        )
        self.find_host_topo_relation = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/find_host_topo_relation/",
            description="获取主机与拓扑的关系",
        )
        self.find_instance_association = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/find_instance_association/",
            description="查询模型实例之间的关联关系",
        )
        self.find_object_association = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/find_object_association/",
            description="查询模型之间的关联关系",
        )
        self.get_biz_internal_module = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_biz_internal_module/",
            description="查询业务的空闲机和故障机模块",
        )
        self.get_custom_query_data = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_custom_query_data/",
            description="根据自定义查询获取数据",
        )
        self.get_custom_query_detail = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_custom_query_detail/",
            description="获取自定义查询详情",
        )
        self.get_host_base_info = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_host_base_info/",
            description="获取主机详情",
        )
        self.get_mainline_object_topo = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_mainline_object_topo/",
            description="查询主线模型的业务拓扑",
        )
        self.get_operation_log = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/get_operation_log/",
            description="获取操作日志",
        )
        self.get_proc_template = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_proc_template/",
            description="获取进程模板",
        )
        self.get_role_privilege = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_role_privilege/",
            description="获取角色绑定权限",
        )
        self.get_service_template = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/get_service_template/",
            description="获取服务模板",
        )
        self.host_install_bk = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/host_install_bk/",
            description="更新主机的云区域字段",
        )
        self.list_biz_hosts = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_biz_hosts/",
            description="查询业务下的主机",
        )
        self.list_biz_hosts_topo = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_biz_hosts_topo/",
            description="查询业务下的主机和拓扑信息",
        )
        self.list_hosts_without_biz = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_hosts_without_biz/",
            description="没有业务ID的主机查询",
        )
        self.list_proc_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_proc_template/",
            description="查询进程模板列表",
        )
        self.list_process_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_process_instance/",
            description="查询进程实例列表",
        )
        self.list_service_category = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_service_category/",
            description="查询服务分类列表",
        )
        self.list_service_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_service_instance/",
            description="查询服务实例列表",
        )
        self.list_service_instance_by_host = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_service_instance_by_host/",
            description="通过主机查询关联的服务实例列表",
        )
        self.list_service_instance_detail = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_service_instance_detail/",
            description="获取服务实例详细信息",
        )
        self.list_service_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/list_service_template/",
            description="服务模板列表查询",
        )
        self.remove_label_from_service_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/remove_label_from_service_instance/",
            description="从服务实例移除标签",
        )
        self.search_biz_inst_topo = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/cc/search_biz_inst_topo/",
            description="查询业务实例拓扑",
        )
        self.search_business = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_business/", description="查询业务"
        )
        self.search_classifications = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_classifications/",
            description="查询模型分类",
        )
        self.search_cloud_area = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_cloud_area/",
            description="查询云区域",
        )
        self.search_custom_query = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_custom_query/",
            description="查询自定义查询",
        )
        self.search_host = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_host/", description="根据条件查询主机"
        )
        self.search_host_lock = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_host_lock/",
            description="查询主机锁",
        )
        self.search_hostidentifier = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_hostidentifier/",
            description="根据条件查询主机身份",
        )
        self.search_inst = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_inst/", description="查询实例"
        )
        self.search_inst_association_topo = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_inst_association_topo/",
            description="查询实例关联拓扑",
        )
        self.search_inst_asst_object_inst_base_info = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_inst_asst_object_inst_base_info/",
            description="查询实例关联模型实例基本信息",
        )
        self.search_inst_by_object = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_inst_by_object/",
            description="查询实例详情",
        )
        self.search_module = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_module/", description="查询模块"
        )
        self.search_object_attribute = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_object_attribute/",
            description="查询对象模型属性",
        )
        self.search_object_topo = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_object_topo/",
            description="查询普通模型拓扑",
        )
        self.search_object_topo_graphics = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_object_topo_graphics/",
            description="查询拓扑图",
        )
        self.search_objects = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_objects/", description="查询模型"
        )
        self.search_set = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/search_set/", description="查询集群"
        )
        self.search_subscription = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/search_subscription/",
            description="查询订阅",
        )
        self.subscribe_event = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/subscribe_event/", description="订阅事件"
        )
        self.testing_connection = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/testing_connection/",
            description="测试推送（只测试连通性）",
        )
        self.transfer_host_module = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_host_module/",
            description="业务内主机转移模块",
        )
        self.transfer_host_to_faultmodule = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_host_to_faultmodule/",
            description="上交主机到业务的故障机模块",
        )
        self.transfer_host_to_idlemodule = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_host_to_idlemodule/",
            description="上交主机到业务的空闲机模块",
        )
        self.transfer_host_to_resourcemodule = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_host_to_resourcemodule/",
            description="上交主机至资源池",
        )
        self.transfer_resourcehost_to_idlemodule = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_resourcehost_to_idlemodule/",
            description="资源池主机分配至业务的空闲机模块",
        )
        self.transfer_sethost_to_idle_module = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/transfer_sethost_to_idle_module/",
            description="清空业务下集群/模块中主机",
        )
        self.unsubcribe_event = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/unsubcribe_event/",
            description="退订事件",
        )
        self.update_business = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_business/", description="修改业务"
        )
        self.update_business_enable_status = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_business_enable_status/",
            description="修改业务启用状态",
        )
        self.update_classification = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_classification/",
            description="更新模型分类",
        )
        self.update_cloud_area = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_cloud_area/",
            description="更新云区域",
        )
        self.update_custom_query = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_custom_query/",
            description="更新自定义查询",
        )
        self.update_event_subscribe = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_event_subscribe/",
            description="修改订阅",
        )
        self.update_host = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_host/", description="更新主机属性"
        )
        self.update_host_cloud_area_field = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_host_cloud_area_field/",
            description="更新主机的云区域字段",
        )
        self.update_inst = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_inst/", description="更新对象实例"
        )
        self.update_module = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_module/", description="更新模块"
        )
        self.update_object = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_object/", description="更新定义"
        )
        self.update_object_attribute = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_object_attribute/",
            description="更新对象模型属性",
        )
        self.update_object_topo_graphics = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_object_topo_graphics/",
            description="更新拓扑图",
        )
        self.update_proc_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_proc_template/",
            description="更新进程模板",
        )
        self.update_process_instance = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_process_instance/",
            description="更新进程实例",
        )
        self.update_service_category = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_service_category/",
            description="更新服务分类",
        )
        self.update_service_template = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/cc/update_service_template/",
            description="更新服务模板",
        )
        self.update_set = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/cc/update_set/", description="更新集群"
        )
