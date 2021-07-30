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
__all__ = ["SENTRY_SUPPORT", "SAAS_SENTRY_DSN"]

import os

# to use sentry
# change SENTRY_SUPPORT to True or
# Set the SENTRY_DSN environment variable
SENTRY_SUPPORT = False


try:
    import sentry_sdk  # noqa
    from sentry_sdk.integrations.django import DjangoIntegration  # noqa

    SENTRY_DSN = os.getenv("SENTRY_DSN") or os.getenv("BKAPP_SENTRY_DSN")
    SENTRY_SUPPORT = bool(SENTRY_DSN) or SENTRY_SUPPORT
except ImportError:
    SENTRY_DSN = ""


SAAS_SENTRY_DSN = SENTRY_DSN
