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
from multiprocessing import dummy as m_dummy

__implements__ = ["DummyProcess"]

# monkey patch
# http://stackoverflow.com/questions/32877365/scikit-random-forest-regressor-attributeerror-thread-object-has-no-attrib


class DummyProcess(m_dummy.DummyProcess):
    def start(self):
        assert self._parent is m_dummy.current_process()  # modified to avoid further imports
        self._start_called = True
        if hasattr(self._parent, "_children"):
            self._parent._children[self] = None
            m_dummy.threading.Thread.start(self)  # modified to avoid further imports
