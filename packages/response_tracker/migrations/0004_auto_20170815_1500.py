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


import re

from django.db import migrations, models

re_code = re.compile(r"^(?P<status_code>\d{3})\s")
re_type = re.compile(r"^Content-Type:\s*(?P<content_type>.*)$", re.M)
re_length = re.compile(r"^Content-Length:\s*(?P<content_length>\d+)$", re.M)


def forwards_func(apps, schema_editor):
    Record = apps.get_model("response_tracker", "Record")
    db_alias = schema_editor.connection.alias

    for record in Record.objects.using(db_alias).all():
        updates = {}

        match_code = re_code.match(record.response_message)
        if match_code:
            value = match_code.groupdict()["status_code"]
            updates.update(
                {
                    "status_code": int(value),
                }
            )
        else:
            continue

        try:
            index = record.response_message.index("\n\n")
        except:
            continue

        match_type = re_type.search(record.response_message)
        if match_type:
            value = match_type.groupdict()["content_type"]
            updates.update(
                {
                    "content_type": value.split(";")[0],
                }
            )

        match_length = re_length.search(record.response_message)
        if match_length:
            value = match_type.groupdict()["content_type"]
            updates.update(
                {
                    "content_length": int(value),
                }
            )
        else:
            updates.update(
                {
                    "content_length": len(record.response_message[index + 2 :]),
                }
            )

        Record.objects.using(db_alias).filter(pk=record.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("response_tracker", "0003_remove_record_exception"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="content_length",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="record",
            name="content_type",
            field=models.CharField(default="text/html", max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="record",
            name="status_code",
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_func),
    ]
