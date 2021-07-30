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

from bkmonitor.utils.db import JsonField
from monitor_web.models import OperateRecordModelBase


class QueryHistory(OperateRecordModelBase):
    """
    查询历史
    """

    bk_biz_id = models.IntegerField(_("业务ID"), db_index=True)
    name = models.CharField(_("名称"), max_length=32)
    config = JsonField(_("查询配置"))

    class Meta:
        verbose_name = "查询历史"
        verbose_name_plural = verbose_name
