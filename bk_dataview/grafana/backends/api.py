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

from .. import client
from . import BaseHandler

_ORG_DATASOURCES_CACHE = {}

logger = logging.getLogger(__name__)


class APIHandler(BaseHandler):
    def handle_user(self, request, username: str):
        pass

    def handle_org(self, request, org_name: str, username: str):
        pass

    def handle_datasources(self, request, org_name: str, org_id: int, ds_list: list):
        """API不能批量处理多个数据源"""
        _ORG_DATASOURCES_CACHE.setdefault(org_name, {})

        for ds in ds_list:
            if ds.name in _ORG_DATASOURCES_CACHE[org_name]:
                continue

            resp = client.get_datasource(org_id, ds.name)
            if resp.status_code == 200:
                result = resp.json()
                ds.version = result["version"] + 1
                resp = client.update_datasource(org_id, result["id"], ds)
                if resp.status_code == 200:
                    _ORG_DATASOURCES_CACHE[org_name][ds.name] = ds
                    logger.info("update provision datasource success, %s", resp)
                    return

            if resp.status_code == 404:
                resp = client.create_datasource(org_id, ds)
                # 412 code 代表已经存在
                if resp.status_code == 200:
                    _ORG_DATASOURCES_CACHE[org_name][ds.name] = ds

                logger.info("create provision datasource success, %s", resp)

    def handle_dashboards(self, request, org_name: str, org_id: int, db_list):
        pass
