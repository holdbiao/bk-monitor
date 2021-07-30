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
import pytest

from bkmonitor.utils import consul
from metadata import models
from metadata.utils import consul_tools
from django.core.management import call_command
import time

pytestmark = pytest.mark.django_db
IS_CONSUL_MOCK = False
es_index = {}


class TestOperateConsulConfig(object):
    def test_redirect_consul_config(self, mocker):
        # 该测试只做实际场景测试
        if IS_CONSUL_MOCK:
            return
        data_name = "test_name_{}".format(time.time())
        etl_config = "bk_standard"
        operator = "admin"
        data_source_label = "bk_monitor"
        data_type_label = "time_series"
        hash_consul = consul_tools.HashConsul()
        consul_client = consul.BKConsul(
            host=hash_consul.host, port=hash_consul.port, scheme=hash_consul.scheme, verify=hash_consul.verify
        )
        # 新建一个datasource
        new_data_source = models.DataSource.create_data_source(
            data_name=data_name,
            etl_config=etl_config,
            operator=operator,
            source_label=data_source_label,
            type_label=data_type_label,
        )
        # 检查consul数据，确认配置成功处理
        result = consul_client.kv.get(new_data_source.consul_config_path)
        assert result[1] is not None
        # 手动传入redirect命令，将配置重定向到新路径下
        call_command("redirect_datasource", data_id=[new_data_source.bk_data_id], target_type="temp")
        # 检查旧路径consul数据
        result = consul_client.kv.get(new_data_source.consul_config_path)
        assert result[1] is None
        # 更新model实例
        new_data_source = models.DataSource.objects.get(pk=new_data_source.bk_data_id)
        # 检查新路径consul数据
        result = consul_client.kv.get(new_data_source.consul_config_path)
        assert result[1] is not None
        # 手动删除新路径下的consul数据
        consul_client.kv.delete(new_data_source.consul_config_path)
        result = consul_client.kv.get(new_data_source.consul_config_path)
        assert result[1] is None
        # 调用clean命令
        call_command("clean_consul_datasource")
        # 检查新路径下数据是否恢复
        result = consul_client.kv.get(new_data_source.consul_config_path)
        assert result[1] is not None
