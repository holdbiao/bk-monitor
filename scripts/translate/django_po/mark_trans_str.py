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
#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import tokenize
from collections import namedtuple
from io import StringIO

SUPPORT_FILE_SUFFIX = (
    ".py",
    ".js",
)
FILE_TYPE_TO_SUFFIX = {
    "python": ".py",
    "js": ".js",
}

TokenPoint = namedtuple("TokenPoint", ["row", "col"])
Token = namedtuple(
    "Token",
    [
        "type",
        "token",
        "start_at",
        "end_at",
        "source_line",
    ],
)

CHINESE_PATTERN = re.compile(u"[\u4e00-\u9fa5]+")


class TagString(object):
    """
    dfa
    """

    def __init__(self):
        self.line = None
        self.lines = []
        self.string_token = []
        pass

    def line_start(self):
        if self.line is not None:
            self.lines.append(self.line)
        self.line = ""

    def line_end(self):
        if self.line is not None:
            self.lines.append(self.line)

        self.line = None

    def write_line(self, line):
        self.line_start()
        self.line = line
        self.line_end()

    def handle_default(self, token):
        if self.line and self.line != token.source_line:
            self.line_end()
            self.line_start()
        self.line = token.source_line

    def handle_newline(self, token):
        if self.line:
            self.line_end()
        else:
            self.write_line(token.token)

    def handle_string(self, token):
        try:
            if (
                is_contain_chinese(token.token)
                and not token.source_line.startswith(u'__author__ = u"蓝鲸智云"')
                and not token.token.endswith(u'"""')
                and not token.token.endswith(u"'''")
            ):
                self.string_token.append(token)
            source_lines = [i + u"\n" for i in token.source_line.split(u"\n")]
            source_lines[0] = self.line or source_lines[0]
            source_lines[-1] = source_lines[-1][:-1]
            lines = source_lines[:-1]
            if len(lines) <= 1:
                return self.handle_default(token)
            line0 = lines[0]
            if not self.line or not self.line.endswith(line0):
                self.line = line0
            self.line_end()
            map(self.write_line, lines[1:-1])
            self.line = lines[-1] + source_lines[-1]
        except Exception as e:
            print(e)

    def tag_str(self):
        cur_line = 1
        cur_line_grow_char = 0
        is_replace = False
        for token in self.string_token:
            start_row = token.start_at.row
            start_col = token.start_at.col
            if cur_line == start_row:
                start_col += cur_line_grow_char
            else:
                cur_line = start_row
                cur_line_grow_char = 0

            line = self.lines[cur_line - 1]
            if line[start_col - 2 : start_col] == "_(":
                continue

            self.lines[cur_line - 1] = "{}{}{}".format(line[:start_col], "_(", line[start_col:])
            cur_line_grow_char += 2

            end_row = token.end_at.row
            end_col = token.end_at.col
            if cur_line == end_row:
                end_col += cur_line_grow_char
            else:
                cur_line = end_row
                cur_line_grow_char = 0
            line = self.lines[cur_line - 1]
            self.lines[cur_line - 1] = "{}{}{}".format(line[:end_col], ")", line[end_col:])
            cur_line_grow_char += 1

            is_replace = True

        if is_replace and len(self.string_token):
            insert_idx = 0

            # 1. 找到import后面的空行
            for idx, line in enumerate(self.lines):
                try:
                    if (
                        (line.startswith("import") or line.startswith("from"))
                        and idx < len(self.lines) - 1
                        and self.lines[idx + 1] == os.linesep
                    ):
                        insert_idx = idx + 1
                        break
                except Exception as e:
                    print(e)

            # 2. 如果1中没有找到，则找个空行即可
            if not insert_idx:
                for idx, line in enumerate(self.lines):
                    if line == "\n" or not line.startswith("#"):
                        insert_idx = idx
                        break

            self.lines.insert(insert_idx, "from django.utils.translation import ugettext as _\n")
            # self.lines.insert(insert_idx,
            #                   "from kernel.utils.i18n import gettext as _ \n")

    def process(self, s):
        g = tokenize.generate_tokens(StringIO(s).readline)  # tokenize the string
        for token_type, tokval, start_at, end_at, source_line in g:
            start_at = TokenPoint(*start_at)
            end_at = TokenPoint(*end_at)
            token = Token(token_type, tokval, start_at, end_at, source_line)

            if token_type in (tokenize.NEWLINE, tokenize.NL):
                self.handle_newline(token)
            elif token_type == tokenize.STRING:
                self.handle_string(token)
            else:
                self.handle_default(token)
        self.tag_str()
        return "".join(self.lines)


class TagJSString(object):
    def __init__(self):
        pass

    def process(self, s):
        import esprima

        try:
            str_token_list = esprima.tokenize(s)
        except:
            str_token_list = []
        chinese_token_set = set()
        for token in str_token_list:
            value = token.value
            if token.type != "String" or value in chinese_token_set:
                continue
            chinese_token_set.add(value)
            if CHINESE_PATTERN.search(value):
                s = s.replace(value, u"gettext(%s)" % value)
        return s


def is_contain_chinese(content):
    if isinstance(content, str):
        try:
            content = content.decode("utf-8", "ignore")
        except:
            pass

    return CHINESE_PATTERN.search(content)


def list_dir(path, suffix, exclude_path_list=None):
    ret = []
    dirs = os.listdir(path)
    for i in dirs:
        if i.startswith(".") or i.startswith("~"):
            continue
        abs_path = os.path.join(path, i)
        if exclude_path_list and any(abs_path.startswith(i) for i in exclude_path_list):
            continue
        if i.endswith(suffix):
            ret.append(abs_path)
        elif os.path.isdir(abs_path):
            ret += list_dir(abs_path, suffix=suffix, exclude_path_list=exclude_path_list)
    return ret


def read_file(file_path):
    with open(file_path, "r") as f:
        try:
            return f.read().decode("utf-8")
        except:
            return f.read()


def write_file(file_path, content):
    with open(file_path, "w") as f:
        try:
            f.write(content.encode("utf-8"))
        except:
            f.write(content)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Find chinese string from file")
    parser.add_argument("-t", "--type", help="type of file to process, options: [python|js] default:all")
    parser.add_argument("path", help="[file|file path] to handle")
    parser.add_argument("-e", "--exclude", nargs="*", help="exclude file path")
    args = parser.parse_args()

    if os.path.isdir(args.path):
        suffix = FILE_TYPE_TO_SUFFIX.get(args.type, SUPPORT_FILE_SUFFIX)
        file_lists = list_dir(args.path, suffix=suffix, exclude_path_list=args.exclude)
    else:
        file_lists = [
            args.path,
        ]

    for each_file in file_lists:
        print("processing: %s" % (each_file))
        content = read_file(each_file)
        if each_file.endswith("py"):
            result = TagString().process(content)
        elif each_file.endswith(".js"):
            result = TagJSString().process(content)
        else:
            result = content
        write_file(each_file, result)


if __name__ == "__main__":
    main()
