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


import json
import os

from api.metadata.default import GetLabelResource, GetResultTableResource, ListResultTableResource
from core.errors.api import BKAPIError
from core.fake_esb_api.register import register

Path = os.path.dirname(__file__)


def read(name):
    dir_path = os.path.dirname(__file__)
    file_path = os.path.join(dir_path, "{}.json".format(name))
    with open(file_path, "r") as f:
        return json.loads(f.read())


@register
def get_label(params=None, **kwargs):
    """
    项目中只用到了result_table_type因此返回数据固定，需要时再补充
    """
    params = params or kwargs
    serializer = GetLabelResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    return read("label")


@register
def get_result_table(params=None, **kwargs):
    params = params or kwargs
    serializer = GetResultTableResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data
    data = read("result_table")

    for result_table in data:
        if result_table["table_id"] == params["table_id"]:
            return result_table

    raise BKAPIError(system_name="metadata", result="ResultTable matching query does not exist.")


@register
def list_result_table(params=None, **kwargs):
    params = params or kwargs
    serializer = ListResultTableResource.RequestSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data

    bk_biz_id = params.get("bk_biz_id")
    datasource_type = params.get("datasource_type")
    is_public_include = params.get("is_public_include")

    result_tables = read("result_table")

    if bk_biz_id is not None:
        result_tables = [
            result_table
            for result_table in result_tables
            if result_table["bk_biz_id"] == bk_biz_id or (result_table["bk_biz_id"] == 0 and is_public_include)
        ]

    if datasource_type is not None:
        result_tables = [
            result_table for result_table in result_tables if result_table["table_id"].split(".")[0] == datasource_type
        ]

    return result_tables
