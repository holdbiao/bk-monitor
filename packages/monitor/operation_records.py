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


import json

from django.db.models import Model

from bkmonitor.utils.common_utils import DictObj, ignored
from bkmonitor.utils.request import get_request
from bkmonitor.utils.thread_backend import InheritParentThread
from common.log import logger
from monitor.models import (
    DataCollector,
    DataGenerateConfig,
    MonitorLocation,
    OperateRecord,
    RolePermission,
    ScenarioMenu,
)

# 定义需要记录的model
MODELS_TO_LOG = (DataCollector, DataGenerateConfig, ScenarioMenu, MonitorLocation, RolePermission)


def pre_save_models(sender, instance, **kwargs):
    if isinstance(instance, MODELS_TO_LOG):
        if (not hasattr(instance, "id")) or instance.id < 1:
            return
        with ignored(Exception):
            before_save_obj = instance
            before_save_obj = serialize_object(before_save_obj)
            request = get_request()
            # 把保存前的信息存入session
            if not request.session.get("model_operation_cache", False):
                request.session["model_operation_cache"] = {}
            key = "{}_{}".format(sender.__name__, instance.id)
            request.session["model_operation_cache"][key] = before_save_obj


def post_save_models(sender, instance, created, **kwargs):
    if isinstance(instance, MODELS_TO_LOG):
        change_type = "create" if created else "update"
        t = InheritParentThread(target=save_change_log, args=(sender, change_type, instance))
        t.start()
        # save_change_log(sender, change_type, instance)


def post_delete_models(sender, instance, **kwargs):
    if isinstance(instance, MODELS_TO_LOG):
        change_type = "delete"
        t = InheritParentThread(target=save_change_log, args=(sender, change_type, instance))
        t.start()
        # save_change_log(sender, change_type, instance)


def save_change_log(sender, change_type, instance):
    # 判断是否为软删除
    if hasattr(instance, "is_deleted") and instance.is_deleted == 1:
        change_type = "delete"

    change_model = str(sender.__name__)
    data = serialize_object(instance)
    ori_data = "[{}]"
    request = get_request()
    if change_type == "update":
        # 把session中保存的信息取出来
        if not request.session.get("model_operation_cache", False):
            request.session["model_operation_cache"] = {}
        key = "{}_{}".format(sender.__name__, instance.id)
        try:
            ori_data = request.session["model_operation_cache"].get(key, {})
        except Exception:
            ori_data = "[{}]"
    try:
        username = request.user.username
        # user_nick = get_nick_by_uin(username).get(username, username)
    except Exception:
        username = "*SYSTEM*"  # celery backend process
        # user_nick = u'系统'

    # 获取biz_id
    if getattr(instance, "biz_id", None):
        biz_id = instance.biz_id
    else:
        biz_id = 0

    if not biz_id:
        biz_id = 0

    try:
        OperateRecord.objects.create(
            config_type=change_model,
            config_id=instance.id,
            operate=change_type,
            operator=username,
            data=data,
            data_ori=ori_data,
            biz_id=biz_id,
            operator_name=username,
        )
    except Exception as e:
        logger.error("save operation log error! %s" % e)


def serialize_object(object):
    class_name = object.__class__.__name__
    module = object.__class__.__module__
    info = object.__dict__
    if isinstance(object, Model):
        info = info.copy()
        info.pop("_state", None)
    return json.dumps({"class": class_name, "module": module, "info": info}, cls=IgnoreForeignKeyEncoder)


class IgnoreForeignKeyEncoder(json.JSONEncoder):
    def default(self, obj):
        if issubclass(obj.__class__, DictObj):
            return ""
        return json.JSONEncoder.default(self, obj)


def unserialize_object(string_content):
    json_info = json.loads(string_content)
    class_name = json_info.get("class", "")
    module_name = json_info.get("module", "")
    info = json_info.get("info", {})
    module = __import__(module_name, globals(), {}, [module_name.split(".")[-1]])
    return getattr(module, class_name)(**info)
