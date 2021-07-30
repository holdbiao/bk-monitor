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
from itertools import chain

import arrow

from alarm_backends.core.cache.cmdb import HostManager
from alarm_backends.service.access.event.records.base import EventRecord

logger = logging.getLogger("access.event")


class GSEBaseAlarmEventRecord(EventRecord):
    TYPE = -1
    NAME = ""
    METRIC_ID = ""
    TITLE = ""

    def __init__(self, raw_data, strategies):
        super(GSEBaseAlarmEventRecord, self).__init__(raw_data=raw_data)
        self.strategies = strategies

    def check(self):
        if len(self.raw_data["value"]) == 1:
            logger.debug("GSE alarm value: %s" % self.raw_data)
            return True
        else:
            logger.warning("GSE alarm value check fail: %s" % self.raw_data)
            return False

    def get_plat_info(self, alarm):
        """获取单机告警中的plat_id, company_id, ip等字段"""
        bk_cloud_id = alarm.get("_cloudid_") or 0
        company_id = alarm.get("_bizid_") or 0  # 这里bizid存储的是companyid，而不是真实的bizid
        ip = alarm["_host_"]
        return bk_cloud_id, company_id, ip

    def full(self):
        alarm = self.raw_data
        bk_cloud_id, company_id, ip = self.get_plat_info(alarm)
        try:
            host_obj = HostManager.get(ip, bk_cloud_id, using_mem=True)
        except Exception as e:
            logger.exception(
                "Custom Event, get host error, bk_cloud_id({}), " "ip({}), except({})".format(bk_cloud_id, ip, e)
            )
            return []

        if not host_obj:
            return []

        biz_id = int(host_obj.bk_biz_id)
        alarm["_biz_id_"] = biz_id

        try:
            dimensions = alarm.setdefault("dimensions", {})
            dimensions["bk_target_ip"] = ip
            dimensions["bk_target_cloud_id"] = bk_cloud_id
            if host_obj.topo_link:
                dimensions["bk_topo_node"] = sorted({node.id for node in chain(*list(host_obj.topo_link.values()))})
        except Exception as e:
            logger.exception("{} full error {}, {}".format(self.__class__.__name__, alarm, e))
            return []

        new_record_list = []
        strategies = self.strategies.get(int(biz_id))
        if not strategies:
            logger.warning("abandon gse event({}), because not strategy in biz({})".format(self.raw_data, biz_id))
            return []

        for strategy_id, strategy_obj in list(strategies.items()):
            if strategy_obj.config["item_list"][0]["metric_id"] != self.METRIC_ID:
                continue

            new_alarm = {}
            new_alarm.update(alarm)
            new_alarm["strategy"] = strategy_obj

            new_record_list.append(self.__class__(new_alarm, self.strategies))

        if not new_record_list:
            logger.warning(
                "abandon gse event({}), because not strategy about({})".format(self.raw_data, self.METRIC_ID)
            )
        return new_record_list

    ######################
    # CLEAN DATA METHODS #
    ######################

    def clean_time(self):
        return self.event_time

    def clean_record_id(self):
        return "{md5_dimension}.{timestamp}".format(md5_dimension=self.md5_dimension, timestamp=self.event_time)

    def clean_dimensions(self):
        return self.raw_data["dimensions"]

    def clean_value(self):
        return self.raw_data["_title_"]

    def clean_values(self):
        return {"time": self.event_time, "value": self.raw_data["_title_"]}

    #########################
    # CLEAN ANOMALY METHODS #
    #########################

    def clean_anomaly_id(self):
        """
        {md5_dimension}.{timestamp}.{strategy_id}.{item_id}.{level}"
        """
        return "{md5_dimension}.{timestamp}.{strategy_id}.{item_id}.{level}".format(
            md5_dimension=self.md5_dimension,
            timestamp=self.event_time,
            strategy_id=self._strategy_id,
            item_id=self._item_id,
            level=self.level,
        )

    def clean_anomaly_message(self):
        return self.raw_data["_title_"]

    def clean_anomaly_time(self):
        return arrow.utcnow().format("YYYY-MM-DD HH:mm:ss")
