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

from django.utils.translation import ugettext as _

from .gse_event import GSEBaseAlarmEventRecord

logger = logging.getLogger("access.event")


class AgentEvent(GSEBaseAlarmEventRecord):
    """
    Agent心跳丢失事件

    raw data format:
    {
        "utctime2":"2019-10-17 07:55:49",
        "value":[
            {
                "event_raw_id":29,
                "event_type":"gse_basic_alarm_type",
                "event_time":"2019-10-17 15:55:49",
                "extra":{
                    "count":1,
                    "host":[
                        {
                            "ip":"10.0.0.1",
                            "cloudid":0,
                            "bizid":0
                        }
                    ],
                    "type":2
                },
                "event_title":"",
                "event_desc":"",
                "event_source_system":""
            }
        ],
        "server":"127.0.0.129",
        "utctime":"2019-10-17 15:55:49",
        "time":"2019-10-17 15:55:49",
        "timezone":8
    }

    """

    TYPE = 2
    NAME = "agent-gse"
    METRIC_ID = "bk_monitor.agent-gse"
    TITLE = _("AGENT心跳丢失-GSE")

    def __init__(self, raw_data, strategies):
        super(AgentEvent, self).__init__(raw_data, strategies)

    def flat(self):
        try:
            server = self.raw_data["server"]
            utctime = self.raw_data.get("utctime2")

            origin_alarms = self.raw_data["value"]
            alarms = []
            for alarm in origin_alarms:
                if not utctime:
                    alarm_time = alarm.get("event_time")
                else:
                    alarm_time = utctime

                hosts = alarm["extra"].pop("host", [])
                for host in hosts:
                    new_alarm = {
                        "_time_": alarm_time,
                        "_type_": alarm["extra"]["type"],
                        "_bizid_": host["bizid"],
                        "_cloudid_": host["cloudid"],
                        "_server_": server,
                        "_host_": host["ip"],
                        "_title_": alarm["event_title"],
                    }
                    alarms.append(self.__class__(new_alarm, self.strategies))
            return alarms
        except Exception as e:
            logger.exception("GSE agent-gse: (%s) (%s)", self.raw_data, e)
            return []

    def clean_anomaly_message(self):
        raw = self.raw_data["_title_"]
        if raw:
            return raw

        return _("GSE AGENT 失联")
