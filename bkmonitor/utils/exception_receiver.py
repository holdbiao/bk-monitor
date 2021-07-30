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

import inspect

import logging

logger = logging.getLogger(__name__)


def receive_exception(*exceptions):
    def setter(func):
        func.exceptions = exceptions
        return func

    return setter


class ExceptionReceiver(object):
    receivers = None

    def __init__(self, **kwargs):
        self.result = None
        self.exception = None
        self.kwargs = kwargs

    def receive_default(self, exception, **kwargs):
        logger.exception(exception)

    def receivers(self):
        for name in dir(self):
            if name.startswith("_"):
                continue
            obj = getattr(self, name)
            if inspect.ismethod(obj) and getattr(obj, "exceptions", None):
                yield obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            return
        if exc_val is None:
            exc_val = exc_type()
        self.exception = exc_val
        for receiver in self.receivers():
            if isinstance(exc_val, receiver.exceptions):
                self.result = receiver(exc_val, **self.kwargs)
                break
        else:
            self.result = self.receive_default(exc_val, **self.kwargs)
        return True
