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
import argparse
import logging
import sys
import time
import xmlrpc.client

from watchdog.tnm2 import TNM2Client

logging.basicConfig(format="%(levelname)8s [%(asctime)s] %(message)s", level=logging.INFO)


class WatchDog(object):
    def __init__(self, delays, retries, recover, proxy=None, tnm2_client=None):
        self.delays = delays
        self.recover = recover
        self._max_loops = delays * retries

        self.proxy = proxy
        self.tnm2_client = tnm2_client

        self._registry = {}

    def watch(self):
        if self.proxy is None:
            logging.warning("watchdog cannot working: 'proxy' is None.")
        else:
            logging.info("watching...")

        running_count = 0
        for process in self.proxy.supervisor.getAllProcessInfo():
            identifier = ":".join((process["group"], process["name"]))

            if process["statename"] in ("FATAL", "EXITED"):
                if identifier in self._registry and self._registry[identifier] == 0:
                    logging.info("recovered monitoring for process %r.", identifier)

                self._registry.setdefault(identifier, 0)
            else:
                if process["statename"] == "RUNNING":
                    running_count += 1

                if identifier in self._registry:
                    del self._registry[identifier]

                    logging.info("process %r is %r.", identifier, process["statename"])

        self.report_num(running_count)

        for identifier in self._registry:
            self._registry[identifier] += 1
            message = None

            if self._registry[identifier] > 0:
                logging.info("process %r 'FATAL' or 'EXITED'.", identifier)

            if self._registry[identifier] > self._max_loops:
                self._registry[identifier] = -self.recover

                message = "giving up process %r, " "reached max retries limit!" % identifier
                logging.error(message)

            if self._registry[identifier] > 0 and self._registry[identifier] % self.delays == 0:
                restart_succeeded = self.restart(identifier)

                message = "watchdog restart process %r " % identifier
                if restart_succeeded:
                    message += "succeeded."
                else:
                    message += "failed."

                logging.info(message)

            if message:
                self.send_message(message)

    def restart(self, identifier):
        try:
            self.proxy.supervisor.stopProcess(identifier)
            is_succeeded = self.proxy.supervisor.startProcess(identifier)
        except Exception:
            is_succeeded = False

        return is_succeeded

    def report_num(self, num):
        if self.tnm2_client is None:
            logging.warning("report_num failed: 'tnm2_client' is None.")
        else:
            self.tnm2_client.report_num(num)

    def send_message(self, message):
        if self.tnm2_client is None:
            logging.warning("send_message failed: 'tnm2_client' is None.")
        else:
            self.tnm2_client.send_message(message)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="watchdog", description="### WatchDog ###")
    parser.add_argument("url", metavar="XML-RPC_URL", help="Supervisor XML-RPC API url.")
    parser.add_argument(
        "-i",
        "--interval",
        metavar="SECONDS",
        dest="interval",
        type=int,
        default=60,
        help="How often the check & handling loop takes " "action (in seconds, default 60).",
    )
    parser.add_argument(
        "-r",
        "--retries",
        metavar="TIMES",
        dest="retries",
        type=int,
        default=3,
        help="How many times that watchdog will allow when "
        "attempting to restart the program before giving "
        "up (default 3).",
    )
    parser.add_argument(
        "-d",
        "--delays",
        metavar="LOOPS",
        dest="delays",
        type=int,
        default=5,
        help="How many loops that watchdog will wait before " "taking the restart action (default 5).",
    )
    parser.add_argument(
        "-R",
        "--recover",
        metavar="LOOPS",
        dest="recover",
        type=int,
        default=1440,
        help="How many loops that watchdog would recover " "after gave up a process (default 60 * 24).",
    )
    parser.add_argument(
        "--num_alarm_id",
        metavar="NUM_ALARM_ID",
        dest="num_alarm_id",
        type=int,
        default=1230011,
        help="TNM2 num alarm attribute id (default 1230011).",
    )
    parser.add_argument(
        "--str_alarm_id",
        metavar="STR_ALARM_ID",
        dest="str_alarm_id",
        type=int,
        default=1147145,
        help="TNM2 str alarm attribute id (default 1147145).",
    )

    args = parser.parse_args()

    logging.info("WatchDog started with options:")
    logging.info("  -i, --interval: %r" % args.interval)
    logging.info("  -r, --retries : %r" % args.retries)
    logging.info("  -d, --delays  : %r" % args.delays)
    logging.info("  -R, --recover : %r" % args.recover)
    logging.info("  --num_alarm_id: %r" % args.num_alarm_id)
    logging.info("  --str_alarm_id: %r" % args.str_alarm_id)

    try:
        proxy = xmlrpc.client.ServerProxy(args.url)
        tnm2_client = TNM2Client(args.num_alarm_id, args.str_alarm_id)
        watchdog = WatchDog(args.delays, args.retries, args.recover, proxy=proxy, tnm2_client=tnm2_client)

        while True:
            time.sleep(args.interval)
            watchdog.watch()
    except KeyboardInterrupt:
        logging.info("(KeyboardInterrupt) received.")
    except Exception:
        import traceback

        sys.stderr.write(traceback.format_exc())

    logging.info("WatchDog stopped.")
