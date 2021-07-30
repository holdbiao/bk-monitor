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


from collections import OrderedDict

from django.conf import settings
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers as slz

ADVANCED_OPTIONS = OrderedDict(
    [
        ("QOS_FLOW_CONTROL_WINDOW", slz.IntegerField(label=_("流控窗口"), default=30)),
        ("QOS_DROP_ALARM_THREADHOLD", slz.IntegerField(label=_("流控丢弃阈值"), default=3)),
        ("QOS_MATCH_QUEUE_MAX_SIZE", slz.IntegerField(label=_("匹配队列流控触发阈值"), default=1000)),
        ("QOS_MATCH_QUEUE_MIN_SIZE", slz.IntegerField(label=_("匹配队列流控停止阈值"), default=300)),
        ("QOS_CONVERGE_QUEUE_MAX_SIZE", slz.IntegerField(label=_("收敛队列流控触发阈值"), default=10000)),
        ("QOS_CONVERGE_QUEUE_MIN_SIZE", slz.IntegerField(label=_("收敛队列流控停止阈值"), default=5000)),
        ("QOS_COLLECT_QUEUE_MAX_SIZE", slz.IntegerField(label=_("汇总队列流控触发阈值"), default=1000)),
        ("QOS_COLLECT_QUEUE_MIN_SIZE", slz.IntegerField(label=_("汇总队列流控停止阈值"), default=500)),
        ("SAAS_APP_CODE", slz.CharField(label=_("SAAS 应用码"), default=settings.APP_CODE)),
        ("SAAS_SECRET_KEY", slz.CharField(label=_("SAAS 应用密钥"), default=settings.SECRET_KEY)),
        ("IS_ASSIGN_DATAID_BY_GSE", slz.BooleanField(label=_("是否由GSE分配dataid"), default=False)),
        ("COLLECT_ALARM_THRESHOLD", slz.IntegerField(label=_("汇总触发阈值（告警数）"), default=2, min_value=0)),
        ("CELERY_WORKERS", slz.IntegerField(label=_("后台处理队列的子进程数（需重启scheduler:*）"), default=0, min_value=0)),
        ("HEALTHZ_ALARM_CONFIG", slz.JSONField(label=_("healthz告警配置"), default={}, binary=True)),
        ("SELF_MONITORING_SWITCH", slz.BooleanField(label=_("全局自监控告警开关"), default=True)),
        ("ENABLE_MESSAGE_QUEUE", slz.BooleanField(label=_("是否开启告警通知队列"), default=True)),
        ("ENABLE_RESOURCE_DATA_COLLECT", slz.BooleanField(label=_("是否开启Resource数据收集"), default=False)),
        ("RESOURCE_DATA_COLLECT_RATIO", slz.IntegerField(label=_("Resource数据采样率"), default=0)),
        ("DIMENSION_COLLECT_THRESHOLD", slz.IntegerField(label=_("同维度汇总阈值"), default=2)),
        ("DIMENSION_COLLECT_WINDOW", slz.IntegerField(label=_("同维度汇总时间窗口"), default=120)),
        ("MULTI_STRATEGY_COLLECT_THRESHOLD", slz.IntegerField(label=_("多策略汇总阈值"), default=3)),
        ("MULTI_STRATEGY_COLLECT_WINDOW", slz.IntegerField(label=_("多策略汇总时间窗口"), default=120)),
        ("UPGRADE_ALLOWED", slz.BooleanField(label=_("是否开启升级页面"), default=True)),
        ("WEBHOOK_TIMEOUT", slz.IntegerField(label=_("Webhook超时时间"), default=3)),
        ("ENABLE_DEFAULT_STRATEGY", slz.BooleanField(label=_("是否开启默认策略"), default=True)),
        ("IS_ACCESS_BK_DATA", slz.BooleanField(label=_("是否开启与计算平台的功能对接"), default=False)),
        ("IS_ENABLE_VIEW_CMDB_LEVEL", slz.BooleanField(label=_("是否开启前端视图部分的CMDB预聚合"), default=False)),
        ("AIOPS_BIZ_WHITE_LIST", slz.ListField(label=_("开启智能异常算法的业务白名单"), default=[])),
        ("BK_DATA_PROJECT_ID", slz.IntegerField(label=_("监控在计算平台使用的公共项目ID"), default=0)),
        ("BK_DATA_BK_BIZ_ID", slz.IntegerField(label=_("监控在计算平台使用的公共业务ID"), default=0)),
        (
            "BK_DATA_RT_ID_PREFIX",
            slz.CharField(label=_("监控在计算平台的数据表前缀(prefix)"), default=settings.BKAPP_DEPLOY_PLATFORM),
        ),
        ("BK_DATA_PROJECT_MAINTAINER", slz.CharField(label=_("计算平台项目的维护人员"), default="")),
        ("BK_DATA_DATA_EXPIRES_DAYS", slz.IntegerField(label=_("计算平台中结果表默认保存天数"), default=30)),
        ("BK_DATA_KAFKA_BROKER_URL", slz.CharField(label=_("与计算平台对接的消息队列BROKER地址"), default="")),
        ("BK_DATA_INTELLIGENT_DETECT_MODEL_ID", slz.CharField(label=_("计算平台通用智能异常检测算法ID"), default="")),
        ("BK_DATA_INTELLIGENT_DETECT_DELAY_WINDOW", slz.IntegerField(label=_("数据接入计算平台后dataflow延时时间"), default=5)),
        ("EVENT_NO_DATA_TOLERANCE_WINDOW_SIZE", slz.IntegerField(label=_("Event 模块最大容忍无数据周期数"), default=5)),
        (
            "ANOMALY_RECORD_COLLECT_WINDOW",
            slz.IntegerField(label=_("单事件异常点清理触发计数"), default=100),
        ),
        ("SAAS_VERSION", slz.CharField(label=_("SaaS版本号"), default="unknown")),
        ("BACKEND_VERSION", slz.CharField(label=_("Backend版本号"), default="unknown")),
        ("WXWORK_BOT_WEBHOOK_URL", slz.CharField(label=_("企业微信机器人回调地址"), default="", allow_blank=True)),
        ("ACCESS_TIME_PER_WINDOW", slz.IntegerField(label=_("access模块策略拉取耗时限制（每10分钟）"), default=30)),
        ("RSA_PRIVATE_KEY", slz.CharField(label=_("RSA PRIVATE KEY"), default=settings.RSA_PRIVATE_KEY)),
        ("SKIP_PLUGIN_DEBUG", slz.BooleanField(label=_("跳过插件调试"), default=False)),
        ("BKUNIFYLOGBEAT_METRIC_BIZ", slz.IntegerField(label=_("日志采集器指标所属业务"), default=0)),
        ("EVENT_RELATED_INFO_LENGTH", slz.IntegerField(label=_("事件关联信息截断长度"), default=1024)),
        (
            "NOTICE_MESSAGE_MAX_LENGTH",
            slz.DictField(label=_("各渠道通知消息最大长度"), default={"sms": 140, "rtx": 4000, "wxwork-bot": 5120}),
        ),
    ]
)

STANDARD_CONFIGS = OrderedDict(
    [
        ("ENABLE_PING_ALARM", slz.BooleanField(label=_("全局 Ping 告警开关"), default=True)),
        ("ENABLE_AGENT_ALARM", slz.BooleanField(label=_("全局 Agent失联 告警开关"), default=True)),
        ("ALARM_MOBILE_NOTICE_WAY", slz.ListField(label=_("是否在微信消息中推送移动端访问链接"), default=[])),
        ("ALARM_MOBILE_URL", slz.CharField(label=_("移动端告警访问链接"), default="")),
        (
            "FILE_SYSTEM_TYPE_IGNORE",
            slz.ListField(
                label=_("全局磁盘类型屏蔽配置"), default=["iso9660", "tmpfs", "udf"], help_text=_("可通过该配置屏蔽指定类型的磁盘的告警")
            ),
        ),
        (
            "ANOMALY_RECORD_SAVE_DAYS",
            slz.IntegerField(
                label=_("异常记录保留天数"),
                default=30,
                min_value=1,
                help_text=_("异常记录表用于展示告警事件的收敛记录，清理后会导致历史事件的流转记录展示不全。" "后台每分钟都会对过期异常记录进行清理，每次清理不超过 1000 条。"),
            ),
        ),
        ("GRAPH_WATERMARK", slz.BooleanField(label=_("显示图表水印"), default=True, help_text=_("开启后，页面上的数据图表将带上当前用户名的水印"))),
        ("ENABLED_NOTICE_WAYS", slz.ListField(label=_("告警通知渠道"), default=["weixin", "mail", "sms", "voice"])),
        (
            "MESSAGE_QUEUE_DSN",
            slz.CharField(
                label=_("告警通知消息队列DSN"),
                default="",
                allow_blank=True,
                help_text=_('例如 "redis://:${passowrd}@${host}:${port}/${db}/${key}" ，' "注意用户名和密码需要进行 urlencode"),
            ),
        ),
        (
            "TS_DATA_SAVED_DAYS",
            slz.IntegerField(
                label=_("监控采集数据保存天数"),
                default=30,
                min_value=1,
                help_text=_("采集上报数据在influxdb的保留天数，" "超出保留天数的将被清理。数值越大对存储资源要求越高"),
            ),
        ),
        (
            "MESSAGE_QUEUE_MAX_LENGTH",
            slz.IntegerField(label=_("通知消息队列长度上限"), default=0, help_text=_("若队列长度超出该值，则丢弃旧消息。值为 0 代表无长度限制")),
        ),
        ("LINUX_GSE_AGENT_PATH", slz.CharField(label=_("Linux Agent 安装路径"), default="/usr/local/gse/")),
        ("LINUX_PLUGIN_DATA_PATH", slz.CharField(label=_("Linux 数据保存路径"), default="/var/lib/gse")),
        ("LINUX_PLUGIN_PID_PATH", slz.CharField(label=_("Linux PID 文件保存路径"), default="/var/run/gse")),
        ("LINUX_PLUGIN_LOG_PATH", slz.CharField(label=_("Linux 日志保存路径"), default="/var/log/gse")),
        ("LINUX_GSE_AGENT_IPC_PATH", slz.CharField(label=_("Linux IPC 路径"), default="/var/run/ipc.state.report")),
        ("WINDOWS_GSE_AGENT_PATH", slz.CharField(label=_("Windows Agent 安装路径"), default="C:\\gse")),
        ("WINDOWS_PLUGINS_DATA_PATH", slz.CharField(label=_("Windows 数据保存路径"), default="C:\\gse\\data")),
        ("WINDOWS_PLUGINS_PID_PATH", slz.CharField(label=_("Windows PID 文件保存路径"), default="C:\\gse\\logs")),
        ("WINDOWS_PLUGINS_LOG_PATH", slz.CharField(label=_("Windows 日志保存路径"), default="C:\\gse\\logs")),
        ("WINDOWS_GSE_AGENT_IPC_PATH", slz.CharField(label=_("Windows IPC 路径"), default="127.0.0.1:47000")),
        ("CUSTOM_REPORT_DEFAULT_PROXY_IP", slz.ListField(label=_("自定义上报默认服务器"), default=[])),
        ("CUSTOM_REPORT_DEFAULT_PROXY_DOMAIN", slz.ListField(label=_("自定义上报默认服务器(域名显示)"), default=[])),
        ("BK_NODEMAN_VERSION", slz.CharField(label=_("节点管理版本号"), default="2.0")),
        (
            "MAX_AVAILABLE_DURATION_LIMIT",
            slz.IntegerField(label=_("拨测任务最大超时限制(ms)"), default=60000, min_value=1000),
        ),
        ("HOST_DISABLE_MONITOR_STATES", slz.ListField(label=_("主机不监控字段列表"), default=[_("备用机"), _("测试中"), _("故障中")])),
        ("HOST_DISABLE_NOTICE_STATES", slz.ListField(label=_("主机不告警字段列表"), default=[_("运营中[无告警]"), _("开发中[无告警]")])),
        ("SPECIFY_AES_KEY", slz.CharField(label=_("特别指定的AES使用密钥"), default="")),
        (
            "OS_GLOBAL_SWITCH",
            slz.MultipleChoiceField(
                label=_("操作系统全局开关"),
                default=["linux", "windows", "linux_aarch64"],
                choices=(
                    ("linux", "Linux"),
                    ("windows", "Windows"),
                    ("aix", "AIX"),
                    ("linux_aarch64", "Linux_aarch64"),
                ),
            ),
        ),
        ("ENTERPRISE_CODE", slz.CharField(label=_("企业代号"), default="")),
        ("IS_ALLOW_ALL_CMDB_LEVEL", slz.BooleanField(label=_("是否允许所有数据源配置CMDB聚合"), default=False)),
        ("ES_RETAIN_INVALID_ALIAS", slz.BooleanField(label=_("当 ES 存在不合法别名时，是否保留该索引"), default=True)),
        ("DEMO_BIZ_ID", slz.IntegerField(label=_("Demo业务ID"), default=-1)),
        ("DEMO_BIZ_WRITE_PERMISSION", slz.BooleanField(label=_("Demo业务写权限"), default=False)),
        ("DEMO_BIZ_APPLY", slz.CharField(label=_("业务接入链接"), default="", allow_blank=True)),
        ("BK_DOCS_VERSION", slz.CharField(label=_("文档版本号(留空默认最新)"), default="", allow_blank=True)),
        ("WXWORK_BOT_NAME", slz.CharField(label=_("蓝鲸监控机器人名称"), default="BK-Monitor", allow_blank=True)),
        ("WXWORK_BOT_SEND_IMAGE", slz.BooleanField(label=_("蓝鲸监控机器人发送图片"), default=True)),
        ("THROTTLE_APP_WHITE_LIST", slz.ListField(label=_("对数据查询API执行流控的APP白名单"), default=[])),
        ("COLLECTING_CONFIG_FILE_MAXSIZE", slz.IntegerField(label=_("采集配置文件参数最大值(M)"), default=2)),
        # 订阅报表相关配置
        ("MAIL_REPORT_BIZ", slz.CharField(label=_("订阅报表默认业务ID(为0时关闭)"), default="0")),
    ]
)

GLOBAL_CONFIGS = list(ADVANCED_OPTIONS.keys()) + list(STANDARD_CONFIGS.keys())


def init_or_update_global_config(GlobalConfig):
    for config_key in GLOBAL_CONFIGS:
        if config_key in ADVANCED_OPTIONS:
            serializer = ADVANCED_OPTIONS[config_key]
            is_advanced = True
        elif config_key in STANDARD_CONFIGS:
            serializer = STANDARD_CONFIGS[config_key]
            is_advanced = False
        else:
            continue

        data_type = serializer.__class__.__name__.replace("Field", "")

        try:
            config = GlobalConfig.objects.get(key=config_key)
        except GlobalConfig.DoesNotExist:
            config = GlobalConfig(
                key=config_key,
                value=serializer.default,
            )
        config.description = serializer.label
        config.data_type = data_type
        config.is_advanced = is_advanced
        config.is_internal = True
        config.options = serializer._kwargs
        config.save()


def run(apps, *args):
    GlobalConfig = apps.get_model("bkmonitor.GlobalConfig")
    try:
        init_or_update_global_config(GlobalConfig)
    except DatabaseError:
        pass
