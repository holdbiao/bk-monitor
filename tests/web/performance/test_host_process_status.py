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
#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from core.drf_resource.exceptions import CustomException
from core.drf_resource import resource
from tests.web.performance import mock_cache, mock_cc


class TestProcessStatus(object):
    def test_process_status(self, mocker):
        mock_cache(mocker)
        mock_cc(mocker)
        assert resource.performance.host_process_status.request(ip="10.0.5.84", bk_cloud_id=0) == [
            {"display_name": "consul-agent", "ports": [8301, 8500, 53], "protocol": "TCP", "status": 0},
            {"display_name": "nginx-paas-http", "ports": [80], "protocol": "TCP", "status": -1},
        ]

    def test_process_status_no_host(self, mocker):
        mock_cache(mocker)
        mock_cc(mocker)
        with pytest.raises(CustomException):
            resource.performance.host_performance_detail.request(ip="10.0.5.83", bk_cloud_id=0)
