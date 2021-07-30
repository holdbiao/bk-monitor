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

import arrow

from bkmonitor.utils.tag_mappings import TagMappings


class EsDsl(object):
    methods = TagMappings()

    def __init__(self, conditions, rule, dimensions):
        self.conditions = conditions or ()
        self.rule = rule
        self.dimensions = dimensions or ()

    @methods.register("match")
    def method_match_phrase(self, field, method, value):
        return dict(match_phrase={field: str(value).lower()})

    @methods.register("term")
    def method_term(self, field, method, value):
        return dict(term={field: str(value).lower()})

    @methods.register("neq")
    def method_neq(self, field, method, value):
        return dict(bool=dict(must_not=dict(term={field: str(value).lower()})))

    def method_simple_range(self, field, method, value):
        return dict(range={field: {method: str(value).lower()}})

    methods.register("gt", method_simple_range)
    methods.register("gte", method_simple_range)
    methods.register("lt", method_simple_range)
    methods.register("lte", method_simple_range)

    def _get_time_range(self, from_time, until_time):
        from_time = arrow.get(from_time)
        until_time = arrow.get(until_time)
        range = dict(
            dtEventTimeStamp={
                "from": from_time.timestamp * 1000,
                "to": until_time.timestamp * 1000,
            }
        )
        return range

    def _get_filter_condition(self, conditions, rule):
        _conditions = []
        for condition in conditions:
            field = condition.get("field")
            name = condition.get("method")
            value = condition.get("value")

            method = self.methods.get(name)
            if not method:
                continue

            _conditions.append(
                method(
                    self,
                    field=field,
                    method=name,
                    value=value,
                )
            )

        return {rule: _conditions}

    def _get_aggregations(self, dimensions=None, **kwargs):
        aggragations = {"count": {"value_count": {"field": "_index"}}}

        for dimension in dimensions:
            _aggragations = {
                dimension: {
                    "terms": {
                        "field": dimension,
                        "size": 10000,
                    }
                }
            }
            _aggragations[dimension]["aggregations"] = aggragations
            aggragations = _aggragations

        return aggragations

    def _dsl(self, from_time, until_time, table_name, **kwargs):
        filter_condition = self._get_filter_condition(
            conditions=self.conditions,
            rule=self.rule,
        )
        time_range = self._get_time_range(from_time, until_time)

        body = {
            "size": 0,
            "query": {"bool": {"must": [{"bool": filter_condition}, {"range": time_range}]}},
        }

        aggregations = self._get_aggregations(self.dimensions)
        if aggregations:
            body["aggregations"] = aggregations

        dsl = dict(index=table_name, body=body)

        return dsl

    def dsl(self, from_time, until_time, table_name, **kwargs):
        return self._dsl(from_time, until_time, table_name, **kwargs)
