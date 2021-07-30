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
import requests
import logging
import arrow
import datetime
import posixpath
from collections import defaultdict

from django.apps import apps
from django.conf import settings
from django.db.models import Q

from bkmonitor.iam import Permission, ActionEnum
from bkmonitor.utils.custom_report_tools import custom_report_tool
from bkmonitor.utils.range import TIME_MATCH_CLASS_MAP
from bkmonitor.utils.range.period import TimeMatchBySingle, TimeMatch
from bkmonitor.models import ReportItems, ReportContents, ReportStatus
from alarm_backends.service.scheduler.app import app

GlobalConfig = apps.get_model("bkmonitor.GlobalConfig")
logger = logging.getLogger("bkmonitor.cron_report")


def operation_data_custom_report():
    """
    运营数据自定义上报
    """
    all_data = []
    try:
        bk_data_id = int(GlobalConfig.objects.get(key="MAIL_REPORT_DATA_ID").value)
    except GlobalConfig.DoesNotExist:
        bk_data_id = settings.MAIL_REPORT_DATA_ID

    report_tool = custom_report_tool(bk_data_id)

    timestamp = arrow.now().timestamp * 1000
    # 获取运营数据
    url = f"{settings.MONITOR_SAAS_URL}/rest/v2/statistics/?response_format=json"
    statistics = requests.request("GET", url, verify=False).json()
    for stat in statistics:
        if not isinstance(stat, dict):
            continue
        for metric in stat.get("metrics", []):
            data = {
                # 指标，必需项
                "metrics": {f"{stat['namespace']}_{metric['metric_name']}": metric["metric_value"]},
                # 来源标识
                "target": settings.BK_PAAS_INNER_HOST,
                # 数据时间，精确到毫秒，非必需项
                "timestamp": timestamp,
            }

            # 补充维度
            if metric.get("dimensions"):
                data["dimension"] = metric["dimensions"]

            all_data.append(data)

    # 数据上报
    report_tool.send_data(all_data)
    logger.info(
        f"[operation_data_report] success, dataid:{bk_data_id}; source:{url}; "
        f"gsecmdline: {posixpath.join(settings.LINUX_GSE_AGENT_PATH, 'plugins', 'bin', 'gsecmdline')}; "
        f"ipc: {settings.LINUX_GSE_AGENT_IPC_PATH}"
    )


def report_mail_detect():
    """
    检测是否有邮件需要发送
    """
    from alarm_backends.service.report.handler import ReportHandler

    today = datetime.datetime.today().strftime("%Y-%m-%d")
    now_time = arrow.now()
    five_minute_ago = TimeMatch.convert_datetime_to_arrow(datetime.datetime.now() - datetime.timedelta(minutes=3))
    report_items = list(
        ReportItems.objects.filter(Q(is_enabled=True) & (Q(last_send_time=None) | Q(last_send_time__lt=today)))
    )

    # 汇总所有订阅的content信息
    report_items_contents = defaultdict(list)
    for report_content in list(ReportContents.objects.filter(id__in=[item.id for item in report_items]).values()):
        report_items_contents[report_content["report_item"]] += report_content

    # 处理订阅
    for item in report_items:
        shield_type = int(item.frequency.get("type", "-1"))
        time_match_class = TIME_MATCH_CLASS_MAP.get(shield_type, TimeMatchBySingle)
        # 补充begin_time和end_time
        item.frequency["begin_time"] = five_minute_ago.format("HH:mm:ss")
        item.frequency["end_time"] = now_time.format("HH:mm:ss")
        time_check = time_match_class(item.frequency, five_minute_ago, now_time)
        run_time = TimeMatch.convert_datetime_to_arrow(
            datetime.datetime.strptime(
                f'{datetime.datetime.today().strftime("%Y-%m-%d")} {item.frequency["run_time"]}', "%Y-%m-%d %H:%M:%S"
            )
        )
        if time_check.is_match(run_time):
            # 更新发送时间
            item.last_send_time = datetime.datetime.now()
            item.save()
            # 发送邮件
            logger.info("[mail_report] start process and render mails...")
            ReportHandler(item.id).process_and_render_mails()
            logger.info("[mail_report] end process and render mails...")


@app.task(ignore_result=True, queue="celery_report_cron")
def render_mails(mail_handler, report_item, report_item_contents, receivers, is_superuser):
    """
    渲染并发送邮件
    :param mail_handler: 报表处理器
    :param report_item: 订阅报表
    :param report_item_contents: 报表内容
    :param receivers: 接收者
    """
    status = {
        "report_item": mail_handler.item_id,
        "mail_title": report_item.mail_title,
        "create_time": datetime.datetime.now(),
        "details": {"receivers": receivers, "report_item_contents": report_item_contents, "error_message": {}},
        "is_success": True,
    }
    # 接收人
    receivers_string = ", ".join([str(receiver) for receiver in receivers])
    try:
        # 获取订阅者的业务列表
        perm_client = Permission(receivers[0])
        perm_client.skip_check = False
        business_list = perm_client.filter_business_list_by_action(ActionEnum.VIEW_BUSINESS)
        render_args, err_msg = mail_handler.render_images_to_html(
            report_item.mail_title,
            report_item_contents,
            [biz.bk_biz_id for biz in business_list],
            receivers,
            report_item.frequency,
            is_superuser,
        )
        status["mail_title"] = f'{report_item.mail_title} {render_args["mail_title_time"]}'
        if err_msg:
            status["details"]["error_message"][receivers_string] = err_msg
        result = mail_handler.send_mails(render_args, receivers)
        if isinstance(result, str):
            failed_list = []
        else:
            failed_list = [msg for msg in result if msg]

        if not failed_list:
            ReportStatus.objects.create(**status)
        else:
            # 将错误信息写入error_message
            status["details"]["error_message"][receivers_string] = failed_list
            status["is_success"] = False
            ReportStatus.objects.create(**status)
    except Exception as e:
        # 有用户发送失败了也得继续，不能影响其他用户的发送流程
        logger.exception("[mail_report] Send mail failed: %s" % e)
        status["details"]["error_message"][receivers_string] = str(e)
        status["is_success"] = False
        ReportStatus.objects.create(**status)
