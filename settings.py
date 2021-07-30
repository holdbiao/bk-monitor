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


import os
import sys
import warnings

from six.moves import map

# monkey patch
import monkey


patch_target = {
    "json": None,
    "multiprocessing.dummy": None,
    "shutil": None,
}

# patch backend celery beat only
if "redbeat.RedBeatScheduler" in sys.argv:
    patch_target.update({"redbeat.schedulers": None})

monkey.patch_all(patch_target)

# append packages to sys.path
sys.path.append(os.path.join(os.getcwd(), "packages"))

#
# load specific settings module
#

_modules = []


def get_bk_env():
    bk_env = os.environ.get("BK_ENV")
    return "conf.%s" % bk_env if bk_env else None


def get_bk_v3_env():
    bk_env_v3 = os.environ.get("BKPAAS_ENVIRONMENT")
    if bk_env_v3:
        bk_env = {"dev": "development", "stag": "testing", "prod": "production"}.get(bk_env_v3)
        return "conf.%s" % bk_env


DJANGO_CONF_MODULE = os.environ.get("DJANGO_CONF_MODULE") or get_bk_env() or get_bk_v3_env() or "conf.development"

# &BEGIN NOTFOR ee, ce
# format DJANGO_CONF_MODULE for web environment
if DJANGO_CONF_MODULE in ("conf.production", "conf.testing", "conf.development"):
    #
    # override DJANGO_CONF_MODULE when deployed by PaaS
    #
    BKAPP_DEPLOY_PLATFORM = os.environ.get("BKAPP_DEPLOY_PLATFORM") or os.environ.get("BKPAAS_ENGINE_REGION")
    if not BKAPP_DEPLOY_PLATFORM and DJANGO_CONF_MODULE == "conf.development":
        BKAPP_DEPLOY_PLATFORM = "ieod"

    _choices = ["ieod", "enterprise", "community"]

    if BKAPP_DEPLOY_PLATFORM not in _choices:
        _choices_str = ", ".join(map(repr, _choices))
        raise RuntimeError(
            "Environment variable 'BKAPP_DEPLOY_PLATFORM' "
            "should not be %r. Choices: %s" % (BKAPP_DEPLOY_PLATFORM, _choices_str)
        )

    _splits = DJANGO_CONF_MODULE.split(".")
    _splits.append(BKAPP_DEPLOY_PLATFORM)

    DJANGO_CONF_MODULE = "%s.web.%s.%s" % tuple(_splits)

# &END

# validate DJANGO_CONF_MODULE
try:
    _, ROLE, ENVIRONMENT, PLATFORM = DJANGO_CONF_MODULE.split(".")
except Exception:
    raise RuntimeError(
        "Environment variable 'DJANGO_CONF_MODULE' "
        "should not be %r. format: %r" % (DJANGO_CONF_MODULE, "conf.{web|worker}.[environment].[platform]")
    )

# inherit from environment specifics

SEARCH_MODULES = (
    DJANGO_CONF_MODULE,
    "conf.%(ROLE)s.%(ENVIRONMENT)s.default_settings" % locals(),
    "conf.%(ROLE)s.default_settings" % locals(),
    "conf.default_settings",
)

for _module_name in SEARCH_MODULES:
    try:
        _modules.append(__import__(_module_name, globals(), locals(), ["*"]))
    except ImportError as e:
        warnings.warn(
            "Could not import conf '{}' (Is it on sys.path?): {}".format(DJANGO_CONF_MODULE, e), ImportWarning
        )
    else:
        IMPORTED_CONF_MODULE = _module_name
        break
else:
    raise ImportError(
        "Could not import neither of confs in {!r}: {}".format("SEARCH_MODULES", ",".join(map(repr, SEARCH_MODULES)))
    )

# inherit from local specifics

if ENVIRONMENT == "development":
    try:
        _modules.append(__import__("local_settings", globals(), locals(), ["*"]))
    except ImportError:
        pass

# assign specifics to locals

PROTECTED_SETTINGS = [
    "DJANGO_CONF_MODULE",
    "ENVIRONMENT",
    "IMPORTED_CONF_MODULE",
    "PLATFORM",
    "PROTECTED_SETTINGS",
    "ROLE",
    "SEARCH_MODULES",
]

for _module in _modules:
    for _setting in dir(_module):
        if _setting == _setting.upper():
            if _setting in PROTECTED_SETTINGS:
                warnings.warn("{!r} in {!r} is a protected setting, ignored.".format(_setting, _module.__name__))
            else:
                locals()[_setting] = getattr(_module, _setting)

# remove disabled apps

DISABLED_APPS = locals().get("DISABLED_APPS")
INSTALLED_APPS = locals().get("INSTALLED_APPS")
if DISABLED_APPS and INSTALLED_APPS:
    INSTALLED_APPS = [_app for _app in INSTALLED_APPS if _app not in DISABLED_APPS]

    _keys = ("AUTHENTICATION_BACKENDS", "DATABASE_ROUTERS", "MIDDLEWARE", "TEMPLATE_CONTEXT_PROCESSORS")

    import itertools

    for _app, _key in itertools.product(DISABLED_APPS, _keys):
        locals()[_key] = tuple([_item for _item in locals()[_key] if not _item.startswith(_app + ".")])

# 环境变量注入 settings
SETTING_ENV_PREFIX = "BKAPP_SETTINGS_"
for key, value in list(os.environ.items()):
    upper_key = key.upper()
    if upper_key.startswith(SETTING_ENV_PREFIX):
        settings_key = upper_key.replace(SETTING_ENV_PREFIX, "")
        locals()[settings_key] = value
        print('[Django Settings] Set config from env: {} = "{}"'.format(settings_key, value))
