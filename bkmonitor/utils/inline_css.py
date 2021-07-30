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
#!/usr/bin/env python
# encoding: utf-8

import re
from collections import defaultdict, namedtuple
from html.parser import HTMLParser
from io import StringIO

from django.utils.functional import cached_property

from bkmonitor.utils.iter_utils import dict_merge

ConvertStatus = (lambda x: namedtuple("ConvertStatus", x)(*x))(
    [
        "ready",
        "in_body",
        "in_style",
        "finish",
    ]
)


def cmp(a, b):
    return (a > b) - (a < b)


class InlineStyleConvertor(HTMLParser):
    StyleAttribute = namedtuple("StyleAttribute", ["key", "value"])
    Style = namedtuple("Style", ["selector", "attributes"])
    StyleLevelOrders = list(
        map(
            re.compile,
            [
                r"#\w+$",
                r"\.\w+$",
                r"\b\w+$",
                r"\*$",
            ],
        )
    )
    StyleParseRegexp = re.compile(r"([\w\.#\*][\w\.\#\s,:-]+)\s*{\s*(.+?)\s}", re.S | re.M)

    def __init__(self, output, style_txt, ignore=False, keep_style=False):
        self.output = output
        self.style_txt = style_txt
        self.ignore_inline = ignore
        self.status = ConvertStatus.ready
        self.keep_style = keep_style
        HTMLParser.__init__(self)

    @cached_property
    def styles(self):
        return self.format_style(self.style_txt)

    @classmethod
    def level_of(cls, selector):
        for i, rex in enumerate(cls.StyleLevelOrders):
            if rex.match(selector):
                break
        return i

    @classmethod
    def cmp_style(cls, a, b):
        return cmp(cls.level_of(a.selector), cls.level_of(b.selector))

    def sort_styles(self, styles):
        styles.sort(self.cmp_style, reverse=True)
        return styles

    def format_style(self, style_txt):
        styles = defaultdict(dict)
        parts = self.StyleParseRegexp.findall(style_txt)
        for selectors, attrs in parts:
            attributes = {}
            for attr in attrs.split(";"):
                attr = attr.strip()
                if not attr:
                    continue
                k, _, v = attr.partition(":")
                k = k.strip()
                v = v.strip()
                attributes[k] = self.StyleAttribute(k, v)

            for selector in selectors.split(","):
                selector = selector.strip()
                if selector:
                    styles[selector].update(attributes)

        results = {}
        for selector, attrs in list(styles.items()):
            results[selector] = self.Style(selector, list(attrs.values()))
        return results

    def css_dict(self, selector):
        css = {}
        styles = self.styles.get(selector)
        if styles:
            for attr in styles.attributes:
                css[attr.key] = attr.value
        return css

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.status = ConvertStatus.in_body
        elif tag == "style" and self.style_txt is None:
            self.status = ConvertStatus.in_style
            if not self.keep_style:
                return

        attrs = dict(attrs)

        if self.status == ConvertStatus.in_body:
            inline_style = attrs.pop("style", "")
            if self.ignore_inline:
                styles_list = []
            else:
                styles_list = [dict(i.strip().split(":") for i in inline_style.split(";") if i.strip())]

            eid = attrs.get("id")
            if eid:
                styles_list.append(self.css_dict("#%s" % eid))

            for cls in attrs.get("class", "").split():
                styles_list.append(self.css_dict(".%s" % cls))

            styles_list.append(self.css_dict(tag))
            styles_list.append(self.css_dict("*"))

            if styles_list:
                styles = dict_merge(styles_list)
            if styles:
                styles_items = list(styles.items())
                styles_items.sort(lambda a, b: cmp(a[0], b[0]))
                attrs["style"] = "; ".join("%s:%s" % i for i in styles_items)

        attr_str = " ".join('%s="%s"' % i for i in list(attrs.items()))
        self.output.write(
            "<{tag}{attrs}>".format(
                tag=tag,
                attrs=" %s" % attr_str if attr_str else "",
            )
        )

    def handle_endtag(self, tag):
        if tag == "body":
            self.status = ConvertStatus.finish
        elif tag == "style" and self.status == ConvertStatus.in_style:
            self.status = ConvertStatus.ready
            if not self.keep_style:
                return

        self.output.write("</{tag}>".format(tag=tag))

    def handle_data(self, data):
        if self.status == ConvertStatus.in_style:
            self.style_txt = data
            if not self.keep_style:
                return

        self.output.write(data)

    def feed(self, html):
        self.status = ConvertStatus.ready
        prefix, tag, postfix = html.partition("<html")
        self.output.write(prefix)
        return HTMLParser.feed(self, tag + postfix)


def transform(html, ignore_inline=False, keep_style=True):
    output = StringIO()
    parser = InlineStyleConvertor(output, None, ignore_inline, keep_style)
    parser.feed(html)
    return output.getvalue()
