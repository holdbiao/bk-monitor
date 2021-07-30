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
import gitlab
import argparse

GITLAB_URL = os.environ.get("GITLAB_URL")
GIT_ACCESS_TOKEN = os.environ.get("GIT_ACCESS_TOKEN")
PROJECT_ID = os.environ.get("CI_PROJECT_ID")


def auto_merge(source_branch, target_branch, title):
    client = gitlab.Gitlab(GITLAB_URL, GIT_ACCESS_TOKEN)
    project = client.projects.get(PROJECT_ID)
    merge_request = project.mergerequests.create(
        {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
        }
    )
    merge_request.merge(merge_commit_message="[ci skip] Auto Merged", should_remove_source_branch=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_branch", type=str)
    parser.add_argument("target_branch", type=str)
    parser.add_argument("title", type=str)
    kwargs = vars(parser.parse_args())
    auto_merge(**kwargs)
