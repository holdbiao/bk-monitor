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

from monitor_web.function_switch.constants import PLUGIN_FUNCTIONS


class PluginFunction(models.Model):

    function_id = models.CharField(_("功能ID"), choices=list(PLUGIN_FUNCTIONS.keys()), max_length=32)
    is_enable = models.BooleanField(_("是否启用"), default=False)
    bk_biz_id = models.IntegerField(_("业务ID"))
    subscription_id = models.IntegerField(_("订阅ID"), null=True, blank=True)

    class Meta:
        unique_together = ("function_id", "bk_biz_id")

    @classmethod
    def list_functions(cls, bk_biz_id):
        """
        获取功能列表，如果没有，则进行初始化
        """
        function_list = []
        for function_id in PLUGIN_FUNCTIONS:
            function, is_create = cls.objects.get_or_create(function_id=function_id, bk_biz_id=bk_biz_id)
            function_list.append(function)
        return function_list

    def get_function_info(self):
        if self.function_id not in PLUGIN_FUNCTIONS:
            raise ValueError(_("功能ID ({}) 对应的信息不存在").format(self.function_id))
        return PLUGIN_FUNCTIONS[self.function_id]

    @property
    def display_name(self):
        return self.get_function_info()["display_name"]

    @property
    def plugin_id(self):
        return self.get_function_info()["plugin_id"]
