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

from django.contrib import admin

from metadata import models

# Register your models here.


# influxdb 路由配置信息
class InfluxdbClusterAdmin(admin.ModelAdmin):
    search_fields = ("host_name", "cluster_name")
    list_filter = ("host_name", "cluster_name")
    list_display = ("host_name", "cluster_name")


class InfluxdbHostAdmin(admin.ModelAdmin):
    search_fields = ("host_name", "domain_name")
    list_filter = ("host_name", "domain_name")
    list_display = ("host_name", "domain_name", "port", "description")


class InfluxdbTagAdmin(admin.ModelAdmin):
    search_fields = ("database", "measurement", "cluster_name")
    list_display = ("database", "measurement", "cluster_name", "tag_name", "tag_value", "host_list")


class InfluxDBStorageAdmin(admin.ModelAdmin):
    search_fields = ("table_id", "database", "real_table_name")
    list_display = (
        "table_id",
        "database",
        "real_table_name",
        "proxy_cluster_name",
        "storage_cluster_id",
        "partition_tag",
    )
    list_filter = ("storage_cluster_id", "proxy_cluster_name")


class KafkaStorageAdmin(admin.ModelAdmin):
    search_fields = (
        "table_id",
        "topic",
    )
    list_display = ("table_id", "topic", "partition", "storage_cluster_id")
    list_filter = ("storage_cluster_id",)


class RedisStorageAdmin(admin.ModelAdmin):
    search_fields = ("table_id", "key")
    list_display = ("table_id", "command", "key", "storage_cluster_id")
    list_filter = ("storage_cluster_id", "command")


class BkDataStorageAdmin(admin.ModelAdmin):
    list_display = ("table_id", "raw_data_id", "etl_json_config", "bk_data_result_table_id")
    search_fields = ("table_id", "bk_data_result_table_id")


class CustomReportSubscriptionConfigAdmin(admin.ModelAdmin):
    search_fields = ("bk_biz_id", "subscription_id")
    list_display = ("bk_biz_id", "subscription_id", "config")


class PingServerSubscriptionConfigAdmin(admin.ModelAdmin):
    search_fields = ("bk_cloud_id", "subscription_id")
    list_display = ("bk_cloud_id", "subscription_id", "config")


class DataSourceAdmin(admin.ModelAdmin):
    search_fields = ("bk_data_id", "data_name")
    list_display = ("bk_data_id", "data_name", "transfer_cluster_id")


class ESStorageAdmin(admin.ModelAdmin):
    search_fields = ("table_id",)
    list_display = (
        "table_id",
        "slice_size",
        "slice_gap",
        "retention",
        "index_settings",
        "mapping_settings",
        "storage_cluster_id",
    )


class EventGroupAdmin(admin.ModelAdmin):
    list_display = (
        "event_group_id",
        "event_group_name",
        "bk_data_id",
        "bk_biz_id",
        "table_id",
        "last_modify_user",
        "last_modify_time",
    )
    search_fields = ("event_group_id", "event_group_name", "bk_data_id", "table_id")
    list_filter = ("bk_biz_id",)


class TimeSeriesGroupAdmin(admin.ModelAdmin):
    list_display = (
        "time_series_group_id",
        "time_series_group_name",
        "bk_data_id",
        "bk_biz_id",
        "table_id",
        "last_modify_user",
        "last_modify_time",
    )
    search_fields = ("time_series_group_id", "time_series_group_name", "bk_data_id", "table_id")
    list_filter = ("bk_biz_id",)


class ResultTableAdmin(admin.ModelAdmin):
    list_display = ("table_id", "table_name_zh", "bk_biz_id", "label", "last_modify_user", "last_modify_time")
    search_fields = ("table_id", "table_name_zh", "bk_biz_id")
    list_filter = ("bk_biz_id",)


class ResultTableOptionAdmin(admin.ModelAdmin):
    list_display = ("table_id", "name", "value_type", "value", "creator", "create_time")
    search_fields = ("table_id", "name")


class ClusterInfoAdmin(admin.ModelAdmin):
    list_display = (
        "cluster_id",
        "cluster_name",
        "cluster_type",
        "registered_system",
        "is_register_to_gse",
        "gse_stream_to_id",
        "last_modify_user",
        "last_modify_time",
    )
    search_fields = ("cluster_name", "cluster_type", "registered_system")
    list_filter = ("cluster_type", "registered_system")


class KafkaTopicInfoAdmin(admin.ModelAdmin):
    list_display = ("bk_data_id", "topic", "partition")
    search_fields = ("topic",)


class DataSourceOptionAdmin(admin.ModelAdmin):
    list_display = ("bk_data_id", "name", "value_type", "value", "creator", "create_time")
    search_fields = ("bk_data_id", "name")


class DataSourceResultTableAdmin(admin.ModelAdmin):
    list_display = ("bk_data_id", "table_id", "creator", "create_time")
    search_fields = ("table_id",)


admin.site.register(models.InfluxDBClusterInfo, InfluxdbClusterAdmin)
admin.site.register(models.InfluxDBHostInfo, InfluxdbHostAdmin)
admin.site.register(models.InfluxDBStorage, InfluxDBStorageAdmin)
admin.site.register(models.KafkaStorage, KafkaStorageAdmin)
admin.site.register(models.BkDataStorage, BkDataStorageAdmin)
admin.site.register(models.RedisStorage, RedisStorageAdmin)
admin.site.register(models.ESStorage, ESStorageAdmin)
admin.site.register(models.EventGroup, EventGroupAdmin)
admin.site.register(models.TimeSeriesGroup, TimeSeriesGroupAdmin)
admin.site.register(models.CustomReportSubscriptionConfig, CustomReportSubscriptionConfigAdmin)
admin.site.register(models.PingServerSubscriptionConfig, PingServerSubscriptionConfigAdmin)
admin.site.register(models.ClusterInfo, ClusterInfoAdmin)
admin.site.register(models.KafkaTopicInfo, KafkaTopicInfoAdmin)
admin.site.register(models.DataSource, DataSourceAdmin)
admin.site.register(models.DataSourceOption, DataSourceOptionAdmin)
admin.site.register(models.DataSourceResultTable, DataSourceResultTableAdmin)
admin.site.register(models.InfluxDBTagInfo, InfluxdbTagAdmin)
admin.site.register(models.ResultTable, ResultTableAdmin)
admin.site.register(models.ResultTableOption, ResultTableOptionAdmin)
