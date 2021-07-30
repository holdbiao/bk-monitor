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


import logging
import re
from collections import defaultdict
from os import path

from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import translation
from jinja2 import Environment, Undefined

logger = logging.getLogger(__name__)


class NoticeRowRenderer(object):
    """
    行渲染器
    """

    LineTemplateMapping = defaultdict(
        lambda: "{title}{content}",
        {
            "mail": '<tr style="background: #FFFFFF;"><td style="color: #979BA5; font-size: 14px; height: 19px; '
            'vertical-align: text-top;">{title}</td><td style="color: #63656E; font-size: 14px; '
            'vertical-align: text-top;">{content}</td></tr><tr style="background: #FFFFFF;">'
            '<td colspan="4" style="height: 20px;"></td></tr>'
        },
    )

    @classmethod
    def format(cls, notice_way, title, content):
        """
        格式化
        :param notice_way: 通知方式
        :param title: 标题
        :param content: 文本
        """
        title = str(title).strip()
        content = str(content).strip()
        if title:
            title += ": "
        if not title and not content:
            return ""
        return cls.LineTemplateMapping[notice_way].format(title=title, content=content)

    @classmethod
    def render_line(cls, line, context):
        """
        使用行模板渲染一行渲染一行
        :param line:
        :param context:
        :return:
        """
        # 是否符合行模板格式
        if not re.match(r"^#.*#", line):
            return line

        title, content = line[1:].split("#", 1)
        return cls.format(context.get("notice_way"), title=title, content=content)

    @classmethod
    def render(cls, content, context):
        lines = []
        for line in content.splitlines():
            line = cls.render_line(line, context)
            if not line.strip():
                continue
            lines.append(line)

        return "\n".join(lines)


class CustomTemplateRenderer(object):
    """
    自定义模板渲染器
    """

    @staticmethod
    def render(content, context):
        content_template = Jinja2Renderer.render(context.get("content_template", ""), context)
        alarm_content = NoticeRowRenderer.render(content_template, context)
        if context.get("notice_way") == "mail":
            content = content.replace("\n", "")
        context["user_content"] = alarm_content
        return content


class Jinja2Renderer(object):
    """
    Jinja2渲染器
    """

    @staticmethod
    def render(content, context):
        return jinja2_environment().from_string(content).render(context)


class AlarmNoticeTemplate(object):
    """
    通知模板
    """

    Renderers = [
        CustomTemplateRenderer,
        Jinja2Renderer,
    ]

    def __init__(self, template_path=None, template_content=None):
        """
        :param template_path: 模板路径
        :type template_path: str or unicode
        """
        if template_path:
            self.template = self.get_template(template_path)
        elif template_content is not None:
            self.template = template_content
        else:
            self.template = ""

    def render(self, context):
        """
        模板渲染
        :param context: 上下文
        :return: 渲染后内容
        :rtype: str
        """
        template_message = self.template
        for renderer in self.Renderers:
            template_message = renderer.render(template_message, context)
        return template_message

    @staticmethod
    def get_template_source(template_path):
        """
        获取模板文本
        :param template_path: 模板路径
        :return: 模板消息
        """
        raw_template = get_template(template_path)
        with open(raw_template.template.filename, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def get_default_path(template_path):
        """
        获取默认模板路径
        :param template_path: 模板路径
        """
        dir_path, filename = path.split(template_path)
        name, ext = path.splitext(filename)
        names = name.split("_")
        names[0] = "default"
        name = "_".join(names) + ext
        return path.join(dir_path, name)

    @classmethod
    def get_template(cls, template_path):
        """
        查找模板
        :param template_path: 模板路径
        """
        if not template_path:
            return ""

        try:
            return cls.get_template_source(template_path)
        except TemplateDoesNotExist:
            logger.info("use empty template because {} not exists".format(template_path))
        except Exception as e:
            logger.info("use default template because {} load fail, {}".format(template_path, e))
        template_path = cls.get_default_path(template_path)

        try:
            return cls.get_template_source(template_path)
        except TemplateDoesNotExist:
            logger.info("use empty template because {} not exists".format(template_path))
        except Exception as e:
            logger.info("use empty template because {} load fail, {}".format(template_path, e))
        return ""


class UndefinedSilently(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return UndefinedSilently()

    def __unicode__(self):
        return ""

    def __str__(self):
        return ""

    __add__ = (
        __radd__
    ) = (
        __mul__
    ) = (
        __rmul__
    ) = (
        __div__
    ) = (
        __rdiv__
    ) = (
        __truediv__
    ) = (
        __rtruediv__
    ) = (
        __floordiv__
    ) = (
        __rfloordiv__
    ) = (
        __mod__
    ) = (
        __rmod__
    ) = (
        __pos__
    ) = (
        __neg__
    ) = (
        __call__
    ) = (
        __getitem__
    ) = (
        __lt__
    ) = (
        __le__
    ) = (
        __gt__
    ) = (
        __ge__
    ) = __int__ = __float__ = __complex__ = __pow__ = __rpow__ = __sub__ = __rsub__ = _fail_with_undefined_error


def jinja2_environment(**options):
    env = Environment(undefined=UndefinedSilently, extensions=["jinja2.ext.i18n"], **options)
    env.install_gettext_translations(translation, newstyle=True)
    return env
