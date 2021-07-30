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

import arrow
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from alarm_backends.core.cache import key
from alarm_backends.core.cache.cmdb import HostManager, ServiceInstanceManager
from alarm_backends.core.cache.key import EVENT_ID_CACHE_KEY, LAST_CHECKPOINTS_CACHE_KEY
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.service.event.manager.status_checker.base import BaseStatusChecker
from api.cmdb.define import TopoNode
from bkmonitor.models import Event, EventAction
from bkmonitor.utils.event_target import parse_target_key
from constants.data_source import DataTypeLabel
from core.errors.alarm_backends import StrategyItemNotFound

logger = logging.getLogger("event.manager")


class CloseStatusChecker(BaseStatusChecker):
    """
    事件关闭判断
    """

    DEFAULT_CHECK_WINDOW_UNIT = 60

    def __init__(self, event, strategy=None, event_id_parser=None):
        super(CloseStatusChecker, self).__init__(event, strategy, event_id_parser)
        self.latest_item = None
        try:
            if self.strategy:
                self.latest_item = Strategy.get_item_in_strategy(self.strategy, self.item_id)
        except StrategyItemNotFound:
            pass
        self.origin_item = Strategy.get_item_in_strategy(self.event.origin_config, self.item_id)

    def check(self):
        # 1. 检查策略是否被删除
        if not self.strategy:
            logger.info(
                "[process result] (closed) event({}), strategy({}) strategy is deleted or close".format(
                    self.event_id, self.strategy_id
                )
            )
            self.close(_("策略已被停用或删除，告警关闭"))
            return True

        # 2. 检查指标是否被删除
        if not self.latest_item:
            logger.info(
                "[process result] (closed) event({}), strategy({}) item({}) item is deleted".format(
                    self.event_id, self.strategy_id, self.item_id
                )
            )
            self.close(_("策略监控项已被删除，告警关闭"))
            return True

        # 3. 检查metric_id是否被修改
        if self.origin_item["metric_id"] != self.latest_item["metric_id"]:
            logger.info(
                "[process result] (closed) event({}), strategy({}) item({}) "
                "item has been changed: metric ({}) -> ({})".format(
                    self.event_id,
                    self.strategy_id,
                    self.item_id,
                    self.origin_item["metric_id"],
                    self.latest_item["metric_id"],
                )
            )
            self.close(_("策略监控项已被修改，告警关闭"))
            return True

        # 4. 检查监控维度是否被修改
        latest_dimensions = self.latest_item["rt_query_config"].get("agg_dimension", [])
        origin_dimensions = self.origin_item["rt_query_config"].get("agg_dimension", [])

        if set(latest_dimensions) != set(origin_dimensions):
            logger.info(
                "[process result] (closed) event({}), strategy({}) item({}) "
                "dimension has been changed: {} -> {}".format(
                    self.event_id,
                    self.strategy_id,
                    self.item_id,
                    json.dumps(origin_dimensions),
                    json.dumps(latest_dimensions),
                )
            )
            self.close(_("策略监控维度已被修改，告警关闭"))
            return True

        # 5. 检查当前告警级别是否被删除
        if not self.event.is_no_data:
            latest_levels = [str(algorithm_config["level"]) for algorithm_config in self.latest_item["algorithm_list"]]
            origin_levels = [str(algorithm_config["level"]) for algorithm_config in self.origin_item["algorithm_list"]]
            if str(self.level) not in latest_levels:
                logger.info(
                    "[process result] (closed) event({}), strategy({}) item({}) "
                    "algorithm_level({}) has been deleted: {} -> {}".format(
                        self.event_id,
                        self.strategy_id,
                        self.item_id,
                        self.level,
                        json.dumps(origin_levels),
                        json.dumps(latest_levels),
                    )
                )
                self.close(_("告警级别对应的检测算法已被删除，告警关闭"))
                return True

        # 6. 当前的是无数据告警，且无数据告警配置被关闭，则直接关闭告警
        if self.event.is_no_data and not self.latest_item["no_data_config"]["is_enabled"]:
            logger.info(
                "[process result] (closed) event({}), strategy({}) item({}) "
                "no_data_config has closed".format(self.event_id, self.strategy_id, self.item_id)
            )
            self.close(_("无数据告警设置被关闭，告警关闭"))
            return True

        # 7. 检查当前告警的目标实例是否还在策略的监控范围内
        if self.check_target_not_included():
            return True

        # 8. 检查是否为无数据上报（仅限时序数据）
        if self.check_no_data():
            return True

        return False

    def check_no_data(self):
        """
        检查是否为无数据上报（仅限时序数据）
        """
        if self.event.is_no_data:
            # 如果是无数据告警，则忽略
            return False

        # 是否为时序类告警
        is_time_series = self.latest_item["data_type_label"] == DataTypeLabel.TIME_SERIES
        if not is_time_series:
            # 如果是非时序类告警，则不检查
            return False

        # 获取当前维度最新上报时间
        last_check_timestamp = LAST_CHECKPOINTS_CACHE_KEY.client.hget(
            LAST_CHECKPOINTS_CACHE_KEY.get_key(),
            LAST_CHECKPOINTS_CACHE_KEY.get_field(
                strategy_id=self.strategy_id,
                item_id=self.item_id,
                dimensions_md5=self.dimensions_md5,
                level=self.level,
            ),
        )

        last_check_timestamp = int(last_check_timestamp) if last_check_timestamp else 0

        now_timestamp = arrow.now().timestamp
        trigger_config = Strategy.get_trigger_configs(self.latest_item)[str(self.level)]
        trigger_window_size = max(trigger_config["check_window_size"], settings.EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE)
        rt_query_config = self.latest_item.get("rt_query_config") or {}
        window_unit = rt_query_config.get("agg_interval", self.DEFAULT_CHECK_WINDOW_UNIT)

        extend_fields = rt_query_config.get("extend_fields") or {}
        if isinstance(extend_fields, dict) and extend_fields.get("intelligent_detect", {}):
            # 智能异常检测在计算平台会经过几层dataflow，会有一定的周期延时，所以这里需要再加上这个延时窗口
            trigger_window_size = trigger_window_size + settings.BK_DATA_INTELLIGENT_DETECT_DELAY_WINDOW

        if int(last_check_timestamp) + trigger_window_size * window_unit < now_timestamp:
            # 如果最近上报时间距离当前时间超过了一个触发窗口的大小，则认为无数据上报，告警关闭
            self.close(_("在恢复检测周期内无数据上报，告警已关闭"))
            logger.info(
                _(
                    "[处理结果] (no_data) event({}), strategy({}), last_check_timestamp({}), now_timestamp({}),"
                    "在恢复检测周期内无数据上报，进行事件关闭"
                ).format(self.event.event_id, self.strategy_id, last_check_timestamp, now_timestamp)
            )
            return True
        return False

    def check_target_not_included(self):
        if self.latest_item["target"] and self.latest_item["target"][0]:
            target = self.latest_item["target"][0][0]
        else:
            return False

        key_generator = parse_target_key(self.event.target_key)

        if isinstance(key_generator, Event.TargetKeyGenerator.Host):
            host = HostManager.get(key_generator.ip, key_generator.bk_cloud_id)

            if not host:
                # 如果主机在缓存中不存在，则直接恢复告警
                # 需要考虑一个问题，如何判断缓存未刷新的情况
                logger.info(
                    "[process result] (closed) event({}), strategy({}), host({}|{}) not found in cmdb".format(
                        self.event.event_id, self.strategy_id, key_generator.ip, key_generator.bk_cloud_id
                    )
                )
                self.close(
                    _("CMDB 未查询到告警目标主机 ({}|{}) 的信息，主机可能已被删除，告警关闭").format(key_generator.ip, key_generator.bk_cloud_id)
                )
                return True

            if target["field"] == "bk_target_ip":
                # 如果是静态主机的情况，直接判断监控目标是否有当前主机
                matched_host = [
                    value
                    for value in target["value"]
                    if value["bk_target_ip"] == host.ip and value["bk_target_cloud_id"] == host.bk_cloud_id
                ]

                if not matched_host:
                    logger.info(
                        "[process result] (closed) event({}), strategy({}), host({}|{}) "
                        "not match current target: {}".format(
                            self.event.event_id,
                            self.strategy_id,
                            key_generator.ip,
                            key_generator.bk_cloud_id,
                            target["value"],
                        )
                    )
                    self.close(_("告警目标实例已不在监控目标范围内，告警关闭"))
                    return True

                return False

            topo_link = list(host.topo_link.values())

        elif isinstance(key_generator, Event.TargetKeyGenerator.ServiceInstance):
            service_instance = ServiceInstanceManager.get(key_generator.bk_service_instance_id)

            if not service_instance:
                # 如果服务实例在缓存中不存在，则直接恢复告警
                logger.info(
                    "[process result] (closed) event({}), strategy({}), service_instance({}) "
                    "not found in cmdb".format(
                        self.event.event_id, self.strategy_id, key_generator.bk_service_instance_id
                    )
                )
                self.close(_("CMDB 未查询到告警目标服务实例 ({}) 的信息，服务实例可能已被删除，告警关闭").format(key_generator.bk_service_instance_id))
                return True

            topo_link = list(service_instance.topo_link.values())

        elif isinstance(key_generator, Event.TargetKeyGenerator.Topo):
            topo_link = [[TopoNode(bk_obj_id=key_generator.bk_obj_id, bk_inst_id=key_generator.bk_inst_id)]]

        else:
            # 如果都不是以上的类型，则跳过检测
            return False

        if target["field"] in ["service_topo_node", "host_topo_node"]:
            topo_link_keys = {node.id for nodes in topo_link for node in nodes}
            target_topo_keys = {"{}|{}".format(node["bk_obj_id"], node["bk_inst_id"]) for node in target["value"]}

            # 当前实例的拓扑链和目标节点有重合的部分的，即表示当前目标包含该实例，否则需要关闭事件
            is_target_included = topo_link_keys & target_topo_keys
            if not is_target_included:

                logger.info(
                    "[process result] (closed) event({}), strategy({}), instance does not match "
                    "current topo {} -> {}".format(
                        self.event.event_id, self.strategy_id, topo_link_keys, target_topo_keys
                    )
                )

                self.close(_("告警目标实例已不在监控目标范围内，告警关闭"))
                return True

        return False

    def close(self, message):
        """
        事件关闭
        """
        self.event.status = Event.EventStatus.CLOSED
        self.event.end_time = timezone.now()
        self.event.save(update_fields=["status", "end_time"])
        EventAction.objects.create(
            operate=EventAction.Operate.CLOSE,
            status=EventAction.Status.SUCCESS,
            event_id=self.event.event_id,
            message=message,
        )

        # 事件关闭的同时，创建对应动作
        self.push_actions(notice_type="close")

        EVENT_ID_CACHE_KEY.client.delete(self.event_id_cache_key)
        # 无数据告警，清理最后检测异常点记录
        if self.event.is_no_data:
            key.NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY.client.hdel(
                key.NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY.get_key(),
                key.NO_DATA_LAST_ANOMALY_CHECKPOINTS_CACHE_KEY.get_field(
                    strategy_id=self.event.strategy_id, item_id=self.item_id, dimensions_md5=self.dimensions_md5
                ),
            )
