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

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from core.drf_resource import api
from bkmonitor.utils.db import JsonField
from bkmonitor.utils.common_utils import count_md5

logger = logging.getLogger("metadata")

DEFAULT_DATA_REPORT_INTERVAL = 60  # 数据上报周期，单位: 秒
DEFAULT_EXEC_TOTAL_NUM = 3  # 单个周期内执行的ping次数
DEFAULT_MAX_BATCH_SIZE = 20  # 单次最多同时ping的IP数量，默认20，尽可能的单次少一点ip，避免瞬间包量太多，导致网卡直接丢包
DEFAULT_PING_SIZE = 16  # ping的大小  默认16个字节
DEFAULT_PING_TIMEOUT = 3  # ping的rtt  默认3秒


class PingServerSubscriptionConfig(models.Model):
    """Ping Server  订阅配置"""

    bk_cloud_id = models.IntegerField(verbose_name=_("云区域ID"), primary_key=True)
    subscription_id = models.IntegerField(_("节点管理订阅ID"), default=0)

    config = JsonField(verbose_name=_("订阅配置"))

    class Meta:
        verbose_name = _("PingServer下发订阅配置")
        verbose_name_plural = _("PingServer下发订阅配置")

    @classmethod
    def create_subscription(cls, bk_cloud_id, items, target_hosts):
        logger.info(
            "update or create ping server subscription task, bk_cloud_id(%s), target_hosts(%s)",
            bk_cloud_id,
            target_hosts,
        )

        plugin_name = "bkmonitorproxy"
        scope = {"object_type": "HOST", "node_type": "INSTANCE", "nodes": target_hosts}
        subscription_params = {
            "scope": scope,
            "steps": [
                {
                    "id": plugin_name,
                    "type": "PLUGIN",
                    "config": {
                        "plugin_name": plugin_name,
                        "plugin_version": "latest",
                        "config_templates": [{"name": "bkmonitorproxy_ping.conf", "version": "latest"}],
                    },
                    "params": {
                        "context": {
                            "dataid": settings.PING_SERVER_DATAID,
                            "period": DEFAULT_DATA_REPORT_INTERVAL,
                            "total_num": DEFAULT_EXEC_TOTAL_NUM,
                            "max_batch_size": DEFAULT_MAX_BATCH_SIZE,
                            "ping_size": DEFAULT_PING_SIZE,
                            "ping_timeout": DEFAULT_PING_TIMEOUT,
                            "server_ip": "{{ cmdb_instance.host.bk_host_innerip }}",
                            "server_cloud_id": bk_cloud_id,
                            "ip_to_items": items,
                        }
                    },
                }
            ],
        }

        qs = PingServerSubscriptionConfig.objects.filter(bk_cloud_id=bk_cloud_id)
        if qs.exists():
            try:
                logger.info("ping server subscription task already exists.")
                sub_config_obj = qs.first()
                subscription_params["subscription_id"] = sub_config_obj.subscription_id
                subscription_params["run_immediately"] = True

                old_subscription_params_md5 = count_md5(sub_config_obj.config)
                new_subscription_params_md5 = count_md5(subscription_params)
                if old_subscription_params_md5 != new_subscription_params_md5:
                    logger.info("ping server subscription task config has changed, update it.")
                    result = api.node_man.update_subscription(subscription_params)
                    logger.info("update ping server subscription successful, result:{}".format(result))
                    qs.update(config=subscription_params)
                return sub_config_obj.subscription_id
            except Exception as e:  # noqa
                logger.exception("update ping server subscription error:{}, params:{}".format(e, subscription_params))
        else:
            try:
                logger.info("ping server subscription task not exists, create it.")
                result = api.node_man.create_subscription(subscription_params)
                logger.info("create ping server subscription successful, result:{}".format(result))

                # 创建订阅成功后，优先存储下来，不然因为其他报错会导致订阅ID丢失
                subscription_id = result["subscription_id"]
                PingServerSubscriptionConfig.objects.create(
                    bk_cloud_id=bk_cloud_id, config=subscription_params, subscription_id=subscription_id
                )

                result = api.node_man.run_subscription(
                    subscription_id=subscription_id, actions={plugin_name: "INSTALL"}
                )
                logger.info("run ping server subscription result:{}".format(result))
                return subscription_id
            except Exception as e:  # noqa
                logger.exception("create ping server subscription error{}, params:{}".format(e, subscription_params))
