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
# TODO redis sentinel


import json
import logging
import socket
import traceback

import arrow
from django.conf import settings
from django.utils.functional import cached_property

from bkmonitor.utils.common_utils import get_local_ip

LOCAL_IP = get_local_ip()
LOCAL_HOSTNAME = socket.gethostname()


class RedisHandler(logging.Handler):
    RedisKeyTTL = getattr(settings, "REDIS_MAXLOG_TTL", 15 * 60)
    RedisKey = "logs"
    redis_client = None

    @classmethod
    def set_redis_client(cls, client):
        cls.redis_client = client

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)

    def emit(self, record):
        try:
            self._emit(record)
        except:  # noqa
            print("WRITE LOG FAILURE")

    def _emit(self, record):
        redis_client = self.redis_client
        if redis_client is None:
            print("WRITE LOG TO REDIS ERROR: REDIS GONE")
            return
        if redis_client.llen(self.RedisKey) >= settings.REDIS_MAXLOG:
            print("WRITE LOG TO REDIS ERROR: REDIS FULL")
            return
        if record.exc_info:
            exc_lines = "".join(traceback.format_exception(*record.exc_info))
        else:
            exc_lines = ""

        record_dict = {
            "host_ip": LOCAL_IP,
            "host_name": LOCAL_HOSTNAME,
            "log_time": arrow.utcnow().isoformat(),
            "exc_info": exc_lines,
            "filename": record.filename,
            "funcname": record.funcName,
            "level": record.levelname,
            "levelno": record.levelno,
            "log_type": "status",
            "lineno": record.lineno,
            "module": record.module,
            "msecs": record.msecs,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "process_id": record.process,
            "processname": record.processName,
            "relativecreated": record.relativeCreated,
            "thread": record.thread,
            "threadname": record.threadName,
        }

        if hasattr(record, "log_type"):
            record_dict["log_type"] = record.log_type
        if hasattr(record, "app_code"):
            record_dict["app_code"] = record.app_code
        if hasattr(record, "remote_ip"):
            record_dict["remote_ip"] = record.remote_ip
        if hasattr(record, "comp_code"):
            record_dict["comp_code"] = record.comp_code
        if hasattr(record, "call_type"):
            record_dict["call_type"] = record.call_type
        if hasattr(record, "call_url"):
            record_dict["call_url"] = record.call_url
        if hasattr(record, "call_args"):
            record_dict["call_args"] = record.call_args
        if hasattr(record, "result"):
            record_dict["result"] = record.result
        if hasattr(record, "result_code"):
            record_dict["result_code"] = record.result_code

        try:
            redis_client.lpush(self.RedisKey, json.dumps(record_dict))
            redis_client.expire(self.RedisKey, self.RedisKeyTTL)
        except Exception as e:
            print("WRITE LOG TO REDIS ERROR: %s" % str(e))


class SentryHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET, tags=()):
        logging.Handler.__init__(self, level)
        self._tags = dict(tags)

    @property
    def dsn(self):
        return settings.SENTRY_DSN

    @cached_property
    def tags(self):
        tags = {
            "host": LOCAL_IP,
            "hostname": LOCAL_HOSTNAME,
            "platform": settings.PLATFORM,
            "env": settings.ENV,
            "app_code": settings.APP_CODE,
        }
        tags.update(self._tags)
        return tags

    @cached_property
    def raven(self):
        from raven.handlers.logging import SentryHandler

        return SentryHandler(dsn=self.dsn, tags=self.tags, sample_rate=0.5)

    def emit(self, record):
        if not self.dsn:
            return
        self.raven.emit(record)
