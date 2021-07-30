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


from optparse import OptionError

from django.core.management.base import BaseCommand

from alarm_backends.management.base.base import ConsulDispatchCommand


class HashRing(ConsulDispatchCommand):
    def on_start(self, *args):
        pass

    def __init__(self, command):
        self.__COMMAND_NAME__ = command
        super(HashRing, self).__init__()


class Command(BaseCommand):
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("--host")
        parser.add_argument("--biz_id", type=int)

    def handle(self, name="run_access", *args, **options):
        if not name:
            raise OptionError("name is required.", "name")

        command = HashRing(name)

        biz_id = options.get("biz_id")
        host = options.get("host")
        if host == "localhost":
            host = command.host_addr

        _, host_targets = command.dispatch_all_hosts(command.query_for_hosts())

        for target_host, targets in list(host_targets.items()):
            if host and target_host != host:
                continue
            target_list = [i for i in targets if not biz_id or i == biz_id]
            if target_list:
                print("host: %s" % target_host)
                for target in target_list:
                    print("- %s" % target)
