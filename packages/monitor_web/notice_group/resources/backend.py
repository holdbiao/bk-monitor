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


from django.utils.translation import ugettext as _

from core.drf_resource.base import Resource
from core.errors.notice_group import NoticeGroupHasStrategy, NoticeGroupNameExist, NoticeGroupNotExist
from bkmonitor.models.base import NoticeGroup
from bkmonitor.views import serializers

from ..constant import RECEIVER_TYPE


class BackendSearchNoticeGroup(Resource):
    """
    查询通知组
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_ids = serializers.ListField(
            child=serializers.IntegerField(required=True, label=_("业务ID")), required=False
        )
        ids = serializers.ListField(child=serializers.IntegerField(required=True, label=_("告警组ID")), required=False)

    def perform_request(self, params):
        notice_groups = NoticeGroup.objects.all().order_by("-update_time")

        if params.get("bk_biz_ids"):
            notice_groups = notice_groups.filter(bk_biz_id__in=params.get("bk_biz_ids"))

        if params.get("ids"):
            notice_groups = notice_groups.filter(id__in=params.get("ids"))

        result = []
        for notice_group in notice_groups:
            result.append(
                {
                    "id": notice_group.id,
                    "name": notice_group.name,
                    "notice_way": notice_group.notice_way,
                    "notice_receiver": [],
                    "webhook_url": notice_group.webhook_url,
                    "wxwork_group": notice_group.wxwork_group,
                    "message": notice_group.message,
                    "create_time": notice_group.create_time,
                    "update_time": notice_group.update_time,
                    "update_user": notice_group.update_user,
                    "bk_biz_id": notice_group.bk_biz_id,
                    "create_user": notice_group.create_user,
                }
            )
            for receiver in notice_group.notice_receiver:
                receiver_list = receiver.split("#")
                result[-1]["notice_receiver"].append(
                    {"id": receiver_list[1] if len(receiver_list) > 1 else "", "type": receiver_list[0]}
                )
        return result


class BackendSaveNoticeGroupResource(Resource):
    """
    保存通知组
    """

    class RequestSerializer(serializers.Serializer):
        class NoticeReceiverSerializer(serializers.Serializer):
            id = serializers.CharField(required=True, label=_("通知对象ID"))
            type = serializers.ChoiceField(required=True, choices=RECEIVER_TYPE, label=_("通知对象类别"))

        bk_biz_id = serializers.IntegerField(required=False, default=0, label=_("业务ID"))
        name = serializers.CharField(required=True, max_length=128, label=_("通知组名称"))
        notice_receiver = NoticeReceiverSerializer(required=True, many=True, label=_("通知对象"))
        message = serializers.CharField(required=False, allow_blank=True, label=_("说明"))
        notice_way = serializers.DictField(required=True, label=_("各级别对应的通知方式"))
        wxwork_group = serializers.DictField(required=False, default={})
        webhook_url = serializers.CharField(required=False, allow_blank=True, default="", label=_("回调地址"))
        id = serializers.IntegerField(required=False, label=_("修改对应的通知组ID列表"))

        def validate_notice_way(self, value):
            if any(value.values()):
                return value
            raise serializers.ValidationError(_("通知方式至少开启一项"))

    def validate_request_data(self, request_data):
        # 对象不存在
        if request_data.get("id"):
            instance = NoticeGroup.objects.filter(id=request_data["id"]).first()
            if not instance:
                raise NoticeGroupNotExist({"msg": _("修改通知组失败")})
            serializer = self.RequestSerializer(instance, data=request_data, partial=True)
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data

        # 重名检测
        instance = (
            NoticeGroup.objects.filter(name=request_data["name"], bk_biz_id=request_data["bk_biz_id"])
            .exclude(id=request_data.get("id"))
            .first()
        )
        if instance:
            raise NoticeGroupNameExist()

        return super(BackendSaveNoticeGroupResource, self).validate_request_data(request_data)

    def perform_request(self, validated_request_data):
        if validated_request_data.get("notice_receiver"):
            validated_request_data["notice_receiver"] = [
                "{}#{}".format(data["type"], data["id"]) for data in validated_request_data["notice_receiver"]
            ]

        if validated_request_data.get("id"):
            notice_group_id = validated_request_data["id"]
            instance = NoticeGroup.objects.get(id=notice_group_id)
            for attr, value in list(validated_request_data.items()):
                setattr(instance, attr, value)
            instance.save()
        else:
            instance = NoticeGroup.objects.create(**validated_request_data)
        return {"id": instance.id}


class BackendDeleteNoticeGroupResource(Resource):
    """
    删除通知组
    """

    class RequestSerializer(serializers.Serializer):
        ids = serializers.ListField(required=True, label=_("通知组ID"))

    def perform_request(self, validated_request_data):
        ids = validated_request_data["ids"]
        groups = NoticeGroup.objects.filter(id__in=ids)
        for group in groups:
            if group.related_strategy:
                raise NoticeGroupHasStrategy
        groups.update(is_deleted=True)
