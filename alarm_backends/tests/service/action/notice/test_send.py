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
import json

import pytest
from django.conf import settings
from django.test import override_settings


@pytest.fixture()
def send_methods(mock):
    settings.WXWORK_BOT_WEBHOOK_URL = "http://example.com"

    def send_msg(*args, **kwargs):
        if "user3" in kwargs["receiver__username"]:
            raise Exception("send fail because I don't like user3")

    def send_request(*args, **kwargs):
        class Response:
            @staticmethod
            def json():
                if "user3" in json.dumps(kwargs["json"]):
                    return {"errcode": 1, "errmsg": "send fail because I don't like user3"}
                else:
                    return {"errcode": 0, "errmsg": ""}

        return Response

    return {
        "send_weixin": mock.patch(
            "alarm_backends.service.action.notice.send.api.cmsi.send_weixin", side_effect=send_msg
        ),
        "send_sms": mock.patch("alarm_backends.service.action.notice.send.api.cmsi.send_sms", side_effect=send_msg),
        "send_mail": mock.patch("alarm_backends.service.action.notice.send.api.cmsi.send_mail", side_effect=send_msg),
        "send_voice": mock.patch("alarm_backends.service.action.notice.send.api.cmsi.send_voice", side_effect=send_msg),
        "send_default": mock.patch("alarm_backends.service.action.notice.send.api.cmsi.send_msg", side_effect=send_msg),
        "send_wxwork_bot": mock.patch("requests.post", side_effect=send_request),
    }


class TestSender(object):
    @override_settings(ENABLED_NOTICE_WAYS=["weixin", "mail", "sms", "voice", "wxwork-bot", "xxx", "yyy"])
    def test_send(self, send_methods):
        from alarm_backends.service.action.notice.send import Sender

        sender = Sender()

        args = [
            ("weixin", "send_weixin", 1),
            ("sms", "send_sms", 1),
            ("mail", "send_mail", 1),
            ("voice", "send_voice", 1),
            ("wxwork-bot", "send_wxwork_bot", 1),
            ("xxx", "send_default", 1),
            ("yyy", "send_default", 2),
        ]

        for arg in args:
            result = sender.send(arg[0], ["user1", "user2"])
            assert result["user1"]["result"]
            assert result["user2"]["result"]
            assert send_methods[arg[1]].call_count == arg[2]

        for arg in args:
            result = sender.send(arg[0], ["user1", "user3"])
            assert not result["user1"]["result"]
            assert not result["user3"]["result"]
            assert result["user1"]["message"] == "send fail because I don't like user3"

    @override_settings(ENABLED_NOTICE_WAYS=["weixin", "sms", "voice", "wxwork-bot"])
    def test_send_disabled(self, send_methods):
        from alarm_backends.service.action.notice.send import Sender

        sender = Sender()

        args = [
            ("weixin", "send_weixin", 1),
            ("sms", "send_sms", 1),
            ("voice", "send_voice", 1),
            ("wxwork-bot", "send_wxwork_bot", 1),
        ]

        for arg in args:
            result = sender.send(arg[0], ["user1", "user2"])
            assert result["user1"]["result"]
            assert result["user2"]["result"]
            assert send_methods[arg[1]].call_count == arg[2]

        for arg in [
            ("mail", "send_mail", 1),
            ("xxx", "send_default", 1),
            ("yyy", "send_default", 2),
        ]:
            result = sender.send(arg[0], ["user1", "user3"])
            assert not result["user1"]["result"]
            assert not result["user3"]["result"]
            assert result["user3"]["message"] == "发送失败，全局配置中该消息渠道被禁用。"
