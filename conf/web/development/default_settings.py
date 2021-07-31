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
conf.web.development.default_settings
====================================
"""


from conf.web.default_settings import *  # noqa

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "webpack"),
    os.path.join(PROJECT_ROOT, "static"),
)

TEMPLATES[0]["DIRS"] = (
    os.path.join(PROJECT_ROOT, "webpack"),
    os.path.join(PROJECT_ROOT, "static"),
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PROJECT_ROOT, "templates", "adapter", BKAPP_DEPLOY_PLATFORM),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 我们默认用mysql
        'NAME': 'saas_dev',                       # 数据库名 (默认与APP_CODE相同)
        'USER': 'root',                                    # 你的数据库user
        'PASSWORD': '',                                 # 你的数据库password
        'HOST': '127.0.0.1',                            # 开发的时候，使用localhost
        'PORT': '3306',               # 默认3306
        # 'CONN_MAX_AGE': 60,
    },
    'monitor_api': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'backend_dev',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        # 'CONN_MAX_AGE': 60,
    },
}


APP_TOKEN = SECRET_KEY = str(os.environ.get(
    "APP_TOKEN",
    'set by env')
)
BK_PAAS_HOST = os.environ.get('BK_PAAS_HOST', 'set by env')