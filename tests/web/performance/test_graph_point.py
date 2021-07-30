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
from monitor_api.models import SnapshotHostIndex
from tests.web.performance import mock_cache


class TestGraphPoint(object):
    def test_perform_request_ori(self, mocker):
        # 设为原始请求数据
        params = {
            "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
            "index_id": 8,
            "time_range": "2019-04-10T09:58:16+08:00 -- 2019-04-10T09:59:16+08:00",
            "filter_dict": {"device_name": "cpu1"},
            "group_fields": ["ip", "bk_cloud_id"],
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=8,
                result_table_id="system_cpu_detail",
                item="usage",
                conversion_unit="%",
                conversion=1,
                category="cpu",
                dimension_field="device_name",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 2,
                "device": "influxdb",
                "list": [
                    {
                        "ip": "1.0.0.1",
                        "_value_": 55.458221023905644,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                    {
                        "ip": "1.0.0.2",
                        "_value_": 43.68279569925282,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                ],
                "timetaken": 0.013022899627685547,
            },
        )

        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": 0,
            "timezone": "Asia/Shanghai",
            "series": [
                {"data": [[1554861480000, None], [1554861540000, 55.46]], "name": "1.0.0.1 | 0"},
                {"data": [[1554861480000, None], [1554861540000, 43.68]], "name": "1.0.0.2 | 0"},
            ],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "%",
            "max_y": 55.46,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(usage) as _value_ from system.cpu_detail  "
                "where time>=1554861496000 "
                "and time<1554861556000 "
                "and device_name='cpu1' "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0'))  "
                "group by ip,bk_cloud_id,minute1  limit 50000"
            )
        )

    def test_perform_request_not_group_field(self, mocker):
        # 测试请求数据无group_fields
        params = {
            "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
            "index_id": 8,
            "time_range": "2019-04-22 20:07:36 -- 2019-04-22 20:08:36",
            "filter_dict": {"device": [{"device_name": "cpu0"}, {"device_name": "cpu1"}]},
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=8,
                result_table_id="system_cpu_detail",
                item="usage",
                conversion_unit="%",
                conversion=1,
                category="cpu",
                dimension_field="device_name",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 4,
                "device": "influxdb",
                "list": [
                    {"_value_": None, "time": 1555934820000, "minute1": 1555934820000, "device_name": "cpu0"},
                    {
                        "_value_": 53.67498314236148,
                        "time": 1555934880000,
                        "minute1": 1555934880000,
                        "device_name": "cpu0",
                    },
                    {"_value_": None, "time": 1555934820000, "minute1": 1555934820000, "device_name": "cpu1"},
                    {
                        "_value_": 53.84097035045981,
                        "time": 1555934880000,
                        "minute1": 1555934880000,
                        "device_name": "cpu1",
                    },
                ],
                "timetaken": 0.013022899627685547,
            },
        )

        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": None,
            "timezone": "Asia/Shanghai",
            "series": [
                {"data": [[1555934820000, None], [1555934880000, 53.67]], "name": "cpu0"},
                {"data": [[1555934820000, None], [1555934880000, 53.84]], "name": "cpu1"},
            ],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "%",
            "max_y": 53.84,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(usage) as _value_ "
                "from system.cpu_detail  "
                "where time>=1555934856000 and time<1555934916000 "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0')) "
                "and ((device_name='cpu0') or (device_name='cpu1'))  group by minute1,device_name  limit 50000"
            )
        )

    def test_perform_request_dimension_field(self, mocker):
        # 测试增加参数dimension_field
        params = {
            "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
            "index_id": 8,
            "time_range": "2019-04-10T09:58:16+08:00 -- 2019-04-10T09:59:16+08:00",
            "dimension_field": "device_name",
            "dimension_field_value": "cpu1",
            "group_fields": ["ip", "bk_cloud_id"],
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=8,
                result_table_id="system_cpu_detail",
                item="usage",
                conversion_unit="%",
                conversion=1,
                category="cpu",
                dimension_field="device_name",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 2,
                "device": "influxdb",
                "list": [
                    {
                        "ip": "1.0.0.1",
                        "_value_": 55.458221023905644,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                    {
                        "ip": "1.0.0.2",
                        "_value_": 43.68279569925282,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                ],
                "timetaken": 0.013022899627685547,
            },
        )

        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": 0,
            "timezone": "Asia/Shanghai",
            "series": [
                {"data": [[1554861480000, None], [1554861540000, 55.46]], "name": "1.0.0.1 | 0"},
                {"data": [[1554861480000, None], [1554861540000, 43.68]], "name": "1.0.0.2 | 0"},
            ],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "%",
            "max_y": 55.46,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(usage) as _value_ from system.cpu_detail  "
                "where time>=1554861496000 "
                "and time<1554861556000 "
                "and device_name='cpu1' "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0'))  "
                "group by ip,bk_cloud_id,minute1  limit 50000"
            )
        )

    def test_perform_request_process(self, mocker):
        # 测试指标类别为process
        params = {
            "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
            "index_id": 122,
            "time_range": "2019-04-10T09:58:16+08:00 -- 2019-04-10T09:59:16+08:00",
            "filter_dict": {"device_name": "cpu1"},
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=122,
                result_table_id="system_proc",
                item="cpu_usage_pct",
                conversion_unit="%",
                conversion=0.01,
                category="process",
                dimension_field="display_name,pid",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 2,
                "device": "influxdb",
                "list": [
                    {
                        "ip": "1.0.0.1",
                        "_value_": 0.554582210239056,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                    {
                        "ip": "1.0.0.2",
                        "_value_": 0.436827956992528,
                        "bk_cloud_id": "0",
                        "minute1": 1554861540000,
                        "time": 1554861540000,
                    },
                ],
                "timetaken": 0.013022899627685547,
            },
        )

        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": 0,
            "timezone": "Asia/Shanghai",
            "series": [{"data": [[1554861480000, None], [1554861540000, 43.68]], "name": "总览"}],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "%",
            "max_y": 55.46,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(cpu_usage_pct) as _value_ from system.proc  "
                "where time>=1554861496000 "
                "and time<1554861556000 "
                "and device_name='cpu1' "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0'))  "
                "group by minute1  limit 50000"
            )
        )

    def test_perform_request_net(self, mocker):
        # 测试net类型指标
        params = {
            "ip_list": [{"ip": "1.0.0.1", "bk_cloud_id": 0}, {"ip": "1.0.0.2", "bk_cloud_id": 0}],
            "index_id": 10,
            "time_range": "2019-04-22 20:07:36 -- 2019-04-22 20:08:36",
            "group_fields": ["ip", "bk_cloud_id"],
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=10,
                result_table_id="system_net",
                item="speedRecv",
                conversion_unit="KB/s",
                conversion=1024,
                category="net",
                dimension_field="device_name",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 2,
                "device": "influxdb",
                "list": [
                    {
                        "ip": "1.0.0.1",
                        "_value_": 538335,
                        "bk_cloud_id": "0",
                        "minute1": 1555934880000,
                        "time": 1555934880000,
                    },
                    {
                        "ip": "1.0.0.2",
                        "_value_": 640817,
                        "bk_cloud_id": "0",
                        "minute1": 1555934880000,
                        "time": 1555934880000,
                    },
                ],
                "timetaken": 0.02236199378967285,
            },
        )

        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": 0,
            "timezone": "Asia/Shanghai",
            "series": [
                {"data": [[1555934820000, None], [1555934880000, 525.72]], "name": "1.0.0.1 | 0"},
                {"data": [[1555934820000, None], [1555934880000, 625.8]], "name": "1.0.0.2 | 0"},
            ],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "KB/s",
            "max_y": 625.8,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(speedRecv) as _value_ "
                "from system.net  "
                "where time>=1555934856000 and time<1555934916000 "
                "and ip!='lo' and bk_cloud_id!='lo' "
                "and ((ip='1.0.0.1' and bk_cloud_id='0') or (ip='1.0.0.2' and bk_cloud_id='0'))  "
                "group by ip,bk_cloud_id,minute1  limit 50000"
            )
        )

    def test_perform_request_disk(self, mocker):
        params = {
            "ip_list": [{"ip": "10.0.1.11", "bk_cloud_id": 0}, {"ip": "10.0.1.10", "bk_cloud_id": 0}],
            "index_id": 81,
            "time_range": "2019-04-24 09:11:20 -- 2019-04-24 09:12:20",
            "group_fields": ["ip", "bk_cloud_id"],
        }

        mock_cache(mocker)

        mocker.patch(
            "monitor_api.models.base.SnapshotHostIndex.objects.get",
            return_value=SnapshotHostIndex(
                id=81,
                result_table_id="system_disk",
                item="in_use",
                conversion_unit="%",
                conversion=1,
                category="disk",
                dimension_field="mount_point",
            ),
        )

        sql_query = mocker.patch(
            "packages.utils.dataview_tools.api.metadata.get_ts_data",
            return_value={
                "totalRecords": 2,
                "device": "influxdb",
                "list": [
                    {
                        "ip": "10.0.1.10",
                        "_value_": 45.808290053106575,
                        "bk_cloud_id": "0",
                        "minute1": 1556068320000,
                        "time": 1556068320000,
                    },
                    {
                        "ip": "10.0.1.11",
                        "_value_": 86.63744686943498,
                        "bk_cloud_id": "0",
                        "minute1": 1556068320000,
                        "time": 1556068320000,
                    },
                ],
                "timetaken": 0.017972946166992188,
            },
        )

        get_key_alias = mocker.patch(
            "monitor_web.commons.data.resources.api.metadata.get_result_table",
            return_value={
                "field_list": [
                    {"field_name": "ip", "description": "采集器IP"},
                    {"field_name": "bk_cloud_id", "description": "采集器云区域ID"},
                ]
            },
        )
        result = resource.performance.graph_point.request(params)["data"]
        # 去掉无法校验的时间间隔参数
        result.pop("duration")
        assert result == {
            "utcoffset": 28800.0,
            "chart_type": "spline",
            "min_y": 0,
            "timezone": "Asia/Shanghai",
            "series": [
                {"data": [[1556068260000, None], [1556068320000, 45.81]], "name": "10.0.1.10 | 0"},
                {"data": [[1556068260000, None], [1556068320000, 86.64]], "name": "10.0.1.11 | 0"},
            ],
            "x_axis": {"minRange": 3600000, "type": "datetime"},
            "pointInterval": 300000,
            "unit": "%",
            "max_y": 86.64,
        }

        sql_query.assert_called_once_with(
            sql=(
                "select  MAX(in_use) as _value_ "
                "from system.disk  "
                "where time>=1556068280000 and time<1556068340000 "
                "and ip not like '%dev\\\\/loop%' and ip not like '%dev\\\\/sr%' and ip not like '%.iso' "
                "and bk_cloud_id not like '%dev\\\\/loop%' and bk_cloud_id not like '%dev\\\\/sr%' "
                "and bk_cloud_id not like '%.iso' "
                "and ((ip='10.0.1.11' and bk_cloud_id='0') or (ip='10.0.1.10' and bk_cloud_id='0'))  "
                "group by ip,bk_cloud_id,minute1  limit 50000"
            )
        )

        get_key_alias.assert_called_with(table_id="system.disk")
