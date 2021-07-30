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

import arrow
from django.conf import settings

from bkmonitor.models import AnomalyRecord

logger = logging.getLogger("trigger")


def clean_anomaly_records():
    try:
        save_days = int(settings.ANOMALY_RECORD_SAVE_DAYS)
    except Exception:
        save_days = 30

    delete_time = arrow.now().replace(days=-save_days).datetime
    record_ids = list(AnomalyRecord.objects.filter(create_time__lte=delete_time).values_list("id", flat=True)[:5000])
    AnomalyRecord.objects.filter(id__in=record_ids).delete()

    if record_ids:
        logger.info(
            "[clean anomaly record] clean anomaly record created {} days age, count: {}".format(
                save_days, len(record_ids)
            )
        )
