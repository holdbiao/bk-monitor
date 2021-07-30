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
from functools import lru_cache
from typing import Optional

from django.conf import settings

from core.drf_resource import api


@lru_cache(maxsize=1000)
def get_org_id(bk_biz_id: int) -> Optional[int]:
    """
    获取业务对应的Grafana组织ID
    :param bk_biz_id: 业务
    :return: 组织ID
    """

    result = api.grafana.get_organization_by_name(name=str(bk_biz_id))

    if not result:
        return

    return result["data"]["id"]


def patch_home_panels(home_config):
    panels = [
        {
            "datasource": None,
            "fieldConfig": {"defaults": {"custom": {}}, "overrides": []},
            "gridPos": {"h": 4, "w": 24, "x": 0, "y": 0},
            "id": 2,
            "options": {"content": "<br>\n<br>\n<br>\n<div><H1>Welcome 欢迎使用仪表盘</H1></div>", "mode": "html"},
            "pluginVersion": "7.1.0",
            "targets": [],
            "timeFrom": None,
            "timeShift": None,
            "title": "",
            "transparent": True,
            "type": "text",
        },
        {
            "datasource": None,
            "fieldConfig": {"defaults": {"custom": {}}, "overrides": []},
            "folderId": None,
            "gridPos": {"h": 24, "w": 8, "x": 0, "y": 4},
            "headings": True,
            "id": 7,
            "limit": 15,
            "pluginVersion": "7.2.0-beta1",
            "query": "",
            "recent": False,
            "search": True,
            "starred": False,
            "tags": [],
            "targets": [],
            "timeFrom": None,
            "timeShift": None,
            "title": "所有仪表盘",
            "type": "dashlist",
        },
        {
            "datasource": None,
            "fieldConfig": {"defaults": {"custom": {}}, "overrides": []},
            "gridPos": {"h": 24, "w": 8, "x": 8, "y": 4},
            "headings": True,
            "id": 6,
            "limit": 15,
            "pluginVersion": "7.2.0-beta1",
            "query": "",
            "recent": True,
            "search": False,
            "starred": True,
            "tags": [],
            "targets": [],
            "timeFrom": None,
            "timeShift": None,
            "title": "收藏和最近查看的仪表盘",
            "type": "dashlist",
        },
        {
            "datasource": None,
            "fieldConfig": {"defaults": {"custom": {}}, "overrides": []},
            "gridPos": {"h": 24, "w": 8, "x": 16, "y": 4},
            "id": 3,
            "options": {
                "content": f"""
<br>
<div>
    <a href="{settings.SITE_URL}grafana/dashboard/new"><H3>还没有仪表盘？快速创建您的仪表盘吧！</H3></a>
</div>
<br>
<div>
    <a href="{settings.SITE_URL}grafana/dashboards/folder/new"><H3>为方便管理仪表盘，可以创建目录。</H3></a>
</div>
<br>
<div>
    <a href="{settings.SITE_URL}grafana/dashboard/import"><H3>本地有仪表盘配置文件，直接导入即可。</H3></a>
</div>
<br><br><br><br>
<div>
    <a href="{settings.BK_DOCS_SITE_URL}markdown/监控平台/产品白皮书/functions/report/new_dashboard.md" target="_blank">
        更多使用方法查看产品文档
    </a>
</div>
                """,
                "mode": "html",
            },
            "pluginVersion": "7.1.0",
            "targets": [],
            "timeFrom": None,
            "timeShift": None,
            "title": "仪表盘使用指引",
            "type": "text",
        },
    ]

    home_config["dashboard"]["panels"] = panels
    return home_config
