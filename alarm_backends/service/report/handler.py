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
import os
import logging
import datetime
import asyncio
import base64
from collections import defaultdict
from pyppeteer.launcher import Launcher

from django.conf import settings

from bkmonitor.utils.common_utils import replce_special_val
from bkmonitor.iam import Permission, ActionEnum
from bkmonitor.commons.tools import Sender
from bkmonitor.models import ReportItems, ReportContents
from bkmonitor.utils.grafana import fetch_panel_title_ids
from constants.report import StaffChoice, LOGO
from core.drf_resource import api
from core.drf_resource.exceptions import CustomException
from alarm_backends.service.report.tasks import render_mails
from alarm_backends.core.cache.mail_report import MailReportCacheManager
from constants.report import return_replace_val_dict, BuildInBizType

logger = logging.getLogger("bkmonitor.cron_report")

try:
    from conf.api.production.gunicorn_config import bind
except Exception as e:
    logger.exception(f"[mail_report] import bind failed: {e}")
    bind = "monitor.bkmonitorv3.service.consul:10204"


CHROME_OPTIONS = {
    "args": [
        "--disable-dev-shm-usage",  # 禁止使用/dev/shm, 防止内存不够用
        "--disable-infobars",
        "--disable-extensions",
        "--disable-gpu",
    ]
}


def get_or_create_eventloop():
    """
    获取或创建事件循环
    :return: 事件循环
    """
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex) or "Event loop is closed" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()


def chunk_list(list_need_to_chunk: list, per_list_max_length: int):
    """
    对数组进行指定长度的分页
    :param list_need_to_chunk: 带分页数组
    :param per_list_max_length: 指定每组长度
    :return: 分页后的数组
    """
    groups = [[]]
    j_index = 0
    for index, value in enumerate(list_need_to_chunk):
        if index != 0 and index % per_list_max_length == 0:
            groups.append([])
            j_index += 1
        groups[j_index].append(value)
    return groups


def generate_url(bk_biz_id, dashboard_uid, panel_id, var_bk_biz_ids, begin_time="", end_time=""):
    """
    生成图片url
    :param bk_biz_id: 业务ID
    :param dashboard_uid: 仪表盘ID
    :param panel_id: Panel ID
    :param begin_time: 起始时间
    :param end_time: 终止时间
    :return: 图表url
    """
    url = (
        f"http://{bind}/grafana/d-solo/{dashboard_uid}/"
        f"?orgName={bk_biz_id}&from={begin_time}&to={end_time}{var_bk_biz_ids}&panelId={panel_id}"
    )
    return url


def fetch_chrome_path():
    """
    获取chrome路径
    :return: chrome路径
    """
    chrome_path = os.popen("command -v google-chrome").readlines()
    if len(chrome_path) > 0:
        chrome_path = chrome_path[0].strip()
    else:
        raise CustomException("[mail_report] Without Chrome, Could not start mail report.")
    return chrome_path


async def fetch_images_by_puppeteer(element, browser):
    """
    使用puppeteer进行截图
    """
    err_msg = []
    try:
        # 启动标签页
        page = await browser.newPage()
        await page.goto(element["url"], {"waitUntil": "networkidle0", "timeout": 30000})
        await page.setViewport(element["image_size"])

        # 等待渲染完成
        await page.waitForSelector("div.panel-content", {"timeout": 30000})

        # 访问指定元素
        target = await page.querySelector(element["classname"])
        # 等待页面变化完毕
        await asyncio.sleep(0.1)
        # 截图
        img = await target.screenshot()
        element["base64"] = base64.b64encode(img).decode("utf-8")
        # 关闭页面
        await page.close()
    except Exception as e:
        err_msg.append({"tag": element["tag"], "exception_msg": e})
        logger.exception(f"[mail_report] error url: {element['url']} fetch_images_by_puppeteer: {e}")

    return element, err_msg


async def start_tasks(chrome_path, elements):
    """
    启动浏览器并执行截图任务
    :param chrome_path: 浏览器路径
    :param elements: panel信息
    :return: [(element, err_msg)]
    """
    launcher = None
    browser = None
    try_times = 0
    while not browser and try_times <= 5:
        try:
            # 处理由于 urllib 报错导致启动失败的问题
            # browser = await launch(headless=True, executablePath=chrome_path, options=CHROME_OPTIONS,)
            launcher = Launcher(headless=True, executablePath=chrome_path, options=CHROME_OPTIONS)
            browser = await launcher.launch()
        except Exception as e:
            if launcher:
                launcher.proc.kill()
            logger.exception(f"[mail_report] chrome start fail, will try again, Number: {try_times}, error: {e}")
            try_times += 1

    # 多线程形式
    # tasks = [fetch_images_by_puppeteer(element, file_dir, browser) for element in elements]
    # result = await asyncio.gather(*tasks)
    result = []
    for element in elements:
        result.append(await fetch_images_by_puppeteer(element, browser))
    try:
        await browser.close()
    except Exception as e:
        logger.exception(f"[mail_report] close browser failed, will try again, msg: {e}")
        await browser.close()

    return result


def screenshot_by_uid_panel_id(graph_info):
    """
    根据所需图表信息进行截图
    :param graph_exporter: 浏览器
    :param graph_info: 图表信息
    [{
        "bk_biz_id": 2,
        "uid": uid,
        "panel_id": panel_id,
        "image_size":{
            "width": width,
            "height": height
        },
        "var_bk_biz_ids": "2,3,4"
        "from_time": 1612766359450,
        "to_time": 1612766359450,
        "is_superuser": False
    }]
    :return: {bk_biz_id-uid-panel_id: {base64: base64, url: url}}
    """

    elements = []
    for graph in graph_info:
        # 加载页面
        url = generate_url(
            bk_biz_id=graph["bk_biz_id"],
            dashboard_uid=graph["uid"],
            panel_id=graph["panel_id"],
            var_bk_biz_ids=graph["var_bk_biz_ids"],
            begin_time=graph.get("from_time", ""),
            end_time=graph.get("to_time", ""),
        )
        element = {"url": url, "classname": "div.panel-content", "tag": graph["tag"], "image_size": graph["image_size"]}
        elements.append(element)

    chrome_path = fetch_chrome_path()

    # 异步启动任务, 生成结果
    logger.info("[mail_report] start asyncio tasks.")
    loop = get_or_create_eventloop()
    result = loop.run_until_complete(start_tasks(chrome_path, elements))

    graph_filename_maps = {
        graph["tag"]: {"base64": graph["base64"], "url": graph["url"]}
        for graph in [item[0] for item in result]
        if graph.get("base64")
    }

    # 处理错误信息
    error_messages = {}
    for item in result:
        tag = item[0]["tag"]
        if item[1]:
            error_messages[tag] = item[1]

    # 返回图表信息和错误信息
    return graph_filename_maps, error_messages


class ReportHandler:
    """
    报表处理器
    """

    def __init__(self, item_id=None):
        self.image_size_mapper = {
            1: {"width": 800, "height": 270, "deviceScaleFactor": 2},
            2: {"width": 620, "height": 300, "deviceScaleFactor": 2},
        }
        self.item_id = item_id

    def fetch_receivers(self, item_receivers=None):
        """
        获取所有需要接收邮件的人
        :return: 接收邮件的名单
        """
        receivers = []
        if not item_receivers:
            item_receivers = ReportItems.objects.get(pk=self.item_id).receivers
        groups_data = api.monitor.group_list()
        # 先解析组，再解析人，去掉is_enabled=False的人员
        # 只有开启了订阅的人才需要接收邮件
        for receiver in item_receivers:
            if receiver["is_enabled"] and receiver["type"] == StaffChoice.group and receiver.get("id") in groups_data:
                receivers.extend(groups_data[receiver["id"]])
        for receiver in item_receivers:
            if receiver["type"] == StaffChoice.user and receiver.get("id"):
                if receiver["is_enabled"]:
                    receivers.append(receiver["id"])
                elif receiver["id"] in receivers and not receiver["is_enabled"]:
                    # 如果 is_enabled=False 删除该接收者
                    receivers.remove(receiver["id"])
        receivers = list(set(receivers))
        if "admin" in receivers:
            receivers.remove("admin")
        if "system" in receivers:
            receivers.remove("system")
        return receivers

    def fetch_graphs_info(self, report_items_contents):
        """
        获取所有图表信息
        :param report_items_contents: 订阅报表内容字典
        :return: 所有图表信息:{
            "bk_biz_id": graph_info[0],
            "uid": graph_info[1],
            "panel_id": graph_info[2],
            "image_size": image_size_mapper.get(content["row_pictures_num"])
        }
        """
        contents = report_items_contents.get(self.item_id)
        total_graphs = []
        for content in contents:
            graphs = content["graphs"]
            for graph in graphs:
                graph_info = graph.split("-")
                if len(graph_info) < 3:
                    raise
                total_graphs.append(
                    {
                        "bk_biz_id": graph_info[0],
                        "uid": graph_info[1],
                        "panel_id": graph_info[2],
                        "image_size": self.image_size_mapper.get(content["row_pictures_num"]),
                    }
                )
        return total_graphs

    def fetch_images_time(self, frequency):
        """
        解析frequency成起始时间和结束时间
        :param frequency: 频率
        :return: 起始时间和结束时间
        """
        now_time = datetime.datetime.now()
        # 如果没有频率参数，默认取最近一天的数据
        if not frequency:
            from_time = now_time + datetime.timedelta(hours=-24)
            return int(from_time.timestamp() * 1000), int(now_time.timestamp() * 1000), from_time, now_time
        if frequency["type"] == 3:
            from_time = now_time + datetime.timedelta(hours=-24 * 7)
        elif frequency["type"] == 4:
            from_time = now_time + datetime.timedelta(hours=-24 * 30)
        else:
            from_time = now_time + datetime.timedelta(hours=-24)
        return int(from_time.timestamp() * 1000), int(now_time.timestamp() * 1000), from_time, now_time

    def parse_graph_info(self, graph_info, is_superuser, user_bizs, receivers):
        """
        解析业务列表
        :param graph_info: ["all-uid-panel_id"] / ["2,3,4-uid-penel_id"]
        :param is_superuser: 超管
        :param user_bizs: 用户有权限的业务列表
        :return: bk_biz_id, var_bk_biz_ids
        """

        def handle_superuser(user_bizs):
            """
            处理超管权限和有权限的业务
            :param user_bizs: 用户的业务列表
            :return: var_bk_biz_ids
            """
            if is_superuser:
                # 如果是超管，默认取全部业务
                var_bk_biz_ids = ["All"]
            else:
                # 否则只取用户对应业务权限的前20个
                var_bk_biz_ids = list(user_bizs)[:20]
                if not var_bk_biz_ids:
                    var_bk_biz_ids = ["none"]
            return var_bk_biz_ids

        var_bk_biz_ids = graph_info[0].split(",")
        setting_notify_group_data = MailReportCacheManager().fetch_groups_and_user_bizs()

        if len(var_bk_biz_ids) > 1:
            # 如果是多选业务的内置指标
            bk_biz_id = int(settings.MAIL_REPORT_BIZ)
        elif BuildInBizType.ALL in var_bk_biz_ids:
            # 内置指标-有权限的业务
            bk_biz_id = int(settings.MAIL_REPORT_BIZ)
            var_bk_biz_ids = handle_superuser(user_bizs)
        elif BuildInBizType.SETTINGS in var_bk_biz_ids:
            # 内置指标-配置管理员组
            bk_biz_id = int(settings.MAIL_REPORT_BIZ)
            var_bk_biz_ids = handle_superuser(
                setting_notify_group_data["controller_group"]["users_biz"].get(receivers[0], [])
            )
        elif BuildInBizType.NOTIFY in var_bk_biz_ids:
            # 内置指标-告警接收组
            bk_biz_id = int(settings.MAIL_REPORT_BIZ)
            var_bk_biz_ids = handle_superuser(
                setting_notify_group_data["alert_group"]["users_biz"].get(receivers[0], [])
            )
        else:
            # 普通情况，直接走原来的逻辑即可
            bk_biz_id = graph_info[0]
        return bk_biz_id, var_bk_biz_ids

    def render_images_to_html(self, mail_title, contents, user_bizs, receivers, frequency=None, is_superuser=False):
        """
        将图像渲染到HTML中
        :param mail_title: 邮件标题
        :param contents: 发送内容
        :param frequency: 发送频率
        :return: True/False
        """
        total_graphs = []
        from_time_stamp, to_time_stamp, from_time, to_time = self.fetch_images_time(frequency)
        for content in contents:
            graphs = content["graphs"]
            for graph in graphs:
                graph_info = graph.split("-")
                if len(graph_info) < 3:
                    raise
                bk_biz_id, var_bk_biz_ids = self.parse_graph_info(graph_info, is_superuser, user_bizs, receivers)

                total_graphs.append(
                    {
                        "bk_biz_id": bk_biz_id,
                        "uid": graph_info[1],
                        "panel_id": graph_info[2],
                        "image_size": self.image_size_mapper.get(content["row_pictures_num"]),
                        "var_bk_biz_ids": "".join([f"&var-bk_biz_id={i}" for i in var_bk_biz_ids]),
                        "tag": graph,
                        "from_time": from_time_stamp,
                        "to_time": to_time_stamp,
                    }
                )

        # 截图
        logger.info("[mail_report] prepare for screenshot...")
        images_files, err_msg = screenshot_by_uid_panel_id(total_graphs)

        # 获取所有图表映射
        panel_biz_uid = {f"{panel['bk_biz_id']}-{panel['uid']}" for panel in total_graphs}

        # 获取所有图表标题
        panel_titles = {}
        for item in panel_biz_uid:
            item_ = replce_special_val(item, return_replace_val_dict(settings.MAIL_REPORT_BIZ))
            for panel in fetch_panel_title_ids(int(item_.split("-")[0]), item_.split("-")[1]):
                panel_titles[f"{item_.split('-')[1]}-{panel['id']}"] = panel["title"]

        # 渲染邮件模板
        render_args = {}
        render_args["redirect_url"] = settings.MAIL_REPORT_URL.format(PAAS_URL=settings.PAAS_URL)
        render_args["mail_title"] = mail_title

        # 邮件范围
        render_args["from_time"] = from_time.strftime("%Y-%m-%d %H:%M:%S")
        render_args["to_time"] = to_time.strftime("%Y-%m-%d %H:%M:%S")

        # 邮件标题后补
        render_args["mail_title_time"] = f'({from_time.strftime("%Y-%m-%d")} ~ {to_time.strftime("%Y-%m-%d")})'

        render_args["contents"] = []
        render_args["attachments"] = [
            {
                "filename": "__INLINE__logo.png",
                "content_id": "<___INLINE__logo.png>",
                "disposition": "inline",
                "type": "png",
                "content": LOGO,
            }
        ]
        for content in contents:
            graphs = []
            for graph in content["graphs"]:
                graph_info = graph.split("-")
                var_bk_biz_ids = graph_info[0].split(",")
                if len(var_bk_biz_ids) > 1:
                    source = ",".join(var_bk_biz_ids)
                elif BuildInBizType.ALL in var_bk_biz_ids:
                    source = "有权限的业务"
                elif BuildInBizType.NOTIFY in var_bk_biz_ids:
                    source = "告警接收业务"
                elif BuildInBizType.SETTINGS in var_bk_biz_ids:
                    source = "配置管理业务"
                else:
                    source = graph_info[0]
                if images_files.get(graph):
                    render_args["attachments"].append(
                        {
                            "filename": f"__INLINE__{graph}.png",
                            "content_id": f"<__INLINE__{graph}.png>",
                            "disposition": "inline",
                            "type": "png",
                            "content": images_files[graph].get("base64"),
                        }
                    )
                image_url = images_files.get(graph, {}).get("url", "")

                graphs.append(
                    {
                        "graph_tag": graph,
                        "url": ""
                        if settings.REPORT_DASHBOARD_UID in image_url
                        else image_url.replace(f"http://{bind}", settings.MONITOR_SAAS_URL),
                        "cid_tag": f"{graph}.png",
                        "title": panel_titles.get(f"{graph_info[1]}-{graph_info[2]}"),
                        "source": source,
                        "content": images_files.get(graph, {}).get("base64"),
                    }
                )

            # 根据每行几幅图填充为 [[1],[2]] 或者 [[1,2], ...]等
            render_grphs = chunk_list(graphs, content["row_pictures_num"])

            render_args["contents"].append(
                {
                    "title": content["content_title"],
                    "content": content["content_details"],
                    "two_graph": True if content["row_pictures_num"] == 2 else False,
                    "graphs": render_grphs,
                }
            )
        return render_args, err_msg

    def send_mails(self, render_args, receivers):
        """
        发送邮件
        :param render_args: 渲染参数
        :param receivers: 接收者
        :return: success or raise failed
        """
        try:
            sender = Sender(
                title_template_path="report/report_title.jinja",
                content_template_path="report/report_content.jinja",
                context=render_args,
            )
            result = sender.send_mail(receivers)
            failed_list = []
            for receiver in result:
                if not result[receiver]["result"]:
                    failed_list.append(result[receiver])
            logger.info(f"[mail_report] send_mail success: {render_args['mail_title']}")
            return "success" if not failed_list else failed_list
        except Exception as e:
            raise CustomException(f"[mail_report] send_mail failed: {e}")

    def parse_users_group(self, all_user_different_graph, receivers, receivers_is_superuser):
        """
        发送分组逻辑
        :param all_user_different_graph: 内置图表类型
        :param receivers: 用户列表
        :param receivers_is_superuser: 用户是否超管 {user: True}
        :return: 分组结果 {"ALL-bk_biz_id1,bk_biz_id2-SETTINGS-bk_biz_id1": {user1, user2}}
        """
        send_groups = defaultdict(set)
        setting_notify_group_data = api.monitor.get_setting_and_notify_group()
        for receiver in receivers:
            tag_string = ""  # 用户各类业务串的唯一标志
            if not receiver or len(receiver) == 32 or "webhook(" in receiver:
                # 过滤空接收人、机器人及webhook
                continue
            user_is_superuser = receivers_is_superuser.get(receiver, False)
            if all_user_different_graph[BuildInBizType.ALL]:
                perm_client = Permission(receiver)
                perm_client.skip_check = False
                business_list = [
                    int(biz.bk_biz_id) for biz in perm_client.filter_business_list_by_action(ActionEnum.VIEW_BUSINESS)
                ]
                business_list.sort()
                biz_list = "superuser" if user_is_superuser else ",".join([str(biz) for biz in business_list])
                tag_string += f"{BuildInBizType.ALL}-{biz_list},"

            if all_user_different_graph[BuildInBizType.SETTINGS]:
                users_biz = [
                    int(biz)
                    for biz in list(setting_notify_group_data["controller_group"]["users_biz"].get(receiver, set()))
                ]
                users_biz.sort()
                biz_list = "superuser" if user_is_superuser else ",".join([str(biz) for biz in users_biz])
                tag_string += f"{BuildInBizType.SETTINGS}-{biz_list},"

            if all_user_different_graph[BuildInBizType.NOTIFY]:
                users_biz = [
                    int(biz) for biz in list(setting_notify_group_data["alert_group"]["users_biz"].get(receiver, set()))
                ]
                users_biz.sort()
                biz_list = "superuser" if user_is_superuser else ",".join([str(biz) for biz in users_biz])
                tag_string += f"{BuildInBizType.NOTIFY}-{biz_list}"

            send_groups[tag_string].add(receiver)
        return send_groups

    def process_and_render_mails(self):
        """
        渲染HTML并发送邮件入库
        """
        report_item = ReportItems.objects.get(pk=self.item_id)
        report_item_contents = list(ReportContents.objects.filter(report_item=self.item_id).values())

        # 如果选择图表时选了'有权限的业务'
        all_user_different_graph = {
            BuildInBizType.ALL: False,
            BuildInBizType.NOTIFY: False,
            BuildInBizType.SETTINGS: False,
        }
        for content in report_item_contents:
            for graph in content["graphs"]:
                if BuildInBizType.ALL in graph:
                    all_user_different_graph[BuildInBizType.ALL] = True
                elif BuildInBizType.NOTIFY in graph:
                    all_user_different_graph[BuildInBizType.NOTIFY] = True
                elif BuildInBizType.SETTINGS in graph:
                    all_user_different_graph[BuildInBizType.SETTINGS] = True

        receivers = self.fetch_receivers(report_item.receivers)

        logger.info(
            f"[mail_report] mail_title: {report_item.mail_title};"
            f"receivers: {receivers};"
            f"different_graph: {all_user_different_graph}"
        )

        receivers_is_superuser = api.monitor.is_superuser(username=receivers)

        if any(all_user_different_graph.values()):
            # 如果每个用户的图表都不一样
            # 获取用户的业务列表并分组渲染发送
            send_groups = self.parse_users_group(all_user_different_graph, receivers, receivers_is_superuser)
            logger.info(f"[mail_report] groups count: {len(send_groups)}")
            # 分组渲染发送
            for biz in send_groups:
                render_mails.apply_async(
                    args=(
                        self,
                        report_item,
                        report_item_contents,
                        list(send_groups[biz]),
                        receivers_is_superuser.get(list(send_groups[biz])[0], False),
                    )
                )
        else:
            # 如果每个用户的图表都一样，一次性解决
            render_mails.apply_async(
                args=(
                    self,
                    report_item,
                    report_item_contents,
                    receivers,
                    receivers_is_superuser.get(report_item.create_user, False),
                )
            )
