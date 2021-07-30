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


class ResultTableType(object):
    # 新链路老表(3.2版本不再使用的表)
    OLD_BK_MONITOR = "OLD_BK_MONITOR"
    # 新链路新表(3.2版本仍在使用的表)
    NEW_BK_MONITOR = "NEW_BK_MONITOR"
    # 计算平台表
    BK_DATA = "BK_DATA"


def classify_result_table(rt_id):
    """
    根据结果表ID识别结果表类型
    :param rt_id: 结果表ID，例如 "2_exporter_rabbitmq"
    :return: ResultTableType, metric_id
    """
    bk_biz_id, db_table = rt_id.split("_", 1)
    if bk_biz_id.isdigit():
        # 如果是以业务ID开头，那么第二位则为DB类型
        db_name = db_table.split("_", 1)[0]
    else:
        # 如果是不以业务ID开头，那么第一位则为DB类型
        db_name = bk_biz_id
        db_table = rt_id

    if db_name in ["selfscript", "slog", "tomcat", "apache", "redis", "nginx", "mysql"]:
        # 新链路老表(3.2版本不再使用的表)
        metric_id_prefix = ".".join(db_table.split("_"))
        rt_type = ResultTableType.OLD_BK_MONITOR
    elif db_name in ["exporter"]:
        part1, part2, part3 = db_table.split("_", 2)
        metric_id_prefix = "exporter_{}.{}".format(part2, part3)
        rt_type = ResultTableType.OLD_BK_MONITOR
    elif db_name in ["system", "uptimecheck"]:
        # 新链路新表(3.2版本仍在使用的表)
        metric_id_prefix = ".".join(db_table.split("_", 1))
        rt_type = ResultTableType.NEW_BK_MONITOR
    else:
        # 其余都是计算平台表
        metric_id_prefix = rt_id
        rt_type = ResultTableType.BK_DATA
    return rt_type, metric_id_prefix
