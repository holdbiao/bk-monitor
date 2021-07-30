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
from django.utils.translation import ugettext_lazy as _lazy
from rest_framework import serializers

from bkmonitor.utils.cache import CacheType
from core.drf_resource.contrib.api import APIResource


class GseBaseResource(six.with_metaclass(abc.ABCMeta, APIResource)):
    base_url = "%s/api/c/compapi/v2/gse/" % settings.BK_PAAS_INNER_HOST
    module_name = "gse"


####################################
#           Stream to              #
####################################
class StorageAddressSerializer(serializers.Serializer):
    ip = serializers.CharField(required=True, label=_lazy("接收端IP或域名"))
    port = serializers.IntegerField(required=True, label=_lazy("接收端PORT"))


class AddStreamTo(GseBaseResource):
    """
    新增数据接收端配置
    """

    action = "config_add_streamto/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class MetadataSerializer(serializers.Serializer):
            label = serializers.DictField(required=False, label=_lazy("可选信息"))
            plat_name = serializers.CharField(required=True, label=_lazy("接收端配置所属的平台"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        class StreamToSerializer(serializers.Serializer):
            class KafkaSerializer(serializers.Serializer):
                storage_address = serializers.ListField(
                    required=True, label=_lazy("kafka的地址和端口配置"), child=StorageAddressSerializer()
                )

            class RedisSerializer(serializers.Serializer):
                storage_address = serializers.ListField(
                    required=True, label=_lazy("redis的地址和端口配置"), child=StorageAddressSerializer()
                )
                passwd = serializers.CharField(required=False, label=_lazy("redis的密码"))
                master_name = serializers.CharField(required=False, label=_lazy("redis sentinel mode的master name"))

            class PulsarSerializer(serializers.Serializer):
                storage_address = serializers.ListField(
                    required=True, label=_lazy("pulsar的地址和端口配置"), child=StorageAddressSerializer()
                )
                token = serializers.CharField(required=False, label=_lazy("pulsar的鉴权token"))

            name = serializers.CharField(required=True, label=_lazy("接收端名称"))
            report_mode = serializers.ChoiceField(
                required=True, choices=["kafka", "redis", "pulsar", "file"], label=_lazy("接收端类型")
            )
            # report_mode:file
            data_log_path = serializers.CharField(required=False, label=_lazy("文件路径"))
            # report_mode:kafka
            kafka = KafkaSerializer(required=False, label=_lazy("kafka接收端配置"))
            # report_mode:redis
            redis = RedisSerializer(required=False, label=_lazy("redis接收端配置"))
            # report_mode:pulsar
            pulsar = PulsarSerializer(required=False, label=_lazy("pulsar接收端配置"))

        metadata = MetadataSerializer(required=True, label=_lazy("所属平台的源信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))
        stream_to = StreamToSerializer(required=True, label=_lazy("接收端详细配置"))


class UpdateStreamTo(GseBaseResource):
    """
    修改数据接收端配置
    """

    action = "config_update_streamto/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            stream_to_id = serializers.IntegerField(required=True, label=_lazy("接收端配置的ID"))
            plat_name = serializers.CharField(required=True, label=_lazy("接收端配置所属的平台"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        class SpecificationSerializer(serializers.Serializer):
            class StreamToSerializer(serializers.Serializer):
                class KafkaSerializer(serializers.Serializer):
                    storage_address = serializers.ListField(
                        required=True, label=_lazy("kafka的地址和端口配置"), child=StorageAddressSerializer()
                    )

                class RedisSerializer(serializers.Serializer):
                    storage_address = serializers.ListField(
                        required=True, label=_lazy("redis的地址和端口配置"), child=StorageAddressSerializer()
                    )
                    passwd = serializers.CharField(required=False, label=_lazy("redis的密码"))
                    master_name = serializers.CharField(required=False, label=_lazy("redis sentinel mode的master name"))

                class PulsarSerializer(serializers.Serializer):
                    storage_address = serializers.ListField(
                        required=True, label=_lazy("pulsar的地址和端口配置"), child=StorageAddressSerializer()
                    )
                    token = serializers.CharField(required=False, label=_lazy("pulsar的鉴权token"))

                name = serializers.CharField(required=True, label=_lazy("接收端名称"))
                report_mode = serializers.ChoiceField(
                    required=True, choices=["kafka", "redis", "pulsar", "file"], label=_lazy("接收端类型")
                )
                # report_mode:file
                data_log_path = serializers.CharField(required=False, label=_lazy("文件路径"))
                # report_mode:kafka
                kafka = KafkaSerializer(required=False, label=_lazy("kafka接收端配置"))
                # report_mode:redis
                redis = RedisSerializer(required=False, label=_lazy("redis接收端配置"))
                # report_mode:pulsar
                pulsar = PulsarSerializer(required=False, label=_lazy("pulsar接收端配置"))

            stream_to = StreamToSerializer(required=True, label=_lazy("接收端详细配置"))

        condition = ConditionSerializer(required=True, label=_lazy("修改接口端配置条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))
        specification = SpecificationSerializer(required=True, label=_lazy("接收端配置信息"))


class DeleteStreamTo(GseBaseResource):
    """
    删除数据接收端配置
    """

    action = "config_delete_streamto/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            stream_to_id = serializers.IntegerField(required=True, label=_lazy("接收端配置的ID"))
            plat_name = serializers.CharField(required=True, label=_lazy("接收端配置所属的平台"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        condition = ConditionSerializer(required=True, label=_lazy("修改接口端配置条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))


class QueryStreamTo(GseBaseResource):
    """
    查询数据接收端配置
    """

    action = "config_query_streamto/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            plat_name = serializers.CharField(required=True, label=_lazy("接收端配置所属的平台"))
            stream_to_id = serializers.IntegerField(required=False, label=_lazy("接收端配置的ID"))
            label = serializers.DictField(required=False, label=_lazy("可选信息"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        condition = ConditionSerializer(required=True, label=_lazy("修改接口端配置条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))


####################################
#           Route Info             #
####################################
class AddRoute(GseBaseResource):
    """
    注册路由配置
    """

    action = "config_add_route/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class MetadataSerializer(serializers.Serializer):
            plat_name = serializers.CharField(required=True, label=_lazy("路由所属的平台"))
            label = serializers.DictField(required=False, label=_lazy("可选信息"))
            channel_id = serializers.IntegerField(required=False, label=_lazy("路由ID"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        class RouteInfoSerializer(serializers.Serializer):
            class StreamToSerializer(serializers.Serializer):
                class KafkaStorageSerializer(serializers.Serializer):
                    topic_name = serializers.CharField(required=True, label=_lazy("kafka的Topic信息"))
                    data_set = serializers.CharField(required=False, label=_lazy("兼容字段，数据集名称"))
                    biz_id = serializers.IntegerField(required=False, label=_lazy("兼容字段，业务ID"))
                    partition = serializers.IntegerField(required=False, label=_lazy("Topic的分区信息"))

                class RedisStorageSerializer(serializers.Serializer):
                    channel_name = serializers.CharField(required=True, label=_lazy("发布订阅Key"))
                    data_set = serializers.CharField(required=False, label=_lazy("兼容字段，数据集名称"))
                    biz_id = serializers.IntegerField(required=False, label=_lazy("兼容字段，业务ID"))

                class PulsarStorageSerializer(serializers.Serializer):
                    name = serializers.CharField(required=True, label=_lazy("Pulsar的Topic"))
                    tenant = serializers.CharField(required=False, label=_lazy("tenant名称"))
                    namespace = serializers.CharField(required=False, label=_lazy("Pulsar的namespace名称"))

                stream_to_id = serializers.IntegerField(required=True, label=_lazy("数据接收端配置ID"))
                kafka = KafkaStorageSerializer(required=False, label=_lazy("Kafka存储信息"))
                redis = RedisStorageSerializer(required=False, label=_lazy("Redis存储信息"))
                pulsar = PulsarStorageSerializer(required=False, label=_lazy("Pulsar存储信息"))

            name = serializers.CharField(required=True, label=_lazy("路由名称"))
            stream_to = StreamToSerializer(required=True, label=_lazy("数据接收端配置信息"))
            filter_name_and = serializers.ListField(required=False, label=_lazy("与条件"), child=serializers.CharField())
            filter_name_or = serializers.ListField(required=False, label=_lazy("或条件"), child=serializers.CharField())

        class StreamFilterInfoSerializer(serializers.Serializer):
            name = serializers.CharField(required=True, label=_lazy("filter名字"))
            field_index = serializers.IntegerField(required=True, label=_lazy("字段索引"))
            field_data_type = serializers.ChoiceField(
                required=True, label=_lazy("数据类型"), choices=["int", "string", "bytes"]
            )
            field_data_value = serializers.CharField(required=True, label=_lazy("数据值"))
            field_separator = serializers.CharField(required=False, label=_lazy("分隔符"))
            field_in = serializers.ChoiceField(
                required=False, default="protocol", label=_lazy("数据来源协议还是原始数据"), choices=["protocol", "data"]
            )

        metadata = MetadataSerializer(required=True, label=_lazy("所属平台的源信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))
        route = serializers.ListField(required=False, label=_lazy("路由入库配置"), child=RouteInfoSerializer())
        stream_filters = serializers.ListField(required=False, label=_lazy("过滤规则配置"))


class UpdateRoute(GseBaseResource):
    """
    修改路由配置
    """

    action = "config_update_route/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            channel_id = serializers.IntegerField(required=True, label=_lazy("路由ID"))
            plat_name = serializers.CharField(required=True, label=_lazy("路由所属的平台"))
            label = serializers.DictField(required=False, label=_lazy("可选信息"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        class SpecificationSerializer(serializers.Serializer):
            class RouteInfoSerializer(serializers.Serializer):
                class StreamToSerializer(serializers.Serializer):
                    class KafkaStorageSerializer(serializers.Serializer):
                        topic_name = serializers.CharField(required=True, label=_lazy("kafka的Topic信息"))
                        data_set = serializers.CharField(required=False, label=_lazy("兼容字段，数据集名称"))
                        biz_id = serializers.IntegerField(required=False, label=_lazy("兼容字段，业务ID"))
                        partition = serializers.IntegerField(required=False, label=_lazy("Topic的分区信息"))

                    class RedisStorageSerializer(serializers.Serializer):
                        channel_name = serializers.CharField(required=True, label=_lazy("发布订阅Key"))
                        data_set = serializers.CharField(required=False, label=_lazy("兼容字段，数据集名称"))
                        biz_id = serializers.IntegerField(required=False, label=_lazy("兼容字段，业务ID"))

                    class PulsarStorageSerializer(serializers.Serializer):
                        name = serializers.CharField(required=True, label=_lazy("Pulsar的Topic"))
                        tenant = serializers.CharField(required=False, label=_lazy("tenant名称"))
                        namespace = serializers.CharField(required=False, label=_lazy("Pulsar的namespace名称"))

                    stream_to_id = serializers.IntegerField(required=True, label=_lazy("数据接收端配置ID"))
                    kafka = KafkaStorageSerializer(required=False, label=_lazy("Kafka存储信息"))
                    redis = RedisStorageSerializer(required=False, label=_lazy("Redis存储信息"))
                    pulsar = PulsarStorageSerializer(required=False, label=_lazy("Pulsar存储信息"))

                name = serializers.CharField(required=True, label=_lazy("路由名称"))
                stream_to = StreamToSerializer(required=True, label=_lazy("数据接收端配置信息"))
                filter_name_and = serializers.ListField(
                    required=False, label=_lazy("与条件"), child=serializers.CharField()
                )
                filter_name_or = serializers.ListField(
                    required=False, label=_lazy("或条件"), child=serializers.CharField()
                )

            class StreamFilterInfoSerializer(serializers.Serializer):
                name = serializers.CharField(required=True, label=_lazy("filter名字"))
                field_index = serializers.IntegerField(required=True, label=_lazy("字段索引"))
                field_data_type = serializers.ChoiceField(
                    required=True, label=_lazy("数据类型"), choices=["int", "string", "bytes"]
                )
                field_data_value = serializers.CharField(required=True, label=_lazy("数据值"))
                field_separator = serializers.CharField(required=False, label=_lazy("分隔符"))
                field_in = serializers.ChoiceField(
                    required=False, default="protocol", label=_lazy("数据来源协议还是原始数据"), choices=["protocol", "data"]
                )

            route = serializers.ListField(required=False, label=_lazy("路由入库配置"), child=RouteInfoSerializer())
            stream_filters = serializers.ListField(required=False, label=_lazy("过滤规则配置"))

        condition = ConditionSerializer(required=True, label=_lazy("修改路由条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作人配置"))
        specification = SpecificationSerializer(required=True, label=_lazy("路由信息"))


class DeleteRoute(GseBaseResource):
    """
    删除路由配置
    """

    action = "config_delete_route/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            channel_id = serializers.IntegerField(required=True, label=_lazy("路由ID"))
            plat_name = serializers.CharField(required=True, label=_lazy("路由所属的平台"))
            label = serializers.DictField(required=False, label=_lazy("可选信息"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))
            method = serializers.ChoiceField(required=True, label=_lazy("指定删除方式"), choices=["all", "specification"])

        class SpecificationSerializer(serializers.Serializer):
            route = serializers.ListField(required=False, label=_lazy("路由名称列表"), child=serializers.CharField())
            stream_filters = serializers.ListField(
                required=False, label=_lazy("过滤条件名称列表"), child=serializers.CharField()
            )

        condition = ConditionSerializer(required=True, label=_lazy("条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作配置"))
        specification = SpecificationSerializer(required=False, label=_lazy("指定待删除的配置名称"))


class QueryRoute(GseBaseResource):
    """
    查询路由配置
    """

    action = "config_query_route/"
    method = "POST"

    class RequestSerializer(serializers.Serializer):
        class ConditionSerializer(serializers.Serializer):
            channel_id = serializers.IntegerField(required=True, label=_lazy("路由ID"))
            plat_name = serializers.CharField(required=False, label=_lazy("路由所属的平台"))
            label = serializers.DictField(required=False, label=_lazy("可选信息"))

        class OperationSerializer(serializers.Serializer):
            operator_name = serializers.CharField(required=True, label=_lazy("API调用者"))

        condition = ConditionSerializer(required=True, label=_lazy("条件信息"))
        operation = OperationSerializer(required=True, label=_lazy("操作配置"))


class GetAgentStatus(GseBaseResource):
    """
    主机查询接口
    """

    action = "get_agent_status"
    method = "POST"
    backend_cache_type = CacheType.GSE

    class RequestSerializer(serializers.Serializer):
        class HostSerializer(serializers.Serializer):
            ip = serializers.IPAddressField(label=_lazy("IP地址"))
            bk_cloud_id = serializers.IntegerField(label=_lazy("云区域ID"))

        hosts = HostSerializer(label=_lazy("主机列表"), many=True)
        bk_supplier_account = serializers.IntegerField(label=_lazy("开发商账号"), default="0")


class GetProcStatus(GseBaseResource):
    """
    主机查询接口
    """

    action = "get_proc_status"
    method = "POST"
    backend_cache_type = CacheType.GSE

    class RequestSerializer(serializers.Serializer):
        class HostSerializer(serializers.Serializer):
            ip = serializers.IPAddressField(label=_lazy("IP地址"))
            bk_cloud_id = serializers.IntegerField(label=_lazy("云区域ID"))

        class MetaSerializer(serializers.Serializer):
            class LabelSerializer(serializers.Serializer):
                proc_name = serializers.CharField(label=_lazy("进程名称"))

            namespace = serializers.CharField(label=_lazy("命名空间"))
            name = serializers.CharField(label=_lazy("进程名"))
            labels = LabelSerializer(label=_lazy("标签信息"))

        namespace = serializers.CharField(label=_lazy("命名空间"))
        hosts = HostSerializer(label=_lazy("主机列表"), many=True)
        meta = MetaSerializer(label=_lazy("元信息"))
