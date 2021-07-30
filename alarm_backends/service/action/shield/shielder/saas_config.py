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


from alarm_backends.core.cache.shield import ShieldCacheManager
from alarm_backends.service.action.shield.shield_obj import ShieldObj
from bkmonitor.utils import extended_json
from constants.shield import ShieldType

from .base import BaseShielder


class SaaSConfigShielder(BaseShielder):
    """
    监控SaaS配置的屏蔽
    """

    type = ShieldType.SAAS_CONFIG

    def __init__(self, event):
        super(SaaSConfigShielder, self).__init__(event)
        self.configs = ShieldCacheManager.get_shields_by_biz_id(self.event.bk_biz_id)

        self.shield_objs = []
        for config in self.configs:
            self.shield_objs.append(ShieldObj(config))

    def is_matched(self):
        # 1. 循环判断告警是否匹配每一条配置信息
        for shield_obj in self.shield_objs:
            # 2. 如果匹配上某一条告警，则说明匹配，返回true
            if shield_obj.is_match(self.event):
                self.detail = extended_json.dumps(shield_obj.config)
                return True

        # 3. 告警配置匹配失败，返回false
        return False
