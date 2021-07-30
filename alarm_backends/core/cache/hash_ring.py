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


import json
import logging

from django.conf import settings

from alarm_backends.constants import CONST_MINUTES
from alarm_backends.core.cache.base import CacheManager
from alarm_backends.management.utils import get_host_addr

logger = logging.getLogger("monitor")


class HashRingResult(CacheManager):
    CACHE_KEY_TEMPLATE = CacheManager.CACHE_KEY_PREFIX + ".hash.ring.result.{}"

    CACHE_TIMEOUT = CONST_MINUTES * 10

    @classmethod
    def _get_biz_targets(cls):
        from alarm_backends.management.commands.hash_ring import HashRing
        from alarm_backends.management.commands.run_access import Command

        hr = HashRing(Command.__COMMAND_NAME__)
        no_use, host_targets = hr.dispatch_all_hosts(hr.query_for_hosts())
        return host_targets

    @classmethod
    def get_biz_targets(cls, ip=None):
        from alarm_backends import constants
        from bkmonitor import models

        if settings.ENVIRONMENT == constants.CONST_DEV:
            qs = models.StrategyModel.objects.filter(is_enabled=True).values_list("bk_biz_id", flat=True).distinct()
            data = list(qs)
            data.extend(settings.BKMONITOR_WORKER_INCLUDE_LIST)
            data = list(set(data))
            data.sort()

            return data

        ip = ip or get_host_addr()
        targets = cls.cache.get(cls.CACHE_KEY_TEMPLATE.format(ip))
        if targets:
            return json.loads(targets)
        else:
            logger.warning("Missed HashRing Result : %s", ip)
            host_targets = cls._get_biz_targets() or {}
            return host_targets.get(ip)

    @classmethod
    def refresh(cls):
        try:
            host_targets = cls._get_biz_targets()
            if host_targets:
                for k, v in list(host_targets.items()):
                    cls.cache.set(cls.CACHE_KEY_TEMPLATE.format(k), json.dumps(v), cls.CACHE_TIMEOUT)
        except Exception as e:
            logger.exception("update hash ring failed: %s" % e)


def main():
    HashRingResult.refresh()
