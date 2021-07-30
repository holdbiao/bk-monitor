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
import hashlib
import json
import os
import re
import subprocess
import traceback
import uuid

import arrow
import six
from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from six.moves import range

import ntpath
import posixpath
from core.drf_resource.exceptions import CustomException
from core.drf_resource import resource
from bkmonitor.utils import time_tools
from bkmonitor.utils.common_utils import check_permission, failed, gen_tsdb_rt, host_key, ok, ok_data, safe_int
from bkmonitor.utils.db.fields import AESJsonField, AESTextField, ConfigDataField, JsonField
from bkmonitor.utils.host import Host
from bkmonitor.utils.request import get_request
from common.log import logger
from core.drf_resource import api
from monitor.constants import (
    EXPORTER_LISTEN_ADDRESS_PARAM_NAME,
    SHELL_COLLECTOR_DB,
    STRUCTURED_LOG_DB,
    UPTIME_CHECK_DB,
    UptimeCheckProtocol,
)
from monitor_web.commons.data_access import DataAccessor, ResultTable, ResultTableField
from monitor_web.models import OperateManagerBase, OperateRecordModelBase
from monitor_web.tasks import append_metric_list_cache, update_task_running_status
from monitor_web.uptime_check.collector import UptimeCheckCollector

key_words_regex_com = re.compile(r"\${\S*?\|?\S*?}")


class OperateManager(OperateManagerBase):
    def all(self, *args, **kwargs):
        # 默认都不显示被标记为删除的告警定义
        return super(OperateManager, self).filter(is_deleted=False)

    def filter(self, *args, **kwargs):
        # 默认都不显示被标记为删除的告警定义
        return super(OperateManager, self).filter(*args, **kwargs).filter(is_deleted=False)


class OperateRecordModel(OperateRecordModelBase):
    class Meta:
        abstract = True

    def gen_operate_desc(self, operate, ori_data=False):
        """
        根据操作类型，与变更前后的配置生成操作说明
        :param operate: 操作类型：create/update/delete
        :param ori_data: 操作前的配置信息 [可选]
        :return: operate_desc 变更说明
        """
        op_desc = self.get_title()
        if operate in ["create", "delete"]:
            return op_desc
        elif operate == "update":
            if not ori_data:
                return op_desc
            # 获得2次修改之间， 变更了哪些配置
            changed_config = self.get_operate_changed_config(ori_data)
            # 根据变更的配置， 生成对应的wording
            op_desc = self.gen_op_desc_by_changed_config(changed_config)
        return op_desc

    def get_operate_changed_config(self, ori_data):
        changed_configs = {}
        operate_record_fields = [f.name for f in OperateRecordModel._meta.fields]
        for f in self._meta.fields:
            if f.name not in operate_record_fields:
                dst_value = getattr(self, f.name)
                ori_value = getattr(ori_data, f.name)
                if dst_value != ori_value:
                    changed_configs[f.name] = {
                        "key": f.name,
                        "title": _(f.verbose_name.replace("(json)", "")),
                        "ori_value": ori_value,
                        "dst_value": dst_value,
                    }
        if hasattr(self, "get_special_change_config"):
            changed_configs = self.get_special_change_config(changed_configs, ori_data)
        return changed_configs

    def gen_op_desc_by_changed_config(self, changed):
        # 仪表盘视图则使用特殊逻辑
        if self._meta.object_name == "DashboardView":
            return self.dashboard_view_gen_op_desc_by_changed_config(changed)
        op_desc = _(self.get_title() + _("的"))
        if len(changed) < 1:
            return ""

        for key in changed:
            changed_attr = changed[key]
            op_desc += _("%(title)s由 [%(ori_val)s] 被修改为 [%(dst_val)s] \t") % {
                "title": changed_attr.get("title", key),
                "ori_val": changed_attr.get("ori_value", ""),
                "dst_val": changed_attr.get("dst_value", ""),
            }
        return op_desc


class OperateRecord(models.Model):
    biz_id = models.IntegerField(_("业务cc_id"), default=0)
    config_type = models.CharField(_("配置类型"), max_length=32)
    config_id = models.IntegerField(_("操作config_id"))
    config_title = models.CharField(_("配置标题"), default="", max_length=512)
    operator = models.CharField(_("操作人"), max_length=32)
    operator_name = models.CharField(_("操作人昵称"), default="", max_length=32)
    operate = models.CharField(_("具体操作"), max_length=32)
    operate_time = models.DateTimeField(_("操作时间"), auto_now_add=True)
    data = models.TextField(_("数据(JSON)"))
    data_ori = models.TextField(_("修改前数据(JSON)"), default="{}")
    operate_desc = models.TextField(_("操作说明"), default="")

    class Meta:
        verbose_name = _("操作记录")
        verbose_name_plural = _("操作记录")

    def gen_operate_desc(self):
        # 准备数据
        from monitor.operation_records import unserialize_object

        try:
            config_obj = unserialize_object(self.data)
            if not config_obj:
                self.operate_desc = ""
                self.config_title = ""
                return False
        except Exception:
            # 信息解析失败， 无法生成操作说明
            self.operate_desc = ""
            self.config_title = ""
            return False

        self.config_title = config_obj.get_title()
        if self.operate in ["create", "delete"]:
            self.operate_desc = config_obj.gen_operate_desc(self.operate)
        elif self.operate == "update":
            # 准备修改前数据
            try:
                from monitor.operation_records import unserialize_object

                config_ori_obj = unserialize_object(self.data_ori)
                if not config_ori_obj:
                    self.operate_desc = ""
                    return False
            except Exception:
                self.operate_desc = ""
                return False
            self.operate_desc = config_obj.gen_operate_desc(self.operate, config_ori_obj)
        else:
            self.operate_desc = ""
        return True

    # def save(self, *args, **kwargs):
    #     如果是update， 则保存原始值
    # try:
    #     self.gen_operate_desc()
    # except Exception, e:
    #     logger.exception(u'saving operate record fail: gen operate desc fail %s' % e)
    # return super(OperateRecord, self).save()

    @staticmethod
    def build_operate_record_data(data_queryset, page, page_size=10):
        """组装操作流水列表数据

        :param data_queryset:
        :param page: page为0表示不分页，返回全部数据
        :param page_size:
        :return:
        """
        if page == 0:
            return list(data_queryset)
        else:
            start = (page - 1) * page_size
            end = start + page_size
            return list(data_queryset[start:end])


class ComponentInstance(OperateRecordModel):
    biz_id = models.IntegerField(_("业务ID"))
    ip = models.GenericIPAddressField(_("实例IP"))
    plat_id = models.CharField(_("子网ID"), default="1", max_length=10)
    component = models.CharField(_("组件名称"), max_length=128)
    config = AESTextField(_("组件配置"))
    instance_name = models.CharField(_("实例名称"), default="", max_length=256)
    tags = JsonField(_("标签"), null=True, blank=True)

    class Meta:
        verbose_name = _("组件实例关系")
        verbose_name_plural = _("组件实例关系")
        ordering = ["-update_time"]

    def get_title(self):
        return _("组件（{}），IP（{}）").format(self.component, self.ip)

    def get_special_change_config(self, changed_configs, ori_data):
        dst_config = self.get_config_result()
        ori_config = ori_data.get_config_result()
        if dst_config != ori_config:
            changed_configs["config"] = {
                "key": "config",
                "title": _("组件配置"),
                "ori_value": ori_config,
                "dst_value": dst_config,
            }
        return changed_configs

    def get_config_result(self):
        return ""


class DataGenerateConfig(OperateRecordModel):
    """
    记录数据处理过程
    biz_id: 业务
    collector_id: 采集表id
    template_id: 模板id
    template_args: 模版参数
    project_id: 子项目ID
    job_id: 对应的作业ID
    """

    STATUS_CHOICES = (
        ("starting", _("启动中")),
        ("running", _("正在运行")),
        ("stopping", _("停止中")),
        ("not running", _("未启动")),
    )

    biz_id = models.IntegerField(_("业务ID"))
    collector_id = models.IntegerField(_("关联数据接入配置"))
    template_id = models.IntegerField(_("模版ID"))
    template_args = models.TextField(_("模版参数"))
    project_id = models.IntegerField(_("子项目ID"))
    job_id = models.CharField(_("对应的作业ID"), max_length=32)
    bksql = models.TextField(_("bksql描述"), default="")
    status = models.CharField(_("作业状态"), max_length=16, default="starting", choices=STATUS_CHOICES)


class DataCollector(OperateRecordModel):
    """
    记录通过监控系统接入的数据来源及配置信息
    biz_id: 业务
    source_type: 数据库 / log / msdk / tqos
    collector_config: 采集数据需要用到的配置信息
    data_set: 数据基简称
    data_id: 数据id
    data_description: 数据描述
    data_type: 数据类型 在线==
    """

    biz_id = models.IntegerField(_("业务ID"))
    source_type = models.CharField(_("数据源类型"), max_length=32)
    collector_config = models.TextField(_("数据接入配置信息"))
    data_id = models.IntegerField(_("下发data id"))
    data_type = models.CharField(_("数据类型"), max_length=32)
    data_set = models.CharField("db_name+table_name", max_length=225)
    data_description = models.TextField(_("数据描述"), null=True)

    def __str__(self):
        return "{}: {}".format(self.id, self.biz_id)


class MonitorHostStickyManager(models.Manager):
    def host_is_stickied(self, host_id, cc_biz_id):
        """
        主机是否置顶，未置顶返回0，置顶返回置顶记录id
        """
        ip, plat_id = host_id.split("|")
        q_set = self.filter(host=ip, plat_id=plat_id, cc_biz_id=cc_biz_id)
        if q_set.exists():
            row = q_set[0]
            return row.id
        return 0


class MonitorHostSticky(models.Model):
    """
    主机基础性能列表置顶信息
    """

    plat_id = models.IntegerField(_("平台ID"), null=True)
    host = models.CharField(_("主机IP"), max_length=128, null=True, db_index=True)
    cc_biz_id = models.CharField(_("cc业务id"), max_length=30)

    objects = MonitorHostStickyManager()


class ScenarioMenuManager(OperateManager):
    def init_biz_scenario_menu(self, biz_id):
        # 初始化用户场景菜单列表
        sms = list()
        for i, (system_menu, menu_name) in enumerate(self.model.SYSTEM_MENU_CHOICES):
            if system_menu:
                if self.filter(system_menu=system_menu, biz_id=biz_id, menu_name=menu_name).exists():
                    continue
                sm = self.model(system_menu=system_menu, biz_id=biz_id, menu_name=menu_name, menu_index=i)
                sm.save()
                sms.append(sm)
        return sms

    def add_scenario_menu(self, biz_id, menu_name):
        # 新建场景菜单
        if not menu_name:
            return failed(_("组名不能为空"))
        menu_name = menu_name.strip()
        exists = self.filter(menu_name=menu_name, biz_id=biz_id).exists()
        if exists:
            return failed(_("组名已存在，无法新增相同分组"))
        if len(menu_name.encode("gbk")) > 20:
            return failed(_("组名长度不能超过20个字符，一个中文算2个字符。"))
        sm = self.model(biz_id=biz_id, menu_name=menu_name)
        sm.save()
        return ok_data(sm.id)

    def edit_scenario_menu(self, menu_id, menu_name, cc_biz_id):
        # 新建场景菜单
        try:
            menu = self.get(pk=menu_id)
        except self.model.DoesNotExist:
            return failed(_("无效的请求"))
        if not check_permission(menu, cc_biz_id):
            return failed(_("无权限"))
        menu_name = menu_name.strip()
        count = self.filter(menu_name=menu_name, biz_id=menu.biz_id).exclude(pk=menu_id).count()
        if count > 0:
            return failed(_("同名分组已存在"))
        if len(menu_name.encode("gbk")) > 20:
            return failed(_("组名长度不能超过20个字符，一个中文算2个字符。"))
        menu.menu_name = menu_name
        menu.save()
        return ok()

    def del_scenario_menu(self, menu_id, cc_biz_id):
        # 新建场景菜单
        try:
            menu = self.get(pk=menu_id)
        except self.model.DoesNotExist:
            return failed(_("无效的请求"))
        if not check_permission(menu, cc_biz_id):
            return failed(_("无权限"))
        menu.is_deleted = True
        menu.save()
        return ok()


class ScenarioMenu(OperateRecordModel):
    """
    左侧场景菜单
    """

    SYSTEM_MENU_CHOICES = (
        ("", _("用户自定义")),
        ("favorite", _("关注")),
        ("default", _("默认分组")),
    )
    system_menu = models.CharField(_("系统菜单栏"), choices=SYSTEM_MENU_CHOICES, max_length=32, default="", blank=True)
    biz_id = models.CharField(_("业务ID"), max_length=100)

    menu_name = models.CharField(_("菜单名"), max_length=255)
    menu_index = models.IntegerField(_("菜单顺序"), default=999)

    objects = ScenarioMenuManager()

    def __unicode__(self):
        return "【{}】{}".format(self.biz_id, self.name)

    class Meta:
        verbose_name = _("左侧菜单")
        verbose_name_plural = _("左侧菜单")

    def system_menu_display(self):
        for i in self.SYSTEM_MENU_CHOICES:
            if i[0] == self.system_menu:
                return _(i[1])
        return self.system_menu

    @property
    def name(self):
        if self.system_menu:
            return self.system_menu_display()
        return self.menu_name

    @property
    def allowed_edit(self):
        if not self.system_menu:
            return True
        return self.system_menu not in [c[0] for c in ScenarioMenu.SYSTEM_MENU_CHOICES]

    def get_title(self):
        return _("自定义监控分组(%s)") % self.name


class MonitorLocationManager(OperateManager):
    def get_scenario_menu_list_by_monitor_id(self, monitor_id):
        # 通过监控id获取对应的所有场景菜单列表
        locations = self.filter(monitor_id=monitor_id)
        menus = []

        for location in locations:
            if location.menu and location.menu.system_menu != "favorite":
                menus.append(location.menu)
        return list(set(menus))


class MonitorLocation(OperateRecordModel):
    """
    监控映射
    """

    biz_id = models.CharField(_("业务ID"), max_length=100)

    menu_id = models.IntegerField(_("菜单id"))
    monitor_id = models.IntegerField(_("监控id"))
    graph_index = models.IntegerField(_("图表所在栏目位置"), default=9999999)
    width = models.IntegerField(_("宽度"), default=6)

    objects = MonitorLocationManager()

    class Meta:
        verbose_name = _("监控映射")
        verbose_name_plural = _("监控映射")

    @property
    def menu(self):
        try:
            if not hasattr(self, "_menu"):
                _menu = ScenarioMenu.objects.get(pk=self.menu_id)
                self._menu = _menu
            return self._menu
        except ScenarioMenu.DoesNotExist:
            return None

    def get_title(self):
        return ""


class DashboardMenuManager(OperateManager):
    default_menu_name_list = [
        _("默认仪表盘"),
    ]

    default_menu_views = [
        {
            "height": 4,
            "metric_config": '[{{"metric_index":"11","where_field_list":"[[]]","metric_field":"usage","view_type":"time","metric":"system.cpu_summary.usage","rt_id":"{biz_id}_system_cpu_summary","order":"desc","id":"{id}","top_count":"5","group_field_list":["minute5"],"method":"AVG","alis":"","metric_graph_type":"spline"}}]',  # noqa
            "name": _("CPU使用率 均值"),
            "symbol_config": "[]",
            "type": "time",
            "width": 6,
            "x": 0,
            "y": 0,
        },
        {
            "height": 4,
            "metric_config": '[{{"where_field_list":"[[]]","metric_field":"usage","rt_id":"{biz_id}_system_cpu_summary","metric":"system.cpu_summary.usage","view_type":"top","order":"desc","id":"{id}","top_count":"5","group_field_list":["ip"],"method":"AVG","alis":""}}]',  # noqa
            "name": _("CPU使用率 TOP5"),
            "symbol_config": '[{"threshold":90,"color":"#ff3300","method":">="}]',
            "type": "top",
            "width": 6,
            "x": 6,
            "y": 0,
        },
        {
            "height": 4,
            "metric_config": '[{{"metric_index":"10","where_field_list":"[[]]","metric_field":"pct_used","view_type":"time","metric":"system.mem.pct_used","rt_id":"{biz_id}_system_mem","order":"desc","id":"{id}","top_count":"5","group_field_list":["minute5"],"method":"AVG","alis":"","metric_graph_type":"spline"}}]',  # noqa
            "name": _("应用内存使用率 均值"),
            "symbol_config": "[]",
            "type": "time",
            "width": 6,
            "x": 0,
            "y": 4,
        },
        {
            "height": 4,
            "metric_config": '[{{"where_field_list":"[[]]","metric_field":"pct_used","rt_id":"{biz_id}_system_mem","metric":"system.mem.pct_used","view_type":"top","order":"desc","id":"{id}","top_count":"5","group_field_list":["ip"],"method":"AVG","alis":""}}]',  # noqa
            "name": _("应用内存使用率 TOP5"),
            "symbol_config": "[]",
            "type": "top",
            "width": 6,
            "x": 6,
            "y": 4,
        },
        {
            "height": 4,
            "metric_config": '[{{"metric_index":"9","where_field_list":"[[]]","metric_field":"util","view_type":"time","metric":"system.io.util","rt_id":"{biz_id}_system_io","order":"desc","id":"{id}","top_count":"5","group_field_list":["minute5"],"method":"AVG","alis":"","metric_graph_type":"spline"}}]',  # noqa
            "name": _("磁盘IO使用率 均值"),
            "symbol_config": "[]",
            "type": "time",
            "width": 6,
            "x": 0,
            "y": 8,
        },
        {
            "height": 4,
            "metric_config": '[{{"where_field_list":"[[]]","metric_field":"in_use","rt_id":"{biz_id}_system_disk","metric":"system.disk.in_use","view_type":"top","order":"desc","id":"{id}","top_count":"5","group_field_list":["ip"],"method":"AVG","alis":"CONN_NUM"}}]',  # noqa
            "name": _("磁盘使用率 TOP5"),
            "symbol_config": '[{"threshold":95,"color":"#ff3300","method":">="}]',
            "type": "top",
            "width": 6,
            "x": 6,
            "y": 12,
        },
        {
            "height": 4,
            "metric_config": '[{{"where_field_list":"[[]]","metric_field":"util","rt_id":"{biz_id}_system_io","metric":"system.io.util","view_type":"top","order":"desc","id":"{id}","top_count":"5","group_field_list":["ip"],"method":"AVG","alis":""}}]',  # noqa
            "name": _("磁盘IO使用率 TOP5"),
            "symbol_config": "[]",
            "type": "top",
            "width": 6,
            "x": 6,
            "y": 8,
        },
        {
            "height": 6,
            "metric_config": '[{{"metric_index":"8","where_field_list":"[[]]","metric_field":"in_use","view_type":"time","metric":"system.disk.in_use","rt_id":"{biz_id}_system_disk","order":"desc","id":"{id}","top_count":"5","group_field_list":["minute5"],"method":"AVG","alis":"","metric_graph_type":"spline"}}]',  # noqa
            "name": _("磁盘使用率 均值"),
            "symbol_config": "[]",
            "type": "time",
            "width": 6,
            "x": 0,
            "y": 12,
        },
        {
            "height": 2,
            "metric_config": '[{{"round_count":"0","where_field_list":"[[]]","metric_field":"total","rt_id":"{biz_id}_system_disk","metric":"system.disk.total","view_type":"status","order":"desc","id":"{id}","top_count":"5","group_field_list":[],"method":"AVG","unit":"MB"}}]',  # noqa
            "name": _("全服磁盘大小 均值"),
            "symbol_config": "[]",
            "type": "status",
            "width": 3,
            "x": 9,
            "y": 16,
        },
        {
            "height": 2,
            "metric_config": '[{{"round_count":"0","where_field_list":"[[]]","metric_field":"total","rt_id":"{biz_id}_system_mem","metric":"system.mem.total","view_type":"status","order":"desc","id":"{id}","top_count":"5","group_field_list":[],"method":"AVG","unit":"MB"}}]',  # noqa
            "name": _("全服物理内存 均值"),
            "symbol_config": "[]",
            "type": "status",
            "width": 3,
            "x": 6,
            "y": 16,
        },
    ]

    def init_dashboard(self, cc_biz_id):
        menu = self.filter(biz_id=cc_biz_id, name=_("默认仪表盘")).first()
        if (
            not menu
            or ApplicationConfig.objects.filter(
                cc_biz_id=cc_biz_id,
                key="dashboard_view_config:{menu_id}".format(menu_id=menu.id),
            ).exists()
        ):
            return

        config_list = []
        for i in self.default_menu_views:
            config = i.copy()
            monitor_config_kwargs = resource.commons.trans_bkcloud_bizid(dict(id=uuid.uuid4(), biz_id=menu.biz_id))
            config["metric_config"] = config["metric_config"].format(**monitor_config_kwargs)
            view = DashboardView.objects.create(
                biz_id=menu.biz_id,
                name=config["name"],
                graph_type=config["type"],
                symbols=config["symbol_config"],
                metrics=config["metric_config"],
            )
            DashboardMenuLocation.objects.create(
                view=view,
                menu=menu,
            )
            config["view_id"] = view.id
            config_list.append(
                {"x": i["x"], "y": i["y"], "width": i["width"], "height": i["height"], "view_id": view.pk}
            )

        ApplicationConfig.objects.create(
            cc_biz_id=menu.biz_id,
            key="dashboard_view_config:{menu_id}".format(menu_id=menu.id),
            value=json.dumps(config_list),
        )

    def init_menu(self, biz_id):
        menus = []
        for _name in self.default_menu_name_list:
            menu = self.create(biz_id=biz_id, name=_name)
            menus.append(menu)
        return menus


class DashboardMenu(OperateRecordModel):
    # 仪表盘菜单
    biz_id = models.IntegerField(_("业务ID"))
    name = models.CharField(_("仪表盘名称"), max_length=32, default="")

    objects = DashboardMenuManager()

    @property
    def locations(self):
        return DashboardMenuLocation.objects.filter(menu_id=self.id).order_by("view_index")

    @property
    def cc_biz_id(self):
        return self.biz_id

    @property
    def name_display(self):
        if self.name in DashboardMenuManager.default_menu_name_list:
            return _(self.name)
        return self.name

    def get_title(self):
        return _("仪表盘菜单（%s）") % self.name_display


class DashboardView(OperateRecordModel):
    # 仪表盘视图
    GRAPH_TYPE_CHOICES = (
        ("time", _("时间序列")),
        ("top", _("TOP排行")),
        ("status", _("状态值")),
    )
    # 展示在流水记录中的字段
    DISPLAY_FIELDS = (
        "alis",
        "group_field_list",
        "method",
        "metric",
        "metric_field",
        "metric_graph_type",
        "order",
        "top_count",
        "graph_type",
        "where_field_list",
    )
    # 指标项中各个字段名称
    METRICS_NAME = {
        "alis": _("别名"),
        "group_field_list": _("group by 字段列表"),
        "id": "id",
        "method": _("聚合方法"),
        "metric": _("指标项"),
        "metric_field": _("指标字段"),
        "metric_graph_type": _("图形类型"),
        "metric_index": _("索引"),
        "order": _("顺序"),
        "rt_id": "rt_id",
        "top_count": _("TOP排行"),
        "view_type": _("显示类型"),
        "graph_type": _("图表类型"),
        "where_field_list": _("where字句"),
    }

    biz_id = models.IntegerField(_("业务ID"))
    name = models.CharField(_("视图名称"), max_length=128, default="")
    graph_type = models.CharField(_("图表类型"), max_length=32, choices=GRAPH_TYPE_CHOICES)
    metrics = models.TextField(_("指标项"))
    symbols = models.TextField(_("标记"))

    @property
    def name_display(self):
        # 默认添加的仪表盘视图名称，需要支持多语言（中文插入DB，显示的时候再做翻译）
        default_dashboard_names = [i["name"] for i in DashboardMenuManager.default_menu_views]
        if self.name in default_dashboard_names:
            return _(self.name)
        return self.name

    def get_title(self):
        return _("仪表盘视图（%s）") % self.name_display

    def get_special_change_config(self, changed_configs, ori_data):
        """
        获取仪表盘视图的特殊逻辑，现在主要是metrics
        :param changed_configs: 已经发生变化的字段
        :param ori_data: 原始数据
        :return: 仪表盘视图的变更配置
        """
        try:
            # 假如metrics已经在changed_config里面，则先要删除
            if "metrics" in changed_configs:
                del changed_configs["metrics"]
                # 两次指标项相同，则直接将原来的changed_config返回
                if ori_data.metrics == self.metrics:
                    return changed_configs
                old_metrics = json.loads(ori_data.metrics)
                current_metrics = json.loads(self.metrics)
                # 指标的变更为一个列表
                metrics_changed_list = []
                # 获取两者的最少长度，表示指标由什么变为什么
                mutual_item_count = min(len(old_metrics), len(current_metrics))
                for i in range(mutual_item_count):
                    # 相等则不做操作直接继续下一个
                    if old_metrics[i] == current_metrics[i]:
                        pass
                    else:
                        metrics_changed_config = {"indicator_index": i, "action": "update"}
                        for tmp_key, tmp_value in six.iteritems(old_metrics[i]):
                            if tmp_value != current_metrics[i][tmp_key]:
                                metrics_changed_config[tmp_key] = {
                                    "key": tmp_key,
                                    "title": self.METRICS_NAME[tmp_key],
                                    "ori_value": tmp_value,
                                    "dst_value": current_metrics[i][tmp_key],
                                }
                        metrics_changed_list.append(metrics_changed_config)
                # 旧指标更多，表示删除
                if len(old_metrics) > mutual_item_count:
                    for i in range(mutual_item_count, len(old_metrics)):
                        metrics_changed_config = {"indicator_index": i, "action": "delete"}
                        for tmp_key, tmp_value in six.iteritems(old_metrics[i]):
                            if tmp_key in self.DISPLAY_FIELDS:
                                metrics_changed_config[tmp_key] = {
                                    "key": tmp_key,
                                    "title": self.METRICS_NAME[tmp_key],
                                    "ori_value": tmp_value,
                                    "dst_value": "",
                                }
                        metrics_changed_list.append(metrics_changed_config)
                # 新指标更多，表示新增
                if len(current_metrics) > mutual_item_count:
                    for i in range(mutual_item_count, len(current_metrics)):
                        metrics_changed_config = {"indicator_index": i, "action": "create"}
                        for tmp_key, tmp_value in six.iteritems(current_metrics[i]):
                            if tmp_key in self.DISPLAY_FIELDS:
                                metrics_changed_config[tmp_key] = {
                                    "key": tmp_key,
                                    "title": self.METRICS_NAME[tmp_key],
                                    "ori_value": "",
                                    "dst_value": tmp_value,
                                }
                        metrics_changed_list.append(metrics_changed_config)
                changed_configs["metrics"] = metrics_changed_list
        except Exception:
            pass
        return changed_configs

    def dashboard_view_gen_op_desc_by_changed_config(self, changed):
        """
        通过变更配置来生成配置的变更逻辑
        :param changed: 变更配置
        :return: 变更描述
        """
        op_desc = _(self.get_title() + _("的"))
        if len(changed) < 1:
            return ""

        for key in changed:
            if key == "metrics":
                op_desc_list = []
                for metrics_indicator in changed["metrics"]:
                    if metrics_indicator["action"] == "create":
                        # 新增操作
                        op_desc_list.append(_(" 指标%s被创建") % (metrics_indicator["indicator_index"] + 1,))
                    elif metrics_indicator["action"] == "delete":
                        # 删除操作
                        op_desc_list.append(_(" 指标%s被删除") % (metrics_indicator["indicator_index"] + 1,))
                    else:
                        # 更新操作
                        tmp_desc = ""
                        for tmp_key, tmp_value in six.iteritems(metrics_indicator):
                            # 只展示需要展示的字段
                            if tmp_key in self.DISPLAY_FIELDS:
                                # 需要拼接 where 子句
                                if tmp_key == "where_field_list":
                                    # 将 where 子句用 and 连接
                                    ori_where = " and ".join(
                                        "{field}{method}{value}".format(
                                            field=i["field"], method=i["method"], value=i["value"]
                                        )
                                        for i in tmp_value["ori_value"][0]
                                    )
                                    cur_where = " and ".join(
                                        "{field}{method}{value}".format(
                                            field=i["field"], method=i["method"], value=i["value"]
                                        )
                                        for i in tmp_value["dst_value"][0]
                                    )
                                    tmp_desc += _("%(title)s由 [%(ori_val)s] 被修改为 [%(dst_val)s]") % {
                                        "title": self.METRICS_NAME[tmp_key],
                                        "ori_val": ori_where,
                                        "dst_val": cur_where,
                                    }
                                else:
                                    tmp_desc += _("%(title)s由 [%(ori_val)s] 被修改为 [%(dst_val)s]") % {
                                        "title": self.METRICS_NAME[tmp_key],
                                        "ori_val": tmp_value.get("ori_value", ""),
                                        "dst_val": tmp_value.get("dst_value", ""),
                                    }
                        if tmp_desc:
                            op_desc_list.append(
                                "{}{}".format(_(" 指标%s的") % (metrics_indicator["indicator_index"] + 1,), tmp_desc)
                            )
                op_desc += ";".join(op_desc_list)

            else:
                changed_attr = changed[key]
                op_desc += _("%(title)s由 [%(ori_val)s] 被修改为 [%(dst_val)s]") % {
                    "title": changed_attr.get("title", key),
                    "ori_val": changed_attr.get("ori_value", ""),
                    "dst_val": changed_attr.get("dst_value", ""),
                }
        return op_desc


class DashboardMenuLocation(OperateRecordModel):
    # 仪表盘上图表link
    view_index = models.IntegerField(_("视图展示顺序"), default=999)
    view_size = models.IntegerField(_("视图大小"), default=12)
    view = models.ForeignKey(DashboardView, verbose_name=_("仪表盘视图"), related_name="locations")
    menu = models.ForeignKey(DashboardMenu, verbose_name=_("仪表盘菜单"))


class HostProperty(models.Model):
    property = models.CharField(_("属性"), max_length=32)
    property_display = models.CharField(_("属性展示名称"), max_length=32)
    required = models.BooleanField(_("必选"), default=False)
    selected = models.BooleanField(_("勾选"), default=False)
    is_deleted = models.BooleanField(_("已删除"), default=False)
    index = models.FloatField(_("排列顺序"), default=0)

    def field_index(self):
        return self.index or self.id

    def refresh_index(self):
        return {"name": self.property_display, "required": self.required, "index": self.field_index()}


class HostPropertyConfManage(OperateManager):
    def init(self, biz_id):
        prop_list = HostProperty.objects.filter(is_deleted=False)
        conf_list = []
        for prop in prop_list:
            conf_list.append(
                {
                    "id": prop.property,
                    "name": prop.property_display,
                    "required": prop.required,
                    "selected": prop.selected,
                    "index": prop.field_index(),
                }
            )
        conf_list.sort(key=lambda x: 1 if x["id"] == "component" else 0)
        conf = self.model(biz_id=biz_id, property_list=json.dumps(conf_list))
        conf.save()
        return conf

    def parse_conf(self, conf_str):
        prop_list = json.loads(conf_str)
        id_list = []
        new_prop_list = []
        for prop in prop_list:
            id_list.append(prop["id"])
            prop_query = HostProperty.objects.filter(property=prop["id"], is_deleted=False)
            if prop_query.exists():
                prop.update(prop_query.get().refresh_index())
                new_prop_list.append(prop)
        remain_prop = HostProperty.objects.filter(is_deleted=False).exclude(property__in=id_list)
        for prop in remain_prop:
            new_prop_list.append(
                {
                    "id": prop.property,
                    "name": prop.property_display,
                    "required": prop.required,
                    "selected": prop.selected,
                    "index": prop.field_index(),
                }
            )
        # new_prop_list.sort(cmp=None, key=lambda p: p["selected"], reverse=True)
        new_prop_list.sort(key=lambda p: p["index"], reverse=False)
        new_prop_list.sort(key=lambda x: 1 if x["id"] == "component" else 0)
        return new_prop_list


class HostPropertyConf(OperateRecordModel):
    biz_id = models.IntegerField(_("业务ID"))
    property_list = models.TextField(_("属性列表"))

    objects = HostPropertyConfManage()


class RolePermission(OperateRecordModel):
    # 角色权限
    biz_id = models.IntegerField(_("业务ID"))
    role = models.CharField(_("角色"), max_length=128)
    permission = models.CharField(_("权限"), max_length=32, default="", blank=True)

    @classmethod
    def get_role_permission_by_role_list(cls, biz_id, role):
        if isinstance(role, str):
            rp = cls.objects.filter(biz_id=biz_id, role=role)
            if rp:
                return rp[0].permission
            else:
                return settings.DEFAULT_ROLE_PERMISSIONS.get(role, "")
        else:
            p_list = []
            for r in role:
                p_list.append(cls.get_role_permission_by_role_list(biz_id, r))
            if not p_list:
                return ""
            p_list.sort(key=lambda p: ["w", "r", ""].index(p))
            return p_list[0]

    def gen_operate_desc(self, operate, ori_data=False):
        """
        根据操作类型，与变更前后的配置生成操作说明
        :param operate: 操作类型：create/update/delete
        :param ori_data: 操作前的配置信息 [可选]
        :return: operate_desc 变更说明
        """
        op_desc = self.get_title()
        if operate in ["create", "delete"]:
            return op_desc
        elif operate == "update":
            if not ori_data:
                return op_desc
            # 获得2次修改之间， 变更了哪些配置
            changed_config = self.get_operate_changed_config(ori_data)
            # 根据变更的配置， 生成对应的wording
            op_desc = self.gen_op_desc_by_changed_config(changed_config)
        return op_desc

    def get_title(self):
        return _("角色权限修改")

    def get_operate_changed_config(self, ori_data):
        changed_configs = {}
        current_permission = self.permission
        ori_permissoin = ori_data.permission
        if not ori_permissoin:
            ori_permissoin = "r"
        if current_permission != ori_permissoin:
            if current_permission == "r" and ori_permissoin == "w":
                changed_configs["role_permission"] = {
                    "key": "role_permission",
                    "title": _("权限类型"),
                    "ori_value": _("查询,变更"),
                    "dst_value": _("查询"),
                }
            else:
                changed_configs["role_permission"] = {
                    "key": "role_permission",
                    "title": _("权限类型"),
                    "ori_value": _("查询"),
                    "dst_value": _("查询,变更"),
                }
        return changed_configs

    def gen_op_desc_by_changed_config(self, changed):
        op_desc = ""
        if len(changed) < 1:
            return op_desc

        role = self.role
        role_name = settings.NOTIRY_MAN_DICT.get(role, role)

        for key in changed:
            changed_attr = changed[key]
            op_desc += _("%(who)s的%(title)s由 [%(ori_val)s] 修改为 [%(dst_val)s]\n") % {
                "who": role_name,
                "title": changed_attr.get("title", key),
                "ori_val": changed_attr.get("ori_value", ""),
                "dst_val": changed_attr.get("dst_value", ""),
            }
        return op_desc


class MetricConf(models.Model):
    # tsdb指标配置
    category = models.CharField(_("指标大类"), max_length=32)
    metric = models.CharField(_("指标id"), max_length=128)
    metric_type = models.CharField(_("指标分类"), max_length=128)
    description = models.CharField(_("指标说明"), max_length=128)
    display = models.TextField(_("指标详细展示"))
    index = models.FloatField(_("指标顺序index"), default=0)

    # 单位转换
    conversion = models.FloatField(_("换算除数"), default=1.0)
    conversion_unit = models.CharField(_("转换单位"), max_length=32, default="", blank=True)

    @property
    def metric_index(self):
        return self.id if self.index == 0 else self.index


class MetricMonitor(OperateRecordModel):
    # 指标监控项
    view_id = models.IntegerField(_("仪表盘视图id"))
    metric_id = models.CharField(_("指标id"), max_length=36)
    monitor_id = models.IntegerField(_("监控项id"))


class Application(models.Model):
    cc_biz_id = models.IntegerField(unique=True)

    name = models.CharField(
        max_length=128,
    )

    groups = models.ManyToManyField(
        Group,
        through="ApplicationGroupMembership",
    )

    class Meta:
        permissions = (
            ("view_application", "Can view application"),
            ("manage_application", "Can manage application"),
        )

    def __unicode__(self):
        return "#{} {}".format(self.cc_biz_id, self.name)


class ApplicationGroupMembership(models.Model):
    application = models.ForeignKey(Application)
    group = models.ForeignKey(Group)

    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("application", "group")

    def __unicode__(self):
        return "Application #{}: Group #{}".format(self.application_id, self.group_id)


class IndexColorConf(models.Model):
    """性能指标颜色配置"""

    range = models.CharField(_("取值区间"), max_length=20)
    color = models.CharField(_("颜色"), max_length=10)
    slug = models.CharField(_("方案标签"), max_length=32)


# 配置相关使用key-value形式存储
# key的格式: '[dashboard_view_config]:menu_id=1'
class UserConfig(models.Model):
    """用户配置信息"""

    username = models.CharField(_("用户名"), max_length=30)
    key = models.CharField("key", max_length=255)
    value = ConfigDataField(_("配置信息"))
    data_created = models.DateTimeField(_("创建时间"), auto_now_add=True)
    data_updated = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("用户配置信息")
        unique_together = (("username", "key"),)


class ApplicationConfig(models.Model):
    """业务配置信息"""

    cc_biz_id = models.IntegerField(_("业务id"))
    key = models.CharField("key", max_length=255)
    value = ConfigDataField(_("配置信息"))
    data_created = models.DateTimeField(_("创建时间"), auto_now_add=True)
    data_updated = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("业务配置信息")
        unique_together = (("cc_biz_id", "key"),)


class GlobalConfig(models.Model):
    """全局配置信息"""

    key = models.CharField("key", max_length=255, unique=True)
    value = ConfigDataField(_("配置信息"))
    data_created = models.DateTimeField(_("创建时间"), auto_now_add=True)
    data_updated = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("全局配置信息")


class CollectorConfig(OperateRecordModel):
    """
    采集配置抽象类
    """

    def get_collector_manager(self):
        raise NotImplementedError

    def get_config_manager(self):
        raise NotImplementedError

    def get_result_tables(self):
        raise NotImplementedError

    def get_data_accessor(self, result_tables):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        try:
            # 尝试停用采集项，停用失败则忽略
            remove_config_result = self.save_config(self.instances.all(), action="remove")
            logger.info(_("配置 [{}] 停用执行结果：{}").format(self.id, remove_config_result))
        except Exception as e:
            logger.warning(_("配置 [{}] 停用失败，原因：{}").format(self.id, e))
        # 删除采集项时，移除采集配置，对应的监控项也要删除
        self.instances.all().delete()
        return super(CollectorConfig, self).delete(*args, **kwargs)

    @classmethod
    def to_host_dict_list(cls, instances):
        """
        将实例列表转换为主机列表
        """
        hosts = []
        for instance in instances:
            hosts += instance.host_dict_list
        return hosts

    def test_config(self, instances):
        """
        测试流程
        """
        collector_manager = self.get_collector_manager()
        config_manager = self.get_config_manager()
        test_config_file, deploy_result = config_manager.deploy_test_config(instances)
        install_result = collector_manager.upgrade_or_install(deploy_result["success"])
        run_result = collector_manager.run_test(install_result["success"], test_config_file)
        result = {
            "success": run_result["success"],
            "failed": deploy_result["failed"] + install_result["failed"] + run_result["failed"],
        }
        return result

    def save_config(self, instances, action="append"):
        """
        保存配置并托管
        """
        collector_manager = self.get_collector_manager()
        config_manager = self.get_config_manager()
        hosts = self.to_host_dict_list(instances)
        collector_manager.upgrade_or_install(hosts)
        deploy_result = config_manager.update_config(instances, action)
        deposit_result = collector_manager.start_deposit(deploy_result["success"])
        return {
            "success": deposit_result["success"],
            "failed": deposit_result["failed"] + deploy_result["failed"],
        }

    def access(self):
        result_tables = self.get_result_tables()
        data_accessor = self.get_data_accessor(result_tables)
        return data_accessor.access()

    def get_operator(self):
        try:
            request = get_request()
        except Exception:
            request = None

        if not request:
            return self.update_user

        username = request.user.username

        if request.user.is_superuser:
            # 如果为超级管理员，则直接以当前业务运维权限执行
            bk_biz_id = getattr(self, "bk_biz_id", getattr(self, "biz_id", None))
            biz = resource.cc.get_app_by_id(bk_biz_id)
            if biz.maintainers:
                username = biz.maintainers[0]
        return username

    class Meta:
        abstract = True


class ScriptCollectorConfig(CollectorConfig):
    """
    新脚本采集
    """

    class ScriptType(object):
        FILE = "file"
        CMD = "cmd"

    class Status(object):
        DRAFT = "draft"
        SAVED = "saved"

    CHARSET_CHOICES = (
        ("UTF8", "UTF8"),
        ("GBK", "GBK"),
    )

    SCRIPT_TYPE_CHOICES = (
        (ScriptType.FILE, _("脚本")),
        (ScriptType.CMD, _("命令行")),
    )

    SCRIPT_EXT_CHOICES = (
        ("shell", "shell"),
        ("bat", "bat"),
        ("python", "python"),
        ("perl", "perl"),
        ("powershell", "powershell"),
        ("vbs", "vbs"),
        ("custom", _("自定义")),
    )

    STATUS_CHOICES = (
        (Status.DRAFT, _("新建未保存")),
        (Status.SAVED, _("已保存")),
    )

    permission_exempt = True

    TSDB_NAME = SHELL_COLLECTOR_DB

    bk_biz_id = models.IntegerField(_("业务ID"))
    data_id = models.IntegerField(_("创建的data id"), null=True, blank=True)

    name = models.CharField(_("数据表名"), max_length=30)
    description = models.CharField(_("数据表中文含义"), max_length=15)
    charset = models.CharField(_("字符集"), max_length=20, choices=CHARSET_CHOICES)
    fields = JsonField(_("字段信息(json)"))

    script_type = models.CharField(_("脚本类型"), max_length=20, choices=SCRIPT_TYPE_CHOICES, default="file")
    script_ext = models.CharField(_("脚本格式"), max_length=20, choices=SCRIPT_EXT_CHOICES, default="shell")
    params_schema = JsonField(_("脚本参数模型"), null=True)
    script_run_cmd = models.TextField(_("启动命令（脚本模式）"), null=True, blank=True)
    script_content_base64 = models.TextField(_("脚本内容"), null=True, blank=True)
    start_cmd = models.TextField(_("启动命令（命令行模式）"), null=True, blank=True)

    collect_interval = models.PositiveIntegerField(_("采集周期(分钟)"), default=1)
    raw_data_interval = models.PositiveIntegerField(_("原始数据保存周期(天)"), default=30)

    status = models.CharField(_("当前状态"), max_length=20, choices=STATUS_CHOICES, default=Status.DRAFT)

    class Meta:
        verbose_name = _("脚本采集配置")

    def __unicode__(self):
        return "{}({})".format(self.description, self.name)

    def get_result_tables(self):
        result_table_field_list = []
        for field in self.fields:
            result_table_field_list.append(
                ResultTableField(
                    field_name=field["name"],
                    description=field["description"],
                    tag=field["monitor_type"],
                    field_type=field["type"],
                    unit=field["unit"],
                )
            )

        result_table = ResultTable(table_name=self.name, description=self.description, fields=result_table_field_list)

        return [result_table]

    def get_data_accessor(self, result_tables):
        return DataAccessor(
            bk_biz_id=self.bk_biz_id,
            db_name=self.TSDB_NAME,
            tables=result_tables,
            etl_config="bk_standard",
            operator=self.update_user,
        )

    def access(self):
        data_id = super(ScriptCollectorConfig, self).access()
        self.data_id = data_id
        self.status = self.Status.SAVED
        self.save()
        return data_id

    @property
    def is_old_config(self):
        try:
            old_script_config = GlobalConfig.objects.get(key="old_script_filename")
        except GlobalConfig.DoesNotExist:
            return False
        return str(self.id) in old_script_config.value

    @property
    def rt_id(self):
        return gen_tsdb_rt(self.bk_biz_id, self.TSDB_NAME, self.name)

    @property
    def table_name(self):
        return "{}_{}".format(self.TSDB_NAME, self.name)

    @property
    def script_content(self):
        if not self.script_content_base64:
            return ""
        try:
            decode_result = base64.b64decode(self.script_content_base64)
        except Exception as e:
            raise CustomException(_("脚本内容解析失败：%s") % e)
        return decode_result

    @property
    def run_command(self):
        if self.script_type == self.ScriptType.CMD:
            return self.start_cmd
        return self.script_run_cmd

    @property
    def script_name(self):
        script_ext = {
            "shell": "sh",
            "bat": "bat",
            "python": "py",
            "perl": "pl",
            "powershell": "ps1",
            "vbs": "vbs",
            "custom": None,
        }.get(self.script_ext, None)
        if not script_ext:
            return self.name
        return "{name}.{ext}".format(name=self.name, ext=script_ext)

    def test_config(self, instances):
        result = super(ScriptCollectorConfig, self).test_config(instances)
        # 解析run_result中的log_content判断脚本是否真正执行成功
        success_list = []
        for success_result in result["success"]:
            content_list = success_result.get("log_content").split("\n")
            try:
                failed_content = [content for content in content_list if json.loads(content).get("error_code") != 0]
                if len(failed_content) > 0:
                    success_result["errmsg"] = success_result.pop("log_content")
                    result["failed"].append(success_result)
                else:
                    success_list.append(success_result)

            except ValueError:
                success_result["errmsg"] = success_result.pop("log_content")
                result["failed"].append(success_result)

        result["success"] = success_list
        return result


class CollectorInstance(OperateRecordModel):
    """
    实例配置抽象类
    """

    INSTANCE_TYPE_CHOICES = (
        ("host", _("主机")),
        ("topo", _("拓扑")),
    )

    type = models.CharField(_("实例类型"), max_length=20, default="host", choices=INSTANCE_TYPE_CHOICES)
    bk_biz_id = models.IntegerField(_("业务ID"))
    ip = models.CharField(_("主机IP"), max_length=30, null=True, blank=True)
    bk_cloud_id = models.IntegerField(_("云区域ID"), null=True, blank=True)
    bk_obj_id = models.CharField(_("拓扑对象ID"), max_length=50, null=True, blank=True)
    bk_inst_id = models.IntegerField(_("拓扑对象实例ID"), null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def bk_cloud_name(self):
        host = Host({"ip": self.ip, "bk_cloud_id": self.bk_cloud_id}, bk_biz_id=self.bk_biz_id)
        if host.fetch_all_host_field():
            return host.bk_cloud_id[0]["bk_inst_name"]
        return str(self.bk_cloud_id)

    def param_equals(self, other_instance):
        """
        判断两个实例的下发参数是否相等
        具有相等配置的实例列表将整合为一个JOB任务执行，从而优化配置下发速度
        可由子类进行重写
        """
        return False

    @property
    def host_dict_list(self):
        """
        将实例转化为主机列表
        """
        if self.type == "host":
            host = Host({"ip": self.ip, "bk_cloud_id": self.bk_cloud_id})
            return [host.host_dict]
        return []

    def delete(self, *args, **kwargs):
        try:
            # 尝试停用，停用失败则忽略
            remove_config_result = self.config.save_config([self], action="remove")
            logger.info(_("配置 [{}] 停用执行结果：{}").format(self.config.id, remove_config_result))
        except Exception as e:
            logger.warning(_("配置 [{}] 停用失败：{}").format(self.config.id, e))
        return super(CollectorInstance, self).delete(*args, **kwargs)


class ScriptCollectorInstance(CollectorInstance):
    """
    采集实例
    """

    config = models.ForeignKey(ScriptCollectorConfig, verbose_name=_("配置"), related_name="instances")
    params = JsonField(_("脚本执行参数"))

    permission_exempt = True

    class Meta:
        verbose_name = _("脚本采集实例")

    def param_equals(self, other_instance):
        return self.params == other_instance.params

    def generate_single_config(self, script_path=""):
        params = copy.deepcopy(self.params) or {}
        run_command = self.config.run_command
        if self.config.script_type == self.config.ScriptType.FILE:
            params["bk_script_name"] = script_path

            # 对启动命令中的变量进行格式替换。{xxx: 123} + ${xxx} => 123
            for key, value in list(params.items()):
                format_string = "${%s}" % key
                run_command = run_command.replace(format_string, value)

        return {
            "bk_biz_id": self.config.bk_biz_id,
            "task_id": self.config.id,
            "dataid": self.config.data_id or 0,
            "timeout": "60s",
            "period": "%ss" % (self.config.collect_interval * 60),
            "command": run_command,
            "user_env": {},
        }


class ShellCollectorParamsMixin(models.Model):
    """脚本采集参数模版"""

    CHARSET_CHOICES = (
        ("UTF8", "UTF8"),
        ("GBK", "GBK"),
    )

    TSDB_NAME = SHELL_COLLECTOR_DB

    # 通用参数
    biz_id = models.IntegerField(_("业务ID"))

    data_id = models.IntegerField(_("创建的data id"), null=True, blank=True)
    rt_id = models.CharField(_("结果表名"), null=True, blank=True, max_length=100)

    # 第一步 - 定义表结构
    table_name = models.CharField(_("数据表名"), max_length=30)
    table_desc = models.CharField(_("数据表中文含义"), max_length=15)
    charset = models.CharField(_("字符集"), max_length=20, choices=CHARSET_CHOICES)
    fields = JsonField(_("字段信息(json)"))

    # 第二步 - 编写采集脚本
    shell_content = models.TextField(_("脚本内容"), null=True)

    # 第三步 - 选择服务器
    ip_list = JsonField(_("IP列表(json)"), null=True, blank=True)
    scope = JsonField(_("大区信息(json)"), null=True, blank=True)

    # 第五步 - 设置采集周期
    collect_interval = models.PositiveIntegerField(_("采集周期(分钟)"), default=1)
    raw_data_interval = models.PositiveIntegerField(_("原始数据保存周期(天)"), default=30)
    trend_data_interval = models.PositiveIntegerField(_("趋势数据保存周期(天)"), default=90)

    @property
    def shell_name(self):
        hash_val = hashlib.md5(self.shell_content).hexdigest()
        name = "{biz_id}_{table_name}_{hash_val}".format(
            biz_id=self.biz_id, table_name=self.table_name, hash_val=hash_val
        )
        return name

    @property
    def rt_name(self):
        return gen_tsdb_rt(self.biz_id, self.TSDB_NAME, self.table_name)

    @rt_name.setter
    def rt_name(self, value):
        self.rt_id = value

    @property
    def full_table_name(self):
        return "{}_{}".format(self.TSDB_NAME, self.table_name)

    class Meta:
        abstract = True


class ShellCollectorConfig(ShellCollectorParamsMixin, OperateRecordModel):
    """脚本采集配置"""

    class Status(object):
        NEW_DRAFT = "new draft"
        EDIT_DRAFT = "edit draft"
        SAVED = "saved"
        DELETE_FAILED = "delete failed"

    STATUS_CHOICES = (
        (Status.NEW_DRAFT, _("新建未保存")),
        (Status.EDIT_DRAFT, _("编辑未保存")),
        (Status.SAVED, _("已保存")),
        (Status.DELETE_FAILED, _("删除失败")),
    )

    STEP_CHOICES = (
        (1, _("定义表结构")),
        (2, _("编写采集脚本")),
        (3, _("选择服务器")),
        (4, _("下发采集测试")),
        (5, _("设置采集周期")),
        (6, _("完成")),
    )

    status = models.CharField(_("当前状态"), max_length=20, choices=STATUS_CHOICES, default=Status.NEW_DRAFT)
    step = models.IntegerField(_("当前步骤(1-6)"), choices=STEP_CHOICES, default=2)

    class Meta:
        verbose_name = _("脚本采集配置")
        verbose_name_plural = _("脚本采集配置")
        ordering = ("-create_time",)


class ShellCollectorDepositTask(ShellCollectorParamsMixin, OperateRecordModel):
    """脚本采集托管任务"""

    class Status(object):
        CREATED = "created"
        RUNNING = "running"
        SUCCESS = "success"
        FAILED = "failed"
        EXCEPTION = "exception"

    STATUS_CHOICES = (
        (Status.CREATED, _("任务创建成功")),
        (Status.RUNNING, _("任务正在执行")),
        (Status.SUCCESS, _("任务执行成功")),
        (Status.FAILED, _("任务执行失败")),
        (Status.EXCEPTION, _("任务执行过程异常")),
    )

    class Process(object):
        READY = "ready"
        CREATE_DATASET = "create dataset"
        CREATE_RT = "create rt"
        SET_ETL_TEMPLATE = "set etl template"
        DEPLOY_TSDB = "deploy_tsdb"
        START_DISPATCH = "start dispatch"
        START_DEPOSIT_TASK = "start deposit task"
        # WAIT_DEPOSIT_TASK = "wait deposit task"
        STOP_OLD_DEPOSIT_TASK = "stop old deposit task"
        FINISHED = "finished"

    PROCESS_CHOICES = (
        (Process.READY, _("任务就绪")),
        (Process.CREATE_RT, _("检查并创建结果表")),
        (Process.CREATE_DATASET, _("检查并创建DataSet")),
        (Process.SET_ETL_TEMPLATE, _("检查并生成清洗配置")),
        (Process.DEPLOY_TSDB, _("检查并创建TSDB")),
        (Process.START_DISPATCH, _("启动入库程序")),
        (Process.START_DEPOSIT_TASK, _("创建脚本托管任务")),
        # (Process.WAIT_DEPOSIT_TASK, _(u"等待脚本托管任务执行结果")),
        (Process.STOP_OLD_DEPOSIT_TASK, _("取消老版本配置的IP托管")),
        (Process.FINISHED, _("任务流程完成")),
    )

    config = models.ForeignKey(ShellCollectorConfig, verbose_name=_("所属配置"), related_name="tasks")

    status = models.CharField(_("任务状态"), choices=STATUS_CHOICES, max_length=50, default=Status.CREATED)

    process = models.CharField(_("任务当前流程"), choices=PROCESS_CHOICES, max_length=50, default=Process.READY)

    result_data = JsonField(_("任务执行结果(JSON)"))
    ex_data = models.TextField(_("任务异常信息"))

    class Meta:
        verbose_name = _("脚本采集托管任务")
        get_latest_by = "update_time"


class ExporterCollectorParamsMixin(models.Model):
    """
    脚本采集参数模版

    一些字段格式
    indices = [
        {
            "table_name": "xxx",
            "table_desc": "yyy",
            "fields": [
                {
                    "name": "test123",
                    "description": "xxx",
                    "unit": "%",
                    "monitor_type": "dimension", # "dimension" or "metric",
                    "type": "double", # "long", "double" or "string"
                }
            ]
        }
    ]

    config_schema = [
        {
            "name": "xxx",
            "description": "desc",
            "type": "text", # "text" or "file",
            "mode": "env", # "env" or "cmd"
            "default": "default_value"
        }
    ]

    config = {
        "execute": {
            "env": {
                "xxx": "yyy"
            },
            "cmd": {
                "aaa": "bbb"
            }
        },
        "collect": {
            "host": "127.0.0.1",
            "port": "8080"
        }
    }

    exporter_file = {
        "origin_file_name": "xxx",  # 用户上传的原文件名
        "file_id": 1234,            # 文件ID
        "file_type": "xxxxx",       # 文件信息
        "file_name": "xxxxxx",      # 真实存储的文件名
        "md5": "xxxxxx",            # 文件的md5
    }

    config_file = [
        {
            "origin_file_name": "xxx",  # 用户上传的原文件名
            "file_id": 1234,            # 文件ID
            "file_type": "xxxxx",       # 文件信息
            "file_name": "xxxxxx",      # 真实存储的文件名
            "md5": "xxxxxx",            # 文件的md5
        }
    ]
    """

    TSDB_NAME = "exporter"

    CHARSET_CHOICES = (
        ("UTF8", "UTF8"),
        ("GBK", "GBK"),
    )

    OS_FIELD_MAPPING = {
        "linux": "exporter_file_info",
        "windows": "windows_exporter_file_info",
        "aix": "aix_exporter_file_info",
    }

    # 通用参数
    biz_id = models.IntegerField(_("业务ID"))

    data_id = models.IntegerField(_("创建的data id"), null=True, blank=True)
    rt_id_list = JsonField(_("虚拟结果表名(列表)"), default=[])
    parent_rt_id = models.CharField(_("实体结果表名"), null=True, blank=True, max_length=100)

    # 第一步 - 导入组件
    component_name = models.CharField(_("组件名称"), max_length=15)
    component_name_display = models.CharField(_("组件中文含义"), max_length=128)
    component_desc = models.TextField(_("组件详细描述(md)"), default="", blank=True)

    indices = JsonField(_("指标项(json)"), default=[])
    exporter_id = models.IntegerField("Exporter ID", default=0)
    exporter_file_info = JsonField(_("上传的Exporter文件信息(Linux)"), null=True, blank=True)
    windows_exporter_file_info = JsonField(_("上传的Exporter文件信息(Windows)"), null=True, blank=True)
    aix_exporter_file_info = JsonField(_("上传的Exporter文件信息(AIX)"), null=True, blank=True)

    logo = models.TextField(_("logo的base64编码"), default="", blank=True)
    logo_small = models.TextField(_("小logo的base64编码"), default="", blank=True)

    charset = models.CharField(_("字符集"), max_length=20, choices=CHARSET_CHOICES, default="UTF8")

    config_schema = JsonField(_("配置模型(json)"), default=[])

    # 第二步 - 选择服务器
    ip_list = JsonField(_("IP列表(json)"), default=[])
    scope = JsonField(_("大区信息(json)"), null=True, blank=True)

    # 第三步 - 填写字段
    cleaned_config_data = JsonField(_("参数填写配置"), null=True, blank=True)
    config = JsonField(_("参数配置"), default={})
    config_files_info = JsonField(_("上传的配置文件详情列表"), null=True, blank=True)

    # 第五步 - 设置采集周期
    collect_interval = models.PositiveIntegerField(_("采集周期(分钟)"), default=1)
    raw_data_interval = models.PositiveIntegerField(_("原始数据保存周期(天)"), default=30)
    trend_data_interval = models.PositiveIntegerField(_("趋势数据保存周期(天)"), default=90)

    def set_exporter_file_info(self, file_info, os_type):
        """
        根据系统类型，把exporter上传信息写入不同的字段中
        :param file_info: 文件信息
        :param os_type: 系统类型
        """
        if os_type in self.OS_FIELD_MAPPING:
            setattr(self, self.OS_FIELD_MAPPING[os_type], file_info)

    @property
    def parent_rt_fields(self):
        """
        实体表的表结构，由多个虚拟表结构共同决定，对虚拟表的维度字段做交集，
        得出实体表的所有维度字段
        """

        names = []
        for table in self.indices:
            names += [field["name"] for field in table["fields"] if field["monitor_type"] == "dimension"]
        # 维度字段去重
        names = set(names)

        # 默认维度metric_name和metric_value
        fields = [
            {
                "name": "metric_name",
                "description": _("指标名称"),
                "unit": "",
                "monitor_type": "dimension",
                "type": "string",
            },
            {"name": "metric_value", "description": _("指标值"), "unit": "", "monitor_type": "metric", "type": "double"},
        ]

        for name in names:
            fields.append(
                {"name": name, "description": name, "unit": "", "monitor_type": "dimension", "type": "string"}
            )
        return fields

    @property
    def parent_rt_name(self):
        return gen_tsdb_rt(self.biz_id, self.TSDB_NAME, self.component_name)

    @property
    def full_component_name(self):
        return "{}_{}".format(self.TSDB_NAME, self.component_name)

    @property
    def field_attrs(self):
        return [field.attname for field in ExporterCollectorParamsMixin._meta.fields]

    class Meta:
        abstract = True


class ExporterComponent(ExporterCollectorParamsMixin, CollectorConfig):
    """
    Exporter自定义组件配置
    """

    class Status(object):
        DRAFT = "DRAFT"
        SAVED = "SAVED"

    STATUS_CHOICES = (
        (Status.DRAFT, _("未保存")),
        (Status.SAVED, _("已保存")),
    )

    is_internal = models.BooleanField(_("是否为内置组件"), default=False)
    version = models.CharField(_("组件版本号（仅限内置组件）"), blank=True, default="", max_length=30)

    status = models.CharField(_("当前状态"), max_length=20, choices=STATUS_CHOICES, default=Status.DRAFT)

    class Meta:
        verbose_name = _("自定义组件")
        verbose_name_plural = _("自定义组件")

    @property
    def component_name_editable(self):
        """
        判断当前的组件名称是否可编辑
        """
        return False

    @property
    def config_form_html(self):
        return self.config_form(label_suffix="").as_ul()

    @property
    def config_form(self):
        return self.gen_config_form(self.config_schema, self.cleaned_config_data)

    @property
    def category_id(self):
        category = ComponentCategoryRelationship.get_category(exporter_component_id=self.id)
        if not category:
            return 0
        return category["id"]

    @category_id.setter
    def category_id(self, val):
        ComponentCategoryRelationship.set_category(category_id=val, exporter_component_id=self.id)

    @classmethod
    def gen_config_form(cls, config_schema, default_data=None):
        """
        将config_schema转化为django form cls
        """

        default_data = default_data or {}

        field_type_mapping = {
            "text": forms.CharField,
            "file": forms.FileField,
            "password": forms.CharField,
        }

        fields = {}
        cmd_keys = []
        env_keys = []
        collector_keys = []

        for config in config_schema:

            # 初始化Field实例
            if config["type"] == "password":
                field = forms.CharField(required=False, widget=forms.PasswordInput())
            else:
                field = field_type_mapping.get(config["type"], forms.CharField)(required=False)

            if not config.get("visible", True):
                # 设置为不可见的配置项，不呈现给用户
                field.widget = forms.HiddenInput()

            # 增加自定义属性，用于区分参数类型
            field.widget.attrs.update({"data-mode": config["mode"]})
            if config["mode"] == "cmd":
                # 命令行类型参数
                cmd_keys.append(config["name"])
            elif config["mode"] == "env":
                # 环境变量类型参数
                env_keys.append(config["name"])
            elif config["mode"] == "collector":
                # 采集器相关参数
                collector_keys.append(config["name"])

            field.label = ugettext_lazy(config["description"])

            if config["mode"] == "collector":
                # 采集器默认参数不允许修改
                field.initial = config["default"]
            else:
                field.initial = default_data.get(config["name"], config["default"])

            fields[config["name"]] = field

        class BaseForm(forms.Form):
            """
            配置Form类模版
            """

            class Meta:
                cmd_fields = cmd_keys
                env_fields = env_keys
                collector_fields = collector_keys

        return type(str("ConfigForm"), (BaseForm,), fields)

    def adapt_to_standard_indices(self):
        """
        将指标适配为标准的扁平化结构的index_list
        """
        index_list = []
        for table in self.indices:
            dimension_fields = ",".join([f["name"] for f in table["fields"] if f["monitor_type"] == "dimension"])
            for field in table["fields"]:
                if field["monitor_type"] == "metric":
                    result_table_id = "exporter_{}_{}".format(self.component_name, table["table_name"])
                    description = _("%(name)s\n\n单位：%(unit)s\n\n含义：%(desc)s") % {
                        "name": field["name"],
                        "unit": field["unit"],
                        "desc": field["description"],
                    }
                    index_list.append(
                        {
                            "item": field["name"],
                            "item_display": "{}({})".format(field["description"], field["name"]),
                            "conversion_unit": field["unit"],
                            "conversion": field.get("conversion", 1.0),
                            "result_table_id": result_table_id,
                            "dimension_field": dimension_fields,
                            "category_display": "{}({})".format(table["table_desc"], table["table_name"]),
                            "description": description,
                            "extra_info": {"category": self.component_name},
                            "collect_interval": self.collect_interval,
                        }
                    )

        return index_list

    @property
    def exporter_upload_name(self):
        # 为防止exporter名称与组件名称相同导致进程名相同，特对exporter_name进行处理：
        # 统一在最后加上后缀"_exporter"
        exporter_name = "%s_exporter" % self.component_name
        return exporter_name

    @property
    def diff_metrics(self):
        metrics = []
        for table in self.indices:
            for field in table["fields"]:
                if field["monitor_type"] == "metric" and field.get("is_diff_metric"):
                    metrics.append(field["name"])
        return metrics

    def upload_exporter_file(self, exporter_files):
        for os_type, exporter_filename in list(settings.EXPORTER_FILENAME_OS_MAPPING.items()):
            exporter_file_info = None
            if exporter_files.get(os_type):
                exporter_file = exporter_files[os_type]
                wrapped_file = SimpleUploadedFile(exporter_filename, exporter_file.read())
                exporter_file_info = self.upload_file(
                    wrapped_file, self.exporter_upload_name, "{}-{}".format(self.exporter_upload_name, os_type)
                )
            self.set_exporter_file_info(exporter_file_info, os_type)

        self.save()

    def upload_file(self, file_data, file_name=None, dir_name=None):
        return {}

    def clean_config(self, data):
        """
        配置数据清洗
        """
        config_form_cls = self.config_form

        # 第二个data参数用于读取文件类型的field
        config_form = config_form_cls(data, data)

        if not config_form.is_valid():
            raise CustomException(config_form.errors.as_text())
        cleaned_data = config_form.cleaned_data

        config_files = []

        for k, v in list(cleaned_data.items()):
            # 若参数值有存在文件类型的，就上传文件，将字段设置为文件名
            if hasattr(v, "read"):
                result = self.upload_file(v)
                cleaned_data[k] = result["file_name"]
                config_files.append(result)

        cmd_kv = {key: cleaned_data[key] or "" for key in config_form_cls.Meta.cmd_fields if key in cleaned_data}
        env_kv = {key: cleaned_data[key] or "" for key in config_form_cls.Meta.env_fields if key in cleaned_data}
        collector_kv = {
            key: cleaned_data[key] or "" for key in config_form_cls.Meta.collector_fields if key in cleaned_data
        }

        exporter_url = collector_kv.get(EXPORTER_LISTEN_ADDRESS_PARAM_NAME)
        if not exporter_url:
            raise CustomException(_("%s 参数不能为空") % EXPORTER_LISTEN_ADDRESS_PARAM_NAME)

        # exporter_host, exporter_uri = self.parse_url(exporter_url)

        result = {
            "exporter_host": exporter_url,
            "exporter_uri": "",
            "cmd_args": cmd_kv,
            "env_args": env_kv,
        }

        self.cleaned_config_data = cleaned_data
        self.config_files_info = config_files
        self.save()

        return result

    def create_deploy_exporter_task(self, ip_list=None, config=None):
        """
        分发Exporter文件到目标主机
        """
        request = get_request()
        try:
            operator = request.user.username
        except Exception:
            operator = self.update_user

        config = config if config is not None else self.config

        if ip_list is None:
            ip_list = copy.deepcopy(self.ip_list)

        config_files = self.config_files_info or []
        config_file_ids = [file["file_id"] for file in config_files]

        # 实时获取当前主机的操作系统
        hosts = resource.cc.hosts(self.biz_id)

        # 给业务下的所有主机建立索引，便于查找
        ip_os_dict = {}
        for host in hosts:
            ip_os_dict[host.host_id] = host.bk_os_type_name

        for ip_info in ip_list:
            host_id = host_key(ip=ip_info["ip"], plat_id=ip_info["plat_id"])
            ip_info["os_type"] = ip_os_dict.get(host_id, "linux")
            ip_info["origin_os_type"] = ip_info["os_type"]
            if ip_info["os_type"] == "aix":
                ip_info["os_type"] = "linux"

        all_deploy_result = {
            "success": [],
            "pending": [],
            "failed": [],
        }

        target_path = {
            "linux": posixpath.join(settings.LINUX_EXPORTER_COLLECTOR_SETUP_PATH, self.exporter_upload_name),
            "windows": ntpath.join(settings.WINDOWS_EXPORTER_COLLECTOR_SETUP_PATH, self.exporter_upload_name),
            "aix": posixpath.join(settings.AIX_EXPORTER_COLLECTOR_SETUP_PATH, self.exporter_upload_name),
        }

        for os_type in settings.EXPORTER_FILENAME_OS_MAPPING:
            os_hosts = [host for host in ip_list if host["origin_os_type"] == os_type]

            if not os_hosts:
                continue
            exporter_file_info = getattr(self, self.OS_FIELD_MAPPING[os_type])
            if exporter_file_info:
                deploy_result = resource.commons.file_deploy(
                    bk_biz_id=self.biz_id,
                    operator=operator,
                    file_ids=config_file_ids + [exporter_file_info["file_id"]],
                    hosts=os_hosts,
                    target_path=target_path[os_type],
                )
            else:
                for host in os_hosts:
                    host["errmsg"] = _("该组件暂不支持 %s 系统" % os_type)
                deploy_result = {
                    "success": [],
                    "pending": [],
                    "failed": os_hosts,
                }
            # 结果聚合
            for key in all_deploy_result:
                all_deploy_result[key] += deploy_result[key]

        collector = self.get_collector(cmd_args=config.get("cmd_args"), env_args=config.get("env_args"))
        install_result = collector.upgrade_or_install(all_deploy_result["success"])
        result = {
            "success": install_result["success"],
            "pending": install_result["pending"] + all_deploy_result["pending"],
            "failed": install_result["failed"] + all_deploy_result["failed"],
        }
        return result

    def create_test_exporter_task(self, ip_list=None, config=None):
        """
        采集测试Exporter接口
        """
        config = config if config is not None else self.config

        if ip_list is None:
            ip_list = copy.deepcopy(self.ip_list)

        collector = self.get_collector(cmd_args=config.get("cmd_args"), env_args=config.get("env_args"))
        result = collector.test(
            ip_list, exporter_host=config.get("exporter_host", ""), exporter_uri=config.get("exporter_uri", "")
        )
        return result

    def create_stop_exporter_task(self, ip_list=None):
        """
        停用Exporter接口
        """
        if ip_list is None:
            ip_list = copy.deepcopy(self.ip_list)

        collector = self.get_collector()
        result = collector.stop_deposit(ip_list)
        return result

    def generate_collector_config(self, config):
        return {
            "exporter_host": config["exporter_host"],
            "exporter_uri": config["exporter_uri"],
            "cycle": self.collect_interval * 60,
            "exporter_name": "%s_exporter" % self.component_name,
            "dataid": self.data_id,
            "diff_metrics": self.diff_metrics,
        }

    def create_deposit_task(self):
        """
        创建托管任务
        """
        task = ExporterDepositTask()

        # 逐个赋值
        for attr in self.field_attrs:
            value = getattr(self, attr)
            setattr(task, attr, value)

        task.component_id = self.id
        task.save()

        return task

    def _gen_result_table_fields(self, table_fields):
        """
        生成创建/修改RT表的参数
        """
        fields = []
        for field in table_fields:
            field_info = ResultTableField(
                description=field.get("description", ""),
                field_name=field.get("name", ""),
                tag="metric" if field.get("monitor_type") != "dimension" else "dimension",
                field_type=field.get("type", ""),
                unit=field.get("unit"),
            )

            fields.append(field_info)

        return fields

    def get_result_tables(self):
        result_table_list = []
        rt_id_list = []
        for table in self.indices:
            table_id = "{}.{}".format(self.full_component_name, table["table_name"])
            rt_id_list.append(table_id)
            result_table = ResultTable(
                table_name=table["table_name"],
                description=table["table_desc"],
                fields=self._gen_result_table_fields(table["fields"]),
            )

            result_table_list.append(result_table)

        self.parent_rt_id = self.full_component_name
        self.rt_id_list = rt_id_list
        return result_table_list

    def get_data_accessor(self, result_tables):
        return DataAccessor(
            bk_biz_id=self.biz_id,
            db_name="{}_{}".format(self.TSDB_NAME, self.component_name),
            tables=result_tables,
            etl_config="bk_exporter",
            operator=self.update_user,
        )

    def get_title(self):
        return _("自定义组件配置（%s）") % self.component_name

    def get_special_change_config(self, changed_configs, ori_data):
        if "logo_small" in changed_configs:
            changed_configs.pop("logo_small")
        if "scope" in changed_configs:
            changed_configs.pop("scope")
        dst_ip = ["{}({})".format(i["ip"], i["plat_name"]) for i in self.ip_list] if self.ip_list else []
        ori_ip = ["{}({})".format(i["ip"], i["plat_name"]) for i in ori_data.ip_list] if ori_data.ip_list else []
        is_changed = set(dst_ip) ^ set(ori_ip)
        if is_changed:
            ori_value = ";".join(ori_ip)
            dst_value = ";".join(dst_ip)
            changed_configs["ip_list"] = {
                "key": "ip_list",
                "title": _("IP列表"),
                "ori_value": ori_value,
                "dst_value": dst_value,
            }
        return changed_configs

    def gen_op_desc_by_changed_config(self, changed):
        op_desc = _(self.get_title() + _("的"))
        if len(changed) < 1:
            return ""

        for key in changed:
            changed_attr = changed[key]
            if key == "logo":
                op_desc += _("Logo做了修改 \t")
            else:
                op_desc += _("%(title)s由 [%(ori_val)s] 被修改为 [%(dst_val)s] \t") % {
                    "title": changed_attr.get("title", key),
                    "ori_val": changed_attr.get("ori_value", ""),
                    "dst_val": changed_attr.get("dst_value", ""),
                }
        return op_desc


class ExporterDepositTask(ExporterCollectorParamsMixin, OperateRecordModel):
    """
    自定义组件Exporter托管任务
    """

    class Status(object):
        CREATED = "CREATED"
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
        EXCEPTION = "EXCEPTION"

    STATUS_CHOICES = (
        (Status.CREATED, _("任务创建成功")),
        (Status.RUNNING, _("任务正在执行")),
        (Status.SUCCESS, _("任务执行成功")),
        (Status.FAILED, _("任务执行失败")),
        (Status.EXCEPTION, _("任务执行过程异常")),
    )

    class Process(object):
        READY = "READY"
        CREATE_DATASET = "CREATE_DATASET"
        CREATE_RT = "CREATE_RT"
        SET_ETL_TEMPLATE = "SET_ETL_TEMPLATE"
        DEPLOY_TSDB = "DEPLOY_TSDB"
        START_DISPATCH = "START_DISPATCH"
        START_DEPOSIT_TASK = "START_DEPOSIT_TASK"
        WAIT_DEPOSIT_TASK = "WAIT_DEPOSIT_TASK"
        STOP_OLD_DEPOSIT_TASK = "STOP_OLD_DEPOSIT_TASK"
        FINISHED = "FINISHED"

    PROCESS_CHOICES = (
        (Process.READY, _("任务就绪")),
        (Process.CREATE_RT, _("检查并创建结果表")),
        (Process.CREATE_DATASET, _("检查并创建DataSet")),
        (Process.SET_ETL_TEMPLATE, _("检查并生成清洗配置")),
        (Process.DEPLOY_TSDB, _("检查并创建TSDB")),
        (Process.START_DISPATCH, _("启动入库程序")),
        (Process.START_DEPOSIT_TASK, _("正在托管exporter")),
        (Process.STOP_OLD_DEPOSIT_TASK, _("取消老版本配置的IP托管")),
        (Process.FINISHED, _("任务流程完成")),
    )

    component = models.ForeignKey(ExporterComponent, verbose_name=_("所属组件"), related_name="tasks")

    status = models.CharField(_("任务状态"), choices=STATUS_CHOICES, max_length=50, default=Status.CREATED)

    process = models.CharField(_("任务当前流程"), choices=PROCESS_CHOICES, max_length=50, default=Process.READY)

    result_data = JsonField(_("任务执行结果(JSON)"))
    ex_data = models.TextField(_("任务异常信息"))

    class Meta:
        verbose_name = _("Exporter托管任务")
        get_latest_by = "update_time"

    def update_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def update_process(self, process, save=True):
        self.process = process
        if save:
            self.save()

    def deposit(self):
        """
        托管流程
        """
        self.update_process(self.Process.START_DEPOSIT_TASK)
        task_result = self.component.create_start_exporter_task()

        self.update_task_result("start_deposit", task_result)

        failed_ip_list = self.result_data["start_deposit"]["data"]["failed"]

        if len(failed_ip_list) > 0:
            return False
        return True

    def update_task_result(self, task_name, task_data):
        if not self.result_data:
            self.result_data = {}

        # 不同类型的任务用不同的key记录，方便任务追踪
        self.result_data.update(
            {
                # 嵌一层data是为了兼容老版本数据结构
                task_name: {"data": task_data}
            }
        )
        self.save()

    def stop_deposit(self, ip_list=None):
        """
        TODO: 停止托管
        """
        pass

    def stop_old_deposit_task(self):
        pass

    def create_component_instance(self):
        """
        为组件实例增加对应的条目
        """
        config = json.dumps([self.cleaned_config_data])
        with transaction.atomic():
            for ip_info in self.ip_list:
                ComponentInstance.objects.update_or_create(
                    defaults={"config": config},
                    ip=ip_info["ip"],
                    plat_id=ip_info["plat_id"],
                    component=self.component_name,
                    biz_id=self.biz_id,
                    is_deleted=False,
                )

    def execute(self):
        """
        执行托管任务
        """
        component = self.component
        self.update_status(self.Status.RUNNING)

        try:
            component.data_id = component.access()
            result = self.deposit()
        except Exception as e:
            exc = traceback.format_exc()
            logger.error(exc)
            self.update_status(self.Status.EXCEPTION, save=False)
            self.ex_data = e
            self.save()
            return

        if not result:
            self.update_status(self.Status.FAILED)
            return

        self.create_component_instance()
        self.update_status(self.Status.SUCCESS)

        component.status = component.Status.SAVED
        component.save()

        # 到这里就可以任务已经执行成功了，用户不关注下面的流程了
        # 只要deposit任务执行成功就认为整个任务已经完成
        # 然后静默在后台执行取消老配置托管的任务
        try:
            self.stop_old_deposit_task()
            self.update_process(self.Process.FINISHED)
        except Exception as e:
            exc = traceback.format_exc()
            logger.error(exc)
            self.ex_data = e
            self.save()

    def get_title(self):
        return _("自定义组件Export采集托管任务（%s）") % self.component_name


class ComponentCategory(models.Model):
    display_name = models.CharField(_("分类显示名称"), max_length=50, unique=True)

    @classmethod
    def get_dict_by_name(cls, name):
        try:
            instance = cls.objects.get(name=name)
            return instance.to_dict()
        except cls.DoesNotExist:
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
        }

    class Meta:
        verbose_name = _("组件分类")
        verbose_name_plural = _("组件分类")
        ordering = ["id"]


class ComponentCategoryRelationship(models.Model):
    category = models.ForeignKey(ComponentCategory, null=True, verbose_name=_("所属分类"), related_name="components")
    is_internal = models.BooleanField(_("是否为内置组件"), default=False)
    component_name = models.CharField(_("组件名称（内置组件专用）"), null=True, blank=True, max_length=32)
    exporter_component = models.OneToOneField(
        ExporterComponent, null=True, related_name="relative_category", verbose_name=_("自定义组件（非内置组件专用）")
    )

    @classmethod
    def get_category(cls, component_name=None, exporter_component_id=None):
        """
        根据组件获取组件分类
        :param component_name: 如果是内置组件，则为字符串
        :param exporter_component_id: 如果是自定义组件，则为ExporterComponent实例
        :return: category.to_dict()
        """
        if component_name:
            instance = cls.objects.filter(is_internal=True, component_name=component_name).first()
        else:
            instance = cls.objects.filter(is_internal=False, exporter_component_id=exporter_component_id).first()
        if instance and instance.category:
            return instance.category.to_dict()
        return None

    @classmethod
    def set_category(cls, component_name=None, exporter_component_id=None, category_id=None):
        """
        设置组件分类
        :param category_id: 设置组件分类
        :param component_name: 如果是内置组件，则为字符串
        :param exporter_component_id: 如果是自定义组件，则为ExporterComponent实例
        """
        if not category_id:
            category = None
        else:
            category = ComponentCategory.objects.get(id=category_id)
        params = {"defaults": {"category": category}}

        if component_name:
            has_permission = False
            try:
                request = get_request()
                has_permission = request.user.is_superuser
            except Exception:
                pass
            if not has_permission:
                raise CustomException(_("当前用户无操作权限"))
            params["is_internal"] = True
            params["component_name"] = component_name
        else:
            exporter_component = ExporterComponent.objects.get(id=exporter_component_id)
            params["is_internal"] = False
            params["exporter_component"] = exporter_component
        cls.objects.update_or_create(**params)

    class Meta:
        verbose_name = _("组件分类关系")
        verbose_name_plural = _("组件分类关系")


SERVICE_TYPE_CHOICES = [
    ("charts", _("图表")),
]


class ServiceAuthorization(models.Model):
    create_time = models.DateTimeField(_("创建时间"), auto_now_add=True)
    update_time = models.DateTimeField(_("更新时间"), auto_now=True)
    expire_time = models.DateTimeField(_("过期时间"), null=True, default=None)

    name = models.CharField(_("名称"), max_length=128, null=True, blank=True)
    enable = models.BooleanField(_("启用"), default=True)
    cc_biz_id = models.CharField(_("cc业务id"), max_length=30)
    service_type = models.CharField(_("服务类型"), max_length=30, choices=SERVICE_TYPE_CHOICES)
    service_id = models.CharField(_("服务id"), max_length=30)
    domain = models.TextField(_("命名空间"), null=True, blank=True)
    access_token = models.CharField(_("授权码"), max_length=128, null=False, default=None)

    extra = models.TextField(_("扩展选项"), null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.domain:
            self.domain = ""

        if not self.extra:
            self.extra = "{}"
        return super(ServiceAuthorization, self).save(*args, **kwargs)

    def refresh_access_token(self):
        uid = uuid.uuid4()
        self.access_token = uid.get_hex()

    def validate_service(self):
        if self.service_type == "charts":
            return DashboardView.objects.filter(
                pk=self.service_id,
                biz_id=self.cc_biz_id,
            ).exists()
        return False

    def is_avaliable(self):
        if not self.enable:
            return False
        if not self.expire_time:
            return True
        if arrow.get(time_tools.localtime(self.expire_time)) < arrow.utcnow():
            return False
        return True

    def is_avaliable_for_domain(self, domain):
        from six.moves.urllib.parse import urljoin

        if not self.domain:
            return True

        my_domain = self.domain
        if self.domain.startswith("/"):
            my_domain = urljoin(domain, my_domain)

        return domain.startswith(my_domain)


class ComponentImportTask(OperateRecordModel):
    class Status(object):
        CREATED = "CREATED"
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
        EXCEPTION = "EXCEPTION"

    STATUS_CHOICES = (
        (Status.CREATED, _("任务创建成功")),
        (Status.RUNNING, _("任务正在执行")),
        (Status.SUCCESS, _("任务执行成功")),
        (Status.EXCEPTION, _("任务执行过程异常")),
    )

    class Process(object):
        READY = "READY"
        UNZIP_FILE = "UNZIP_FILE"
        CHECK_COMPONENT_NAME = "CHECK_COMPONENT_NAME"
        CHECK_INDEX_FILE = "CHECK_INDEX_FILE"
        CHECK_CONFIG_FILE = "CHECK_CONFIG_FILE"
        CHECK_COMPONENT_DESC = "CHECK_COMPONENT_DESC"
        PROCESS_LOGO = "PROCESS_LOGO"
        CHECK_EXPORTER_FILE = "CHECK_EXPORTER_FILE"
        SAVE_COMPONENT = "SAVE_COMPONENT"
        FINISHED = "FINISHED"

    PROCESS_CHOICES = (
        (Process.READY, _("任务就绪")),
        (Process.UNZIP_FILE, _("解压文件")),
        (Process.CHECK_COMPONENT_NAME, _("校验组件名称")),
        (Process.CHECK_COMPONENT_DESC, _("校验组件描述")),
        (Process.CHECK_INDEX_FILE, _("校验指标项文件")),
        (Process.CHECK_CONFIG_FILE, _("校验配置项文件")),
        (Process.PROCESS_LOGO, _("读取并压缩LOGO")),
        (Process.CHECK_EXPORTER_FILE, _("校验二进制exporter")),
        (Process.SAVE_COMPONENT, _("保存组件配置")),
        (Process.FINISHED, _("任务流程完成")),
    )

    biz_id = models.IntegerField(_("业务ID"))

    process_data = JsonField(_("任务流程中间数据(json)"), null=True, blank=True)
    result_data = JsonField(_("任务执行结果(JSON)"), null=True, blank=True)
    ex_data = models.TextField(_("任务异常信息"), null=True, blank=True)

    status = models.CharField(_("任务状态"), choices=STATUS_CHOICES, max_length=50, default=Status.CREATED)
    process = models.CharField(_("任务当前流程"), choices=PROCESS_CHOICES, max_length=50, default=Process.READY)

    class Meta:
        verbose_name = _("组件导入任务")
        verbose_name_plural = _("组件导入任务")

    def update_process_data(self, data, save=True):
        if not self.process_data:
            self.process_data = {}
        self.process_data.update(data)
        if save:
            self.save()

    def update_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def update_process(self, process, save=True):
        self.process = process
        if save:
            self.save()


class LogCollector(CollectorConfig):
    """
    日志接入配置
    """

    TSDB_NAME = "slog"
    permission_exempt = True

    class Status(object):
        STARTING = "create"
        NORMAL = "normal"
        STOPPING = "stop"
        STOPPED = "stopped"

    STATUS_CHOICES = (
        (Status.STARTING, _("启用中")),
        (Status.STOPPING, _("停用中")),
        (Status.NORMAL, _("正常")),
        (Status.STOPPED, _("停用")),
    )

    biz_id = models.IntegerField(_("业务id"))
    data_id = models.CharField(_("数据源ID"), max_length=100, default="")
    result_table_id = models.CharField(_("结果表ID"), max_length=100, default="")
    data_set = models.CharField(_("数据源表名"), max_length=100)
    data_desc = models.CharField(_("数据源中文名"), max_length=100)
    data_encode = models.CharField(_("字符编码"), max_length=30)
    sep = models.CharField(_("数据分隔符"), max_length=30)
    log_path = models.TextField(_("日志路径"))
    fields = JsonField(_("字段配置"))
    ips = JsonField(_("采集对象ip列表"))
    conditions = JsonField(_("采集条件"))
    file_frequency = models.CharField(_("日志生成频率"), max_length=30)

    @property
    def status(self):
        """
        日志接入状态，根据IP决定
        """
        if not self.result_table_id or not self.data_id:
            return self.Status.STARTING

        host_status_list = [host.status for host in self.hosts.all()]

        if [s for s in host_status_list if s == LogCollectorHost.Status.NORMAL]:
            return self.Status.NORMAL
        if [s for s in host_status_list if s == LogCollectorHost.Status.STOPPED]:
            return self.Status.STOPPED
        if [s for s in host_status_list if s == LogCollectorHost.Status.STARTING]:
            return self.Status.STARTING
        if [s for s in host_status_list if s == LogCollectorHost.Status.STOPPING]:
            return self.Status.STOPPING
        return self.Status.NORMAL

    @property
    def has_exception(self):
        return self.hosts.filter(status=LogCollectorHost.Status.EXCEPTION).exists()

    @property
    def time_field_name(self):
        for field in self.fields:
            if field["time_format"]:
                return field["name"]
        raise CustomException(_("日志采集配置不合法：缺少时间字段"))

    class Meta:
        verbose_name = _("日志接入配置")
        verbose_name_plural = _("日志接入配置")

    def is_tsdb_storage(self):
        """
        该配置是否使用tsdb存储
        """
        return self.result_table_id.startswith("{}_{}".format(self.biz_id, STRUCTURED_LOG_DB))

    def get_title(self):
        return _("日志采集（%s）") % self.data_set

    def get_special_change_config(self, changed_configs, ori_data):
        ori_conditions = ori_data.get_condition_result()
        dst_conditions = self.get_condition_result()
        if ori_conditions != dst_conditions:
            changed_configs["conditions"] = {
                "key": "conditions",
                "title": _("采集条件"),
                "ori_value": ori_conditions,
                "dst_value": dst_conditions,
            }
        return changed_configs

    def get_condition_result(self):
        conditions = self.conditions
        conditions.sort()
        condition_list = []
        for i in conditions:
            tmp = _("当第{}列的值等于{}").format(i["index"], i["value"])
            condition_list.append(tmp)
        return ";".join(condition_list)

    @property
    def rt_name(self):
        return "{}_{}".format(STRUCTURED_LOG_DB, self.data_set)

    @property
    def rt_id(self):
        return "{}_{}_{}".format(self.biz_id, STRUCTURED_LOG_DB, self.data_set)

    def save_config(self, instances, action="append"):
        deposit_result = super(LogCollector, self).save_config(instances, action)
        for success in deposit_result["success"]:
            if action == "remove":
                for instance in [x for x in instances if x.ip == "{}|{}".format(success["ip"], success["bk_cloud_id"])]:
                    instance.delete()
            else:
                for instance in [x for x in instances if x.ip == "{}|{}".format(success["ip"], success["bk_cloud_id"])]:
                    instance.status = "normal"
                    instance.save()

        for failed_info in deposit_result["failed"]:
            for instance in [
                x for x in instances if x.ip == "{}|{}".format(failed_info["ip"], failed_info["bk_cloud_id"])
            ]:
                instance.status = "exception"
                instance.save()

        return deposit_result

    def delete(self, *args, **kwargs):
        try:
            # 尝试停用采集项，停用失败则忽略
            remove_config_result = self.save_config(self.hosts.all(), action="remove")
            logger.info(_("配置 [{}] 停用执行结果：{}").format(self.id, remove_config_result))
        except Exception as e:
            logger.warning(_("配置 [{}] 停用失败，原因：{}").format(self.id, e))
        # 删除采集项时，移除采集配置，对应的监控项也要删除
        self.hosts.all().delete()
        return super(CollectorConfig, self).delete(*args, **kwargs)

    def get_result_tables(self):
        result_table_field_list = []
        for field in self.fields:
            result_table_field_list.append(
                ResultTableField(
                    field_name=field["name"],
                    description=field["description"],
                    tag="dimension" if field["type"] in ["string", "text"] else "metric",
                    field_type=field["type"],
                )
            )

        result_table = ResultTable(table_name=self.data_set, description=self.data_desc, fields=result_table_field_list)

        return [result_table]

    def get_data_accessor(self, result_tables):
        return DataAccessor(
            bk_biz_id=self.biz_id,
            db_name=self.TSDB_NAME,
            tables=result_tables,
            etl_config="bk_standard",
            operator=self.update_user,
        )

    def access(self):
        data_id = super(LogCollector, self).access()
        self.data_id = data_id
        self.result_table_id = "{}_{}".format(self.TSDB_NAME, self.data_set)
        self.save()
        return data_id


class LogCollectorHost(OperateRecordModel):
    permission_exempt = True

    class Status(object):
        STARTING = "create"
        NORMAL = "normal"
        STOPPING = "stop"
        STOPPED = "stopped"
        EXCEPTION = "exception"

    STATUS_CHOICES = (
        (Status.STARTING, _("启用中")),
        (Status.NORMAL, _("正常")),
        (Status.STOPPING, _("停用中")),
        (Status.STOPPED, _("停用")),
        (Status.EXCEPTION, _("异常")),
    )
    log_collector = models.ForeignKey(LogCollector, verbose_name=_("所属采集器"), related_name="hosts")
    ip = models.CharField(_("采集对象IP"), max_length=20)
    plat_id = models.IntegerField(_("平台ID"), default=0)
    status = models.CharField(_("数据上报状态"), max_length=20, default=Status.STARTING, choices=STATUS_CHOICES)

    @property
    def host_dict_list(self):
        """
        将实例转化为主机列表
        """
        host = Host(self.ip)
        return [host.host_dict]

    def generate_single_config(self):
        # 生成当前实例的采集配置
        variables = []
        monitor_fields = {}
        for field in self.log_collector.fields:
            variables.append("$%s" % field["name"])
            field_type = field.get("type")
            if field_type in ["string", "text"]:
                monitor_fields[field["name"]] = {"monitor_type": "dimension", "conditions": []}
            else:
                monitor_fields[field["name"]] = {
                    "monitor_type": "metric",
                    "type": "int64" if field_type in ["int", "long"] else "float64",
                    "conditions": [],
                }

        regex_format = self.log_collector.sep.join(variables)

        for condition in self.log_collector.conditions:
            field_index = int(condition["index"]) - 1
            if field_index < len(self.log_collector.fields):
                field_name = self.log_collector.fields[field_index].get("name")
                monitor_fields[field_name]["conditions"].append({"method": "eq", "value": condition["value"]})

        return {
            "input_type": "log",
            "enabled": True,
            "task_id": self.log_collector.id,
            "dataid": safe_int(self.log_collector.data_id),
            "tail_files": True,
            "paths": [self.log_collector.log_path],
            "regex_format": regex_format,
            "monitor_fields": monitor_fields,
        }

    class Meta:
        unique_together = ["log_collector", "ip", "plat_id"]
        verbose_name = _("日志接入主机状态")
        verbose_name_plural = _("日志接入主机状态")


class UptimeCheckNode(OperateRecordModel):
    bk_biz_id = models.IntegerField(_("业务ID"), default=0)
    is_common = models.BooleanField(_("是否为通用节点"), default=False)
    name = models.CharField(_("节点名称"), max_length=50)

    ip = models.GenericIPAddressField(_("IP地址"))
    plat_id = models.IntegerField(_("云区域ID"))
    # 地点改为可选
    location = JsonField(_("地区"), default="{}")
    carrieroperator = models.CharField(_("外网运营商"), max_length=50, blank=True, null=True, default="")

    @property
    def full_table_name(self):
        return "{}_{}_{}".format(self.bk_biz_id, UPTIME_CHECK_DB, "heartbeat")

    @property
    def permission_exempt(self):
        return True

    def uninstall_agent(self):
        """
        卸载采集器
        取消采集器gse托管 -> 停止采集器进程 -> 删除配置文件和采集器
        """
        collector = UptimeCheckCollector(self.bk_biz_id)
        result = collector.uninstall([{"ip": self.ip, "plat_id": self.plat_id}])
        if len(result["failed"]):
            logger.error(result)
            err_msg = ""
            for err_obj in result["failed"]:
                err_msg += err_obj["ip"] + " - " + err_obj["errmsg"] + "\n"
            raise CustomException(_("安装采集器时部分IP失败: %s" % err_msg), data=result)

        return result

    def install_agent(self):
        """
        分发配置文件和采集器
        下发压缩包 -> Install(解压、install.sh、start.sh、check.sh) -> 注册GSE托管
        """
        # 下发配置文件和采集器
        result = resource.uptime_check.update_config({"node_id": self.pk})
        if len(result["failed"]):
            logger.error(result)
            err_msg = ""
            for err_obj in result["failed"]:
                err_msg += err_obj["ip"] + " - " + err_obj["errmsg"] + "\n"
            raise CustomException(_("下发配置文件时部分IP失败:%s" % err_msg), data=result)

        # INSTALL
        collector = UptimeCheckCollector(self.bk_biz_id)
        result = collector.upgrade_or_install_then_deposit([{"ip": self.ip, "plat_id": self.plat_id}])
        if len(result["failed"]):
            logger.error(result)
            err_msg = ""
            for err_obj in result["failed"]:
                err_msg += err_obj["ip"] + " - " + err_obj["errmsg"] + "\n"
            raise CustomException(_("安装采集器时部分IP失败：%s" % err_msg), data=result)

        return result

    def save(self, update=False, *args, **kwargs):
        """
        保存拨测节点
        :return:
        """
        # 数据验证
        self.validate_data(update)

        super(UptimeCheckNode, self).save(*args, **kwargs)

    def delete(self, force=False, *args, **kwargs):
        """
        删除拨测节点
        """
        if not force:
            # 删除前需要先确保该节点上没有正在执行的拨测任务
            tasks = self.tasks.all()
            task_name = ";".join([task.name for task in tasks if (task.status == task.Status.RUNNING)])
            if len(self.tasks.all()) != 0:
                raise CustomException(_("该节点存在以下运行中的拨测任务：%s，" + _("请先暂停或删除相关联的任务")) % task_name)

        self.uninstall_agent()

        super(UptimeCheckNode, self).delete(*args, **kwargs)

    def validate_data(self, update):
        """
        用于在保存之前对拨测节点进行输入验证
        """
        # 创建操作
        if not update:
            # ip不能重复
            if UptimeCheckNode.objects.filter(ip=self.ip, bk_biz_id=self.bk_biz_id).exists():
                raise CustomException(_("保存拨测节点失败，主机%(ip)s已存在：name=%(name)s") % {"ip": self.ip, "name": self.name})
            # 名称不能重复
            if UptimeCheckNode.objects.filter(name=self.name, bk_biz_id=self.bk_biz_id).exists():
                raise CustomException(_("保存拨测节点失败，节点名称%(name)s已存在") % {"name": self.name})
        # 更新操作
        else:
            # 先获取到已有的数据，再比较具体变更
            try:
                old_uptimecheck_node = UptimeCheckNode.objects.get(pk=self.pk)
            except UptimeCheckNode.DoesNotExist:
                raise CustomException(_("保存拨测节点失败，不存在id为%(id)s的节点") % {"id": self.pk})
            # ip变更，则新的ip不能和其他的相同
            if (
                old_uptimecheck_node.ip != self.ip
                and UptimeCheckNode.objects.filter(ip=self.ip, bk_biz_id=self.bk_biz_id).exists()
            ):
                raise CustomException(_("保存拨测节点失败，主机%(ip)s已存在：name=%(name)s") % {"ip": self.ip, "name": self.name})
            # 名称变更，则不能和其他的相同
            if (
                old_uptimecheck_node.name != self.name
                and UptimeCheckNode.objects.filter(name=self.name, bk_biz_id=self.bk_biz_id).exists()
            ):
                raise CustomException(_("保存拨测节点失败，节点名称'%(name)s'已存在") % {"name": self.name})

    class Meta:
        verbose_name = _("拨测节点")
        verbose_name_plural = _("拨测节点")

    def get_title(self):
        return _("拨测节点（%s）") % self.name


class UptimeCheckTaskSubscription(OperateRecordModel):
    uptimecheck_id = models.IntegerField(_("拨测任务id"), default=0)
    subscription_id = models.IntegerField(_("节点管理订阅ID"), default=0)
    bk_biz_id = models.IntegerField(_("业务ID"), default=0)

    class Meta:
        # 每个任务针对每个业务只能有一个item
        unique_together = (("uptimecheck_id", "bk_biz_id"),)


class UptimeCheckTask(OperateRecordModel):
    class Protocol(object):
        TCP = UptimeCheckProtocol.TCP
        UDP = UptimeCheckProtocol.UDP
        HTTP = UptimeCheckProtocol.HTTP
        ICMP = UptimeCheckProtocol.ICMP

    PROTOCOL_CHOICES = (
        (Protocol.TCP, "TCP"),
        (Protocol.UDP, "UDP"),
        (Protocol.HTTP, "HTTP(S)"),
        (Protocol.ICMP, "ICMP"),
    )

    class Status(object):
        NEW_DRAFT = "new_draft"
        RUNNING = "running"
        STOPED = "stoped"
        STARTING = "starting"
        STOPING = "stoping"
        START_FAILED = "start_failed"
        STOP_FAILED = "stop_failed"

    STATUS_CHOICES = (
        (Status.NEW_DRAFT, _("未保存")),
        (Status.RUNNING, _("运行中")),
        (Status.STOPED, _("未启用")),
        (Status.STARTING, _("启动中")),
        (Status.STOPING, _("停止中")),
        (Status.START_FAILED, _("启动失败")),
        (Status.STOP_FAILED, _("停止失败")),
    )
    permission_exempt = True

    bk_biz_id = models.IntegerField(_("业务ID"))
    name = models.CharField(_("任务名称"), max_length=50)
    protocol = models.CharField(_("协议"), choices=PROTOCOL_CHOICES, max_length=10)
    check_interval = models.PositiveIntegerField(_("拨测周期(分钟)"), default=5)
    # 地点变为可选项
    location = JsonField(_("地区"), default="{}")

    nodes = models.ManyToManyField(UptimeCheckNode, verbose_name=_("拨测节点"), related_name="tasks")
    status = models.CharField(_("当前状态"), max_length=20, choices=STATUS_CHOICES, default=Status.NEW_DRAFT)
    config = AESJsonField(_("拨测配置"), null=True, blank=True)

    @property
    def full_table_name(self):
        return "{}_{}_{}".format(self.bk_biz_id, UPTIME_CHECK_DB, self.protocol.lower())

    def delete(self, *args, **kwargs):
        """
        重写拨测任务删除方法
        1、删除前
            首先要清除该拨测任务所关联的监控源、告警策略
        2、删除后
            如果删除一个正在运行中的拨测任务
            需要在任务相关联的节点上重新生成下发最新配置，并执行重载操作
        """
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        if len(subscriptions) != 0:
            # 删除任务前先删除订阅
            self.switch_off_subscription()
            self.stop_subscription()
            self.delete_subscription()

        pk = self.pk
        super(UptimeCheckTask, self).delete(*args, **kwargs)

        # 在对应的分组中，将此任务剔除
        with transaction.atomic():
            for group in self.groups.all():
                group.tasks.remove(self.id)

        logger.info(_("拨测任务已删除,ID:%d") % pk)

    @property
    def temp_conf_name(self):
        """
        测试流程临时配置文件名
            filename = {bizid}_{pk}_uptimecheckbeat.yml
        """
        return "_".join([str(self.bk_biz_id), str(self.pk), "uptimecheckbeat.yml"])

    def update_subscription(self):
        """
        更新订阅
        更新自身绑定的订阅对象的配置项
        """
        params_list = self.generate_subscription_configs()
        create_params = []
        result_list = []
        # 更新任务信息
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        delete_map = {}
        for subscription in subscriptions:
            delete_map[subscription.bk_biz_id] = subscription.subscription_id

        # 更新任务信息
        for params in params_list:
            bk_biz_id = params["scope"]["bk_biz_id"]
            # 删除匹配到的biz_id，剩下的就是没有匹配成功的，这些订阅需要删除
            if bk_biz_id in delete_map.keys():
                del delete_map[bk_biz_id]
            subscription_item = subscriptions.filter(bk_biz_id=bk_biz_id)
            # 如果查到了，说明要更新节点管理的id
            if len(subscription_item) != 0:
                params["subscription_id"] = subscription_item[0].subscription_id
                params["run_immediately"] = True
                result = api.node_man.update_subscription(params)
                logger.info(_("订阅任务已更新，订阅ID:%d,任务ID:%d") % (result.get("subscription_id", 0), result.get("task_id", 0)))
                result_list.append(result)
            else:
                # 否则说明要新增订阅
                create_params.append(params)
        # 开始删除
        delete_subscription_id = []
        for biz_id in delete_map.keys():
            delete_subscription_id.append(delete_map[biz_id])
        if delete_subscription_id:
            self.send_delete_subscription(delete_subscription_id)

        create_result_list = []
        if create_params:
            create_result_list = self.send_create_subscription(create_params)

        return result_list, create_result_list, delete_map.keys()

    def delete_subscription(self):
        """
        删除订阅
        该操作执行前，需要先执行switch_off和stop_scrioption手动卸载正在运行的拨测任务，直接执行该操作会导致拨测配置文件遗留
        """
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        ids = [subscription.subscription_id for subscription in subscriptions]
        self.send_delete_subscription(ids)
        subscriptions.delete()

    def send_delete_subscription(self, subscription_ids):
        for subscription_id in subscription_ids:
            api.node_man.delete_subscription(subscription_id=subscription_id)
            logger.info(_("订阅任务已删除，ID:%d") % subscription_id)

    def switch_off_subscription(self):
        """
        关闭订阅
        关闭对自身绑定的订阅的监听，该操作不会立刻执行插件删除操作，若要立刻执行，需要调用stop_subscription
        """
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        for subscription in subscriptions:
            api.node_man.switch_subscription(subscription_id=subscription.subscription_id, action="disable")
            logger.info(_("订阅任务已关闭，ID:%d") % subscription.subscription_id)

    def switch_on_subscription(self):
        """
        开启订阅
        启动对自身绑定的订阅的监听,该操作不会立刻执行插件部署操作，若要立刻执行，需要调用start_subscription
        """
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        for subscription in subscriptions:
            api.node_man.switch_subscription(subscription_id=subscription.subscription_id, action="enable")
            logger.info(_("订阅任务已启动，ID:%d") % subscription.subscription_id)

    def stop_subscription(self):
        """
        停止订阅
        立即执行自身绑定的订阅id的STOP命令
        """
        action_name = "bkmonitorbeat_%s" % self.protocol.lower()
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        for subscription in subscriptions:
            api.node_man.run_subscription(subscription_id=subscription.subscription_id, actions={action_name: "STOP"})
            logger.info(_("订阅任务执行STOP，ID:%d") % subscription.subscription_id)

    def start_subscription(self):
        """
        启动订阅
        立即执行自身绑定的订阅id的START命令
        """
        action_name = "bkmonitorbeat_%s" % self.protocol.lower()
        subscriptions = UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)
        for subscription in subscriptions:
            api.node_man.run_subscription(subscription_id=subscription.subscription_id, actions={action_name: "START"})
            logger.info(_("订阅任务执行START，ID:%d") % subscription.subscription_id)

    # 外层增加双引号，内层对有双引号的数据增加转义字符
    def add_escape(self, input_string):
        if input_string:
            temp = input_string.replace('"', '\\"')
            return '"%s"' % temp
        return input_string

    def generate_subscription_configs(self):
        """
        生成订阅参数
        读取当前对象的属性，并组装成节点管理的参数
        """
        pk = self.pk
        protocol = self.protocol.lower()
        dataid_map = {
            UptimeCheckProtocol.HTTP: settings.UPTIMECHECK_HTTP_DATAID,
            UptimeCheckProtocol.TCP: settings.UPTIMECHECK_TCP_DATAID,
            UptimeCheckProtocol.UDP: settings.UPTIMECHECK_UDP_DATAID,
            UptimeCheckProtocol.ICMP: settings.UPTIMECHECK_ICMP_DATAID,
        }

        biz_nodes = {}
        # 先遍历收集所有的节点信息，按业务id分组
        for node in self.nodes.values():
            if node["bk_biz_id"] in biz_nodes.keys():
                biz_nodes[node["bk_biz_id"]].append(node)
            else:
                biz_nodes[node["bk_biz_id"]] = [node]

        # 再按业务id生成订阅参数
        available_duration = int(self.config.get("timeout", self.config["period"] * 60000))
        if available_duration > settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT:
            timeout = available_duration + 5000
        else:
            timeout = settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT

        params_list = []
        for bk_biz_id in biz_nodes.keys():
            scope = {
                "bk_biz_id": bk_biz_id,
                "object_type": "HOST",
                "node_type": "INSTANCE",
                "nodes": [
                    {"ip": node["ip"], "bk_cloud_id": node["plat_id"], "bk_supplier_id": settings.BK_SUPPLIER_ID}
                    for node in biz_nodes[bk_biz_id]
                ],
            }
            step = {
                "id": "bkmonitorbeat_%s" % protocol,
                "type": "PLUGIN",
                "config": {
                    "plugin_name": "bkmonitorbeat",
                    "plugin_version": "latest",
                    "config_templates": [{"name": "bkmonitorbeat_%s.conf" % protocol, "version": "latest"}],
                },
                "params": {
                    "context": {
                        "data_id": dataid_map[protocol.upper()],
                        "max_timeout": str(settings.UPTIMECHECK_DEFAULT_MAX_TIMEOUT) + "ms",
                        "tasks": resource.uptime_check.generate_sub_config({"task_id": pk}),
                        "config_hosts": self.config.get("hosts", []),
                        # 针对动态节点的情况, 注意，业务ID必须拿当前task的业务ID：
                        "task_id": pk,
                        "bk_biz_id": self.bk_biz_id,
                        "period": "{}m".format(self.config["period"]),
                        "available_duration": "{}ms".format(available_duration),
                        "timeout": "{}ms".format(timeout),
                        "target_port": self.config.get("port"),
                        "response": self.add_escape(self.config.get("response", "")),
                        "request": self.add_escape(self.config.get("request", "")),
                        "response_format": self.config.get("response_format", "in"),
                        "size": self.config.get("size"),
                        "total_num": self.config.get("total_num"),
                        "max_rtt": "{}ms".format(self.config.get("max_rtt", 3000)),
                    }
                },
            }
            params = {
                "scope": scope,
                "steps": [step],
                "run_immediately": True,
            }
            params_list.append(params)

        return params_list

    def create_subscription(self):
        """
        建立订阅
        解析当前对象的属性生成参数列表，并向节点管理发起订阅请求
        """
        params_list = self.generate_subscription_configs()
        result_list = self.send_create_subscription(params_list)
        return result_list

    def send_create_subscription(self, params_list):
        """
        使用传入的参数列表，发送新增请求
        """
        result_list = []
        for params in params_list:
            result = api.node_man.create_subscription(params)
            logger.info(_("订阅任务已创建，ID:%d") % result.get("subscription_id", 0))
            result["bk_biz_id"] = params["scope"]["bk_biz_id"]
            result_list.append(result)
        return result_list

    def deploy(self, enable_strategy=False):
        """
        正式创建任务
        通过向节点管理发起订阅的方式执行任务
        如果当前拨测任务对象没有subscription_id，说明是新增任务流程
        如果已经有subscription_id，说明是更新任务流程
        """
        create_strategy = True if (self.status == self.Status.NEW_DRAFT) else False
        self.status = self.Status.STARTING
        self.save()
        UptimeCheckTaskCollectorLog.objects.filter(task_id=self.id).update(is_deleted=True)
        try:
            if len(UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk)) == 0:
                # 没有订阅id说明为新增任务，此时调用新增订阅接口
                create_result_list = self.create_subscription()
                # 生成新的订阅后，要将其入库存储
                for result in create_result_list:
                    # 遍历生成新的数据
                    UptimeCheckTaskSubscription.objects.create(
                        uptimecheck_id=self.pk, subscription_id=result["subscription_id"], bk_biz_id=result["bk_biz_id"]
                    )
                # 默认打开订阅
                self.switch_on_subscription()
                logger.info(_("新增拨测任务订阅完毕，任务id:%d,新增的订阅信息:%s") % (self.pk, str(create_result_list)))
            else:
                # 存在订阅id说明为旧任务，则需执行以下操作:
                # 1.停止订阅任务
                # 2.更新订阅配置
                # 3.启动订阅任务
                self.switch_off_subscription()
                # 由于订阅任务的特性，
                update_result, create_result_list, delete_list = self.update_subscription()
                # 生成新的订阅后，要将其入库存储
                for result in create_result_list:
                    # 遍历生成新的数据
                    UptimeCheckTaskSubscription.objects.create(
                        uptimecheck_id=self.pk, subscription_id=result["subscription_id"], bk_biz_id=result["bk_biz_id"]
                    )
                # 删除数据库中记录的订阅信息
                UptimeCheckTaskSubscription.objects.filter(uptimecheck_id=self.pk, bk_biz_id__in=delete_list).delete()
                self.switch_on_subscription()
                logger.info(
                    _("更新拨测任务订阅完毕，任务id:%d,更新的订阅信息:%s,新增的订阅信息:%s,删除的订阅信息:%s")
                    % (self.pk, str(update_result), str(create_result_list), str(delete_list))
                )
        except Exception as e:
            self.status = self.Status.START_FAILED
            self.save()
            logger.error(_("重启采集器时部分IP失败: %s") % e)
            raise CustomException(_("重启采集器时部分IP失败: %s") % e)
        self.save()
        update_task_running_status.delay(self.pk)
        # if create_strategy:
        #     resource.uptime_check.generate_default_strategy({'task_id': self.pk})

        if enable_strategy or create_strategy:
            resource.uptime_check.switch_strategy_by_task_id(
                {"bk_biz_id": self.bk_biz_id, "task_id": self.pk, "is_enabled": True}
            )

        # 将新拨测任务追加进缓存表中
        result_table_id_list = ["uptimecheck.{}".format(self.protocol.lower())]
        append_metric_list_cache.delay(result_table_id_list, task_id=self.pk)

        return "success"

    def start_task(self):
        """
        启动任务
        """
        self.status = self.Status.STARTING
        self.save()
        try:
            resource.uptime_check.switch_strategy_by_task_id(
                {"bk_biz_id": self.bk_biz_id, "task_id": self.pk, "is_enabled": True}
            )
            self.switch_on_subscription()
            self.start_subscription()
        except Exception as e:
            self.status = self.Status.START_FAILED
            self.save()
            raise CustomException(_("拨测任务启用失败：%s") % e.message)

        self.status = self.Status.RUNNING
        self.save()

        return "success"

    def stop_task(self):
        """
        停止任务
        """
        self.status = self.Status.STOPING
        self.save()
        try:
            resource.uptime_check.switch_strategy_by_task_id(
                {"bk_biz_id": self.bk_biz_id, "task_id": self.pk, "is_enabled": False}
            )
            self.switch_off_subscription()
            self.stop_subscription()
        except Exception as e:
            self.status = self.Status.STOP_FAILED
            self.save()
            raise CustomException(_("拨测任务停用失败：%s") % str(e))

        self.status = self.Status.STOPED
        self.save()

        return "success"

    def change_status(self, status):
        """
        更改任务运行状态
        :return:
        """
        if not status:
            raise CustomException(_("更改拨测任务状态：目标状态为空"))
        if status == self.status:
            return "success"
        elif status == self.Status.STOPED:
            return self.stop_task()
        elif status == self.Status.RUNNING:
            return self.start_task()
        else:
            raise CustomException(_("更改拨测任务状态：无效的目标状态：%s") % status)

    class Meta:
        verbose_name = _("拨测任务")
        verbose_name_plural = _("拨测任务")

    def get_title(self):
        return _("拨测任务（%s）") % self.name

    def gen_operate_desc(self, operate, ori_data=False):
        """
        根据操作类型，与变更前后的配置生成操作说明，对于 uptimechecktask 来说，status 的变更是由系统轮训而来，而不是用户产生，所以不展示
        :param operate: 操作类型：create/update/delete
        :param ori_data: 操作前的配置信息 [可选]
        :return: operate_desc 变更说明
        """
        op_desc = self.get_title()
        if operate in ["create", "delete"]:
            return op_desc
        elif operate == "update":
            if not ori_data:
                return op_desc
            # 获得2次修改之间， 变更了哪些配置
            changed_config = self.get_operate_changed_config(ori_data)
            # 判断changed_config是不是只是status的变更，如果'是'表示这些变更时系统产生的，前端界面不展示
            if len(changed_config) == 1 and ("status" in changed_config):
                return ""
            # 根据变更的配置， 生成对应的wording
            op_desc = self.gen_op_desc_by_changed_config(changed_config)
        return op_desc

    def get_operate_changed_config(self, ori_data):
        changed_configs = {}
        operate_record_fields = [f.name for f in OperateRecordModel._meta.fields]
        for f in self._meta.fields:
            if f.name not in operate_record_fields:
                dst_value = getattr(self, f.name)
                ori_value = getattr(ori_data, f.name)
                if dst_value != ori_value:
                    changed_configs[f.name] = {
                        "key": f.name,
                        "title": _(f.verbose_name.replace("(json)", "")),
                        "ori_value": ori_value,
                        "dst_value": dst_value,
                    }
        if hasattr(self, "get_special_change_config"):
            changed_configs = self.get_special_change_config(changed_configs, ori_data)
        return changed_configs

    def get_timeout(self):
        """
        获取期待响应时间
        """
        return self.config.get("timeout", 3000)

    def get_period(self):
        """
        获取采集周期
        """
        return self.config.get("period", 1)


class UptimeCheckTaskCollectorLog(models.Model):
    """
    下发拨测任务时，获取节点管理中相关节点执行日志
    """

    task_id = models.IntegerField(_("拨测任务ID"))
    error_log = JsonField(_("错误日志"), default="{}")
    is_deleted = models.BooleanField(_("已删除"), default=False)
    subscription_id = models.IntegerField(_("节点管理订阅ID"), default=0)
    nodeman_task_id = models.IntegerField(_("节点管理任务ID"), default=0)


class UptimeCheckGroup(OperateRecordModel):
    """
    拨测任务分组
    """

    name = models.CharField(_("分组名称"), max_length=50)
    tasks = models.ManyToManyField(UptimeCheckTask, verbose_name=_("拨测任务"), related_name="groups")
    logo = models.TextField(_("图片base64形式"), default="", blank=True)
    bk_biz_id = models.IntegerField(_("业务ID"), default=0)
    permission_exempt = True

    # 运行中任务
    # 如果停用分组中关联的某任务，那么被停用的任务既不在分组曲线中显示，也不会参与分组的可用率计算
    @property
    def running_tasks(self):
        return self.tasks.filter(status=UptimeCheckTask.Status.RUNNING)

    class Meta:
        verbose_name = _("拨测分组")
        verbose_name_plural = _("拨测分组")


def generate_upload_path(instance, filename):
    return os.path.join(instance.relative_path, instance.actual_filename)


class UploadedFile(OperateRecordModel):
    original_filename = models.CharField(_("原始文件名"), max_length=255)
    actual_filename = models.CharField(_("文件名"), max_length=255)
    relative_path = models.TextField(_("文件相对路径"))
    file_data = models.FileField(_("文件内容"), upload_to=generate_upload_path)

    @property
    def file_md5(self):
        return hashlib.md5(self.file_data.file.read()).hexdigest()

    @property
    def file_type(self):
        file_command = ["file", "-b", self.file_data.path]
        try:
            stdout, stderr = subprocess.Popen(file_command, stdout=subprocess.PIPE).communicate()
        except Exception as e:
            logger.exception(_("不存在的文件，获取文件类型失败：%s") % e)
            return ""
        return stdout
