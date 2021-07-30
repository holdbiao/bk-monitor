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
from django_filters.constants import STRICTNESS
from rest_framework import serializers, viewsets

from monitor import models

__all__ = ["ComponentInstanceViewSet"]


class ComponentInstanceSlz(serializers.ModelSerializer):
    bk_biz_id = serializers.IntegerField(source="biz_id", help_text=_("业务ID"))
    bk_cloud_id = serializers.IntegerField(source="plat_id", help_text=_("子网ID"))

    class Meta:
        model = models.ComponentInstance
        exclude = ["config"]


class ComponentInstanceFtr(django_filters.FilterSet):
    bk_biz_id = django_filters.NumberFilter(name="biz_id")
    bk_cloud_id = django_filters.NumberFilter(name="plat_id")

    class Meta:
        model = models.ComponentInstance
        strict = STRICTNESS.RAISE_VALIDATION_ERROR
        fields = ("id", "bk_biz_id", "ip", "bk_cloud_id", "component")


class ComponentInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    组件实例查询 API

    retrieve: 返回指定组件
    返回指定id的组件实例

    list: 批量筛选组件
    根据指定的过滤条件和分页参数来筛选组件列表
    """

    queryset = models.ComponentInstance.objects.all()
    serializer_class = ComponentInstanceSlz
    filter_class = ComponentInstanceFtr
