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
conf.web.development.enterprise
===========================
"""


from conf.web.development.default_settings import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

#
# Main
#

INSTALLED_APPS += ()

# Keep 'DATABASES' empty in this file,
# configurate it in your own local_settings.py instead.
DATABASES = {}

#
# Redis
# configurate it in your own local_settings.py instead.
REDIS_HOST = ""
REDIS_PORT = ""
REDIS_PASSWORD = ""
REDIS_DB = 0

#
# Logging
#

LOGGING = get_logging_settings("DEBUG")

#
# FIXTURES (初始数据)
#
FIXTURE_FILE = os.path.join(PROJECT_DIR, PROJECT_MODULE_NAME, "fixtures/t_fixtures/initial_data.json")


BK_URL = os.environ.get("BK_URL", "%s/console" % BK_PAAS_HOST)
REMOTE_STATIC_URL = os.environ.get("BK_REMOTE_STATIC_URL", "http://o.bkclouds.cc/static_api/")
