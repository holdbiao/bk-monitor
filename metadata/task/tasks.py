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


from alarm_backends.service.scheduler.app import app
from metadata import models
from metadata.task.custom_report import refresh_custom_report_config_to_node_man


@app.task(ignore_result=True, queue="celery_cron")
def refresh_custom_report_config(bk_biz_id=None):
    refresh_custom_report_config_to_node_man(bk_biz_id=bk_biz_id)


@app.task(ignore_result=True, queue="celery_cron")
def access_to_bk_data_task(table_id):
    try:
        bkdata_storage = models.BkDataStorage.objects.get(table_id=table_id)
    except models.BkDataStorage.DoesNotExist:
        models.BkDataStorage.create_table(table_id, is_sync_db=True)
        return

    bkdata_storage.access_to_bk_data()


@app.task(ignore_result=True, queue="celery_cron")
def create_statistics_data_flow(table_id, agg_interval):
    try:
        bkdata_storage = models.BkDataStorage.objects.get(table_id=table_id)
    except models.BkDataStorage.DoesNotExist:
        raise Exception("数据({})未接入到计算平台，请先接入后再试".format(table_id))

    bkdata_storage.create_statistics_data_flow(agg_interval)


@app.task(ignore_result=True, queue="celery_cron")
def create_full_cmdb_level_data_flow(table_id):
    try:
        bkdata_storage = models.BkDataStorage.objects.get(table_id=table_id)
    except models.BkDataStorage.DoesNotExist:
        raise Exception("数据({})未接入到计算平台，请先接入后再试".format(table_id))

    bkdata_storage.full_cmdb_node_info_to_result_table()
