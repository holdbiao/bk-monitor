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


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Record",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("method", models.CharField(max_length=8)),
                ("path", models.URLField(max_length=255)),
                ("request_message", models.TextField(null=True, blank=True)),
                ("exception", models.BooleanField(default=False)),
                ("status_code", models.PositiveSmallIntegerField(null=True)),
                ("response_message", models.TextField(null=True, blank=True)),
                ("date_created", models.DateTimeField()),
                ("duration", models.DurationField(null=True, blank=True)),
            ],
        ),
    ]
