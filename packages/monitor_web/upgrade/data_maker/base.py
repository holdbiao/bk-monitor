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


from monitor.models import GlobalConfig


class BaseDataMaker(object):
    # 全局配置的KEY
    GLOBAL_CONFIG_KEY = "custom_monitor_migrate_record"

    @classmethod
    def get_migrate_record(cls):
        migrate_record, is_create = GlobalConfig.objects.get_or_create(
            key=cls.GLOBAL_CONFIG_KEY, defaults={"value": {}}
        )
        return migrate_record

    @classmethod
    def make_migrations(cls, bk_biz_id=0):
        raise NotImplementedError

    @classmethod
    def migrate(cls, bk_biz_id=0):
        raise NotImplementedError
