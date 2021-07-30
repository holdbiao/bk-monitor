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

from celery.schedules import crontab
from celery.task import periodic_task

from alarm_backends.core.api_cache.library import API_CRONTAB
from alarm_backends.service.scheduler.tasks.cron import task_duration

logger = logging.getLogger("cron")


for func, cron_expr in API_CRONTAB:
    cron_list = cron_expr.split()
    new_func = task_duration(func.__name__, logger)(func)
    locals()[new_func.__name__] = periodic_task(
        run_every=crontab(*cron_list),
        ignore_result=True,
        queue="celery_api_cron",
        expires=120,  # The task will not be executed after the expiration time.
    )(new_func)
