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


import base64
import copy

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _lazy

from bkmonitor.utils.db.fields import JsonField, YamlField
from monitor_web.models import OperateRecordModelBase
from monitor_web.plugin.constant import PluginType, DEFAULT_TRAP_V3_CONFIG
from monitor_web.plugin.signature import Signature


class CollectorPluginMeta(OperateRecordModelBase):
    """
    采集插件源信息
    """

    PluginType = PluginType
    PLUGIN_TYPE_CHOICES = (
        (PluginType.EXPORTER, PluginType.EXPORTER),
        (PluginType.SCRIPT, PluginType.SCRIPT),
        (PluginType.JMX, PluginType.JMX),
        (PluginType.DATADOG, PluginType.DATADOG),
        (PluginType.PUSHGATEWAY, "BK-Pull"),
        (PluginType.BUILT_IN, "BK-Monitor"),
        (PluginType.LOG, PluginType.LOG),
        (PluginType.PROCESS, "Process"),
        (PluginType.SNMP_TRAP, PluginType.SNMP_TRAP),
        (PluginType.SNMP, PluginType.SNMP),
    )

    VIRTUAL_PLUGIN_TYPE = [PluginType.LOG, PluginType.PROCESS, PluginType.SNMP_TRAP]

    plugin_id = models.CharField(_lazy("插件ID"), max_length=64, primary_key=True)
    bk_biz_id = models.IntegerField(_lazy("业务ID"), default=0, blank=True, db_index=True)
    bk_supplier_id = models.IntegerField(_lazy("开发商ID"), default=0, blank=True)
    plugin_type = models.CharField(_lazy("插件类型"), max_length=32, choices=PLUGIN_TYPE_CHOICES, db_index=True)
    tag = models.CharField(_lazy("插件标签"), max_length=64, default="")
    label = models.CharField(_lazy("二级标签"), max_length=64, default="")
    is_internal = models.BooleanField(_lazy("是否内置"), default=False)

    def __str__(self):
        return f"{self.plugin_type}-{self.plugin_id}"

    @property
    def is_global(self):
        """
        是否为全局插件
        """
        return self.bk_biz_id == 0

    @property
    def edit_allowed(self):
        if self.is_internal:
            return False
        return True

    @property
    def delete_allowed(self):
        return not (self.is_internal or self.current_version.collecting_config_total)

    @property
    def export_allowed(self):
        if self.plugin_type == self.PluginType.BUILT_IN or not self.release_version:
            return False
        return True

    @property
    def release_version(self):
        """
        最新的发布版本
        """
        return self.versions.filter(stage=PluginVersionHistory.Stage.RELEASE).last()

    @property
    def packaged_release_version(self):
        """
        最新的发布版本
        """
        version = self.versions.filter(stage=PluginVersionHistory.Stage.RELEASE, is_packaged=True).last()
        if not version:
            version = self.versions.filter(stage=PluginVersionHistory.Stage.RELEASE).last()
        return version

    @property
    def initial_version(self):
        """
        最初的发布版本
        """
        return self.versions.filter(stage=PluginVersionHistory.Stage.RELEASE).first()

    @property
    def current_version(self):
        """
        获取当前版本
        """
        release_version = self.release_version
        if release_version:
            return release_version

        # 如果没有发布版本，获取最新草稿版本
        debug_version = self.versions.filter(~Q(stage=PluginVersionHistory.Stage.RELEASE)).last()
        if not debug_version:
            # 没有草稿版本，创建一个
            debug_version = self.generate_version(config_version=1, info_version=1)

        return debug_version

    def get_version(self, config_version, info_version):
        """
        获取特定版本
        """
        return self.versions.get(config_version=config_version, info_version=info_version)

    def get_release_version_by_config_version(self, config_version):
        version = self.versions.filter(config_version=config_version, stage=PluginVersionHistory.Stage.RELEASE).last()
        return version

    def rollback_version_status(self, config_version):
        """
        获取特定版本
        """
        version = self.versions.filter(
            config_version=config_version, stage=PluginVersionHistory.Stage.RELEASE, is_packaged=True
        )
        if not version:
            self.versions.filter(config_version=config_version, stage=PluginVersionHistory.Stage.RELEASE).update(
                stage=PluginVersionHistory.Stage.UNREGISTER
            )

    def get_debug_version(self, config_version):
        version = self.versions.filter(
            config_version=config_version,
            stage__in=[PluginVersionHistory.Stage.DEBUG, PluginVersionHistory.Stage.RELEASE],
            is_packaged=True,
        ).last()
        if not version:
            version = self.versions.filter(
                config_version=config_version, stage=PluginVersionHistory.Stage.RELEASE
            ).last()
        return version

    def generate_version(self, config_version, info_version, config=None, info=None):
        """
        生成特定版本
        """
        try:
            version = self.get_version(config_version, info_version)
            if config:
                version.config = config
            if info:
                version.info = info
            version.save()
        except PluginVersionHistory.DoesNotExist:
            if config is None:
                config = CollectorPluginConfig.objects.create()
            if info is None:
                info = CollectorPluginInfo.objects.create()
            version = self.versions.create(
                config_version=config_version,
                info_version=info_version,
                config=config,
                info=info,
            )
        return version

    def get_plugin_detail(self):
        current_version = self.current_version
        logo_base64 = current_version.info.logo_content
        plugin_detail = {
            "plugin_id": self.plugin_id,
            "plugin_display_name": current_version.info.plugin_display_name,
            "plugin_type": self.plugin_type,
            "tag": self.tag,
            "label": self.label,
            "status": "normal" if current_version.is_release else "draft",
            "logo": logo_base64,
            "collector_json": current_version.config.collector_json,
            "config_json": current_version.config.config_json,
            "metric_json": current_version.info.metric_json,
            "description_md": current_version.info.description_md,
            "config_version": current_version.config_version,
            "info_version": current_version.info_version,
            "stage": current_version.stage,
            "bk_biz_id": self.bk_biz_id,
            "signature": Signature(current_version.signature).dumps2yaml() if current_version.signature else "",
            "is_support_remote": current_version.config.is_support_remote,
            "is_official": current_version.is_official,
            "is_safety": current_version.is_safety,
            "create_user": self.create_user,
            "update_user": current_version.update_user,
            "os_type_list": current_version.os_type_list,
            "create_time": current_version.create_time,
            "update_time": current_version.update_time,
            "related_conf_count": current_version.get_related_config_count(),
            "edit_allowed": self.edit_allowed if not current_version.is_official else False,
        }
        if self.plugin_type == PluginType.SNMP_TRAP:
            params = current_version.deployment_versions.last().params
            plugin_detail["config_json"] = self.get_config_json(params["snmp_trap"])
        return plugin_detail

    def get_config_json(self, params):
        trap_config = [
            {
                "default": params.get("server_port"),
                "mode": "collector",
                "type": "text",
                "key": "server_port",
                "name": "Trap服务端口",
                "description": "Trap服务端口",
            },
            {
                "default": params.get("listen_ip"),
                "mode": "collector",
                "type": "text",
                "key": "listen_ip",
                "name": "绑定地址",
                "description": "绑定地址",
            },
            {
                "default": params.get("yaml"),
                "mode": "collector",
                "type": "file",
                "key": "yaml",
                "name": "Yaml配置文件",
                "description": "Yaml配置文件",
            },
            {
                "default": params.get("community"),
                "mode": "collector",
                "type": "text",
                "key": "community",
                "name": "团体名",
                "description": "团体名",
            },
        ]
        #
        if params.get("version") == "v3":
            auth_info = {
                k: [
                    [
                        {
                            "default": i["security_name"],
                            "mode": "collector",
                            "type": "text",
                            "key": "security_name",
                            "name": "安全名",
                            "description": "安全名",
                        },
                        {
                            "default": i["context_name"],
                            "mode": "collector",
                            "type": "text",
                            "key": "context_name",
                            "name": "上下文名称",
                            "description": "上下文名称",
                        },
                        {
                            "default": i["security_level"],
                            "election": ["authPriv", "authNoPriv", "noAuthNoPriv"],
                            "mode": "collector",
                            "type": "list",
                            "key": "security_level",
                            "name": "安全级别",
                            "description": "安全级别",
                        },
                        {
                            "default": i["authentication_protocol"],
                            "election": ["MD5", "SHA", "DES", "AES"],
                            "mode": "collector",
                            "type": "list",
                            "key": "authentication_protocol",
                            "name": "验证协议",
                            "description": "验证协议",
                            "auth_priv": {
                                "noAuthNoPriv": {"need": False},
                                "authNoPriv": {"need": True, "election": ["MD5", "SHA"]},
                                "authPriv": {"need": True, "election": ["MD5", "SHA", "DES", "AES"]},
                            },
                        },
                        {
                            "default": i["authentication_passphrase"],
                            "mode": "collector",
                            "type": "text",
                            "key": "authentication_passphrase",
                            "name": "验证口令",
                            "description": "验证口令",
                            "auth_priv": {
                                "noAuthNoPriv": {"need": False},
                                "authNoPriv": {"need": True},
                                "authPriv": {"need": True},
                            },
                        },
                        {
                            "default": i["privacy_protocol"],
                            "election": ["DES", "AES"],
                            "mode": "collector",
                            "type": "list",
                            "key": "privacy_protocol",
                            "name": "隐私协议",
                            "description": "隐私协议",
                            "auth_priv": {
                                "NoAuthNoPriv": {"need": False},
                                "authNoPriv": {"need": False},
                                "authPriv": {"need": True, "election": ["DES", "AES"]},
                            },
                        },
                        {
                            "default": i["privacy_passphrase"],
                            "mode": "collector",
                            "type": "text",
                            "key": "privacy_passphrase",
                            "name": "私钥",
                            "description": "私钥",
                            "auth_priv": {
                                "noAuthNoPriv": {"need": False},
                                "authNoPriv": {"need": False},
                                "authPriv": {"need": True},
                            },
                        },
                        {
                            "default": i["authoritative_engineID"],
                            "mode": "collector",
                            "type": "text",
                            "key": "authoritative_engineID",
                            "name": "认证设备",
                            "description": "认证设备",
                        },
                    ]
                    for i in v
                ]
                for k, v in {
                    "auth_json": params.get("auth_info", ""),
                    "template_auth_json": DEFAULT_TRAP_V3_CONFIG["auth_info"],
                }.items()
            }
            trap_config.extend([auth_info])
        trap_config.append(
            {
                "default": params.get("aggregate"),
                "mode": "collector",
                "type": "boolean",
                "key": "aggregate",
                "name": "是否汇聚",
                "description": "是否汇聚",
            }
        )
        return trap_config


class CollectorPluginConfig(OperateRecordModelBase):
    """
    采集器插件功能信息
    """

    config_json = JsonField(_lazy("参数配置"), default=None)
    collector_json = JsonField(_lazy("采集器配置"), default=None)
    is_support_remote = models.BooleanField(_lazy("是否支持远程采集"), default=False)

    def __str__(self):
        return f"{self.__class__.__name__}<{self.id}>"

    def config2dict(self, config_params=None):
        if config_params is None:
            config_params = {}

        now_collector_json = copy.deepcopy(self.collector_json)
        if now_collector_json:
            now_collector_json.pop("diff_fields", None)

        return {
            "config_json": config_params.get("config_json", self.config_json),
            "collector_json": config_params.get("collector_json", now_collector_json),
            "is_support_remote": config_params.get("is_support_remote", self.is_support_remote),
        }

    @property
    def diff_fields(self):
        self.collector_json = self.collector_json or {}
        return self.collector_json.get("diff_fields") or ""

    @diff_fields.setter
    def diff_fields(self, value):
        if value:
            self.collector_json = self.collector_json or {}
            self.collector_json.update({"diff_fields": value})
        else:
            if self.collector_json:
                self.collector_json.pop("diff_fields", "")

    @property
    def file_config(self):
        _file_config = dict()
        for key in self.collector_json:
            if key in OperatorSystem.objects.os_type_list():
                _file_config.setdefault(key, self.collector_json[key])

        return _file_config

    @property
    def debug_flag(self):
        return {"debugged": True}


class CollectorPluginInfo(OperateRecordModelBase):
    """
    采集器插件信息
    发布成功后，新纪录的info_version+=1
    草稿下，info_version=0
    """

    plugin_display_name = models.CharField(_lazy("插件别名"), max_length=64, default="")
    metric_json = JsonField(_lazy("指标配置"), default=[])
    description_md = models.TextField(_lazy("插件描述，markdown文本"), default="")
    logo = models.ImageField(_lazy("logo文件"), null=True)

    def __str__(self):
        return f"{self.plugin_display_name}"

    def info2dict(self, info_params=None):
        if info_params is None:
            info_params = {}
            logo_str = self.logo_content
            description_md = self.description_md
        else:
            logo_str = info_params.get("logo", "").split(",")[-1]
            description_md = info_params.get("description_md", "")

        result = {
            "plugin_display_name": info_params.get("plugin_display_name", self.plugin_display_name),
            "description_md": description_md,
            "logo": logo_str,
            "metric_json": info_params.get("metric_json") or self.metric_json,
        }

        return result

    @property
    def logo_content(self):
        """
        logo content with base64 encoding
        :return:
        """
        if not self.logo:
            return ""
        try:
            logo_str = b"".join(self.logo.chunks())
        except Exception:
            return ""
        return base64.b64encode(logo_str)


class PluginVersionHistory(OperateRecordModelBase):
    """
    采集插件版本历史
    """

    class Stage(object):
        """
        插件状态
        """

        UNREGISTER = "unregister"
        DEBUG = "debug"
        RELEASE = "release"

    STAGE_CHOICES = (
        (Stage.UNREGISTER, _lazy("未注册版本")),
        (Stage.DEBUG, _lazy("调试版本")),
        (Stage.RELEASE, _lazy("发布版本")),
    )

    plugin = models.ForeignKey(CollectorPluginMeta, verbose_name=_lazy("插件元信息"), related_name="versions")
    stage = models.CharField(_lazy("版本阶段"), choices=STAGE_CHOICES, default=Stage.UNREGISTER, max_length=30)
    config = models.ForeignKey(CollectorPluginConfig, verbose_name=_lazy("插件功能配置"), related_name="version")
    info = models.ForeignKey(CollectorPluginInfo, verbose_name=_lazy("插件信息配置"), related_name="version")
    config_version = models.IntegerField(_lazy("插件版本"), default=1)
    info_version = models.IntegerField(_lazy("插件信息版本"), default=1)
    signature = YamlField(_lazy("版本签名"), default="")
    version_log = models.CharField(_lazy("版本修改日志"), max_length=100, default="")
    is_packaged = models.BooleanField(_lazy("是否已上传到节点管理"), default=False)

    @property
    def os_type_list(self):
        """
        获取该版本支持的操作系统类型
        :return:
        """
        if self.plugin.plugin_type in [
            CollectorPluginMeta.PluginType.JMX,
            CollectorPluginMeta.PluginType.SNMP,
            CollectorPluginMeta.PluginType.BUILT_IN,
            CollectorPluginMeta.PluginType.PUSHGATEWAY,
        ]:
            return ["linux", "windows", "linux_aarch64"]
        else:
            return list(self.config.file_config.keys())

    @property
    def is_release(self):
        if self.stage == "release":
            return True
        return False

    @property
    def version_info(self):
        """
        获取版本号元组，例如 (2, 3)
        major - config_version
        minor - info_version
        """
        return self.config_version, self.info_version

    @property
    def version(self):
        """
        获取版本号字符串，例如 "2.3"
        major - config_version
        minor - info_version
        """
        return ".".join([str(num) for num in self.version_info])

    @property
    def is_official(self):
        return Signature(self.signature).verificate("official", self)

    @property
    def is_safety(self):
        return Signature(self.signature).verificate("safety", self)

    @property
    def collecting_config_count(self):
        """该版本关联的采集配置数量"""
        from monitor_web.models.collecting import DeploymentConfigVersion

        return DeploymentConfigVersion.objects.filter(plugin_version=self).values("config_meta_id").distinct().count()

    @property
    def collecting_config_total(self):
        """该版本插件全部版本关联的采集配置数量"""
        from monitor_web.models.collecting import CollectConfigMeta

        return CollectConfigMeta.objects.filter(plugin_id=self.plugin.plugin_id).count()

    @property
    def collecting_config_detail(self):
        from monitor_web.models.collecting import CollectConfigMeta

        collect_config = list(CollectConfigMeta.objects.filter(plugin_id=self.plugin.plugin_id).values())
        return collect_config

    def get_related_config_count(self, bk_biz_id=None):
        from monitor_web.models.collecting import CollectConfigMeta

        if bk_biz_id:
            return CollectConfigMeta.objects.filter(plugin_id=self.plugin.plugin_id, bk_biz_id=bk_biz_id).count()
        else:
            return CollectConfigMeta.objects.filter(plugin_id=self.plugin.plugin_id).count()

    def update_diff_fields(self):
        diff_fields_value = PluginVersionHistory.gen_diff_fields(self.info.metric_json)

        self.config.diff_fields = diff_fields_value

    def save(self, *args, **kwargs):
        self.update_diff_fields()
        self.config.save()

        if self.signature:
            signature = Signature(self.signature)
            new_signature = dict()
            for protocol, ret in signature.iter_verificate(self):
                if ret:
                    new_signature[protocol] = self.signature[protocol]

            self.signature = new_signature or ""
        return super(PluginVersionHistory, self).save(*args, **kwargs)

    @classmethod
    def gen_diff_fields(cls, metric_json):
        diff_fields = []
        for table in metric_json:
            for field in table.get("fields", []):
                if field.get("is_diff_metric", False):
                    diff_fields.append(field["name"])

        if diff_fields:
            return ",".join(sorted(diff_fields))
        else:
            return ""

    def get_plugin_version_detail(self):
        logo_base64 = self.info.logo_content
        plugin_detail = {
            "plugin_id": self.plugin_id,
            "plugin_display_name": self.info.plugin_display_name,
            "plugin_type": self.plugin.plugin_type,
            "tag": self.plugin.tag,
            "logo": logo_base64,
            "collector_json": self.config.collector_json,
            "config_json": self.config.config_json,
            "metric_json": self.info.metric_json,
            "description_md": self.info.description_md,
            "config_version": self.config_version,
            "info_version": self.info_version,
            "stage": self.stage,
            "bk_biz_id": self.plugin.bk_biz_id,
            "signature": Signature(self.signature).dumps2yaml() if self.signature else "",
            "is_support_remote": self.config.is_support_remote,
            "is_official": self.is_official,
            "is_safety": self.is_safety,
            "create_user": self.create_user,
            "update_user": self.update_user,
            "os_type_list": self.os_type_list,
        }
        return plugin_detail

    class Meta:
        ordering = ["config_version", "info_version", "create_time", "update_time"]
        unique_together = ["plugin", "config_version", "info_version"]

    def __str__(self):
        return "{}-{}".format(self.plugin_id, self.version)


class OperatorSystemManager(models.Manager):
    def os_type_list(self):
        supported_os = self.all().values("os_type")
        return [_o["os_type"] for _o in supported_os]

    def get_queryset(self):
        return super(OperatorSystemManager, self).get_queryset().filter(os_type__in=settings.OS_GLOBAL_SWITCH)


class OperatorSystem(models.Model):
    """
    操作系统
    windows,os_type_id=2
    linux,os_type_id=1
    aix(is_enable=False),os_type_id=3
    """

    objects = OperatorSystemManager()

    os_type_id = models.CharField(_lazy("操作系统类型ID"), max_length=10)
    os_type = models.CharField(_lazy("操作系统类型"), max_length=16, unique=True)
