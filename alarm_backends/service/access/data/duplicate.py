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


from alarm_backends.core.cache import key


class Duplicate(object):
    def __init__(self, strategy_group_key, client=None):
        self.strategy_group_key = strategy_group_key
        self.record_ids_cache = {}

        self.client = client or key.ACCESS_DUPLICATE_KEY.client

    def get_record_ids(self, time):
        dup_key = key.ACCESS_DUPLICATE_KEY.get_key(strategy_group_key=self.strategy_group_key, dt_event_time=time)
        record_ids = self.record_ids_cache.get(dup_key)
        if not record_ids:
            # 这里是为了减少redis的查询次数，所以将结果缓存到当前实例中
            record_ids = self.client.smembers(dup_key)
            self.record_ids_cache[dup_key] = record_ids
        return record_ids

    def is_duplicate(self, record):
        """
        判断数据是否重复
        采用redis的集合功能。以分钟+维度作为key，值为record_id的集合
        """
        record_ids = self.get_record_ids(record.time)
        return str(record.record_id) in record_ids

    def add_record(self, record):
        record_ids = self.get_record_ids(record.time)
        record_ids.add(record.record_id)

    def refresh_cache(self):
        pipeline = self.client.pipeline(transaction=False)
        for dup_key, record_ids in list(self.record_ids_cache.items()):
            pipeline.sadd(dup_key, *record_ids)
            pipeline.expire(dup_key, key.ACCESS_DUPLICATE_KEY.ttl)
        pipeline.execute()
