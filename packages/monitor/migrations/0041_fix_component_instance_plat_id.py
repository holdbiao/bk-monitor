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

from common.context_processors import Platform


def repair_by_model(apps, model_name):
    ModelToRepair = apps.get_model("monitor", model_name)
    for instance in ModelToRepair.objects.all():
        if not instance.ip_list:
            continue
        for host in instance.ip_list:
            host["plat_id"] = 0
        instance.save()


def run_repair(apps, schema_editor):
    if not Platform.te:
        return

    ComponentInstance = apps.get_model("monitor", "ComponentInstance")
    for instance in ComponentInstance.objects.all():
        instance.plat_id = 0
        instance.save()

    repair_by_model(apps, "ExporterComponent")
    repair_by_model(apps, "ExporterDepositTask")
    repair_by_model(apps, "ShellCollectorConfig")
    repair_by_model(apps, "ShellCollectorDepositTask")


class Migration(migrations.Migration):

    dependencies = [
        ("monitor", "0040_auto_20180620_1506"),
    ]

    operations = [migrations.RunPython(run_repair)]
