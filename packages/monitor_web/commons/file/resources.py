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


import os

from django.conf import settings
from django.utils.translation import ugettext as _
from rest_framework import serializers

from core.drf_resource import Resource
from core.drf_resource.exceptions import CustomException
from monitor.models import UploadedFile
from monitor_web.commons.job import JobTaskClient


class FileUploadResource(Resource):
    """
    通用文件上传接口
    """

    class RequestSerializer(serializers.Serializer):
        file_data = serializers.FileField(required=True)
        path = serializers.CharField(default="")
        file_name = serializers.CharField(required=False)

    def perform_request(self, validated_request_data):
        file_data = validated_request_data["file_data"]
        relative_path = validated_request_data["path"]
        original_filename = file_data.name
        file_name = validated_request_data.get("file_name", original_filename)

        # 复制上传文件到本地，路径为settings.MEDIA_ROOT+relative_path
        absolute_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, relative_path))
        if not absolute_path.startswith(settings.MEDIA_ROOT):
            raise CustomException(_("传入的路径不合法"))

        file = UploadedFile(
            actual_filename=file_name,
            original_filename=original_filename,
            relative_path=relative_path,
            file_data=file_data,
        )
        file.save()

        result = {
            "file_id": file.pk,
            "md5": file.file_md5,
            "origin_file_name": original_filename,
            "file_type": file.file_type,
            "file_name": file_name,
        }
        return result


class FileDeployResource(Resource):
    """
    通用文件分发接口
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=True)
        operator = serializers.CharField(required=True)
        file_ids = serializers.ListField(required=True)
        hosts = serializers.ListField(required=True)
        target_path = serializers.CharField(required=True)

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data["bk_biz_id"]
        operator = validated_request_data["operator"]
        file_ids = validated_request_data["file_ids"]
        hosts = validated_request_data["hosts"]
        target_path = validated_request_data["target_path"]

        file_set = UploadedFile.objects.filter(pk__in=file_ids)
        file_list = []
        for file in file_set:
            file_list.append({"file_name": file.actual_filename, "content": file.file_data.file.read()})

        job_client = JobTaskClient(bk_biz_id, operator)
        result = job_client.gse_push_file(hosts=hosts, path=target_path, file_list=file_list)
        result = job_client.label_failed_ip(result, _("文件下发失败"))
        return result
