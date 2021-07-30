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
from __future__ import absolute_import, unicode_literals

import os
import random
import string

from conf.default_settings import BASE_DIR


def get_logging_config_dict(settings_module):
    APP_CODE = settings_module["APP_CODE"]
    log_class = "logging.handlers.RotatingFileHandler"
    log_level = settings_module.get("LOG_LEVEL", "INFO")

    if settings_module.get("IS_LOCAL", False):
        log_dir = os.path.join(os.path.dirname(BASE_DIR), "logs", APP_CODE)
        log_name_prefix = os.getenv("BKPAAS_LOG_NAME_PREFIX", APP_CODE)
        logging_format = {
            "format": (
                "%(levelname)s [%(asctime)s] %(pathname)s "
                "%(lineno)d %(funcName)s %(process)d %(thread)d "
                "\n \t %(message)s \n"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    else:
        log_dir = settings_module.get("LOG_DIR_PREFIX", "/app/v3logs/")
        rand_str = "".join(random.sample(string.ascii_letters + string.digits, 4))
        log_name_prefix = "{}-{}".format(os.getenv("BKPAAS_PROCESS_TYPE"), rand_str)

        logging_format = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": (
                "%(levelname)s %(asctime)s %(pathname)s %(lineno)d " "%(funcName)s %(process)d %(thread)d %(message)s"
            ),
        }
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": logging_format,
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "null": {
                "level": "DEBUG",
                "class": "logging.NullHandler",
            },
            "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
            "root": {
                "class": log_class,
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "%s-django.log" % log_name_prefix),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
            },
            "component": {
                "class": log_class,
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "%s-component.log" % log_name_prefix),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
            },
            "mysql": {
                "class": log_class,
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "%s-mysql.log" % log_name_prefix),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
            },
            "celery": {
                "class": log_class,
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "%s-celery.log" % log_name_prefix),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
            },
            "blueapps": {
                "class": log_class,
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "%s-django.log" % log_name_prefix),
                # TODO blueapps log 等待平台提供单独的路径
                # log_dir, '%s-blueapps.log' % log_name_prefix),
                "maxBytes": 1024 * 1024 * 10,
                "backupCount": 5,
            },
        },
        "loggers": {
            "celery": {
                "handlers": ["null"],
                "level": "WARNING",
                "propagate": True,
            },
            "component": {
                "handlers": ["component"],
                "level": "WARNING",
                "propagate": True,
            },
            "django": {
                "handlers": ["null"],
                "level": "INFO",
                "propagate": True,
            },
            "django.db.backends": {
                "handlers": ["mysql"],
                "level": "DEBUG",
                "propagate": True,
            },
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": True,
            },
            "monitor_web": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "monitor_api": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "utils": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "drf_non_orm": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "common": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "monitor_adapter": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "root": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "core": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "bkmonitor": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
            "metadata": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": True,
            },
        },
    }
