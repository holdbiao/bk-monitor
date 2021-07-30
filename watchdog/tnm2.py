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
import subprocess

logger = logging.getLogger(__name__)


class TNM2Client(object):

    NUM_ALARM_BIN = "/usr/local/agenttools/agent/agentRepNum"
    STR_ALARM_BIN = "/usr/local/agenttools/agent/agentRepStr"

    def __init__(self, num_attr_id, str_attr_id):
        self.num_attr_id = num_attr_id
        self.str_attr_id = str_attr_id

    def _execute(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.info(p.stdout.read())

    def report_num(self, num):
        cmd = list(map(str, [self.NUM_ALARM_BIN, self.num_attr_id, num]))
        self._execute(cmd)

    def send_message(self, message):
        cmd = list(map(str, [self.STR_ALARM_BIN, self.str_attr_id, message]))
        self._execute(cmd)
