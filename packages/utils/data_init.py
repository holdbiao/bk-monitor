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
from bkmonitor.utils.common_utils import safe_int
from monitor.models import ScriptCollectorConfig, LogCollector, ExporterComponent

SCRIPT_DATA_NAME = "selfscript"
LOG_DATA_NAME = "slog"
COMPONENT_DATA_NAME = "exporter"


def _get_script_custom_data():
    """
    获取脚本表自定义表结构数据
    :return:
    """
    result_data = {"datasource_list": [], "result_table_list": []}
    all_script_config = ScriptCollectorConfig.objects.all()
    for config in all_script_config:
        if not config.data_id:
            continue

        datasource = {
            "data_id": config.data_id,  # 数据源ID
            "data_name": "{}_{}".format(SCRIPT_DATA_NAME, config.name),
            "etl": "bk_standard",  # 数据源清洗方案，exportor(采集器) 或 standard(标准方案)
            "operator": config.update_user,
            "bk_biz_id": config.bk_biz_id,
        }
        result_table = {
            "bk_biz_id": config.bk_biz_id,  # 业务ID
            "data_id": config.data_id,
            "table_id": "{}.{}".format(SCRIPT_DATA_NAME, config.name),
            "table_name_zh": config.description,
            "field_list": [],
            "operator": config.update_user,
        }
        for field in config.fields:
            result_table["field_list"].append(
                {
                    "field_type": field["type"],
                    "field_name": field["name"],
                    "is_dimension": field["monitor_type"] == "dimension",
                    "description": field["description"],
                    "unit": field.get("unit", ""),
                }
            )

        result_data["datasource_list"].append(datasource)
        result_data["result_table_list"].append(result_table)

    return result_data


def _get_log_custom_data():
    """
    获取日志表自定义表结构数据
    :return:
    """
    result_data = {"datasource_list": [], "result_table_list": []}
    all_log_config = LogCollector.objects.all()
    for config in all_log_config:
        if not config.data_id:
            continue

        datasource = {
            "data_id": safe_int(config.data_id),  # 数据源ID
            "data_name": "{}_{}".format(LOG_DATA_NAME, config.data_set),
            "etl": "bk_standard",  # 数据源清洗方案，exportor(采集器) 或 standard(标准方案)
            "operator": config.update_user,
            "bk_biz_id": config.biz_id,
        }
        result_table = {
            "bk_biz_id": config.biz_id,  # 业务ID
            "data_id": safe_int(config.data_id),
            "table_id": "{}.{}".format(LOG_DATA_NAME, config.data_set),
            "table_name_zh": config.data_desc,
            "field_list": [],
            "operator": config.update_user,
        }
        for field in config.fields:
            if not field["time_format"]:
                result_table["field_list"].append(
                    {
                        "field_type": field["type"],
                        "field_name": field["name"],
                        "is_dimension": field["type"] in ["string", "text"],
                        "description": field["description"],
                        "unit": "",
                    }
                )

        result_data["datasource_list"].append(datasource)
        result_data["result_table_list"].append(result_table)

    return result_data


def _get_component_custom_data():
    """
    获取组件表自定义表结构数据
    :return:
    """
    result_data = {"datasource_list": [], "result_table_list": []}
    all_component_config = ExporterComponent.objects.all()
    for config in all_component_config:
        if not config.data_id:
            continue

        datasource = {
            "data_id": config.data_id,  # 数据源ID
            "data_name": "{}_{}".format(COMPONENT_DATA_NAME, config.component_name),
            "etl": "bk_exporter",  # 数据源清洗方案，exportor(采集器) 或 standard(标准方案)
            "operator": config.update_user,
            "bk_biz_id": config.biz_id,
        }
        for table in config.indices:
            result_table = {
                "bk_biz_id": config.biz_id,  # 业务ID
                "data_id": config.data_id,
                "table_id": "{}_{}.{}".format(COMPONENT_DATA_NAME, config.component_name, table["table_name"]),
                "table_name_zh": table["table_desc"],
                "field_list": [],
                "operator": config.update_user,
            }
            for field in table["fields"]:
                result_table["field_list"].append(
                    {
                        "field_type": field["type"],
                        "field_name": field["name"],
                        "is_dimension": field["monitor_type"] == "dimension",
                        "description": field["description"],
                        "unit": field.get("unit", ""),
                    }
                )

            result_data["result_table_list"].append(result_table)

        result_data["datasource_list"].append(datasource)

    return result_data


def get_all_custom_data():
    script = _get_script_custom_data()
    log = _get_log_custom_data()
    component = _get_component_custom_data()
    return {
        "datasource_list": script["datasource_list"] + log["datasource_list"] + component["datasource_list"],
        "result_table_list": script["result_table_list"] + log["result_table_list"] + component["result_table_list"],
    }
