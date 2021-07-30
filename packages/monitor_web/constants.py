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


from django.utils.translation import ugettext as _


def enum(**enums):
    return type(str("Enum"), (), enums)


# Agent状态
AGENT_STATUS = enum(UNKNOWN=-1, ON=0, OFF=1, NOT_EXIST=2, NO_DATA=3)

UPTIME_CHECK_DB = "uptimecheck"


class AlgorithmType(object):
    Threshold = "Threshold"
    SimpleRingRatio = "SimpleRingRatio"
    AdvancedRingRatio = "AdvancedRingRatio"
    SimpleYearRound = "SimpleYearRound"
    AdvancedYearRound = "AdvancedYearRound"
    PartialNodes = "PartialNodes"


class EventLevel(object):
    EVENT_LEVEL = (
        (1, _("致命")),
        (2, _("预警")),
        (3, _("提醒")),
    )
    EVENT_LEVEL_MAP = dict(list(EVENT_LEVEL))


EVENT_TYPE = enum(SYSTEM="system", CUSTOM_EVENT="custom_event", KEYWORDS="keywords")

ETL_CONFIG = enum(
    CUSTOM_EVENT="bk_standard_v2_event",
    CUSTOM_TS="bk_standard_v2_time_series",
)

EVENT_FIELD_CHINESE = dict(
    id=_("ID"),
    bk_biz_id=_("业务ID"),
    anomaly_count=_("告警次数"),
    duration=_("持续时间"),
    begin_time=_("发生时间"),
    strategy_name=_("触发策略"),
    event_message=_("通知内容"),
    alert_status=_("最近通知状态"),
    event_status=_("告警状态"),
    level=_("告警等级"),
    is_ack=_("是否确认"),
    ack_user=_("确认用户"),
    ack_message=_("确认信息"),
    target_key=_("目标"),
    is_shielded=_("是否屏蔽"),
    shield_type=_("屏蔽类型"),
)
