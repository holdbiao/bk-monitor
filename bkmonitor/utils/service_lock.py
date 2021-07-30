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


import time

from django.conf import settings

from bkmonitor.utils import consul


def render_macro(template):
    return template.format(**{k.lower(): getattr(settings, k) for k in dir(settings)})


class BaseServiceLock(object):
    def __init__(self, name, macro=True, *args, **kwargs):
        self.name = render_macro(name) if macro else name

    def acquire(self, timeout=None):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    def __exit__(self, t, v, tb):
        self.release()

    def __enter__(self):
        self.acquire()
        return self


class ConsulServiceLock(BaseServiceLock):
    DEFAULT_LOCK_TTL = getattr(settings, "DEFAULT_CONSUL_SERVICE_LOCK_TTL", 3600)

    def __init__(self, name, ttl=0, *args, **kwargs):
        super(ConsulServiceLock, self).__init__(name, *args, **kwargs)
        self.client = consul.BKConsul()
        self.ttl = self.DEFAULT_LOCK_TTL if ttl == 0 else ttl
        self.sid = self.client.session.create(ttl=self.ttl)

    def touch(self):
        self.client.session.renew(self.sid)

    def make_value(self):
        if not self.ttl:
            return ""
        return "%d" % (time.time() + self.ttl)

    def get_value(self):
        _, info = self.client.kv.get(self.name)
        if not info:
            return None

        value = info.get("Value")
        if value is not None and value.isdigit():
            return int(value)
        return None

    def is_expired(self):
        self.touch()
        value = self.get_value()
        if value is None:
            return True
        elif value == "":
            return False

        return int(time.time()) > value

    def acquire(self, timeout=0.0):
        self.touch()
        interval = min(timeout / 10, 0.2)
        timeout = time.time() + timeout
        while not self.client.kv.put(
            self.name,
            self.make_value(),
            acquire=self.sid,
        ):
            if timeout < time.time():
                return False
            time.sleep(interval)
        return True

    def release(self):
        self.touch()
        return self.client.kv.put(self.name, "", release=self.sid)


class ConsulServiceDurationLock(ConsulServiceLock):

    value = ""

    def initialize(self):
        return self.client.kv.put(self.name, self.value, acquire=self.sid)

    def _wait(self, timeout=None):
        if not timeout:
            timeout = time.time() + 0.0001

        self.touch()
        interval = min(timeout / 10, 0.2)
        while not self.is_expired():
            if timeout < time.time():
                return False
            time.sleep(interval)
        else:
            self.initialize()
        return True

    def acquire(self, timeout=None):
        self.value = self.make_value()
        if not self._wait(timeout):
            return False
        return self.client.kv.put(self.name, self.value, release=self.sid)

    def release(self):
        if self.get_value() != self.value:
            return False
        if not self._wait():
            return False
        self.client.kv.put(self.name, "0", release=self.sid)
        return self.is_expired()


ServiceLock = ConsulServiceLock
ServiceDurationLock = ConsulServiceDurationLock
