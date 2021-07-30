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

from django.db import transaction
from django.utils.translation import ugettext as _

from monitor.models import ApplicationConfig, DashboardMenu, DashboardMenuLocation, DashboardView
from monitor_web.upgrade.data_maker.base import BaseDataMaker
from monitor_web.upgrade.data_maker.commons import ResultTableType, classify_result_table


class DashboardMaker(BaseDataMaker):
    """
    仪表盘数据迁移
    """

    # 全局配置的KEY
    GLOBAL_CONFIG_KEY = "dashboard_migrate_record"

    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        menus = DashboardMenu.objects.using("monitor_saas_3_1").all()

        if bk_biz_id:
            menus = menus.filter(biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()
        migrate_record_value = migrate_record.value

        results = []
        for menu in menus:
            for location in menu.dashboardmenulocation_set.all():
                view = location.view
                if str(view.id) in migrate_record_value:
                    # 如果已经有迁移记录了，则显示上次的迁移结果
                    results.append(migrate_record_value[str(view.id)])
                else:
                    results.append(
                        {
                            "status": "READY",
                            "message": _("等待迁移"),
                            "bk_biz_id": view.biz_id,
                            "old_view": {"id": view.id, "name": view.name},
                            "new_view": {},
                        }
                    )
        return results

    @classmethod
    def migrate(cls, bk_biz_id=0):
        # 删除老数据
        if bk_biz_id:
            DashboardMenu.origin_objects.filter(biz_id=bk_biz_id).delete()
            DashboardView.origin_objects.filter(biz_id=bk_biz_id).delete()
        else:
            DashboardView.origin_objects.all().delete()
            DashboardView.origin_objects.all().delete()

        menus = DashboardMenu.objects.using("monitor_saas_3_1").all()

        if bk_biz_id:
            menus = menus.filter(biz_id=bk_biz_id)

        migrate_record = cls.get_migrate_record()

        # 新旧视图ID的映射 key: 旧ID，value: 新ID
        view_id_mapping = {}
        results = []
        for menu in menus:
            old_menu_id = menu.id
            menu.id = None
            menu.save(using="default")
            for location in DashboardMenuLocation.objects.using("monitor_saas_3_1").filter(menu=old_menu_id).all():
                view = location.view
                result = {
                    "status": "READY",
                    "message": _("等待迁移"),
                    "bk_biz_id": view.biz_id,
                    "old_view": {"id": view.id, "name": view.name},
                    "new_view": {},
                }
                try:
                    for metric_info in json.loads(view.metrics):
                        rt_type, metric_id_prefix = classify_result_table(metric_info["rt_id"])
                        if rt_type == ResultTableType.OLD_BK_MONITOR:
                            raise Exception(_("不支持迁移。该视图配置使用了不支持的数据源类型。RT({})".format(metric_info["rt_id"])))

                    with transaction.atomic():
                        view.id = None
                        view.save(using="default")
                        location.id = None
                        location.view_id = view.id
                        location.menu_id = menu.id
                        location.save(using="default")

                        # 记录新老ID映射
                        view_id_mapping[result["old_view"]["id"]] = view.id

                    result.update(
                        {"status": "SUCCESS", "message": _("迁移成功"), "new_view": {"id": view.id, "name": view.name}}
                    )
                except Exception as e:
                    result.update({"status": "FAILED", "message": _("迁移失败，原因：{}").format(e)})
                finally:
                    migrate_record.value.update({str(result["old_view"]["id"]): result})
                    results.append(result)

            # 迁移仪表盘视图位置信息
            config = (
                ApplicationConfig.objects.using("monitor_saas_3_1")
                .filter(cc_biz_id=menu.biz_id, key="dashboard_view_config:{}".format(old_menu_id))
                .first()
            )
            if config:
                location_infos = []
                try:
                    for location_info in json.loads(config.value):
                        if location_info["view_id"] not in view_id_mapping:
                            # 视图已经不存在了
                            continue
                        location_info["view_id"] = view_id_mapping[location_info["view_id"]]
                        location_infos.append(location_info)

                    ApplicationConfig.objects.update_or_create(
                        cc_biz_id=menu.biz_id,
                        key="dashboard_view_config:{}".format(menu.id),
                        defaults={"value": json.dumps(location_infos)},
                    )
                except Exception:
                    # 出错了忽略，位置信息不是必要的
                    pass

        migrate_record.save()

        return results
