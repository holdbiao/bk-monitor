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
conf.web.production.community
===========================
"""


import os

from conf.web.production.default_settings import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["*"]

DEFAULT_DB_NAME = os.environ.get("DB_NAME")
DEFAULT_DB_USER = os.environ.get("DB_USERNAME")
DEFAULT_DB_PASSWORD = os.environ.get("DB_PASSWORD")
DEFAULT_DB_HOST = os.environ.get("DB_HOST")
DEFAULT_DB_PORT = os.environ.get("DB_PORT")


# 正式环境数据库设置
DATABASES = {
    # default 请不要做修改 ！！！！！！！！！！
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DEFAULT_DB_NAME,
        "USER": DEFAULT_DB_USER,
        "PASSWORD": DEFAULT_DB_PASSWORD,
        "HOST": DEFAULT_DB_HOST,
        "PORT": DEFAULT_DB_PORT,
    },
    # 后台DB实例
    "monitor_api": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "bkmonitorv3_alert",
        "USER": os.environ.get("BKAPP_BACKEND_DB_USERNAME", DEFAULT_DB_USER),
        "PASSWORD": os.environ.get("BKAPP_BACKEND_DB_PASSWORD", DEFAULT_DB_PASSWORD),
        "HOST": os.environ.get("BKAPP_BACKEND_DB_HOST", DEFAULT_DB_HOST),
        "PORT": os.environ.get("BKAPP_BACKEND_DB_PORT", DEFAULT_DB_PORT),
    },
    # 3.1 老数据库，用于数据迁移
    "monitor_saas_3_1": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("BKAPP_OLD_SAAS_DB_NAME", "bk_monitor"),
        "USER": os.environ.get("BKAPP_OLD_SAAS_DB_USERNAME", DEFAULT_DB_USER),
        "PASSWORD": os.environ.get("BKAPP_OLD_SAAS_DB_PASSWORD", DEFAULT_DB_PASSWORD),
        "HOST": os.environ.get("BKAPP_OLD_SAAS_DB_HOST", DEFAULT_DB_HOST),
        "PORT": os.environ.get("BKAPP_OLD_SAAS_DB_PORT", DEFAULT_DB_PORT),
    },
    "monitor_api_3_1": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("BKAPP_OLD_BACKEND_DB_NAME", "bkdata_monitor_alert"),
        "USER": os.environ.get("BKAPP_OLD_BACKEND_DB_USERNAME", DEFAULT_DB_USER),
        "PASSWORD": os.environ.get("BKAPP_OLD_BACKEND_DB_PASSWORD", DEFAULT_DB_PASSWORD),
        "HOST": os.environ.get("BKAPP_OLD_BACKEND_DB_HOST", DEFAULT_DB_HOST),
        "PORT": os.environ.get("BKAPP_OLD_BACKEND_DB_PORT", DEFAULT_DB_PORT),
    },
}

# 节点管理数据库，仅当监控SaaS与节点管理公用DB实例时适用
DATABASES["nodeman"] = {}
DATABASES["nodeman"].update(DATABASES["default"])
DATABASES["nodeman"]["NAME"] = os.environ.get("BKAPP_NODEMAN_DB_NAME", "bk_nodeman")

# Redis 相关配置
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_DB = 0

if "REDIS_HOST" in os.environ and "REDIS_PORT" in os.environ and "REDIS_PASSWORD" in os.environ:
    try:
        importlib.import_module("django_redis")  # noqa
    except ImportError:
        pass
    else:
        CACHES["redis"] = {  # noqa
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:{}@{}:{}/{}".format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT, REDIS_DB),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }

        CACHES["default"] = CACHES["redis"]  # noqa

#
# Logging
#
BK_LOG_DIR = os.environ.get("BK_LOG_DIR", "/data/paas/apps/logs/")
LOGGING_DIR = os.path.join(BK_LOG_DIR, APP_CODE)  # noqa

LOG_LEVEL = os.environ.get("BKAPP_LOG_LEVEL", "DEBUG")
LOGGING = get_logging_settings(LOG_LEVEL, LOGGING_DIR)  # noqa

#
# DataPlatform Settings
#
PROJECT_ID = 3093

#
# FIXTURES (初始数据)
#
FIXTURE_FILE = os.path.join(PROJECT_DIR, PROJECT_MODULE_NAME, "fixtures/o_fixtures/initial_data.json")  # noqa

BK_URL = os.environ.get("BK_URL", "%s/console" % BK_PAAS_HOST)  # noqa
SITE_URL = os.environ.get("BK_SITE_URL", "/o/%s/" % APP_CODE)  # noqa
STATIC_URL = "%sstatic/" % SITE_URL
REMOTE_STATIC_URL = "%sremote/" % STATIC_URL

# 在企业版中启用RIO
if os.environ.get("BKAPP_ENABLE_RIO_IN_ENTERPRISE", False):
    MIDDLEWARE = list(MIDDLEWARE)  # noqa
    index = MIDDLEWARE.index("blueapps.account.middlewares.RioLoginRequiredMiddleware")
    MIDDLEWARE[index] = "blueapps.account.components.rio.middlewares.RioLoginRequiredMiddleware"
    MIDDLEWARE = tuple(MIDDLEWARE)

    AUTHENTICATION_BACKENDS = list(AUTHENTICATION_BACKENDS)  # noqa
    index = AUTHENTICATION_BACKENDS.index("blueapps.account.backends.RioBackend")
    AUTHENTICATION_BACKENDS[index] = "blueapps.account.components.rio.backends.RioBackend"
    AUTHENTICATION_BACKENDS = tuple(AUTHENTICATION_BACKENDS)
