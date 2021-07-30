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

from unittest import TestCase

import mock

from . import exception_receiver


class TestExceptionReceiver(TestCase):
    class TestER(exception_receiver.ExceptionReceiver):
        def __init__(self, **kwargs):
            super(self.__class__, self).__init__(**kwargs)
            self.key_error = mock.MagicMock()
            self.index_error = mock.MagicMock()
            self.zero_division_error = mock.MagicMock()
            self.errors = mock.MagicMock()

        @exception_receiver.receive_exception(KeyError, IndexError)
        def receive_key_or_value_error(self, exception, **kwargs):
            if isinstance(exception, IndexError):
                self.index_error()
                return self.index_error.call_count
            elif isinstance(exception, KeyError):
                self.key_error()
                return self.key_error.call_count
            else:
                raise TypeError()

        @exception_receiver.receive_exception(ZeroDivisionError)
        def receive_zero_division_error(self, exception, **kwargs):
            if isinstance(exception, ZeroDivisionError):
                self.zero_division_error()
                return self.zero_division_error.call_count
            else:
                raise TypeError()

        @exception_receiver.receive_exception(ValueError)
        def receive_and_raise(self, exception, **kwargs):
            raise exception

        def receive_default(self, exception, raise_exceptions=(), **kwargs):
            self.errors()
            if isinstance(exception, raise_exceptions):
                raise exception
            return self.errors.call_count

    def test_case1(self):
        with self.TestER() as er:
            x = 1 + 1
        self.assertEqual(x, 2)
        self.assertIsNone(er.result)
        self.assertIsNone(er.exception)

    def test_case2(self):
        with self.TestER() as er:
            x = []
            y = x[1]
        self.assertEqual(x, [])
        with self.assertRaises(NameError):
            self.assertEqual(y, None)
        self.assertEqual(er.result, 1)
        self.assertIsInstance(er.exception, IndexError)
        self.assertEqual(er.index_error.call_count, 1)
        self.assertEqual(er.key_error.call_count, 0)
        self.assertEqual(er.zero_division_error.call_count, 0)
        self.assertEqual(er.errors.call_count, 0)

    def test_case3(self):
        with self.TestER() as er:
            x = {}
            y = x[1]
        self.assertEqual(x, {})
        with self.assertRaises(NameError):
            self.assertEqual(y, None)
        self.assertEqual(er.result, 1)
        self.assertIsInstance(er.exception, KeyError)
        self.assertEqual(er.index_error.call_count, 0)
        self.assertEqual(er.key_error.call_count, 1)
        self.assertEqual(er.zero_division_error.call_count, 0)
        self.assertEqual(er.errors.call_count, 0)

    def test_case4(self):
        with self.TestER() as er:
            x = 0
            y = 1 / x
        self.assertEqual(x, 0)
        with self.assertRaises(NameError):
            self.assertEqual(y, None)
        self.assertEqual(er.result, 1)
        self.assertIsInstance(er.exception, ZeroDivisionError)
        self.assertEqual(er.index_error.call_count, 0)
        self.assertEqual(er.key_error.call_count, 0)
        self.assertEqual(er.zero_division_error.call_count, 1)
        self.assertEqual(er.errors.call_count, 0)

    def test_case5(self):
        with self.assertRaises(ValueError):
            with self.TestER() as er:
                raise ValueError()
        self.assertIsNone(er.result)
        self.assertIsInstance(er.exception, ValueError)
        self.assertEqual(er.index_error.call_count, 0)
        self.assertEqual(er.key_error.call_count, 0)
        self.assertEqual(er.zero_division_error.call_count, 0)
        self.assertEqual(er.errors.call_count, 0)

    def test_case6(self):
        with self.TestER() as er:
            raise TypeError()
        self.assertEqual(er.result, 1)
        self.assertIsInstance(er.exception, TypeError)
        self.assertEqual(er.index_error.call_count, 0)
        self.assertEqual(er.key_error.call_count, 0)
        self.assertEqual(er.zero_division_error.call_count, 0)
        self.assertEqual(er.errors.call_count, 1)

    def test_case7(self):
        with self.assertRaises(NotImplementedError):
            with self.TestER(raise_exceptions=NotImplementedError) as er:
                raise NotImplementedError()
        self.assertIsNone(er.result)
        self.assertIsInstance(er.exception, NotImplementedError)
        self.assertEqual(er.index_error.call_count, 0)
        self.assertEqual(er.key_error.call_count, 0)
        self.assertEqual(er.zero_division_error.call_count, 0)
        self.assertEqual(er.errors.call_count, 1)
