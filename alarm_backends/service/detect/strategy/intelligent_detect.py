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
IntelligentDetect：智能异常检测算法基于计算平台的计算结果，再基于结果表的is_anomaly{1,2,3}来进行判断。
"""

from django.utils.translation import ugettext as _

from alarm_backends.service.detect.strategy import BasicAlgorithmsCollection, ExprDetectAlgorithms


class DetectDirect(object):
    CEIL = "ceil"
    FLOOR = "floor"
    ALL = "all"


class IntelligentDetect(BasicAlgorithmsCollection):
    """
    智能异常检测（动态阈值算法）
    """

    def gen_expr(self):
        sensitivity_value = self.config.get("sensitivity_value", 0)
        anomaly_detect_direct = self.config.get("anomaly_detect_direct", DetectDirect.ALL)
        # 上边界 > 下边界， 如果不满足这个条件，则说明算法未准备就绪，则不做检测。(场景：刚配置的时候，上边界和下边界值都默认为0)
        common_expr = "(upper_bound > lower_bound)"
        if anomaly_detect_direct == DetectDirect.CEIL:
            expr = f"{common_expr} and (data_point.value > upper_bound)"
        elif anomaly_detect_direct == DetectDirect.FLOOR:
            expr = f"{common_expr} and (data_point.value < lower_bound)"
        else:
            expr = f"{common_expr} and (data_point.value > upper_bound or data_point.value < lower_bound)"

        yield ExprDetectAlgorithms(
            expr,
            _("智能异常检测，预期值{{{{{}}}}}~{{{{{}}}}}, 敏感度{}".format("lower_bound", "upper_bound", sensitivity_value)),
        )

    def extra_context(self, context):
        return getattr(context.data_point, "values", {})
