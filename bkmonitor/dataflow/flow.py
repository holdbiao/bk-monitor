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

import logging

from django.conf import settings

from constants.dataflow import ConsumingMode
from core.errors.bkmonitor.dataflow import (
    DataFlowNotExists,
    DataFlowStartFailed,
)
from core.drf_resource import api


logger = logging.getLogger("bkmonitor.dataflow")


class DataFlow(object):
    """
    对应计算平台的dataflow
    """

    class Status(object):
        NoStart = "no-start"
        Running = "running"
        Starting = "starting"
        Failure = "failure"
        Stopping = "stopping"
        Warning = "warning"

    def __init__(self, flow_id, project_id=None, flow_name=None):
        """
        根据flow_id，从计算平台请求flow中的节点信息，并初始化自身(懒加载模式)
        :param flow_id:
        """
        self.flow_id = flow_id

        self.flow_name = flow_name
        self.project_id = project_id or settings.BK_DATA_PROJECT_ID

        self._flow_info = None
        self._flow_graph_info = None

        self.is_modified = False

    @property
    def flow_info(self):
        if self._flow_info is None:
            self._flow_info = api.bkdata.get_data_flow(flow_id=self.flow_id)
        return self._flow_info

    @property
    def flow_graph_info(self):
        if self._flow_graph_info is None:
            result = api.bkdata.get_data_flow_graph(flow_id=self.flow_id)
            self._flow_graph_info = result.get("nodes", [])
        return self._flow_graph_info

    @classmethod
    def from_bkdata_by_flow_id(cls, flow_id):
        """
        从bkdata接口查询到flow相关信息，然后初始化一个DataFlow对象返回
        :param flow_id:
        """
        result = api.bkdata.get_data_flow(flow_id=flow_id)
        if result:
            return cls(flow_id, project_id=result["project_id"], flow_name=result["flow_name"])
        raise DataFlowNotExists(flow_id=flow_id)

    @classmethod
    def from_bkdata_by_flow_name(cls, flow_name):
        """
        从bkdata接口查询到flow相关信息，根据flow_name，然后初始化一个DataFlow对象返回
        :param flow_name:
        """
        result = api.bkdata.get_data_flow_list(project_id=settings.BK_DATA_PROJECT_ID)
        if not result:
            raise DataFlowNotExists()

        for flow in result:
            name = flow.get("flow_name", "")
            if flow_name == name:
                return cls(flow["flow_id"], project_id=flow["project_id"], flow_name=flow_name)

        raise DataFlowNotExists()

    @classmethod
    def create_flow(cls, flow_name):
        result = api.bkdata.create_data_flow(project_id=settings.BK_DATA_PROJECT_ID, flow_name=flow_name)
        return cls(flow_id=result["flow_id"], project_id=result["project_id"], flow_name=result["flow_name"])

    @classmethod
    def ensure_data_flow_exists(cls, flow_id=None, flow_name=None):
        try:
            if flow_id:
                return DataFlow.from_bkdata_by_flow_id(flow_id)
            elif flow_name:
                return DataFlow.from_bkdata_by_flow_name(flow_name)
        except DataFlowNotExists:
            if flow_name:
                return DataFlow.create_flow(flow_name=flow_name)

    def start(self, consuming_mode=None):
        if not self.is_modified:
            logger.info("dataflow({}({})) has not changed.".format(self.flow_name, self.flow_id))
            return

        try:
            if self.flow_info["status"] == self.Status.NoStart:
                # 新启动，从尾部开始处理
                consuming_mode = consuming_mode or ConsumingMode.Tail
                result = api.bkdata.start_data_flow(
                    flow_id=self.flow_id, consuming_mode=consuming_mode, cluster_group="default"
                )
            else:
                # 重启，从上次停止位置开始处理
                consuming_mode = consuming_mode or ConsumingMode.Current
                result = api.bkdata.restart_data_flow(
                    flow_id=self.flow_id, consuming_mode=consuming_mode, cluster_group="default"
                )
        except Exception:  # noqa
            logger.exception("start/restart dataflow({}({})) failed".format(self.flow_name, self.flow_id))
            raise DataFlowStartFailed(flow_id=self.flow_id, flow_name=self.flow_name)
        logger.info("start/restart dataflow({}({})) success, result:({})".format(self.flow_name, self.flow_id, result))

    def stop(self):
        api.bkdata.stop_data_flow(flow_id=self.flow_id)

    def add_node(self, node):
        for graph_node in self.flow_graph_info:
            node_config = graph_node.get("node_config", {})
            # 判断是否为同样的节点(只判断关键信息，比如输入和输出表ID等信息)
            if node == node_config:
                node_id = graph_node.get("node_id")
                # 如果部分信息不一样，则做一遍更新
                if node.need_update(node_config):
                    node.update(self.flow_id, node_id)
                    self.is_modified = True
                node.node_id = node_id
                return

        node.create(self.flow_id)
        self.is_modified = True
