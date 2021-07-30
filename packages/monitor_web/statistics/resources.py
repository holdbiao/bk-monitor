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

from __future__ import absolute_import, unicode_literals

import logging
import time

import requests
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bkmonitor.utils.dns_resolve import resolve_domain
from core.drf_resource import Resource
from monitor_web.statistics.metrics import MetricCollector


logger = logging.getLogger(__name__)


class ResponseFormat(object):
    JSON = "json"
    PROMETHEUS = "prometheus"


class GetStatisticsDataResource(Resource):
    """
    获取统计数据
    """

    INFLUXDB_METRIC_WHITE_LIST = ["influxdb_database_numSeries"]

    class RequestSerializer(serializers.Serializer):
        namespaces = serializers.CharField(required=False, label=_("命名空间"))
        collect_interval = serializers.IntegerField(default=300, label=_("采集周期"))
        response_format = serializers.ChoiceField(
            required=False,
            default=ResponseFormat.PROMETHEUS,
            label=_("返回格式"),
            choices=[ResponseFormat.PROMETHEUS, ResponseFormat.JSON],
        )

    def fetch_influxdb_metrics(self):
        metrics = []

        domains = [d for d in settings.INFLUXDB_METRIC_HOST.split(",") if d]
        ips = []

        # 解析域名
        for domain in domains:
            resolved_ips = resolve_domain(domain)
            if not resolved_ips:
                resolved_ips = [domain]
            ips += resolved_ips

        for ip in ips:
            url = f"http://{ip}:{settings.INFLUXDB_METRIC_PORT}{settings.INFLUXDB_METRIC_URI}"

            try:
                response = requests.get(url=url)
                for line in response.text.splitlines():
                    for prefix in self.INFLUXDB_METRIC_WHITE_LIST:
                        if line.startswith(prefix):
                            metrics.append(line)
            except Exception as e:
                logger.warning("[get_statistics_data] fetch influxdb metrics error for ip (%s): %s", ip, e)

        metric_text = "\n".join(metrics)
        return metric_text

    def perform_request(self, validated_request_data):
        namespaces = validated_request_data.get("namespaces", "")
        namespaces = [ns for ns in namespaces.split(",") if ns]
        collector = MetricCollector(collect_interval=validated_request_data["collect_interval"])
        metrics = collector.collect(namespaces=namespaces, response_format=validated_request_data["response_format"])

        if validated_request_data["response_format"] == "json":
            # json格式用于运营报表，不需要返回influxdb指标
            return metrics

        try:
            begin_time = time.time()
            influxdb_metrics = self.fetch_influxdb_metrics()
            metrics += "\n" + influxdb_metrics
            logger.info(
                "[statistics_data] collect metric->[influxdb] took %s ms", int((time.time() - begin_time) * 1000)
            )
        except Exception as e:
            logger.warning("[statistics_data] fetch influxdb metrics error: %s", e)

        return metrics
