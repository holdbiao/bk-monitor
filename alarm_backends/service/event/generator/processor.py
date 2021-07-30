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


import copy
import json
import logging

import arrow
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext as _

from alarm_backends.constants import NO_DATA_LEVEL, NO_DATA_TAG_DIMENSION
from alarm_backends.core.cache.key import EVENT_EXTEND_CACHE_KEY, EVENT_EXTEND_ID_CACHE_KEY, EVENT_ID_CACHE_KEY
from alarm_backends.core.cache.strategy import StrategyCacheManager
from alarm_backends.core.control.record_parser import AnomalyIDParser, EventIDParser, RecordParser
from alarm_backends.core.control.strategy import Strategy
from alarm_backends.core.i18n import i18n
from alarm_backends.service.action.utils import create_actions
from alarm_backends.service.event.generator.translator import TranslatorFactory
from bkmonitor.models import AnomalyRecord, DataTypeLabel, Event, EventAction
from constants.data_source import DataSourceLabel
from core.errors.alarm_backends import StrategyNotFound

logger = logging.getLogger("event.generator")


class EventGeneratorProcessor(object):
    def __init__(self, anomaly_event):
        self.anomaly_event = anomaly_event["event_record"]
        self.anomaly_records = anomaly_event["anomaly_records"]
        self.strategy = self.get_strategy_snapshot(self.anomaly_event["strategy_snapshot_key"])
        self.strategy_id = self.strategy["id"]
        self.record_parser = RecordParser(self.anomaly_event)
        self.dimensions_md5 = self.record_parser.dimensions_md5
        self.source_time = self.record_parser.source_time
        self.event_id_cache_key = EVENT_ID_CACHE_KEY.get_key(
            strategy_id=self.strategy_id, item_id=self.record_parser.item_id, dimensions_md5=self.dimensions_md5
        )
        self.anomaly_ids = self.anomaly_event["trigger"]["anomaly_ids"]

        # 获取触发次数，以生成事件ID
        item = Strategy.get_item_in_strategy(self.strategy, self.record_parser.item_id)
        if self.is_no_data_point(self.anomaly_event):
            trigger_configs = {str(NO_DATA_LEVEL): Strategy.get_no_data_configs(item)}
        else:
            trigger_configs = Strategy.get_trigger_configs(item)
        trigger_count = trigger_configs[self.anomaly_event["trigger"]["level"]]["trigger_count"]

        self.new_event_id = self.anomaly_ids[trigger_count - 1]
        self.event_id = EVENT_ID_CACHE_KEY.client.get(self.event_id_cache_key)

    @staticmethod
    def is_no_data_point(event_record):
        """
        :summary: 判断是否是无数据告警生成的异常点
        :param event_record:
        :return:
        """
        dimensions = event_record["data"]["dimensions"]
        if NO_DATA_TAG_DIMENSION in dimensions:
            return True
        return False

    @classmethod
    def get_strategy_snapshot(cls, key):
        """
        获取配置快照
        bkmonitorv3.ee.cache.strategy.snapshot.2.1607087606
        ->
        ['bkmonitorv3.ee.cache.strategy.snapshot', '2', '1607087606']
        """
        try:
            strategy_id = int(key.rsplit(".", 2)[1])
        except IndexError:
            logger.exception(f"get an unexpected key: [{key}]")
            strategy_id = None
        snapshot = Strategy.get_strategy_snapshot_by_key(key, strategy_id)
        if not snapshot:
            raise StrategyNotFound({"key": key})
        return snapshot

    def expire_event_cache(self):
        """
        延长缓存过期时间
        """
        EVENT_ID_CACHE_KEY.expire(
            strategy_id=self.strategy_id, item_id=self.record_parser.item_id, dimensions_md5=self.dimensions_md5
        )

    def process(self):
        i18n.set_biz(self.strategy["bk_biz_id"])

        # 查询缓存是否有已经存在正在产生的事件ID
        event_id = EVENT_ID_CACHE_KEY.client.get(self.event_id_cache_key)

        if not event_id:
            # 如果当前没有告警事件，则创建一条新的事件
            logger.info(
                "anomaly({new_event_id}) no creating event, create new event, strategy({strategy_id})".format(
                    new_event_id=self.new_event_id, strategy_id=self.strategy_id
                )
            )
            self.create_new_event()
            return

        # 如果已有老事件ID.
        # 获取新事件告警级别
        new_event_level = int(self.anomaly_event["trigger"]["level"])
        # 获取老事件的告警级别
        old_event_level = EventIDParser(event_id).level

        if new_event_level > old_event_level:
            # 1-致命，2-预警，3-提醒
            # 如果新产生的告警级别比正在产生的事件级别低，则直接忽略
            logger.info(
                "[detect result] (ignored) anomaly({new_event_id}) restrained by event({old_event_id}), "
                "strategy({strategy_id})".format(
                    new_event_id=self.new_event_id, old_event_id=event_id, strategy_id=self.strategy_id
                )
            )
        elif new_event_level == old_event_level:
            # 新老告警级别相同，则只需更新异常点的 event_id 即可
            logger.info(
                "[detect result] (converged) anomaly({new_event_id}) converged because event({old_event_id}) "
                "has same level, strategy({strategy_id})".format(
                    new_event_id=self.new_event_id, old_event_id=event_id, strategy_id=self.strategy_id
                )
            )
            # self.update_event_id_for_anomaly_records(event_id)
            self.update_or_create_converge_action(event_id)
        else:
            # 新级别大于老级别，将老事件置为恢复，并且创建一个新的事件
            logger.info(
                "[detect result] (created) anomaly({new_event_id}) create a new event, "
                "strategy({strategy_id})".format(new_event_id=self.new_event_id, strategy_id=self.strategy_id)
            )
            self.recover_old_event(event_id, _("当前维度存在级别更高的事件，告警已恢复"))
            self.create_new_event()

        self.expire_event_cache()

    def recover_old_event(self, event_id, message=""):
        # 将老事件记录对应的状态置为“已恢复”
        Event.objects.filter(event_id=event_id).update(
            status=Event.EventStatus.RECOVERED,
            end_time=self.record_parser.mysql_time,
        )
        EventAction.objects.create(
            operate=EventAction.Operate.RECOVER,
            status=EventAction.Status.SUCCESS,
            event_id=event_id,
            message=message,
        )

    def create_new_event(self):
        """
        创建新事件
        """
        # 创建新的事件记录
        self.create_anomaly_records(self.new_event_id)
        with transaction.atomic():
            try:
                Event.objects.create(
                    event_id=self.new_event_id,
                    begin_time=AnomalyIDParser(self.anomaly_ids[0]).mysql_time,
                    bk_biz_id=self.strategy["bk_biz_id"],
                    strategy_id=self.strategy_id,
                    origin_config=self.strategy,
                    origin_alarm=self.get_origin_alarm(),
                    level=self.anomaly_event["trigger"]["level"],
                    status=Event.EventStatus.ABNORMAL,
                    target_key=self.target_key,
                )
            except IntegrityError:
                logger.info(
                    "[detect result] (ignored) anomaly({new_event_id}) event exists, ignore this event, "
                    "strategy({strategy_id})".format(new_event_id=self.new_event_id, strategy_id=self.strategy_id)
                )
                return
            EventAction.objects.create(
                operate=EventAction.Operate.CREATE, status=EventAction.Status.SUCCESS, event_id=self.new_event_id
            )

        # 事件第一次产生的同时，创建对应动作
        self.push_actions()

        # 更新异常记录的事件ID
        EVENT_ID_CACHE_KEY.client.set(self.event_id_cache_key, self.new_event_id)

    def push_actions(self):
        """
        将事件动作推送到队列中
        """
        # 尝试从缓存中获取最新策略数据，如果获取不到就使用快照
        strategy = StrategyCacheManager.get_strategy_by_id(self.strategy_id)
        strategy = strategy or self.strategy

        create_actions(self.new_event_id, strategy["action_list"], "anomaly")

    def get_origin_alarm(self):
        """
        补充维度翻译数据
        """
        dimensions = self.anomaly_event["data"].get("dimensions", {})
        translator = TranslatorFactory(self.strategy)
        dimension_translation = translator.translate(dimensions)
        origin_alarm = copy.deepcopy(self.anomaly_event)
        origin_alarm["dimension_translation"] = dimension_translation
        return origin_alarm

    def create_anomaly_records(self, event_id):
        """
        更新异常记录的event id
        """
        logger.debug(
            "update anomaly record event_id: AnomalyRecord: ({anomaly_ids})，event({event_id})".format(
                anomaly_ids=", ".join(self.anomaly_ids), event_id=event_id
            )
        )
        AnomalyRecord.objects.ignore_blur_create(self.anomaly_records, batch_size=200)
        AnomalyRecord.objects.filter(anomaly_id__in=self.anomaly_ids).update(event_id=event_id)

    def update_or_create_converge_action(self, event_id):
        """
        更新或创建收敛动作
        """
        if not self.event_id:
            # 如果初始化时判断没有事件产生，现在却被检测到收敛，这个时候也需要更新关联一下异常记录的event_id
            # 避免并发处理同一策略的多个异常点时，出现某些异常点漏关联event_id的问题
            self.create_anomaly_records(event_id)

        # 从异常记录中获取异常点的处理时间
        anomaly_id = self.anomaly_event["anomaly"][self.anomaly_event["trigger"]["level"]]["anomaly_id"]
        process_time = self.source_time
        for record in self.anomaly_records:
            if record.anomaly_id == anomaly_id:
                process_time = arrow.get(record.create_time).timestamp

        data_time = self.source_time
        latest_action = EventAction.objects.filter(event_id=event_id).last()

        if not latest_action or latest_action.operate != EventAction.Operate.CONVERGE:
            logger.debug("event({}) create Converge EventAction".format(event_id))
            extend_info = {
                "anomaly_record": self.anomaly_event,
                "data_time": {"min": data_time, "max": data_time},
                "process_time": {"min": process_time, "max": process_time},
                "anomaly_count": 1,
            }
            event_action_obj = EventAction.objects.create(
                operate=EventAction.Operate.CONVERGE,
                status=EventAction.Status.SUCCESS,
                event_id=event_id,
                extend_info=extend_info,
            )
            extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=event_action_obj.id)
            EVENT_EXTEND_CACHE_KEY.client.set(
                extend_cache_keys,
                json.dumps({"need_insert": False, "extend_info": extend_info}),
                ex=EVENT_EXTEND_CACHE_KEY.ttl,
            )
            cache_extend_id_keys = EVENT_EXTEND_ID_CACHE_KEY.get_key()
            EVENT_EXTEND_ID_CACHE_KEY.client.sadd(cache_extend_id_keys, event_action_obj.id)
            EVENT_EXTEND_ID_CACHE_KEY.expire()
        else:
            extend_cache_keys = EVENT_EXTEND_CACHE_KEY.get_key(id=latest_action.id)
            cache_extend_info = EVENT_EXTEND_CACHE_KEY.client.get(extend_cache_keys)
            if cache_extend_info:
                last_extend = json.loads(cache_extend_info)["extend_info"]
                # 计算出最值，并更新 extend_info
                new_extend_info = {
                    "anomaly_record": self.anomaly_event,
                    "data_time": {
                        "min": min(last_extend["data_time"]["min"], data_time),
                        "max": max(last_extend["data_time"]["max"], data_time),
                    },
                    "process_time": {
                        "min": min(last_extend["process_time"]["min"], process_time),
                        "max": max(last_extend["process_time"]["max"], process_time),
                    },
                    "anomaly_count": last_extend["anomaly_count"] + 1,
                }
                EVENT_EXTEND_CACHE_KEY.client.set(
                    extend_cache_keys,
                    json.dumps({"need_insert": True, "extend_info": new_extend_info}),
                    ex=EVENT_EXTEND_CACHE_KEY.ttl,
                )

    @property
    def target_key(self):
        """
        生成事件的 target key
        """
        item = self.strategy["item_list"][0]
        agg_dimensions = item.get("rt_query_config", {}).get("agg_dimension", [])
        if (
            item["data_type_label"] == DataTypeLabel.EVENT
            and item["data_source_label"] == DataSourceLabel.BK_MONITOR_COLLECTOR
        ):
            agg_dimensions = ["bk_target_ip", "bk_target_cloud_id"]

        data_dimensions = self.anomaly_event["data"]["dimensions"]
        scenario = self.strategy["scenario"]
        return self.generate_target_key(agg_dimensions, data_dimensions, scenario)

    @classmethod
    def generate_target_key(cls, agg_dimensions, data_dimensions, scenario):
        try:
            if scenario in ["os", "host_process"]:
                if "bk_target_ip" in agg_dimensions:
                    return Event.TargetKeyGenerator.Host.get_key(
                        ip=data_dimensions["bk_target_ip"], bk_cloud_id=data_dimensions["bk_target_cloud_id"]
                    )
                elif "ip" in agg_dimensions:
                    return Event.TargetKeyGenerator.Host.get_key(
                        ip=data_dimensions["ip"], bk_cloud_id=data_dimensions["bk_cloud_id"]
                    )
                else:
                    return Event.TargetKeyGenerator.Topo.get_key(
                        bk_obj_id=data_dimensions["bk_obj_id"], bk_inst_id=data_dimensions["bk_inst_id"]
                    )
            elif scenario in ["service_module", "component", "service_process"]:
                if "bk_target_service_instance_id" in agg_dimensions:
                    return Event.TargetKeyGenerator.ServiceInstance.get_key(
                        data_dimensions["bk_target_service_instance_id"]
                    )
                else:
                    return Event.TargetKeyGenerator.Topo.get_key(
                        bk_obj_id=data_dimensions["bk_obj_id"], bk_inst_id=data_dimensions["bk_inst_id"]
                    )
        except KeyError:
            return ""
        return ""
