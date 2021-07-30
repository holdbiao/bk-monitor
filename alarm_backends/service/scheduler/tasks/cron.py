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


import functools
import logging
import time

from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger("cron")


def task_duration(task_name, logger_instance=None):
    def wrapper(_func):
        @functools.wraps(_func)
        def _inner(*args, **kwargs):
            start = time.time()
            logger.info("^[Cron Task](%s)" % task_name)
            try:
                return _func(*args, **kwargs)
            except Exception as e:
                logger.exception("![Cron Task]({}) error: {}".format(task_name, e))
            finally:
                if logger:
                    logger.info("$[Cron Task]({}) cost: {}".format(task_name, time.time() - start))

        return _inner

    return wrapper


def _get_func(module_path):
    def _inner_func(*args, **kwargs):
        try:
            process_func = import_string(module_path)
            process_func = getattr(process_func, "main", process_func)
        except ImportError:
            process_func = import_string("%s.main" % module_path)

        return task_duration(module_path, logger)(process_func)(*args, **kwargs)

    return _inner_func


for module_name, cron_expr in settings.DEFAULT_CRONTAB:
    func_name = str(module_name.replace(".", "_"))

    cron_list = cron_expr.split()
    func = _get_func(module_name)
    func.__name__ = func_name
    locals()[func_name] = periodic_task(
        run_every=crontab(*cron_list),
        ignore_result=True,
        queue="celery_cron",
        expires=120,  # The task will not be executed after the expiration time.
    )(func)
