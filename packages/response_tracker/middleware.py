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
import time

from django.utils import timezone
from response_tracker.models import Record
from response_tracker.utils import http_message

logger = logging.getLogger(__name__)

DEFAULT_CONTENT_TYPE = "text/html"


class ResponseTrackerMiddleware(object):
    def __init__(self):
        self._registry = {}

    def _is_ignored(self, request):
        if (
            getattr(request, "current_app", None) == "admin"
            or request.path.endswith("/admin/jsi18n/")
            or request.path.endswith("/favicon.ico")
        ):
            return True

        return False

    def set(self, request, key, value):
        self._registry.setdefault(id(request), {})[key] = value

    def get(self, request, key, raise_exception=True):
        registry = self._registry.setdefault(id(request), {})

        if raise_exception:
            return registry[key]
        else:
            return registry.get(key, None)

    def update(self, request, items):
        self._registry.setdefault(id(request), {}).update(**items)

    def destroy(self, request):
        self._registry.pop(id(request), None)

    def process_request(self, request):
        self.update(
            request,
            {
                "method": request.method,
                "path": request.path,
                "request_message": http_message.render_request_message(request),
                "date_created": timezone.now(),
            },
        )

    def get_content_type(self, response):
        if "Content-Type" in response:
            return response["Content-Type"].split(";")[0]
        else:
            return DEFAULT_CONTENT_TYPE

    def get_content_length(self, response):
        if "Content-Length" in response:
            return response["Content-Length"]
        elif isinstance(response.content, str):
            return len(response.content)
        else:
            return 0

    def process_response(self, request, response):
        timedelta = timezone.now() - self.get(request, "date_created")
        duration = int(round(timedelta.total_seconds() * 1000))

        self.update(
            request,
            {
                "status_code": response.status_code,
                "content_type": self.get_content_type(response),
                "content_length": self.get_content_length(response),
                "response_message": http_message.render_response_message(response),
                "duration": duration,
            },
        )

        consuming = self.record_response(request)
        response["X-Response-Tracker-Consuming"] = consuming
        response["X-Response-Tracker-Duration"] = duration

        self.destroy(request)
        return response

    def record_response(self, request):
        try:
            before = int(time.time() * 1000)
            if not self._is_ignored(request):
                Record.objects.create(**self._registry[id(request)])
        except Exception:
            logger.exception("Record response failed.")
        finally:
            after = int(round(time.time() * 1000))

        return after - before
