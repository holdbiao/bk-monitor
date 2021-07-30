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


from core.fake_esb_api.register import register


@register
def get_user(params=None, **kwargs):
    pass


@register
def get_all_user(params=None, **kwargs):
    return [
        {
            "username": "admin",
            "qq": "",
            "language": "zh-cn",
            "wx_userid": "",
            "time_zone": "Asia/Shanghai",
            "phone": "11111111111",
            "role": "1",
            "email": "admin@tencent.com",
            "chname": "admin",
        },
        {
            "username": "user1",
            "qq": "",
            "language": "zh-cn",
            "wx_userid": "",
            "time_zone": "Asia/Shanghai",
            "phone": "2222222222",
            "role": "0",
            "email": "user1@tencent.com",
            "chname": "user1",
        },
        {
            "username": "user2",
            "qq": "",
            "language": "zh-cn",
            "wx_userid": "",
            "time_zone": "Asia/Shanghai",
            "phone": "2222222222",
            "role": "0",
            "email": "user2@tencent.com",
            "chname": "user2",
        },
    ]
