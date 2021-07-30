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

from . import default_settings


class SliceSettings(object):
    def __init__(self, _default_settings):
        self._default_settings = _default_settings

        from django.conf import settings as django_settings

        self._django_settings = django_settings

    def __getattr__(self, key):
        if key == key.upper():
            if hasattr(self._django_settings, key):
                return getattr(self._django_settings, key)
            elif hasattr(self._default_settings, key):
                return getattr(self._default_settings, key)

        raise AttributeError("{!r} object has no attribute {!r}".format(self.__class__.__name__, key))


settings = SliceSettings(default_settings)
