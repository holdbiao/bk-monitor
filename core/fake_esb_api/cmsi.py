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


from django.utils.translation import ugettext as _

from core.fake_esb_api.register import register


@register
def get_msg_type(params=None, **kwargs):
    return [
        {"type": "weixin", "icon": "", "is_active": True, "label": _("微信")},
        {"type": "mail", "icon": "", "is_active": True, "label": _("邮件")},
        {"type": "sms", "icon": "", "is_active": True, "label": _("短信")},
        {"type": "voice", "icon": "", "is_active": True, "label": _("语音")},
        {"type": "custom", "icon": "", "is_active": False, "label": _("自定义")},
    ]


@register
def send_msg(params=None, **kwargs):
    return None


@register
def send_weixin(params=None, **kwargs):
    return None


@register
def send_mail(params=None, **kwargs):
    return None


@register
def send_sms(params=None, **kwargs):
    return None


@register
def send_voice(params=None, **kwargs):
    return None
