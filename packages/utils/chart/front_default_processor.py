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

from bkmonitor.chart.chart_tools import DefaultProcessor
from core.drf_resource import resource


class FrontDefaultProcessor(DefaultProcessor):
    """
    图表数据处理器  Saas使用
    """

    def _get_desc_by_field(self, field):
        """获取字段中文释义"""
        if not self.result_table_id:
            return field

        return resource.commons.get_desc_by_field(self.result_table_id, field) or field
