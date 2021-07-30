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

import abc

from django.utils.functional import cached_property

from bkmonitor.dataflow.node.base import Node
from core.drf_resource import api


class MachineLearnNode(Node, abc.ABC):
    pass


###############
#   ModelCal  #
###############
class ModelCalculateNode(MachineLearnNode):
    """
    模型计算节点
    """

    NODE_TYPE = "model_ts_custom"

    def __init__(self, source_rt_id, *args, **kwargs):
        self.source_rt_id = source_rt_id
        self.bk_biz_id, _, self.process_rt_id = source_rt_id.partition("_")
        self.bk_biz_id = int(self.bk_biz_id)

        self.output_rt_id = kwargs.pop("output_rt_id", "")
        _, _, self._process_rt_id = self.output_rt_id.partition("_")

        super(ModelCalculateNode, self).__init__(*args, **kwargs)

    @property
    def name(self):
        return ""

    @property
    @abc.abstractmethod
    def table_name(self):
        """
        输出表名（不带业务ID前缀）
        """
        return self._process_rt_id if self._process_rt_id else self.process_rt_id

    @property
    def output_table_name(self):
        """
        输出表名（带上业务ID前缀）
        """
        return "{}_{}".format(self.bk_biz_id, self.table_name)

    @property
    def config(self):
        return {}


class IntelligentModelDetectNode(ModelCalculateNode):
    """
    内置智能异常检测
    """

    DEFAULT_TIME_FIELD = "timestamp"

    def __init__(
        self,
        source_rt_id,
        model_id,
        model_release_id,
        sensitivity_config,
        metric_field,
        agg_dimensions,
        time_field=None,
        *args,
        **kwargs
    ):
        self.model_id = model_id
        self.model_release_id = model_release_id

        # 对应级别如果未配置，则使用默认值
        self.sensitivity_config = {
            "sensitivity": 0.5,  # 敏感度
            "alert_upward": 1,  # 上升异常
            "alert_down": 1,  # 下降异常
        }
        self.sensitivity_config.update(sensitivity_config)

        self.metric_field = metric_field
        self.time_field = time_field or self.DEFAULT_TIME_FIELD
        self.agg_dimensions = agg_dimensions

        super(IntelligentModelDetectNode, self).__init__(source_rt_id, *args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, dict):
            config = self.config
            if (
                config.get("from_result_table_ids") == other.get("from_result_table_ids")
                and config.get("table_name") == other.get("table_name")
                and config.get("bk_biz_id") == other.get("bk_biz_id")
                and config.get("model_id") == other.get("model_id")
            ):
                return True
        elif isinstance(other, self.__class__):
            return self == other.config
        return False

    @property
    def name(self):
        return "智能异常检测 {}".format(self.model_id)

    @property
    def table_name(self):
        """
        模型输出表名，后缀只取模型ID的最后4个字符
        """
        if self._process_rt_id:
            return self._process_rt_id
        return "{}_{}".format(self.process_rt_id, self.model_id[-4:])

    @cached_property
    def release_model_info(self):
        return api.bkdata.get_release_model_info(model_release_id=self.model_release_id)

    @property
    def model_extra_config(self):
        origin_config = self.release_model_info["model_config_template"]["model_extra_config"]
        new_config = []
        for args in origin_config["predict_args"]:
            config = {}
            config.update(args)
            field_name = args["field_name"]
            config["value"] = self.sensitivity_config.get(field_name, args["value"])
            new_config.append(config)
        return {"predict_args": new_config}

    @property
    def input_config(self):
        return {
            "input_node": {
                "group_serving": True,
                "serving_fields_mapping": {"value": self.metric_field, "timestamp": self.time_field},
                "group_serving_enable": True,
                "input_result_table": self.source_rt_id,
                "input_fields": [],
                "group_fields": self.agg_dimensions,
                "group_columns": [],
            }
        }

    @property
    def output_config(self):
        output_fields = self.release_model_info["model_config_template"]["output_standard_config"]["fields"]
        return {
            "output_node": {
                "table_name": self.table_name,
                "table_zh_name": self.table_name,
                "table_alias": self.table_name,
                "output_fields": output_fields,
            }
        }

    @property
    def schedule_config(self):
        # 运行配置
        return {
            "training_scheduler_params": None,
            "serving_scheduler_params": {
                "recovery": {"enable": False, "interval_time": "5m", "retry_times": 1},
                "data_period": 1,
                "data_period_unit": "day",
                "period": 1,
                "fixed_delay": 1,
                "first_run_time": "",
                "dependency_rule": "all_finished",
                "period_unit": "day",
            },
        }

    @property
    def config(self):
        return {
            "from_result_table_ids": [self.source_rt_id],
            "name": self.name,
            "bk_biz_id": self.bk_biz_id,
            "model_id": self.release_model_info["model_id"],
            "model_extra_config": self.model_extra_config,
            "schedule_config": self.schedule_config,
            "input_config": self.input_config,
            "output_config": self.output_config,
            "table_name": self.table_name,
            "output_name": self.table_name,
            "serving_mode": "realtime",
            "model_release_id": self.model_release_id,
            "sample_feedback_config": {},
            "upgrade_config": {},
        }


class IntelligentPredictionNode(ModelCalculateNode):
    """
    内置智能预测
    """

    @property
    def table_name(self):
        if self._process_rt_id:
            return self._process_rt_id
        return ""
