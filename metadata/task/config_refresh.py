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
import logging
import traceback

from alarm_backends.core.lock.service_lock import share_lock
from metadata import models
from metadata.utils import consul_tools

logger = logging.getLogger("metadata")


def clean_influxdb_route():
    models.InfluxDBTagInfo.clean_consul_config()
    models.InfluxDBStorage.clean_consul_config()
    models.InfluxDBClusterInfo.clean_consul_config()
    models.InfluxDBHostInfo.clean_consul_config()


@share_lock(identify="metadata_refreshInfluxdbRoute")
def refresh_influxdb_route():
    """
    实际定时任务需要操作的内容
    注意：会发现此处有很多单独的异常捕获内容，主要是为了防止其中一个系统的异常，会波及其他系统
    :return:
    """

    # 更新influxdb路由信息至consul当中
    # 顺序应该是 主机 -> 集群 -> 结果表
    try:
        for host_info in models.InfluxDBHostInfo.objects.all():
            host_info.refresh_consul_cluster_config()
            logger.debug("host->[%s] refresh consul config success." % host_info.host_name)

        models.InfluxDBClusterInfo.refresh_consul_cluster_config()
        logger.debug("influxdb cluster refresh consul config success.")

        for result_table in models.InfluxDBStorage.objects.all():
            result_table.refresh_consul_cluster_config()
            logger.debug("result_table->[%s] refresh consul config success." % result_table.table_id)
    except Exception:
        # 上述的内容对外统一是依赖consul，所以使用一个exception进行捕获
        logger.error("failed to refresh influxdb router info for->[{}]".format(traceback.format_exc()))

    # 任务完成前，更新一下version
    consul_tools.refresh_router_version()
    logger.info("influxdb router config refresh success.")

    # 更新TS结果表外部的依赖信息
    for result_table in models.InfluxDBStorage.objects.all():
        try:
            # 确认数据库已经创建
            result_table.sync_db()
            # 确保存在可用的清理策略
            result_table.ensure_rp()
            logger.debug("tsdb result_table->[{}] sync_db success.".format(result_table.table_id))
        except Exception:
            logger.error(
                "result_table->[{}] failed to sync database for->[{}]".format(
                    result_table.table_id, traceback.format_exc()
                )
            )
    # 刷新tag路由
    try:
        logger.info("start to refresh metadata tag")
        models.InfluxDBTagInfo.refresh_consul_tag_config()
    except Exception as e:
        logger.error("refresh tag failed for ->{}".format(e))

    # 清理consul信息，删除已经不存在的信息
    try:
        logger.info("start to clean influxdb route")
        clean_influxdb_route()
    except Exception as e:
        logger.error("clean route failed for ->{}".format(e))


@share_lock(identify="metadata_refreshDatasource")
def refresh_datasource():
    # 更新datasource的外部依赖 及 配置信息
    # 但是只会启用的数据源
    for datasource in models.DataSource.objects.filter(is_enable=True):
        try:
            # 2. 更新ETL及datasource的配置
            datasource.refresh_outer_config()
            logger.debug("data_id->[%s] refresh all outer success" % datasource.bk_data_id)
        except Exception:
            logger.error(
                "data_id->[{}] failed to refresh outer config for->[{}]".format(
                    datasource.bk_data_id, traceback.format_exc()
                )
            )

        # 3. 更新字段配置信息
        # data source是否可以进行更新的判断，将会在update_field_config中进行判断
        try:
            datasource.update_field_config()
            logger.info("data_id->[%s] update fields config." % datasource.bk_data_id)
        except Exception:
            logger.error(
                "data_id->[{}] failed to refresh field config for->[{}]".format(
                    datasource.bk_data_id, traceback.format_exc()
                )
            )


@share_lock(identify="metadata_refreshKafkaStorage")
def refresh_kafka_storage():
    # 确认所有kafka存储都有对应的topic
    for kafka_storage in models.KafkaStorage.objects.all():
        try:
            kafka_storage.ensure_topic()
            logger.debug("kafka storage for result_table->[{}] is ensure create.".format(kafka_storage.table_id))
        except Exception:
            logger.error(
                "kafka->[{}] failed to make sure topic exists for->[{}]".format(
                    kafka_storage.table_id, traceback.format_exc()
                )
            )


@share_lock(identify="metadata_refreshESStorage", ttl=1800)
def refresh_es_storage():
    # 遍历所有的ES存储并创建index
    for es_storage in models.ESStorage.objects.all():
        try:
            # 先预创建各个时间段的index，
            # 1. 同时判断各个预创建好的index是否字段与数据库的一致
            # 2. 也判断各个创建的index是否有大小需要切片的需要

            if not es_storage.index_exist():
                #   如果该table_id的index在es中不存在，说明要走初始化流程
                logger.info("table_id->[%s] found no index in es,will create new one", es_storage.table_id)
                es_storage.create_index_and_aliases(es_storage.slice_gap)
            else:
                # 否则走更新流程
                es_storage.update_index_and_aliases(ahead_time=es_storage.slice_gap)

            # 清理过期的index
            es_storage.clean_index_v2()

            # 重新分配索引数据
            es_storage.reallocate_index()

            logger.debug("es_storage->[{}] cron task success.".format(es_storage.table_id))
        except Exception:
            logger.info(
                "es_storage->[{}] failed to cron task for->[{}]".format(es_storage.table_id, traceback.format_exc())
            )
            continue
