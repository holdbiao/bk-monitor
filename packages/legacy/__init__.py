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
用于处理旧版本Migration的专用app
"""

import datetime
import sys

from django.db import connections


class LegacyMigration(object):
    def __init__(self, db):
        self.now_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db = db

    @staticmethod
    def query_tables(cursor):
        cursor.execute("show tables;")
        tables = {item[0] for item in cursor.fetchall()}
        return tables

    def get_or_create_migration(self, cursor, app, name):
        cursor.execute(
            """
            select * from `django_migrations` where app=%s and name=%s;
            """,
            (app, name),
        )
        row = cursor.fetchall()
        if row:
            return False
        cursor.execute(
            """
            insert into `django_migrations` (app, name, applied) values (%s, %s, %s);
            """,
            (app, name, self.now_time_str),
        )
        return True

    def update_djcelery(self):
        try:
            import djcelery
        except Exception:
            return

        # djcelery upgrade compatible
        if int(djcelery.__version__.split(".")[1]) >= 2:
            with connections[self.db].cursor() as cursor:
                tables = self.query_tables(cursor)
                is_first_migrate = "django_migrations" not in tables
                if is_first_migrate:
                    return

                using_djcelery = "djcelery_taskstate" in tables
                if not using_djcelery:
                    return

                # insert djcelery migration record
                self.get_or_create_migration(cursor, "djcelery", "0001_initial")

    def replace_account(self):
        with connections[self.db].cursor() as cursor:
            tables = self.query_tables(cursor)
            is_first_migrate = "django_migrations" not in tables
            if is_first_migrate:
                return

            cursor.execute(
                """
                update django_migrations set name='0001_initial' where app='account' and name='1001_initial';
                delete from django_migrations where app='account' and name='1002_migrate_user';
                delete from django_migrations where app='account' and name='1003_update_user';
                """
            )

            self.get_or_create_migration(cursor, "auth", "0007_alter_validators_add_error_messages")
            self.get_or_create_migration(cursor, "auth", "0008_alter_user_username_max_length")


if "migrate" in sys.argv:
    for db in ["default", "monitor_api"]:
        runner = LegacyMigration(db)
        runner.update_djcelery()
        runner.replace_account()
