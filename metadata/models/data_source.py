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


import copy
import datetime
import json
import logging
import traceback
import uuid

import kafka
import six
from django.conf import settings
from django.db import models
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from kazoo.client import KazooClient

from bkmonitor.utils import consul
from core.drf_resource import api
from core.errors.api import BKAPIError
from metadata import config
from metadata.utils import consul_tools, hash_util

from .common import Label, OptionBase
from .storage import ClusterInfo, KafkaTopicInfo

ResultTable = None
ResultTableField = None
ResultTableRecordFormat = None
ResultTableOption = None

logger = logging.getLogger("metadata")


class DataSource(models.Model):
    """数据源配置"""

    # 默认使用的MQ类型
    DEFAULT_MQ_TYPE = ClusterInfo.TYPE_KAFKA
    # DATA_LIST列表
    CONSUL_DATA_LIST_PATH = "{}/{}".format(config.CONSUL_PATH, "data_list")

    # 消息队列配置对应关系配置
    MQ_CONFIG_DICT = {ClusterInfo.TYPE_KAFKA: KafkaTopicInfo}

    # 需要指定是纳秒级别的清洗配置内容
    NS_TIMESTAMP_ETL_CONFIG = {"bk_standard_v2_event", "bk_standard_v2_time_series"}

    bk_data_id = models.AutoField(_("数据源ID"), primary_key=True)
    # data_source的token, 用于供各个自定义上报对data_id进行校验，防止恶意上报, 但是对于已有的data_id由于不是自定义，不做处理
    token = models.CharField(_("上报校验token"), max_length=32, default="")
    data_name = models.CharField(_("数据源名称"), max_length=128, db_index=True, unique=True)
    data_description = models.TextField(_("数据源描述"))
    # 对应StorageCluster 记录ID
    mq_cluster_id = models.IntegerField(_("消息队列集群ID"))
    # 对应KafkaTopicInfo 记录ID
    # 后续如果是切换到其他的MQ，可以增加新的消息队列配置表，增加一个data_id对应的mq_type字段
    mq_config_id = models.IntegerField(_("消息队列配置ID"))
    # json格式的记录 或 内容清洗模板的名称
    etl_config = models.TextField(_("ETL配置"))
    is_custom_source = models.BooleanField(_("是否自定义数据源"))
    creator = models.CharField(_("创建者"), max_length=32)
    create_time = models.DateTimeField(_("创建时间"), auto_now_add=True)
    last_modify_user = models.CharField(_("最后更新者"), max_length=32)
    last_modify_time = models.DateTimeField(_("最后更新时间"), auto_now=True)
    # 标签配置
    # 但是此处将所有的默认值都置为了other，原因是实际这些配置不会用上，在migrations会将标签都修改为符合预期的内容
    # 此处只是为了安慰django migrations
    # 数据类型，表明数据是时序数据、时间数据、事件数据
    type_label = models.CharField(verbose_name=_("数据类型标签"), max_length=128, default=Label.RESULT_TABLE_LABEL_OTHER)
    # 数据源，表明数据是从渠道上来的，可能有bk_monitor, bk_data, custom
    source_label = models.CharField(verbose_name=_("数据源标签"), max_length=128, default=Label.RESULT_TABLE_LABEL_OTHER)
    # 自定义标签信息，供各个信息注入各种自定义内容使用
    # 没有使用description，因为前者是供用户读而用的，提供格式化的数据并不合适
    custom_label = models.CharField(verbose_name=_("自定义标签信息"), max_length=256, default=None, null=True)
    source_system = models.CharField(verbose_name=_("请求来源的系统"), max_length=256, default=settings.SAAS_APP_CODE)
    # 是否启用数据源
    is_enable = models.BooleanField(verbose_name=_("数据源是否启用"), default=True)

    transfer_cluster_id = models.CharField(verbose_name=_("transfer集群ID"), default="default", max_length=50)

    class Meta:
        verbose_name = _("数据源管理")
        verbose_name_plural = _("数据源管理表")

    def __init__(self, *args, **kwargs):
        super(DataSource, self).__init__(*args, **kwargs)
        # just for IDE
        self._mq_cluster = None
        self._mq_config = None

    @staticmethod
    def make_token():
        """生成一个随机的token"""
        return uuid.uuid4().hex

    @property
    def mq_cluster(self):
        """返回数据源的消息队列类型"""
        # 这个配置应该是很少变化的，所以考虑增加缓存
        if getattr(self, "_mq_cluster", None) is None:
            self._mq_cluster = ClusterInfo.objects.get(cluster_id=self.mq_cluster_id)

        return self._mq_cluster

    @property
    def consul_config_path(self):
        """返回当前consul的配置路径"""
        return config.CONSUL_DATA_ID_PATH_FORMAT.format(
            transfer_cluster_id=self.transfer_cluster_id, data_id=self.bk_data_id
        )

    @property
    def consul_fields_path(self):
        """返回当前consul字段的配置路径"""
        return f"{self.consul_config_path}/fields"

    @property
    def zk_config_path(self):
        """返回当前zk的配置路径"""

        return "{}/{}".format(config.ZK_GSE_DATA_ID_INFO_PREFIX, self.bk_data_id)

    @property
    def mq_config(self):
        """获取data_id对应消息队列的配置信息"""
        if getattr(self, "_mq_config", None) is None:
            self._mq_config = KafkaTopicInfo.objects.get(bk_data_id=self.bk_data_id)

        return self._mq_config

    def to_json(self, is_consul_config=False):
        """返回当前data_id的配置字符串"""

        # 获取ResultTable的配置
        result_table_id_list = [
            info.table_id for info in DataSourceResultTable.objects.filter(bk_data_id=self.bk_data_id)
        ]

        result_table_info_list = []
        # 判断需要未删除，而且在启用状态的结果表
        for result_table in ResultTable.objects.filter(
            table_id__in=result_table_id_list, is_deleted=False, is_enable=True
        ):
            field_list = [
                field_info.to_json(is_consul_config)
                for field_info in ResultTableField.objects.filter(table_id=result_table.table_id)
            ]

            shipper_list = []
            for real_table in result_table.real_storage_list:
                consul_config = real_table.consul_config
                if consul_config:
                    shipper_list.append(consul_config)

            result_table_info_list.append(
                {
                    "result_table": result_table.table_id,
                    "shipper_list": shipper_list,
                    "field_list": field_list,
                    "schema_type": result_table.schema_type,
                    "option": ResultTableOption.get_option(result_table.table_id),
                }
            )

        mq_config = {"storage_config": {"topic": self.mq_config.topic, "partition": self.mq_config.partition}}
        # 添加集群信息
        mq_config.update(self.mq_cluster.consul_config)
        mq_config["cluster_config"].pop("last_modify_time")

        result_config = {
            "bk_data_id": self.bk_data_id,
            "data_id": self.bk_data_id,
            "mq_config": mq_config,
            "etl_config": self.etl_config,
            "result_table_list": result_table_info_list,
            "option": DataSourceOption.get_option(self.bk_data_id),
            "type_label": self.type_label,
            "source_label": self.source_label,
            "token": self.token,
            "transfer_cluster_id": self.transfer_cluster_id,
        }

        return result_config

    @property
    def zk_config(self):
        """返回当前data_id的在zk上的配置字符串"""

        return {
            "server_id": -1,
            # 此处不拿topic最后一个字符的原因是：
            # 1. GSE的topic拼接规则是 ${data_set}${biz_id}
            # 2. 监控写死biz_id为0，所以在初始化的时候，会将topic追加一个0结尾
            # 3. 所以在提供给GSE DATA的时候，需要将这个0摘掉
            "data_set": six.text_type(self.mq_config.topic[:-1]),
            "partition": self.mq_config.partition,
            "cluster_index": config.ZK_GSE_DATA_CLUSTER_ID,
            "biz_id": 0,
            "msg_system": 1,
            # 增加一个蓝鲸监控配置的标志位
            "bkmonitor_config": True,
        }

    @property
    def gse_route_config(self):
        """
        返回当前data_id在gse的路由配置
        """
        route_name = "stream_to_{}_{}_{}".format(
            config.DEFAULT_GSE_API_PLAT_NAME, self.DEFAULT_MQ_TYPE, self.mq_config.topic
        )
        return {
            "name": route_name,
            "stream_to": {
                "stream_to_id": self.mq_cluster.gse_stream_to_id,
                self.DEFAULT_MQ_TYPE: {
                    "topic_name": self.mq_config.topic,
                    "data_set": six.text_type(self.mq_config.topic[:-1]),
                    "partition": self.mq_config.partition,
                    "biz_id": 0,
                },
            },
        }

    @property
    def is_field_discoverable(self):
        """
        返回该dataSource下覆盖的结果表是否可以支持字段自发现
        :return:
        """
        return self.etl_config == "bk_standard"

    @classmethod
    def refresh_consul_data_list(cls):
        """
        更新consul上data_list列表
        :return: True | False
        """
        # data list 在consul中的作用被废弃，不再使用
        pass

    @classmethod
    def apply_for_data_id_from_gse(cls, operator):
        # 从GSE接口分配dataid
        try:
            params = {
                "metadata": {"plat_name": config.DEFAULT_GSE_API_PLAT_NAME},
                "operation": {"operator_name": operator},
            }
            result = api.gse.add_route(**params)
            return result["channel_id"]
        except BKAPIError:
            logger.exception("从GSE申请ChannelID出错")
            raise

    @classmethod
    def create_data_source(
        cls,
        data_name,
        etl_config,
        operator,
        source_label,
        type_label,
        bk_data_id=None,
        mq_cluster=None,
        data_description="",
        is_custom_source=True,
        is_refresh_config=True,
        custom_label=None,
        option=None,
        transfer_cluster_id="default",
        source_system=settings.SAAS_APP_CODE,
    ):
        """
        创建一个新的数据源, 如果创建过程失败则会抛出异常
        :param transfer_cluster_id: transfer 集群ID，默认为 default
        :param data_name: 数据源名称
        :param bk_data_id: 数据源ID，如果未None则自增配置
        :param mq_cluster: Kafka 集群ID，如果为None时，则使用默认的Kafka集群
        :param etl_config: 清洗配置，可以为json格式字符串，或者默认内置的清洗配置函数名
        :param operator: 操作者
        :param source_label: 数据源标签
        :param type_label: 数据类型标签
        :param is_custom_source: 是否自定义数据源
        :param data_description: 数据源描述
        :param is_refresh_config: 是否需要刷新外部依赖配置
        :param custom_label: 自定义标签配置信息
        :param option: 额外配置项，格式应该为字典（object）方式传入，key为配置项，value为配置内容
        :param source_system: 来源注册系统
        :return: DataSource instance | raise Exception
        """
        # 判断两个使用到的标签是否存在
        if not Label.exists_label(label_id=source_label, label_type=Label.LABEL_TYPE_SOURCE) or not Label.exists_label(
            label_id=type_label, label_type=Label.LABEL_TYPE_TYPE
        ):
            logger.error(
                "user->[{}] try to create datasource but use type_label->[{}] or source_type->[{}] "
                "which is not exists.".format(operator, type_label, source_label)
            )
            raise ValueError(_("标签[{} | {}]不存在，请确认后重试").format(source_label, type_label))

        # 1. 判断参数是否符合预期
        # 数据源名称是否重复
        if cls.objects.filter(data_name=data_name).exists():
            logger.error("data_name->[%s] is already exists, maybe something go wrong?" % data_name)
            raise ValueError(_("数据源名称[%s]已经存在，请确认后重试") % data_name)

        try:
            # 如果集群信息无提供，则使用默认的MQ集群信息
            if mq_cluster is None:
                mq_cluster = ClusterInfo.objects.get(cluster_type=cls.DEFAULT_MQ_TYPE, is_default_cluster=True)
            else:
                mq_cluster = ClusterInfo.objects.get(cluster_id=mq_cluster)
        except ClusterInfo.DoesNotExist:
            # 此时，用户无提供新的数据源配置的集群信息，而也没有配置默认的集群信息，新的数据源无法配置集群信息
            # 需要抛出异常
            logger.error(
                "failed to get default MQ for cluster type->[%s], maybe admin set something wrong?"
                % cls.DEFAULT_MQ_TYPE
            )
            raise ValueError(_("缺少数据源MQ集群信息，请联系管理员协助处理"))

        if bk_data_id is None and settings.IS_ASSIGN_DATAID_BY_GSE:
            # 如果由GSE来分配DataID的话，那么从GSE获取data_id，而不是走数据库的自增id
            bk_data_id = cls.apply_for_data_id_from_gse(operator)

        # 此处启动DB事务，创建默认的信息
        with atomic(config.DATABASE_CONNECTION_NAME):
            # 3. 创建新的实例及数据源配置
            # 注意：此处由于已经开启事务，MySQL会保留PK给该新实例，因此可以放心将该PK传给其他依赖model
            data_source = cls.objects.create(
                bk_data_id=bk_data_id,
                data_name=data_name,
                etl_config=etl_config,
                creator=operator,
                mq_cluster_id=mq_cluster.cluster_id,
                is_custom_source=is_custom_source,
                data_description=data_description,
                # 由于mq_config和data_source两者相互指向对方，所以只能先提供占位符，先创建data_source
                mq_config_id=0,
                last_modify_user=operator,
                source_label=source_label,
                type_label=type_label,
                custom_label=custom_label,
                source_system=source_system,
                # 生成token
                token=cls.make_token(),
                is_enable=True,
                transfer_cluster_id=transfer_cluster_id,
            )

            # 由监控自己分配的dataid需要校验是否在合理的范围内
            if not settings.IS_ASSIGN_DATAID_BY_GSE:
                # 判断DATA_ID是否有问题
                if data_source.bk_data_id < config.MIN_DATA_ID:
                    # 如果小于的最小的data_id，需要判断最小ID是否已经分配了，如果没有分配，则使用之
                    if cls.objects.filter(bk_data_id=config.MIN_DATA_ID).exists():
                        logger.info(
                            "new data_id->[%s] and min data_id is exists, maybe something go wrong?"
                            % data_source.bk_data_id
                        )
                        raise ValueError(_("数据源ID生成异常，请联系管理员协助处理"))

                    # 表示不存在最小的ID，使用之
                    # 但在替换DATA_ID之前，需要先将已有的记录清理，否则对于django操作会有两条记录
                    data_source.delete()
                    data_source.bk_data_id = config.MIN_DATA_ID
                    data_source.save()

                # 达到了最大值的判断
                if data_source.bk_data_id > config.MAX_DATA_ID:
                    logger.info(
                        "new data_id->[%s] is lager than max data id->[%s], nothing will create."
                        % data_source.bk_data_id,
                        config.MAX_DATA_ID,
                    )
                    raise ValueError(_("数据源ID分配达到最大上限，请联系管理员协助处理"))

            logger.info(
                "data_id->[{}] data_name->[{}] by operator->[{}] now is pre-create.".format(
                    data_source.bk_data_id, data_source.data_name, data_source.creator
                )
            )

            # 获取这个数据源对应的配置记录model，并创建一个新的配置记录
            mq_config = cls.MQ_CONFIG_DICT[mq_cluster.cluster_type].create_info(bk_data_id=data_source.bk_data_id)
            data_source.mq_config_id = mq_config.id
            data_source.save()
            logger.info(
                "data_id->[%s] now is relate to its mq config id->[%s]"
                % (data_source.bk_data_id, data_source.mq_config_id)
            )

            # 创建option配置
            option = {} if option is None else option
            for option_name, option_value in list(option.items()):
                DataSourceOption.create_option(
                    bk_data_id=data_source.bk_data_id, name=option_name, value=option_value, creator=operator
                )
                logger.info(
                    "bk_data_id->[{}] now has option->[{}] with value->[{}]".format(
                        data_source.bk_data_id, option_name, option_value
                    )
                )

            # 判断是否NS支持的etl配置，如果是，则需要追加option内容
            if etl_config in cls.NS_TIMESTAMP_ETL_CONFIG:
                DataSourceOption.create_option(
                    bk_data_id=data_source.bk_data_id,
                    name=DataSourceOption.OPTION_TIMESTAMP_UNIT,
                    value="ms",
                    creator=operator,
                )
                logger.info(
                    "bk_data_id->[{}] etl_config->[{}] so is has now has option->[{}] with value->[ns]".format(
                        data_source.bk_data_id,
                        DataSourceOption.OPTION_TIMESTAMP_UNIT,
                        DataSourceOption.OPTION_TIMESTAMP_UNIT,
                    )
                )

        # 5. 触发consul刷新, 只有提交了事务后，其他人才可以看到DB记录
        if is_refresh_config:
            try:
                data_source.refresh_outer_config()
                logger.info("data_id->[%s] refresh consul and outer_config done. " % data_source.bk_data_id)

            except Exception:
                logger.error(
                    "data_id->[%s] refresh outer_config failed for->[%s] will wait cron task to finish."
                    % (data_source.bk_data_id, traceback.format_exc())
                )

        logger.info("data->[%s] now IS READY, TRY IT~" % data_source.bk_data_id)

        # 6. 返回新实例
        return data_source

    def update_config(
        self,
        operator,
        data_name=None,
        mq_cluster_id=None,
        etl_config=None,
        data_description=None,
        option=None,
        is_enable=None,
    ):
        """
        更新一个数据源的配置，操作成功将会返回True 否则 抛出异常
        :param operator: 操作者
        :param data_name: 数据源名称
        :param mq_cluster_id: 集群ID
        :param etl_config: 清洗配置修改
        :param data_description: 数据源描述
        :param option: 额外配置项，格式应该为字典（object）方式传入，key为配置项，value为配置内容
        :param is_enable: 是否启用数据源
        :return: True | raise Exception
        """

        # 1. 增加标志位，判断是否有修改成功的记录
        is_change = False

        # 2. 判断和修改请求内容，注意判断修改的内容是否合理
        # 2.1 etl_config的配置是否符合要求
        if etl_config is not None:
            self.etl_config = etl_config
            logger.info("data_id->[{}] got new etl_config->[{}]".format(self.bk_data_id, etl_config))
            is_change = True

        # 2.2 mq_cluster_id集群修改
        if mq_cluster_id is not None:
            # 是否存在，集群配置是否合理
            if not ClusterInfo.objects.filter(cluster_id=mq_cluster_id).exists():
                logger.error("cluster_id->[{}] is not exists, nothing will update.".format(mq_cluster_id))
                raise ValueError(_("集群配置不存在，请确认"))

            self.mq_cluster_id = mq_cluster_id
            logger.info("data_id->[{}] now is point to new cluster_id->[{}]".format(self.bk_data_id, mq_cluster_id))
            is_change = True

        # 2.3 data_name判断是否需要修改
        # 需要提供了data_name，而且data_name与当前的data_name不是一个东东
        if data_name is not None and self.data_name != data_name:

            if self.__class__.objects.filter(data_name=data_name).exists():
                logger.error(
                    "user->[{operator}] try to update data_id->{data_id}] data_name->[{data_name}] "
                    "but data name is already exists, nothing will do".format(
                        operator=operator, data_id=self.bk_data_id, data_name=data_name
                    )
                )
                raise ValueError(_("数据源名称已存在，请确认"))
            self.data_name = data_name
            is_change = True

        # 2.4 修改数据源的描述
        if data_description is not None:
            self.data_description = data_description
            logger.info("data_id->[{}] set new data_description.".format(self.bk_data_id))
            is_change = True

        if option is not None:
            # 更新option配置
            for option_name, option_value in list(option.items()):
                DataSourceOption.create_or_update(
                    bk_data_id=self.bk_data_id, name=option_name, value=option_value, creator=operator
                )
                logger.info(
                    "bk_data_id->[{}] now has option->[{}] with value->[{}]".format(
                        self.bk_data_id, option_name, option_value
                    )
                )

        # 2.5 判断是否需要修改启用标记位
        if is_enable is not None:
            consul_client = consul.BKConsul()

            self.is_enable = is_enable
            logger.info("data_id->[{}] now set is_enable->[{}]".format(self.bk_data_id, self.is_enable))
            is_change = True

            # 判断是否is_change变为了False(数据源禁用)，如果是则需要同时清理consul配置，告知transfer停止写入
            if not is_enable:
                consul_client.kv.delete(self.consul_config_path)
                logger.info("datasource->[%s] now is deleted its consul path." % self.bk_data_id)

            else:
                self.refresh_consul_config()
                logger.info(f"datasource->[{self.bk_data_id}] is enable now refresh consul config.")

        # 3. 如果有成功修改，提交修改
        if is_change:
            # 修改后更新ZK配置 和 consul配置
            self.last_modify_user = operator
            self.save()
            self.refresh_consul_config()
            self.refresh_gse_config()
            logger.info("data_id->[%s] update success and notify zk & consul success." % self.bk_data_id)

        return True

    def refresh_gse_config(self):
        """
        刷新GSE 配置，告知GSE DATA服务最新的MQ配置信息
        :return: True | raise Exception
        """
        if settings.IS_ASSIGN_DATAID_BY_GSE:
            self.refresh_gse_config_to_gse()
        else:
            self.refresh_gse_config_to_zk()

    def add_built_in_channel_id_config_to_gse(self):
        if not config.is_built_in_data_id(self.bk_data_id):
            return

        logger.warning("try to add register built_in channel_id({}) to gse".format(self.bk_data_id))
        params = {
            "metadata": {"channel_id": self.bk_data_id, "plat_name": config.DEFAULT_GSE_API_PLAT_NAME},
            "operation": {"operator_name": settings.COMMON_USERNAME},
            "route": [self.gse_route_config],
        }
        result = api.gse.add_route(**params)
        return result.get("channel_id", -1) == self.bk_data_id

    def refresh_gse_config_to_gse(self):
        """同步路由配置到gse"""
        if self.mq_cluster.gse_stream_to_id == -1:
            raise ValueError("dataid({})的消息队列未初始化，请联系管理员处理".format(self.bk_data_id))

        params = {
            "condition": {"plat_name": config.DEFAULT_GSE_API_PLAT_NAME, "channel_id": self.bk_data_id},
            "operation": {"operator_name": settings.COMMON_USERNAME},
        }
        try:
            result = api.gse.query_route(**params)
            if not result:
                logger.error("can not find route info from gse, please check your datasource config")
                return
        except BKAPIError as e:
            logger.exception("query gse route failed, error:({})".format(e))
            self.add_built_in_channel_id_config_to_gse()
            return

        old_route = None
        for route_info in result:
            if old_route:
                break

            stream_to_info_list = route_info.get("route", [])
            if not stream_to_info_list:
                continue

            for stream_to_info in stream_to_info_list:
                route_name = stream_to_info.get("name", "")
                if route_name != self.gse_route_config["name"]:
                    continue

                old_route = {"name": route_name, "stream_to": stream_to_info["stream_to"]}
                break

        # 有的话，先比对是否一致
        old_hash = hash_util.object_md5(old_route)
        new_hash = hash_util.object_md5(self.gse_route_config)
        if old_hash == new_hash:
            return

        logger.debug(
            "data_id->[{}] gse route config->[{}] is different from gse->[{}],"
            " will refresh it.".format(self.bk_data_id, new_hash, old_hash)
        )

        params = {
            "condition": {"channel_id": self.bk_data_id, "plat_name": config.DEFAULT_GSE_API_PLAT_NAME},
            "operation": {"operator_name": self.creator},
            "specification": {"route": [self.gse_route_config]},
        }
        api.gse.update_route(**params)
        logger.info("data_id->[%s] success to push route info to gse" % self.bk_data_id)

    def refresh_gse_config_to_zk(self):
        """同步zk的配置"""
        for zk_host in config.ZK_GSE_HOST_INFO_LIST:

            # 创建新的data_id配置信息
            zk_client = KazooClient(hosts=zk_host)
            zk_client.start()

            # 确保监控的数据一定是存在
            result_list = [self.zk_config]
            try:

                zk_client.ensure_path(self.zk_config_path)
                # 先尝试将上述路径的内容拿出来
                try:
                    current_zk_config = json.loads(zk_client.get(self.zk_config_path)[0])

                except (ValueError, IndexError):
                    # 如果遇到了异常，则使用一个空的数组
                    current_zk_config = []

                old_zk_config = copy.copy(current_zk_config)
                # 判断内容是object还是array
                if type(current_zk_config) == dict:
                    # 如果是object，判断是否监控的信息，如果是监控的信息，则丢弃使用新的就好
                    # 否则，需要增加到数组中使用
                    if not current_zk_config.get("bkmonitor_config", False):
                        result_list.append(current_zk_config)

                # 如果是array
                elif type(current_zk_config) == list:
                    for pre_config in current_zk_config:
                        # 保留除监控以外的其他信息
                        if not pre_config.get("bkmonitor_config", False):
                            result_list.append(pre_config)

                # 需要判断新构建的内容和已有的内容是否一致
                old_hash = hash_util.object_md5(old_zk_config)
                new_hash = hash_util.object_md5(result_list)

                if old_hash != new_hash:
                    logger.debug(
                        f"data_id->[{self.bk_data_id}] zk config->[{new_hash}] is different from zk->[{old_hash}],"
                        f" will refresh it."
                    )

                    # 将新的数组写入到zk中
                    zk_client.set(self.zk_config_path, json.dumps(result_list).encode("utf-8"))
                    logger.info("data_id->[%s] success to push info to zk" % self.bk_data_id)

            finally:
                zk_client.stop()

        return True

    def delete_consul_config(self, consul_config_path=""):
        consul_config_path = consul_config_path or self.consul_config_path
        # 获取consul的句柄
        hash_consul = consul_tools.HashConsul()
        # 删除旧dataid的配置
        hash_consul.delete(consul_config_path)
        logger.info("dataid->[%d] has delete config from->[%s]" % (self.bk_data_id, consul_config_path))

    def redirect_consul_config(self, new_transfer_cluster_id):
        """
        重定向consul上对应节点的配置
        :return: True | raise Exception
        """
        # 暂存旧的prefix
        old_transfer_cluster_id = self.transfer_cluster_id
        if old_transfer_cluster_id == new_transfer_cluster_id:
            logger.info(
                "dataid->[%d] get new transfer cluster id which is same as old->[%s] nothing to do",
                self.bk_data_id,
                old_transfer_cluster_id,
            )
            return

        # 删除旧consul数据
        self.delete_consul_config()

        # 更新为新路径
        self.transfer_cluster_id = new_transfer_cluster_id

        # 将数据库修改存储起来
        self.save()

        # 刷新consul数据
        self.refresh_consul_config()

        logger.info(
            "data_id->[%s] redirect config from ->[%s] to ->[%s] success",
            self.bk_data_id,
            old_transfer_cluster_id,
            new_transfer_cluster_id,
        )

    def refresh_consul_config(self):
        """
        更新consul配置，告知ETL等其他依赖模块配置有所更新
        :return: True | raise Exception
        """
        # 1. 获取consul的句柄
        hash_consul = consul_tools.HashConsul()

        # 2. 刷新当前data_id的配置
        hash_consul.put(key=self.consul_config_path, value=self.to_json(is_consul_config=True))
        logger.info(
            "data_id->[{}] has update config to ->[{}] success".format(self.bk_data_id, self.consul_config_path)
        )

    def create_mq(self):
        """
        初始化准备消息队列环境，预期中获取消息队列的配置，创建之
        :return: True | raise Exception
        """
        kafka_hosts = "{}:{}".format(self.mq_cluster.domain_name, self.mq_cluster.port)
        client = kafka.SimpleClient(hosts=kafka_hosts)
        # 只是确保TOPIC存在，如果不存在则会创建之
        client.ensure_topic_exists("%s" % self.mq_config.topic)
        logger.info("data_id->[{}] now must has topic->[{}]".format(self.bk_data_id, self.mq_config.topic))

    def get_consul_fields(self):
        """
        获取返回consul上的配置信息
        :return: [{
            # 指标字段名称
            "metric":  {
                # 字段类型可有以下选项：
                # int: 整形
                # float: 浮点型
                # string: 字符串
                # timestamp: 时间戳
                "type":"float",
                # 是否由用户配置字段，可能存在字段已自动发现，但未由用户确认
                "is_config_by_user":true,
                # 字段名
                "field_name":"usage",
                "updated_time": "2018-09-09 10:10:10"
            },
            # 组成该条记录的维度字段列表
            "dimension": [{
                # 字段类型可有以下选项：
                # int: 整形
                # float: 浮点型
                # string: 字符串
                # timestamp: 时间戳
                "type":"string",
                # 是否由用户配置字段，可能存在字段已自动发现，但未由用户确认
                "is_config_by_user":true,
                # 字段名
                "field_name":"hostname",
                "updated_time": "2018-09-09 10:10:10"
            }],
            "result_table":  "table_name"
        }]
        """
        consul_client = consul.BKConsul()
        consul_result = consul_client.kv.get(self.consul_fields_path)

        # 如果找不到配置的，不做处理
        if consul_result is None:
            return []

        try:
            result = json.load(consul_result)

        except TypeError:
            return []

        return result

    def update_field_config(self):
        """
        更新结果表的字段配置信息
        :return: True | raise Exception
        """
        # 确认必须是可以更新字段的datasource
        if not self.is_field_discoverable:
            logger.info("data_id->[%s] is not self discoverable, nothing will update ." % self.bk_data_id)
            return True

        consul_fields = self.get_consul_fields()

        for table_config in consul_fields:
            table_id = table_config["result_table"]
            metric_name = table_config["metric"]["field_name"]
            dimension_list = [dimension_field["field_name"] for dimension_field in table_config["dimension"]]

            # 判断是否已经存在字段配置
            if ResultTableRecordFormat.objects.filter(
                table_id=table_id, metric=metric_name, dimension_list=json.dumps(dimension_list)
            ).exists():
                logger.info(
                    "record format for table->[%s] metric->[%s] dimension->[%s] is exists, nothing will do."
                    % (table_id, metric_name, dimension_list)
                )
                continue

            # 如果不存在，需要先创建所有的字段，然后创建record_format
            for dimension_field in table_config["dimension"]:
                if not ResultTableField.objects.filter(
                    table_id=table_id, field_name=dimension_field["field_name"]
                ).exists():
                    ResultTableField.create_field(
                        table_id=table_id,
                        field_name=dimension_field["field_name"],
                        field_type=dimension_field["type"],
                        is_config_by_user=False,
                        operator="system",
                        tag="dimension",
                    )

            if not ResultTableField.objects.filter(
                table_id=table_id, field_name=table_config["metric"]["field_name"]
            ).exists():
                ResultTableField.create_field(
                    table_id=table_id,
                    field_name=table_config["metric"]["field_name"],
                    field_type=table_config["metric"]["type"],
                    is_config_by_user=False,
                    operator="system",
                    tag="metric",
                )

            # 创建record_format记录
            ResultTableRecordFormat.create_record_format(
                table_id=table_id, metric=metric_name, dimension_list=dimension_list
            )
            logger.info("new record for table->[%s] now is create.")

            return True

    def refresh_outer_config(self):
        """
        刷新外部的依赖配置:
        1. GSE 需要写入的MQ创建及准备
        2. GSE的zk配置
        3. Consul的配置
        :return: True | raise Exception
        """
        if not self.is_enable:
            logger.info("data->[%s] is not enable, nothing will refresh to outer systems.", self.bk_data_id)
            return True

        # 1. 创建MQ，里面会判断是否存在该MQ
        self.create_mq()
        logger.debug("data_id->[%s] refresh create mq success." % self.bk_data_id)

        # 刷新GSE的zk配置
        self.refresh_gse_config()
        logger.debug("data_id->[%s] refresh gse config to zk success" % self.bk_data_id)

        # 刷新consul配置
        self.refresh_consul_config()
        logger.debug("data_id->[%s] refresh consul config success." % self.bk_data_id)

        logger.debug("refresh data_id->[%s] all outer config success" % self.bk_data_id)
        return True


class DataSourceOption(OptionBase):
    """数据源配置选项内容"""

    QUERY_NAME = "bk_data_id"

    # 使用本地时间替换数据时间
    OPTION_USE_SOURCE_TIME = "use_source_time"
    # 禁用指标切分
    OPTION_DISABLE_METRIC_CUTTER = "disable_metric_cutter"
    # 允许指标字段缺失
    OPTION_ALLOW_METRICS_MISSING = "allow_metrics_missing"
    # 允许维度字段缺失
    OPTION_ALLOW_DIMENSIONS_MISSING = "allow_dimensions_missing"
    # 记录时间精度
    OPTION_TIME_PRECISION = "time_precision"
    # 增加入库时间指标
    OPTION_INJECT_LOCAL_TIME = "inject_local_time"
    # 入库字段映射改名
    OPTION_ALLOW_USE_ALIAS_NAME = "allow_use_alias_name"
    # GROUP_INFO别名配置
    OPTION_GROUP_INFO_ALIAS = "group_info_alias"
    # 时间单位的配置选项
    OPTION_TIMESTAMP_UNIT = "timestamp_precision"

    # 增加option标记内容
    bk_data_id = models.IntegerField(_("数据源ID"), db_index=True)
    name = models.CharField(
        _("option名称"),
        choices=(
            (OPTION_ALLOW_DIMENSIONS_MISSING, OPTION_ALLOW_DIMENSIONS_MISSING),
            (OPTION_ALLOW_METRICS_MISSING, OPTION_ALLOW_METRICS_MISSING),
            (OPTION_DISABLE_METRIC_CUTTER, OPTION_DISABLE_METRIC_CUTTER),
            (OPTION_INJECT_LOCAL_TIME, OPTION_INJECT_LOCAL_TIME),
            (OPTION_TIME_PRECISION, OPTION_TIME_PRECISION),
            (OPTION_USE_SOURCE_TIME, OPTION_USE_SOURCE_TIME),
            (OPTION_ALLOW_USE_ALIAS_NAME, OPTION_ALLOW_USE_ALIAS_NAME),
            (OPTION_GROUP_INFO_ALIAS, OPTION_GROUP_INFO_ALIAS),
        ),
        max_length=128,
    )

    @classmethod
    def create_option(cls, bk_data_id, name, value, creator):
        """
        创建结果表字段选项
        :param bk_data_id: 结果表ID
        :param name: 选项名
        :param value: 值
        :param creator: 创建者
        :return:
        """
        if cls.objects.filter(bk_data_id=bk_data_id, name=name).exists():
            logger.error(
                "bk_data_id->[{}] already has option->[{}], maybe something go wrong?".format(bk_data_id, name)
            )
            raise ValueError(_("数据源已存在[{}]选项").format(name))

        # 通过父类统一创建基本信息
        record = cls._create_option(value, creator)

        # 补充子类的特殊信息
        record.bk_data_id = bk_data_id
        record.name = name

        # 写入到数据库
        record.save()

        return record

    @classmethod
    def create_or_update(cls, bk_data_id, name, value, creator):
        """
        创建或者更新结果表字段选项
        :param bk_data_id:  数据源ID
        :param name:   可选字段名称
        :param value:  可选字段值
        :param creator: 创建人和更新人
        :return:
        """
        try:
            record = cls.objects.get(bk_data_id=bk_data_id, name=name)
            val, val_type = cls._parse_value(value)
            record.value = val
            record.value_type = val_type
            record.creator = creator
            record.create_time = datetime.datetime.now()
            record.save()
            return record
        except cls.DoesNotExist:
            # 通过父类统一创建基本信息
            record = cls._create_option(value, creator)

            # 补充子类的特殊信息
            record.bk_data_id = bk_data_id
            record.name = name

            # 写入到数据库
            record.save()
        return record


class DataSourceResultTable(models.Model):
    """数据源与结果表的关系"""

    bk_data_id = models.IntegerField(_("数据源ID"))
    table_id = models.CharField(_("结果表名"), max_length=128)
    creator = models.CharField(_("创建者"), max_length=32)
    create_time = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        unique_together = ("bk_data_id", "table_id")
        verbose_name = _("数据源-结果表关系配置")
        verbose_name_plural = _("数据源-结果表关系配置表")
