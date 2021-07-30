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

from blueapps.account.decorators import login_exempt
from django.conf import settings
from django.http import HttpResponse
from django.http.response import JsonResponse

from bkmonitor.utils.local import local
from core.drf_resource import resource


@login_exempt
def get_statistics(request):
    request.user.username = "admin"
    request.user.is_superuser = True
    local.username = settings.COMMON_USERNAME
    result = resource.statistics.get_statistics_data(request.GET)
    if request.GET.get("response_format") == "json":
        return JsonResponse(result, safe=False)
    return HttpResponse(result, content_type="text/plain")
