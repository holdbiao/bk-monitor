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

import inspect
import logging
import os
from importlib import import_module

from django.core.management.base import BaseCommand
from django.template import engines

django_engine = engines["django"]

logger = logging.getLogger(__name__)

TEMPLATE = """# -*- coding: UTF-8 -*-

class ConfigureMixin(object):
    {% for module, methods in tree.items %}{% if module == "adapter" %}
    class adapter:
        {% for adapter_module, adapter_methods in methods.items %}
        class {{ adapter_module }}:{% for method_name, method in adapter_methods.items %}
            from {{ method.module }} import {{ method.name}} as {{ method_name }}{% endfor %}
            {% for method_name, method in adapter_methods.items %}{% if method.type == "function" %}
            {{ method_name }}: function = {{ method_name }}{% else %}
            {{ method_name }}: {{ method_name }} = ...{% endif %}{% endfor %}
            ...
        {% endfor %}
    {% else %}
    class {{ module }}:{% for method_name, method in methods.items %}
        from {{ method.module }} import {{ method.name}} as {{ method_name }}{% endfor %}
        {% for method_name, method in methods.items %}{% if method.type == "function" %}
        {{ method_name }}: function = {{ method_name }}{% else %}
        {{ method_name }}: {{ method_name }} = ...{% endif %}{% endfor %}
        ...
    {% endif %}{% endfor %}
    ...
"""


template = django_engine.from_string(TEMPLATE)


class Command(BaseCommand):
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("-p", "--path")
        parser.add_argument("-o", "--output")

    def search_attr(self, instance):
        resource_tree = {}

        for name in dir(instance):
            if name.startswith("_"):
                continue
            obj = getattr(instance, name)

            if hasattr(obj, "list_method"):
                try:
                    obj._setup()
                except Exception as err:
                    logger.exception(err)
                resource_tree[name] = {}
                for key, value in list(obj._methods.items()):
                    resource_tree[name][key] = {"name": value.__name__, "module": value.__module__, "cls": value}
                    if inspect.isfunction(value):
                        resource_tree[name][key]["type"] = "function"
                    else:
                        resource_tree[name][key]["type"] = "class"
            else:
                resource_tree[name] = self.search_attr(obj)

        return resource_tree

    def handle(self, path, output, *args, **options):
        module_name, attr_name = path.rsplit(".", 1)
        module = import_module(module_name)
        resource = getattr(module, attr_name)

        tree = self.search_attr(resource)

        if not output:
            source_file, ext = os.path.splitext(module.__file__)
            output = "%s.pyi" % source_file

        with open(output, "w+") as fp:
            fp.write(template.render({"tree": tree}))
