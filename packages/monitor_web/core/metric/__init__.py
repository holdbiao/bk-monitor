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


import six
from django.utils.module_loading import import_string

from monitor_web.core.metric.base import BaseMetricFactory


class MetricAdapter(object):
    def __init__(self):
        self.metric_factories = []

    def register_factory(self, factory):
        self.metric_factories.append(factory)

    def call_factory_method(self, func_name, *args, **kwargs):
        for metric_factory in self.metric_factories:
            func_obj = getattr(metric_factory, func_name)
            if not callable(func_obj):
                raise TypeError("Invalided Metric Factory, " "load method is required")

            yield func_obj(*args, **kwargs)

    def __call__(self, metric_id, *args, **kwargs):
        """
        metric_id: "docker.cpu_summary.cpuusage"
        string only
        """
        ret = metric_id.split(".")
        if len(ret) != 3:
            raise ValueError("invalid metric_id: %r" % metric_id)

        for metric_obj in self.call_factory_method("load", ret, *args, **kwargs):
            if metric_obj:
                break
        else:
            raise ValueError("metric_id: %r is not exist" % metric_id)

        return metric_obj

    def make_metric_conf_list(self, *args, **kwargs):
        result = []
        for metric_conf_list in self.call_factory_method("make_metric_conf_list", *args, **kwargs):
            if metric_conf_list:
                result.extend(metric_conf_list)
        return result


Metric = MetricAdapter()


def register_metric(metric_modules):
    for metric_module in metric_modules:
        if isinstance(metric_module, six.string_types):
            metric_module = import_string(metric_module)
        assert issubclass(metric_module, BaseMetricFactory), "invalid metric factory config"
        Metric.register_factory(metric_module)
