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


import logging

from blueapps.account.middlewares import LoginRequiredMiddleware
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework.authentication import SessionAuthentication

logger = logging.getLogger(__name__)

User = get_user_model()


class KernelSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        request.csrf_processing_done = True


class AppWhiteListModelBackend(ModelBackend):

    # 经过esb 鉴权， bktoken已经丢失，因此不再对用户名进行校验。
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user_model = get_user_model()
            user, _ = user_model.objects.get_or_create(username=username, defaults={"nickname": username})
        except Exception:
            logger.exception("Auto create & update UserModel fail")
            return None

        if self.user_can_authenticate(user):
            return user

    def user_can_authenticate(self, user):
        is_active = getattr(user, "is_active", None)
        return is_active or is_active is None


class ESBAuthenticationMiddleware(LoginRequiredMiddleware):
    def process_view(self, request, *args, **kwargs):
        if "/grafana/" in request.path:
            app_code = settings.APP_CODE
            username = "admin"
        else:
            app_code = request.META.get("HTTP_BK_APP_CODE")
            username = request.META.get("HTTP_BK_USERNAME")

        if app_code:
            user = auth.authenticate(username=username)
            if user:
                request.user = user
                return None
        return super(ESBAuthenticationMiddleware, self).process_view(request, *args, **kwargs)


class JWTAuthenticationMiddleware(LoginRequiredMiddleware):
    def process_view(self, request, *args, **kwargs):
        user = None

        if "/grafana/" in request.path:
            user = auth.authenticate(username="admin")
        else:
            from bkoauth.jwt_client import JWTClient

            request.jwt = JWTClient(request)

            if request.jwt.is_valid:
                user = auth.authenticate(request=request, username=request.jwt.user.username)

        if user:
            request.user = user
            return None

        return super(JWTAuthenticationMiddleware, self).process_view(request, *args, **kwargs)


# 如无设置JWT则说明接入ESB
if settings.APIGW_PUBLIC_KEY:
    AuthenticationMiddleware = JWTAuthenticationMiddleware
else:
    AuthenticationMiddleware = ESBAuthenticationMiddleware
