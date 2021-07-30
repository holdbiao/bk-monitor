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

from __future__ import absolute_import, print_function, unicode_literals

import math

from django.conf import settings

from bkmonitor.dataflow.node.machine_learning import IntelligentModelDetectNode
from bkmonitor.dataflow.node.processor import AlarmStrategyNode
from bkmonitor.dataflow.node.source import StreamSourceNode
from bkmonitor.dataflow.node.storage import TSpiderStorageNode
from bkmonitor.utils.time_tools import parse_time_compare_abbreviation
from core.drf_resource import api
from bkmonitor.dataflow.task.base import BaseTask


class StrategyIntelligentModelDetectTask(BaseTask):
    """
    监控策略 对接智能检测模型
    """

    FLOW_NAME_KEY = "模型应用"
    DEFAULT_TS_DEPEND = 7 * 86400

    def __init__(
        self,
        strategy_id,
        model_id,
        model_release_id,
        rt_id,
        metric_field,
        agg_interval,
        agg_dimensions,
        strategy_sql,
        sensitivity_config,
        output_table_name="",
    ):
        """
        :param strategy_id: 策略ID
        :param model_id:    模型ID
        :param model_release_id:   模型发布版本（数字id表示）
        :param rt_id:       原始输入表
        :param metric_field:  指标字段
        :param agg_interval:  聚合周期
        :param agg_dimensions:  聚合分组维度
        :param strategy_sql:   直接指定sql语句
        :param sensitivity_config:   模型公共参数：敏感度值
        :param output_table_name:   指定dataflow输出表名
        """
        super(StrategyIntelligentModelDetectTask, self).__init__()

        self.strategy_id = strategy_id
        self.rt_id = rt_id
        self.model_id = model_id
        self.model_release_id = model_release_id

        release_model_info = api.bkdata.get_release_model_info(model_release_id=model_release_id)
        ts_depend = (
            release_model_info["model_config_template"]
            .get("input_standard_config", {})
            .get("ts_depend", self.DEFAULT_TS_DEPEND)
        )
        ts_depend_days = (
            math.ceil(math.fabs(parse_time_compare_abbreviation(ts_depend)) / 86400) + 3
        )  # 历史依赖多增加3天，方便问题排查

        stream_source_node = StreamSourceNode(rt_id)
        strategy_process_node = AlarmStrategyNode(
            strategy_id=strategy_id,
            source_rt_id=rt_id,
            agg_interval=agg_interval,
            sql=strategy_sql,
            parent=stream_source_node,
        )
        strategy_storage_node = TSpiderStorageNode(
            source_rt_id=strategy_process_node.output_table_name,
            storage_expires=ts_depend_days,
            parent=strategy_process_node,
        )

        model_node = IntelligentModelDetectNode(
            source_rt_id=strategy_process_node.output_table_name,
            output_rt_id=output_table_name,
            model_id=self.model_id,
            model_release_id=self.model_release_id,
            sensitivity_config=sensitivity_config,
            metric_field=metric_field,
            agg_dimensions=agg_dimensions,
            time_field=None,
            parent=strategy_process_node,
        )
        storage_node = TSpiderStorageNode(
            source_rt_id=model_node.output_table_name,
            storage_expires=settings.BK_DATA_DATA_EXPIRES_DAYS,
            parent=model_node,
        )

        self.node_list = [stream_source_node, strategy_process_node, strategy_storage_node, model_node, storage_node]

        self.data_flow = None
        self.output_table_name = storage_node.output_table_name

    @property
    def flow_name(self):
        # 模型名称如果有变更，需要同步修改维护dataflow的定时任务逻辑
        return "{} {} {}".format(self.strategy_id, self.FLOW_NAME_KEY, self.rt_id)
