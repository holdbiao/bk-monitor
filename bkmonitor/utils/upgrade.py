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


from django.conf import settings
from django.db.migrations.recorder import MigrationRecorder


def allow_upgrade():
    """
    判断当前是否符合升级条件，3.1.x 以下才允许升级
    """
    if not settings.UPGRADE_ALLOWED:
        return False
    try:
        # 旧版本是否小于3.2
        is_less_than_3_2 = (
            not MigrationRecorder.Migration.objects.using("monitor_saas_3_1").filter(app="monitor_web").exists()
        )

        return is_less_than_3_2

    except Exception:
        # 遇到数据库查询之类的异常，必定不能迁移
        return False


def is_new_biz(bk_biz_id):
    """
    判断是否为3.2版本后使用的业务，根据老版本是否有策略来判断
    """
    try:
        from monitor_api.models import MonitorSource

        # 老版本的DB中策略不存在，则被认为是新接入业务
        return not MonitorSource.objects.using("monitor_api_3_1").filter(biz_id=bk_biz_id).exists()
    except Exception:
        # 数据库查询异常，则可能是数据库不存在，这时候任何业务都被看做新业务
        return True
