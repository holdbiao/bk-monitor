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


import django_filters
from django.utils.translation import ugettext as _
from rest_framework import serializers

from monitor_api import views


class BaseAlarmViewSet(views.BaseAlarmViewSet):
    """
    基础告警

    list:获取基础告警列表

    count:基础告警计数

    """

    class BaseAlarmSerializer(views.BaseAlarmViewSet.serializer_class):
        pass

    serializer_class = BaseAlarmSerializer

    class BaseAlarmFilterSet(views.BaseAlarmViewSet.filter_class):
        pass

    filter_class = BaseAlarmFilterSet


class UserConfigViewSet(views.UserConfigViewSet):
    """
    用户配置信息

    count:用户配置信息计数

    partial_update:部分更新用户配置信息

    list:用户配置信息列表
    """

    class UserConfigSerializer(views.UserConfigViewSet.serializer_class):
        bk_username = serializers.CharField(source="username", help_text=_("用户名"))

    serializer_class = UserConfigSerializer

    class UserConfigFilterSet(views.UserConfigViewSet.filter_class):
        bk_username = django_filters.CharFilter(name="username", label=_("用户名"))

    filter_class = UserConfigFilterSet


class ApplicationConfigViewSet(views.ApplicationConfigViewSet):
    """
    业务配置信息

    count:业务配置信息计数

    create:创建业务配置信息
    """

    class ApplicationConfigSerializer(views.ApplicationConfigViewSet.serializer_class):
        bk_biz_id = serializers.IntegerField(source="cc_biz_id", help_text=_("业务ID"))

    serializer_class = ApplicationConfigSerializer

    class ApplicationConfigFilterSet(views.ApplicationConfigViewSet.filter_class):
        bk_biz_id = django_filters.NumberFilter(name="cc_biz_id", label=_("业务id"))

    filter_class = ApplicationConfigFilterSet


class IndexColorConfViewSet(views.IndexColorConfViewSet):
    """
    性能指标颜色配置

    count:性能指标颜色配置计数
    """

    class IndexColorConfSerializer(views.IndexColorConfViewSet.serializer_class):
        pass

    serializer_class = IndexColorConfSerializer

    class IndexColorConfFilterSet(views.IndexColorConfViewSet.filter_class):
        pass

    filter_class = IndexColorConfFilterSet


class GlobalConfigViewSet(views.GlobalConfigViewSet):
    """
    全局配置信息

    count:全局配置信息计数
    """

    class GlobalConfigSerializer(views.GlobalConfigViewSet.serializer_class):
        pass

    serializer_class = GlobalConfigSerializer

    class GlobalConfigFilterSet(views.GlobalConfigViewSet.filter_class):
        pass

    filter_class = GlobalConfigFilterSet


class OperateRecordViewSet(views.OperateRecordViewSet):
    """
    操作记录

    count:操作记录计数

    list:操作记录列表
    """

    class OperateRecordSerializer(views.OperateRecordViewSet.serializer_class):
        bk_biz_id = serializers.IntegerField(source="biz_id", help_text=_("业务ID"))

    serializer_class = OperateRecordSerializer

    class OperateRecordFilterSet(views.OperateRecordViewSet.filter_class):
        bk_biz_id = django_filters.NumberFilter(name="biz_id", help_text=_("业务ID"))

    filter_class = OperateRecordFilterSet


class RolePermissionViewSet(views.RolePermissionViewSet):
    """
    角色权限管理

    count:角色权限管理计数

    delete:删除角色权限

    list:角色权限管理列表
    """

    class RolePermissionSerializer(views.RolePermissionViewSet.serializer_class):
        bk_biz_id = serializers.IntegerField(source="biz_id", help_text=_("业务ID"))

    serializer_class = RolePermissionSerializer

    class RolePermissionFilterSet(views.RolePermissionViewSet.filter_class):
        bk_biz_id = django_filters.NumberFilter(name="biz_id", label=_("业务ID"))

    filter_class = RolePermissionFilterSet


class SnapshotHostIndexViewSet(views.SnapshotHostIndexViewSet):
    class SnapshotHostIndexSerializer(views.SnapshotHostIndexViewSet.serializer_class):
        pass

    serializer_class = SnapshotHostIndexSerializer

    class SnapshotHostIndexFilterSet(views.SnapshotHostIndexViewSet.filter_class):
        pass

    filter_class = SnapshotHostIndexFilterSet


class MonitorLocationViewSet(views.MonitorLocationViewSet):
    """
    监控映射

    count:监控映射计数
    """

    class MonitorLocationSerializer(views.MonitorLocationViewSet.serializer_class):
        bk_biz_id = serializers.CharField(source="biz_id", help_text=_("业务ID"))

    serializer_class = MonitorLocationSerializer

    class MonitorLocationFilterSet(views.MonitorLocationViewSet.filter_class):
        bk_biz_id = django_filters.CharFilter(name="biz_id", label=_("业务ID"))

    filter_class = MonitorLocationFilterSet


class AlarmTypeViewSet(views.AlarmTypeViewSet):
    """
    告警类型
    """

    pass
