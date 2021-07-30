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


from core.drf_resource import resource
from monitor_api.models.base import SnapshotHostIndex
from tests.web.performance import mock_cache


class TestGetFieldValues(object):
    def test_perform_request_ip_list(self, mocker):
        # 含or的查询条件
        params = {
            "index_id": 8,
            "field": "device_name",
            "condition": {
                "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
                "time__gte": "1h",
            },
        }
        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(id=8, result_table_id="system_cpu_detail", item="usage"),
        )

        mock_cache(mocker)

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 8,
                "device": "influxdb",
                "list": [
                    {"max": 96.21109607837872, "time": 1555897269000, "device_name": "cpu0"},
                    {"max": 93.70345294344237, "time": 1555897269000, "device_name": "cpu1"},
                    {"max": 94.98984428200798, "time": 1555897269000, "device_name": "cpu2"},
                    {"max": 96.67796610402095, "time": 1555897269000, "device_name": "cpu3"},
                    {"max": 86.24661246651581, "time": 1555897269000, "device_name": "cpu4"},
                    {"max": 85.77235772430825, "time": 1555897269000, "device_name": "cpu5"},
                    {"max": 89.38471940458933, "time": 1555897269000, "device_name": "cpu6"},
                    {"max": 89.5989123079662, "time": 1555897269000, "device_name": "cpu7"},
                ],
            },
        )

        assert resource.performance.get_field_values_by_index_id(params) == [
            "cpu0",
            "cpu1",
            "cpu2",
            "cpu3",
            "cpu4",
            "cpu5",
            "cpu6",
            "cpu7",
        ]

        sql_query.assert_called_once_with(
            sql=(
                "select max(usage) "
                "from system.cpu_detail  "
                "where time>='1h' "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0'))  "
                "group by device_name  limit 50000"
            )
        )

    def test_perform_request_ip(self, mocker):
        # 不含or的查询条件
        params = {
            "index_id": 87,
            "field": "device_name",
            "condition": {"ip": "1.0.0.1", "bk_cloud_id": 0, "time__gte": "1h"},
        }
        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(id=87, result_table_id="system_io", item="w_s"),
        )

        mock_cache(mocker)

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 3,
                "device": "influxdb",
                "list": [
                    {"max": 0, "time": 1555900454000, "device_name": "sr0"},
                    {"max": 37.617116129136164, "time": 1555902374000, "device_name": "vda"},
                    {"max": 33.48373340869941, "time": 1555902374000, "device_name": "vda1"},
                ],
                "timetaken": 0.00811004638671875,
            },
        )

        assert resource.performance.get_field_values_by_index_id(params) == ["sr0", "vda", "vda1"]

        sql_query.assert_called_once_with(
            sql=(
                "select max(w_s) "
                "from system.io  "
                "where time>='1h' "
                "and ip='1.0.0.1' and bk_cloud_id='0'  "
                "group by device_name  limit 50000"
            )
        )
