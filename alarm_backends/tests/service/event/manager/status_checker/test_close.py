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


import copy

import arrow
import mock
import pytest

from alarm_backends.core.cache.key import (
    ACTION_LIST_KEY,
    EVENT_ID_CACHE_KEY,
    LAST_CHECKPOINTS_CACHE_KEY,
)
from alarm_backends.service.event.manager.status_checker import CloseStatusChecker
from alarm_backends.tests.service.event.manager import ANOMALY_EVENT, EVENT_KEY, STRATEGY
from api.cmdb.define import Host, ServiceInstance, TopoNode
from bkmonitor.models import Event, EventAction
from bkmonitor.utils import time_tools

pytestmark = pytest.mark.django_db


class TestCloseStatusChecker(object):
    def setup(self):
        check_time = arrow.now().replace(seconds=-200).timestamp
        LAST_CHECKPOINTS_CACHE_KEY.client.hset(
            LAST_CHECKPOINTS_CACHE_KEY.get_key(),
            LAST_CHECKPOINTS_CACHE_KEY.get_field(
                strategy_id=1,
                item_id=1,
                dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
                level=1,
            ),
            check_time,
        )

        Event.objects.create(
            event_id="new-event-id",
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

    @classmethod
    def create_event(cls, event_id, strategy=None):
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        source_time = time_tools.mysql_time(arrow.now().datetime)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=source_time,
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy or STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        return event

    def teardown(self):
        Event.objects.all().delete()
        EventAction.objects.all().delete()

    def test_set_closed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.get("1569246180").datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        checker = CloseStatusChecker(event)
        checker.close("测试关闭")
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED
        event_actions = EventAction.objects.filter(event_id=event_id)
        assert event_actions[0].operate == EventAction.Operate.CLOSE
        assert event_actions[0].message == "测试关闭"
        assert event_actions[0].status == EventAction.Status.SUCCESS

    def test_strategy_item_changed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["item_id"] = 3
        checker = CloseStatusChecker(event, strategy)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_deleted(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )
        checker = CloseStatusChecker(event, None)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_metric_changed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["metric_id"] = "new-metric-id"
        checker = CloseStatusChecker(event, strategy)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_dimension_changed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["rt_query_config"]["agg_dimension"] = ["ip"]
        checker = CloseStatusChecker(event, strategy)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_level_deleted(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["algorithm_list"].pop(0)
        checker = CloseStatusChecker(event, strategy)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_level_changed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["algorithm_list"].pop(1)
        checker = CloseStatusChecker(event, strategy)
        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_strategy_no_data_alarm(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        old_strategy = copy.deepcopy(STRATEGY)
        old_strategy["item_list"][0]["rt_query_config"]["agg_dimension"] = ["__NO_DATA_DIMENSION__"]
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=old_strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        new_strategy = copy.deepcopy(STRATEGY)
        new_strategy["item_list"][0]["no_data_config"]["is_enable"] = False
        checker = CloseStatusChecker(event, new_strategy)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_strategy_no_data_alarm_not_closed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        new_strategy = copy.deepcopy(STRATEGY)
        new_strategy["item_list"][0]["no_data_config"]["is_enable"] = True
        checker = CloseStatusChecker(event, new_strategy)
        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_strategy_no_changed(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        checker = CloseStatusChecker(event, STRATEGY)
        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    def test_no_data_close(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        check_time = arrow.now().replace(seconds=-310).timestamp
        LAST_CHECKPOINTS_CACHE_KEY.client.hset(
            LAST_CHECKPOINTS_CACHE_KEY.get_key(),
            LAST_CHECKPOINTS_CACHE_KEY.get_field(
                strategy_id=1,
                item_id=1,
                dimensions_md5="55a76cf628e46c04a052f4e19bdb9dbf",
                level=1,
            ),
            check_time,
        )

        checker = CloseStatusChecker(event, STRATEGY)
        assert checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) is None
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.CLOSED

    def test_not_timeseries_event(self):
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)

        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["data_type_label"] = "event"

        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
        )

        checker = CloseStatusChecker(event, strategy)
        assert not checker.check()

        assert EVENT_ID_CACHE_KEY.client.get(EVENT_KEY) == event_id
        assert Event.objects.get(event_id=event_id).status == Event.EventStatus.ABNORMAL

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.HostManager")
    def test_host_target_included(self, HostManager):
        HostManager.get.return_value = Host(
            bk_host_innerip="10.0.0.1",
            bk_cloud_id=0,
            bk_cloud_name="default area",
            bk_host_id=1,
            bk_biz_id=2,
            operator=["admin"],
            bk_bak_operator=["admin1"],
            bk_module_ids=[1],
            bk_set_ids=[1],
        )
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="host|10.0.0.1|0",
        )
        checker = CloseStatusChecker(event, STRATEGY)
        assert not checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.HostManager")
    def test_host_target_not_found(self, HostManager):
        HostManager.get.return_value = None
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="host|10.0.0.1|0",
        )
        checker = CloseStatusChecker(event, STRATEGY)
        assert checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.HostManager")
    def test_host_target_not_included(self, HostManager):
        HostManager.get.return_value = HostManager.get.return_value = Host(
            bk_host_innerip="10.0.0.2",
            bk_cloud_id=0,
            bk_cloud_name="default area",
            bk_host_id=1,
            bk_biz_id=2,
            operator=["admin"],
            bk_bak_operator=["admin1"],
            bk_module_ids=[1],
            bk_set_ids=[1],
        )
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=STRATEGY,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="host|10.0.0.2|0",
        )
        checker = CloseStatusChecker(event, STRATEGY)
        assert checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.HostManager")
    def test_topo_target_included(self, HostManager):
        HostManager.get.return_value = HostManager.get.return_value = Host(
            bk_host_innerip="10.0.0.2",
            bk_cloud_id=0,
            bk_cloud_name="default area",
            bk_host_id=1,
            bk_biz_id=2,
            operator=["admin"],
            bk_bak_operator=["admin1"],
            bk_module_ids=[1],
            bk_set_ids=[1],
            topo_link={
                "module|16": [TopoNode("module", 16), TopoNode("set", 13)],
                "module|28": [TopoNode("module", 28), TopoNode("set", 26)],
            },
        )
        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["target"][0][0] = {
            "field": "host_topo_node",
            "method": "eq",
            "value": [{"bk_inst_id": 28, "bk_obj_id": "module"}, {"bk_inst_id": 13, "bk_obj_id": "set"}],
        }
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="host|10.0.0.2|0",
        )
        checker = CloseStatusChecker(event, strategy)
        assert not checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.HostManager")
    def test_topo_target_not_included(self, HostManager):
        HostManager.get.return_value = HostManager.get.return_value = Host(
            bk_host_innerip="10.0.0.1",
            bk_cloud_id=0,
            bk_cloud_name="default area",
            bk_host_id=1,
            bk_biz_id=2,
            operator=["admin"],
            bk_bak_operator=["admin1"],
            bk_module_ids=[1],
            bk_set_ids=[1],
            topo_link={
                "module|16": [TopoNode("module", 16), TopoNode("set", 13)],
                "module|28": [TopoNode("module", 28), TopoNode("set", 26)],
            },
        )
        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["target"][0][0] = {
            "field": "host_topo_node",
            "method": "eq",
            "value": [{"bk_inst_id": 26, "bk_obj_id": "module"}, {"bk_inst_id": 12, "bk_obj_id": "set"}],
        }
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="host|10.0.0.2|0",
        )
        checker = CloseStatusChecker(event, strategy)
        assert checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.ServiceInstanceManager")
    def test_service_target_not_included(self, ServiceInstanceManager):
        ServiceInstanceManager.get.return_value = ServiceInstance(
            123,
            topo_link={
                "module|16": [TopoNode("module", 16), TopoNode("set", 13)],
                "module|28": [TopoNode("module", 28), TopoNode("set", 26)],
            },
        )
        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["target"][0][0] = {
            "field": "service_topo_node",
            "method": "eq",
            "value": [{"bk_inst_id": 26, "bk_obj_id": "module"}, {"bk_inst_id": 12, "bk_obj_id": "set"}],
        }
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="service|123",
        )
        checker = CloseStatusChecker(event, strategy)
        assert checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.ServiceInstanceManager")
    def test_service_target_included(self, ServiceInstanceManager):
        ServiceInstanceManager.get.return_value = ServiceInstance(
            2,
            topo_link={
                "module|16": [TopoNode("module", 16), TopoNode("set", 13)],
                "module|28": [TopoNode("module", 28), TopoNode("set", 26)],
            },
        )
        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["target"][0][0] = {
            "field": "service_topo_node",
            "method": "eq",
            "value": [{"bk_inst_id": 16, "bk_obj_id": "module"}, {"bk_inst_id": 12, "bk_obj_id": "set"}],
        }
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="service|123",
        )
        checker = CloseStatusChecker(event, strategy)
        assert not checker.check_target_not_included()

    @mock.patch("alarm_backends.service.event.manager.status_checker.close.ServiceInstanceManager")
    def test_service_target_not_found(self, ServiceInstanceManager):
        ServiceInstanceManager.get.return_value = None
        strategy = copy.deepcopy(STRATEGY)
        strategy["item_list"][0]["target"][0][0] = {
            "field": "service_topo_node",
            "method": "eq",
            "value": [{"bk_inst_id": 16, "bk_obj_id": "module"}, {"bk_inst_id": 12, "bk_obj_id": "set"}],
        }
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        EVENT_ID_CACHE_KEY.client.set(EVENT_KEY, event_id)
        event = Event.objects.create(
            event_id=event_id,
            begin_time=time_tools.mysql_time(arrow.now().replace(seconds=-300).datetime),
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=2,
            strategy_id=1,
            origin_config=strategy,
            origin_alarm=ANOMALY_EVENT,
            level=1,
            target_key="service|123",
        )
        checker = CloseStatusChecker(event, strategy)
        assert checker.check_target_not_included()

    def test_push_actions(self):
        new_strategy = copy.deepcopy(STRATEGY)
        new_strategy["action_list"][0]["config"]["send_close_alarm"] = True
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id, new_strategy)
        checker = CloseStatusChecker(event, new_strategy)
        checker.push_actions("close")

        # 测试消息队列
        event_actions = EventAction.objects.filter(event_id=event_id, operate="CLOSE_PUSH")
        assert "action" in event_actions[0].extend_info
        assert event_actions[0].operate == EventAction.Operate.CLOSE_PUSH
        assert event_actions[0].status == EventAction.Status.RUNNING
        action_id = ACTION_LIST_KEY.client.lpop(ACTION_LIST_KEY.get_key(action_type="message_queue"))
        assert int(action_id) == event_actions[0].id

        # 测试告警队列
        event_actions = EventAction.objects.filter(event_id=event_id, operate="CLOSE_NOTICE")
        assert "action" in event_actions[0].extend_info
        assert event_actions[0].operate == EventAction.Operate.CLOSE_NOTICE
        assert event_actions[0].status == EventAction.Status.RUNNING
        action_id = ACTION_LIST_KEY.client.lpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        assert int(action_id) == event_actions[0].id

    def test_push_actions_no_close(self):
        new_strategy = copy.deepcopy(STRATEGY)
        new_strategy["action_list"][0]["config"]["send_close_alarm"] = False
        event_id = "55a76cf628e46c04a052f4e19bdb9dbf.1569246240.1.1.1"
        event = self.create_event(event_id, new_strategy)
        checker = CloseStatusChecker(event)
        checker.push_actions("close")
        # 在处理逻辑中关闭告警会被过滤掉，应当只有消息队列有一个action
        assert len(EventAction.objects.filter(event_id=event_id)) == 1
        action_id = ACTION_LIST_KEY.client.rpop(ACTION_LIST_KEY.get_key(action_type="notice"))
        assert action_id is None
