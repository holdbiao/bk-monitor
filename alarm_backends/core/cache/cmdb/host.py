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


from alarm_backends.core.cache.cmdb.base import CMDBCacheManager, RefreshByBizMixin
from api.cmdb.define import Host, TopoTree
from bkmonitor.utils.common_utils import host_key
from core.drf_resource import api
from bkmonitor.utils.local import local


setattr(local, "host_cache", {})


class HostIDManager(RefreshByBizMixin, CMDBCacheManager):
    """
    CMDB 主机缓存
    """

    CACHE_KEY = "{prefix}.cmdb.host_id".format(prefix=CMDBCacheManager.CACHE_KEY_PREFIX)

    @classmethod
    def serialize(cls, obj):
        """
        序列化数据
        """
        return obj

    @classmethod
    def deserialize(cls, string):
        """
        反序列化数据
        """
        return string

    @classmethod
    def key_to_internal_value(cls, bk_host_id):
        return "{}".format(bk_host_id)

    @classmethod
    def get(cls, bk_host_id):
        """
        :rtype: str
        """
        return super(HostIDManager, cls).get(bk_host_id)

    @classmethod
    def refresh_by_biz(cls, bk_biz_id):
        hosts = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id)  # type: list[Host]
        return {cls.key_to_internal_value(host.bk_host_id): "{}|{}".format(host.ip, host.bk_cloud_id) for host in hosts}


class HostManager(RefreshByBizMixin, CMDBCacheManager):
    """
    CMDB 主机缓存
    """

    CACHE_KEY = "{prefix}.cmdb.host".format(prefix=CMDBCacheManager.CACHE_KEY_PREFIX)

    @classmethod
    def key_to_internal_value(cls, ip, bk_cloud_id=0):
        return "{}|{}".format(ip, bk_cloud_id)

    @classmethod
    def get(cls, ip, bk_cloud_id=0, using_mem=False):
        """
        :rtype: Host
        """
        if not using_mem:
            return super(HostManager, cls).get(ip, bk_cloud_id)
        # 如果使用本地内存，那么在逻辑结束后，需要调用clear_mem_cache函数清理
        host_id = host_key(ip=ip, bk_cloud_id=bk_cloud_id)
        host = local.host_cache.get(host_id, None)
        if host is None:
            host = cls.get(ip, bk_cloud_id)
            if host is not None:
                local.host_cache[host_id] = host
        return host

    @classmethod
    def refresh_by_biz(cls, bk_biz_id):
        hosts = api.cmdb.get_host_by_topo_node(bk_biz_id=bk_biz_id)  # type: list[Host]
        topo_tree = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)  # type: TopoTree
        # 填充拓扑链
        topo_link_dict = topo_tree.convert_to_topo_link()
        for host in hosts:
            host.topo_link = {}
            for module_id in host.bk_module_ids:
                key = "module|{}".format(module_id)
                host.topo_link[key] = topo_link_dict.get(key, [])
        return {cls.key_to_internal_value(host.ip, host.bk_cloud_id): host for host in hosts}


def main():
    HostIDManager.refresh()
    HostManager.refresh()
