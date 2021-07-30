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

from django.db.models.signals import post_save, pre_save, post_delete, post_init
from monitor.signals import handlers

DISPATCH_UID = __name__.replace(".", "_")


def dispath_orm_permission_check():
    post_init.connect(handlers.post_init_handler, dispatch_uid=DISPATCH_UID)


def dispatch_model_operate_record():
    """
    将信号和相关的处理函数连接，其中
    pre_save 用来处理修改记录
    post_save 用来处理创建记录
    post_delete 用来处理删除操作
    :return:
    """
    pre_save.connect(handlers.create_model_update_operate_record)
    post_save.connect(handlers.create_model_create_operate_record)
    post_delete.connect(handlers.create_model_delete_operate_record)


def dispatch_all():
    dispath_orm_permission_check()
    dispatch_model_operate_record()
