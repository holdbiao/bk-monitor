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
from core.drf_resource import resource
from bkmonitor.utils.time_tools import localtime, now
from bkmonitor.views import serializers
from constants.shield import ScopeType, ShieldCategory, ShieldStatus
from monitor_web.shield.utils import ShieldDisplayManager

from .backend_resources import ShieldListSerializer


class FrontendShieldListResource(Resource):
    """
    告警屏蔽列表（前端）
    """

    def __init__(self):
        super(FrontendShieldListResource, self).__init__()

    class RequestSerializer(ShieldListSerializer):
        search = serializers.CharField(required=False, label=_("查询参数"), allow_blank=True)

    @staticmethod
    def get_dimension_config(shield):
        if shield["category"] in [ShieldCategory.STRATEGY, ShieldCategory.EVENT]:
            return {"id": shield["dimension_config"].get("strategy_id") or shield["dimension_config"].get("_event_id")}
        return {}

    @staticmethod
    def get_status_name(status):
        status_mapping = {0: _("屏蔽中"), 1: _("已过期"), 2: _("被解除")}
        return status_mapping.get(status)

    def perform_request(self, data):
        page = data.get("page", 0)
        page_size = data.get("page_size", 0)
        params = {
            "bk_biz_id": data.get("bk_biz_id"),
            "is_active": data.get("is_active"),
            "order": data.get("order"),
            "categories": data.get("categories"),
            "time_range": data.get("time_range"),
        }
        result = resource.shield.shield_list(**params)

        shield_display_manager = ShieldDisplayManager(data["bk_biz_id"])
        shields = []
        for shield in result["shield_list"]:
            shields.append(
                {
                    "id": shield["id"],
                    "bk_biz_id": shield["bk_biz_id"],
                    "category": shield["category"],
                    "category_name": shield_display_manager.get_category_name(shield),
                    "status": shield["status"],
                    "status_name": self.get_status_name(shield["status"]),
                    "dimension_config": self.get_dimension_config(shield),
                    "content": shield["content"]
                    if shield["content"]
                    else shield_display_manager.get_shield_content(shield),
                    "begin_time": shield["begin_time"],
                    "failure_time": shield["failure_time"],
                    "cycle_duration": shield_display_manager.get_cycle_duration(shield),
                    "description": shield["description"],
                    "source": shield["source"],
                }
            )

        if data.get("search"):
            # 全字段范匹配
            if data.get("is_active"):
                fuzzy_search_list = [
                    "id",
                    "category_name",
                    "content",
                    "begin_time",
                    "cycle_duration",
                    "description",
                    "status_name",
                ]
            else:
                fuzzy_search_list = ["id", "category_name", "content", "failure_time", "description", "status_name"]

            search_result = []
            for shield in shields:
                for fuzzy_key in fuzzy_search_list:
                    if data.get("search") in str(shield.get(fuzzy_key, "")):
                        search_result.append(shield)
                        break

            shields = search_result

        # 统计数目
        count = len(shields)

        # 分页
        if all([data.get("page"), data.get("page_size")]):
            shields = shields[(page - 1) * page_size : page * page_size]

        return {"count": count, "shield_list": shields}


class FrontendShieldDetailResource(Resource):
    """
    告警屏蔽详情（前端）
    """

    def __init__(self):
        super(FrontendShieldDetailResource, self).__init__()
        self.bk_biz_id = None

    class RequestSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=True, label=_("屏蔽id"))
        bk_biz_id = serializers.IntegerField(required=True, label=_("业务ID"))

    @property
    def receivers(self):
        return resource.notice_group.get_receiver()

    def get_receiver_list(self, receiver_id, receiver_type):
        receiver_list = []
        for item in self.receivers:
            if item["id"] == receiver_type:
                receiver_list = item["children"]
                break

        for receiver_msg in receiver_list:
            if receiver_msg["id"] == receiver_id:
                return {
                    "id": receiver_msg["id"],
                    "display_name": receiver_msg["display_name"],
                    "logo": receiver_msg["logo"],
                    "type": receiver_msg["type"],
                }

        return None

    def handle_notice_config(self, notice_config):
        notice_receiver = []
        for receiver in notice_config["notice_receiver"]:
            receiver_id = receiver.split("#", 1)[1]
            receiver_type = receiver.split("#", 1)[0]
            notice_receiver.append(self.get_receiver_list(receiver_id, receiver_type))
        notice_config["notice_receiver"] = [receiver for receiver in notice_receiver if receiver]
        return notice_config

    def handle_dimension_config(self, shield):
        dimension_config = {}
        shield_display_manager = ShieldDisplayManager(self.bk_biz_id)
        if shield.get("scope_type"):
            if shield["scope_type"] == ScopeType.INSTANCE:
                target = shield_display_manager.get_service_name_list(
                    self.bk_biz_id, shield["dimension_config"].get("service_instance_id")
                )
            elif shield["scope_type"] == ScopeType.IP:
                target = [ip["bk_target_ip"] for ip in shield["dimension_config"].get("bk_target_ip")]
            elif shield["scope_type"] == ScopeType.NODE:
                target = shield_display_manager.get_node_path_list(
                    self.bk_biz_id, shield["dimension_config"].get("bk_topo_node")
                )
                target = ["/".join(item) for item in target]
            else:
                business = shield_display_manager.get_business_name(shield["bk_biz_id"])
                target = [business]

            dimension_config.update({"scope_type": shield["scope_type"], "target": target})

        if shield["category"] == ShieldCategory.STRATEGY:
            strategy_ids = shield["dimension_config"]["strategy_id"]
            if not isinstance(strategy_ids, list):
                strategy_ids = [strategy_ids]
            strategies = []
            for strategy_id in strategy_ids:
                strategy_info = resource.strategies.strategy_info(id=strategy_id, bk_biz_id=self.bk_biz_id)
                strategies.append(strategy_info)
            dimension_config.update({"strategies": strategies, "level": shield["dimension_config"]["level"]})
        elif shield["category"] == ShieldCategory.EVENT:
            dimension_config.update(
                {
                    "level": shield["dimension_config"]["_level"],
                    "event_message": shield["dimension_config"]["_event_message"],
                    "dimensions": shield["dimension_config"]["_dimensions"],
                }
            )
        return dimension_config

    def perform_request(self, data):
        result = resource.shield.shield_detail(**data)
        self.bk_biz_id = data["bk_biz_id"]
        dimension_config = self.handle_dimension_config(result)
        notice_config = self.handle_notice_config(result["notice_config"]) if result["notice_config"] else {}
        result.update(dimension_config=dimension_config, notice_config=notice_config)
        return result


class ShieldSnapshotResource(FrontendShieldDetailResource):
    """
    告警屏蔽详情（快照）
    """

    def __init__(self):
        super(ShieldSnapshotResource, self).__init__()

    class RequestSerializer(serializers.Serializer):
        config = serializers.DictField(required=True, label=_("屏蔽快照"))

    @staticmethod
    def get_shield_status(config):
        now_time = localtime(now())
        end_time = localtime(config["end_time"])
        if config["is_enabled"]:
            if now_time > end_time:
                return ShieldStatus.EXPIRED
            else:
                return ShieldStatus.SHIELDED
        else:
            return ShieldStatus.REMOVED

    def perform_request(self, data):
        config = data["config"]
        self.bk_biz_id = config["bk_biz_id"]
        config["shield_notice"] = True if config["notice_config"] else False
        config["status"] = self.get_shield_status(config)
        config["begin_time"] = config["begin_time"].strftime("%Y-%m-%d %H:%M:%S")
        config["end_time"] = config["end_time"].strftime("%Y-%m-%d %H:%M:%S")
        dimension_config = self.handle_dimension_config(config)
        notice_config = self.handle_notice_config(config["notice_config"]) if config["notice_config"] else {}
        config.update(dimension_config=dimension_config, notice_config=notice_config)
        return config
