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
from django.db.models import F


def forwards_func(apps, schema_editor):
    Record = apps.get_model("response_tracker", "Record")
    db_alias = schema_editor.connection.alias
    Record.objects.using(db_alias).update(
        duration=F("duration") / 1000,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("response_tracker", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="record",
            name="duration",
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.RunPython(forwards_func),
    ]
