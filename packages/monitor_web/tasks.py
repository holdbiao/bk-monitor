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


import logging
import shutil
import traceback

from celery.task import task
from django.utils import six
from django.conf import settings
from django.core.files.storage import default_storage
from pymysql.converters import escape_item, escape_string

from bkmonitor.dataflow.flow import DataFlow
from bkmonitor.strategy.new_strategy import QueryConfig
from bkmonitor.utils.common_utils import to_bk_data_rt_id
from constants.data_source import DataSourceLabel, DataTypeLabel
from constants.dataflow import ConsumingMode
from core.drf_resource import resource
from bkmonitor.utils.local import local
from bkmonitor.utils.user import set_local_username
from core.drf_resource import api
from core.errors.api import BKAPIError
from monitor_web.commons.cc.utils import CmdbUtil
from monitor_web.export_import.constant import ImportDetailStatus, ImportHistoryStatus
from monitor_web.models.custom_report import CustomEventGroup, CustomTSTable
from utils import business


logger = logging.getLogger("monitor_web")


def set_client_user():
    biz_set = business.get_all_activate_business()
    local.username = business.maintainer(biz_set[0])


@task(ignore_result=True)
def update_config_status():
    """
    周期性查询节点管理任务状态，更新执行中的采集配置的状态
    """
    resource.collecting.update_config_status()


@task(ignore_result=True)
def update_config_instance_count():
    """
    周期性查询节点管理任务状态，更新启用中的采集配置的主机数和异常数
    """
    resource.collecting.update_config_instance_count()


@task(ignore_result=True)
def update_metric_list():
    """
    定时刷新指标列表结果表
    :return:
    """
    from monitor_web.strategies.metric_list_cache import SOURCE_TYPE

    set_local_username(settings.COMMON_USERNAME)

    # 查询第三方应用是否部署，如果未部署，则不请求
    source_type_to_app_code = {
        "BKDATA": "bk_dataweb",
        "LOGTIMESERIES": "bk_log_search",
    }

    try:
        apps = api.bk_paas.get_app_info(target_app_code="bk_dataweb,bk_log_search")
        apps = [app["bk_app_code"] for app in apps]
    except BKAPIError:
        apps = list(source_type_to_app_code.values())

    # 使用业务缓存
    source_type_use_biz = ["BKDATA", "LOGTIMESERIES"]
    businesses = api.cmdb.get_business()

    for source_type, source in list(SOURCE_TYPE.items()):
        # 如果数据源对应的应用没有部署，则不请求
        if source_type in source_type_to_app_code and source_type_to_app_code[source_type] not in apps:
            continue

        try:
            logger.info("^update metric list(%s)" % source_type)
            if source_type in source_type_use_biz:
                for biz in businesses:
                    source(biz.bk_biz_id).run()
            else:
                source().run()

            logger.info("$update metric list(%s)" % source_type)
        except Exception as e:
            logger.exception("!update metric list({}): ({})".format(source_type, e))


@task(ignore_result=True)
def run_metric_manager_async(manager):
    """
    异步执行更新任务
    """
    manager._run()


@task(ignore_result=True)
def update_cmdb_util_info():
    """
    更新cc util的缓存数据
    :return:
    """
    CmdbUtil.refresh()


@task(ignore_result=True)
def append_metric_list_cache(result_table_id_list, task_id=None):
    """
    追加或更新新增的采集插件标列表
    """
    from monitor_web.strategies.metric_list_cache import BkmonitorMetricCacheManager
    from monitor_web.models.metric_list_cache import MetricListCache

    set_local_username(settings.COMMON_USERNAME)
    for result_table_id in result_table_id_list:
        result_table_msg = api.metadata.get_result_table(table_id=result_table_id)
        data_id_info = api.metadata.get_data_id(bk_data_id=result_table_msg["bk_data_id"])
        for k in ["source_label", "type_label"]:
            result_table_msg[k] = data_id_info[k]

        create_msg = BkmonitorMetricCacheManager().get_metrics_by_table(result_table_msg, task_id=task_id)
        for metric_msg in create_msg:
            MetricListCache.objects.update_or_create(
                metric_field=metric_msg["metric_field"],
                result_table_id=metric_msg["result_table_id"],
                related_id=metric_msg.get("related_id"),
                data_type_label=metric_msg.get("data_type_label"),
                data_source_label=metric_msg.get("data_source_label"),
                defaults=metric_msg,
            )


@task(ignore_result=True)
def update_failure_shield_content():
    """
    更新失效的屏蔽策略的内容信息
    """
    resource.shield.update_failure_shield_content()


@task(ignore_result=True)
def import_config(username, bk_biz_id, history_instance, collect_config_list, strategy_config_list):
    """
    批量导入采集配置、策略配置
    :param username:
    :param bk_biz_id:
    :param history_instance:
    :param collect_config_list:
    :param strategy_config_list:
    :return:
    """
    from monitor_web.models import ImportDetail
    from monitor_web.export_import.import_config import import_collect, import_strategy

    set_local_username(username)
    import_collect(bk_biz_id, history_instance, collect_config_list)
    import_strategy(bk_biz_id, history_instance, strategy_config_list)
    if (
        ImportDetail.objects.filter(history_id=history_instance.id, import_status=ImportDetailStatus.IMPORTING).count()
        == 0
    ):
        history_instance.status = ImportHistoryStatus.IMPORTED
        history_instance.save()


@task(ignore_result=True)
def remove_file(file_path):
    """
    定时删除指定文件夹
    :param file_path:
    :return:
    """
    shutil.rmtree(file_path)
    if settings.USE_CEPH:
        default_storage.delete(file_path.replace(settings.MEDIA_ROOT, ""))


@task(ignore_result=True)
def append_event_metric_list_cache(bk_event_group_id):
    """
    追加或更新新增的自定义事件入缓存表
    :param bk_event_group_id:
    :return:
    """
    from monitor_web.strategies.metric_list_cache import CustomEventCacheManager
    from monitor_web.strategies.metric_list_cache import BkMonitorLogCacheManager
    from monitor_web.models.metric_list_cache import MetricListCache

    set_local_username(settings.COMMON_USERNAME)
    event_group_id = int(bk_event_group_id)
    event_type = CustomEventGroup.objects.get(bk_event_group_id=event_group_id).type
    if event_type == "custom_event":
        result_table_msg = api.metadata.get_event_group.request.refresh(event_group_id=event_group_id)
        create_msg = CustomEventCacheManager().get_metrics_by_table(result_table_msg)
        for metric_msg in create_msg:
            MetricListCache.objects.update_or_create(
                metric_field=metric_msg["metric_field"],
                result_table_id=metric_msg["result_table_id"],
                related_id=metric_msg.get("related_id", ""),
                data_type_label=metric_msg.get("data_type_label"),
                data_source_label=metric_msg.get("data_source_label"),
                defaults=metric_msg,
            )
    else:
        BkMonitorLogCacheManager().run()


@task(ignore_result=True)
def update_task_running_status(task_id):
    """
    异步查询拨测任务启动状态，更新拨测任务列表中的运行状态
    """
    set_local_username(settings.COMMON_USERNAME)
    resource.uptime_check.update_task_running_status(task_id)


@task(ignore_result=True)
def append_custom_ts_metric_list_cache(time_series_group_id):
    from monitor_web.strategies.metric_list_cache import CustomMetricCacheManager
    from monitor_web.models.metric_list_cache import MetricListCache

    try:
        params = {
            "time_series_group_id": time_series_group_id,
        }
        result = api.metadata.get_time_series_group(params)
        result["custom_ts"] = CustomTSTable.objects.get(time_series_group_id=time_series_group_id)
        create_msg = CustomMetricCacheManager().get_metrics_by_table(result)
        for metric_msg in create_msg:
            MetricListCache.objects.update_or_create(
                metric_field=metric_msg["metric_field"],
                result_table_id=metric_msg["result_table_id"],
                related_id=metric_msg.get("related_id", ""),
                data_type_label=metric_msg.get("data_type_label"),
                data_source_label=metric_msg.get("data_source_label"),
                defaults=metric_msg,
            )
    except Exception as err:
        logger.error("[update_custom_ts_metric] failed, msg is {}".format(err))


@task(ignore_result=True)
def access_aiops_by_strategy_id(strategy_id):
    from bkmonitor.models import StrategyModel, ItemModel, AlgorithmModel, QueryConfigModel
    from bkmonitor.data_source.handler import DataQueryHandler
    from bkmonitor.dataflow.task.intelligent_detect import StrategyIntelligentModelDetectTask

    strategy = StrategyModel.objects.get(id=strategy_id, is_enabled=True)
    item = ItemModel.objects.filter(strategy_id=strategy_id).first()
    detect_algorithms = AlgorithmModel.objects.filter(strategy_id=strategy_id, item_id=item.id)
    # detect_algorithms 按产品设计，同一个策略下只能应用一个模型算法，所以这里应该只会有一个
    sensitivity_config = {}
    for d in detect_algorithms:
        sensitivity_value = d.config.get("sensitivity_value", 0) or 0
        sensitivity_config["sensitivity"] = float(sensitivity_value) / 100  # 这里需转成0 - 1 的数字

    rt_query_config = QueryConfig.from_models(
        QueryConfigModel.objects.filter(strategy_id=strategy_id, item_id=item.id)
    )[0]
    if rt_query_config.data_source_label == DataSourceLabel.BK_MONITOR_COLLECTOR:
        # 1. 接入
        try:
            api.metadata.access_bk_data_by_result_table(table_id=rt_query_config.result_table_id)
        except Exception:  # noqa
            logger.exception("access({}) to bkdata failed.".format(rt_query_config.result_table_id))
            return
        logger.info("access({}) to bkdata success.".format(rt_query_config.result_table_id))

        rt_scope = {"bk_biz_id": str(strategy.bk_biz_id)}
        bk_data_result_table_id = to_bk_data_rt_id(rt_query_config.result_table_id, settings.BK_DATA_RAW_TABLE_SUFFIX)
    elif rt_query_config.data_source_label == DataSourceLabel.BK_DATA:
        rt_scope = {}
        bk_data_result_table_id = rt_query_config.result_table_id
    else:
        raise Exception(
            "time series data of other platforms does not support intelligent anomaly detection algorithms, "
            "pending development"
        )

    # 3. 创建智能检测dataflow
    metric_field = rt_query_config.metric_field
    value_fields = ["`{}`".format(f) for f in rt_query_config.agg_dimension[:]]
    value_fields.append(
        "%(method)s(`%(field)s`) as `%(field)s`" % dict(field=metric_field, method=rt_query_config.agg_method)
    )

    sql, params = (
        DataQueryHandler(rt_query_config.data_source_label, rt_query_config.data_type_label)
        .table(bk_data_result_table_id)
        .filter(**rt_scope)
        .group_by(*rt_query_config.agg_dimension)
        .agg_condition(rt_query_config.agg_condition)
        .values(*value_fields)
        .query.sql_with_params()
    )

    def escape(obj):
        if isinstance(obj, six.string_types):
            return "'" + escape_string(obj) + "'"
        return escape_item(obj, "utf8", mapping=None)

    params = tuple(escape(arg) for arg in params)
    strategy_sql = sql % params

    model_release_id = -1
    model_id = settings.BK_DATA_INTELLIGENT_DETECT_MODEL_ID
    if not model_id:
        logger.error("the model id is empty, please configure it on the admin page.")
        return
    result = api.bkdata.get_model_release_info(
        model_id=model_id, project_id=settings.BK_DATA_PROJECT_ID, extra_filters="{}"
    )
    if not result:
        logger.error("get model release info from bk-data error, model_id:({})".format(model_id))
        return

    for m in result:
        if m.get("publish_status") == "latest":
            model_release_id = m.get("model_release_id")
    if model_release_id < 0:
        logger.error("can't find latest version of model, model_id:({}), result:({})".format(model_id, result))
        return

    try:
        old_intelligent_detect = getattr(rt_query_config, "intelligent_detect", {})
        detect_data_flow = StrategyIntelligentModelDetectTask(
            strategy_id=strategy.id,
            model_id=model_id,
            model_release_id=model_release_id,
            rt_id=bk_data_result_table_id,
            metric_field=rt_query_config.metric_field,
            agg_interval=rt_query_config.agg_interval,
            agg_dimensions=rt_query_config.agg_dimension,
            strategy_sql=strategy_sql,
            sensitivity_config=sensitivity_config,
            output_table_name=old_intelligent_detect.get("result_table_id", ""),
        )
        detect_data_flow.create_flow()
        detect_data_flow.start_flow(consuming_mode=ConsumingMode.Current)
        output_table_name = detect_data_flow.output_table_name
    except Exception:  # noqa
        logger.exception("create intelligent detect by strategy_id({}) failed".format(strategy.id))
        params = {
            "receiver__username": settings.BK_DATA_PROJECT_MAINTAINER,
            "title": f"{strategy_id}创建异常检测",
            "content": traceback.format_exc().replace("\n", "<br>"),
            "is_content_base64": True,
        }
        try:
            api.cmsi.send_mail(**params)
        except Exception:  # noqa
            logger.exception("send.mail({}) failed, content:({})".format(settings.BK_DATA_PROJECT_MAINTAINER, params))
        return

    # 将配置好的模型生成的rt_id放到extend_fields中，前端会根据这张表来查询数据
    rt_query_config.intelligent_detect = {
        "data_flow_id": detect_data_flow.data_flow.flow_id,
        "data_source_label": DataSourceLabel.BK_DATA,
        "data_type_label": DataTypeLabel.TIME_SERIES,
        "result_table_id": output_table_name,
        "metric_field": "value",
        "extend_fields": {"values": ["is_anomaly", "lower_bound", "upper_bound"]},
        "agg_condition": [],
        "agg_dimensions": rt_query_config.agg_dimension,
    }
    rt_query_config.save()


@task(ignore_result=True)
def update_aiops_dataflow_status():
    """
    aiops的状态维护
    增加：
        - 新建dataflow
    删除：
        - 延时删除dataflow
    修改：
        - 如果表未变更，只修改部分查询条件等，则直接更新dataflow
        - 如果表发生了切换，那么需要重建dataflow(停用已有的dataflow，新建一个)

    注意：
    这里没有发多个任务运行，是因为同时操作多个任务，计算平台会出错
    后续策略配置多了后，需要拆解这里的任务
    """
    if not settings.IS_ACCESS_BK_DATA:
        return

    from bkmonitor.models import StrategyModel, AlgorithmModel, QueryConfigModel
    from bkmonitor.dataflow.task.intelligent_detect import StrategyIntelligentModelDetectTask

    result = api.bkdata.get_data_flow_list(project_id=settings.BK_DATA_PROJECT_ID)
    if not result:
        logger.info("no dataflow exists in project({})".format(settings.BK_DATA_PROJECT_ID))

    # 找到当前计算平台已有的模型应用dataflow
    strategy_to_data_flow = {}
    for flow in result:
        # 去掉没在运行的dataflow
        flow_status = flow["status"]
        if flow_status != DataFlow.Status.Running:
            continue

        # 从名称判断是否为智能异常检测的dataflow
        flow_name = flow.get("flow_name", "")
        if StrategyIntelligentModelDetectTask.FLOW_NAME_KEY not in flow_name:
            continue

        groups = flow_name.split(StrategyIntelligentModelDetectTask.FLOW_NAME_KEY)
        groups = [i.strip() for i in groups if i.strip()]
        if len(groups) != 2:
            continue

        strategy_id, rt_id = groups
        if not strategy_id.isdigit():
            continue

        strategy_to_data_flow.setdefault(int(strategy_id), []).append({"rt_id": rt_id, "flow": flow})

    # 找到监控平台配置了智能异常检测的所有策略
    qs = AlgorithmModel.objects.filter(type=AlgorithmModel.AlgorithmChoices.IntelligentDetect).values_list(
        "strategy_id", flat=True
    )
    strategy_ids = list(qs)

    strategy_ids = list(StrategyModel.objects.filter(id__in=strategy_ids, is_enabled=True).values_list("id", flat=True))
    query_configs = QueryConfig.from_models(QueryConfigModel.objects.filter(strategy_id__in=strategy_ids))
    strategy_to_query_config = {query_config.strategy_id: query_config for query_config in query_configs}

    # 停用掉策略已停用或删除，但是计算平台仍然在运行的dataflow
    for strategy_id in set(strategy_to_data_flow.keys()) - set(strategy_to_query_config.keys()):
        flow_list = strategy_to_data_flow.get(strategy_id)
        for f in flow_list:
            flow_id, flow_status = f["flow"]["flow_id"], f["flow"]["status"]
            try:
                api.bkdata.stop_data_flow(flow_id=flow_id)
            except Exception:  # noqa
                logger.exception("stop dataflow({}) error".format(flow_id))

    # 创建新的dataflow
    for strategy_id in set(strategy_to_query_config.keys()) - set(strategy_to_data_flow.keys()):
        try:
            access_aiops_by_strategy_id(strategy_id=strategy_id)
        except Exception:  # noqa
            logger.exception("create strategy({}) dataflow status error".format(strategy_id))

    # 修改正在运行的dataflow，保持和监控平台的策略配置一致
    for strategy_id in set(strategy_to_query_config.keys()) & set(strategy_to_data_flow.keys()):
        try:
            rt_query_config = strategy_to_query_config.get(strategy_id)
            if rt_query_config.data_source_label == DataSourceLabel.BK_DATA:
                bk_data_result_table_id = rt_query_config.result_table_id
            else:
                bk_data_result_table_id = to_bk_data_rt_id(
                    rt_query_config.result_table_id, settings.BK_DATA_RAW_TABLE_SUFFIX
                )

            # 去掉多余的dataflow
            flow_list = strategy_to_data_flow.get(strategy_id)
            for f in flow_list:
                rt_id = f["rt_id"]
                flow_id = f["flow"]["flow_id"]
                if rt_id != bk_data_result_table_id:
                    try:
                        api.bkdata.stop_data_flow(flow_id=flow_id)
                    except Exception:  # noqa
                        logger.exception("stop dataflow({}) error".format(flow_id))

            access_aiops_by_strategy_id(strategy_id=strategy_id)
        except Exception:  # noqa
            logger.exception("update strategy({}) dataflow status error".format(strategy_id))
