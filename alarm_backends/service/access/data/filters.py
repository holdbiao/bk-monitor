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

import arrow
from django.conf import settings
from django.db.models.sql import AND, OR

from alarm_backends import constants
from alarm_backends.core.cache.cmdb import HostManager
from alarm_backends.service.access import base
from bkmonitor.utils.range import load_condition_instance
from constants.strategy import AdvanceConditionMethod, AGG_METHOD_REAL_TIME

logger = logging.getLogger("access.data")


class ExpireFilter(base.Filter):
    """
    过期数据过滤器
    """

    def filter(self, record):
        utctime = record.time
        # 丢弃超过max(半个小时 或者 10个周期延迟)的告警
        expire_seconds = max([record.items[0].rt_query_config["agg_interval"] * 10, 30 * constants.CONST_MINUTES])
        if arrow.utcnow().timestamp - arrow.get(utctime).timestamp > expire_seconds:
            logger.info("Discard the data(%s) because it takes more than 30 minutes" % record.raw_data)
            return True
        else:
            return False


class RangeFilter(base.Filter):
    """
    策略目标过滤器
    """

    @classmethod
    def load_target_obj(cls, item):
        return load_condition_instance(item.target)

    @classmethod
    def load_item_extra_agg_condition(cls, item):
        try:
            data_source = item.data_source
        except:  # noqa
            return

        if getattr(data_source, "_is_system_disk", lambda: False)():
            and_cond = []
            for file_type in settings.FILE_SYSTEM_TYPE_IGNORE:
                t = {"field": settings.FILE_SYSTEM_TYPE_FIELD_NAME, "method": "neq", "value": file_type}
                and_cond.append(t)
            return load_condition_instance([and_cond])

        if getattr(data_source, "_is_system_net", lambda: False)():
            and_cond = []
            for condition in settings.ETH_FILTER_CONDITION_LIST:
                t = {
                    "field": settings.SYSTEM_NET_GROUP_FIELD_NAME,
                    "method": "neq",
                    "value": condition["sql_statement"],
                }
                and_cond.append(t)
            return load_condition_instance([and_cond])

    @classmethod
    def load_item_agg_condition_target_obj(cls, item):
        agg_condition = item.rt_query_config.get("agg_condition", [])
        if not agg_condition:
            return

        # 实时监控，需要将agg_condition转换成监控目标
        if item.rt_query_config.get("agg_method", "") != AGG_METHOD_REAL_TIME:
            for condition in agg_condition:
                if condition["method"] in AdvanceConditionMethod:
                    break
            else:
                return

        or_cond = []
        and_cond = []
        for cond in agg_condition:
            t = {"field": cond["key"], "method": cond["method"], "value": cond["value"]}
            connector = cond.get("condition")
            if connector:
                if connector.upper() == AND:
                    and_cond.append(t)
                elif connector.upper() == OR:
                    or_cond.append(and_cond)
                    and_cond = [t]
                else:
                    raise Exception("Unsupported connector(%s)" % connector)
            else:
                and_cond = [t]

        if and_cond:
            or_cond.append(and_cond)
        return load_condition_instance(or_cond)

    def filter(self, record):
        """
        1. 在范围内，则不过滤掉，返回False
        2. 不在范围内，则过滤掉，返回True

        注意：每个item的范围是不一致的，只有当所有的item都被过滤掉后，才返回True

        :param record: DataRecord / EventRecord
        """

        dimensions = record.dimensions
        items = record.items
        for item in items:
            item_id = item.id
            if not record.is_retains[item_id]:
                # 如果被前面的filter过滤了，没有被保留下来，这里就直接跳过，节省时间
                continue

            # 1. 匹配监控目标
            target_obj = self.load_target_obj(item)
            is_match = target_obj.is_match(dimensions)

            # 2. 匹配监控条件(即where条件)
            agg_condition_target_obj = self.load_item_agg_condition_target_obj(item)
            if agg_condition_target_obj:
                is_match = is_match and agg_condition_target_obj.is_match(dimensions)

            # 3. 匹配额外的内置监控条件(针对磁盘、网络做的特殊处理)
            extra_agg_condition_target_obj = self.load_item_extra_agg_condition(item)
            if extra_agg_condition_target_obj:
                is_match = is_match and extra_agg_condition_target_obj.is_match(dimensions)

            is_filtered = not is_match
            if is_filtered:
                logger.debug(
                    "Discard the alarm ({}) because it not match strategy({}) item({}) agg_condition".format(
                        record.raw_data, item.strategy.id, item_id
                    )
                )

            record.is_retains[item_id] = not is_filtered

        # 数据保留下来，因为数据可能多策略共用，不同策略有不同的过滤条件。同时都被过滤的情况下，也保留下来（给无数据告警使用）
        return False


class HostStatusFilter(base.Filter):
    """
    主机状态过滤器
    """

    def filter(self, record):
        """
        如果主机运营状态为不监控的几种类型，则直接过滤

        :param record: DataRecord / EventRecord
        """
        if "bk_target_ip" not in record.dimensions or "bk_target_cloud_id" not in record.dimensions:
            return False

        ip = record.dimensions["bk_target_ip"]
        bk_cloud_id = record.dimensions["bk_target_cloud_id"]

        host = HostManager.get(ip=ip, bk_cloud_id=bk_cloud_id, using_mem=True)
        if host is None:
            logger.debug(f"Discard the record ({record.raw_data}) " f"because host({ip}|{bk_cloud_id}) is unknown")
            return True
        is_filtered = host.ignore_monitoring
        for item in record.items:
            record.is_retains[item.id] = not is_filtered and record.is_retains[item.id]
        if is_filtered:
            logger.debug(
                f"Discard the record ({record.raw_data}) " f"because host({ip}|{bk_cloud_id}) status is {host.bk_state}"
            )
        return False
