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
# !/usr/bin/env python

"""
python convert_yaml.py -s ../docs/api/monitor_v3.yaml -t ./ -f json
"""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import json
import os
import time

import yaml


class BasicException(Exception):
    """异常"""

    pass


def parse_fenlei(path):
    return path.split("/")[3]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert yaml to apigw file")
    parser.add_argument("-s", "--source", type=str, help="input yaml file", required=True)
    parser.add_argument("-t", "--target", type=str, help="output dir", required=True)
    parser.add_argument("-n", "--name", type=str, help="output file name", required=False)
    parser.add_argument(
        "-f", "--format", type=str, help="output file format", required=True, choices=["json", "yaml"], default="yaml"
    )
    args = parser.parse_args()

    source, target, format, name = args.source, args.target, args.format, args.name
    name = name or "apigw_default"

    print(
        """
        ===========================
        source:         {},
        target:         {},
        format:         {},
        name:         {},
        ===========================
    """.format(
            source, target, format, name
        )
    )

    with open(source, "rb") as f:
        apis = yaml.load(f)
        data = [
            {
                "resource_classification": parse_fenlei(api["dest_path"]),
                "headers": {},
                "resource_name": api["name"],
                "description": api["label"],
                "timeout": 30,
                "path": api["path"].replace("/v2/monitor_v3", ""),
                "registed_http_method": api.get("suggest_method") or api["dest_http_method"],
                "dest_http_method": api["dest_http_method"],
                "dest_url": "http://{stageVariables.domain}" + api["dest_path"],
            }
            for api in apis
        ]

        output = open(os.path.join(target, "{}.{}".format(name, format)), "w")
        if format == "json":
            json.dump(data, output, indent=2)
        else:
            yaml.dump(data, output)
