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
import base64
import hashlib
import logging

import requests
from django.conf import settings
from django.utils.translation import ugettext as _

from bkmonitor.utils.template import AlarmNoticeTemplate
from core.drf_resource import api

logger = logging.getLogger("bkmonitor.cron_report")


class Sender(object):
    """
    通知发送器
    """

    LengthLimit = {
        "sms": 140,
    }

    def __init__(self, context=None, title_template_path="", content_template_path=""):
        """
        :param context: EventContext or dict
        :param title_template_path: 通知title的模板路径
        :param content_template_path: 通知content的模板路径
        """
        self.context = context

        title_template = AlarmNoticeTemplate(title_template_path)
        content_template = AlarmNoticeTemplate(content_template_path)
        self.title = title_template.render(self.get_context_dict())
        try:
            self.content = content_template.render(self.get_context_dict())
        except Exception as e:
            logger.exception(e)
            self.content = e
            return

        # 如果消息长度超过限制，那么需要限制长度
        length_limit = self.LengthLimit.get(getattr(context, "notice_way", None))
        if length_limit and length_limit < len(self.content.encode("utf-8")):
            self.context.limit = True
            self.content = content_template.render(self.get_context_dict())

    def get_context_dict(self):
        """
        获取上下文字典
        """
        if self.context is None:
            return {}
        elif not isinstance(self.context, dict):
            return self.context.get_dictionary()
        return self.context

    def send(self, notice_way: str, notice_receivers: list):
        """
        统一发送通知
        :return: :return: {
            "user1": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        if isinstance(self.content, Exception):
            return {
                notice_receiver: {"message": str(self.content), "result": False} for notice_receiver in notice_receivers
            }

        method = getattr(self, "send_{}".format(notice_way.replace("-", "_")), None)
        if method:
            return method(notice_receivers)
        else:
            return self.send_default(notice_way, notice_receivers)

    def send_weixin(self, notice_receivers):
        """
        发送微信通知
        :return: {
            "user1": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        notice_result = {}
        message = _("发送成功")

        logger.info(
            "send.weixin({}): \ntitle: {}\ncontent: {}".format(",".join(notice_receivers), self.title, self.content)
        )

        result = True
        try:
            api.cmsi.send_weixin(
                receiver__username=",".join(notice_receivers),
                heading=self.title,
                message=self.content,
                is_message_base64=True,
            )
        except Exception as e:
            result = False
            message = str(e)
            logger.error("send.weixin failed, {}".format(e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {"message": message, "result": result}
        return notice_result

    def send_mail(self, notice_receivers):
        """
        发送邮件通知
        :return: {
            "user1": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        notice_result = {}
        params = {
            "receiver__username": ",".join(notice_receivers),
            "title": self.title,
            "content": self.content,
            "is_content_base64": True,
        }

        # 添加附件
        if getattr(self.context, "alarm", None) and getattr(self.context.alarm, "attachments", None):
            params["attachments"] = self.context.alarm.attachments

        if "attachments" in self.context:
            params["attachments"] = self.context["attachments"]

        message = _("发送成功")

        logger.info("send.mail({}): \ntitle: {}".format(",".join(notice_receivers), self.title))

        result = True
        try:
            api.cmsi.send_mail(**params)
        except Exception as e:
            result = False
            message = str(e)
            logger.error("send.mail failed, {}".format(e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {
                "message": message,
                "result": result,
            }
        return notice_result

    def send_sms(self, notice_receivers):
        """
        发送短信通知
        :return: {
            "user1": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        notice_result = {}
        message = _("发送成功")

        logger.info("send.sms({}): \ncontent: {}".format(",".join(notice_receivers), self.content))

        result = True
        try:
            api.cmsi.send_sms(
                receiver__username=",".join(notice_receivers),
                content=self.content,
                is_content_base64=True,
            )
        except Exception as e:
            result = False
            message = str(e)
            logger.error("send.sms failed, {}".format(e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {"message": message, "result": result}
        return notice_result

    def send_voice(self, notice_receivers):
        """
        发送语音通知
        :return: {
            "user1,user2": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        notice_result = {}
        message = _("发送成功")

        logger.info("send.voice({}): \ncontent: {}".format(",".join(notice_receivers), self.content))

        result = True
        try:
            api.cmsi.send_voice(
                receiver__username=",".join(notice_receivers),
                auto_read_message=self.content,
            )
        except Exception as e:
            result = False
            message = str(e)
            logger.error("send.voice failed, {}".format(e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {"message": message, "result": result}
        return notice_result

    def send_wxwork_bot(self, notice_receivers):
        """
        发送企业微信群通知
        """
        notice_result = {}
        message = _("发送成功")
        params = {"msgtype": "text", "chatid": "|".join(notice_receivers), "text": {"content": self.content}}

        logger.info("send.wxwork_group({}): \ncontent: {}".format(",".join(notice_receivers), self.content))

        result = True

        if not settings.WXWORK_BOT_WEBHOOK_URL:
            result = False
            message = _("未配置企业微信群机器人，请联系管理员")
        elif not params["chatid"]:
            result = False
            message = _("通知人不能为空")
        else:
            try:
                r = requests.post(settings.WXWORK_BOT_WEBHOOK_URL, json=params)
                response = r.json()
                if response["errcode"] != 0:
                    result = False
                    message = response["errmsg"]
            except Exception as e:
                result = False
                message = str(e)
                logger.error("send.wxwork_group failed, {}".format(e))

            if settings.WXWORK_BOT_SEND_IMAGE:
                try:
                    image = self.context.alarm.chart_image
                    if image:
                        md5 = hashlib.md5(base64.decodebytes(image.encode(encoding="UTF-8"))).hexdigest()
                        params = {
                            "chatid": "|".join(notice_receivers),
                            "msgtype": "image",
                            "image": {"base64": image, "md5": md5},
                        }
                        r = requests.post(settings.WXWORK_BOT_WEBHOOK_URL, json=params)
                        response = r.json()
                        if response["errcode"] != 0:
                            logger.error("send.wxwork_group image failed, {}".format(response["errmsg"]))
                except Exception as e:
                    logger.error("send.wxwork_group image failed, {}".format(e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {"message": message, "result": result}
        return notice_result

    def send_default(self, notice_way, notice_receivers):
        """
        发送默认通知
        :return: {
            "user1": {"result": true, "message": "OK"},
            "user2": {"result": false, "message": "发送失败"}
        }
        :rtype: dict
        """
        notice_result = {}
        message = _("发送成功")

        logger.info(
            "send.{}({}): \ntitle: {}\ncontent: {}".format(
                notice_way, ",".join(notice_receivers), self.title, self.content
            )
        )

        result = True
        try:
            api.cmsi.send_msg(
                msg_type=notice_way,
                receiver__username=",".join(notice_receivers),
                title=self.title,
                content=self.content,
            )
        except Exception as e:
            result = False
            message = str(e)
            logger.error("send.{} failed, {}".format(notice_way, e))

        for notice_receiver in notice_receivers:
            notice_result[notice_receiver] = {"message": message, "result": result}
        return notice_result
