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


from django.db import connections, migrations


class AlterUniqueTogetherNX(migrations.AlterUniqueTogether):
    def exists_unique_together(self, db, model, unique_together_name):
        connection = connections[db]
        with connection.cursor() as cursor:
            cursor.execute(
                """
            SELECT *
            FROM information_schema.TABLE_CONSTRAINTS
            WHERE
                TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            AND CONSTRAINT_NAME = '{constraint_name}'
            LIMIT 1
            """.format(
                    table_name=model._meta.db_table, constraint_name=unique_together_name
                )
            )
            if cursor.fetchall():
                return True
        return False

    def _alter_unique_together(self, schema_editor, model, old_unique_together, new_unique_together):
        olds = {tuple(fields) for fields in old_unique_together}
        news = {tuple(fields) for fields in new_unique_together}

        # Deleted uniques
        for fields in olds.difference(news):
            schema_editor._delete_composed_index(model, fields, {"unique": True}, schema_editor.sql_delete_unique)

        # Created uniques
        db = schema_editor.connection.alias
        for fields in news.difference(olds):
            columns = [model._meta.get_field(field).column for field in fields]
            unique_together_name = schema_editor._create_index_name(model, columns, suffix="_uniq")
            if not self.exists_unique_together(db, model, unique_together_name):
                schema_editor.execute(schema_editor._create_unique_sql(model, columns))

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        new_model = to_state.apps.get_model(app_label, self.name)
        db = schema_editor.connection.alias

        if self.allow_migrate_model(db, new_model):
            old_model = from_state.apps.get_model(app_label, self.name)
            self._alter_unique_together(
                schema_editor,
                new_model,
                getattr(old_model._meta, self.option_name, set()),
                getattr(new_model._meta, self.option_name, set()),
            )
