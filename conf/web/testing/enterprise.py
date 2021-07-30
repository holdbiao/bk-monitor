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
conf.web.testing.enterprise
========================
"""


from conf.web.testing.default_settings import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    # default 请不要做修改 ！！！！！！！！！！
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USERNAME"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    },
    "monitor_api": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "bkdata_monitor_alert",
        "USER": os.environ.get("DB_USERNAME"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    },
}

# Redis 相关配置
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_DB = 0

if "REDIS_HOST" in os.environ and "REDIS_PORT" in os.environ and "REDIS_PASSWORD" in os.environ:
    try:
        importlib.import_module("django_redis")
    except ImportError:
        pass
    else:
        CACHES["redis"] = {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:{}@{}:{}/{}".format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT, REDIS_DB),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }

        CACHES["default"] = CACHES["redis"]

#
# Logging
#
BK_LOG_DIR = os.environ.get("BK_LOG_DIR", "/data/paas/apps/logs/")
LOGGING_DIR = os.path.join(BK_LOG_DIR, APP_CODE)

LOG_LEVEL = os.environ.get("BKAPP_LOG_LEVEL", "INFO")
LOGGING = get_logging_settings(LOG_LEVEL, LOGGING_DIR)

#
# FIXTURES (初始数据)
#
FIXTURE_FILE = os.path.join(PROJECT_DIR, PROJECT_MODULE_NAME, "fixtures/t_fixtures/initial_data.json")

BK_URL = os.environ.get("BK_URL", "%s/console" % BK_PAAS_HOST)
SITE_URL = os.environ.get("BK_SITE_URL", "/t/%s/" % APP_CODE)
STATIC_URL = "%sstatic/" % SITE_URL
REMOTE_STATIC_URL = os.environ.get("BK_REMOTE_STATIC_URL", "http://%s/static_api/" % BK_PAAS_HOST)
