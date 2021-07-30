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


import glob
import inspect
import logging
from importlib import import_module
from os.path import basename, dirname, isfile, join

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import engines
from django.utils.translation import ugettext as _

from core.errors import Error

logger = logging.getLogger(__name__)

template = engines["django"].from_string(
    """#### {{ module_description }}
| 错误码 | 错误类 | 错误名称 | 描述 |
| ------- | ------- | ------- | ------- |
{% for error in errors %}| {{ error.code }} | {{error.class_name}} | {{ error.name }} | {{ error.description }} |
{% endfor %}

"""
)


class Command(BaseCommand):
    """
    生成错误码文档
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("-o", "--output")

    @classmethod
    def get_all_errors(cls, module):
        """
        从模块中获取全部Error的子类
        :param module: 模块
        :return: list
        """
        errors = []
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isclass(obj) and issubclass(obj, Error) and Error != obj:
                errors.append(obj)
        errors.sort(key=lambda x: int(x.code))
        return errors

    @classmethod
    def create_module_document(cls, module):
        """
        根据模块生成文档
        :param module: 模块
        :return: str
        """
        error_classes = cls.get_all_errors(module)
        if not error_classes:
            return ""

        errors = []
        for error in error_classes:
            description = getattr(error, "description", "")
            description = description.lstrip()
            errors.append(
                {"name": error.name, "code": error.code, "description": description, "class_name": error.__name__}
            )

        module_description = module.__doc__ if module.__doc__ else module.__name__
        module_description = module_description.lstrip()
        return template.render({"errors": errors, "module_description": module_description})

    def handle(self, output=None, *args, **options):
        errors_modules = []

        # 从INSTALL_APPS寻找错误定义
        for app in settings.INSTALLED_APPS:
            errors_module = getattr(import_module(app), "errors", None)
            if not errors_module:
                continue
            errors_modules.append(errors_module)

        # 从指定模块中寻找错误定义
        search_paths = getattr(settings, "ERROR_SEARCH_PATH", [])

        for path in search_paths:
            module = import_module(path)
            if module.__file__.endswith("__init__.pyc"):
                files = glob.glob(join(dirname(module.__file__), "*.py"))
                sub_modules = [
                    import_module("{}.{}".format(path, basename(f)[:-3]))
                    for f in files
                    if isfile(f) and not f.endswith("__init__.py")
                ]
                errors_modules.extend(sub_modules)
            else:
                errors_modules.append(module)

        document_string = _("### 错误码文档\n\n[TOC]\n\n")
        for errors_module in errors_modules:
            document_string += self.create_module_document(errors_module)

        if not output:
            output = "errors.md"
        with open(output, "w+") as f:
            f.write(document_string.encode("utf-8"))
