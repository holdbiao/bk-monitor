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


import abc
import base64

import six
from django.conf import settings
from rest_framework import serializers

from core.drf_resource.contrib.api import APIResource


class CMSIBaseResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url = "%s/api/c/compapi/cmsi/" % settings.BK_PAAS_INNER_HOST
    module_name = "cmsi"


class GetMsgType(CMSIBaseResource):
    """
    查询通知类型
    """

    action = "get_msg_type"
    method = "GET"


class SendMsg(CMSIBaseResource):
    """
    通用发送消息
    """

    action = "send_msg"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        receiver__username = serializers.CharField()
        title = serializers.CharField()
        content = serializers.CharField()
        msg_type = serializers.CharField()
        is_content_base64 = serializers.BooleanField(default=False)

        def validate(self, attrs):
            if attrs["is_content_base64"]:
                attrs["content"] = base64.b64encode(attrs["content"].encode("utf-8"))
            return attrs


class SendWeixin(CMSIBaseResource):
    """
    发送微信消息
    """

    action = "send_weixin"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        receiver__username = serializers.CharField()
        heading = serializers.CharField()
        message = serializers.CharField()
        date = serializers.CharField(required=False)
        remark = serializers.CharField(required=False)
        is_message_base64 = serializers.BooleanField(default=False)

        def validate(self, attrs):
            if attrs["is_message_base64"]:
                attrs["message"] = base64.b64encode(attrs["message"].encode("utf-8"))

            params = {
                "receiver__username": attrs["receiver__username"],
                "data": {
                    "heading": attrs["heading"],
                    "message": attrs["message"],
                    "is_message_base64": attrs["is_message_base64"],
                },
            }

            if "date" in attrs:
                params["data"]["date"] = attrs["date"]
            if "remark" in attrs:
                params["data"]["remark"] = attrs["remark"]

            return params


class SendMail(CMSIBaseResource):
    """
    发送邮件消息
    """

    action = "send_mail"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class Attachment(serializers.Serializer):
            filename = serializers.CharField()
            content = serializers.CharField()
            type = serializers.CharField(required=False)
            disposition = serializers.CharField(required=False)
            content_id = serializers.CharField(required=False)

        receiver = serializers.CharField(required=False)
        receiver__username = serializers.CharField(required=False)
        sender = serializers.CharField(required=False)
        cc = serializers.CharField(required=False)
        cc__username = serializers.CharField(required=False)
        title = serializers.CharField()
        content = serializers.CharField()
        body_format = serializers.CharField(default="Html")
        is_content_base64 = serializers.BooleanField(default=False)
        attachments = Attachment(many=True, required=False)

        def validate(self, attrs):
            if attrs["is_content_base64"]:
                attrs["content"] = base64.b64encode(attrs["content"].encode("utf-8"))

            return attrs


class SendSms(CMSIBaseResource):
    """
    发送短信消息
    """

    action = "send_sms"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        receiver = serializers.CharField(required=False)
        receiver__username = serializers.CharField(required=False)
        content = serializers.CharField()
        is_content_base64 = serializers.BooleanField(default=False)

        def validate(self, attrs):
            if attrs["is_content_base64"]:
                attrs["content"] = base64.b64encode(attrs["content"].encode("utf-8"))

            return attrs


class SendVoice(CMSIBaseResource):
    """
    发送语言消息
    """

    action = "send_voice_msg"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class UserInfo(serializers.Serializer):
            username = serializers.CharField()
            mobile_phone = serializers.CharField(required=False)

        user_list_information = UserInfo(required=False, many=True)
        receiver__username = serializers.CharField(required=False)
        auto_read_message = serializers.CharField()
