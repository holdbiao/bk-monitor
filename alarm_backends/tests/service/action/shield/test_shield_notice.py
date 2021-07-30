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


import arrow
import pytest

from alarm_backends.core.cache.key import NOTICE_SHIELD_KEY_LOCK
from alarm_backends.service.action.shield.shield_obj import ShieldObj
from alarm_backends.service.action.shield.tasks import do_check_and_send_shield_notice
from api.cmdb.define import Business, ServiceInstance, TopoNode
from bkmonitor.models import Shield
from bkmonitor.utils import time_tools

pytestmark = pytest.mark.django_db


def create_shield_obj(begin_time, end_time):
    shield_config = Shield.objects.create(
        bk_biz_id=2,
        category="strategy",
        scope_type="",
        content="",
        begin_time=time_tools.mysql_time(begin_time),
        end_time=time_tools.mysql_time(end_time),
        failure_time=time_tools.mysql_time(end_time),
        dimension_config={
            "level": [1],
            "strategy_id": 11,
        },
        cycle_config={
            "begin_time": "",
            "end_time": "",
            "type": 1,
            "day_list": [],
            "week_list": [],
        },
        notice_config={
            "notice_receiver": ["user#admin1", "user#admin2", "group#bk_biz_maintainer"],
            "notice_time": 5,
            "notice_way": ["weixin", "mail", "voice"],
        },
        description="test shield description",
        is_quick=False,
    )
    shield_config = list(Shield.objects.filter(id=shield_config.id).values())[0]
    return ShieldObj(shield_config)


@pytest.fixture()
def get_business_roles(mocker):
    return mocker.patch("alarm_backends.service.action.shield.shield_obj.get_business_roles")


@pytest.fixture()
def cmsi(mocker):
    mock = mocker.patch("alarm_backends.service.action.notice.send.api.cmsi")
    mock.send_sms.return_value = True
    mock.send_weixin.return_value = True
    mock.send_voice.return_value = True
    mock.send_mail.return_value = True
    mock.send_msg.return_value = True
    return mock


@pytest.fixture()
def get_now_datetime(mocker):
    return mocker.patch("alarm_backends.service.action.shield.shield_obj.ShieldObj.get_now_datetime")


@pytest.fixture()
def service_manager(mocker):
    return mocker.patch("alarm_backends.service.action.shield.display_manager.ServiceInstanceManager")


@pytest.fixture()
def topo_manager(mocker):
    return mocker.patch("alarm_backends.service.action.shield.display_manager.TopoManager")


@pytest.fixture()
def biz_manager(mocker):
    return mocker.patch("alarm_backends.service.action.shield.display_manager.BusinessManager")


class TestShieldNotice(object):

    EXPECTED_SEND_RESULT = {
        "weixin": {
            "admin1": {"message": "发送成功", "result": True},
            "admin2": {"message": "发送成功", "result": True},
        },
        "mail": {
            "admin1": {"message": "发送成功", "result": True},
            "admin2": {"message": "发送成功", "result": True},
        },
        "voice": {
            "admin1": {"message": "发送成功", "result": True},
            "admin2": {"message": "发送成功", "result": True},
        },
    }

    def setup(self):
        Shield.objects.all().delete()
        NOTICE_SHIELD_KEY_LOCK.client.flushall()

    def teardown(self):
        Shield.objects.all().delete()
        NOTICE_SHIELD_KEY_LOCK.client.flushall()

    def test_can_send_start(self):
        begin_time = arrow.now().replace(minutes=4).datetime
        end_time = arrow.now().replace(minutes=14).datetime
        obj = create_shield_obj(begin_time, end_time)
        assert obj.can_send_start_notice()
        assert not obj.can_send_end_notice()

    def test_can_send_start_has_lock(self):
        begin_time = arrow.now().replace(minutes=4).datetime
        end_time = arrow.now().replace(minutes=14).datetime
        obj = create_shield_obj(begin_time, end_time)

        NOTICE_SHIELD_KEY_LOCK.client.set(obj.notice_lock_key, "__lock__", NOTICE_SHIELD_KEY_LOCK.ttl)

        assert not obj.can_send_start_notice()
        assert not obj.can_send_end_notice()

    def test_can_send_start_not_time_match(self):
        begin_time = arrow.now().replace(minutes=6).datetime
        end_time = arrow.now().replace(minutes=16).datetime
        obj = create_shield_obj(begin_time, end_time)

        assert not obj.can_send_start_notice()
        assert not obj.can_send_end_notice()

    def test_can_send_end(self):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=5).datetime
        obj = create_shield_obj(begin_time, end_time)

        NOTICE_SHIELD_KEY_LOCK.client.set(obj.notice_lock_key, "__lock__", NOTICE_SHIELD_KEY_LOCK.ttl)

        assert not obj.can_send_start_notice()
        assert obj.can_send_end_notice()

    def test_can_send_end_no_lock(self):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=4).datetime
        obj = create_shield_obj(begin_time, end_time)

        assert not obj.can_send_start_notice()
        assert not obj.can_send_end_notice()

    def test_can_send_end_not_time_match(self):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)

        NOTICE_SHIELD_KEY_LOCK.client.set(obj.notice_lock_key, "__lock__", NOTICE_SHIELD_KEY_LOCK.ttl)

        assert not obj.can_send_start_notice()
        assert not obj.can_send_end_notice()

    def test_get_context_start(self):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)

        context = obj.get_notice_context("start")
        excepted_context = {
            "description": "test shield description",
            "shield_content": "该策略已经被删除",
            "start_time": begin_time.strftime("%H:%M"),
            "shield_id": obj.config["id"],
            "notice_type": "开始",
            "cycle_duration": "<1小时/次",
            "category_name": "策略屏蔽",
        }
        assert excepted_context == context

    def test_get_context_service_instance(self, service_manager):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)
        obj.config["category"] = "scope"
        obj.config["scope_type"] = "instance"
        obj.config["dimension_config"] = {"service_instance_id": [1, 2, 3]}

        service_manager.multi_get.return_value = [
            ServiceInstance(service_instance_id=1, name="s1", bk_host_id=1, bk_module_id=5, bk_biz_id=2),
            None,
            ServiceInstance(service_instance_id=3, name="s3", bk_host_id=3, bk_module_id=3, bk_biz_id=3),
        ]

        context = obj.get_notice_context("start")
        excepted_context = {
            "description": "test shield description",
            "shield_content": "s1,2,s3",
            "start_time": begin_time.strftime("%H:%M"),
            "shield_id": obj.config["id"],
            "notice_type": "开始",
            "cycle_duration": "<1小时/次",
            "category_name": "范围屏蔽（ 服务实例 ）",
        }
        assert excepted_context == context

    def test_get_context_topo(self, topo_manager):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)
        obj.config["category"] = "scope"
        obj.config["scope_type"] = "node"
        obj.config["dimension_config"] = {
            "bk_topo_node": [
                {
                    "bk_obj_id": "module",
                    "bk_inst_id": 2,
                },
                {
                    "bk_obj_id": "set",
                    "bk_inst_id": 4,
                },
                {
                    "bk_obj_id": "biz",
                    "bk_inst_id": 3,
                },
            ]
        }

        topo_manager.multi_get.return_value = [
            TopoNode("module", 2, "模块", "作业平台"),
            None,
            TopoNode("biz", 3, "业务", "蓝鲸"),
        ]

        context = obj.get_notice_context("start")
        excepted_context = {
            "description": "test shield description",
            "shield_content": "模块/作业平台,set/4,业务/蓝鲸",
            "start_time": begin_time.strftime("%H:%M"),
            "shield_id": obj.config["id"],
            "notice_type": "开始",
            "cycle_duration": "<1小时/次",
            "category_name": "范围屏蔽（ 节点 ）",
        }
        assert excepted_context == context

    def test_get_context_biz(self, biz_manager):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)
        obj.config["category"] = "scope"
        obj.config["scope_type"] = "biz"
        obj.config["dimension_config"] = {}

        biz_manager.get.return_value = Business(2, "蓝鲸")

        context = obj.get_notice_context("end")
        excepted_context = {
            "description": "test shield description",
            "shield_content": "蓝鲸",
            "start_time": end_time.strftime("%H:%M"),
            "shield_id": obj.config["id"],
            "notice_type": "结束",
            "cycle_duration": "<1小时/次",
            "category_name": "范围屏蔽（ 业务 ）",
        }
        assert excepted_context == context

    def test_get_context_end(self):
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)

        context = obj.get_notice_context("end")
        excepted_context = {
            "description": "test shield description",
            "shield_content": "该策略已经被删除",
            "start_time": end_time.strftime("%H:%M"),
            "shield_id": obj.config["id"],
            "notice_type": "结束",
            "cycle_duration": "<1小时/次",
            "category_name": "策略屏蔽",
        }
        assert excepted_context == context

    def test_parse_notice_receivers(self, get_business_roles):
        get_business_roles.return_value = {"bk_biz_maintainer": ["admin2", "admin3", "admin1"]}
        begin_time = arrow.now().replace(minutes=-5).datetime
        end_time = arrow.now().replace(minutes=10).datetime
        obj = create_shield_obj(begin_time, end_time)
        receivers = obj.parse_notice_receivers()
        assert receivers == ["admin1", "admin2", "admin3"]

    def test_send_notice(self, cmsi):
        begin_time = arrow.now().replace(minutes=4).datetime
        end_time = arrow.now().replace(minutes=14).datetime
        obj = create_shield_obj(begin_time, end_time)
        result = obj.send_notice("start")

        assert result == self.EXPECTED_SEND_RESULT

    def test_check_and_send(self, cmsi, get_now_datetime):
        now_time = arrow.now()
        get_now_datetime.return_value = now_time
        begin_time = now_time.replace(minutes=6).datetime
        end_time = now_time.replace(minutes=14).datetime
        obj = create_shield_obj(begin_time, end_time)
        start_result, end_result = obj.check_and_send_notice()

        assert start_result is None
        assert end_result is None
        assert not NOTICE_SHIELD_KEY_LOCK.client.exists(obj.notice_lock_key)

        get_now_datetime.return_value = now_time.replace(minutes=1)
        start_result, end_result = obj.check_and_send_notice()

        assert start_result == self.EXPECTED_SEND_RESULT
        assert end_result is None
        assert NOTICE_SHIELD_KEY_LOCK.client.exists(obj.notice_lock_key)

        get_now_datetime.return_value = now_time.replace(minutes=10)
        start_result, end_result = obj.check_and_send_notice()
        assert start_result is None
        assert end_result == self.EXPECTED_SEND_RESULT
        assert not NOTICE_SHIELD_KEY_LOCK.client.exists(obj.notice_lock_key)

    def test_task(self, cmsi, get_now_datetime):
        now_time = arrow.now()
        get_now_datetime.return_value = now_time

        begin_time = now_time.replace(minutes=4).datetime
        end_time = now_time.replace(minutes=14).datetime
        obj1 = create_shield_obj(begin_time, end_time)

        begin_time = now_time.replace(minutes=5).datetime
        end_time = now_time.replace(minutes=15).datetime
        obj2 = create_shield_obj(begin_time, end_time)

        begin_time = now_time.replace(minutes=6).datetime
        end_time = now_time.replace(minutes=16).datetime
        obj3 = create_shield_obj(begin_time, end_time)

        target_ids = Shield.objects.filter(
            is_enabled=True, is_deleted=False, failure_time__gte=time_tools.now()
        ).values_list("id", flat=True)

        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == {obj1.config["id"], obj2.config["id"]}

        get_now_datetime.return_value = now_time.replace(minutes=3)

        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == {obj3.config["id"]}

        get_now_datetime.return_value = now_time.replace(minutes=7)

        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == set()

        get_now_datetime.return_value = now_time.replace(minutes=9)
        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == {obj1.config["id"]}

        get_now_datetime.return_value = now_time.replace(minutes=12)
        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == {obj2.config["id"], obj3.config["id"]}

        get_now_datetime.return_value = now_time.replace(minutes=15)
        result = do_check_and_send_shield_notice(list(target_ids))
        assert result == set()
