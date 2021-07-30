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

from __future__ import absolute_import, print_function, unicode_literals

import re
import logging

from django.conf import settings
from bkmonitor.utils.common_utils import to_host_id, safe_int

from core.drf_resource import api

logger = logging.getLogger("metadata")


class ProcStatus(object):
    NOT_REGISTED = 0
    RUNNING = 1
    TERMINATED = 2


class AutoDeployProxy(object):
    """
    Auto Deploy Proxy(bkmonitorproxy), include first deploy, upgrade
    """

    PLUGIN_NAME = "bkmonitorproxy"
    PLUGIN_LATEST_VERSION = "latest"
    VERSION_PATTERN = re.compile(r"[vV]?(\d+\.){1,5}\d+$")

    @classmethod
    def deploy_proxy(cls, bk_cloud_id, all_hosts, host_id_dict):
        logger.info(
            "update proxy on bk_cloud_id({}), get hosts->[{}], host_id->[{}]".format(
                bk_cloud_id, all_hosts, host_id_dict
            )
        )
        params = {
            "namespace": "nodeman",
            "meta": {"namespace": "nodeman", "name": cls.PLUGIN_NAME, "labels": {"proc_name": cls.PLUGIN_NAME}},
            "hosts": all_hosts,
        }
        proc_result = api.gse.get_proc_status(params)
        proc_info_list = proc_result["proc_infos"]
        logger.info("get proc info->[%s]", str(proc_info_list))
        deploy_host_list = []
        for proc in proc_info_list:
            plugin_version = cls.VERSION_PATTERN.search(proc.get("version", ""))
            plugin_version = plugin_version.group() if plugin_version else ""
            if plugin_version == cls.PLUGIN_LATEST_VERSION:
                logger.info(
                    "{} has already latest version({}), do nothing.".format(
                        proc["host"]["ip"], cls.PLUGIN_LATEST_VERSION
                    )
                )
                # 已经是最新的版本，无需部署
                continue

            # plugin_status = proc.get("status", ProcStatus.NOT_REGISTED)
            # if plugin_status != ProcStatus.NOT_REGISTED:
            #     continue
            host_info = {"ip": proc["host"]["ip"], "bk_cloud_id": proc["host"]["bk_cloud_id"]}
            bk_host_id = host_id_dict[to_host_id(host_info)]
            deploy_host_list.append(bk_host_id)

        logger.info("get deploy host list->[%s]", deploy_host_list)
        if not deploy_host_list:
            logger.info(
                "all proxy of bk_cloud_id({}) is already deployed, proxy list({})".format(bk_cloud_id, all_hosts)
            )
            return

        params = dict(
            plugin_params={"name": cls.PLUGIN_NAME, "version": cls.PLUGIN_LATEST_VERSION},
            job_type="MAIN_INSTALL_PLUGIN",
            bk_host_id=deploy_host_list,
        )
        try:
            result = api.node_man.plugin_operate(**params)
            message = "update ({}) to version({}) success with result({}), Please see detail in bk_nodeman SaaS".format(
                cls.PLUGIN_NAME, cls.PLUGIN_LATEST_VERSION, result
            )
            logger.info(message)
        except Exception as e:  # noqa
            raise Exception("update ({}) error:{}, params:{}".format(cls.PLUGIN_NAME, e, params))

        logger.info("refresh bk_cloud_id->[%s] proxy success", bk_cloud_id)

    @classmethod
    def get_proxy_hosts_by_cloud(cls, bk_cloud_id):
        all_hosts = []
        host_id_dict = {}
        proxies = api.node_man.get_proxies(bk_cloud_id=bk_cloud_id)
        logger.info("bk_cloud_id->[%d] has %d proxies", bk_cloud_id, len(proxies))
        # 获取全体proxy主机列表
        for proxy in proxies:
            if proxy["status"] != "RUNNING":
                logger.warning("proxy({}) can not be use, because it's status not running".format(proxy["inner_ip"]))
                continue
            host = {"ip": proxy["inner_ip"], "bk_cloud_id": bk_cloud_id}
            all_hosts.append(host)
            host_id_dict[to_host_id(host)] = proxy["bk_host_id"]
        return all_hosts, host_id_dict

    @classmethod
    def deploy_with_cloud_id(cls, bk_cloud_id):
        all_hosts, host_id_dict = cls.get_proxy_hosts_by_cloud(bk_cloud_id)
        if len(all_hosts) == 0:
            logger.info("bk_cloud_id->[%s] has no proxy host, skip it", bk_cloud_id)
            return

        cls.deploy_proxy(bk_cloud_id, all_hosts, host_id_dict)

    @classmethod
    def deploy_direct_area_proxy(cls):
        bk_biz_id = api.cmdb.get_blueking_biz()
        try:
            target_hosts = [{"ip": proxy_ip, "bk_cloud_id": 0} for proxy_ip in settings.CUSTOM_REPORT_DEFAULT_PROXY_IP]
            hosts = api.cmdb.get_host_by_ip(ips=target_hosts, bk_biz_id=bk_biz_id)
            if not hosts:
                logger.warning(
                    "auto deploy direct area proxy failed, "
                    "can't get host from cmdb, please check you ip({}) is in blueking({})".format(
                        target_hosts, bk_biz_id
                    )
                )
                return
            host_id_dict = {
                to_host_id({"ip": h.bk_host_innerip, "bk_cloud_id": h.bk_cloud_id}): h.bk_host_id for h in hosts
            }
        except Exception:  # noqa
            logger.exception(
                "auto deploy direct area proxy failed, Get host({}) info from CMDB error".format(
                    settings.CUSTOM_REPORT_DEFAULT_PROXY_IP
                )
            )
            return

        cls.deploy_proxy(0, target_hosts, host_id_dict)

    @classmethod
    def find_latest_version(cls):
        default_version = "0.0.0"
        plugin_infos = api.node_man.plugin_info(name=cls.PLUGIN_NAME)
        version_str_list = [p.get("version", default_version) for p in plugin_infos]
        version_tuple_list = []
        for version in version_str_list:
            version_tuple = tuple(safe_int(v, v) if v else 0 for v in version.strip().split("."))
            version_tuple_list.append(version_tuple)

        max_version = max(version_tuple_list) if version_tuple_list else default_version
        return ".".join([str(i) for i in max_version])

    @classmethod
    def refresh(cls):
        cls.PLUGIN_LATEST_VERSION = cls.find_latest_version()
        logger.info(
            "find {} version {} from bk_nodeman, start auto deploy.".format(cls.PLUGIN_NAME, cls.PLUGIN_LATEST_VERSION)
        )

        # 云区域
        cloud_infos = api.cmdb.search_cloud_area()
        for cloud_info in cloud_infos:
            bk_cloud_id = cloud_info.get("bk_cloud_id", -1)
            if int(bk_cloud_id) == 0:
                continue

            try:
                cls.deploy_with_cloud_id(bk_cloud_id)
            except Exception as e:
                logger.exception(
                    "Auto deploy {} error, with bk_cloud_id({}), error({}).".format(cls.PLUGIN_NAME, bk_cloud_id, e)
                )

        # 直连区域
        try:
            cls.deploy_direct_area_proxy()
        except Exception as e:
            logger.exception("Auto deploy {} error, with direct area, error({}).".format(cls.PLUGIN_NAME, e))


def main():
    AutoDeployProxy.refresh()
