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

import six
from schematics import Model, types


class BaseMetric(Model):

    # 表名
    result_table_id = types.StringType(required=True)
    # 指标字段名
    item = types.StringType(required=True)
    # 指标字段展示
    item_display = types.StringType(required=True)
    # 指标描述
    description = types.StringType(required=True)
    # 转换后单位
    conversion_unit = types.StringType(default="")
    # 转换除数
    conversion = types.FloatType(default=1.0)
    # 展示维度（页面图表展示）
    dimension_field = types.StringType(default="")
    # 指标分类描述
    category_display = types.StringType(required=True)
    # metric_id
    metric_id = types.StringType(required=True)
    # table_name
    table_name = types.StringType(required=True)
    # 采集周期
    collect_interval = types.IntType(required=True)

    def __repr__(self):
        return self.metric_id

    def get_category(self):
        raise NotImplementedError("get_category need implemented")


class BaseMetricFactory(six.with_metaclass(abc.ABCMeta, object)):
    @classmethod
    def load(cls, parsed_metric_id, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def make_metric_conf_list(cls, *args, **kwargs):
        raise NotImplementedError
