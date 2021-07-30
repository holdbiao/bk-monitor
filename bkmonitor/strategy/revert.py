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
新版多指标策略模型升级回滚脚本
"""
import datetime
from collections import defaultdict
from typing import List

from bkmonitor import models
from bkmonitor.strategy.strategy import StrategyConfig
from bkmonitor.strategy.new_strategy import Strategy
from monitor_web.models import CustomEventGroup, MetricListCache


def clean_strategy_dict(strategy_dict):
    strategy_dict.pop("strategy_id", None)
    strategy_dict.pop("strategy_name", None)
    strategy_dict.pop("update_time", None)
    strategy_dict.pop("update_user", None)
    strategy_dict.pop("create_time", None)
    strategy_dict.pop("create_user", None)
    return strategy_dict


def revert_strategy(update_time: datetime.datetime):
    strategies = models.StrategyModel.objects.only("id", "update_time")
    strategy_ids = {s.id for s in strategies}
    old_strategy_ids = set(models.Strategy.objects.values_list("id", flat=True))

    new_strategy_ids = strategy_ids - old_strategy_ids
    deleted_strategy_ids = old_strategy_ids - strategy_ids
    updated_strategy_ids = [s.id for s in strategies if s.update_time > update_time and s.id not in new_strategy_ids]

    # 批量删除旧策略
    models.Strategy.objects.filter(id__in=deleted_strategy_ids).delete()
    models.Item.objects.filter(strategy_id__in=deleted_strategy_ids).delete()
    models.Action.objects.filter(strategy_id__in=deleted_strategy_ids).delete()
    models.DetectAlgorithm.objects.filter(strategy_id__in=deleted_strategy_ids).delete()

    event_groups = {}
    event_table_id_to_data_id = {}
    event_items = defaultdict(dict)

    for custom_event_item in MetricListCache.objects.filter(
        data_source_label="custom",
        data_type_label="event",
    ).values("metric_field_name", "metric_field", "result_table_id"):
        event_items[custom_event_item["result_table_id"]].update(
            {custom_event_item["metric_field_name"]: custom_event_item["metric_field"]}
        )

    for event_group in CustomEventGroup.objects.values("table_id", "bk_event_group_id", "bk_data_id"):
        event_groups[event_group["table_id"]] = str(event_group["bk_event_group_id"])
        event_groups[event_group["table_id"]] = str(event_group["bk_data_id"])

    new_strategies: List[Strategy] = Strategy.from_models(models.StrategyModel.objects.filter(id__in=new_strategy_ids))
    for strategy in new_strategies:
        strategy_dict = clean_strategy_dict(strategy.to_dict_v1())
        for item in strategy_dict["item_list"]:
            if item["data_source_label"] != "custom" or item["data_type_label"] != "event":
                continue
            item["bk_event_group_id"] = event_groups.get(item["result_table_id"], "0")
            bk_data_id = event_table_id_to_data_id.get(item["result_table_id"], "0")
            item["custom_event_id"] = event_items.get(bk_data_id, {}).get(
                item["extend_fields"]["custom_event_name"], "0"
            )
        StrategyConfig.create(strategy_dict)

    updated_strategies = Strategy.from_models(models.StrategyModel.objects.filter(id__in=updated_strategy_ids))
    for strategy in updated_strategies:
        strategy_dict = clean_strategy_dict(strategy.to_dict_v1())
        for item in strategy_dict["item_list"]:
            if item["data_source_label"] != "custom" or item["data_type_label"] != "event":
                continue
            item["bk_event_group_id"] = event_groups.get(item["result_table_id"], "0")
            item["custom_event_id"] = event_items.get(item["bk_event_group_id"], {}).get(
                item["extend_fields"]["custom_event_name"], "0"
            )

        StrategyConfig(strategy.bk_biz_id, strategy.id).update_strategy(strategy_dict)
