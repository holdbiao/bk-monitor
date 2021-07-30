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
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from bkmonitor.iam import ActionEnum
from bkmonitor.iam.drf import IAMPermissionMixin
from core.drf_resource import resource
from core.drf_resource.viewsets import ResourceViewSet, ResourceRoute
from monitor_web.data_explorer.serializers import QueryHistorySerializer, QueryHistoryListQuerySerializer
from monitor_web.models import QueryHistory


class QueryHistoryViewSet(IAMPermissionMixin, viewsets.ModelViewSet):
    iam_read_actions = ActionEnum.EXPLORE_METRIC
    iam_write_actions = ActionEnum.EXPLORE_METRIC

    queryset = QueryHistory.objects.all().order_by("-id")
    serializer_class = QueryHistorySerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        serializer = QueryHistoryListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        bk_biz_id = serializer.validated_data["bk_biz_id"]
        records = self.queryset.filter(bk_biz_id=bk_biz_id)

        response_serializer = self.get_serializer(records, many=True)
        return Response(response_serializer.data)


class DataExplorerViewSet(IAMPermissionMixin, ResourceViewSet):
    iam_read_actions = ActionEnum.EXPLORE_METRIC
    iam_write_actions = ActionEnum.EXPLORE_METRIC

    def get_iam_actions(self):
        if self.action == "get_graph_query_config":
            return [ActionEnum.EXPLORE_METRIC]
        if self.action == "save_panel_order":
            return [ActionEnum.MANAGE_HOST, ActionEnum.MANAGE_COLLECTION]
        return super(DataExplorerViewSet, self).get_iam_actions()

    resource_routes = [
        ResourceRoute("POST", resource.data_explorer.get_graph_query_config, endpoint="get_graph_query_config"),
        ResourceRoute("POST", resource.data_explorer.save_panel_order, endpoint="save_panel_order"),
        ResourceRoute("POST", resource.data_explorer.delete_panel_order, endpoint="delete_panel_order"),
    ]
