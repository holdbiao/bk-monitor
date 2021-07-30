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

from alarm_backends.constants import CONST_MINUTES
from alarm_backends.core.storage.redis import Cache
from bkmonitor.utils.common_utils import uniqid4


class BaseLock(object):
    def __init__(self, name, ttl=None):
        self.name = name
        # 默认60秒过期
        self.ttl = ttl or CONST_MINUTES

    def acquire(self, _wait=None):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    def __exit__(self, t, v, tb):
        self.release()

    def __enter__(self):
        self.acquire()
        return self


class RedisLock(BaseLock):
    __token = None

    def __init__(self, name, ttl=None):
        super(RedisLock, self).__init__(name, ttl)
        self.client = Cache("service")

    def acquire(self, _wait=0.001):
        token = uniqid4()
        wait_until = time.time() + _wait
        while not self.client.set(self.name, token, ex=self.ttl, nx=True):
            if time.time() < wait_until:
                time.sleep(0.01)
            else:
                return False

        self.__token = token
        return True

    def release(self):
        if not self.__token:
            return False
        token = self.client.get(self.name)
        if not token or token != self.__token:
            return False
        return self.client.delete(self.name)
