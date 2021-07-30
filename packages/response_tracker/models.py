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
"""
response_tracker.models
=======================
"""
from django.db import models


class RecordManager(models.Manager):
    def get_queryset(self):
        return super(RecordManager, self).get_queryset().defer("request_message", "response_message")


class Record(models.Model):

    # request info
    method = models.CharField(
        max_length=8,
    )
    path = models.URLField(max_length=255)
    request_message = models.TextField(
        null=True,
        blank=True,
    )

    # response info
    status_code = models.PositiveSmallIntegerField()
    content_type = models.CharField(
        max_length=32,
    )
    content_length = models.PositiveIntegerField()
    response_message = models.TextField(
        null=True,
        blank=True,
    )

    # important datetimes
    date_created = models.DateTimeField()
    duration = models.BigIntegerField(blank=True, null=True)

    def __unicode__(self):
        return str("[#{}] {} {}".format(self.pk, self.method, self.path))
