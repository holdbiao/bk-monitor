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


from api.gse.default import GetAgentStatus
from core.fake_esb_api.register import register


@register
def get_agent_status(params=None, **kwargs):
    params = params or kwargs
    serializer = GetAgentStatus.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    hosts = params["hosts"]

    result = {}
    for host in hosts:
        host_key = "{bk_cloud_id}:{ip}".format(**host)

        result[host_key] = {
            "ip": host["ip"],
            "bk_cloud_id": host["bk_cloud_id"],
            "bk_agent_alive": get_agent_status.result.get("{ip}:{bk_cloud_id}".format(**host), 1),
        }


get_agent_status.result = {}
