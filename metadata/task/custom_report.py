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


import logging
import traceback


from alarm_backends.core.lock.service_lock import share_lock
from metadata import models

logger = logging.getLogger("metadata")


@share_lock(identify="metadata_refreshEventGroup")
def check_event_update():

    for event_group in models.EventGroup.objects.filter(is_enable=True, is_delete=False).iterator():
        try:
            event_group.update_event_dimensions_from_es()
        except Exception:
            logger.error(
                "event_group->[{}] try to update from es failed for->[{}]".format(
                    event_group.event_group_name, traceback.format_exc()
                )
            )
        else:
            logger.info("event_group->[{}] is update from es success.".format(event_group.event_group_name))


@share_lock()
def refresh_custom_report_config_to_node_man(bk_biz_id=None):
    try:
        models.CustomReportSubscriptionConfig.refresh_collector_custom_report_config(bk_biz_id)
    except Exception:  # noqa
        logger.exception("refresh custom report config to colletor error")


@share_lock(identify="metadata_refreshTimeSeriesMetrics")
def check_update_time_series_metric_update():

    for time_series_group in models.TimeSeriesGroup.objects.filter(is_enable=True, is_delete=False).iterator():
        try:
            time_series_group.update_time_series_metric_from_consul()
        except Exception:
            logger.error(
                "time_series_group->[{}] try to update metrics from consul failed for->[{}]".format(
                    time_series_group.bk_data_id, traceback.format_exc()
                )
            )
        else:
            logger.info(
                "time_series_group->[{}] metric update from consul success.".format(time_series_group.bk_data_id)
            )
