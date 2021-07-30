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

from __future__ import absolute_import, print_function, unicode_literals

import logging
from collections import defaultdict
from itertools import chain
from operator import methodcaller

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from bkmonitor.utils.common_utils import count_md5
from bkmonitor.utils.db.fields import JsonField
from core.drf_resource import api

logger = logging.getLogger("metadata")

MAX_REQ_LENGTH = 500 * 1024  # 最大请求Body大小，500KB
MAX_REQ_THROUGHPUT = 4000  # 最大的请求数(单位：秒)
MAX_DATA_ID_THROUGHPUT = 1000  # 单个dataid最大的上报频率(条/min)
MAX_FUTURE_TIME_OFFSET = 3600  # 支持的最大未来时间，超过这个偏移值，则丢弃


NODE_MAN_VERSIOIN_2_0 = "2.0"
NODE_MAN_VERSIOIN_1_3 = "1.3"


class CustomReportSubscriptionConfig(models.Model):
    """自定义上报  订阅配置"""

    bk_biz_id = models.IntegerField(verbose_name=_("业务ID"), primary_key=True)
    subscription_id = models.IntegerField(_("节点管理订阅ID"), default=0)

    config = JsonField(verbose_name=_("订阅配置"))

    class Meta:
        verbose_name = _("自定义上报订阅配置")
        verbose_name_plural = _("自定义上报订阅配置")

    @classmethod
    def create_subscription(cls, bk_biz_id, items, target_hosts):
        logger.info("update or create subscription task, bk_biz_id(%s), target_hosts(%s)", bk_biz_id, target_hosts)
        plugin_name = "bkmonitorproxy"
        if settings.BK_NODEMAN_VERSION == NODE_MAN_VERSIOIN_2_0:
            scope = {"object_type": "HOST", "node_type": "INSTANCE", "nodes": target_hosts}
        else:
            scope_biz = bk_biz_id if int(bk_biz_id) else api.cmdb.get_blueking_biz()
            scope = {"bk_biz_id": scope_biz, "object_type": "HOST", "node_type": "INSTANCE", "nodes": target_hosts}
        subscription_params = {
            "scope": scope,
            "steps": [
                {
                    "id": plugin_name,
                    "type": "PLUGIN",
                    "config": {
                        "plugin_name": plugin_name,
                        "plugin_version": "latest",
                        "config_templates": [{"name": "bkmonitorproxy_report.conf", "version": "latest"}],
                    },
                    "params": {
                        "context": {
                            "listen_ip": "{{ cmdb_instance.host.bk_host_innerip }}",
                            "listen_port": settings.BK_MONITOR_PROXY_LISTEN_PORT,
                            "max_length": MAX_REQ_LENGTH,
                            "max_throughput": MAX_REQ_THROUGHPUT,
                            "items": items,
                        }
                    },
                }
            ],
        }

        qs = CustomReportSubscriptionConfig.objects.filter(bk_biz_id=bk_biz_id)
        if qs.exists():
            try:
                logger.info("subscription task already exists.")
                sub_config_obj = qs.first()
                subscription_params["subscription_id"] = sub_config_obj.subscription_id
                subscription_params["run_immediately"] = True

                old_subscription_params_md5 = count_md5(sub_config_obj.config)
                new_subscription_params_md5 = count_md5(subscription_params)
                if old_subscription_params_md5 != new_subscription_params_md5:
                    logger.info("subscription task config has changed, update it.")
                    result = api.node_man.update_subscription(subscription_params)
                    logger.info("update subscription successful, result:{}".format(result))
                    qs.update(config=subscription_params)
                return sub_config_obj.subscription_id
            except Exception as e:  # noqa
                logger.exception("update subscription error:{}, params:{}".format(e, subscription_params))
        else:
            try:
                logger.info("subscription task not exists, create it.")
                result = api.node_man.create_subscription(subscription_params)
                logger.info("create subscription successful, result:{}".format(result))

                # 创建订阅成功后，优先存储下来，不然因为其他报错会导致订阅ID丢失
                subscription_id = result["subscription_id"]
                CustomReportSubscriptionConfig.objects.create(
                    bk_biz_id=bk_biz_id, config=subscription_params, subscription_id=subscription_id
                )

                result = api.node_man.run_subscription(
                    subscription_id=subscription_id, actions={plugin_name: "INSTALL"}
                )
                logger.info("run subscription result:{}".format(result))
                return subscription_id
            except Exception as e:  # noqa
                logger.exception("create subscription error{}, params:{}".format(e, subscription_params))

    @classmethod
    def get_custom_event_config(cls, bk_biz_id=None):
        logger.info("get custom event config, bk_biz_id(%s)", bk_biz_id)
        from metadata.models.data_source import DataSource
        from metadata.models.custom_report.event import EventGroup

        qs = EventGroup.objects.filter(is_enable=True, is_delete=False)
        if bk_biz_id is not None:
            qs = qs.filter(bk_biz_id=bk_biz_id)

        # 1. 从数据库查询到bk_biz_id到自定义上报配置的数据
        event_group_table_name = EventGroup._meta.db_table
        data_source_table_name = DataSource._meta.db_table
        result = (
            qs.extra(
                select={"token": "{}.token".format(data_source_table_name)},
                tables=[data_source_table_name],
                where=["{}.bk_data_id={}.bk_data_id".format(event_group_table_name, data_source_table_name)],
            )
            .values("bk_biz_id", "bk_data_id", "token", "max_rate")
            .distinct()
        )
        if not result:
            logger.info("no custom report config in database")
            return

        biz_id_to_data_id_config = {}
        for r in result:
            max_rate = int(r.get("max_rate", MAX_DATA_ID_THROUGHPUT))
            if max_rate < 0:
                max_rate = MAX_DATA_ID_THROUGHPUT
            biz_id_to_data_id_config.setdefault(r["bk_biz_id"], []).append(
                {
                    "dataid": r["bk_data_id"],
                    "datatype": "event",
                    "version": "v2",
                    "access_token": r["token"],
                    "max_rate": max_rate,
                    "max_future_time_offset": MAX_FUTURE_TIME_OFFSET,
                }
            )

        logger.info(
            "get custom event config success, bk_biz_id(%s), len(config)=>(%s)",
            bk_biz_id,
            len(biz_id_to_data_id_config),
        )
        return biz_id_to_data_id_config

    @classmethod
    def get_custom_time_series_config(cls, bk_biz_id=None):
        logger.info("get custom time_series config, bk_biz_id(%s)", bk_biz_id)
        from metadata.models.data_source import DataSource
        from metadata.models.custom_report.time_series import TimeSeriesGroup

        qs = TimeSeriesGroup.objects.filter(is_enable=True, is_delete=False)
        if bk_biz_id is not None:
            qs = qs.filter(bk_biz_id=bk_biz_id)

        # 1. 从数据库查询到bk_biz_id到自定义上报配置的数据
        event_group_table_name = TimeSeriesGroup._meta.db_table
        data_source_table_name = DataSource._meta.db_table
        result = (
            qs.extra(
                select={"token": "{}.token".format(data_source_table_name)},
                tables=[data_source_table_name],
                where=["{}.bk_data_id={}.bk_data_id".format(event_group_table_name, data_source_table_name)],
            )
            .values("bk_biz_id", "bk_data_id", "token", "max_rate")
            .distinct()
        )
        if not result:
            logger.info("no custom report config in database")
            return

        biz_id_to_data_id_config = {}
        for r in result:
            max_rate = int(r.get("max_rate", MAX_DATA_ID_THROUGHPUT))
            if max_rate < 0:
                max_rate = MAX_DATA_ID_THROUGHPUT
            biz_id_to_data_id_config.setdefault(r["bk_biz_id"], []).append(
                {
                    "dataid": r["bk_data_id"],
                    "datatype": "time_series",
                    "version": "v2",
                    "access_token": r["token"],
                    "max_rate": max_rate,
                    "max_future_time_offset": MAX_FUTURE_TIME_OFFSET,
                }
            )
        logger.info(
            "get custom time_series config success, bk_biz_id(%s), len(config)=>(%s)",
            bk_biz_id,
            len(biz_id_to_data_id_config),
        )
        return biz_id_to_data_id_config

    @classmethod
    def refresh_collector_custom_report_config(cls, bk_biz_id=None):
        """
        指定业务ID更新，或者更新全量业务

        Steps:
            - Metadata
                0. 从EventGroup, TimeSeriesGroup表查询到bk_biz_id到bk_data_id的对应关系
                1. 从DataSource上查询到bk_data_id到的token
                3. 根据上面的查询结果生成bk_biz_id的相关自定义上报dataid的对应关系配置列表

            - Nodeman
                0. 从api.node_man.get_proxies_by_biz接口获取到业务下所有使用到的proxyip
                1. 根据上面的查询结果生成业务ID到目标Proxy的对应关系

            按业务ID将上面的任务下发到机器上，通过节点管理的订阅接口
        """
        logger.info("refresh custom report config to proxy on bk_biz_id(%s)", bk_biz_id)

        all_biz_ids = [b.bk_biz_id for b in api.cmdb.get_business()]
        custom_event_config = cls.get_custom_event_config()
        custom_time_series_config = cls.get_custom_time_series_config()

        biz_id_to_data_id_config = defaultdict(list)

        dict_items_list = []
        if custom_event_config is not None:
            dict_items_list.append(custom_event_config)

        if custom_time_series_config is not None:
            dict_items_list.append(custom_time_series_config)

        dict_items = map(methodcaller("items"), dict_items_list)
        for k, v in chain.from_iterable(dict_items):
            biz_id_to_data_id_config[k].extend(v)

        is_all_biz_refresh = bk_biz_id is None

        # TODO optimization me
        # TODO 目前节点管理的接口，只能根据业务ID查询主机，这里每个业务需要查询一次
        for biz_id, items in biz_id_to_data_id_config.items():
            if biz_id not in all_biz_ids:
                # 如果cmdb不存在这个业务，那么需要跳过这个业务的下发
                logger.info("biz_id({}) does not exists in cmdb".format(biz_id))
                continue

            if not is_all_biz_refresh and bk_biz_id != biz_id:
                # 如果仅仅是只刷新一个业务，则跳过其他业务
                continue

            # 2. 从节点管理查询到biz_id下的Proxy机器
            try:
                if settings.BK_NODEMAN_VERSION == NODE_MAN_VERSIOIN_2_0:
                    proxy_hosts = api.node_man.get_proxies_by_biz(bk_biz_id=biz_id)
                else:
                    proxy_hosts = api.node_man.query_hosts(node_type="PROXY", bk_biz_id=biz_id)
            except Exception as e:
                logger.exception("Get ProxyIP from node_man error:{}".format(e))
                continue

            target_hosts = []
            for host_info in proxy_hosts:
                bk_cloud_id = host_info.get("bk_cloud_id", 0)
                if settings.BK_NODEMAN_VERSION == NODE_MAN_VERSIOIN_2_0:
                    ip = host_info["inner_ip"]
                else:
                    ip = host_info["conn_ip"]
                target_hosts.append({"ip": ip, "bk_cloud_id": bk_cloud_id, "bk_supplier_id": 0})

            # 3. 通过节点管理下发配置
            if target_hosts:
                cls.create_subscription(biz_id, items, target_hosts)

        # 4. 通过节点管理下发直连区域配置
        items = list(chain(*list(biz_id_to_data_id_config.values())))
        target_hosts = [
            {"ip": proxy_ip, "bk_cloud_id": 0, "bk_supplier_id": 0}
            for proxy_ip in settings.CUSTOM_REPORT_DEFAULT_PROXY_IP
        ]
        if not target_hosts:
            logger.warning(
                "Update custom report config to default cloud area error, The default cloud area is not deployed"
            )
            return
        cls.create_subscription(0, items, target_hosts)
