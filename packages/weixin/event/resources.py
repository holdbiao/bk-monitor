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
from __future__ import absolute_import, print_function, unicode_literals

import logging
from datetime import datetime, timedelta

from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bkmonitor.models import Alert, AlertCollect, Event, EventAction, StrategyModel
from bkmonitor.utils.event_related_info import get_event_relation_info
from bkmonitor.utils.request import get_request
from bkmonitor.utils.time_tools import hms_string
from core.drf_resource import Resource, api, resource
from core.errors.weixin.event import AlertCollectNotFound, EventNotFound
from monitor_web.alert_events.resources import EventDimensionMixin, EventPermissionResource

logger = logging.getLogger(__name__)


class EventTargetMixin(object):
    @classmethod
    def get_target_display(cls, event, topo_links=None):
        """
        目标展示
        """
        if not event.target_key:
            return ""

        dimensions = event.origin_alarm.get("dimension_translation", {})

        target_key = event.target_key
        if target_key.startswith("host|"):
            return dimensions.get("bk_target_ip", {}).get("display_value", "")
        elif target_key.startswith("service|"):
            return dimensions.get("bk_target_service_instance_id", {}).get("display_value", "")
        elif target_key.startswith("topo|"):
            bk_obj_id = dimensions.get("bk_obj_id", {}).get("value", "")
            bk_inst_id = dimensions.get("bk_inst_id", {}).get("value", "")

            if not bk_obj_id or not bk_inst_id:
                return ""

            # 尝试获取拓扑信息
            if not topo_links:
                topo_tree = api.cmdb.get_topo_tree(bk_biz_id=event.bk_biz_id)
                topo_links = topo_tree.convert_to_topo_link()

            for topo_link in topo_links.values():
                for index, topo in enumerate(topo_link):
                    if topo.bk_inst_id != bk_inst_id or topo.bk_obj_id != bk_obj_id:
                        continue

                    return "/".join(topo.bk_inst_name for topo in topo_link[index:])

            # 如果没有拓扑链，则直接展示
            return "{}({})".format(
                dimensions.get("bk_obj_id", {}).get("display_value", bk_obj_id),
                dimensions.get("bk_inst_id", {}).get("display_value", bk_inst_id),
            )

        return ""


class AlarmPermissionResource(EventPermissionResource):
    @classmethod
    def has_alert_collect_permission(cls, alert_collect_id: int):
        """
        通知汇总鉴权
        """
        return Alert.objects.filter(alert_collect_id=alert_collect_id, username=get_request().user.username).exists()

    def request(self, request_data=None, **kwargs):
        """
        执行请求，并对请求数据和返回数据进行数据校验
        """
        request_data = request_data or kwargs
        validated_request_data = self.validate_request_data(request_data)

        if not self.has_biz_permission():
            if "event_id" in validated_request_data:
                if not self.has_event_permission(validated_request_data["event_id"]):
                    raise ValidationError(_("无该事件权限"))
            elif "alert_collect_id" in validated_request_data:
                if not self.has_alert_collect_permission(validated_request_data["alert_collect_id"]):
                    raise ValidationError(_("无该告警权限"))
            else:
                validated_request_data["receiver"] = get_request().user.username

        response_data = self.perform_request(validated_request_data)
        validated_response_data = self.validate_response_data(response_data)
        return validated_response_data


class GetAlarmDetail(AlarmPermissionResource, EventDimensionMixin, EventTargetMixin):
    """
    根据汇总ID展示告警信息及事件列表
    """

    class RequestSerializer(serializers.Serializer):
        alert_collect_id = serializers.IntegerField()
        bk_biz_id = serializers.IntegerField()

    def perform_request(self, params):
        try:
            alert_collect = AlertCollect.objects.get(id=params["alert_collect_id"])
        except AlertCollect.DoesNotExist:
            raise AlertCollectNotFound(alert_collect_id=params["alert_collect_id"])

        # 获取业务名
        business = api.cmdb.get_business(bk_biz_ids=[params["bk_biz_id"]])
        if business:
            bk_biz_name = business[0].bk_biz_name
        else:
            bk_biz_name = str(params["bk_biz_id"])

        result = {
            "collect_time": alert_collect.collect_time,
            "message": alert_collect.extend_info.get("message", ""),
            "bk_biz_id": params["bk_biz_id"],
            "bk_biz_name": bk_biz_name,
            "events": [],
        }

        # 查询关联事件
        alerts = Alert.objects.filter(alert_collect_id=alert_collect.id).values("event_id")
        event_ids = {alert["event_id"] for alert in alerts}
        events = Event.objects.filter(event_id__in=event_ids, bk_biz_id=params["bk_biz_id"])

        # 获取最新策略名
        strategies = StrategyModel.objects.filter(id__in=[event.strategy_id for event in events]).values("id", "name")
        strategy_names = {strategy["id"]: strategy["name"] for strategy in strategies}

        topo_links = None
        for event in events:
            # 处理已删除策略
            if event.strategy_id not in strategy_names:
                strategy_names[event.strategy_id] = event.origin_config.get("name", "")

            # 获取最近异常时间
            latest_anomaly_time = ""
            if event.latest_anomaly_record:
                latest_anomaly_time = event.latest_anomaly_record.source_time

            # 获取事件标题，如果有目标则展示目标，否则展示维度
            if event.target_key:
                # 避免重复请求拓扑链
                if event.target_key.startswith("topo|") and not topo_links:
                    topo_tree = api.cmdb.get_topo_tree(bk_biz_id=event.bk_biz_id)
                    topo_links = topo_tree.convert_to_topo_link()

                title = self.get_target_display(event, topo_links)
            else:
                dimensions = self.get_dimensions(event)
                title = " ".join(
                    "{}={}".format(dimension["display_name"], dimension["display_value"]) for dimension in dimensions
                )

            result["events"].append(
                {
                    "id": event.id,
                    "event_id": event.event_id,
                    "first_anomaly_time": event.begin_time,
                    "latest_anomaly_time": latest_anomaly_time,
                    "status": event.status,
                    "is_shielded": event.is_shielded,
                    "shield_type": event.shield_type,
                    "is_ack": event.is_ack,
                    "duration": hms_string(event.duration.total_seconds()),
                    "strategy_name": strategy_names[event.strategy_id],
                    "dimension_message": self.get_dimensions_str(event),
                    "title": title,
                    "level": event.level,
                    "data_type_label": event.origin_config["item_list"][0]["data_type_label"],
                }
            )
        return result


class GetEventDetail(AlarmPermissionResource, EventDimensionMixin, EventTargetMixin):
    """
    事件详情
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        event_id = serializers.IntegerField(label=_lazy("事件ID"))

    def perform_request(self, params):
        try:
            event = Event.objects.get(id=params["event_id"])
        except Event.DoesNotExist:
            raise EventNotFound(event_id=params["event_id"])

        # 查询事件通知对象
        alerts = Alert.objects.filter(event_id=event.event_id).values("username")
        users = [alert["username"] for alert in alerts]

        # 尝试获取最新的策略名称
        strategy = StrategyModel.objects.filter(id=event.strategy_id).first()
        if strategy:
            strategy_name = strategy.name
        else:
            strategy_name = event.origin_config.get("name", "")

        # 获取最近异常时间
        latest_anomaly_time = ""
        if event.latest_anomaly_record:
            latest_anomaly_time = event.latest_anomaly_record.source_time

        # 获取关联信息
        from monitor_web.alert_events.resources import DetailEventResource

        related_info = ""
        try:
            if event.target_key:
                related_info += DetailEventResource.get_target_relation_info(event.bk_biz_id, event.target_key)
            related_info += get_event_relation_info(event)
        except Exception as e:
            logger.exception(e)

        # 获取事件标题
        if event.target_key:
            title = self.get_target_display(event)
        else:
            dimensions = self.get_dimensions(event)
            title = " ".join(
                "{}={}".format(dimension["display_name"], dimension["display_value"]) for dimension in dimensions
            )

        # 获取最近通知
        latest_notice = EventAction.objects.filter(event_id=event.event_id).last()

        result = {
            "id": event.id,
            "strategy_name": strategy_name,
            "username": ",".join(users),
            "first_anomaly_time": event.begin_time,
            "latest_anomaly_time": latest_anomaly_time,
            "create_time": event.create_time,
            "level_name": event.level_name,
            "level": event.level,
            "status": event.status,
            "notice_status": latest_notice.status if latest_notice else "",
            "current_value": event.origin_alarm["data"]["value"],
            "anomaly_message": list(event.origin_alarm["anomaly"].values())[0]["anomaly_message"],
            "duration": hms_string(event.duration.total_seconds()),
            "dimension_message": self.get_dimensions_str(event),
            "related_info": related_info,
            "target_type": event.target_key.split("|")[0],
            "target_message": self.get_target_display(event),
            "title": title,
            "is_shield": event.is_shielded,
            "shield_type": event.shield_type,
            "data_type_label": event.origin_config["item_list"][0]["data_type_label"],
        }

        return result


class GetEventGraphView(AlarmPermissionResource):
    """
    查询事件视图
    """

    class RequestSerializer(serializers.Serializer):
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        event_id = serializers.IntegerField(label=_lazy("事件ID"), required=True)
        start_time = serializers.IntegerField(required=False, label=_lazy("开始时间"))
        end_time = serializers.IntegerField(required=False, label=_lazy("结束时间"))
        time_compare = serializers.IntegerField(
            label=_lazy("时间对比(小时)"),
            required=False,
        )

    def perform_request(self, params):
        current_params = {"bk_biz_id": params["bk_biz_id"], "id": params["event_id"]}
        if "start_time" in params and "end_time" in params:
            current_params["start_time"] = params["start_time"]
            current_params["end_time"] = params["end_time"]

        event_detail = resource.alert_events.detail_event(bk_biz_id=params["bk_biz_id"], id=params["event_id"])
        query_params = event_detail["graph_panel"]["targets"][0]["data"]
        query_params.update(current_params)
        time_compare = params.get("time_compare")

        query_params["function"] = {}
        if query_params.get("extend_metric_fields"):
            # 如果有多个指标数据，暂时不对曲线做降采样。  待支持：底层需要支持多个指标的降采样点需保持一致
            query_params["function"].update({"max_point_number": 0})

        compare_series_name = ""
        if time_compare:
            query_params["function"].update({"time_compare": ["{}h".format(time_compare)]})
            compare_series_name = hms_string(timedelta(hours=time_compare).total_seconds())
        result = resource.alert_events.event_graph_query(**query_params)

        # 计算statistics数据
        current_time = None
        for series in result:
            datapoints = series["datapoints"]
            points = [point[0] for point in datapoints if point[0] is not None]

            # 移动端图例名称精简
            if time_compare:
                series["target"] = _("当前") if series["time_offset"] == "current" else compare_series_name
            else:
                series["target"] = _("当前")

            # 获取当前值，取最新的点，历史数据取对应时间的点
            current = ""
            if current_time is None:
                # 查找最新的值不为None的点
                for point in reversed(datapoints):
                    if point[0] is None:
                        continue
                    # 记录该点的时间
                    current_time = point[1]
                    current = "{:g}".format(point[0])
                    break
                else:
                    current_time = 0
            elif current_time:
                # 查找对应时间的点
                for point in datapoints:
                    if point[1] == current_time and point[0] is not None:
                        current = "{:g}".format(point[0])

            series["statistics"] = {
                "min": "{:g}".format(min(points)) if points else "",
                "max": "{:g}".format(max(points)) if points else "",
                "avg": "{:g}".format(sum(points) / len(points)) if points else "",
                "current": current,
                "total": "{:g}".format(sum(points)),
            }

        return result


class GetEventList(AlarmPermissionResource, EventDimensionMixin, EventTargetMixin):
    """
    获取未恢复事件列表
    """

    class RequestSerializer(serializers.Serializer):
        level = serializers.IntegerField(label=_lazy("告警级别"), required=False)
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        type = serializers.ChoiceField(
            label=_lazy("分组类型"), default="strategy", choices=("strategy", "target", "shield")
        )
        only_count = serializers.BooleanField(label=_lazy("只看统计数量"), default=False)

    def group_by_strategy(self, events):
        """
        按策略分组展示
        :param events: 事件列表
        :type events: list(Event)
        :return: 展示结果
        """
        result = {}

        # 获取最新策略名
        strategies = StrategyModel.objects.filter(id__in=[event.strategy_id for event in events]).values("id", "name")
        strategy_names = {strategy["id"]: strategy["name"] for strategy in strategies}

        topo_links = None
        for event in events:
            # 如果策略已删除，则使用策略配置快照
            if event.strategy_id not in strategy_names:
                strategy_names[event.strategy_id] = event.origin_config.get("name", "")

            key = "{}|{}".format(event.strategy_id, event.level)
            # 如果不存在分组则初始化
            if key not in result:
                result[key] = {
                    "strategy_id": event.strategy_id,
                    "level": event.level,
                    "name": strategy_names[event.strategy_id],
                    "events": [],
                }

            # 获取事件标题，如果有目标则展示目标，否则展示维度
            if event.target_key:
                # 避免重复请求拓扑链
                if event.target_key.startswith("topo|") and not topo_links:
                    topo_tree = api.cmdb.get_topo_tree(bk_biz_id=event.bk_biz_id)
                    topo_links = topo_tree.convert_to_topo_link()

                title = self.get_target_display(event, topo_links)
            else:
                dimensions = self.get_dimensions(event)
                title = " ".join(
                    "{}={}".format(dimension["display_name"], dimension["display_value"]) for dimension in dimensions
                )

            result[key]["events"].append(
                {
                    "event_id": event.id,
                    "target": title,
                    "duration": hms_string(event.duration.total_seconds()),
                    "dimension_message": self.get_dimensions_str(event),
                }
            )

        return list(result.values())

    def group_by_target(self, events):
        """
        按监控目标分组展示
        :param events: 事件列表
        :type events: list(Event)
        :return: 展示结果
        """
        result = {}

        # 获取最新策略名
        strategies = StrategyModel.objects.filter(id__in=[event.strategy_id for event in events]).values("id", "name")
        strategy_names = {strategy["id"]: strategy["name"] for strategy in strategies}

        for event in events:
            # 如果策略已删除，则使用策略配置快照
            if event.strategy_id not in strategy_names:
                strategy_names[event.strategy_id] = event.origin_config.get("name", "")

            if not event.target_key:
                continue

            # 如果不存在分组则初始化
            key = self.get_target_display(event)
            if key not in result:
                result[key] = {"target": key, "events": []}

            result[key]["events"].append(
                {
                    "event_id": event.id,
                    "level": event.level,
                    "strategy_name": strategy_names[event.strategy_id],
                    "dimension_message": self.get_dimensions_str(event),
                }
            )

        return list(result.values())

    def perform_request(self, params):
        # 没有业务权限，使用接收人权限
        event_ids = None
        if "receiver" in params:
            event_ids = Event.objects.filter(
                status=Event.EventStatus.ABNORMAL,
                bk_biz_id=params["bk_biz_id"],
                end_time=Event.DEFAULT_END_TIME,
            ).values_list("event_id", flat=True)

            # 事件通知接收人过滤
            event_ids = (
                Alert.objects.filter(username=params["receiver"], event_id__in=event_ids)
                .values_list("event_id", flat=True)
                .distinct()
            )

        # 如果没有被通知的未恢复事件，则无数据
        if event_ids is not None and not event_ids:
            return {
                "count": {"strategy": 0, "target": 0, "shield": 0},
                "groups": [],
            }

        if params["only_count"]:
            groups = []
        else:
            event_params = {
                "status": Event.EventStatus.ABNORMAL,
                "is_shielded": params["type"] == "shield",
                "bk_biz_id": params["bk_biz_id"],
                "end_time": Event.DEFAULT_END_TIME,
            }

            # 是否按告警级别过滤
            if "level" in params:
                event_params["level"] = params["level"]

            events = Event.objects.filter(**event_params)

            if event_ids is not None:
                events = events.filter(event_id__in=event_ids)

            # 是否有告警目标
            if params["type"] == "target":
                events = events.exclude(target_key="")

            if params["type"] == "target":
                groups = list(self.group_by_target(events))
            else:
                groups = list(self.group_by_strategy(events))

        strategy_query = Event.objects.filter(
            is_shielded=False,
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=params["bk_biz_id"],
            end_time=Event.DEFAULT_END_TIME,
        )

        target_query = Event.objects.filter(
            is_shielded=False,
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=params["bk_biz_id"],
            end_time=Event.DEFAULT_END_TIME,
        ).exclude(target_key="")

        shield_query = Event.objects.filter(
            is_shielded=True,
            status=Event.EventStatus.ABNORMAL,
            bk_biz_id=params["bk_biz_id"],
            end_time=Event.DEFAULT_END_TIME,
        )

        if event_ids is not None:
            strategy_query = strategy_query.filter(event_id__in=event_ids)
            target_query = target_query.filter(event_id__in=event_ids)
            shield_query = shield_query.filter(event_id__in=event_ids)

        return {
            "count": {
                "strategy": strategy_query.count(),
                "target": target_query.count(),
                "shield": shield_query.count(),
            },
            "groups": groups,
        }


class AckEvent(AlarmPermissionResource):
    """
    基于告警汇总对事件进行批量确认
    """

    class RequestSerializer(serializers.Serializer):
        alert_collect_id = serializers.IntegerField(label=_lazy("告警汇总ID"))
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))

    def perform_request(self, params):
        alerts = Alert.objects.filter(alert_collect_id=params["alert_collect_id"])
        events = Event.objects.filter(event_id__in={alert.event_id for alert in alerts}, bk_biz_id=params["bk_biz_id"])

        event_actions = []
        for event in events:
            # 添加确认操作日志
            action_dict = {
                "username": get_request().user.username,
                "operate": EventAction.Operate.ACK,
                "extend_info": {"message": _("移动端确认")},
                "event_id": event.event_id,
            }
            event_actions.append(EventAction(**action_dict))

        events.update(is_ack=True)
        EventAction.objects.bulk_create(event_actions)


class QuickShield(Resource):
    """
    快速屏蔽事件
    """

    class RequestSerializer(serializers.Serializer):
        type = serializers.ChoiceField(label=_lazy("屏蔽类型"), choices=["scope", "strategy", "event"])
        event_id = serializers.IntegerField(label=_lazy("事件ID"))
        bk_biz_id = serializers.IntegerField(label=_lazy("业务ID"))
        end_time = serializers.DateTimeField(label=_lazy("屏蔽结束时间"), input_formats=["%Y-%m-%d %H:%M:%S"])
        description = serializers.CharField(label=_lazy("屏蔽描述"), allow_blank=True, default="")

    @staticmethod
    def handle_scope(event):
        """
        根据事件生成目标范围屏蔽参数
        """
        params = {
            "category": "scope",
        }

        if event.target_key.startswith("host|"):
            ip, bk_cloud_id = event.target_key.split("|")[1:]
            params["dimension_config"] = {"scope_type": "ip", "target": [{"ip": ip, "bk_cloud_id": bk_cloud_id}]}
        elif event.target_key.startswith("instance|"):
            service_instance_id = int(event.target_key.split("|")[1])
            params["dimension_config"] = {
                "scope_type": "instance",
                "target": [service_instance_id],
            }
        elif event.target_key.startswith("topo|"):
            bk_obj_id, bk_inst_id = event.target_key.split("|")[1:]
            params["dimension_config"] = {
                "scope_type": "topo",
                "target": [{"bk_obj_id": bk_obj_id, "bk_inst_id": bk_inst_id}],
            }
        return params

    @staticmethod
    def handle_strategy(event):
        """
        根据事件生成策略屏蔽参数
        """
        return {"category": "strategy", "dimension_config": {"id": [event.strategy_id]}}

    @staticmethod
    def handle_event(event):
        """
        根据事件生成事件屏蔽参数
        """
        return {"category": "event", "dimension_config": {"id": event.id}}

    def handle(self, params, event):
        """
        根据事件及屏蔽类型生成屏蔽参数
        """
        method_map = {
            "scope": self.handle_scope,
            "event": self.handle_event,
            "strategy": self.handle_strategy,
        }

        shield_params = {
            "end_time": params["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "begin_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": params["description"],
            "bk_biz_id": params["bk_biz_id"],
            "shield_notice": False,
            "cycle_config": {"begin_time": "", "type": 1, "end_time": ""},
            "is_quick": True,
        }

        shield_params.update(method_map[params["type"]](event))
        return shield_params

    def perform_request(self, params):
        try:
            event = Event.objects.get(id=params["event_id"], bk_biz_id=params["bk_biz_id"])
        except Event.DoesNotExist:
            raise EventNotFound(event_id=params["event_id"])

        return resource.shield.add_shield(self.handle(params, event))
