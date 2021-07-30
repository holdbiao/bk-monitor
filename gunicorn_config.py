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
"""
所有api服务将解析在：monitor.bkmonitor.service.consul
dig +short monitor.bkmonitor.service.consul
"""


import hashlib
import os
import signal
import sys

# gunicorn 19.8.0之前的一个bug: 配置文件所在路径如果未在环境变量：PYTHONPATH中，则配置文件无法引入同目录下第三方模块
# detail: https://github.com/benoitc/gunicorn/issues/1349
# 当前gunicorn指定版本19.6.0，在未升级情况下，单独修复

try:
    from bkmonitor.utils.consul import BKConsul, consul
except ImportError:
    sys.path.insert(0, os.getcwd())
    from bkmonitor.utils.consul import BKConsul, consul


try:
    _config = __import__("conf.api.production.gunicorn_config", globals(), locals(), ["*"])
    for _setting in dir(_config):
        locals()[_setting] = getattr(_config, _setting)

except ImportError:
    from conf.api.development.gunicorn_config import *  # noqa

node_name_prefix = "bkmonitor-api"


def get_bind_info(server):
    bind_info = server.cfg.settings["bind"].get()[0]
    _ip, _port = bind_info.split(":")
    _port = int(_port)
    return _ip, _port


def get_node_id(server):
    return hashlib.md5(server.cfg.settings["bind"].get()[0].encode("utf-8")).hexdigest()


def when_ready(server):
    _ip, _port = get_bind_info(server)
    node_name = "{}-{}".format(node_name_prefix, get_node_id(server))

    if server.cfg.settings["worker_class"].get() == "gevent":
        from gevent import monkey

        monkey.patch_all()

    check = consul.Check.tcp(_ip, _port, "10s")
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    client = BKConsul()

    # 注册服务
    client.agent.service.register("bkmonitorv3", node_name, address=_ip, port=_port, check=check, tags=["monitor"])
    signal.signal(signal.SIGCHLD, server.handle_chld)

    server.log.info("Server register node: {}".format(node_name))


def on_exit(server):
    client = BKConsul()
    node_name = "{}-{}".format(node_name_prefix, get_node_id(server))
    client.agent.service.deregister(node_name)
    server.log.info("Server deregister node: {}".format(node_name))
