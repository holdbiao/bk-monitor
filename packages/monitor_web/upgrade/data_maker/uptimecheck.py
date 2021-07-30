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


import json

from django.conf import settings
from django.db import connections, transaction
from django.utils.translation import ugettext as _

from bkmonitor.utils.local import local
from monitor_web.models.uptime_check import UptimeCheckNode, UptimeCheckTask
from monitor_web.upgrade.data_maker.base import BaseDataMaker


class UptimecheckMaker(BaseDataMaker):

    # 全局配置的KEY
    GLOBAL_CONFIG_KEY = "uptimecheck_migrate_record"

    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        tasks = UptimeCheckTask.objects.using("monitor_saas_3_1").all()

        if bk_biz_id:
            tasks = tasks.filter(bk_biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value

        results = []
        for task in tasks:
            if str(task.id) in migrate_record_value:
                # 如果已经有迁移记录了，则显示上次的迁移结果
                results.append(migrate_record_value[str(task.id)])
            else:
                results.append(
                    {
                        "status": "READY",
                        "message": _("等待迁移"),
                        "bk_biz_id": task.bk_biz_id,
                        "old_task": {"id": task.id, "name": task.name},
                        "new_task": {},
                    }
                )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        new_aes_x_key = getattr(settings, settings.AES_X_KEY_FIELD)
        try:
            # 从3.1的数据库中提取出APP_TOKEN，用于字段解密
            with connections["monitor_api_3_1"].cursor() as cursor:
                cursor.execute('select `value` from global_config where `key` = "SAAS_SECRET_KEY";')
                row = cursor.fetchall()
                old_aes_x_key = row[0][0].strip('"')
        except Exception:
            old_aes_x_key = new_aes_x_key

        # # 清除老记录
        # if bk_biz_id:
        #     for task in UptimeCheckTask.origin_objects.filter(bk_biz_id=bk_biz_id):
        #         task.groups.all().delete()
        #     UptimeCheckTask.origin_objects.filter(bk_biz_id=bk_biz_id).delete()
        #     UptimeCheckNode.origin_objects.filter(bk_biz_id=bk_biz_id).delete()
        # else:
        #     UptimeCheckTask.origin_objects.all().delete()
        #     UptimeCheckNode.origin_objects.all().delete()
        #     UptimeCheckGroup.origin_objects.all().delete()

        tasks = UptimeCheckTask.objects.using("monitor_saas_3_1").all()

        if bk_biz_id:
            tasks = tasks.filter(bk_biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value
        results = []
        for task in tasks:

            if migrate_record_value.get(str(task.id), {}).get("status") == "SUCCESS":
                # 如果成功就不再迁移了，直接返回结果
                results.append(migrate_record_value[str(task.id)])
                continue

            result = {
                "status": "READY",
                "message": _("等待迁移"),
                "bk_biz_id": task.bk_biz_id,
                "old_task": {"id": task.id, "name": task.name},
                "new_task": {},
            }
            try:
                with transaction.atomic():
                    # 数据格式化
                    if not isinstance(task.location, dict):
                        task.location = json.loads(task.location)
                    config = task.config
                    task.save(using="default")

                    # 老版本有个BUG，config的加密串两侧还有个引号，需要把它去掉
                    with connections["default"].cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE monitor_uptimechecktask SET config = %s WHERE id = %s;
                        """,
                            [config, task.id],
                        )

                    # 这里先用老的加密秘钥取出来，然后再用新的加密秘钥存回去
                    try:
                        local.AES_X_KEY = old_aes_x_key
                        task = UptimeCheckTask.objects.get(id=task.id)
                        config = task.config
                        local.AES_X_KEY = new_aes_x_key
                        task.config = config
                    finally:
                        local.AES_X_KEY = new_aes_x_key

                    if task.protocol == "HTTP":
                        # HTTP 协议的字段结构转换
                        try:
                            headers = json.loads(task.config["headers"])
                            task.config["headers"] = headers
                        except Exception:
                            pass

                    task.save()

                    for node in task.nodes.using("monitor_saas_3_1").all():
                        if not isinstance(node.location, dict):
                            node.location = json.loads(node.location)

                        if UptimeCheckNode.objects.filter(id=node.id).exists():
                            # 将对象切换到新版数据库
                            node._state.db = "default"
                        else:
                            node.save(using="default")
                        task.nodes.add(node)

                    for group in task.groups.using("monitor_saas_3_1").defer("logo").all():
                        group.logo = ""
                        group.save(using="default", not_update_user=True)
                        task.groups.add(group)

                result.update(
                    {"status": "SUCCESS", "message": _("迁移成功"), "new_task": {"id": task.id, "name": task.name}}
                )
            except Exception as e:
                result.update({"status": "FAILED", "message": _("迁移失败，原因：{}").format(e)})
            finally:
                migrate_record_value.update({str(result["old_task"]["id"]): result})
                results.append(result)

        migrate_record.value = migrate_record_value
        migrate_record.save()

        return results
