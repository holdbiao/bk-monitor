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
from django.contrib import admin

from response_tracker.models import Record


class RecordAdmin(admin.ModelAdmin):

    date_hierarchy = "date_created"

    list_display = (
        "__unicode__",
        "status_code",
        "content_type",
        "show_content_length",
        "show_date_created",
        "duration",
    )
    list_filter = ("date_created", "method", "status_code", "content_type")
    search_fields = ("request_message", "response_message")

    fieldsets = (
        (
            "Request",
            {
                "fields": (
                    "method",
                    "path",
                    "request_message",
                ),
            },
        ),
        (
            "Response",
            {
                "fields": (
                    "status_code",
                    "content_type",
                    "content_length",
                    "response_message",
                ),
            },
        ),
        (
            "Important Datetimes",
            {
                "fields": (
                    "date_created",
                    "duration",
                ),
            },
        ),
    )

    readonly_fields = ("method", "path", "status_code", "content_type", "content_length", "date_created", "duration")

    def show_content_length(self, obj):
        if obj.content_length == 1:
            kb_size = 0.0
        elif obj.content_length <= 51:
            kb_size = 0.1
        else:
            kb_size = obj.content_length / 1024.0
        return "{:.1f} KB".format(kb_size)

    show_content_length.short_description = "Content length"

    def show_date_created(self, obj):
        return obj.date_created.strftime("%Y-%m-%d %H:%M:%S")

    show_date_created.short_description = "Date created"


admin.site.register(Record, RecordAdmin)
