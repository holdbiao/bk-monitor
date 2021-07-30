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
#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging

from django.db import migrations
from django.db import models as django_model

from metadata import config

logger = logging.getLogger("metadata")

models = {
    "ClusterInfo": None,
    "DataSource": None,
    "ResultTableField": None,
    "ResultTable": None,
    "DataSourceResultTable": None,
    "KafkaTopicInfo": None,
    "InfluxDBStorage": None,
}


def init_data(apps, schema_editor):
    for model_name in list(models.keys()):
        models[model_name] = apps.get_model("metadata", model_name)

    # 1. 获取所有的数据
    try:
        from utils.data_init import get_all_custom_data

        init_data = get_all_custom_data()
    except Exception:
        init_data = {"datasource_list": [], "result_table_list": []}

    # 2. 写入datasource信息
    kafka_cluster = models["ClusterInfo"].objects.get(cluster_type="kafka")
    influx_cluster = models["ClusterInfo"].objects.get(cluster_type="influxdb")

    data_source_list = init_data["datasource_list"]

    for data_source in data_source_list:
        if data_source["data_id"] >= 1048576:
            continue

        data_object = models["DataSource"].objects.create(
            bk_data_id=data_source["data_id"],
            data_name="{}_{}".format(data_source["data_name"], data_source["bk_biz_id"]),
            etl_config=data_source["etl"],
            creator=data_source["operator"],
            mq_cluster_id=kafka_cluster.cluster_id,
            is_custom_source=True,
            data_description="Trans data from SaaS for data_set->[%s]" % data_source["data_name"],
            # 由于mq_config和data_source两者相互指向对方，所以只能先提供占位符，先创建data_source
            mq_config_id=0,
            last_modify_user=data_source["operator"],
        )

        # 获取这个数据源对应的配置记录model，并创建一个新的配置记录
        mq_config = models["KafkaTopicInfo"].objects.create(
            bk_data_id=data_object.bk_data_id,
            topic="{}{}0".format(config.KAFKA_TOPIC_PREFIX, data_object.bk_data_id),
            partition=1,
        )
        data_object.mq_config_id = mq_config.id
        data_object.save()

    # 3. 写入结果表信息
    result_table_list = init_data["result_table_list"]
    for result_table in result_table_list:
        if result_table["data_id"] >= 1048576:
            continue

        # 创建字段准备
        field_list = []
        for field in result_table["field_list"]:
            if field["field_type"] == "timestamp":
                continue
            field_type = field["field_type"] if field["field_type"] != "long" else "int"

            # 判断字段的类型： dimension, metric, timestamp
            if field["is_dimension"]:
                field_tag = "dimension"

            else:
                field_tag = "metric"

            field_list.append(
                {
                    "field_name": field["field_name"],
                    "field_type": field_type,
                    "operator": result_table["operator"],
                    "is_config_by_user": True,
                    "tag": field_tag,
                    "unit": field["unit"],
                    "description": field["description"],
                }
            )

        # 追加时间、bk_biz_id和供应商的字段
        field_list.append(
            {
                "field_name": "bk_biz_id",
                "field_type": "int",
                "operator": result_table["operator"],
                "is_config_by_user": True,
                "tag": "dimension",
                "description": "业务ID",
            }
        )

        field_list.append(
            {
                "field_name": "bk_supplier_id",
                "field_type": "int",
                "operator": result_table["operator"],
                "is_config_by_user": True,
                "tag": "dimension",
                "description": "开发商ID",
            }
        )

        field_list.append(
            {
                "field_name": "bk_cloud_id",
                "field_type": "int",
                "operator": result_table["operator"],
                "is_config_by_user": True,
                "tag": "dimension",
                "description": "云区域ID",
            }
        )

        field_list.append(
            {
                "field_name": "time",
                "field_type": "timestamp",
                "operator": result_table["operator"],
                "is_config_by_user": True,
                "tag": "",
                "description": "数据上报时间",
            }
        )

        field_list.append(
            {
                "field_name": "ip",
                "field_type": "string",
                "operator": result_table["operator"],
                "is_config_by_user": True,
                "tag": "dimension",
                "description": "采集器IP地址",
            }
        )

        # 创建结果表
        result_table_object = models["ResultTable"].objects.create(
            table_id="{}_{}".format(result_table["bk_biz_id"], result_table["table_id"]),
            table_name_zh=result_table["table_name_zh"],
            is_custom_table=True,
            schema_type="free",
            default_storage=result_table.get("default_storage", "influxdb"),
            creator=result_table["operator"],
            last_modify_user=result_table["operator"],
            bk_biz_id=result_table["bk_biz_id"],
        )

        # 3. 创建新的字段信息，同时追加默认的字段
        for field_info in field_list:
            models["ResultTableField"].objects.create(
                table_id=result_table_object.table_id,
                field_name=field_info["field_name"],
                field_type=field_info["field_type"],
                unit=field_info.get("unit", ""),
                tag=field_info["tag"],
                is_config_by_user=True,
                default_value=None,
                creator=result_table["operator"],
                description=field_info["description"],
            )

        # 4. 创建data_id和该结果表的关系
        models["DataSourceResultTable"].objects.create(
            bk_data_id=result_table["data_id"], table_id=result_table_object.table_id, creator=result_table["operator"]
        )

        # 5. 创建实际结果表记录
        database, table_name = result_table_object.table_id.split(".")
        models["InfluxDBStorage"].objects.create(
            table_id=result_table_object.table_id,
            storage_cluster_id=influx_cluster.cluster_id,
            database=database,
            real_table_name=table_name,
            source_duration_time="90d",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0006_auto_20190321_1443"),
    ]

    operations = [
        # 增加业务ID字段信息
        migrations.AddField(
            model_name="resulttable",
            name="bk_biz_id",
            field=django_model.IntegerField(default=0, verbose_name="\u7ed3\u679c\u8868\u6240\u5c5e\u4e1a\u52a1"),
        ),
        migrations.RunPython(init_data),
    ]
