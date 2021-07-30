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
conf.web.default_settings
=========================
"""


import importlib
import re
import sys
import os
import time

import six

from conf.default_settings import *  # noqa
from conf.web.sentry import SENTRY_SUPPORT

APP_CODE = None

# load platform config
BKAPP_DEPLOY_PLATFORM = os.environ.get("BKAPP_DEPLOY_PLATFORM")
if BKAPP_DEPLOY_PLATFORM is None:
    try:
        local_module = __import__("local_settings", globals(), locals(), ["*"])
        BKAPP_DEPLOY_PLATFORM = getattr(local_module, "BKAPP_DEPLOY_PLATFORM")
    except ImportError:
        pass
    BKAPP_DEPLOY_PLATFORM = BKAPP_DEPLOY_PLATFORM or "ieod"

_platform_module = __import__("conf.platform.%s" % BKAPP_DEPLOY_PLATFORM, globals(), locals(), ["*"])

for _setting in dir(_platform_module):
    locals()[_setting] = getattr(_platform_module, _setting)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ROOT_URLCONF = "urls"

SITE_ID = 1

#
# APP 运行环境配置信息
#
WSGI_ENV = os.environ.get("DJANGO_CONF_MODULE", "") or os.environ.get("BK_ENV", "")
# 运行模式， DEVELOP(开发模式)， TEST(测试模式)， PRODUCT(正式产品模式)
RUN_MODE = "DEVELOP"  # DEVELOP TEST PRODUCT
if WSGI_ENV.endswith("production"):
    RUN_MODE = "PRODUCT"
    DEBUG = False
elif WSGI_ENV.endswith("testing"):
    RUN_MODE = "TEST"
    DEBUG = False
else:
    RUN_MODE = "DEVELOP"
    DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR, PROJECT_MODULE_NAME = os.path.split(PROJECT_ROOT)
PYTHON_BIN = os.path.dirname(sys.executable)
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media/')
STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, "static"),)

#
# Internationalization and localization
#

# 语言相关
LANGUAGE_CODE = "zh-hans"
LOCALE_PATHS = (os.path.join(PROJECT_ROOT, "locale"),)
LANGUAGES = (("en", "English"), ("zh-hans", "简体中文"))

LANGUAGE_SESSION_KEY = "blueking_language"
LANGUAGE_COOKIE_NAME = "blueking_language"

# 时区相关
TIME_ZONE = "Asia/Shanghai"
# TIME_ZONE = 'Etc/GMT%+d' % (
#     (time.altzone if time.daylight else time.timezone) / 3600
# )
TIMEZONE_SESSION_KEY = "blueking_timezone"

#
# Inherit from environment variables
#

# fmt: off
for k, v in six.iteritems(os.environ):
    for prefix in ("BK_", "BKAPP_"):
        k = k.upper()
        if k.startswith(prefix) and k[len(prefix):]:
            locals()[k[len(prefix):]] = v
# fmt: on

STATIC_VERSION = time.time()
STATIC_URL = "/static/%s/" % (APP_CODE)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa
SITE_URL = os.environ.get("BK_SITE_URL", "/")

#
# Main
#

INSTALLED_APPS = locals().get("INSTALLED_APPS", tuple())
INSTALLED_APPS += (
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
    "healthz",
    "monitor",
    "monitor_api",
    "monitor_web",
    "weixin.core",
    "weixin",
    "core.drf_resource",
    "version_log",
    "iam.contrib.iam_migration",
)

MIDDLEWARE = (
    "blueapps.middleware.request_provider.RequestProvider",
    "bkmonitor.middlewares.request_middlewares.RequestProvider",
    # 'response_tracker.middleware.ResponseTrackerMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "weixin.core.middlewares.WeixinProxyPatchMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    # Auth middleware
    "weixin.core.middlewares.WeixinAuthenticationMiddleware",
    "weixin.core.middlewares.WeixinLoginMiddleware",
    "blueapps.account.middlewares.RioLoginRequiredMiddleware",
    "blueapps.account.middlewares.LoginRequiredMiddleware",
    "common.middlewares.CheckXssMiddleware",
    "common.middlewares.TimeZoneMiddleware",
    "common.middlewares.ActiveBusinessMiddleware",
    "common.middlewares.RecordLoginUserMiddleware",
    "version_log.middleware.VersionLogMiddleware",
    "monitor_api.middlewares.MonitorAPIMiddleware",
)

PAAS_V3 = False

# v3 support
if "BKPAAS_SUB_PATH" in os.environ:
    # SITE_URL = os.getenv('BKPAAS_SUB_PATH')
    STATIC_URL = "/static/"

    # About whitenoise
    WHITENOISE_STATIC_PREFIX = "/static/"

    # 蓝鲸静态资源服务
    MIDDLEWARE += ("whitenoise.middleware.WhiteNoiseMiddleware",)

    PAAS_V3 = True

    # sentry
    SENTRY_DSN = os.environ.get("SENTRY_DSN")  # noqa
    if SENTRY_DSN:
        INSTALLED_APPS += ("raven.contrib.django.raven_compat",)
        RAVEN_CONFIG = {
            "dsn": SENTRY_DSN,
        }

    # apm
    APM_ID = os.environ.get("APM_ID")
    APM_TOKEN = os.environ.get("APM_TOKEN")
    if APM_ID and APM_TOKEN:
        INSTALLED_APPS += ("ddtrace.contrib.django",)
        DATADOG_TRACE = {
            "TAGS": {"env": os.getenv("BKPAAS_ENVIRONMENT", "dev"), "apm_id": APM_ID, "apm_token": APM_TOKEN},
        }
        # requests for APIGateway/ESB
        # remove pymysql while Django Defaultdb has been traced already
        try:
            import requests  # noqa
            from ddtrace import patch

            patch(requests=True, pymysql=False)
        except Exception as e:
            print("patch fail for requests and pymysql: %s" % e)

        # rewrite RUN_MODE with v3 env
        RUN_MODE = {"dev": "DEVELOP", "stag": "TEST", "prod": "PRODUCT"}.get(
            os.environ.get("BKPAAS_ENVIRONMENT", "dev")
        )

SILENCED_SYSTEM_CHECKS = ["1_8.W001", "fields.W161", "fields.W122"]

#
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
#
# 数据库的配置信息
APP_PWD = os.environ.get("BK_APP_PWD", "")
DB_HOST = os.environ.get("BK_DB_HOST", "")
DB_PORT = os.environ.get("BK_DB_PORT", "")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": APP_CODE,
        "USER": APP_CODE,
        "PASSWORD": APP_PWD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

DATABASE_ROUTERS = ("bkmonitor.db_routers.BackendRouter",)

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

# mako template dir(render_mako settings)
MAKO_TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
MAKO_TEMPLATE_MODULE_DIR = os.path.join(PROJECT_DIR, "templates_module", APP_CODE)
if RUN_MODE != "DEVELOP":
    MAKO_TEMPLATE_MODULE_DIR = os.path.join(PROJECT_ROOT, "templates_module", APP_CODE)

# django template dir(support mako)
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "static"),
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PROJECT_ROOT, "templates", "adapter", BKAPP_DEPLOY_PLATFORM),
)

TEMPLATES = [
    {
        "BACKEND": "monitor_web.core.template.backends.mako.MakoTemplates",
        "DIRS": TEMPLATE_DIRS,
        "OPTIONS": {"context_processors": list(TEMPLATE_CONTEXT_PROCESSORS), "default_filters": ["h"]},
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": list(TEMPLATE_DIRS),
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": list(TEMPLATE_CONTEXT_PROCESSORS)},
    },
]

#
# Cache
#

CACHES = {
    "db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 100000, "CULL_FREQUENCY": 10},
    },
    "login_db": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "account_cache"},
    "dummy": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "locmem": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
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
            "LOCATION": "redis://:{}@{}:{}/0".format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            },
        }

if "redis" in CACHES:
    CACHES["default"] = CACHES["redis"]
else:
    CACHES["default"] = CACHES["db"]

#
# Cookies & Sessions
#

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

if "SITE_URL" in locals():
    SESSION_COOKIE_PATH = locals()["SITE_URL"]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = APP_CODE + "_sessionid"

#
# Authentication & Authorization
#
AUTH_USER_MODEL = "account.User"

AUTHENTICATION_BACKENDS = (
    "blueapps.account.backends.RioBackend",
    "blueapps.account.backends.UserBackend",
)

#
# Logging
#

if "LOGGING_DIR" not in locals():
    LOGGING_DIR = os.path.join(BASE_DIR, "var/log")  # noqa: F405

if not os.path.exists(LOGGING_DIR):
    try:
        os.makedirs(LOGGING_DIR)
    except OSError as e:
        import errno

        if e.errno == errno.EEXIST and os.path.isdir(LOGGING_DIR):
            pass
        else:
            raise


def get_logging_settings(loglevel="WARNING", logdir=LOGGING_DIR):
    # 自动建立日志目录
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except Exception:
            pass

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(levelname)s %(message)s \n"},
            "verbose": {
                "format": (
                    "%(levelname)s [%(asctime)s] %(pathname)s "
                    "%(lineno)d %(funcName)s %(process)d %(thread)d "
                    "\n \t %(message)s \n"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "component": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(logdir, "component.log"),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
            "mail_admins": {"level": "ERROR", "class": "django.utils.log.AdminEmailHandler"},
            "null": {"level": "DEBUG", "class": "logging.NullHandler"},
            "root": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(logdir, "%s.log" % APP_CODE),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "wb_mysql": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(logdir, "wb_mysql.log"),
                "maxBytes": 1024 * 1024 * 50,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "celery": {"handlers": ["null"], "level": "WARNING", "propagate": True},
            "django": {"handlers": ["null"], "level": "INFO", "propagate": True},
            "django.db.backends": {"handlers": ["wb_mysql"], "level": "DEBUG", "propagate": True},
            "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": True},
            "monitor_web": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "monitor_api": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "utils": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "core": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "common": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "monitor_adapter": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "root": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "account": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "bkmonitor": {"handlers": ["root"], "level": loglevel, "propagate": True},
            "metadata": {"handlers": ["root"], "level": loglevel, "propagate": True},
        },
    }


#
# CELERY 配置
#
IS_USE_CELERY = True  # APP是否使用celery
if IS_USE_CELERY:
    try:
        import djcelery

        INSTALLED_APPS += ("djcelery",)  # djcelery
        djcelery.setup_loader()
        # CELERY_ENABLE_UTC = False
        # CELERY_IMPORTS = ()
        CELERYBEAT_SCHEDULER = "monitor.schedulers.MonitorDatabaseScheduler"
        if "celery" in sys.argv:
            DEBUG = False

        from celery.schedules import crontab

        CELERYBEAT_SCHEDULE = {
            "monitor_web.tasks.update_config_status": {
                "task": "monitor_web.tasks.update_config_status",
                "schedule": crontab(),
                "enabled": True,
            },
            "monitor_web.tasks.update_config_instance_count": {
                "task": "monitor_web.tasks.update_config_instance_count",
                "schedule": crontab(minute=0),  # todo 该任务的周期需建议和节点管理的自动执行的周期保持一致
                "enabled": False,
            },
            "monitor_web.tasks.update_metric_list": {
                "task": "monitor_web.tasks.update_metric_list",
                "schedule": crontab(minute="*/5"),
                "enabled": True,
            },
            "monitor_web.tasks.update_aiops_dataflow_status": {
                "task": "monitor_web.tasks.update_aiops_dataflow_status",
                "schedule": crontab(minute="*/10"),
                "enabled": True,
            },
        }

        BROKER_URL = os.environ.get("BK_BROKER_URL", "amqp://guest:guest@127.0.0.1:5672/")

        CELERY_RESULT_BACKEND = "djcelery.backends.database:DatabaseBackend"

        if RUN_MODE == "DEVELOP":
            from celery.signals import worker_process_init

            @worker_process_init.connect
            def configure_workers(*args, **kwargs):
                import django

                django.setup()

    except Exception:
        pass

#
# Django Rest Framework Settings
#

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": ("monitor_api.renderers.MonitorJSONRenderer",),
    # 'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
    "EXCEPTION_HANDLER": "core.drf_resource.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "monitor_api.pagination.MonitorAPIPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_PERMISSION_CLASSES": ("monitor_web.permissions.BusinessViewPermission",),
}

#
# OperateRecord
#
OPERATE_RECORD_CONFIG = (
    "DashboardMenu",
    "DashboardView",
    "MonitorSource",
    # 'MonitorItem',
    "DetectAlgorithmConfig",
    "AlarmSource",
    "ShieldConfig",
    "RolePermission",
    "NoticeGroup",
    "DataCollector",
    "DataGenerateConfig",
    "ScenarioMenu",
    "MonitorLocation",
    "NoticeConfig",
    "ConvergeConfig",
    "ExporterComponent",
    "UptimeCheckNode",
    "UptimeCheckTask",
    "LogCollector",
    "ShellCollectorConfig",
    "ComponentInstance",
    # API
    "ShellCollectorDepositTask",
    "ExporterDepositTask",
)

#
# MonitorAPI Settings
#

MONITOR_API_MODELS = (
    # ('app_label.model_name', read_only),
    # Monitor Related Read-only Models
    ("bkmonitor.BaseAlarm", True),
    ("bkmonitor.SnapshotHostIndex", True),
    ("monitor.RolePermission", False),
    # SaaS Models
    ("monitor.IndexColorConf", True),
    # 配置相关
    ("monitor.UserConfig", False),
    ("monitor.ApplicationConfig", False),
    ("monitor.GlobalConfig", True),
    ("monitor.OperateRecord", True),
    ("monitor.MonitorLocation", False),
)

###############################################################################

NORMAL_TRT_TYPE = 7

# 虚拟结果表的类型(trt_type)编号
VIRTUAL_TRT_TYPE = 11

RE_MOBILE = re.compile(r"Mobile|Android|iPhone|iPad|iPod", re.IGNORECASE)
RE_WECHAT = re.compile(r"MicroMessenger", re.IGNORECASE)

# 水印字体素材路径
SIGNATURE_FONT_PATH = os.path.join(PROJECT_ROOT, "static", "font", "arial.ttf")

# 重启服务器时清除缓存
CLEAR_CACHE_ON_RESTART = False

# csrf token name
CSRF_COOKIE_NAME = "%s_monitor_csrftoken" % BKAPP_DEPLOY_PLATFORM

# 主机任务状态码: 1.Agent异常; 3.上次已成功; 5.等待执行; 7.正在执行;
# 9.执行成功; 11.任务失败; 12.任务下发失败; 13.任务超时; 15.任务日志错误;
# 101.脚本执行失败; 102.脚本执行超时; 103.脚本执行被终止; 104.脚本返回码非零;
# 202.文件传输失败; 203.源文件不存在; 310.Agent异常; 311.用户名不存在;
# 320.文件获取失败; 321.文件超出限制; 329.文件传输错误; 399.任务执行出错
IP_STATUS_SUCCESS = 9
IP_STATUS_WAITING = 5

# 脚本类型：1(shell脚本)、2(bat脚本)、3(perl脚本)、4(python脚本)、5(Powershell脚本)
SCRIPT_TYPE_SHELL = 1
SCRIPT_TYPE_BAT = 2

# 操作类型，可选值：0:启动进程(start);
# 1:停止进程(stop); 2:进程状态查询; 3:注册托管进程; 4:取消托管进程;
# 7:重启进程(restart); 8:重新加载进程(reload); 9:杀死进程(kill)
PROC_OP_TYPE_START = 0
PROC_OP_TYPE_STOP = 1
PROC_OP_TYPE_CHECK = 2
PROC_OP_TYPE_REGISTER = 3
PROC_OP_TYPE_UNREGISTER = 4
PROC_OP_TYPE_RESTART = 7
PROC_OP_TYPE_RELOAD = 8

# 进程返回error_code
PROC_NON_EXIST = 829

# 进程托管类型，0:周期执行进程，1:常驻进程，2:单次执行进程。默认0
PROC_RUN_TYPE_CYCLE = 0
PROC_RUN_TYPE_PERMANENT = 1

# 任务执行状态
# 115表示任务正在执行
GSE_TASK_SUCCESS = 0
GSE_TASK_RUNNING = 115

# 采集器资源消耗
COLLECTOR_DEFAULT_CPU_LIMIT = 30
COLLECTOR_DEFAULT_MEM_LIMIT = 10

# 自定义上报服务器IP
CUSTOM_REPORT_DEFAULT_PROXY_IP = []
CUSTOM_REPORT_DEFAULT_PROXY_DOMAIN = []

# bk_monitor_proxy 自定义上报服务监听的端口
BK_MONITOR_PROXY_LISTEN_PORT = 10205

# 文档Host
DOC_HOST = "http://docs.bk.tencent.com/"

# 作业平台

JOB_HOST = "https://jobee-dev.bktencent.com/"

MIGRATE_MONITOR_API = True

# 不同OS对应的exporter文件名
EXPORTER_FILENAME_OS_MAPPING = {
    "linux": "exporter-linux",
    "windows": "exporter-windows.exe",
    "aix": "exporter-aix",
}

OS_TYPE_NAME_DICT = {1: "linux", 2: "windows", 3: "aix"}


# sentry
def get_saas_version():
    version = ""
    try:
        # only for packaged by ci
        with open(os.path.join(BASE_DIR, "release.md")) as fd:  # noqa
            version = fd.readline()
    except Exception:
        pass
    if version.startswith("#"):
        return ""
    return version.strip("V\n")


# 实际版本号，基于包解析的
REAL_SAAS_VERSION = get_saas_version()

# 高级配置，放在db的
SAAS_VERSION = REAL_SAAS_VERSION or "3.2.x"

if SENTRY_SUPPORT:
    import sentry_sdk  # noqa
    from sentry_sdk.integrations.django import DjangoIntegration  # noqa
    from conf.web.sentry import SAAS_SENTRY_DSN

    sentry_sdk.init(
        dsn=SAAS_SENTRY_DSN,
        integrations=[DjangoIntegration(str("function_name"))],
        send_default_pii=True,
        release=f"{APP_CODE}@{SAAS_VERSION}",
        environment=os.getenv("BKAPP_SENTRY_ENV", RUN_MODE),
    )

ERROR_SEARCH_PATH = [
    "bkmonitor.errors",
]

# 版本日志配置
VERSION_LOG = {
    "LATEST_VERSION_INFORM": True,
    "LATEST_VERSION_INFORM_TYPE": "popup",
}

# ajax请求401返回plain信息
IS_AJAX_PLAIN_MODE = True

# 显示图表水印
GRAPH_WATERMARK = True

# Grafana配置
GRAFANA_URL = os.getenv("BKAPP_GRAFANA_URL", "http://grafana.bkmonitorv3.service.consul:3000")
GRAFANA_ADMIN_USERNAME = os.getenv("BKAPP_GRAFANA_ADMIN_USERNAME", "admin")

GRAFANA = {
    "HOST": os.getenv("BKAPP_GRAFANA_URL", "http://grafana.bkmonitorv3.service.consul:3000"),
    "PROVISIONING_PATH": BASE_DIR + "/packages/monitor_web/grafana/provisioning",  # noqa
    "PROVISIONING_CLASSES": ["monitor_web.grafana.provisioning.BkMonitorProvisioning"],
    "PERMISSION_CLASSES": ["monitor_web.grafana.permissions.BizPermission"],
    "CODE_INJECTIONS": {
        "<head>": """<head>
<style>
      .sidemenu {
        display: none !important;
      }
      .navbar-page-btn .gicon-dashboard {
        display: none !important;
      }
      .navbar .navbar-buttons--tv {
        display: none !important;
      }
    .css-1jrggg2 {
          left: 0 !important;
      }
      .css-9nwlx8 {
        display: none;
      }
</style>
<script>
var _wr = function(type) {
    var orig = history[type];
    return function() {
        var rv = orig.apply(this, arguments);
        var e = new Event(type);
        e.arguments = arguments;
        window.dispatchEvent(e);
        return rv;
    };
};
   history.pushState = _wr('pushState');
   history.replaceState = _wr('replaceState');
  ["popstate", "replaceState", "pushState"].forEach(function(eventName) {
    window.addEventListener(eventName, function() {
      window.parent.postMessage({ pathname: this.location.pathname }, "*");
    });
  });
   window.addEventListener('message', function(e) {
        if(e && e.data ) {
        var dom = null;
        switch(e.data) {
            case 'create':
            dom = document.querySelector('.sidemenu__top .sidemenu-item:nth-child(2) .dropdown-menu li:nth-child(2) a');
            break;
            case 'folder':
            dom = document.querySelector('.sidemenu__top .sidemenu-item:nth-child(2) .dropdown-menu li:nth-child(3) a');
            break;
            case 'import':
            dom = document.querySelector('.sidemenu__top .sidemenu-item:nth-child(2) .dropdown-menu li:nth-child(4) a');
            break;
        }
        dom && dom.click()
        }
    })
</script>
"""
    },
}

# 是否展示升级页面
UPGRADE_ALLOWED = True

# APPO_IP
APPO_IP = os.getenv("BKAPP_APPO_IP", "")

# 拨测任务最大超时限制(ms)
MAX_AVAILABLE_DURATION_LIMIT = 60000

# 特别的AES加密配置信息
SPECIFY_AES_KEY = ""

# job平台在登录目标机器时，有时会遇到目标机器配置了登录时打印一些信息的情况
# 该变量用于分割额外信息与真正的脚本执行结果
DIVIDE_SYMBOL = "=======bkmonitor======="

# 开发商ID
BK_SUPPLIER_ID = 0

# 主机默认匹配维度
DEFAULT_DIMENSION = ["bk_cloud_id", "bk_target_ip"]

# 登录缓存时间配置, 单位秒（与django cache单位一致）
LOGIN_CACHE_EXPIRED = 60

# 解决多级nginx代理下遇到的最外层nginx的`X-Forwarded-Host`设置失效问题
X_FORWARDED_WEIXIN_HOST = "HTTP_X_FORWARDED_WEIXIN_HOST"

# 是否开启使用
USE_WEIXIN = os.environ.get("BKAPP_USE_WEIXIN", None) == "1"
# 是否为企业微信
IS_QY_WEIXIN = os.environ.get("BKAPP_IS_QY_WEIXIN", None) == "1"
# django 配置, 可使用自定义HOST
USE_X_FORWARDED_HOST = USE_WEIXIN
# 微信公众号的app id/企业微信corp id
WEIXIN_APP_ID = os.environ.get("BKAPP_WEIXIN_APP_ID", "")
# 微信公众号的app secret/企业微信应用的secret
WEIXIN_APP_SECRET = os.environ.get("BKAPP_WEIXIN_APP_SECRET", "")
# 该蓝鲸应用对外暴露的外网域名，即配置的微信能回调或访问的域名，如：test.bking.com
WEIXIN_APP_EXTERNAL_HOST = os.environ.get("BKAPP_WEIXIN_APP_EXTERNAL_HOST", "")

# 应用授权作用域
# snsapi_base （不弹出授权页面，直接跳转，只能获取用户openid），
# snsapi_userinfo （弹出授权页面，可通过openid拿到昵称、性别、所在地。并且， 即使在未关注的情况下，只要用户授权，也能获取其信息 ）
WEIXIN_SCOPE = "snsapi_userinfo"

# 蓝鲸微信请求URL前缀
WEIXIN_SITE_URL = os.environ.get("BKAPP_WEIXIN_SITE_URL", SITE_URL + "weixin/")
# 蓝鲸微信本地静态文件请求URL前缀
WEIXIN_STATIC_URL = os.environ.get("BKAPP_WEIXIN_STATIC_URL", STATIC_URL + "weixin/")
# 蓝鲸微信登录的URL
WEIXIN_LOGIN_URL = SITE_URL + "weixin/login/"
# 微信分享地址
WEIXIN_SHARE_URL = WEIXIN_APP_EXTERNAL_HOST + SITE_URL

# 微信调试开关
WX_USER = os.environ.get("BKAPP_WX_USER", None) == 1

# 微信Console开关
ENABLE_CONSOLE = os.environ.get("BKAPP_ENABLE_CONSOLE", None) == 1

# 移动网关鉴权
RIO_TOKEN = os.environ.get("BKAPP_RIO_TOKEN", "")
RIO_TOKEN_LIMIT = os.environ.get("BKAPP_RIO_TOKEN_LIMIT", "")
RIO_URL_LIMIT = os.environ.get("BKAPP_RIO_URL_LIMIT", "")

# 代理转发的请求需要配置
if os.environ.get("BKAPP_CSRF_TRUSTED_ORIGINS", ""):
    CSRF_TRUSTED_ORIGINS = os.environ.get("BKAPP_CSRF_TRUSTED_ORIGINS").split("|")

# COMMON_USERNAME 平台账号
COMMON_USERNAME = os.environ.get("BKAPP_COMMON_USERNAME", "admin")

# 自定义字符型data id
GSE_CUSTOM_EVENT_DATAID = 1100000


# influxdb host
INFLUXDB_METRIC_HOST = os.getenv("BKAPP_INFLUXDB_METRIC_HOST", "influxdb.service.consul")
INFLUXDB_METRIC_PORT = os.getenv("BKAPP_INFLUXDB_METRIC_PORT", "9273")
INFLUXDB_METRIC_URI = os.getenv("BKAPP_INFLUXDB_METRIC_URI", "/metrics")

# 聚合网关默认业务ID
AGGREGATION_BIZ_ID = 2
