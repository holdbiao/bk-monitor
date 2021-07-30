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
import json
import logging
from datetime import datetime, timedelta
from typing import List

import arrow
from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import get_current_timezone_name

from bkmonitor.data_source import load_data_source
from constants.data_source import DataSourceLabel, DataTypeLabel
from core.drf_resource import Resource, resource
from monitor_web.data_explorer.resources import GetGraphQueryConfig

logger = logging.getLogger(__name__)


class LogQueryResource(Resource):
    """
    日志数据查询
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_("业务ID"))
        data_source_label = serializers.CharField(label=_("数据来源"))
        data_type_label = serializers.CharField(label=_("数据类型"))

        query_string = serializers.CharField(default="", allow_blank=True)
        index_set_id = serializers.CharField(label=_("结果表ID"))
        where = serializers.ListField(label=_("过滤条件"), default=lambda: [])
        filter_dict = serializers.DictField(default=lambda: {})

        start_time = serializers.IntegerField(required=False, label=_("开始时间"))
        end_time = serializers.IntegerField(required=False, label=_("结束时间"))
        limit = serializers.IntegerField(label=_("查询条数"), default=10)

    def perform_request(self, params) -> List:
        if "start_time" not in params or "end_time" not in params:
            params["end_time"] = int(datetime.now().timestamp())
            params["start_time"] = int((datetime.now() - timedelta(hours=1)).timestamp())

        params["start_time"] *= 1000
        params["end_time"] *= 1000
        params["where"] = GetGraphQueryConfig.create_where_with_dimensions(params["where"], params["filter_dict"])

        time_field = None
        # 查询日志平台关键字时间字段
        if (params["data_source_label"], params["data_type_label"]) == (
            DataSourceLabel.BK_LOG_SEARCH,
            DataTypeLabel.LOG,
        ):
            try:
                result = resource.strategies.get_index_set_list(
                    bk_biz_id=params["bk_biz_id"], index_set_id=params["index_set_id"]
                )
                if result["metric_list"]:
                    time_field = result["metric_list"][0]["extend_fields"].get("time_field") or None
            except Exception as e:
                logger.exception(e)

        data_source_class = load_data_source(params["data_source_label"], params["data_type_label"])
        data_source = data_source_class(
            table=params["index_set_id"],
            index_set_id=params["index_set_id"],
            where=params["where"],
            query_string=params["query_string"],
            filter_dict=params["filter_dict"],
            time_field=time_field,
        )
        records, _ = data_source.query_log(
            start_time=params["start_time"], end_time=params["end_time"], limit=params["limit"]
        )

        result = []
        for record in records:
            if params["data_source_label"] in (DataSourceLabel.BK_MONITOR_COLLECTOR, DataSourceLabel.CUSTOM):
                content = record["event"]["content"]
            elif params["data_source_label"] == DataSourceLabel.BK_LOG_SEARCH and "log" in record:
                content = record["log"]
            else:
                content = json.dumps(record, ensure_ascii=False)
            time_value = record.get(data_source.time_field)

            # 带毫秒的时间戳处理
            try:
                time_value = int(time_value)
                if len(str(time_value)) > 10:
                    time_value = time_value // 1000
            except (TypeError, ValueError):
                pass

            # 将时间字段序列化
            try:
                _time = arrow.get(time_value).replace(tzinfo=get_current_timezone_name())
            except Exception as e:
                logger.error(f"parse time error: {time_value}")
                logger.exception(e)
                _time = arrow.now(tz=get_current_timezone_name())

            result.append({"time": _time.isoformat(), "content": content})
        return result
