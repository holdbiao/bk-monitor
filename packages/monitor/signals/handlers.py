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


import datetime
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _

from bkmonitor.utils.common_utils import check_permission
from bkmonitor.utils.model_manager import AbstractRecordModel
from bkmonitor.utils.request import get_request
from common.log import logger

MODELS_TO_OPERATE_RECORD = settings.OPERATE_RECORD_CONFIG


def post_init_handler(sender, instance, *args, **kwargs):
    if instance._meta.app_label not in ["monitor", "monitor_api"]:
        return
    if getattr(instance, "permission_exempt", True):
        return
    try:
        request = get_request()
        request_bk_biz_id = getattr(request, "biz_id", None)
        if request_bk_biz_id is not None:
            if not check_permission(instance, request_bk_biz_id):
                raise PermissionDenied(_("权限不通过！ 请求项不属于当前业务"))

    except PermissionDenied as e:
        raise PermissionDenied(e)

    except Exception:
        pass


def get_changed_status(sender, old_dict_value, new_dict_value):
    """
    在 pre_save 信号中查看当前实例是否已经存在于表中，如果不存在，则为创建操作，直接跳出
    :param sender: 发送信号实例的 Model 类
    :param old_dict_value: 从数据库读取的参数
    :param new_dict_value: 更新时，新实例的参数
    :return:
    """
    is_changed = False
    # 将旧数据和新数据逐条对比，以确定当前更新有没有信息更新，如果没有则不记录流水
    for i in list(old_dict_value.keys()):
        if type(old_dict_value[i]) == datetime.datetime:
            old_value = str(old_dict_value[i] + datetime.timedelta(hours=8))[:16]
            new_value = str(new_dict_value[i])[:16]
            if old_value != new_value:
                is_changed = True
                break
        elif str(old_dict_value[i]) != str(new_dict_value[i]):
            is_changed = True
            break
    return is_changed


def get_existed_status(sender, instance):
    """
    在 pre_save 中是否已经存在对应实例 id 的记录，如果不是则对应
    :param sender: 发送信号实例的 Model 类
    :param instance: 发送信号的实例
    :return: 当前实例是否已经存在于记录中
    """
    return sender.objects.filter(pk=instance.pk).exists()


def create_model_update_operate_record(sender, instance, *args, **kwargs):
    """
    处理更新操作
    :param sender: 发送信号实例的 Model 类
    :param instance: 发送信号的实例
    :param args:
    :param kwargs:
    :return:
    """
    try:
        if instance._meta.app_label not in ["monitor", "monitor_api"]:
            return
        request = get_request(peaceful=True)
        if not request:
            return
        # 如果不在需要记录的类中，或者当前数据库中不存在对应 id 的记录，不做任何操作直接跳出
        if (instance._meta.object_name not in MODELS_TO_OPERATE_RECORD) or (not get_existed_status(sender, instance)):
            return
        # 新的数据来自传过来的 instance ，旧数据来自数据库，将两者对比，没有变更则不做任何操作
        try:
            old_instance = sender.objects.get(id=instance.id)
        except Exception:
            # 所有的报错都放在上层处理
            raise
        new_dict_value = model_to_dict(instance)
        old_dict_value = model_to_dict(old_instance)
        new_dict_to_db = format_object_to_dic(instance)
        old_dict_to_db = format_object_to_dic(old_instance)
        is_changed = get_changed_status(sender, old_dict_value, new_dict_value)
        if not is_changed:
            return
        from monitor.models import OperateRecord

        OperateRecord.objects.create(
            biz_id=request.biz_id if request.biz_id else instance.biz_id,
            config_type=instance._meta.object_name,
            config_id=instance.id,
            config_title=instance.get_title() if hasattr(instance, "get_title") else "",
            operator=request.user.username,
            operator_name=request.user.nickname,
            operate="update",
            data=new_dict_to_db,
            data_ori=old_dict_to_db,
        )
    except Exception as e:
        logger.warning(e)
        return


def create_model_create_operate_record(sender, instance, *args, **kwargs):
    """
    处理创建操作
    :param sender: 发送信号实例的 Model 类
    :param instance: 发送信号的实例
    :param args:
    :param kwargs:
    :return:
    """
    try:
        if instance._meta.app_label not in ["monitor", "monitor_api"]:
            return
        request = get_request(peaceful=True)
        if not request:
            return
        # 如果不在需要记录的类中，或者不是创建操作时，不做任何操作直接跳出
        if (instance._meta.object_name not in MODELS_TO_OPERATE_RECORD) or (not kwargs["created"]):
            return
        from monitor.models import OperateRecord

        OperateRecord.objects.create(
            biz_id=request.biz_id if request.biz_id else instance.biz_id,
            config_type=instance._meta.object_name,
            config_id=instance.id,
            config_title=instance.get_title() if hasattr(instance, "get_title") else "",
            operator=request.user.username,
            operator_name=request.user.nickname,
            operate="create",
            data=format_object_to_dic(instance),
            data_ori={},
        )
    except Exception as e:
        logger.warning(e)
        return


def create_model_delete_operate_record(sender, instance, *args, **kwargs):
    """
    处理删除操作
    :param sender: 发送信号实例的 Model 类
    :param instance: 发送信号的实例
    :param args:
    :param kwargs:
    :return:
    """
    try:
        if instance._meta.app_label not in ["monitor", "monitor_api"]:
            return
        request = get_request(peaceful=True)
        if not request:
            return
        if instance._meta.object_name not in MODELS_TO_OPERATE_RECORD:
            return
        # 先判断 send 是不是继承自 AbstractRecordModel ，如果是的话，则要使用不同的query_set接口
        if issubclass(sender, AbstractRecordModel):
            old_dict_value = model_to_dict(sender.origin_objects.get(id=instance.id))
        else:
            old_dict_value = model_to_dict(sender.objects.get(id=instance.id))
        from monitor.models import OperateRecord

        OperateRecord.objects.create(
            biz_id=request.biz_id if request.biz_id else instance.biz_id,
            config_type=instance._meta.object_name,
            config_id=instance.id,
            config_title=instance.get_title() if hasattr(instance, "get_title") else "",
            operator=request.user.username,
            operator_name=request.user.nickname,
            operate="delete",
            data_ori=json.dumps(old_dict_value),
            data=format_object_to_dic(instance),
        )
    except Exception as e:
        logger.warning(e)
        return


def format_object_to_dic(instance, **kwargs):
    if not instance:
        return "{}"
    class_name = instance.__class__.__name__
    module = instance.__class__.__module__
    info = instance.__dict__
    info.update(kwargs)
    if isinstance(instance, Model):
        info = info.copy()
        info.pop("_state", None)
        info.pop("_menu", None)
        info.pop("_monitor", None)
    return json.dumps({"class": class_name, "module": module, "info": info}, cls=JsonDatetimeEncode)


class JsonDatetimeEncode(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, datetime.time):
            return str(value)
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        return json.JSONEncoder.default(self, value)


def create_api_operate_record(task):
    pass
