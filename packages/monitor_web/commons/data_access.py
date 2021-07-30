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


from django.conf import settings
from django.utils.translation import ugettext as _
from six.moves import map

from bkmonitor.utils.common_utils import safe_int
from core.drf_resource import api
from core.errors.api import BKAPIError
from monitor_web.plugin.constant import PluginType


class ResultTableField(object):
    FIELD_TYPE_FLOAT = ("double",)
    FIELD_TYPE_STRING = ("text",)

    def __init__(self, field_name, description, tag, field_type, unit="", is_config_by_user=True, alias_name=""):
        """
        field_name: 字段名
        description: 字段描述
        tag: metric 或 dimension 或 group
        field_type: 字段类型,metadata支持int,long,float,string,boolean,timestamp
        is_config_by_user:是否启用
        alias_name: 字段别名
        """
        self.field_name = field_name
        self.description = description
        self.tag = tag
        self.unit = unit
        self.is_config_by_user = is_config_by_user

        if field_type in self.FIELD_TYPE_FLOAT:
            self.field_type = "float"
        elif field_type in self.FIELD_TYPE_STRING:
            self.field_type = "string"
        else:
            self.field_type = field_type

        if alias_name:
            self.alias_name = alias_name


class ResultTable(object):
    def __init__(self, table_name, description, fields):
        self.table_name = table_name.lower()
        self.description = description
        self.fields = [field.__dict__ for field in fields]
        self.field_instance_list = fields

    @classmethod
    def new_result_table(cls, table_dict):
        """
        :param table_dict: 结果表存入数据库的格式
        {
            "fields":[
                {
                    "source_name":"",
                    "name":"collector",
                    "type":"string",
                    "monitor_type":"dimension",
                    "unit":"",
                    "description":"collector"
                },
            ],
            "table_name":"mysql_exporter_collector_duration_seconds",
            "table_desc":"mysql_exporter_collector_duration_seconds"
        }
        :return: ResultTable
        """
        fields = []
        for field in table_dict.get("fields", []):
            if field.get("is_active"):
                fields.append(
                    ResultTableField(
                        field_name=field["name"],
                        description=field.get("description") or field["name"],
                        tag=field["monitor_type"],
                        field_type=field["type"],
                        unit=field.get("unit", ""),
                    )
                )

        return cls(table_name=table_dict["table_name"], description=table_dict.get("table_desc", ""), fields=fields)


class DataAccessor(object):
    """
    申请数据链路资源
    """

    def __init__(self, bk_biz_id, db_name, tables, etl_config, operator, type_label, source_label, label):
        """
        :param bk_biz_id: 业务ID
        :param db_name: 数据库名
        :param tables: ResultTable列表
        :param etl_config: 清洗方式
        :param operator: 操作人
        """
        self.bk_biz_id = bk_biz_id
        self.db_name = db_name.lower()
        self.tables = tables
        self.operator = operator
        self.etl_config = etl_config
        self.modify = False
        # 获取table_id与table的映射关系
        self.tables_info = {self.get_table_id(table): table for table in self.tables}
        self.type_label = type_label
        self.source_label = source_label
        self.label = label
        try:
            self.data_id = self.get_data_id()
        except BKAPIError:
            self.data_id = None

    def get_table_id(self, table):
        """
        table_id:库.表(system.cpu)
        """
        return "{}.{}".format(self.tsdb_name, table.table_name)

    @property
    def tsdb_name(self):
        return "{}_{}".format(self.bk_biz_id, self.db_name) if self.bk_biz_id else self.db_name

    @property
    def data_name(self):
        # TODO: 新规范是业务ID在后，这个要确定影响范围
        return "{}_{}".format(self.bk_biz_id, self.db_name) if self.bk_biz_id else self.db_name

    def create_dataid(self):
        """
        创建/修改dataid
        """
        param = {
            "data_name": self.data_name,
            "etl_config": self.etl_config,
            "operator": self.operator,
            "data_description": self.data_name,
            "type_label": self.type_label,
            "source_label": self.source_label,
            # 新增入库时间
            "option": {"inject_local_time": True},
        }
        if self.etl_config == "bk_exporter":
            param["option"].update({"allow_dimensions_missing": True})
        self.data_id = api.metadata.create_data_id(param)["bk_data_id"]
        return self.data_id

    def contrast_rt(self):
        result_table_list = api.metadata.list_result_table(
            {"datasource_type": self.tsdb_name, "is_config_by_user": True}
        )
        new_table_id_set = {i for i in list(self.tables_info.keys())}

        old_table_id_set = set()
        for old_table in result_table_list:
            old_table_id = old_table["table_id"]
            old_table_id_set.add(old_table_id)
            if old_table_id not in new_table_id_set:
                self.tables_info[old_table_id] = ResultTable(
                    table_name=old_table_id.split(".")[-1],
                    description=old_table["table_name_zh"],
                    fields=[],
                )

        return {
            "create": new_table_id_set - old_table_id_set,
            "modify": new_table_id_set & old_table_id_set,
            "clean": old_table_id_set - new_table_id_set,
        }

    def create_rt(self):
        """
        创建结果表
        """
        create_rt_result_list = []
        contrast_result = self.contrast_rt()
        for operation in contrast_result:
            param = {
                "bk_data_id": self.data_id,
                "is_custom_table": True,
                "operator": self.operator,
                "schema_type": "free",
                "default_storage": "influxdb",
                "label": self.label,
            }
            for table_id in contrast_result[operation]:
                external_storage = {"kafka": {"expired_time": 1800000}}
                if settings.IS_ACCESS_BK_DATA:
                    external_storage["bkdata"] = {}
                param.update(
                    {
                        "bk_biz_id": self.bk_biz_id,
                        "table_id": table_id,
                        "table_name_zh": self.tables_info[table_id].description,
                        "field_list": self.tables_info[table_id].fields,
                        "external_storage": external_storage,
                    }
                )
                if operation == "create":
                    if self.etl_config == "bk_exporter":
                        param.update({"option": {"enable_default_value": False}})
                    create_rt_result = api.metadata.create_result_table(param)
                else:
                    create_rt_result = api.metadata.modify_result_table(param)

                create_rt_result_list.append(create_rt_result)

        return create_rt_result_list

    def access(self):
        """
        接入数据链路
        :return: 创建的 data id
        """
        if not self.data_id:
            self.create_dataid()

        self.create_rt()
        return self.data_id

    def get_data_id(self):
        data_id_info = api.metadata.get_data_id({"data_name": self.data_name})
        self.data_id = safe_int(data_id_info["data_id"])
        return self.data_id

    def modify_label(self, label):
        """
        修改label
        """
        result_table_list = api.metadata.list_result_table({"datasource_type": self.tsdb_name})
        for table in result_table_list:
            external_storage = {"kafka": {"expired_time": 1800000}}
            if settings.IS_ACCESS_BK_DATA:
                external_storage["bkdata"] = {}
            param = {
                "bk_data_id": self.data_id,
                "is_custom_table": True,
                "operator": self.operator,
                "schema_type": "free",
                "default_storage": "influxdb",
                "label": label,
                "bk_biz_id": self.bk_biz_id,
                "table_id": table["table_id"],
                "table_name_zh": table["table_name_zh"],
                "external_storage": external_storage,
            }
            api.metadata.modify_result_table(param)

        return "success"


class PluginDataAccessor(DataAccessor):
    def __init__(self, plugin_version, operator):
        def get_field_instance(field):
            # 将field字典转化为ResultTableField对象
            return ResultTableField(
                field_name=field["name"],
                tag=field["monitor_type"],
                field_type=field["type"],
                description=field.get("description", ""),
                unit=field.get("unit", ""),
                is_config_by_user=field.get("is_active", True),
                alias_name=field.get("source_name", ""),
            )

        metric_json = plugin_version.info.metric_json
        # 获取表结构信息
        tables = []

        add_fields = []
        add_fields_names = [
            ("bk_target_ip", _("目标IP")),
            ("bk_target_cloud_id", _("云区域ID")),
            ("bk_target_topo_level", _("拓扑层级")),
            ("bk_target_topo_id", _("拓扑ID")),
            ("bk_target_service_category_id", _("服务类别ID")),
            ("bk_target_service_instance_id", _("服务实例")),
            ("bk_collect_config_id", _("采集配置ID")),
        ]
        plugin_type = plugin_version.plugin.plugin_type
        if plugin_type == PluginType.SNMP:
            add_fields_names.append(("bk_target_device_ip", _("远程采集目标IP")))
        for name, description in add_fields_names:
            add_fields.append({"name": name, "description": description, "monitor_type": "group", "type": "string"})

        for table in metric_json:
            # 获取字段信息
            fields = list(
                map(
                    get_field_instance,
                    [i for i in table["fields"] if i["monitor_type"] == "dimension" or i.get("is_active")],
                )
            )
            fields.extend(list(map(get_field_instance, add_fields)))
            tables.append(ResultTable(table_name=table["table_name"], description=table["table_desc"], fields=fields))

        db_name = "{}_{}".format(plugin_type, plugin_version.plugin.plugin_id)
        etl_config = "bk_standard" if plugin_type in [PluginType.SCRIPT, PluginType.DATADOG] else "bk_exporter"
        super(PluginDataAccessor, self).__init__(
            bk_biz_id=0,
            db_name=db_name,
            tables=tables,
            etl_config=etl_config,
            operator=operator,
            type_label="time_series",
            source_label="bk_monitor",
            label=plugin_version.plugin.label,
        )


class EventDataAccessor(object):
    def __init__(self, current_version, operator):
        self.bk_biz_id = current_version.plugin.bk_biz_id
        self.name = "{}_{}".format(current_version.plugin.plugin_type, current_version.plugin_id)
        self.label = current_version.plugin.label
        self.operator = operator

    def get_data_id(self):
        data_id_info = api.metadata.get_data_id({"data_name": "{}_{}".format(self.name, self.bk_biz_id)})
        return safe_int(data_id_info["bk_data_id"])

    def create_data_id(self, source_label, type_label):
        data_name = "{}_{}".format(self.name, self.bk_biz_id)
        try:
            data_id_info = api.metadata.get_data_id({"data_name": data_name})
        except BKAPIError:
            param = {
                "data_name": data_name,
                "etl_config": "bk_standard_v2_event",
                "operator": self.operator,
                "data_description": data_name,
                "type_label": type_label,
                "source_label": source_label,
                "option": {"inject_local_time": True},
            }
            data_id_info = api.metadata.create_data_id(param)
        bk_data_id = data_id_info["bk_data_id"]
        return bk_data_id

    def create_result_table(self, bk_data_id, event_info_list):
        params = {
            "operator": self.operator,
            "bk_data_id": bk_data_id,
            "bk_biz_id": self.bk_biz_id,
            "event_group_name": self.name,
            # 目前metadata中米有hardware标签
            "label": self.label,
            "event_info_list": event_info_list,
        }
        group_info = api.metadata.create_event_group(params)
        return group_info

    def modify_result_table(self, event_info_list):
        event_groups = api.metadata.query_event_group(event_group_name=self.name)
        if event_groups:
            event_group_id = event_groups[0]["event_group_id"]
            params = {
                "operator": self.operator,
                "event_group_id": event_group_id,
                "event_info_list": event_info_list,
            }
            params = {key: value for key, value in params.items() if value is not None}
            group_info = api.metadata.modify_event_group(params)
            return group_info
        raise Exception(_("结果表不存在，请确认后重试"))

    def delete_result_table(self):
        event_groups = api.metadata.query_event_group(event_group_name=self.name)
        if event_groups:
            event_group_id = event_groups[0]["event_group_id"]
            api.metadata.delete_event_group(event_group_id=event_group_id, operator=self.operator)
            return event_group_id
