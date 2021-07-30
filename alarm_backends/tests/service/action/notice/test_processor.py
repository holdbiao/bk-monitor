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


from datetime import datetime

import arrow
import pytest
import pytz

from alarm_backends.service.action.notice.processor import NoticeProcessor
from api.cmdb.define import Host, Module
from bkmonitor.models import AnomalyRecord, Event, EventAction

strategy = {
    "bk_biz_id": 2,
    "is_enabled": True,
    "update_time": 1570072047,
    "update_user": "admin",
    "name": "CPU\u603b\u4f7f\u7528\u7387",
    "scenario": "os",
    "item_list": [
        {
            "rt_query_config": {
                "agg_method": "AVG",
                "agg_dimension": ["bk_target_ip", "bk_target_cloud_id"],
                "unit_conversion": 1.0,
                "agg_condition": [],
                "agg_interval": 60,
                "extend_fields": "",
                "metric_field": "usage",
                "result_table_id": "system.cpu_summary",
                "unit": "%",
            },
            "metric_id": "system.cpu_summary.usage",
            "name": "usage",
            "algorithm_list": [
                {
                    "algorithm_config": [{"threshold": 90, "method": "gte"}],
                    "level": 1,
                    "trigger_config": {"count": 3, "check_window": 5},
                    "algorithm_type": "Threshold",
                    "recovery_config": {"check_window": 5},
                    "algorithm_id": 6,
                    "id": 6,
                }
            ],
            "item_id": 6,
            "data_source_label": "bk_monitor",
            "id": 6,
            "no_data_config": {"is_enabled": False, "continuous": 5},
            "item_name": "usage",
            "data_type_label": "time_series",
        }
    ],
    "strategy_id": 6,
    "strategy_name": "CPU\u603b\u4f7f\u7528\u7387",
    "action_list": [
        {
            "notice_template": {"anomaly_template": "", "recovery_template": ""},
            "notice_group_list": [
                {
                    "notice_way": {"1": ["sms"], "3": ["weixin"], "2": ["mail"]},
                    "notice_receiver": ["group#bk_biz_maintainer", "user#layman"],
                    "id": 3,
                    "name": "\u84dd\u9cb8\u8fd0\u7ef4\u7ec4",
                }
            ],
            "action_type": "notice",
            "config": {
                "alarm_end_time": "23:59:59",
                "send_recovery_alarm": False,
                "alarm_start_time": "00:00:00",
                "alarm_interval": 120,
            },
            "wxwork_group": {"1": "12345,254678"},
            "id": 6,
            "action_id": 6,
        }
    ],
    "create_user": "admin",
    "source_type": "BKMONITOR",
    "create_time": 1570072047,
    "id": 6,
    "target": [
        [{"field": "ip", "method": "eq", "value": [{"ip": "127.0.0.1", "bk_cloud_id": 0, "bk_supplier_id": 0}]}]
    ],
}

origin_alarm = {
    "anomaly": {
        "1": {
            "anomaly_message": "\\u5f53\\u524d\\u6307\\u6807\\u503c(77.88%) >=(1.0%)",
            "anomaly_time": "2019-10-05 14:11:05",
            "anomaly_id": "11dd36c4e45b40da6a8f436a01c781cc.1570284540.6.6.1",
        }
    },
    "trigger": {
        "anomaly_ids": [
            "11dd36c4e45b40da6a8f436a01c781cc.1570284300.6.6.1",
            "11dd36c4e45b40da6a8f436a01c781cc.1570284360.6.6.1",
            "11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        ],
        "level": "1",
    },
    "data": {
        "record_id": "11dd36c4e45b40da6a8f436a01c781cc.1570284540",
        "values": {"usage": 77.88, "time": 1570284540},
        "dimensions": {
            "bk_target_ip": "10.0.1.11",
            "bk_target_cloud_id": "0",
            "bk_topo_node": [
                "set|3",
                "module|21",
                "set|5",
                "module|19",
                "module|16",
                "module|17",
                "module|28",
                "test|2",
                "module|13",
                "module|10",
                "module|5",
                "module|12",
                "biz|2",
                "module|9",
                "set|6",
            ],
        },
        "value": 77.88,
        "time": 1570284540,
    },
    "dimension_translation": {
        "bk_target_ip": {"display_value": "10.0.1.11", "display_name": "内网IP地址"},
        "bk_topo_node": {
            "display_name": "bk_topo_node",
            "display_value": [
                {"bk_obj_name": "模块", "bk_inst_name": "gameserver"},
                {"bk_obj_name": "集群", "bk_inst_name": "paas"},
            ],
        },
    },
    "strategy_snapshot_key": "bk_monitor.ee[development].cache.strategy.snapshot.6.1570072047",
}

host = Host(
    bk_host_innerip="10.0.1.11",
    bk_cloud_id=0,
    bk_cloud_name="default area",
    bk_host_id=1,
    bk_biz_id=2,
    operator=["admin"],
    bk_bak_operator=["admin1"],
    bk_module_ids=[1],
    bk_set_ids=[1],
)


module = Module(
    **{
        "bk_biz_id": 2,
        "bk_module_type": "1",
        "bk_module_id": 1,
        "service_category_id": 10,
        "default": 1,
        "bk_childid": None,
        "bk_bak_operator": [],
        "create_time": "2019-05-17T12:38:29.545+08:00",
        "bk_module_name": "idle machine",
        "bk_set_id": 1,
        "bk_supplier_account": "0",
        "operator": [],
        "service_template_id": 0,
        "bk_parent_id": 1,
        "last_time": "2019-05-17T12:38:29.545+08:00",
    }
)


pytestmark = pytest.mark.django_db


@pytest.fixture()
def setup(mock):
    Event.objects.all().delete()
    EventAction.objects.all().delete()
    AnomalyRecord.objects.all().delete()

    mock.patch(
        "alarm_backends.service.action.notice.processor.get_business_roles",
        lambda *args, **kwargs: {
            "bk_biz_maintainer": ["user2"],
            "bk_biz_productor": [],
            "bk_biz_developer": [],
            "bk_biz_tester": [],
        },
    )

    Event.objects.create(
        event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        begin_time=arrow.now().datetime,
        bk_biz_id=2,
        strategy_id=6,
        origin_alarm=origin_alarm,
        origin_config=strategy,
        level=1,
        status=Event.EventStatus.ABNORMAL,
    )

    AnomalyRecord.objects.create(
        anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284300.6.6.1",
        event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=6,
    )
    AnomalyRecord.objects.create(
        anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284360.6.6.1",
        event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=6,
    )
    AnomalyRecord.objects.create(
        anomaly_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
        origin_alarm=origin_alarm,
        source_time=arrow.now().datetime,
        strategy_id=6,
    )

    yield EventAction.objects.create(
        operate=EventAction.Operate.ANOMALY_NOTICE,
        extend_info={
            "action": {
                "notice_template": {"anomaly_template": "", "recovery_template": ""},
                "notice_group_list": [
                    {
                        "notice_way": {"1": ["sms", "voice", "wxwork-bot"], "3": ["weixin"], "2": ["mail"]},
                        "notice_receiver": ["group#bk_biz_maintainer", "user#user1"],
                        "id": 3,
                        "name": "\u84dd\u9cb8\u8fd0\u7ef4\u7ec4",
                        "wxwork_group": {"1": "12345,254678"},
                    }
                ],
                "action_type": "notice",
                "config": {
                    "alarm_end_time": "23:59:59",
                    "send_recovery_alarm": False,
                    "alarm_start_time": "00:00:00",
                    "alarm_interval": 120,
                },
                "id": 6,
                "action_id": 6,
            }
        },
        status=EventAction.Status.RUNNING,
        event_id="11dd36c4e45b40da6a8f436a01c781cc.1570284420.6.6.1",
    )

    Event.objects.all().delete()
    EventAction.objects.all().delete()
    AnomalyRecord.objects.all().delete()


@pytest.fixture()
def mock_collect(mock):
    return {
        "voice_collector": mock.patch("alarm_backends.service.action.notice.processor.VoiceCollector.collect"),
        "collector": mock.patch("alarm_backends.service.action.notice.processor.Collector.collect"),
        "short_collect": mock.patch("alarm_backends.service.action.tasks.short_collect"),
        "long_collect": mock.patch("alarm_backends.service.action.tasks.long_collect"),
        "multi_collect": mock.patch("alarm_backends.service.action.tasks.multi_collect"),
    }


@pytest.fixture()
def mock_host(mock):
    host_manager = mock.patch("alarm_backends.service.action.notice.utils.HostManager")
    host_manager.get.return_value = host

    module_manager = mock.patch("alarm_backends.service.action.notice.utils.ModuleManager")
    module_manager.get.return_value = module
    return host_manager


class TestProcess(object):
    def test_alarm_time(self, setup):
        processor = NoticeProcessor(setup.id)
        assert processor.is_alarm_time()

        setup.extend_info = {
            "action": {
                "notice_template": {"anomaly_template": "", "recovery_template": ""},
                "notice_group_list": [
                    {
                        "notice_way": {"1": ["sms"], "3": ["weixin"], "2": ["mail"]},
                        "notice_receiver": ["group#bk_biz_maintainer", "user#user1"],
                        "id": 3,
                        "name": "\u84dd\u9cb8\u8fd0\u7ef4\u7ec4",
                    }
                ],
                "action_type": "notice",
                "config": {
                    "alarm_end_time": "20:00:00",
                    "send_recovery_alarm": False,
                    "alarm_start_time": "00:00:00",
                    "alarm_interval": 120,
                },
                "id": 6,
                "action_id": 6,
            }
        }

        setup.create_time = datetime.strptime("2019-10-28 12:00:00", "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=pytz.timezone("utc")
        )
        setup.save()
        processor = NoticeProcessor(setup.id)
        assert processor.is_alarm_time()

        setup.create_time = datetime.strptime("2019-10-28 12:00:01", "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=pytz.timezone("utc")
        )
        setup.save()
        processor = NoticeProcessor(setup.id)
        assert not processor.is_alarm_time()

        setup.create_time = datetime.strptime("2019-10-28 11:59:59", "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=pytz.timezone("utc")
        )
        setup.save()
        processor = NoticeProcessor(setup.id)
        assert processor.is_alarm_time()

    def test_notice_config(self, setup):
        processor = NoticeProcessor(setup.id)
        assert len(processor.notice_configs) == 3

        notice_ways = {notice_config["notice_way"] for notice_config in processor.notice_configs}
        assert notice_ways == {"sms", "voice", "wxwork-bot"}

        for notice_config in processor.notice_configs:
            if notice_config["notice_way"] == "sms":
                assert set(notice_config["notice_receivers"]) == {"user2", "user1"}
            elif notice_config["notice_way"] == "voice":
                assert set(notice_config["notice_receivers"]) == {"user2,user1"}
            else:
                assert set(notice_config["notice_receivers"]) == {"12345", "254678"}

    def test_group_to_users(self, setup, mock_host):
        processor = NoticeProcessor(setup.id)
        assert processor.group_to_users("operator") == ["admin"]
        assert processor.group_to_users("bk_bak_operator") == ["admin1"]

        host.operator = []
        module.operator.append("user1")

        host.bk_bak_operator = []
        module.bk_bak_operator.append("user2")

        processor = NoticeProcessor(setup.id)
        assert processor.group_to_users("operator") == ["user1"]
        assert processor.group_to_users("bk_bak_operator") == ["user2"]
