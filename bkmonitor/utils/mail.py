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

from email.Header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


class MailMessage(object):
    def __init__(self):
        self._content = MIMEMultipart("alternative")

    @property
    def content(self):
        return self._content.as_string()

    def add_image_attatchment(self, name, data):
        att = MIMEImage(data)
        att.add_header("Content-ID", name)
        self._content.attach(att)

    def add_html(self, html, charset="utf-8"):
        content = MIMEText(html, "html", charset)
        self._content.attach(content)

    def add_attatchment(self, name, data, type, is_base64=False, charset="utf-8"):
        if not is_base64:
            data = base64.encodestring(data)
        att = MIMEText(data, "base64", charset)
        att.add_header("Content-ID", name)
        self._content.attach(att)
