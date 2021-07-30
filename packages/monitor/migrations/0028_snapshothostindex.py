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


from django.db import migrations, models

init_sql = """
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (3,'cpu','load5','double','system_load','5分钟平均负载（乘以100）','',0.01,'','system.load.load5');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (7,'cpu','usage','double','system_cpu_summary','CPU总使用率','',1,'%','system.cpu_summary.usage');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (8,'cpu','usage','double','system_cpu_detail','CPU单核使用率','device_name',1,'%','system.cpu_detail.usage');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (10,'net','speedRecv','double','system_net','接收字节流量','device_name',1024,'KB/s','system.net.speedRecv');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (14,'net','speedSent','double','system_net','发送字节流量','device_name',1024,'KB/s','system.net.speedSent');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (16,'net','speedPacketsSent','double','system_net','发送包速率','device_name',1,'个/s','system.net.speedPacketsSent');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (20,'net','speedPacketsRecv','double','system_net','接收包速率','device_name',1,'个/s','system.net.speedPacketsRecv');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (60,'mem','free','int','system_mem','可用物理内存','',1048576,'MB','system.mem.free');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (63,'mem','used','int','system_swap','交换分区已用量','',1024,'MB','system.swap.used');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (64,'mem','psc_pct_used','double','system_mem','内存使用率','',1,'%','system.mem.psc_pct_used');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (81,'disk','in_use','float','system_disk','已用空间占比','device_name',1,'%','system.disk.in_use');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (86,'disk','r_s','double','system_io','读速率','device_name',1,'次/秒','system.io.r_s');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (87,'disk','w_s','double','system_io','写速率','device_name',1,'次/秒','system.io.w_s');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (96,'disk','util','double','system_io','磁盘IO使用率','device_name',0.01,'%','system.io.util');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (97,'mem','psc_used','int','system_mem','已用物理内存','',1048576,'MB','system.mem.psc_used');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (98,'mem','used','int','system_mem','应用内存使用量','',1048576,'MB','system.mem.used');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (99,'mem','pct_used','int','system_mem','应用内存使用率','',1,' %','system.mem.pct_used');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (110,'net','cur_tcp_estab','int','system_netstat','established连接数','',1,'','system.netstat.cur_tcp_estab');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (111,'net','cur_tcp_timewait','int','system_netstat','time_wait连接数','',1,'','system.netstat.cur_tcp_timewait');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (112,'net','cur_tcp_listen','int','system_netstat','listen连接数','',1,'','system.netstat.cur_tcp_listen');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (113,'net','cur_tcp_lastack','int','system_netstat','last_ack连接数','',1,'','system.netstat.cur_tcp_lastack');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (114,'net','cur_tcp_syn_recv','int','system_netstat','syn_recv连接数','',1,'','system.netstat.cur_tcp_syn_recv');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (115,'net','cur_tcp_syn_sent','int','system_netstat','syn_sent连接数','',1,'','system.netstat.cur_tcp_syn_sent');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (116,'net','cur_tcp_finwait1','int','system_netstat','fin_wait1连接数','',1,'','system.netstat.cur_tcp_finwait1');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (117,'net','cur_tcp_finwait2','int','system_netstat','fin_wait2连接数','',1,'','system.netstat.cur_tcp_finwait2');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (118,'net','cur_tcp_closing','int','system_netstat','closing连接数','',1,'','system.netstat.cur_tcp_closing');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (119,'net','cur_tcp_closed','int','system_netstat','closed状态连接数','',1,'','system.netstat.cur_tcp_closed');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (120,'net','cur_udp_indatagrams','int','system_netstat','UDP接收包量','',1,'','system.netstat.cur_udp_indatagrams');
INSERT INTO `app_snapshot_host_index` (`id`,`category`,`item`,`type`,`result_table_id`,`description`,`dimension_field`,`conversion`,`conversion_unit`,`metric`) VALUES (121,'net','cur_udp_outdatagrams','int','system_netstat','UDP发送包量','',1,'','system.netstat.cur_udp_outdatagrams');
"""


class Migration(migrations.Migration):

    dependencies = [
        ("monitor", "0027_alarmstrategy_metric_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="SnapshotHostIndex",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("category", models.CharField(max_length=32)),
                ("item", models.CharField(max_length=32)),
                ("type", models.CharField(max_length=32)),
                ("result_table_id", models.CharField(max_length=128)),
                ("description", models.CharField(max_length=50)),
                ("dimension_field", models.CharField(max_length=32)),
                ("conversion", models.FloatField()),
                ("conversion_unit", models.CharField(max_length=32)),
                ("metric", models.CharField(max_length=128, null=True, blank=True)),
            ],
            options={
                "db_table": "app_snapshot_host_index",
            },
        ),
        migrations.RunSQL(init_sql),
    ]
