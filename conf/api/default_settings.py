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
conf.api.default_settings
============================
"""


import os

from conf.web.default_settings import *  # noqa
from conf.worker.default_settings import *  # noqa

SECRET_KEY = os.environ.get("APP_TOKEN")
MIGRATE_MONITOR_API = False

INSTALLED_APPS = (
    "legacy",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "blueapps.account",
    "bkmonitor",
    "monitor",
    "monitor_api",
    "monitor_web",
    "kernel_api",
    "metadata",
    "core.drf_resource",
    "djcelery",
)


# api not use celery worker
CELERY_ALWAYS_EAGER = True


ROOT_PATH = BASE_DIR  # noqa
LOG_PATH = os.path.join(BASE_DIR, "logs/")  # noqa
BAK_PATH = os.path.join(BASE_DIR, "data/")  # noqa

LOGGER_HANDLERS = ["file", "sentry"]
if os.getenv("LOGGER_WITHOUT_CONSOLE") != "1":  # noqa
    LOGGER_HANDLERS.append("console")
if os.getenv("LOGGER_WITHOUT_REDIS") != "1":  # noqa
    LOGGER_HANDLERS.append("redis")

# LOGGING
LOGGER_LEVEL = "DEBUG"
LOGGER_DEFAULT = {
    "level": LOGGER_LEVEL,
    "propagate": False,
    "handlers": LOGGER_HANDLERS,
}


def get_logging(log_path):
    return {
        "version": 1,
        "loggers": {
            "": {"level": "ERROR", "handlers": LOGGER_HANDLERS},
            "django.request": {"handlers": LOGGER_HANDLERS, "level": "ERROR", "propagate": True},
            "monitor": LOGGER_DEFAULT,
            "monitor_api": LOGGER_DEFAULT,
            "utils": LOGGER_DEFAULT,
            "drf_non_orm": LOGGER_DEFAULT,
            "common": LOGGER_DEFAULT,
            "monitor_adapter": LOGGER_DEFAULT,
            "kernel_api": LOGGER_DEFAULT,
            "project": LOGGER_DEFAULT,
            "bkmonitor": LOGGER_DEFAULT,
            "kernel": LOGGER_DEFAULT,
            "metadata": LOGGER_DEFAULT,
            "sql_parse": LOGGER_DEFAULT,
            "file-only": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["file"]},
            "console-only": {"level": LOGGER_LEVEL, "propagate": False, "handlers": ["console"]},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "level": "DEBUG", "formatter": "standard"},
            "file": {
                "class": "logging.handlers.WatchedFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": log_path,
                "encoding": "utf-8",
            },
            "redis": {"class": "bkmonitor.utils.log.handlers.RedisHandler", "level": "INFO"},
            "sentry": {"class": "bkmonitor.utils.log.handlers.SentryHandler", "level": "ERROR"},
        },
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s %(levelname)-8s %(process)-8d" "%(name)-15s %(filename)20s[%(lineno)03d] %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
    }


LOG_FILE_PATH = os.path.join(LOG_PATH, "kernel_api.log")  # noqa
LOGGING = LOGGER_CONF = get_logging(LOG_FILE_PATH)

CELERY_REDIS_DB = 6

API_TEMPLATE = True
#
# Templates
#
TEMPLATE_CONTEXT_PROCESSORS = (
    # the context to the templates
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.request",
    "django.template.context_processors.csrf",
    "common.context_processors.get_context",  # 自定义模版context，可以在页面中使用STATIC_URL等变量
    "django.template.context_processors.i18n",
)
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "kernel_api/templates"),  # noqa
    os.path.join(BASE_DIR, "bkmonitor/templates"),  # noqa
)
TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": ["django.template.context_processors.i18n"],
            "undefined": DebugUndefined,
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": list(TEMPLATE_DIRS),
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": list(TEMPLATE_CONTEXT_PROCESSORS)},
    },
]

DEFAULT_LOCALE = "zh_Hans"
DEFAULT_TIMEZONE = "Asia/Shanghai"
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)  # noqa

SENTRY_DSN = ""

DATETIME_FORMAT = "Y-m-d H:i:sO"
ROOT_URLCONF = "kernel_api.urls"
ALLOWED_HOSTS = ["*"]
STATIC_URL = "/static/"
MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "blueapps.middleware.request_provider.RequestProvider",
    "bkmonitor.middlewares.request_middlewares.RequestProvider",
    "kernel_api.middlewares.ApiTimeZoneMiddleware",
    "kernel_api.middlewares.ApiLanguageMiddleware",
    "kernel_api.middlewares.authentication.AuthenticationMiddleware",
)

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": ("kernel_api.adapters.ApiRenderer",),
    "DEFAULT_AUTHENTICATION_CLASSES": ("kernel_api.middlewares.authentication.KernelSessionAuthentication",),
    # 'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
    "EXCEPTION_HANDLER": "kernel_api.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "bkmonitor.views.pagination.MonitorAPIPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_PERMISSION_CLASSES": (),
}

RESOURCE_PROXY_TEMPLATE = "{module}.project.{path}"

#
# Authentication & Authorization
#
AUTH_USER_MODEL = "account.User"

AUTHENTICATION_BACKENDS = (
    "kernel_api.middlewares.authentication.AppWhiteListModelBackend",
    "blueapps.account.backends.UserBackend",
)

BACKEND_DATABASE_NAME = "monitor_api"
DATABASE_ROUTERS = [
    "bkmonitor.db_routers.BackendRouter",
]

ALLOW_EXTEND_API = True
APIGW_PUBLIC_KEY = ""
AES_X_KEY_FIELD = "SAAS_SECRET_KEY"

# 特别的AES加密配置信息
SPECIFY_AES_KEY = ""

# 跳过权限中心检查
SKIP_IAM_PERMISSION_CHECK = True

# paas url
PAAS_URL = os.environ.get("BK_PAAS_PUBLIC_URL", "")


# 监控SAAS的HOST
MONITOR_SAAS_URL = PAAS_URL
# 重启服务器时清除缓存
CLEAR_CACHE_ON_RESTART = False

# 聚合网关默认业务ID
AGGREGATION_BIZ_ID = 2
