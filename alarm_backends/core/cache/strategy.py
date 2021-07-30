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
告警策略配置缓存
"""
import copy
import json
import logging
from collections import defaultdict
from hashlib import md5
from itertools import chain, groupby, product
from operator import itemgetter
from typing import List, Optional, Dict

from six.moves import map

from alarm_backends.constants import CONST_ONE_DAY
from alarm_backends.core.cache.base import CacheManager
from api.cmdb.define import TopoTree
from bkmonitor.models import (
    NoticeGroup,
    StrategyLabel,
    StrategyModel,
)
from bkmonitor.strategy.new_strategy import Strategy
from bkmonitor.utils.common_utils import count_md5
from constants.data_source import DataSourceLabel, DataTypeLabel
from constants.strategy import (
    AdvanceConditionMethod,
    TargetFieldType,
    AGG_METHOD_REAL_TIME,
)
from core.drf_resource import api
from constants.cmdb import TargetNodeType
from alarm_backends.core.cache.cmdb import ServiceTemplateManager, SetTemplateManager

logger = logging.getLogger("cache")


class StrategyCacheManager(CacheManager):
    """
    告警策略缓存
    """

    CACHE_TIMEOUT = CONST_ONE_DAY
    # 策略详情的缓存key
    CACHE_KEY_TEMPLATE = CacheManager.CACHE_KEY_PREFIX + ".strategy_{strategy_id}"
    # 策略ID列表缓存key
    IDS_CACHE_KEY = CacheManager.CACHE_KEY_PREFIX + ".strategy_ids"
    # 业务ID列表缓存key
    BK_BIZ_IDS_CACHE_KEY = CacheManager.CACHE_KEY_PREFIX + ".bk_biz_ids"
    # real time 走实时数据相关的策略
    REAL_TIME_CACHE_KEY = CacheManager.CACHE_KEY_PREFIX + ".real_time_strategy_ids"
    # gse事件
    GSE_ALARM_CACHE_KEY = CacheManager.CACHE_KEY_PREFIX + ".gse_alarm_strategy_ids"
    # 策略分组
    STRATEGY_GROUP_CACHE_KEY = CacheManager.CACHE_KEY_PREFIX + ".strategy_group"

    @classmethod
    def transform_template_to_topo_nodes(cls, item, template_node_type, cache_manager):
        """
        转化模板为节点
        :param item: 监控项
        :param template_node_type: 模板类型，可选[SET_TEMPLATE, SERVICE_TEMPLATE]
        :param cache_manager: 模板缓存管理器
        :return: 修改target后的监控项
        """
        if template_node_type == TargetNodeType.SET_TEMPLATE:
            bk_obj_id = "set"
        else:
            bk_obj_id = "module"

        new_value = []
        for target in item["target"][0][0]["value"]:
            instances = cache_manager.get(target["bk_inst_id"]) or []
            for instance in instances:
                new_value.append(
                    {
                        "bk_obj_id": bk_obj_id,
                        "bk_inst_id": instance if isinstance(instance, int) else instance["bk_inst_id"],  # 新老缓存兼容
                    }
                )
        item["target"][0][0]["field"] = item["target"][0][0]["field"].replace(template_node_type.lower(), "topo_node")
        item["target"][0][0]["value"] = new_value
        return item

    @classmethod
    def get_strategies(cls):
        strategy_label_dict = StrategyLabel.get_label_dict()

        strategies = []
        for strategy in Strategy.from_models(StrategyModel.objects.filter(is_enabled=True)):
            try:
                strategies.append(strategy.to_dict_v1())
            except Exception as err:
                logger.exception(f"cache strategy[{strategy.id}][{strategy.bk_biz_id}] error: {err}")

        notice_groups = {}
        for notice_group in NoticeGroup.objects.filter(is_enabled=True, is_deleted=False).values(
            "notice_receiver",
            "name",
            "webhook_url",
            "notice_way",
            "message",
            "id",
            "wxwork_group",
        ):
            notice_group["notice_group_id"] = notice_group["id"]
            notice_group["notice_group_name"] = notice_group["name"]
            notice_groups[notice_group["id"]] = notice_group

        result = []
        for strategy in strategies:
            # 补充策略标签
            strategy["labels"] = strategy_label_dict.get(strategy["id"], [])

            # 拆分rt_query_config
            for item in strategy["item_list"]:
                rt_query_config = {}
                for field, value in item.items():
                    if field not in [
                        "strategy_id",
                        "no_data_config",
                        "metric_id",
                        "id",
                        "name",
                        "data_source_label",
                        "data_type_label",
                        "target",
                        "item_id",
                        "item_name",
                        "algorithm_list",
                        "rt_query_config_id",
                        "update_time",
                        "update_user",
                    ]:
                        rt_query_config[field] = value
                for field in rt_query_config:
                    item.pop(field)
                rt_query_config["id"] = item["rt_query_config_id"]
                rt_query_config["rt_query_config_id"] = item["rt_query_config_id"]
                item["rt_query_config"] = rt_query_config

            # 补充通知组信息
            for action in strategy["action_list"]:
                action["notice_group_list"] = [
                    notice_groups[int(notice_group_id)]
                    for notice_group_id in action["notice_group_list"]
                    if int(notice_group_id) in notice_groups
                ]

            # 过滤没有item的策略
            if not strategy["item_list"]:
                logger.warning(f"strategy({strategy['id']}) item_list is empty")
                continue

            try:
                if cls.handle_strategy(strategy):
                    result.append(strategy)
            except Exception as e:
                logger.error("refresh strategy error when handle_strategy", e)
                logger.exception(e)
        return result

    @classmethod
    def handle_strategy(cls, strategy) -> bool:
        for item in strategy["item_list"]:
            data_source_label = item["data_source_label"]
            data_type_label = item["data_type_label"]

            target = item["target"]
            if target and target[0]:
                item.setdefault("rt_query_config", {}).setdefault("agg_dimension", [])
                is_instance_dimension = {"bk_target_ip", "bk_target_service_instance_id"} & set(
                    item["rt_query_config"]["agg_dimension"]
                )
                is_ip_target = target[0][0]["field"] == "bk_target_ip"

                # 如果是静态IP监控目标，需要补全维度，避免监控目标失效
                if is_ip_target:
                    item["rt_query_config"]["agg_dimension"].extend(["bk_target_ip", "bk_target_cloud_id"])
                    item["rt_query_config"]["agg_dimension"] = list(set(item["rt_query_config"]["agg_dimension"]))

                # 日志关键字告警按节点聚合需要使用bk_obj_id和bk_inst_id
                if data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR and data_type_label == DataTypeLabel.LOG:
                    if not is_ip_target and not is_instance_dimension:
                        item["rt_query_config"]["agg_dimension"].extend(["bk_obj_id", "bk_inst_id"])

                # 转化集群/服务模板为拓扑节点
                target_field = item["target"][0][0]["field"]
                if TargetNodeType.SET_TEMPLATE in target_field.upper():
                    item = cls.transform_template_to_topo_nodes(item, TargetNodeType.SET_TEMPLATE, SetTemplateManager)
                elif TargetNodeType.SERVICE_TEMPLATE in target_field.upper():
                    item = cls.transform_template_to_topo_nodes(
                        item, TargetNodeType.SERVICE_TEMPLATE, ServiceTemplateManager
                    )

                # 如果value为空，则说明模板下不存在节点，过滤掉
                if not item["target"][0][0]["value"]:
                    logger.info(f"skip strategy({strategy['id']}) because target is empty")
                    return False

            query_config = item.get("rt_query_config", {})
            extend_fields = query_config.get("extend_fields", {})

            # 智能异常检测算法，结果表是存在intelligent_detect中，需要用这个配置
            if isinstance(extend_fields, dict) and extend_fields.get("intelligent_detect", {}):
                intelligent_detect = extend_fields.get("intelligent_detect", {})
                item["data_source_label"] = intelligent_detect.get("data_source_label", item["data_source_label"])
                item["data_type_label"] = intelligent_detect.get("data_type_label", item["data_type_label"])
                query_config.update(intelligent_detect)
                query_config.setdefault("extend_fields", {})["intelligent_detect"] = copy.deepcopy(intelligent_detect)

            # 补充查询配置md5，后续进行分组查询
            item_one = data_type_label in [DataTypeLabel.TIME_SERIES, DataTypeLabel.LOG]
            item_two = data_source_label == DataSourceLabel.CUSTOM and data_type_label == DataTypeLabel.EVENT
            if not any([item_one, item_two]):
                item["query_md5"] = ""
            else:
                item["query_md5"] = cls.get_query_md5(strategy["bk_biz_id"], item)

            return True

    @classmethod
    def get_strategy_ids(cls):
        """
        从缓存获取策略ID列表
        :return: 策略ID列表
        :rtype: list[int]
        """
        return json.loads(cls.cache.get(cls.IDS_CACHE_KEY) or "[]")

    @classmethod
    def get_strategy_by_id(cls, strategy_id):
        """
        从缓存中获取策略详情
        :param strategy_id: 策略ID
        :return: dict
        {
            "bk_biz_id":2,
            "item_list":[
                {
                    "rt_query_config":{
                        "metric_field":"idle",
                        "agg_dimension":[
                            "ip",
                            "bk_cloud_id"
                        ],
                        "unit_conversion":1.0,
                        "id":2,
                        "extend_fields":"",
                        "rt_query_config_id":2,
                        "agg_method":"AVG",
                        "agg_condition":[

                        ],
                        "agg_interval":60,
                        "result_table_id":"system.cpu_detail",
                        "unit":"%"
                    },
                    "metric_id":"bk_monitor.system.cpu_detail.idle",
                    "item_name":"\u7a7a\u95f2\u7387",
                    "strategy_id":1,
                    "data_source_label":"bk_monitor",
                    "algorithm_list":[
                        {
                            "algorithm_config":[
                                {
                                    "threshold":0.1,
                                    "method":"gte"
                                }
                            ],
                            "level":1,
                            "strategy_id":1,
                            "trigger_config":{
                                "count":1,
                                "check_window":5
                            },
                            "algorithm_type":"Threshold",
                            "recovery_config":{
                                "check_window":5
                            },
                            "algorithm_id":2,
                            "message_template":"",
                            "item_id":2,
                            "id":2
                        }
                    ],
                    "no_data_config":{
                        "is_enabled":False,
                        "continuous":5
                    },
                    "rt_query_config_id":2,
                    "item_id":2,
                    "data_type_label":"time_series",
                    "id":2,
                    "name":"\u7a7a\u95f2\u7387",
                    "target":[
                        [
                            {
                                "field":"bk_target_ip",
                                "method":"eq",
                                "value":[
                                    {
                                        "bk_target_ip":"127.0.0.1",
                                        "bk_target_cloud_id":0,
                                        "bk_supplier_id":0
                                    },
                                ]
                            }
                        ]
                    ],
                }
            ],
            "scenario":"os",
            "strategy_id":1,
            "action_list":[
                {
                    "notice_template":{
                        "action_id":2,
                        "anomaly_template":"aa",
                        "recovery_template":""
                    },
                    "id":2,
                    "notice_group_list":[
                        {
                            "notice_receiver":[
                                "user#test"
                            ],
                            "name":"test",
                            "notice_way":{
                                "1":[
                                    "weixin"
                                ],
                                "3":[
                                    "weixin"
                                ],
                                "2":[
                                    "weixin"
                                ]
                            },
                            "webhook_url": "",
                            "notice_group_id":1,
                            "message":"",
                            "notice_group_name":"test",
                            "id":1
                        }
                    ],
                    "action_type":"notice",
                    "config":{
                        "alarm_end_time":"23:59:59",
                        "send_recovery_alarm":False,
                        "alarm_start_time":"00:00:00",
                        "alarm_interval":120
                    },
                    "strategy_id":1,
                    "action_id":2
                }
            ],
            "source":"bk_monitor",
            "strategy_name":"test",
            "id":1,
            "name":"test"
        }
        """
        return json.loads(cls.cache.get(cls.CACHE_KEY_TEMPLATE.format(strategy_id=strategy_id)) or "null")

    @classmethod
    def get_all_bk_biz_ids(cls):
        bk_biz_ids = json.loads(cls.cache.get(cls.BK_BIZ_IDS_CACHE_KEY) or "[]")
        if not bk_biz_ids:
            strategies = cls.get_strategies()
            bk_biz_ids = [strategy["bk_biz_id"] for strategy in strategies]
        return bk_biz_ids

    @classmethod
    def get_time_series_strategy_ids(cls):
        # 1. 所有的配置的策略
        all_strategy_ids = set(map(int, cls.get_strategy_ids()))

        # 2. 系统事件、自定义字符型、进程托管事件相关策略
        custom_event_strategy_ids = set(map(int, chain(*list(cls.get_gse_alarm_strategy_ids().values()))))

        # 3. 实时数据相关策略
        real_time = cls.get_real_time_data_strategy_ids()
        real_time_strategy_ids = set(map(int, chain(*[s for r in list(real_time.values()) for s in list(r.values())])))

        return all_strategy_ids - custom_event_strategy_ids - real_time_strategy_ids

    @classmethod
    def get_real_time_data_strategy_ids(cls):
        """
        获取real time 走实时数据相关的策略

        type:dict(rt_id -> bk_biz_id -> strategy_ids)
        """
        return json.loads(cls.cache.get(cls.REAL_TIME_CACHE_KEY) or "{}")

    @classmethod
    def get_gse_alarm_strategy_ids(cls):
        """
        获取gse事件策略
        :return: 策略ID列表
        :rtype: dict
        """
        return json.loads(cls.cache.get(cls.GSE_ALARM_CACHE_KEY) or "{}")

    @classmethod
    def get_host_target_key(cls, item):
        """
        主机目标hash key
        :param item: Item配置
        :rtype: str
        """
        metric_id = item["metric_id"]
        rt_query_config = item["rt_query_config"]
        agg_config = {
            "agg_condition": rt_query_config.get("agg_condition"),
            "agg_dimension": rt_query_config.get("agg_dimension"),
            "agg_method": rt_query_config.get("agg_method"),
            "agg_interval": rt_query_config.get("agg_interval"),
        }

        m = md5()
        m.update(json.dumps(agg_config, sort_keys=True).encode("utf-8"))
        agg_md5 = m.hexdigest()

        return "{}.{}".format(metric_id, agg_md5)

    @classmethod
    def get_strategy_group_keys(cls):
        """
        获取全部策略分组key
        :return:
        """
        return cls.cache.hkeys(cls.STRATEGY_GROUP_CACHE_KEY)

    @classmethod
    def get_strategy_group_detail(cls, strategy_group_key):
        data = cls.cache.hget(cls.STRATEGY_GROUP_CACHE_KEY, strategy_group_key) or "{}"
        return json.loads(data)

    @classmethod
    def refresh_strategy_ids(cls, strategies):
        """
        刷新策略ID列表缓存
        :param strategies: 策略列表
        :type strategies: list
        """
        old_strategy_ids = cls.get_strategy_ids()
        new_strategy_ids = [strategy["id"] for strategy in strategies]

        # 缓存策略列表
        cls.cache.set(cls.IDS_CACHE_KEY, json.dumps(new_strategy_ids), cls.CACHE_TIMEOUT)

        for strategy_id in old_strategy_ids:
            if strategy_id not in new_strategy_ids:
                cls.cache.delete(cls.CACHE_KEY_TEMPLATE.format(strategy_id=strategy_id))

    @classmethod
    def refresh_bk_biz_ids(cls, strategies):
        """
        刷新配置了策略的业务ID列表
        """
        bk_biz_ids = [strategy["bk_biz_id"] for strategy in strategies]
        cls.cache.set(cls.BK_BIZ_IDS_CACHE_KEY, json.dumps(bk_biz_ids), cls.CACHE_TIMEOUT)

    @classmethod
    def refresh_real_time_strategy_ids(cls, strategies):
        """
        刷新实时数据的相关策略
        :param strategies: 策略列表
        :cache data: type:dict(rt_id -> bk_biz_id -> strategy_ids)
        """
        real_time_strategys = {}
        for strategy in strategies:
            try:
                bk_biz_id = strategy["bk_biz_id"]
                item = strategy["item_list"][0]
                data_type_label = item["data_type_label"]
                if (
                    data_type_label == DataTypeLabel.TIME_SERIES
                    and item["rt_query_config"]["agg_method"] == AGG_METHOD_REAL_TIME
                ):
                    real_time_strategys.setdefault(item["rt_query_config"]["result_table_id"], {}).setdefault(
                        bk_biz_id, []
                    ).append(strategy["id"])
            except Exception as e:
                logger.error("refresh strategy error when refresh_real_time_strategy_ids", e)
                logger.exception(e)

        cls.cache.set(cls.REAL_TIME_CACHE_KEY, json.dumps(real_time_strategys), cls.CACHE_TIMEOUT)

    @classmethod
    def refresh_gse_alarm_strategy_ids(cls, strategies):
        """
        刷新gse事件策略ID列表缓存
        :param strategies: 策略列表
        :type strategies: list
        """
        gse_event_strategy_ids = defaultdict(list)
        for strategy in strategies:
            try:
                item = strategy["item_list"][0]
                data_source_label = item["data_source_label"]
                data_type_label = item["data_type_label"]
                if data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR and data_type_label == DataTypeLabel.EVENT:
                    gse_event_strategy_ids[strategy["bk_biz_id"]].append(strategy["id"])
            except Exception as e:
                logger.error("refresh strategy error when refresh_gse_alarm_strategy_ids", e)
                logger.exception(e)

        cls.cache.set(cls.GSE_ALARM_CACHE_KEY, json.dumps(gse_event_strategy_ids), cls.CACHE_TIMEOUT)

    @classmethod
    def get_query_md5(cls, bk_biz_id, item):
        item = copy.deepcopy(item)
        rt_query_config = item["rt_query_config"]
        query_config = {
            "bk_biz_id": int(bk_biz_id),
            "data_source_label": item["data_source_label"],
            "data_type_label": item["data_type_label"],
            "agg_method": rt_query_config.get("agg_method"),
            "agg_interval": rt_query_config.get("agg_interval"),
            "agg_dimension": rt_query_config.get("agg_dimension"),
            "agg_condition": rt_query_config.get("agg_condition"),
            "result_table_id": rt_query_config.get("result_table_id"),
            "metric_field": rt_query_config.get("metric_field"),
            "keywords_query_string": rt_query_config.get("keywords_query_string"),
        }

        # 日志平台来源数据需要加上index_set_id作为查询条件
        if query_config["data_source_label"] == DataSourceLabel.BK_LOG_SEARCH:
            query_config["index_set_id"] = rt_query_config.get("extend_fields", {}).get("index_set_id")
        elif (
            query_config["data_source_label"] == DataSourceLabel.CUSTOM
            and query_config["data_type_label"] == DataTypeLabel.EVENT
        ):
            query_config["custom_event_name"] = rt_query_config.get("extend_fields", {}).get("custom_event_name")

        # 如果含有复杂查询条件，则查询时不添加该条件
        if item["data_type_label"] == DataTypeLabel.TIME_SERIES and query_config["agg_condition"]:
            for condition in query_config["agg_condition"]:
                if condition["method"] in AdvanceConditionMethod:
                    query_config["agg_condition"] = []
                    break

        return count_md5(query_config)

    @classmethod
    def refresh_strategy(cls, strategies):
        """
        刷新策略缓存
        :param strategies: 策略列表
        :type strategies: list
        """
        strategy_groups = defaultdict(lambda: defaultdict(list))

        pipeline = cls.cache.pipeline()
        for strategy in strategies:
            pipeline.set(
                cls.CACHE_KEY_TEMPLATE.format(strategy_id=strategy["id"]), json.dumps(strategy), cls.CACHE_TIMEOUT
            )

            for item in strategy["item_list"]:
                if item.get("query_md5"):
                    strategy_groups[item["query_md5"]][strategy["id"]].append(item["id"])

        old_groups = cls.cache.hkeys(cls.STRATEGY_GROUP_CACHE_KEY)
        for query_md5 in old_groups:
            if query_md5 not in strategy_groups:
                pipeline.hdel(cls.STRATEGY_GROUP_CACHE_KEY, query_md5)
        for query_md5 in strategy_groups:
            pipeline.hset(cls.STRATEGY_GROUP_CACHE_KEY, query_md5, json.dumps(strategy_groups[query_md5]))
        pipeline.expire(cls.STRATEGY_GROUP_CACHE_KEY, cls.CACHE_TIMEOUT)

        pipeline.execute()

    @classmethod
    def add_target_shield_condition(cls, strategies: List):
        """
        添加监控目标抑制条件
        1. 主机目标抑制拓扑目标
           如主机A属于模块B，同时配置两个查询条件相同的策略，模块B的策略不会产生主机A的告警
        2. 低层级拓扑目标抑制高层级拓扑目标
           如果模块A属于集群B，同时配置两个查询条件相同的策略，集群B不会产生模块A的告警
        """

        def get_query_sort_key(x):
            """
            获取查询配置排序字段
            """
            return x["items"][0]["query_md5"] or x["items"][0]["query_configs"][0]["metric_id"]

        # 过滤掉无目标，无查询分组的策略
        strategies = [
            strategy
            for strategy in strategies
            if (
                (
                    strategy["item_list"][0]["query_md5"]
                    or (
                        strategy["item_list"][0]["data_type_label"] == DataTypeLabel.EVENT
                        and strategy["item_list"][0]["data_source_label"] == DataSourceLabel.BK_MONITOR_COLLECTOR
                    )
                )
                and strategy["item_list"][0]["target"]
                and strategy["item_list"][0]["target"][0]
            )
        ]

        # 按业务、查询配置md5分组添加抑制条件
        strategies.sort(key=itemgetter("bk_biz_id"))
        for bk_biz_id, strategies_biz in groupby(strategies, key=itemgetter("bk_biz_id")):
            try:
                topo_tree: TopoTree = api.cmdb.get_topo_tree(bk_biz_id=bk_biz_id)
                strategies_biz = list(strategies_biz)
                strategies_biz.sort(key=get_query_sort_key)
                for query_md5, strategies_query in groupby(strategies_biz, get_query_sort_key):
                    strategies_query = list(strategies_query)

                    # 只有一条则不存抑制的可能
                    if len(strategies_query) <= 1:
                        continue

                    # 根据同组内的其他策略配置，在target中添加抑制条件
                    processor = TargetShieldProcessor(strategies_query, topo_tree)
                    for strategy in strategies_query:
                        processor.insert_target(strategy)
            except Exception as e:
                logger.error("refresh strategy error when add_target_shield_condition", e)
                logger.exception(e)

    @classmethod
    def refresh(cls):
        # 获取策略列表并缓存
        strategies = cls.get_strategies()

        processors = [
            cls.add_target_shield_condition,
            cls.refresh_strategy_ids,
            cls.refresh_bk_biz_ids,
            cls.refresh_strategy,
            cls.refresh_real_time_strategy_ids,
            cls.refresh_gse_alarm_strategy_ids,
        ]

        for processor in processors:
            try:
                processor(strategies)
            except Exception as e:
                logger.error(f"refresh strategy error when {processor.__name__}")
                logger.exception(e)


class TargetShieldProcessor:
    """
    策略目标抑制处理器
    """

    def __init__(self, strategies: List, topo_tree: TopoTree):
        self.strategies = strategies
        self.nodes = topo_tree.get_all_nodes_with_relation()

        self.static_nodes = self.get_static_nodes()
        self.dynamic_nodes = self.get_dynamic_nodes()

    def get_static_nodes(self):
        """
        静态节点所属模块列表
        """
        nodes = set()
        for strategy in self.strategies:
            target = strategy["item_list"][0]["target"][0][0]

            if not target["field"] in [TargetFieldType.host_target_ip, TargetFieldType.host_ip]:
                continue

            for host in target["value"]:
                ip = host.get("bk_target_ip") or host.get("ip", "")
                bk_cloud_id = host.get("bk_target_cloud_id") or host.get("bk_cloud_id", 0)
                nodes.add(f"{ip}|{bk_cloud_id}")
        return nodes

    def get_dynamic_nodes(self):
        """
        动态节点列表
        """
        nodes = set()
        for strategy in self.strategies:
            target = strategy["item_list"][0]["target"][0][0]

            if target["field"] not in ["host_topo_node", "service_topo_node"]:
                continue

            for node in target["value"]:
                key = f"{node['bk_obj_id']}|{node['bk_inst_id']}"

                if key in self.nodes:
                    nodes.add(key)
        return nodes

    def is_parent(self, a: str, b: str) -> bool:
        """
        节点A是否是节点B的父节点
        """
        a: Optional[TopoTree] = self.nodes.get(a)
        b: Optional[TopoTree] = self.nodes.get(b)

        if not a or not b:
            return False

        result = False
        while b._parent:
            if b._parent == a:
                result = True
                break
            b = b._parent

        return result

    def insert_target(self, current_strategy):
        """
        根据其他策略添加屏蔽条件
        """
        current_target = current_strategy["item_list"][0]["target"][0][0]

        # 静态目标直接跳过
        if current_target["field"] in [TargetFieldType.host_ip, TargetFieldType.host_target_ip]:
            return

        # 静态节点直接抑制
        if self.static_nodes:
            current_strategy["item_list"][0]["target"][0].append(
                {
                    "field": "bk_target_ip",
                    "method": "neq",
                    "value": [
                        {"bk_target_ip": node.split("|")[0], "bk_target_cloud_id": node.split("|")[1]}
                        for node in self.static_nodes
                    ],
                }
            )

        if not self.dynamic_nodes:
            return

        # 动态节点判断是否是策略目标的子节点
        sub_nodes: List[Dict] = []
        for current_node, dynamic_node in product(current_target["value"], self.dynamic_nodes):
            current_node = f"{current_node['bk_obj_id']}|{current_node['bk_inst_id']}"
            if self.is_parent(current_node, dynamic_node):
                bk_obj_id, bk_inst_id = dynamic_node.split("|")
                sub_nodes.append({"bk_obj_id": bk_obj_id, "bk_inst_id": bk_inst_id})

        if sub_nodes:
            current_strategy["item_list"][0]["target"][0].append(
                {"field": current_target["field"], "method": "neq", "value": sub_nodes}
            )


def main():
    StrategyCacheManager.refresh()
