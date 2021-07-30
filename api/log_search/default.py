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
from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy
from rest_framework import serializers

from bkmonitor.utils.cache import CacheType
from core.drf_resource import APIResource


class LogSearchAPIGWResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url_statement = None
    base_url = settings.BKLOGSEARCH_API_BASE_URL or "%s/api/c/compapi/v2/bk_log/" % settings.BK_PAAS_INNER_HOST

    # 模块名
    module_name = "bk_log"

    @property
    def label(self):
        return self.__doc__


class ESQuerySearchResource(LogSearchAPIGWResource):
    """
    日志查询接口
    """

    action = "esquery_search/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        # 下面字段，二选一
        # index_set_id 和 indices,scenario_id,storage_cluster_id,time_field 任选一种
        index_set_id = serializers.IntegerField(required=False, label=_lazy("索引集ID"))

        indices = serializers.CharField(required=False, label=_lazy("索引列表"))
        # ES接入场景(非必填） 默认为log，蓝鲸计算平台：bkdata 原生ES：es 日志采集：log
        scenario_id = serializers.CharField(required=False, label=_lazy("ES接入场景"))
        # 当scenario_id为es或log时候需要传入
        storage_cluster_id = serializers.IntegerField(required=False, label=_lazy("存储集群"))
        time_field = serializers.CharField(required=False, label=_lazy("时间字段"))

        start_time = serializers.CharField(required=False, label=_lazy("开始时间"))
        end_time = serializers.CharField(required=False, label=_lazy("结束时间"))

        #  时间标识符符["15m", "30m", "1h", "4h", "12h", "1d", "customized"]
        # （非必填，默认15m）
        time_range = serializers.CharField(required=False, label=_lazy("时间标识符"))

        # 搜索语句query_string(非必填，默认为*)
        query_string = serializers.CharField(required=False, label=_lazy("搜索语句"))

        # 搜索过滤条件（非必填，默认为没有过滤，默认的操作符是is） 操作符支持 is、is one of、is not、is not one of
        filter = serializers.ListField(required=False, label=_lazy("搜索过滤条件"))

        # 起始位置（非必填，类似数组切片，默认为0）
        start = serializers.IntegerField(required=False, label=_lazy("起始位置"))

        # 条数（非必填，控制返回条目，默认为500）
        size = serializers.IntegerField(required=False, label=_lazy("条数"))
        aggs = serializers.DictField(required=False, label=_lazy("ES的聚合条件"))
        highlight = serializers.DictField(required=False, label=_lazy("高亮参数"))
        sort_list = serializers.ListField(required=False, label=_lazy("排序"))

        # 默认所有的日志检索查询均不包含end_time那一时刻，避免窗口数据不准
        include_end_time = serializers.BooleanField(required=False, label=_lazy("end_time__gt or gte"), default=False)


class SearchIndexFieldsResource(LogSearchAPIGWResource):
    """
    索引集field
    """

    method = "GET"
    action = ""

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        index_set_id = serializers.IntegerField(required=True, label=_lazy("索引集ID"))

    def get_request_url(self, validated_request_data):
        """
        重写父类方法,获取最终请求的url
        """
        index_set_id = validated_request_data["index_set_id"]
        return self.base_url.rstrip("/") + "/search_index_set/" + str(index_set_id) + "/fields"


class SearchIndexSetResource(LogSearchAPIGWResource):
    """
    索引集列表
    """

    action = "/search_index_set/"
    method = "GET"
    backend_cache_type = CacheType.LOG_SEARCH

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))


class OperatorsResource(LogSearchAPIGWResource):
    """
    获取可支持查询方法
    """

    action = "/search_index_set/operators/"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))


class ListCollectorsByHost(LogSearchAPIGWResource):
    """
    获取主机采集项列表
    """

    action = "/databus_collectors/list_collectors_by_host/"
    method = "GET"

    class RequestSerializer(serializers.Serializer):
        bk_host_innerip = serializers.CharField(required=True, label=_lazy("主机IP"))
        bk_cloud_id = serializers.IntegerField(required=False, label=_lazy("云区域ID"), default=0, allow_null=True)
        bk_biz_id = serializers.IntegerField(required=True, help_text=_lazy("业务ID"))
