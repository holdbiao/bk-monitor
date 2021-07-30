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
import logging
import re
from collections import defaultdict

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from alarm_backends.core.cache.key import ACTION_LIST_KEY
from alarm_backends.core.i18n import i18n
from alarm_backends.service.action.shield import ShieldManager
from bkmonitor.models import EventAction
from bkmonitor.utils.range.period import TimeMatch
from constants.shield import ShieldType

from .collector import DimensionCollector, BizCollector, VoiceCollector
from .utils import get_business_roles, get_host_bak_operator, get_host_operator

logger = logging.getLogger("action")


class NoticeProcessor(object):
    """
    通知处理
    """

    ShortSingleCollectTime = 1
    LongSingleCollectTime = 60
    MultiCollectTime = 60

    def __init__(self, event_action_id):
        """
        :param event_action_id: 事件操作记录ID
        """

        self.event_action = EventAction.objects.get(id=event_action_id)
        self.event = self.event_action.event
        i18n.set_biz(self.event.bk_biz_id)

        self.action = self.event_action.extend_info["action"]
        self.notice_type = self.event_action.operate.split("_")[0].lower()
        self._noticed_receivers = defaultdict(list)
        self._group_to_users = {}

        self.shield_manager = ShieldManager()

    def group_to_users(self, group):
        """
        通知组转换为通知人员列表
        :param group: str 通知组(bk_biz_productor,bk_biz_maintainer,bk_biz_developer,bk_biz_tester)
        :return: list 通知人员列表 [admin, test_user]
        """
        # 业务通知组缓存
        if group in self._group_to_users:
            return self._group_to_users[group]

        # 如果有业务角色，则查询业务角色
        if group in settings.AUTHORIZED_ROLES:
            self._group_to_users = get_business_roles(self.event.bk_biz_id)
            return self._group_to_users[group]

        # 如果拥有ip维度且有主备负责人，则查询主机主备负责人
        origin_dimension = self.event.latest_anomaly_record.anomaly_data["dimensions"]
        if group in ["operator", "bk_bak_operator"]:
            for ip_key in ["bk_target_ip", "ip"]:
                ip = origin_dimension.get(ip_key)
                if ip:
                    break
            else:
                return []

            for cloud_id_key in ["bk_target_cloud_id", "bk_cloud_id"]:
                bk_cloud_id = origin_dimension.get(cloud_id_key)
                if bk_cloud_id is not None:
                    break

            bk_cloud_id = str(bk_cloud_id) if bk_cloud_id is not None else "0"
            if group == "operator":
                users = get_host_operator(ip, bk_cloud_id)
                self._group_to_users["operator"] = users
            else:
                users = get_host_bak_operator(ip, bk_cloud_id)
                self._group_to_users["bak_operator"] = users

            return users

        return []

    @cached_property
    def notice_configs(self):
        """
        从策略配置中获取通知配置
        :rtype: list
        [
            {
                "notice_way": ["sms", "weixin"],
                "notice_receivers": ["admin"],
                "user_to_groups": {
                    "admin": "bk_biz_maintainer"
                }
            }
        ]
        """
        notice_configs = defaultdict(lambda: {"notice_receivers": [], "user_to_groups": {}})

        for notice_group in self.action["notice_group_list"]:
            # 将通知组转换为通知人员，并去重
            notice_receivers = []
            user_to_groups = {}
            for origin_receiver in notice_group["notice_receiver"]:
                receivers = []

                if origin_receiver.startswith("user#"):
                    receivers = [origin_receiver[5:]]
                elif origin_receiver.startswith("group#"):
                    receivers = self.group_to_users(origin_receiver[6:])

                # 在保证人员顺序的情况下去重
                # 记录人员所属的组
                for receiver in receivers:
                    if receiver in notice_receivers:
                        continue

                    if origin_receiver.startswith("group#"):
                        user_to_groups[receiver] = origin_receiver[6:]
                    notice_receivers.append(receiver)

            notice_ways = notice_group["notice_way"].get(str(self.event.level), [])

            # 企业微信群机器人特殊处理
            wxwork_group = notice_group.get("wxwork_group", {}).get(str(self.event.level))
            if "wxwork-bot" in notice_ways and wxwork_group:
                # 会话ID切分及特殊会话ID过滤
                receivers = [
                    receiver
                    for receiver in re.split(r"[ ;,]", wxwork_group)
                    if receiver and not receiver.startswith("@all")
                ]
                notice_configs["wxwork-bot"]["notice_receivers"].extend(receivers)
                notice_ways = [notice_way for notice_way in notice_ways if notice_way != "wxwork-bot"]

            if not notice_receivers:
                continue

            for notice_way in notice_ways:
                # 语音告警通知人合并
                if notice_way == "voice":
                    notice_configs[notice_way]["notice_receivers"].append(",".join(notice_receivers))
                else:
                    notice_configs[notice_way]["notice_receivers"].extend(notice_receivers)
                    notice_configs[notice_way]["user_to_groups"].update(user_to_groups)

        # 接收人去重
        for notice_way, config in notice_configs.items():
            config["notice_receivers"] = list(set(config["notice_receivers"]))

        return [
            {
                "notice_way": notice_way,
                "notice_receivers": list(set(config["notice_receivers"])),
                "user_to_groups": config["user_to_groups"],
            }
            for notice_way, config in notice_configs.items()
            if config["notice_receivers"]
        ]

    @cached_property
    def webhook_configs(self):
        webhook_configs = []
        for notice_group in self.action["notice_group_list"]:
            if notice_group.get("webhook_url"):
                webhook_configs.append({"url": notice_group["webhook_url"], "name": notice_group["notice_group_name"]})
        return webhook_configs

    def is_alarm_time(self) -> bool:
        """
        是否在告警时间内
        :return: bool
        """

        alarm_time_matcher = TimeMatch(
            cycle={
                "begin_time": self.action["config"]["alarm_start_time"],
                "end_time": self.action["config"]["alarm_end_time"],
            }
        )

        return alarm_time_matcher.is_time_match(self.event_action.create_time)

    def execute(self):
        """
        执行通知
        """
        logger.info("--begin collect_notice_action event_action({})".format(self.event_action.id))

        # 告警屏蔽
        is_shielded, shielder = self.shield_manager.shield(self.event)
        if is_shielded:
            self.event_action.extend_info["shield"] = {"type": shielder.type, "detail": shielder.detail}
            self.event_action.status = "SHIELDED"
            self.event_action.save()
            logger.info("event_action({}) shielded".format(self.event_action.id))
            return

        # 如果不在告警时间内，则不通知
        if not self.is_alarm_time():
            logger.info(
                "event_action({}) shielded because not in alarm time({} - {})".format(
                    self.event_action.id,
                    self.action["config"]["alarm_start_time"],
                    self.action["config"]["alarm_end_time"],
                )
            )
            self.event_action.extend_info["shield"] = {
                "type": ShieldType.ALARM_TIME,
                "detail": {
                    "alarm_start_time": self.action["config"]["alarm_start_time"],
                    "alarm_end_time": self.action["config"]["alarm_end_time"],
                },
            }
            self.event_action.status = "SHIELDED"
            self.event_action.save()
            return

        logger.info(
            "event_action({}) collect by notice_config({})".format(
                self.event_action.id, json.dumps(self.notice_configs)
            )
        )

        # 触发回调
        if self.webhook_configs:
            self.event_action.extend_info["webhook_configs"] = self.webhook_configs
            self.event_action.save()
            ACTION_LIST_KEY.client.lpush(ACTION_LIST_KEY.get_key(action_type="webhook"), self.event_action.id)
            ACTION_LIST_KEY.client.expire(ACTION_LIST_KEY.get_key(action_type="webhook"), ACTION_LIST_KEY.ttl)

        # 通知人及回调都为空
        if not self.notice_configs and not self.webhook_configs:
            self.event_action.status = EventAction.Status.FAILED
            self.event_action.message = _("通知对象为空")
            self.event_action.extend_info["empty_receiver"] = True
            self.event_action.save()
            return

        # 汇总通知
        for notice_config in self.notice_configs:
            self.notice(notice_config)

        logger.info("--end collect_notice_action event_action({})".format(self.event_action.id))

    def notice(self, notice_config):
        """
        按通知组进行汇总、通知
        :param notice_config: dict 通知组配置
        {
            "notice_way": "sms",,
            "notice_receivers": ["admin"],
            "user_to_groups": {
                "admin": "bk_biz_maintainer"
            }
        }
        """
        # 分通知类型进行汇总
        notice_way = notice_config["notice_way"]
        notice_receivers = notice_config["notice_receivers"]

        # 语音的汇总逻辑不一样
        if notice_config["notice_way"] == "voice":
            collector = VoiceCollector(self.event_action, notice_way)
            collector.collect(notice_receivers)
        else:
            collectors = [
                BizCollector(self.event_action, notice_way),
                DimensionCollector(self.event_action, notice_way),
            ]

            for collector in collectors:
                if not notice_receivers:
                    break
                collector.lock()
                notice_receivers = collector.collect(notice_receivers)
                collector.unlock()
