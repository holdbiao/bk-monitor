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
from collections import defaultdict
from typing import Dict

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from core.drf_resource.base import Resource
from core.errors.notice_group import NoticeGroupNotExist
from bkmonitor.models import ActionNoticeMapping, Action, StrategyModel
from core.drf_resource import resource
from bkmonitor.utils.request import get_request
from bkmonitor.views import serializers
from core.drf_resource import api


class GetReceiverResource(Resource):
    """
    获取平台全部的通知对象
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, label=_("业务Id"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data.get("bk_biz_id", 0)
        # 获取user_list
        if not bk_biz_id:
            user_list = resource.cc.get_all_user()
        else:
            user_list = resource.cc.get_member_data(bk_biz_id=bk_biz_id)

        user_list = [
            {
                "id": user.get("english_name", ""),
                "display_name": user["chinese_name"] if user.get("chinese_name", "") else user.get("english_name", ""),
                "logo": user.get("logo", ""),
                "type": "user",
            }
            for user in user_list
        ]
        # 获取角色组列表
        group_msg = settings.NOTIRY_MAN_DICT
        group_list = []
        for key, value in list(group_msg.items()):
            group_list.append({"id": key, "display_name": value, "logo": "", "type": "group"})

        return [
            {"id": "group", "display_name": _("用户组"), "children": group_list},
            {"id": "user", "display_name": _("用户"), "children": user_list},
        ]


class GetNoticeWayResource(Resource):
    """
    获取平台全部的通知方式
    """

    class RequestSerializer(serializers.Serializer):
        show_all = serializers.BooleanField(label=_lazy("是否展示全部"), default=False)

    def perform_request(self, validated_request_data):
        data = api.cmsi.get_msg_type()

        data.append(
            {
                "icon": "iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAMAAAANIilAAAAARVBMVEWAuv+FvP+Iv/+Mwf+Pw/+Sxf+k0P+t1P/a7P///"
                "//5/P/o8//C3v+Wx//Q5v+Zyf+cy/+hzv/h7//v9/+o0v8/ivhmovpV06EdAAADI0lEQVRIx4XViW7kIAwAUGZycIY7/f"
                "9PXQHGMSSZddSqVefVBhzM2BQfEt/Pt8cCsWJs6zbT8iC9LOJLb9s2pyWZv9/XvFuhI/4MRf/fbmPJD6vd+XYrGOz2uFf"
                "fCwsp1V5p10gJ/nyeSuZSSqlp4o0EKZk9LNcUrAil+rjn/dKdqpkFsYQex+8TWq1WUrv1wXb8oY0xnBAXwh/Lelvu0eJ1"
                "q5ZyulaY9cF2XSi7p20nG4Rw6/qa2LEfrbyaaP32RiHzbaeWZeU2KVlDJcvvFZfEbmirHocF2ENZ/2AR0/MxE23cUepqs"
                "Hm5i0vyMVK4dgo0mxsjK/kSih9j4oKHftxfLWqHwcZddj+slCpQ7D0b+1HLn6GdO5A6z4bGMJhDJRIK6zFonfcEl5bqH0"
                "KmIbBj/EUvXPvR9J4qrDwatQZte9EXXhpOaBsdoul0UcQleMKaJxnrA3813hO8DDXLpFO6yRK98+yA27vbt3RO2mT53g+"
                "CNxoC6+PAAFYNGW9b1hiNN9VH+ICyYAPr48AOOJ/nyVtSfp7nPmDRKMFiwH/nef61fP1HAYu+4XWdMhfBGmYdiwuHgLje"
                "UUY1repKzXn+2Ybt33kaUUJBF5iAGC44l6AFNZgIIaIVLXoL5Rte+YibE1FgRMCYOLBrgAXbzpnYQpG3JVve6b4zOoU0S"
                "T1mxcQaaQiA4VptHaoanaMt6qp5h8x4oScoXAz1CiGshT8RWjGZBlx2fVFbH3grDLU7G0eugOYntH7BSxMpHXG5GfsNmC"
                "KmFfgyprZTO2KUbRyEa17AHXhdxiqHUbNp+rnwevsmTire9z1nNtnj8OLZxh1OFy3gcQjxh1FXm5IsN+eO5wHmzVS7NuM"
                "2g2a3odtu1t0InZRSKmlh8kxz7pmfbIlsa+ShqQgt+Jjmpp8wB3lPnNlLWu89H3C45UU85+VGRF3GY0o6CsPvWXPmDTs6"
                "N70P9jbilc03mjkrjTGmLfeoqiGVlKo/Nu95p5RXjGmrFt31f9F+VSpmmphXPKYNEeSlZK8kjpRzNi4X8r6EQJspxuNRP"
                "8MMtmGPWP/GmtTMOf8HAJeB5MYmTQgAAAAASUVORK5CYII=",
                "is_active": "true",
                "label": "群机器人",
                "type": "wxwork-bot",
                "name": settings.WXWORK_BOT_NAME,
            }
        )

        if not validated_request_data["show_all"]:
            data = [way for way in data if way["type"] in settings.ENABLED_NOTICE_WAYS]
        return data


class NoticeGroupDetailResource(Resource):
    """
    获取通知组详情
    """

    class RequestSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=True, label=_("通知組ID"))

    @cached_property
    def receivers(self) -> Dict[str, Dict[str, Dict]]:
        """
        接收人信息
        """
        receivers: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        for item in resource.notice_group.get_receiver():
            receiver_type = item["id"]
            for receiver in item["children"]:
                receivers[receiver_type][receiver["id"]] = receiver
        return receivers

    def perform_request(self, params):
        instance = resource.notice_group.backend_search_notice_group(ids=[params["id"]])
        if not instance:
            raise NoticeGroupNotExist({"msg": _("获取详情失败")})
        else:
            instance = instance[0]

        notice_receiver = instance["notice_receiver"]
        return_notice_receiver = []
        for receiver in notice_receiver:
            if receiver["id"] not in self.receivers[receiver["type"]]:
                continue
            return_notice_receiver.append(self.receivers[receiver["type"]][receiver["id"]])

        return {
            "id": instance["id"],
            "bk_biz_id": instance["bk_biz_id"],
            "name": instance["name"],
            "message": instance["message"],
            "notice_receiver": return_notice_receiver,
            "notice_way": instance["notice_way"] or {},
            "webhook_url": instance["webhook_url"],
            "wxwork_group": instance["wxwork_group"],
            "create_user": instance["create_user"],
            "update_user": instance["update_user"],
            "create_time": instance["create_time"],
            "update_time": instance["update_time"],
        }


class NoticeGroupListResource(NoticeGroupDetailResource):
    """
    获取通知组列表
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(required=False, default=0, label=_("业务ID"))

    def perform_request(self, validated_request_data):
        bk_biz_id = validated_request_data.get("bk_biz_id")

        if bk_biz_id:
            bk_biz_ids = [0, bk_biz_id]
        else:
            bk_biz_ids = [biz.id for biz in resource.cc.get_app_by_user(get_request().user)]

        notice_groups = resource.notice_group.backend_search_notice_group(bk_biz_ids=bk_biz_ids)
        strategy_ids = StrategyModel.objects.filter(bk_biz_id__in=bk_biz_ids).values_list("id", flat=True)
        action_ids = Action.objects.filter(strategy_id__in=strategy_ids).values_list("id", flat=True)
        # 统计关联的告警策略数量
        strategy_counts = (
            ActionNoticeMapping.objects.filter(
                notice_group_id__in=[notice_group["id"] for notice_group in notice_groups],
                action_id__in=action_ids,
            )
            .values("notice_group_id")
            .annotate(count=models.Count("action_id", distinct=True))
        )

        strategy_count_dict = {
            strategy_count["notice_group_id"]: strategy_count["count"] for strategy_count in strategy_counts
        }

        for notice_group in notice_groups:
            notice_receiver = notice_group["notice_receiver"]
            return_notice_receiver = []
            for receiver in notice_receiver:
                if receiver["id"] not in self.receivers[receiver["type"]]:
                    continue
                return_notice_receiver.append(self.receivers[receiver["type"]][receiver["id"]])
            notice_group["notice_receiver"] = return_notice_receiver

        return [
            {
                "id": notice_group["id"],
                "name": notice_group["name"],
                "bk_biz_id": notice_group["bk_biz_id"],
                "related_strategy": strategy_count_dict.get(notice_group["id"], 0),
                "message": notice_group["message"],
                "notice_receiver": notice_group["notice_receiver"],
                "delete_allowed": strategy_count_dict.get(notice_group["id"], 0) == 0,
                "edit_allowed": True,
            }
            for notice_group in notice_groups
        ]


class NoticeGroupConfigResource(Resource):
    """
    创建、修改通知组
    """

    def perform_request(self, params):
        return resource.notice_group.backend_save_notice_group(**params)


class DeleteNoticeGroupResource(Resource):
    """
    删除通知组
    """

    class RequestSerializer(serializers.Serializer):
        id_list = serializers.ListField(required=True, label=_("通知组ID"))

    def perform_request(self, params):
        return resource.notice_group.backend_delete_notice_group(ids=params["id_list"])
