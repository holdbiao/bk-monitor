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
import time
import datetime
import json
import logging
import re
import traceback

import arrow
import curator
import elasticsearch5
import influxdb
import requests
from django.db import models
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from django.conf import settings

from bkmonitor.dataflow import auth
from bkmonitor.dataflow.task.cmdblevel import CMDBPrepareAggregateTask
from bkmonitor.dataflow.task.downsample import StatisticTask
from bkmonitor.dataflow.task.filtertime import FilterUnknownTimeTask
from bkmonitor.utils.common_utils import to_bk_data_rt_id, gen_bk_data_rt_id_without_biz_id
from bkmonitor.utils.db.fields import AESTextField, JsonField
from core.drf_resource import api
from metadata import config
from metadata.utils import consul_tools, golang_time_format, influxdb_tools
from metadata.utils.curator import IndexList

from .influxdb_cluster import InfluxDBClusterInfo, InfluxDBHostInfo

logger = logging.getLogger("metadata")

ResultTableField = None
ResultTableFieldOption = None
ResultTable = None
EventGroup = None


class ClusterInfo(models.Model):
    """
    集群信息配置
    此处的集群信息，主要是指对于外部使用监控kafka集群或者influxDB-proxy集群的信息
    如果需要看到influxDB-proxy后面的实际集群信息，请看InfluxDBClusterInfo记录
    """

    TYPE_INFLUXDB = "influxdb"
    TYPE_KAFKA = "kafka"
    TYPE_REDIS = "redis"
    TYPE_BKDATA = "bkdata"
    TYPE_ES = "elasticsearch"

    CLUSTER_TYPE_CHOICES = (
        (TYPE_INFLUXDB, "influxDB"),
        (TYPE_KAFKA, "kafka"),
        (TYPE_REDIS, "redis"),
        (TYPE_ES, "elasticsearch"),
    )

    # 默认注册系统名
    DEFAULT_REGISTERED_SYSTEM = "_default"

    cluster_id = models.AutoField(_("集群ID"), primary_key=True)
    # 集群中文名，便于管理员维护
    cluster_name = models.CharField(_("集群名称"), max_length=128, unique=True)
    cluster_type = models.CharField(_("集群类型"), max_length=32, db_index=True)
    domain_name = models.CharField(_("集群域名"), max_length=128)
    port = models.IntegerField(_("端口"))
    description = models.CharField(_("集群备注说明信息"), max_length=256)
    # 是否默认使用的集群
    # 当用户尝试使用该类型的集群时，且没有指定集群ID，则会优先使用默认集群
    is_default_cluster = models.BooleanField(_("是否默认集群"))
    # 用户名及密码配置
    username = models.CharField(_("用户名"), max_length=64, default="")
    password = AESTextField(_("密码"), max_length=128, default="")
    version = models.CharField(_("存储集群版本"), max_length=64, default=None, null=True)
    # 自定义标签信息，此处存储的内容是格式化数据，供机器读写使用
    custom_option = models.TextField(_("自定义标签"), default="")
    # 供部分http协议连接方案的存储使用，配置可以为http或者https等
    schema = models.CharField(_("访问协议"), max_length=32, default=None, null=True)
    is_ssl_verify = models.BooleanField(_("SSL验证是否强验证"), default=False)
    # 描述该存储集群被何系统使用
    registered_system = models.CharField(_("注册来源系统"), default=DEFAULT_REGISTERED_SYSTEM, max_length=128)

    # GSE注册相关
    # 是否需要往GSE注册
    is_register_to_gse = models.BooleanField(verbose_name=_("是否需要往GSE注册"), default=False)
    gse_stream_to_id = models.IntegerField(verbose_name=_("GSE接收端配置ID"), default=-1)

    # 创建和修改信息
    creator = models.CharField(_("创建者"), default="system", max_length=255)
    create_time = models.DateTimeField(_("创建时间"), auto_now_add=True)
    last_modify_user = models.CharField(_("最后更新者"), max_length=32, default="system")
    last_modify_time = models.DateTimeField(_("最后更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("集群配置信息")
        verbose_name_plural = _("集群配置信息")

    @property
    def consul_config(self):
        """
        返回consul配置，字典
        :return: {
            "cluster_config": {
                "domain_name": self.mq_cluster.domain_name,
                "port": self.mq_cluster.port,
            },
            "cluster_type": self.mq_cluster.cluster_type
        }
        """

        return {
            "cluster_config": {
                "domain_name": self.domain_name,
                "port": self.port,
                "schema": self.schema,
                "is_ssl_verify": self.is_ssl_verify,
                "cluster_id": self.cluster_id,
                "cluster_name": self.cluster_name,
                "version": self.version,
                "custom_option": self.custom_option,
                "registered_system": self.registered_system,
                "creator": self.creator,
                "create_time": arrow.get(self.create_time).timestamp,
                "last_modify_user": self.last_modify_user,
                "last_modify_time": arrow.get(self.last_modify_time).timestamp,
                "is_default_cluster": self.is_default_cluster,
            },
            "cluster_type": self.cluster_type,
            "auth_info": {"password": self.password, "username": self.username},
        }

    @classmethod
    @atomic(config.DATABASE_CONNECTION_NAME)
    def create_cluster(
        cls,
        cluster_name,
        cluster_type,
        domain_name,
        port,
        registered_system,
        operator,
        description="",
        username="",
        password="",
        version="",
        custom_option="",
        schema="",
        is_ssl_verify=False,
    ):
        """
        创建一个存储集群信息
        :param cluster_name: 集群名
        :param cluster_type: 集群类型
        :param domain_name: 集群域名，也可以提供集群IP
        :param port: 集群端口
        :param operator: 创建者
        :param description: 集群描述内容，可以为空
        :param username: 用户名，用于身份验证（如果有）
        :param password: 密码，用于身份验证（如果有）
        :param version: 集群版本信息
        :param custom_option: 自定义标签
        :param schema: 通信协议，可以提供https或http的差异
        :param is_ssl_verify: 是否需要强制验证SSL
        :param registered_system: 注册来源系统
        :return: clusterInfo object
        """

        # 1. 判断请求的数据是否有冲突
        # 基本数据校验
        if cls.objects.filter(cluster_name=cluster_name).exists():
            logger.error(
                "reg_system->[{}] try to add cluster with name->[{}] which is already exists, nothing "
                "will do".format(registered_system, cluster_name)
            )
            raise ValueError(_("集群名【{}】与已有集群冲突，请确认后重试").format(cluster_name))

        if cluster_type not in (cls.TYPE_INFLUXDB, cls.TYPE_ES, cls.TYPE_KAFKA, cls.TYPE_REDIS):
            logger.error(
                "reg_system->[{}] try to add cluster type->[{}] but is not at CLUSTER_TYPE_CHOICES, nothing "
                "will do".format(registered_system, cluster_type)
            )
            raise ValueError(_("存储集群【{}】暂不支持，请确认后重试").format(cluster_type))

        # 判断集群信息是否有存在冲突的
        if cls.objects.filter(domain_name=domain_name, port=port, username=username).exists():
            logger.error(
                "reg_system->[{}] try to add cluster->[{}] with domain->[{}] port->[{}] username->[{}] "
                "pass->[{}] which already has the same cluster config , nothing will do.".format(
                    registered_system, cluster_type, domain_name, port, username, password
                )
            )
            raise ValueError(_("存在同样配置集群，请确认后重试"))

        # 2. 创建新的逻辑
        new_cluster = cls.objects.create(
            cluster_name=cluster_name,
            cluster_type=cluster_type,
            domain_name=domain_name,
            port=port,
            registered_system=registered_system,
            creator=operator,
            last_modify_user=operator,
            description=description,
            username=username,
            password=password,
            version=version,
            custom_option=custom_option,
            schema=schema,
            is_ssl_verify=is_ssl_verify,
            # 新添加的，不可以为默认集群，触发运维通过admin修改
            is_default_cluster=False,
        )
        logger.info(
            "reg_system->[{}] created new cluster->[{}] type->[{}]".format(
                registered_system, new_cluster.cluster_id, cluster_type
            )
        )

        return new_cluster

    @atomic(config.DATABASE_CONNECTION_NAME)
    def modify(
        self,
        operator,
        description=None,
        username=None,
        password=None,
        custom_option=None,
        schema=None,
        is_ssl_verify=None,
    ):
        """
        修改存储集群信息
        :param operator: 操作者
        :param description: 描述信息
        :param username: 用户名
        :param password: 密码
        :param custom_option: 自定义标签信息
        :param schema: 通信协议
        :param is_ssl_verify: 是否需要强制验证SSL
        :return: True | raise Exception
        """
        args = {
            "description": description,
            "username": username,
            "password": password,
            "custom_option": custom_option,
            "schema": schema,
            "is_ssl_verify": is_ssl_verify,
        }

        # 遍历更新，降低重复代码
        for attribute_name, value in list(args.items()):
            if value is not None:
                setattr(self, attribute_name, value)
                # 由于已经有更新了，所以需要更新最后更新者
                self.last_modify_user = operator
                logger.info(
                    "cluster->[{}] attribute->[{}] is set to->[{}] by->[{}]".format(
                        self.cluster_name, attribute_name, value, operator
                    )
                )

        self.save()
        logger.info("cluster->[{}] update success.".format(self.cluster_name))
        return True


class KafkaTopicInfo(models.Model):
    """数据源对应的Kafka队列配置"""

    bk_data_id = models.IntegerField(_("数据源ID"), unique=True)
    topic = models.CharField(_("kafka topic"), max_length=128)
    partition = models.IntegerField(_("分区数量"))

    class Meta:
        verbose_name = _("Kafka消息队列配置")
        verbose_name_plural = _("Kafka消息队列配置表")

    @classmethod
    def create_info(cls, bk_data_id, topic=None, partition=1):
        """
        创建一个新的Topic信息
        :param bk_data_id: 数据源ID
        :param topic: topic默认与data_id一致，如果有提供，使用提供的topic
        :param partition: 默认分区为1，如果有提供，则使用提供的分区值
        :return: KafkaTopicInfo | raise Exception
        """
        # 1. 判断是否已经存在该data_id的配置
        if cls.objects.filter(bk_data_id=bk_data_id).exists():
            logger.error(
                "try to create kafka topic for data_id->[%s], but which is already exists, "
                "something go wrong?" % bk_data_id
            )
            raise ValueError(_("数据源已经配置，请确认"))

        # 2. 创建新的记录
        info = cls.objects.create(
            bk_data_id=bk_data_id,
            # 如果topic没有指定，则设定为该data_id同名
            # TOPIC的生成规范，可以参考DataSource.gse_config注释
            topic=topic if topic is not None else "{}{}0".format(config.KAFKA_TOPIC_PREFIX, bk_data_id),
            partition=partition,
        )
        logger.info(
            "new kafka topic is set for data_id->[%s] topic->[%s] partition->[%s]"
            % (info.bk_data_id, info.topic, info.partition)
        )

        # 3. 返回新的实例
        return info


class StorageResultTable(object):
    """实际结果表基类，提供公共方法的模板"""

    STORAGE_TYPE = None
    UPGRADE_FIELD_CONFIG = ()

    # JSON 类型的字段列表
    JSON_FIELDS = ()

    # 对应ResultTable的table_id
    table_id = None
    storage_cluster_id = None

    @classmethod
    @abc.abstractmethod
    def create_table(cls, table_id, is_sync_db=False, **kwargs):
        """实际创建结果表"""
        # 注意在创建结果表的时候，需要注意
        # 1. 创建当前结果表的DB信息记录
        # 2. 创建实际结果表，带上所有的字段
        pass

    @abc.abstractmethod
    def get_client(self):
        """获取该结果表的客户端句柄"""
        pass

    @abc.abstractmethod
    def add_field(self, field):
        """增加一个新的字段"""

    @abc.abstractproperty
    def consul_config(self):
        """返回一个实际存储的consul配置"""
        pass

    def update_storage(self, **kwargs):
        """更新存储配置"""
        # 遍历获取所有可以更新的字段，逐一更新
        for field_name in self.UPGRADE_FIELD_CONFIG:
            # 尝试获取配置
            upgrade_config = kwargs.get(field_name, None)

            if upgrade_config is None:
                logger.info(
                    "table_id->[{}] try to upgrade storage->[{}] config->[{}] but is not exists, "
                    "nothing will do.".format(self.table_id, self.STORAGE_TYPE, field_name)
                )
                continue

            # 判断写入的内容是否字典，如果是，需要json dumps一波
            if type(upgrade_config) in (dict, list) and field_name not in self.JSON_FIELDS:
                setattr(self, field_name, json.dumps(upgrade_config))

            else:
                setattr(self, field_name, upgrade_config)

            logger.info(
                "table_id->[{}] storage->[{}] has upgrade attribute->[{}] to->[{}]".format(
                    self.table_id, self.STORAGE_TYPE, field_name, upgrade_config
                )
            )

        self.save()
        logger.info("table->[{}] storage->[{}] upgrade operation success.".format(self.table_id, self.STORAGE_TYPE))

        return True

    @property
    def storage_cluster(self):
        """返回数据源的消息队列类型"""
        # 这个配置应该是很少变化的，所以考虑增加缓存
        if getattr(self, "_cluster", None) is None:
            self._cluster = ClusterInfo.objects.get(cluster_id=self.storage_cluster_id)

        return self._cluster


class InfluxDBStorage(models.Model, StorageResultTable):
    """TSDB物理表配置"""

    CONSUL_CONFIG_CLUSTER_PATH = "%s/influxdb_info/router" % config.CONSUL_PATH

    STORAGE_TYPE = ClusterInfo.TYPE_INFLUXDB
    UPGRADE_FIELD_CONFIG = ("source_duration_time",)

    # 对应ResultTable的table_id
    table_id = models.CharField(_("结果表名"), max_length=128, primary_key=True)
    # 对应StorageCluster记录ID
    # 该字段配置，供监控存储外部使用
    storage_cluster_id = models.IntegerField(_("存储集群"))
    real_table_name = models.CharField(_("实际存储表名"), max_length=128)
    database = models.CharField(_("数据库名"), max_length=128)
    # 字段格式应该符合influxDB的格式
    source_duration_time = models.CharField(_("原始数据保留时间"), max_length=32)
    # 降样后的表名
    down_sample_table = models.CharField(_("降样结果表名"), blank=True, max_length=128)
    down_sample_gap = models.CharField(_("降样聚合区间"), blank=True, max_length=32)
    # 字段格式应该符合influxDB的格式
    down_sample_duration_time = models.CharField(_("降样数据的保存时间"), blank=True, max_length=32)
    # 实际存储（influxdb-proxy后）的存储集群名字
    # 该字段配置，供influxdb-proxy使用
    # 默认对于新建的结果表，如果在没有指定的情况下，使用默认集群
    proxy_cluster_name = models.CharField(_("实际存储集群名字"), default="default", max_length=128)
    use_default_rp = models.BooleanField(_("是否使用默认RP配置"), default=True)
    partition_tag = models.CharField(_("tag分组列表"), blank=True, default="", max_length=128)

    class Meta:
        # 实际数据库存储表信息不可重复
        unique_together = ("real_table_name", "database")
        verbose_name = _("TSDB物理表配置")
        verbose_name_plural = _("TSDB物理表配置")

    @classmethod
    def export_data(cls):
        items = cls.objects.all()
        data = list(
            items.values(
                "table_id",
                "storage_cluster_id",
                "real_table_name",
                "database",
                "source_duration_time",
                "down_sample_table",
                "down_sample_gap",
                "down_sample_duration_time",
                "proxy_cluster_name",
                "use_default_rp",
                "partition_tag",
            )
        )
        return data

    @classmethod
    def import_data(cls, data):
        items = data
        delete_list = []
        for info in cls.objects.all():
            exist = False
            for item in items:
                if (item["real_table_name"] == info.real_table_name) and (item["database"] == info.database):
                    exist = True
            if not exist:
                delete_list.append(info)

        for info in delete_list:
            data = info.__dict__
            info.delete()
            print("delete route:{}".format(data))
            logger.info("delete route info:{}".format(data))

        for item in items:
            # info = InfluxDBTagInfo(**item)
            obj, created = cls.objects.update_or_create(
                real_table_name=item["real_table_name"],
                database=item["database"],
                defaults=item,
            )
            if created:
                print("created route:{}".format(item))
                logger.info("create new route info:{}".format(str(item)))
            else:
                print("updated route:{}".format(item))
                logger.info("update route info to:{}".format(str(item)))

    @classmethod
    def create_table(
        cls,
        table_id,
        is_sync_db=True,
        storage_cluster_id=None,
        database=None,
        real_table_name=None,
        source_duration_time="30d",
        proxy_cluster_name="default",
        **kwargs,
    ):
        """
        创建一个实际的结果表
        :param table_id: 结果表ID
        :param is_sync_db: 是否将创建同步到DB
        :param storage_cluster_id: 数据库集群ID，如果没有指定，则直接使用默认集群
        :param database: 数据库名，如果未None，则使用table_id.split['.'][0]
        :param real_table_name: 实际的结果表名，如果为None, 则使用table_id.split('.')[1]
        :param source_duration_time: 源数据保留的时间，默认是30d
        :param proxy_cluster_name: 对于influxdb-proxy，这个结果表需要路由至哪个集群的配置
        :param kwargs: 其他创建的参数
        :return: storage object
        """

        # 判断是否指定了集群
        if storage_cluster_id is None:
            storage_cluster_id = ClusterInfo.objects.get(
                cluster_type=ClusterInfo.TYPE_INFLUXDB, is_default_cluster=True
            ).cluster_id

        # 如果未有指定集群，需要判断集群是真实存在的
        else:
            if not ClusterInfo.objects.filter(
                cluster_type=ClusterInfo.TYPE_INFLUXDB, cluster_id=storage_cluster_id
            ).exists():
                logger.error(
                    "cluster_id->[%s] is not exists or is not influxdb cluster, something go wrong?"
                    % storage_cluster_id
                )
                raise ValueError(_("存储集群配置有误，请确认或联系管理员处理"))

        # 如果未有指定对应的结果表及数据库，则从table_id中分割获取
        except_database, except_table_name = table_id.split(".")
        if database is None:
            database = except_database

        if real_table_name is None:
            real_table_name = except_table_name

        # 需要判断是否存在默认的集群
        if not InfluxDBClusterInfo.objects.filter(cluster_name=proxy_cluster_name).exists():
            # 如果调入此处，表示指定的proxy并没有对应的任何机器
            logger.error(
                "proxy_cluster->[%s] has no config, maybe something go wrong?Nothing will do." % proxy_cluster_name
            )
            raise ValueError(_("请求集群[%s]不存在，请确认后重试") % proxy_cluster_name)

        # InfluxDB不需要实际创建结果表，只需要创建一条DB记录即可
        new_storage = cls.objects.create(
            table_id=table_id,
            storage_cluster_id=storage_cluster_id,
            database=database,
            real_table_name=real_table_name,
            source_duration_time=source_duration_time,
            proxy_cluster_name=proxy_cluster_name,
            **kwargs,
        )
        logger.info("result_table->[%s] now has create influxDB storage." % new_storage.table_id)

        if is_sync_db:
            new_storage.sync_db()

        # 刷新一次结果表的路由信息至consul中
        # 由于是创建结果表，必须强行刷新到consul配置中
        new_storage.refresh_consul_cluster_config(is_version_refresh=True)

        logger.info("result_table->[%s] all database create is done." % new_storage.table_id)
        return new_storage

    @property
    def consul_config(self):

        consul_config = {
            "storage_config": {
                "real_table_name": self.real_table_name,
                "database": self.database,
                "retention_policy_name": self.rp_name,
            }
        }
        # 添加集群信息
        consul_config.update(self.storage_cluster.consul_config)

        # 将存储的修改时间去掉，防止MD5命中失败
        consul_config["cluster_config"].pop("last_modify_time")

        return consul_config

    @property
    def consul_cluster_path(self):

        return "/".join([self.CONSUL_CONFIG_CLUSTER_PATH, self.database, self.real_table_name])

    @property
    def consul_cluster_config(self):
        config = {"cluster": self.proxy_cluster_name}

        if self.partition_tag != "":
            partition_tags = self.partition_tag.split(",")
            config["partition_tag"] = partition_tags

        return config

    @property
    def rp_name(self):
        """该结果表的rp名字"""
        if self.use_default_rp:
            return ""

        return "bkmonitor_rp_{}".format(self.table_id)

    def create_database(self):
        """
        创建一个配置记录对应的数据库内容，包括
        1. 数据库的创建
        2. 数据库的downsampling
        未来可以考虑在此增加CQ，保留粗粒度数据
        :return: True | raise Exception
        """

        # 1. 数据库的创建
        result = requests.post(
            url="http://{}:{}/create_database".format(self.storage_cluster.domain_name, self.storage_cluster.port),
            params={
                # 语句是供非表路由的proxy使用
                "q": 'CREATE DATABASE "%s"' % self.database,
                # cluster及DB名是供表路由proxy使用
                "db": self.database,
                "cluster": self.proxy_cluster_name,
            },
            headers={"Content-type": "application/json"},
        )

        # 判断数据库创建是否正常
        if result.status_code >= 300:
            logger.error(
                "failed to create database->[%s] for status->[%s] content->[%s]"
                % (self.database, result.status_code, result.content)
            )
            raise ValueError(_("创建数据库[%s]失败，请联系管理员") % self.database)

        logger.info(
            "database->[{}] is create on host->[{}:{}]".format(
                self.database, self.storage_cluster.domain_name, self.storage_cluster.port
            )
        )
        return True

    def create_rp(self, host_info, name=None, is_update=False):
        """
        创建一个数据库的RP
        :param host_info: 需要创建RP的集群信息 InfluxDBHostInfo
        :param name: RP 名称
        :param is_update: 是否更新rp
        :return: True | raise Exception
        """
        # 判断是否存在这个主机在这个集群中的配置
        if not InfluxDBClusterInfo.objects.filter(
            cluster_name=self.proxy_cluster_name, host_name=host_info.host_name
        ).exists():
            logger.error(
                "cluster_info->[%s] is not same as storage cluster_id->[%s]"
                % (host_info.cluster_name, self.proxy_cluster_name)
            )
            raise ValueError(_("创建集群信息非结果表配置，请确认"))

        client = influxdb.client.InfluxDBClient(host=host_info.domain_name, port=host_info.port)

        rp_config = {
            "name": self.rp_name if name is None else name,
            "duration": self.source_duration_time,
            "database": self.database,
            "default": False,
            "replication": "1",
        }

        # 2. 数据库的配置实施
        if is_update:
            client.alter_retention_policy(**rp_config)
        else:
            client.create_retention_policy(**rp_config)
        logger.info(
            "database->[{}] now has rp duration->[{}] on host->[{}] port->[{}] host_name->[{}]".format(
                self.database, self.source_duration_time, host_info.domain_name, host_info.port, host_info.host_name
            )
        )

        return True

    def ensure_rp(self):
        """
        确保数据库存在该存储的独立RP策略
        :return: True
        """
        # 判断是否使用独立的策略，否则不需要配置
        if self.use_default_rp:
            logger.info("table->[{}] use default rp, nothing will refresh for it.".format(self.table_id))
            return True

        # 否则，需要在相关的所有机器上，遍历判断RP是否正确配置了
        cluster_list = InfluxDBClusterInfo.objects.filter(cluster_name=self.proxy_cluster_name)
        for cluster_info in cluster_list:
            # 获取当次集群机器的信息
            host_info = InfluxDBHostInfo.objects.get(host_name=cluster_info.host_name)

            # 1. 判断数据库是否存在RP
            client = influxdb.client.InfluxDBClient(host=host_info.domain_name, port=host_info.port)
            rp_result = client.get_list_retention_policies(database=self.database)

            # 判断这个rp是否正确配置了
            for rp_info in rp_result:
                duration = rp_info.get("duration", "")
                name = rp_info.get("name", "")

                if name != self.rp_name:
                    continue

                # 判断duration是否一致
                if duration == golang_time_format.trans_time_format(self.source_duration_time):
                    logger.info(
                        "table->[{}] rp->[{} | {}] check fine on host->[{}]".format(
                            self.table_id, self.rp_name, self.source_duration_time, host_info.domain_name
                        )
                    )
                    # 可以直接找下一个机器了
                    break

                # 否则此处发现rp配置不一致，需要修复
                client.alter_retention_policy(
                    name=self.rp_name, database=self.database, duration=self.source_duration_time
                )
                logger.info(
                    "table->[{}] rp->[{} | {}] is updated on host->[{}]".format(
                        self.table_id, self.rp_name, self.source_duration_time, host_info.domain_name
                    )
                )
                break

            # 如果没有找到, 那么需要创建一个RP
            else:
                client.create_retention_policy(
                    name=self.rp_name,
                    database=self.database,
                    duration=self.source_duration_time,
                    replication=1,
                    shard_duration="7d",
                    default=False,
                )
                logger.info(
                    "table->[{}] rp->[{} | {}] is create on host->[{}]".format(
                        self.table_id, self.rp_name, self.source_duration_time, host_info.domain_name
                    )
                )

        return True

    def sync_db(self):
        """
        将这个结果表同步到实际数据库上
        1. 创建database
        2. 创建保留策略
        :return: True
        """
        # if self.is_database_exists():
        self.create_database()
        # self.create_rp()
        logger.debug("table_id->[%s] now is sync to db success" % self.table_id)

        return True

    def is_database_exists(self):
        """
        判断一个influx DB中的database是否存在
        :return: True | False
        """

        client = influxdb.client.InfluxDBClient(host=self.storage_cluster.domain_name, port=self.storage_cluster.port)

        return self.database in client.get_list_database()

    def add_field(self, field):
        """增加一个新的字段"""
        # InfluxDB不需要真的增加字段
        pass

    def get_client(self):
        pass

    @classmethod
    def clean_consul_config(cls):
        """
        清理掉不存在的consul key
        """
        # 遍历consul,删除已经不存在的key
        hash_consul = consul_tools.HashConsul()
        result_data = hash_consul.list(cls.CONSUL_CONFIG_CLUSTER_PATH)
        if not result_data[1]:
            return
        for item in result_data[1]:
            key = item["Key"]
            # 取路径最后一段，为主机名
            measurement = key.split("/")[-1]
            db = key.split("/")[-2]

            # 数据库里找不到的，就删掉
            length = len(cls.objects.filter(real_table_name=measurement, database=db))
            if length == 0:
                hash_consul.delete(key)
                logger.info("route info:{} deleted in consul".format(key))
            else:
                logger.info("route:{} has {} result,not delete".format(key, length))

    def refresh_consul_cluster_config(self, is_version_refresh=False):
        """
        刷新consul上的集群信息
        :return: None
        """

        hash_consul = consul_tools.HashConsul()
        hash_consul.put(key=self.consul_cluster_path, value=self.consul_cluster_config)
        logger.info("result_table->[%s] refresh cluster_info to consul success." % self.table_id)

        # 判断是否需要强行刷新一次consul版本
        if is_version_refresh:
            consul_tools.refresh_router_version()

    def get_metric_map(self):
        """
        获取metric及tag信息
        :return: [{
            "metric_name": "xxx",
            "metric_display_name": "XXX",
            "unit": "",
            "type": "float",
            "dimensions": [{
                "dimension_name": "",
                "dimension_display_name": ""
            }]
        }]
        """

        proxy = influxdb_tools.InfluxDBSchemaProxy(
            host=self.storage_cluster.domain_name,
            port=self.storage_cluster.port,
            database=self.database,
            measurement=self.real_table_name,
        )

        return proxy.get_metric_tag_values()

    def get_tag_values(self, tag_name):
        proxy = influxdb_tools.InfluxDBSchemaProxy(
            host=self.storage_cluster.domain_name,
            port=self.storage_cluster.port,
            database=self.database,
            measurement=self.real_table_name,
        )
        return proxy.get_tag_values(tag_name)


class RedisStorage(models.Model, StorageResultTable):
    """Redis存储方案记录"""

    STORAGE_TYPE = ClusterInfo.TYPE_REDIS
    UPGRADE_FIELD_CONFIG = ("is_sentinel", "master_name")

    # 对应ResultTable的table_id
    table_id = models.CharField(_("结果表名"), max_length=128, primary_key=True)
    # 默认命令是PUBLISH
    command = models.CharField(_("写入消息的命令"), max_length=32, default="PUBLISH")
    key = models.CharField(_("存储键值"), max_length=256)
    # 默认publish未用到该配置，为后续扩展预留
    db = models.IntegerField(_("redis DB配置"), default=0)
    # 对应StorageCluster记录ID
    # 该字段配置，供监控存储外部使用
    storage_cluster_id = models.IntegerField(_("存储集群"))
    # redis配置是否哨兵模式
    is_sentinel = models.BooleanField(_("是否哨兵模式"), default=False)
    # redis哨兵模式下的master名字
    master_name = models.CharField(_("哨兵模式master名字"), default="", max_length=128)

    @classmethod
    def create_table(
        cls,
        table_id,
        storage_cluster_id=None,
        key=None,
        db=0,
        command="PUBLISH",
        is_sentinel=False,
        master_name="",
        **kwargs,
    ):
        """
        实际创建结果表
        :param table_id: 结果表ID
        :param storage_cluster_id: 存储集群配置ID
        :param key: 写入到redis的键值配置
        :param db: redis DB，但该配置在publish命令下无效
        :param command: 写入redis的命令
        :param is_sentinel: 是否使用哨兵模式
        :param master_name: 哨兵master名字
        :param kwargs: 其余的额外配置，目前无效
        :return: storage object
        """

        # 0. 判断是否需要使用默认集群信息
        if storage_cluster_id is None:
            storage_cluster_id = ClusterInfo.objects.get(
                cluster_type=ClusterInfo.TYPE_REDIS, is_default_cluster=True
            ).cluster_id

        # 如果有提供集群信息，需要判断
        else:
            if not ClusterInfo.objects.filter(
                cluster_type=ClusterInfo.TYPE_REDIS, cluster_id=storage_cluster_id
            ).exists():
                logger.error(
                    "cluster_id->[%s] is not exists or is not redis cluster, something go wrong?" % storage_cluster_id
                )
                raise ValueError(_("存储集群配置有误，请确认或联系管理员处理"))

        # 1. 校验table_id， key是否存在冲突
        if cls.objects.filter(table_id=table_id).exists():
            logger.error("result_table->[%s] already has redis storage config, nothing will add." % table_id)
            raise ValueError(_("结果表[%s]配置已存在，请确认后重试") % table_id)

        # 如果未有执行key，则改为table_id
        key = key if key is not None else table_id
        # key的构造为 ${prefix}_${key}
        key = "_".join([config.REDIS_KEY_PREFIX, key])
        # 由于redis不必提前创建key，创建记录完成后即可
        new_record = cls.objects.create(
            table_id=table_id,
            storage_cluster_id=storage_cluster_id,
            command=command,
            key=key,
            db=db,
            is_sentinel=is_sentinel,
            master_name=master_name,
        )

        logger.info("table->[%s] now has create redis storage config" % table_id)
        return new_record

    @property
    def consul_config(self):
        """返回一个实际存储的consul配置"""

        consul_config = {
            "storage_config": {
                "db": self.db,
                "key": self.key,
                "command": self.command,
                "is_sentinel": self.is_sentinel,
                "master_name": self.master_name,
            }
        }
        # 添加集群信息
        consul_config.update(self.storage_cluster.consul_config)

        # 将存储的修改时间去掉，防止MD5命中失败
        consul_config["cluster_config"].pop("last_modify_time")

        return consul_config

    def get_client(self):
        """获取该结果表的客户端句柄"""
        pass

    def add_field(self, field):
        """增加一个新的字段"""
        # redis算是无结构表数据库，不必提供方法
        pass


class KafkaStorage(models.Model, StorageResultTable):
    """Kafka存储方案记录"""

    STORAGE_TYPE = ClusterInfo.TYPE_KAFKA
    UPGRADE_FIELD_CONFIG = ("partition", "retention")

    # 对应ResultTable的table_id
    table_id = models.CharField(_("结果表名"), max_length=128, primary_key=True)
    topic = models.CharField(_("topic"), max_length=256)
    partition = models.IntegerField(_("topic分区数量"), default=1)
    # 对应StorageCluster记录ID
    # 该字段配置，供监控存储外部使用
    storage_cluster_id = models.IntegerField(_("存储集群"))
    # 数据过期时间配置为半小时，原因是kafka数据通常是为实时告警使用，该类告警不必保留过长时间
    retention = models.IntegerField(_("保存数据超时时间"), default=1800000)

    def __unicode__(self):
        return "{}->[t:{} p:{}]".format(self.table_id, self.topic, self.partition)

    class Meta:
        verbose_name = _("Kafka存储配置")
        verbose_name_plural = _("Kafka存储配置")

    @classmethod
    def create_table(
        cls, table_id, is_sync_db=False, storage_cluster_id=None, topic=None, partition=1, retention=1800000, **kwargs
    ):
        """
        实际创建结果表
        :param table_id: 结果表ID
        :param is_sync_db: 是否需要同步到存储
        :param storage_cluster_id: 存储集群配置ID
        :param topic: topic
        :param partition: topic分区
        :param retention: 数据过期时间
        :param kwargs: 其余的额外配置，目前无效
        :return: storage object
        """

        # 0. 判断是否需要使用默认集群信息
        if storage_cluster_id is None:
            storage_cluster_id = ClusterInfo.objects.get(
                cluster_type=ClusterInfo.TYPE_KAFKA, is_default_cluster=True
            ).cluster_id

        # 如果有提供集群信息，需要判断
        else:
            if not ClusterInfo.objects.filter(
                cluster_type=ClusterInfo.TYPE_KAFKA, cluster_id=storage_cluster_id
            ).exists():
                logger.error(
                    "cluster_id->[%s] is not exists or is not redis cluster, something go wrong?" % storage_cluster_id
                )
                raise ValueError(_("存储集群配置有误，请确认或联系管理员处理"))

        # 1. 校验table_id， key是否存在冲突
        if cls.objects.filter(table_id=table_id).exists():
            logger.error("result_table->[%s] already has redis storage config, nothing will add." % table_id)
            raise ValueError(_("结果表[%s]配置已存在，请确认后重试") % table_id)

        # 如果未有指定key，则改为table_id
        topic = topic if topic is not None else table_id
        # topic的构造为 ${prefix}_${key}
        topic = "_".join([config.KAFKA_TOPIC_PREFIX_STORAGE, topic])

        new_record = cls.objects.create(
            table_id=table_id,
            storage_cluster_id=storage_cluster_id,
            topic=topic,
            partition=partition,
            retention=retention,
        )

        # 需要确保topic存在
        if is_sync_db:
            new_record.ensure_topic()

        logger.info("table->[%s] now has create kafka storage config" % table_id)
        return new_record

    @property
    def consul_config(self):
        """返回一个实际存储的consul配置"""

        consul_config = {"storage_config": {"topic": self.topic, "partition": self.partition}}
        # 添加集群信息
        consul_config.update(self.storage_cluster.consul_config)

        # 将存储的修改时间去掉，防止MD5命中失败
        consul_config["cluster_config"].pop("last_modify_time")

        return consul_config

    def get_client(self):
        """获取该结果表的客户端句柄"""
        pass

    def add_field(self, field):
        """增加一个新的字段"""
        # kafka算是无结构表数据库，不必提供方法
        pass

    def ensure_topic(self):
        """
        确保这个存储的topic存在
        :return: True | raise Exception
        """
        logger.info("topic->[%s] will auto create by kafka server, nothing will do any more.", self.topic)
        return True


class ESStorage(models.Model, StorageResultTable):
    """ES存储配置信息"""

    STORAGE_TYPE = ClusterInfo.TYPE_ES
    UPGRADE_FIELD_CONFIG = (
        "retention",
        "slice_size",
        "slice_gap",
        "index_settings",
        "mapping_settings",
        "storage_cluster_id",
        "warm_phase_days",
        "warm_phase_settings",
    )
    JSON_FIELDS = ("warm_phase_settings",)
    # 从ES7开始移除_type
    ES_REMOVE_TYPE_VERSION = 7

    # 对应ResultTable的table_id
    table_id = models.CharField(_("结果表名"), max_length=128, primary_key=True)
    # 格式化配置字符串，用于追加到table_id后，作为index的创建方案，默认格式类似为20190910194802
    date_format = models.CharField(_("日期格式化配置"), max_length=64, default="%Y%m%d%H")
    # index切分大小阈值，单位GB，默认是500GB
    slice_size = models.IntegerField(_("index大小切分阈值"), default=500)
    # index分片时间间隔，单位分钟，默认2小时
    slice_gap = models.IntegerField(_("index分片时间间隔"), default=120)
    # 存储时间, 单位天，默认30天
    retention = models.IntegerField(_("index保存时间"), default=30)

    # 索引数据分配配置
    # 通过配置，将一定天数前的索引数据分配到拥有特定属性的节点
    warm_phase_days = models.IntegerField(_("切换到暖数据的等待天数"), default=0)
    # 暖数据配置：dict
    # 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/shard-allocation-filtering.html
    # {
    #   "allocation_attr_name": "box_type",  // 切换路由的节点属性名称
    #   "allocation_attr_value": "warm",     // 切换路由的节点属性值
    #   "allocation_type": "include",   // 属性匹配类型，可选 require, include, exclude 等
    # }
    warm_phase_settings = JsonField(_("暖数据配置"), default={})

    # 下方三个配置，对于metadata都是透明存储的方式，供用户直接配置使用
    # 从而降低对版本等信息的依赖，格式应该是JSON格式，以便可以直接在创建请求的body中使用
    index_settings = models.TextField(_("索引配置信息"))
    mapping_settings = models.TextField(_("别名配置信息"))
    storage_cluster_id = models.IntegerField(_("存储集群"))

    @classmethod
    def create_table(
        cls,
        table_id,
        is_sync_db=True,
        date_format="%Y%m%d%H",
        slice_size=500,
        slice_gap=120,
        index_settings=None,
        mapping_settings=None,
        cluster_id=None,
        retention=30,
        warm_phase_days=0,
        warm_phase_settings=None,
        **kwargs,
    ):
        """
        实际创建结果表
        :param table_id: 结果表ID
        :param is_sync_db: 是否需要同步创建结果表
        :param date_format: 时间格式，用于拼接index及别名
        :param slice_size: 切分大小，不提供使用默认值
        :param slice_gap: 切分时间间隔，不提供使用默认值
        :param index_settings: index创建配置，如果不提供，默认为{}(无配置)
        :param mapping_settings: index创建时的mapping配置，如果不提供，默认为{}，但是字段信息将会被覆盖
        :param cluster_id: 集群ID，如果不提供使用默认的ES集群
        :param retention: 保留时间
        :param warm_phase_days: 暖数据执行分配的等待天数，默认为 0 (不开启)
        :param warm_phase_settings: 暖数据切换配置，当 warm_phase_days > 0 时，此项必填
        :param kwargs: 其他配置参数
        :return:
        """
        # 0. 判断是否需要使用默认集群信息
        if cluster_id is None:
            cluster_id = ClusterInfo.objects.get(cluster_type=ClusterInfo.TYPE_ES, is_default_cluster=True).cluster_id

        # 如果有提供集群信息，需要判断
        else:
            if not ClusterInfo.objects.filter(cluster_type=ClusterInfo.TYPE_ES, cluster_id=cluster_id).exists():
                logger.error("cluster_id->[%s] is not exists or is not redis cluster, something go wrong?" % cluster_id)
                raise ValueError(_("存储集群配置有误，请确认或联系管理员处理"))

        # 1. 校验table_id， key是否存在冲突
        if cls.objects.filter(table_id=table_id).exists():
            logger.error("result_table->[%s] already has redis storage config, nothing will add." % table_id)
            raise ValueError(_("结果表[%s]配置已存在，请确认后重试") % table_id)

        # 测试date_format是否正确可用的 -- 格式化结果的数据只能包含数字，不能有其他结果
        test_str = datetime.datetime.utcnow().strftime(date_format)
        if re.match(r"^\d+$", test_str) is None:
            logger.error("result_table->[{}] date_format contains none digit info, it is bad.".format(table_id))
            raise ValueError(_("时间格式不允许包含非数字格式"))

        # 校验分配配置
        if warm_phase_days > 0:
            if not warm_phase_settings:
                logger.error("result_table->[{}] warm_phase_settings is empty, but min_days > 0.".format(table_id))
                raise ValueError(_("warm_phase_settings 不能为空"))
            for required_field in ["allocation_attr_name", "allocation_attr_value", "allocation_type"]:
                if not warm_phase_settings.get(required_field):
                    raise ValueError(_("warm_phase_settings.{} 不能为空").format(required_field))

        warm_phase_settings = {} if warm_phase_settings is None else warm_phase_settings

        # 判断两个TextField的配置内容
        index_settings = {} if index_settings is None else index_settings
        mapping_settings = {} if mapping_settings is None else mapping_settings

        # alias settings目前暂时没有用上，在参数和配置中都没有更新
        new_record = cls.objects.create(
            table_id=table_id,
            date_format=date_format,
            slice_size=slice_size,
            slice_gap=slice_gap,
            retention=retention,
            warm_phase_days=warm_phase_days,
            warm_phase_settings=warm_phase_settings,
            index_settings=json.dumps(index_settings),
            mapping_settings=json.dumps(mapping_settings),
            storage_cluster_id=cluster_id,
        )
        logger.info("result_table->[{}] now has es_storage will try to create index.".format(table_id))

        if is_sync_db:
            # 只往前创建一个index
            new_record.create_index_and_aliases(new_record.slice_gap)
        logger.info("result_table->[{}] has create es storage index".format(table_id))

        return new_record

    @property
    def index_body(self):
        """
        ES创建索引的配置内容
        :return: dict, 可以直接
        """
        body = {"settings": json.loads(self.index_settings), "mappings": json.loads(self.mapping_settings)}

        # 构建mapping内容
        # 将所有properties先去掉，防止用户注入了自行的字段内容
        properties = body["mappings"]["properties"] = {}
        for field in ResultTableField.objects.filter(table_id=self.table_id):
            # 直接注入这个字段的配置
            properties[field.field_name] = ResultTableFieldOption.get_field_option_es_format(
                table_id=self.table_id, field_name=field.field_name
            )

        # 按ES版本返回构建body内容
        if self.es_version < self.ES_REMOVE_TYPE_VERSION:
            body["mappings"] = {self.table_id: body["mappings"]}
        return body

    @property
    def index_re_v1(self):
        """获取这个存储的正则匹配内容"""
        pattern = r"{}_(?P<datetime>\d+)_(?P<index>\d+)".format(self.index_name)
        return re.compile(pattern)

    @property
    def index_re_v2(self):
        """获取这个存储的正则匹配内容"""
        pattern = r"^v2_{}_(?P<datetime>\d+)_(?P<index>\d+)$".format(self.index_name)
        return re.compile(pattern)

    @property
    def index_re_common(self):
        """获取这个存储的正则匹配内容"""
        pattern = r"^(v2_)?{}_(?P<datetime>\d+)_(?P<index>\d+)$".format(self.index_name)
        return re.compile(pattern)

    @property
    def write_alias_re(self):
        """获取写入别名的正则匹配"""
        pattern = r"write_(?P<datetime>\d+)_{}".format(self.index_name)
        return re.compile(pattern)

    @property
    def old_write_alias_re(self):
        """获取旧版写入别名的正则匹配"""
        pattern = r"{}_(?P<datetime>\d+)_write".format(self.index_name)
        return re.compile(pattern)

    @property
    def read_alias_re(self):
        """获取读取别名的正则匹配"""
        pattern = r"{}_(?P<datetime>\d+)_read".format(self.index_name)
        return re.compile(pattern)

    @property
    def index_name(self):
        """返回该index的名字"""
        return self.table_id.replace(".", "_")

    @property
    def es_version(self):
        """
        获取ES版本号
        """
        cluster_info = ClusterInfo.objects.get(cluster_id=self.storage_cluster_id)
        try:
            cluster_version = int(cluster_info.version.split(".")[0])
        except Exception:
            logger.error(
                "cluster_id->[{}] get version error->[{}] ".format(self.storage_cluster_id, traceback.format_exc())
            )
            cluster_version = config.ES_CLUSTER_VERSION_DEFAULT
        return cluster_version

    @property
    def consul_config(self):
        """返回一个实际存储的consul配置"""
        standard_time = datetime.datetime.strptime("200601021504", "%Y%m%d%H%M%S")

        consul_config = {
            "storage_config": {
                "index_datetime_format": "write_{}".format(standard_time.strftime(self.date_format)),
                "date_format": self.date_format,
                "slice_size": self.slice_size,
                "slice_gap": self.slice_gap,
                "retention": self.retention,
                "warm_phase_days": self.warm_phase_days,
                "warm_phase_settings": self.warm_phase_settings,
                "base_index": self.table_id.replace(".", "_"),
                "index_settings": json.loads(self.index_settings),
                "mapping_settings": json.loads(self.mapping_settings),
            }
        }
        # 添加集群信息
        consul_config.update(self.storage_cluster.consul_config)

        # 将存储的修改时间去掉，防止MD5命中失败
        consul_config["cluster_config"].pop("last_modify_time")

        return consul_config

    def is_index_enable(self):
        """判断index是否启用中"""

        # 判断如果结果表已经废弃了，那么不再进行index的创建
        if not ResultTable.objects.filter(table_id=self.table_id, is_enable=True, is_deleted=False).exists():
            logger.info("table_id->[%s] now is delete or disable, no index will create.", self.table_id)
            return False

        # 同时需要增加判断这个结果表是否可能遗留的自定义事件上报，需要考虑自定义上报已经关闭了
        try:
            # 查找发现，1. 这个es存储是归属于自定义事件的，而且 2. 不是在启动且未被删除的，那么不需要创建这个索引
            event_group = EventGroup.objects.get(table_id=self.table_id)

            if not event_group.is_enable or event_group.is_delete:
                logger.info(
                    "table_id->[%s] is belong to event group and is disable or deleted, no index will create",
                    self.table_id,
                )
                return False

        except EventGroup.DoesNotExist:
            # 如果查找失败，那么这个存储是日志平台，而且rt没有被删除或废弃，需要继续建立index
            logger.info("table_id->[%s] belong to log search, will create it.", self.table_id)

        return True

    def search_format_v2(self):
        return f"v2_{self.index_name}_*"

    def search_format_v1(self):
        return f"{self.index_name}_*"

    def index_exist(self):
        """
        判断该index是否已经存在,优先v2，随后v1
        :return: True | False
        """
        es_client = self.get_client()
        stat_info_list = es_client.indices.stats(self.search_format_v2())
        if len(stat_info_list["indices"]) != 0:
            logger.info("table_id->[%s] found v2 index list->[%s]", self.table_id, str(stat_info_list))
            return True
        stat_info_list = es_client.indices.stats(self.search_format_v1())
        if len(stat_info_list["indices"]) != 0:
            logger.info("table_id->[%s] found v1 index list->[%s]", self.table_id, str(stat_info_list))
            return True
        logger.info("table_id->[%s] no index", self.table_id)
        return False

    def current_index_info(self):
        """
        返回当前使用的最新index相关的信息
        :return: {
            "datetime_object": max_datetime_object,
            "index": 0,
            "size": 123123,  # index大小，单位byte
        }
        """
        es_client = self.get_client()
        # stats格式为：{
        #   "indices": {
        #       "${index_name}": {
        #           "total": {
        #               "store": {
        #                   "size_in_bytes": 1000
        #               }
        #           }
        #       }
        #   }
        # }
        index_re = None
        index_version = ""
        # 查找index,找不到v2的就找v1的
        stat_info_list = es_client.indices.stats(self.search_format_v2())
        if len(stat_info_list["indices"]) != 0:
            index_version = "v2"
            index_re = self.index_re_v2
        else:
            stat_info_list = es_client.indices.stats(self.search_format_v1())
            if len(stat_info_list["indices"]) != 0:
                index_version = "v1"
                index_re = self.index_re_v1

        # 如果index_re为空，说明没找到任何可用的index
        if index_version == "":
            logger.info("index->[%s] has no index now, will raise a fake not found error", self.index_name)
            raise elasticsearch5.NotFoundError(self.index_name)

        # 1.1 判断获取最新的index
        max_index = 0
        max_datetime_object = None
        for stat_index_name in list(stat_info_list["indices"].keys()):

            re_result = index_re.match(stat_index_name)
            if re_result is None:
                # 去掉一个整体index的计数
                logger.warning("index->[%s] is not match re, maybe something go wrong?", stat_index_name)
                continue

            # 获取实际的count及时间对象
            current_index = int(re_result.group("index"))
            current_datetime_str = re_result.group("datetime")

            current_datetime_object = datetime.datetime.strptime(current_datetime_str, self.date_format)

            logger.info(
                "going to detect index->[%s] datetime->[%s] count->[%s]",
                stat_index_name,
                current_index,
                current_datetime_str,
            )

            # 初始化轮，直接赋值
            if max_datetime_object is None:
                max_index = current_index
                max_datetime_object = current_datetime_object
                logger.debug(
                    "current round is init round, will use datetime->[%s] and count->[%s]",
                    current_datetime_str,
                    current_index,
                )
                continue

            # 判断获取最新的index内容
            # 当时间较大的时候，直接赋值使用
            if current_datetime_object > max_datetime_object:
                max_datetime_object = current_datetime_object
                max_index = current_index
                logger.debug(
                    "current time->[%s] is newer than max time->[%s] will use it and reset count->[%s]",
                    current_datetime_str,
                    max_datetime_object.strftime(self.date_format),
                    current_index,
                )
                continue

            # 判断如果时间一致且index较大，需要更新替换
            if current_datetime_object == max_datetime_object and current_index > max_index:
                max_index = current_index
                logger.debug(
                    "current time->[%s] found newer index->[%s] will use it",
                    max_datetime_object.strftime(self.date_format),
                    current_index,
                )

        return {
            "index_version": index_version,
            "datetime_object": max_datetime_object,
            "index": max_index,
            "size": stat_info_list["indices"][f"{self.make_index_name(max_datetime_object, max_index,index_version)}"][
                "primaries"
            ]["store"]["size_in_bytes"],
        }

    def make_index_name(self, datetime_object, index, version):
        """根据传入的时间和index，创建返回一个index名"""
        if version == "v2":
            return f"v2_{self.index_name}_{datetime_object.strftime(self.date_format)}_{index}"
        return f"{self.index_name}_{datetime_object.strftime(self.date_format)}_{index}"

    def get_client(self):
        """获取该结果表的客户端句柄"""
        cluster_info = ClusterInfo.objects.get(cluster_id=self.storage_cluster_id)

        connection_info = {
            "hosts": ["{}:{}".format(cluster_info.domain_name, cluster_info.port)],
            "verify_certs": cluster_info.is_ssl_verify,
            "use_ssl": cluster_info.is_ssl_verify,
        }

        # 如果需要身份验证
        if cluster_info.username is not None and cluster_info.password is not None:
            connection_info["http_auth"] = (cluster_info.username, cluster_info.password)

        es_client = elasticsearch5.Elasticsearch(**connection_info)
        return es_client

    def add_field(self, field):
        """需要修改ES的mapping"""
        pass

    def create_index(self, ahead_time=1440):
        """
        创建index，具有提前创建index的能力
        :param ahead_time: 需要提前创建多少分钟后的index
        :return: True | raise Exception
        """

        # 判断如果结果表已经废弃了，那么不再进行index的创建
        if not ResultTable.objects.filter(table_id=self.table_id, is_enable=True, is_deleted=False).exists():
            logger.info("table_id->[%s] now is delete or disable, no index will create.", self.table_id)
            return

        # 同时需要增加判断这个结果表是否可能遗留的自定义事件上报，需要考虑自定义上报已经关闭了
        try:
            # 查找发现，1. 这个es存储是归属于自定义事件的，而且 2. 不是在启动且未被删除的，那么不需要创建这个索引
            event_group = EventGroup.objects.get(table_id=self.table_id)

            if not event_group.is_enable or event_group.is_delete:
                logger.info(
                    "table_id->[%s] is belong to event group and is disable or deleted, no index will create",
                    self.table_id,
                )
                return

        except EventGroup.DoesNotExist:
            # 如果查找失败，那么这个存储是日志平台，而且rt没有被删除或废弃，需要继续建立index
            logger.info("table_id->[%s] belong to log search, will create it.", self.table_id)

        now_time = datetime.datetime.utcnow()
        now_gap = 0

        # 1. 获取客户端
        es_client = self.get_client()
        # 统一的将所有【.】分割符改为【_】
        index_name = self.index_name

        # 3. 遍历创建所有的index
        # 创建的方式，是从近到远的创建
        while now_gap <= ahead_time:
            try:
                delete_index_list = []
                current_time = now_time + datetime.timedelta(minutes=now_gap)
                current_time_str = current_time.strftime(self.date_format)

                current_index_wildcard = "{}_{}_*".format(self.index_name, current_time_str)

                # 获取这个index的大小信息，这是需要兼容判断是否有未来数据写入到index上了
                stat_info = es_client.indices.stats(current_index_wildcard)
                max_index = -1

                # 判断获取最大的index名字
                for stat_index_name in list(stat_info["indices"].keys()):

                    re_result = self.index_re.match(stat_index_name)
                    if re_result is None:
                        # 去掉一个整体index的计数
                        logger.warning("index->[{}] is not match re, maybe something go wrong?".format(index_name))
                        continue

                    current_index_count = int(re_result.group("index"))
                    if max_index < current_index_count:
                        max_index = current_index_count

                # 获取现在当前最大的index
                # 注意，这时候的index有可能是-1的名字，例如：2_test_log_20191112_-1
                max_index_name = "{}_{}_{}".format(self.index_name, current_time_str, max_index)

                # 如果已经存在的index，不必重复创建
                is_index_exists = es_client.indices.exists(index=max_index_name)
                # 如果一个index是不存在的，则默认需要创建
                should_create = not is_index_exists

                # 判断index如果是存在的，需要判断：
                # 1. 是否大小需要进行切片分割
                # 2. 是否字段有变化，需要进行重建
                if is_index_exists:
                    # 判断字段是否一致，如果不一致，需要创建新的删除并创建新的
                    if not self.is_mapping_same(max_index_name):
                        logger.info(
                            "index->[{}] is exists, and field type is not the same as database, "
                            "will create a new index.".format(max_index_name)
                        )
                        should_create = True

                    # 判断大小是否有超限，需要切片
                    try:
                        size_in_bytes = stat_info["indices"][max_index_name]["total"]["store"]["size_in_bytes"]
                    except KeyError:
                        logger.warning(
                            "ops, index->[{}] is not exists in stat_info, maybe is not exists?".format(max_index_name)
                        )
                    else:
                        if size_in_bytes / 1024.0 / 1024.0 / 1024.0 > self.slice_size:
                            logger.info(
                                "index->[{}] size->[{}]bytes now is bigger than slice_size->[{}]GB, will "
                                "create new one".format(max_index_name, size_in_bytes, self.slice_size)
                            )
                            should_create = True

                # 判断是否需要重建了，不用重建的，直接下一个周期
                if not should_create:
                    logger.info("index->[{}] meet all config, nothing will create.".format(max_index_name))
                    # gap的更新在finally进行
                    continue

                # 如果判断要创建index，需要先判断这个index是否有数据了
                try:
                    # 如果是存在数据的，需要创建一个新的index
                    if es_client.count(max_index_name).get("count", 0) != 0:
                        logger.info(
                            "index->[{}] already has data, will keep it and create new index.".format(max_index_name)
                        )
                        # 有数据的，需要增加index
                        current_index = "{}_{}_{}".format(index_name, current_time_str, max_index + 1)
                        delete_index_list.append(max_index_name)

                    # 不存在数据的，则删除并重新创建
                    else:
                        es_client.indices.delete(max_index_name)
                        logger.warning(
                            "index->[{}] is differ from database config, "
                            "will be delete and recreated.".format(max_index_name)
                        )
                        # 创建的新index，使用已有的最大index名即可
                        # 此处可以保留已有的别名配置，不用删除
                        current_index = max_index_name

                except elasticsearch5.NotFoundError:
                    # 很可能是0号或者-1号的index没有创建，所以判断count不存在
                    logger.warning("index->[{}] may not exists, cannot found count? will create new one.")
                    # 看下是否-1的index，需要调整为0的
                    current_index = (
                        "{}_{}_0".format(index_name, current_time_str) if max_index == -1 else max_index_name
                    )

                # 创建索引需要增加一个请求超时的防御
                logger.info("index->[{}] trying to create, index_body->[{}]".format(index_name, self.index_body))
                es_client.indices.create(index=current_index, body=self.index_body, params={"request_timeout": 30})
                logger.info("index->[{}] now is created.".format(current_index))

                # 需要将对应的别名指向这个新建的index
                # 新旧类型的alias都会创建，防止transfer未更新导致异常
                new_current_alias_name = "write_{}_{}".format(current_time_str, index_name)
                old_current_alias_name = "{}_{}_write".format(index_name, current_time_str)

                es_client.indices.put_alias(index=current_index, name=new_current_alias_name)
                es_client.indices.put_alias(index=current_index, name=old_current_alias_name)

                logger.info(
                    "index->[{}] now has write alias->[{} | {}]".format(
                        current_index, new_current_alias_name, old_current_alias_name
                    )
                )

                # 清理别名
                if len(delete_index_list) != 0:
                    es_client.indices.delete_alias(index=",".join(delete_index_list), name=old_current_alias_name)
                    es_client.indices.delete_alias(index=",".join(delete_index_list), name=new_current_alias_name)
                    logger.info(
                        "index->[{}] has delete relation to alias->[{} | {}]".format(
                            delete_index_list, old_current_alias_name, new_current_alias_name
                        )
                    )

            finally:
                logger.info("all operations for index->[{}] gap->[{}] now is done.".format(self.table_id, now_gap))
                now_gap += self.slice_gap

        return True

    def create_or_update_aliases(self, ahead_time=1440):
        """
        更新alias，如果有已存在的alias，则将其指向最新的index，并根据ahead_time前向预留一定的alias
        """
        es_client = self.get_client()
        current_index_info = self.current_index_info()
        last_index_name = self.make_index_name(
            current_index_info["datetime_object"], current_index_info["index"], current_index_info["index_version"]
        )

        now_datetime_object = datetime.datetime.utcnow()

        now_gap = 0
        index_name = self.index_name

        while now_gap <= ahead_time:

            round_time = now_datetime_object + datetime.timedelta(minutes=now_gap)
            round_time_str = round_time.strftime(self.date_format)

            try:
                round_alias_name = f"write_{round_time_str}_{index_name}"
                round_read_alias_name = f"{index_name}_{round_time_str}_read"

                # 3.1 判断这个别名是否有指向旧的index，如果存在则需要解除
                try:
                    # 此处是非通配的别名，所以会有NotFound的异常
                    index_list = es_client.indices.get_alias(name=round_alias_name).keys()

                    # 排除已经指向最新index的alias
                    delete_list = []
                    for alias_index in index_list:
                        if alias_index != last_index_name:
                            delete_list.append(alias_index)

                    logger.info(
                        "table_id->[%s] found alias_name->[%s] is relay with index->[%s] all will be deleted.",
                        self.table_id,
                        round_alias_name,
                        delete_list,
                    )
                except elasticsearch5.NotFoundError:
                    # 可能是在创建未来的alias，所以不一定会有别名关联的index
                    logger.info(
                        "table_id->[%s] alias_name->[%s] found not index relay, will not delete any thing.",
                        self.table_id,
                        round_alias_name,
                    )
                    delete_list = []

                # 3.2 需要将循环中的别名都指向了最新的index
                es_client.indices.update_aliases(
                    body={
                        "actions": [
                            {"add": {"index": last_index_name, "alias": round_alias_name}},
                            {"add": {"index": last_index_name, "alias": round_read_alias_name}},
                        ]
                    }
                )

                logger.info(
                    "table_id->[%s] now has index->[%s] and alias->[%s | %s]",
                    self.table_id,
                    last_index_name,
                    round_alias_name,
                    round_read_alias_name,
                )

                # 只有当index相关列表不为空的时候，才会进行别名关联清理
                if len(delete_list) != 0:
                    index_list_str = ",".join(delete_list)
                    es_client.indices.delete_alias(index=index_list_str, name=round_alias_name)
                    logger.info(
                        "table_id->[%s] index->[%s] alias->[%s] relations now had delete.",
                        self.table_id,
                        delete_list,
                        round_alias_name,
                    )

            finally:
                logger.info("all operations for index->[{}] gap->[{}] now is done.".format(self.table_id, now_gap))
                now_gap += self.slice_gap

    def create_index_and_aliases(self, ahead_time=1440):
        self.create_index_v2()
        self.create_or_update_aliases(ahead_time)

    def update_index_and_aliases(self, ahead_time=1440):
        self.update_index_v2()
        self.create_or_update_aliases(ahead_time)

    def create_index_v2(self):
        """
        创建全新的index序列，以及指向它的全新alias
        """
        if not self.is_index_enable():
            return False

        now_datetime_object = datetime.datetime.utcnow()
        es_client = self.get_client()
        new_index_name = self.make_index_name(now_datetime_object, 0, "v2")
        # 创建index
        es_client.indices.create(index=new_index_name, body=self.index_body, params={"request_timeout": 30})
        logger.info("table_id->[%s] has created new index->[%s]", self.table_id, new_index_name)
        return True

    def update_index_v2(self):
        """
        判断index是否需要分裂，并提前建立index别名的功能
        此处仍然保留每个小时创建新的索引，主要是为了在发生异常的时候，可以降低影响的索引范围（最多一个小时）
        :return: True | raise Exception
        """
        if not self.is_index_enable():
            return False

        now_datetime_object = datetime.datetime.utcnow()

        # 0. 获取客户端
        es_client = self.get_client()

        # 1. 获取当前最新的index
        try:
            current_index_info = self.current_index_info()
            last_index_name = self.make_index_name(
                current_index_info["datetime_object"], current_index_info["index"], current_index_info["index_version"]
            )
            index_size_in_byte = current_index_info["size"]

        except elasticsearch5.NotFoundError:
            logger.warn(
                "attention! table_id->[%s] can not found any index to update,will do create function", self.table_id
            )
            return self.create_index_v2()

        # 1.1 兼容旧任务，将不合理的超前index清理掉
        # 如果最新时间超前了，要对应处理一下,通常发生在旧任务应用新的es代码过程中
        # 循环处理，以应对预留时间被手动加长,导致超前index有多个的场景
        while now_datetime_object < current_index_info["datetime_object"]:
            logger.warn("table_id->[%s] delete index->[%s] because it has ahead time", self.table_id, last_index_name)
            es_client.indices.delete(index=last_index_name)
            # 重新获取最新的index，这里没做防护，默认存在超前的index，就一定存在不超前的可用index
            current_index_info = self.current_index_info()
            last_index_name = self.make_index_name(
                current_index_info["datetime_object"], current_index_info["index"], current_index_info["index_version"]
            )

        # 2. 判断index是否需要分割
        # 如果是小于分割大小的，不必进行处理
        should_create = False
        if index_size_in_byte / 1024.0 / 1024.0 / 1024.0 > self.slice_size:
            logger.info(
                "table_id->[%s] index->[%s] current_size->[%s] is larger than slice size->[%s], create new index slice",
                self.table_id,
                last_index_name,
                index_size_in_byte,
                self.slice_size,
            )
            should_create = True

        # mapping 不一样了，也需要创建新的index
        if not self.is_mapping_same(last_index_name):
            logger.info(
                "table_id->[%s] index->[%s] mapping is not the same, will create the new",
                self.table_id,
                last_index_name,
            )
            should_create = True

        # 达到保存期限进行分裂
        expired_time_point = datetime.datetime.utcnow() - datetime.timedelta(days=self.retention)
        if current_index_info["datetime_object"] < expired_time_point:
            logger.info(
                "table_id->[%s] index->[%s] has arrive retention date, will create the new",
                self.table_id,
                last_index_name,
            )
            should_create = True

        # 2.0 判断新的index信息：日期以及对应的index
        if not should_create:
            logger.info(
                "table_id->[%s] index->[%s] everything is ok,nothing to do",
                self.table_id,
                last_index_name,
            )
            return True

        new_index = 0
        # 判断日期是否当前的时期或时间
        if now_datetime_object.strftime(self.date_format) == current_index_info["datetime_object"].strftime(
            self.date_format
        ):

            # 如果当前index并没有写入过数据(count==0),则对其进行删除重建操作即可
            if es_client.count(last_index_name).get("count", 0) == 0:
                new_index = current_index_info["index"]
                es_client.indices.delete(index=last_index_name)
                logger.info(
                    "table_id->[%s] has index->[%s] which has not data, will be deleted for new index create.",
                    self.table_id,
                    last_index_name,
                )
            # 否则原来的index不动，新增一个index，并把alias指向过去
            else:
                new_index = current_index_info["index"] + 1
                logger.info("table_id->[%s] index->[%s] has data, so new index will create", self.table_id, new_index)

        # 但凡涉及到index新增，都使用v2版本的格式
        new_index_name = self.make_index_name(now_datetime_object, new_index, "v2")
        logger.info("table_id->[%s] will create new index->[%s]", self.table_id, new_index_name)

        # 2.1 创建新的index
        es_client.indices.create(index=new_index_name, body=self.index_body, params={"request_timeout": 30})
        logger.info("table_id->[%s] new index_name->[%s] is created now", self.table_id, new_index_name)

        return True

    def clean_index(self):
        """
        清理过期index的操作
        :return: int(清理的index个数) | raise Exception
        """
        # 1. 计算获取当前超时时间节点
        expired_datetime_point = datetime.datetime.utcnow() - datetime.timedelta(days=self.retention)
        logger.debug(
            "going to clean table->[{}] es storage index, expired time is->[{}]".format(
                self.table_id, expired_datetime_point.strftime(self.date_format)
            )
        )

        # 2. 获取这个table_id相关的所有index名字
        es_client = self.get_client()
        index_list = es_client.indices.get("{}*".format(self.index_name))
        delete_count = 0

        # 3. 遍历所有的index
        for index_name in list(index_list.keys()):
            # 获取这个index对应的时间内容，并反序列到datetime对象
            result = self.index_re.match(index_name)
            # 如果拿不到正则的匹配成功，需要跳过
            if result is None:
                logger.warning(
                    "table_id->[{}] got index->[{}] which is not match index_re, something go wrong?".format(
                        self.table_id, index_name
                    )
                )
                continue

            # 需要将时间字符串反序列化为datetime object
            datetime_str = result.group("datetime")
            try:
                index_datetime_object = datetime.datetime.strptime(datetime_str, self.date_format)
            except ValueError:
                logger.error(
                    "table_id->[{}] got index->[{}] with datetime_str->[{}] which is not match date_format->"
                    "[{}], something go wrong?".format(self.table_id, index_name, datetime_str, self.date_format)
                )
                continue

            # 判断datetime是否已经小于时间节点
            if index_datetime_object > expired_datetime_point:
                # 未小于，放过他
                logger.info(
                    "table_id->[{}] got index->[{}] which still available, clean later?".format(
                        self.table_id, index_name
                    )
                )
                continue

            # 如果小于时间节点，需要将index清理
            es_client.indices.delete(index_name)
            logger.info(
                "table_id->[{}] now has delete index_name->[{}] for datetime->[{}]".format(
                    self.table_id, index_name, datetime_str
                )
            )
            delete_count += 1

        logging.info("table_id->[{}] clean es index success with count->[{}]".format(self.table_id, delete_count))
        return delete_count

    def get_alias_datetime_str(self, alias_name):
        # 判断是否是需要的格式
        # write_xxx
        alias_write_re = self.write_alias_re
        # xxx_read
        alias_read_re = self.read_alias_re
        # xxx_write
        old_write_alias_re = self.old_write_alias_re

        # 匹配并获取时间字符串
        write_result = alias_write_re.match(alias_name)
        if write_result is not None:
            return write_result.group("datetime")
        read_result = alias_read_re.match(alias_name)
        if read_result is not None:
            return read_result.group("datetime")
        old_write_result = old_write_alias_re.match(alias_name)
        if old_write_result is not None:
            return old_write_result.group("datetime")
        return ""

    def clean_index_v2(self):
        """
        清理过期的写入别名及index的操作，如果发现某个index已经没有写入别名，那么将会清理该index
        :return: int(清理的index个数) | raise Exception
        """
        # 获取所有的写入别名
        es_client = self.get_client()

        alias_list = es_client.indices.get_alias(index=f"*{self.index_name}_*_*")

        filter_result = self.group_expired_alias(alias_list, self.retention)

        for index_name, alias_info in filter_result.items():
            if not alias_info["not_expired_alias"]:
                # 如果已经不存在未过期的别名，则将索引删除
                logger.info(
                    "table_id->[%s] has not alias need to keep, will delete the index->[%s].",
                    self.table_id,
                    index_name,
                )
                es_client.indices.delete(index=index_name)
                logger.warning("table_id->[%s] index->[%s] is deleted now.", self.table_id, index_name)
                continue

            elif alias_info["expired_alias"]:
                # 如果存在已过期的别名，则将别名删除
                logger.info(
                    "table_id->[%s] delete_alias_list->[%s] is not empty will delete the alias.",
                    self.table_id,
                    alias_info["expired_alias"],
                )
                es_client.indices.delete_alias(index=index_name, name=",".join(alias_info["expired_alias"]))
                logger.warning(
                    "table_id->[%s] delete_alias_list->[%s] is deleted.", self.table_id, alias_info["expired_alias"]
                )

            logger.info("table_id->[%s] index->[%s] is process done.", self.table_id, index_name)

        logger.info("table_id->[%s] is process done.", self.table_id)

        return True

    def is_mapping_same(self, index_name):
        """
        判断一个index的mapping和数据库当前记录的配置是否一致
        :param index_name: 当前的时间字符串
        :return: {
            # 是否需要创建新的索引
            "should_create": True | False,
            # 新的索引名
            "index": "index_name",
            # 新索引对应的写别名
            "write_alias": "write_alias"
        }
        """
        es_client = self.get_client()

        # 判断最后一个index的配置是否和数据库的一致，如果不是，表示需要重建
        try:
            es_mappings = es_client.indices.get_mapping(index=index_name)[index_name]["mappings"]
            current_mapping = {}
            if es_mappings.get(self.table_id):
                current_mapping = es_mappings[self.table_id]["properties"]
            else:
                current_mapping = es_mappings["properties"]

        except (KeyError, elasticsearch5.NotFoundError):
            logger.info("index_name->[{}] is not exists, will think the mapping is not same.".format(index_name))
            return False

        # 判断字段列表是否一致的: _type在ES7.x版本后取消
        if self.es_version < self.ES_REMOVE_TYPE_VERSION:
            es_properties = self.index_body["mappings"][self.table_id]["properties"]
        else:
            es_properties = self.index_body["mappings"]["properties"]
        database_field_list = list(es_properties.keys())
        current_field_list = list(current_mapping.keys())

        field_diff_set = set(database_field_list) ^ set(current_field_list)
        if len(field_diff_set) != 0:
            logger.info(
                "table_id->[{}] index->[{}] found differ field->[{}] will thing not same".format(
                    self.table_id, index_name, field_diff_set
                )
            )
            return False

        # 遍历判断字段的内容是否完全一致
        for field_name, database_config in list(es_properties.items()):
            try:
                current_config = current_mapping[field_name]

            except KeyError:
                logger.info(
                    "table_id->[{}] found field->[{}] is missing in current_mapping->[{}], "
                    "will delete it and recreate."
                )
                return False

            # 判断具体的内容是否一致，只要判断具体的四个内容
            for field_config in ["type", "include_in_all", "doc_values", "format"]:
                database_value = database_config.get(field_config, None)
                current_value = current_config.get(field_config, None)

                if field_config == "type" and current_value is None:
                    logger.info(
                        "table_id->[{}] index->[{}] field->[{}] config->[{}] database->[{}] es config is None, "
                        "so nothing will do.".format(
                            self.table_id, index_name, field_name, field_config, database_value
                        )
                    )
                    continue

                if database_value != current_value:
                    logger.info(
                        "table_id->[{}] index->[{}] field->[{}] config->[{}] database->[{}] es->[{}] is "
                        "not the same, ".format(
                            self.table_id, index_name, field_name, field_config, database_value, current_value
                        )
                    )
                    return False

        logger.info("table_id->[{}] index->[{}] field config same.".format(self.table_id, index_name))
        return True

    def get_tag_values(self, tag_name):
        """
        curl -XGET  http://es.service.consul:10004/2_bklog_abcde_20200608_0/_search?pretty -d '
        {
            "aggs" : {
                "field_values" : {
                    "terms" : { "field" : "serverIp", "size":10000 }
                }
            },
            "size" : 0
        }'
        response ==>
        {
            "took" : 301,
            "timed_out" : false,
            "_shards" : {
                "total" : 5,
                "successful" : 5,
                "failed" : 0
            },
            "hits" : {
                "total" : 2124190,
                "max_score" : 0.0,
                "hits" : [ ]
            },
            "aggregations" : {
                "field_values" : {
                    "doc_count_error_upper_bound" : 0,
                    "sum_other_doc_count" : 0,
                    "buckets" : [{
                        "key" : "10.0.0.1",
                        "doc_count" : 2124190
                    }]
                }
            }
        }
        """
        es_client = self.get_client()
        index_list = es_client.indices.get("{}*".format(self.index_name))

        result = []
        for index_name in index_list:
            body = {"aggs": {"field_values": {"terms": {"field": tag_name, "size": 10000}}}, "size": 0}
            res = es_client.search(index=index_name, body=body)
            buckets = res["aggregations"]["field_values"]["buckets"]
            tag_values = [bucket["key"] for bucket in buckets]
            result += tag_values

        return result

    def group_expired_alias(self, alias_list, expired_days):
        """
        将每个索引的别名进行分组，分为已过期和未过期
        :param alias_list: 别名列表，格式
        {
            "2_bkmonitor_event_1500498_20200603_0":{
                "aliases":{
                    "2_bkmonitor_event_1500498_20200603_write":{},
                    "write_20200603_2_bkmonitor_event_1500498":{}
                }
            }
        }
        :param expired_days: 过期时间，单位天
        :return: 格式
        {
            "2_bkmonitor_event_1500498_20200603_0": {
                "expired_alias": ["write_20200603_2_bkmonitor_event_1500498"],
                "not_expired_alias: ["write_20200602_2_bkmonitor_event_1500498"],
            }
        }
        """
        logger.info("table_id->[%s] filtering expired alias before %s days.", self.table_id, expired_days)

        expired_datetime_point = datetime.datetime.utcnow() - datetime.timedelta(days=expired_days)

        filter_result = {}

        for index_name, alias_info in alias_list.items():

            expired_alias = []
            not_expired_alias = []

            # 遍历所有的alias是否需要删除
            for alias_name in alias_info["aliases"]:

                logger.info("going to process table_id->[%s] ", self.table_id)

                # 判断这个alias是否命中正则，是否需要删除的范围内
                datetime_str = self.get_alias_datetime_str(alias_name)

                if not datetime_str:
                    # 匹配不上时间字符串的情况，一般是因为用户自行创建了别名
                    if settings.ES_RETAIN_INVALID_ALIAS:
                        # 保留不合法的别名，将该别名视为未过期
                        not_expired_alias.append(alias_name)
                        logger.info(
                            "table_id->[%s] index->[%s] got alias_name->[%s] " "not match datetime str, retain it.",
                            self.table_id,
                            index_name,
                            alias_name,
                        )
                    else:
                        # 不保留不合法的别名，将该别名视为已过期
                        expired_alias.append(alias_name)
                        logger.info(
                            "table_id->[%s] index->[%s] got alias_name->[%s] not match datetime str, remove it.",
                            self.table_id,
                            index_name,
                            alias_name,
                        )
                    continue

                try:
                    index_datetime_object = datetime.datetime.strptime(datetime_str, self.date_format)
                except ValueError:
                    logger.error(
                        "table_id->[%s] got index->[%s] with datetime_str->[%s] which is not match date_format->"
                        "[%s], something go wrong?",
                        self.table_id,
                        index_name,
                        datetime_str,
                        self.date_format,
                    )
                    continue

                # 检查当前别名是否过期
                logger.info("%s %s", index_datetime_object, expired_datetime_point)
                if index_datetime_object > expired_datetime_point:
                    logger.info(
                        "table_id->[%s] got alias->[%s] for index->[%s] is not expired.",
                        self.table_id,
                        alias_name,
                        index_name,
                    )
                    not_expired_alias.append(alias_name)
                else:
                    logger.info(
                        "table_id->[%s] got alias->[%s] for index->[%s] is expired.",
                        self.table_id,
                        alias_name,
                        index_name,
                    )
                    expired_alias.append(alias_name)

            filter_result[index_name] = {
                "expired_alias": expired_alias,
                "not_expired_alias": not_expired_alias,
            }

        return filter_result

    def reallocate_index(self):
        """
        重新分配索引所在的节点
        """
        if self.warm_phase_days <= 0:
            logger.info("table_id->[%s] warm_phase_days is not set, skip.", self.table_id)
            return

        warm_phase_settings = self.warm_phase_settings
        allocation_attr_name = warm_phase_settings["allocation_attr_name"]
        allocation_attr_value = warm_phase_settings["allocation_attr_value"]
        allocation_type = warm_phase_settings["allocation_type"]

        es_client = self.get_client()

        # 获取索引对应的别名
        alias_list = es_client.indices.get_alias(index=f"*{self.index_name}_*_*")

        filter_result = self.group_expired_alias(alias_list, self.warm_phase_days)

        # 如果存在未过期的别名，那说明这个索引仍在被写入，不能把它切换到冷节点
        reallocate_index_list = [
            index_name for index_name, alias in filter_result.items() if not alias["not_expired_alias"]
        ]

        # 如果没有过期的索引，则返回
        if not reallocate_index_list:
            logger.info(
                "table_id->[%s] no index should be allocated, skip.",
                self.table_id,
            )
            return

        ilo = IndexList(es_client, index_names=reallocate_index_list)
        # 过滤掉已经被 allocate 过的 index
        ilo.filter_allocated(key=allocation_attr_name, value=allocation_attr_value, allocation_type=allocation_type)

        # 过滤后索引为空，则返回
        if not ilo.indices:
            logger.info(
                "table_id->[%s] no index should be allocated, skip.",
                self.table_id,
            )
            return

        logger.info(
            "table_id->[%s] ready to reallocate with settings: days(%s), name(%s), value(%s), type(%s), "
            "for index_list: %s",
            self.table_id,
            self.warm_phase_days,
            allocation_attr_name,
            allocation_attr_value,
            allocation_type,
            ilo.indices,
        )

        try:
            # 执行 allocation 动作
            allocation = curator.Allocation(
                ilo=ilo,
                key=allocation_attr_name,
                value=allocation_attr_value,
                allocation_type=allocation_type,
            )
            allocation.do_action()
        except curator.NoIndices:
            # 过滤后索引列表为空，则返回
            if not ilo.indices:
                logger.info(
                    "table_id->[%s] no index should be allocated, skip.",
                    self.table_id,
                )
                return
        except Exception as e:
            logger.exception("table_id->[%s] error occurred when allocate: %s", self.table_id, e)
        else:
            logger.info("table_id->[%s] index->[%s] allocate success!", self.table_id, ilo.indices)


class BkDataStorage(models.Model, StorageResultTable):
    STORAGE_TYPE = ClusterInfo.TYPE_BKDATA

    # 对应ResultTable的table_id
    table_id = models.CharField(_("结果表名"), max_length=128, primary_key=True)

    # 对应计算平台的接入配置ID
    raw_data_id = models.IntegerField(_("接入配置ID"), default=-1)
    etl_json_config = models.TextField(_("清洗配置"))
    bk_data_result_table_id = models.CharField(_("计算平台的结果表名"), max_length=64)

    def __unicode__(self):
        return "{}->{}".format(self.table_id, self.raw_data_id)

    class Meta:
        verbose_name = _("bkdata存储配置")
        verbose_name_plural = _("bkdata存储配置")

    def get_client(self):
        pass

    def add_field(self, field):
        """
        字段变更的时候需要同步变更计算平台清洗逻辑，以及统计计算节点

        这个变更动作很重，需要放到后台异步任务去执行
        """
        pass

    @property
    def consul_config(self):
        """
        bkdata的storage暂时不需要同步配置到consul，故返回空数据
        """
        return {}

    @classmethod
    def create_table(cls, table_id, is_sync_db=False, is_access_now=False, **kwargs):
        try:
            bkdata_storage = BkDataStorage.objects.get(table_id=table_id)
        except BkDataStorage.DoesNotExist:
            bkdata_storage = BkDataStorage.objects.create(table_id=table_id)

        bkdata_storage.update_storage(is_access_now=is_access_now, **kwargs)

    def update_storage(self, is_access_now=False, **kwargs):
        # 如果立马接入，则在当前进程直接执行，否则走celery异步任务来同步
        if is_access_now:
            self.access_to_bk_data()
        else:
            from metadata.task import tasks

            tasks.access_to_bk_data_task.apply_async(args=(self.table_id,), countdown=60)

    def create_databus_clean(self, result_table):
        try:
            kafka_storage = KafkaStorage.objects.get(table_id=result_table.table_id)
        except KafkaStorage.DoesNotExist:
            raise ValueError(_("结果表[{}]数据未写入消息队列，请确认后重试".format(result_table.table_id)))

        # 增加接入部署计划
        topic = kafka_storage.topic
        partition = kafka_storage.partition
        consul_config = kafka_storage.storage_cluster.consul_config

        domain = consul_config.get("cluster_config", {}).get("domain_name")
        port = consul_config.get("cluster_config", {}).get("port")
        broker_url = settings.BK_DATA_KAFKA_BROKER_URL or "{}:{}".format(domain, port)
        is_sasl = consul_config.get("cluster_config", {}).get("is_ssl_verify")
        user = consul_config.get("auth_info", {}).get("username")
        passwd = consul_config.get("auth_info", {}).get("password")
        KAFKA_CONSUMER_GROUP_NAME = "access_to_bk_data_consumer_group"

        # 计算平台要求，raw_data_name不能超过50个字符
        raw_data_name = "{}_{}".format(settings.BK_DATA_RT_ID_PREFIX, result_table.table_id.replace(".", "__"))[-50:]
        params = {
            "data_scenario": "queue",
            "bk_biz_id": settings.BK_DATA_BK_BIZ_ID,
            "description": "",
            "access_raw_data": {
                "raw_data_name": raw_data_name,
                "maintainer": settings.BK_DATA_PROJECT_MAINTAINER,
                "raw_data_alias": result_table.table_name_zh,
                "data_source": "kafka",
                "data_encoding": "UTF-8",
                "sensitivity": "private",
                "description": "接入配置 ({})".format(result_table.table_name_zh),
                "tags": [],
                "data_source_tags": ["src_kafka"],
            },
            "access_conf_info": {
                "collection_model": {"collection_type": "incr", "start_at": 1, "period": "-1"},
                "resource": {
                    "type": "kafka",
                    "scope": [
                        {
                            "master": broker_url,
                            "group": KAFKA_CONSUMER_GROUP_NAME,
                            "topic": topic,
                            "tasks": partition,
                            "use_sasl": is_sasl,
                            "security_protocol": "SASL_PLAINTEXT",
                            "sasl_mechanism": "SCRAM-SHA-512",
                            "user": user,
                            "password": passwd,
                        }
                    ],
                },
            },
        }
        try:
            result = api.bkdata.access_deploy_plan(**params)
            logger.info("access to bkdata, result:%s", result)

            self.raw_data_id = result["raw_data_id"]
            self.save()
        except Exception:  # noqa
            logger.exception("access to bkdata failed, params:%s", params)
            raise  # 这里继续往外抛出去

    def access_to_bk_data(self):
        """
        1. 先看是否已经接入，没有接入则继续
            第一步：
                - 按kafka逻辑，接入到100147业务下
                - 走access/deploy_plan接口配置kafka接入
                - 走databus/cleans接口配置清洗规则
                - 走databus/tasks接口启动清洗

            第二步：
                - 走auth/tickets接口将100147业务的表授权给某个项目
                - 走dataflow/flow/flows接口创建出一个画布
                - 走dataflow/flow/flows/{flow_id}/nodes/接口创建画布上的实时数据源、统计节点、存储节点
                - 走dataflow/flow/flows/{flow_id}/start/接口启动任务

        2. 已经接入，则走更新逻辑
            - 判断字段是否有变更，无变更则退出，有变更则继续
            - 走access/deploy_plan/{raw_data_id}/接口更新接入计划
            - 走databus/cleans/{processing_id}/接口更新清洗配置
            - 走dataflow/flow/flows/{fid}/nodes/{nid}/接口更新计算节点 & 存储节点
            - 走dataflow/flow/flows/{flow_id}/restart/接口重启任务

        :return:
        """
        try:
            result_table = ResultTable.objects.get(table_id=self.table_id)
        except ResultTable.DoesNotExist:
            raise ValueError(_("结果表%s不存在，请确认后重试") % self.table_id)

        if self.raw_data_id == -1:
            self.create_databus_clean(result_table)

        # 增加清洗配置
        json_config, fields = self.generate_bk_data_etl_config()
        etl_json_config = json.dumps(json_config)
        if self.etl_json_config != etl_json_config:
            bk_data_rt_id_without_biz_id = gen_bk_data_rt_id_without_biz_id(self.table_id)
            result_table_id = "{}_{}".format(settings.BK_DATA_BK_BIZ_ID, bk_data_rt_id_without_biz_id)
            params = {
                "raw_data_id": self.raw_data_id,
                "json_config": etl_json_config,
                "pe_config": "",
                "bk_biz_id": settings.BK_DATA_BK_BIZ_ID,
                "description": "清洗配置 ({})".format(result_table.table_name_zh),
                "clean_config_name": "清洗配置 ({})".format(result_table.table_name_zh),
                "result_table_name": bk_data_rt_id_without_biz_id,
                "result_table_name_alias": result_table.table_name_zh,
                "fields": fields,
            }
            if self.etl_json_config:
                # 如果已经有清洗配置，则做更新动作
                # 更新：停止清洗任务  -> 修改清洗配置  ->  启动清洗配置
                try:
                    result = api.bkdata.stop_databus_cleans(result_table_id=result_table_id, storages=["kafka"])
                except Exception:  # noqa
                    logger.exception("stop bkdata databus clean failed, param:%s", params)
                    return
                logger.info("stop bkdata databus clean success, result:%s", result)

                try:
                    params["processing_id"] = result_table_id
                    result = api.bkdata.update_databus_cleans(**params)
                except Exception:  # noqa
                    logger.exception("update databus clean to bkdata failed, params:%s", params)
                    return

                logger.info("update databus clean to bkdata success, result:%s", result)
            else:
                # 如果没有清洗配置，则做创建动作
                # 创建：新增清洗配置  ->  启动清洗配置
                try:
                    result = api.bkdata.databus_cleans(**params)
                except Exception:  # noqa
                    logger.exception("add databus clean to bkdata failed, params:%s", params)
                    return

                logger.info("add databus clean to bkdata, result:%s", result)

            # 启动清洗任务
            try:
                result = api.bkdata.start_databus_cleans(result_table_id=result_table_id, storages=["kafka"])
            except Exception:  # noqa
                logger.exception("start bkdata databus clean failed, param:%s", params)
                return
            logger.info("start bkdata databus clean success, result:%s", result)

            self.etl_json_config = etl_json_config
            self.bk_data_result_table_id = result_table_id
            self.save()

            # 提前做一次授权，授权给某个项目
            auth.ensure_has_permission_with_rt_id(
                settings.BK_DATA_PROJECT_MAINTAINER, result_table_id, int(settings.BK_DATA_PROJECT_ID)
            )

        # filter_unknown_time_with_result_table 过滤掉未来时间后再入库
        if self.filter_unknown_time_with_result_table():
            time.sleep(60)  # 两个dataflow的创建需要等待，暂时通过等待1分钟的方式，后续优化成pipeline的形式
            self.full_cmdb_node_info_to_result_table()

    def filter_unknown_time_with_result_table(self):
        """
        通过dataflow过滤掉未来时间, 同时过滤过去时间后，再进行入库
        """
        from metadata.models.result_table import ResultTableField

        qs = ResultTableField.objects.filter(table_id=self.table_id)
        if not qs.exists():
            return False

        metric_fields = []
        dimension_fields = []
        for field in qs:
            if field.tag in [ResultTableField.FIELD_TAG_DIMENSION, ResultTableField.FIELD_TAG_GROUP]:
                dimension_fields.append(field.field_name)
            elif field.tag in [ResultTableField.FIELD_TAG_METRIC, ResultTableField.FIELD_TAG_TIMESTAMP]:
                metric_fields.append(field.field_name)

        task = FilterUnknownTimeTask(
            rt_id=self.bk_data_result_table_id,
            metric_field=metric_fields,
            dimension_fields=dimension_fields,
        )
        try:
            task.create_flow()
            task.start_flow()
        except Exception:  # noqa
            logger.exception(
                "create/start flow({}) failed, result_id:({})".format(task.flow_name, self.bk_data_result_table_id)
            )
            return False
        logger.info("create flow({}) successfully, result_id:({})".format(task.flow_name, self.bk_data_result_table_id))
        return True

    def generate_bk_data_etl_config(self):
        from metadata.models.result_table import ResultTableField

        qs = ResultTableField.objects.filter(table_id=self.table_id)
        etl_dimension_assign = []
        etl_metric_assign = []
        etl_time_assign = []
        time_field_name = "time"

        fields = []
        i = 1
        for field in qs:
            if field.tag in [ResultTableField.FIELD_TAG_DIMENSION, ResultTableField.FIELD_TAG_GROUP]:
                fields.append(
                    {
                        "field_name": field.field_name,
                        "field_type": "string",
                        "field_alias": field.description or field.field_name,
                        "is_dimension": True,
                        "field_index": i,
                    }
                )
                etl_dimension_assign.append({"type": "string", "key": field.field_name, "assign_to": field.field_name})
            elif field.tag == ResultTableField.FIELD_TAG_METRIC:
                # 计算平台没有float类型，这里使用double做一层转换
                # 监控的int类型转成计算平台的long类型
                field_type = field.field_type
                if field.field_type == ResultTableField.FIELD_TYPE_FLOAT:
                    field_type = "double"
                elif field.field_type == ResultTableField.FIELD_TYPE_INT:
                    field_type = "long"
                fields.append(
                    {
                        "field_name": field.field_name,
                        "field_type": field_type,
                        "field_alias": field.description or field.field_name,
                        "is_dimension": False,
                        "field_index": i,
                    }
                )
                etl_metric_assign.append({"type": field_type, "key": field.field_name, "assign_to": field.field_name})
            elif field.tag == ResultTableField.FIELD_TAG_TIMESTAMP:
                time_field_name = field.field_name
                fields.append(
                    {
                        "field_name": field.field_name,
                        "field_type": "string",
                        "field_alias": field.description or field.field_name,
                        "is_dimension": False,
                        "field_index": i,
                    }
                )
                etl_time_assign.append({"type": "string", "key": field.field_name, "assign_to": field.field_name})
            else:
                continue

            i += 1

        return (
            {
                "extract": {
                    "args": [],
                    "type": "fun",
                    "label": "label6356db",
                    "result": "json",
                    "next": {
                        "type": "branch",
                        "name": "",
                        "label": None,
                        "next": [
                            {
                                "type": "access",
                                "label": "label5a9c45",
                                "result": "dimensions",
                                "next": {
                                    "type": "assign",
                                    "label": "labelb2c1cb",
                                    "subtype": "assign_obj",
                                    "assign": etl_dimension_assign,
                                    "next": None,
                                },
                                "key": "dimensions",
                                "subtype": "access_obj",
                            },
                            {
                                "type": "access",
                                "label": "label65f2f1",
                                "result": "metrics",
                                "next": {
                                    "type": "assign",
                                    "label": "labela6b250",
                                    "subtype": "assign_obj",
                                    "assign": etl_metric_assign,
                                    "next": None,
                                },
                                "key": "metrics",
                                "subtype": "access_obj",
                            },
                            {
                                "type": "assign",
                                "label": "labelecd758",
                                "subtype": "assign_obj",
                                "assign": etl_time_assign,
                                "next": None,
                            },
                        ],
                    },
                    "method": "from_json",
                },
                "conf": {
                    "timezone": 8,
                    "output_field_name": "timestamp",
                    "time_format": "Unix Time Stamp(seconds)",
                    "time_field_name": time_field_name,
                    "timestamp_len": 10,
                    "encoding": "UTF-8",
                },
            },
            fields,
        )

    def create_statistics_data_flow(self, agg_interval):
        """
        创建好统计的dataflow, 按指定的聚合周期

        实时数据源(数据源节点)  ->  按sql统计聚合(计算节点)  ->  tspider存储（存储节点）

        :param agg_interval: 统计聚合
        :return:
        """
        from metadata.models.result_table import ResultTableField

        qs = ResultTableField.objects.filter(table_id=self.table_id)
        metric_fields = []
        dimension_fields = []
        for field in qs:
            if field.tag in [ResultTableField.FIELD_TAG_DIMENSION, ResultTableField.FIELD_TAG_GROUP]:
                dimension_fields.append(field.field_name)
            elif field.tag == ResultTableField.FIELD_TAG_METRIC:
                metric_fields.append(field.field_name)

        task = StatisticTask(
            rt_id=self.bk_data_result_table_id,
            agg_interval=agg_interval,
            agg_method="MAX",
            metric_field=metric_fields,
            dimension_fields=dimension_fields,
        )
        try:
            task.create_flow()
            task.start_flow()
        except Exception:  # noqa
            logger.exception(
                "create/start flow({}) failed, result_id:({})".format(task.flow_name, self.bk_data_result_table_id)
            )
            return
        logger.info("create flow({}) successfully, result_id:({})".format(task.flow_name, self.bk_data_result_table_id))

    def full_cmdb_node_info_to_result_table(self):
        from metadata.models.result_table import ResultTableField

        qs = ResultTableField.objects.filter(table_id=self.table_id)
        if not qs.exists():
            return

        metric_fields = []
        dimension_fields = []
        for field in qs:
            if field.tag in [ResultTableField.FIELD_TAG_DIMENSION, ResultTableField.FIELD_TAG_GROUP]:
                dimension_fields.append(field.field_name)
            elif field.tag == ResultTableField.FIELD_TAG_METRIC:
                metric_fields.append(field.field_name)

        task = CMDBPrepareAggregateTask(
            rt_id=to_bk_data_rt_id(self.table_id, settings.BK_DATA_RAW_TABLE_SUFFIX),
            agg_interval=0,
            agg_method="",
            metric_field=metric_fields,
            dimension_fields=dimension_fields,
        )
        try:
            task.create_flow()
            task.start_flow()
        except Exception:  # noqa
            logger.exception(
                "create/start flow({}) failed, result_id:({})".format(task.flow_name, self.bk_data_result_table_id)
            )
            return
        logger.info("create flow({}) successfully, result_id:({})".format(task.flow_name, self.bk_data_result_table_id))
