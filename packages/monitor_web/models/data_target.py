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


from django.db import models
from django.utils.translation import ugettext_lazy as _

from constants.strategy import DATA_TARGET_MAP, DataTarget


class DataTargetMapping(models.Model):

    # 数据来源标签，例如：计算平台(bk_data)，监控采集(bk_monitor)
    data_source_label = models.CharField(verbose_name=_("数据来源标签"), max_length=255)

    # 数据类型标签，例如：时序数据(time_series)，事件数据(event)，日志数据(log)
    data_type_label = models.CharField(verbose_name=_("数据类型标签"), max_length=255)

    # 结果表标签，此处记录的是二级标签，对应一级标签将由二级标签推导得到
    result_table_label = models.CharField(verbose_name=_("结果表标签"), max_length=255)

    # 数据目标， 例如：CMDB-服务拓扑(service_target)，CMDB-主机(host_target)
    data_target = models.CharField(verbose_name=_("数据目标"), max_length=255)

    class Meta:
        unique_together = (("data_source_label", "data_type_label", "result_table_label"),)

    def get_data_target(self, result_table_label, data_source_label, data_type_label):
        data_target = DATA_TARGET_MAP.get(result_table_label, {}).get(data_source_label, {}).get(data_type_label)
        if data_target:
            return data_target
        else:
            try:
                return DataTargetMapping.objects.get(
                    result_table_label=result_table_label,
                    data_source_label=data_source_label,
                    data_type_label=data_type_label,
                ).data_target
            except DataTargetMapping.DoesNotExist:
                return DataTarget.NONE_TARGET
