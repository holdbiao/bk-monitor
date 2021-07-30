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

from ..define import BaseNode, Host


class TestDefine:
    def test_base(self):
        foo = BaseNode({"a": 1, "b": 2})
        assert foo.a == foo["a"] == foo._extra_attr["a"] == 1
        assert foo.b == foo["b"] == foo._extra_attr["b"] == 2

        foo.a = 4
        foo.c = 3
        foo["d"] = 5
        assert foo.a == foo["a"] == foo._extra_attr["a"] == 4
        assert foo.b == foo["b"] == foo._extra_attr["b"] == 2
        assert foo.c == foo["c"] == 3
        assert foo.d == foo["d"] == 5

    def test_host(self):
        host = Host(
            {
                "bk_biz_id": 2,
                "bk_isp_name": "2",
                "bk_os_name": "ubuntu",
                "bk_host_id": 1,
                "bk_cloud_id": 0,
                "operator": ["user1"],
                "bk_bak_operator": ["user2"],
                "bk_os_version": "linux",
                "bk_host_outerip": "",
                "bk_supplier_account": "0",
                "bk_host_name": "loyalty-acglog-backup-HN11NEW",
                "bk_host_innerip": "127.0.0.1",
                "bk_set_ids": [1, 2],
                "bk_module_ids": [1, 2],
                "bk_province_name": "130000",
                "bk_state_name": "DE",
                "bk_state": "测试中",
            }
        )

        assert host.bk_host_innerip == host["bk_host_innerip"] == "127.0.0.1"
        assert host.bk_cloud_id == host["bk_cloud_id"] == 0
        assert host.bk_biz_id == host["bk_biz_id"] == 2

        assert host.ip == "127.0.0.1"
        assert host.bk_isp_name == "联通"
        assert host.bk_province_name == "河北"
        assert host.bk_state_name == "德国"
        assert host.host_id == "127.0.0.1|0"
        assert not host.is_shielding
        assert host.ignore_monitoring
