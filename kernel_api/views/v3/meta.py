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


from core.drf_resource.viewsets import ResourceRoute, ResourceViewSet
from bkmonitor.views.renderers import MonitorJSONRenderer
from metadata import resource

RENDER_CLASSES = [MonitorJSONRenderer]


class MetaViewSet(ResourceViewSet):

    renderer_classes = RENDER_CLASSES


class CreateDataIDViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.CreateDataIDResource)]


class ModifyDataIDViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.ModifyDataSource)]


class ResultTableViewSet(MetaViewSet):

    resource_routes = [
        ResourceRoute("POST", resource.CreateResultTableResource),
        ResourceRoute("GET", resource.ListResultTableResource),
    ]


class ModifyResultTableViewSet(MetaViewSet):

    resource_routes = [
        ResourceRoute("POST", resource.ModifyResultTableResource),
    ]


class AccessBkDataByResultTableViewSet(MetaViewSet):

    resource_routes = [
        ResourceRoute("POST", resource.AccessBkDataByResultTableResource),
    ]


class CreateDownSampleDataFlowViewSet(MetaViewSet):

    resource_routes = [
        ResourceRoute("POST", resource.CreateDownSampleDataFlowResource),
    ]


class GetDataIDViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.QueryDataSourceResource)]


class GetResultTableViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.QueryResultTableSourceResource)]


class UpgradeResultTableViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.UpgradeResultTableResource)]


class FullCmdbNodeInfoViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("POST", resource.FullCmdbNodeInfoResource)]


class CreateResultTableMetricSplitViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.CreateResultTableMetricSplitResource)]


class CleanResultTableMetricSplitViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.CleanResultTableMetricSplitResource)]


class LabelViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.LabelResource)]


class GetResultTableStorageViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.GetResultTableStorageResult)]


class CreateClusterInfoViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.CreateClusterInfoResource)]


class ModifyClusterInfoViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.ModifyClusterInfoResource)]


class GetClusterInfoViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.QueryClusterInfoResource)]


class QueryEventGroupViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("GET", resource.QueryEventGroupResource)]


class CreateEventGroupViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.CreateEventGroupResource)]


class ModifyEventGroupViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.ModifyEventGroupResource)]


class DeleteEventGroupViewSet(MetaViewSet):

    resource_routes = [ResourceRoute("POST", resource.DeleteEventGroupResource)]


class GetEventGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.GetEventGroupResource)]


class GetTimeSeriesMetricsViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.GetTimeSeriesMetricsResource)]


class CreateTimeSeriesGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("POST", resource.CreateTimeSeriesGroupResource)]


class ModifyTimeSeriesGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("POST", resource.ModifyTimeSeriesGroupResource)]


class DeleteTimeSeriesGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("POST", resource.DeleteTimeSeriesGroupResource)]


class GetTimeSeriesGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.GetTimeSeriesGroupResource)]


class QueryTimeSeriesGroupViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.QueryTimeSeriesGroupResource)]


class QueryTagValuesViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.QueryTagValuesResource)]


class ListTransferClusterViewSet(MetaViewSet):
    resource_routes = [ResourceRoute("GET", resource.ListTransferClusterResource)]
