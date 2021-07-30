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


import logging
from collections import OrderedDict, defaultdict

from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from alarm_backends.constants import LATEST_POINT_WITH_ALL_KEY
from alarm_backends.core.detect_result import ANOMALY_LABEL, CheckResult
from bkmonitor.utils.text import camel_to_underscore

logger = logging.getLogger("core.control")


def load_detector_cls(_type):
    algorithms_target = camel_to_underscore(_type)
    package_name = "alarm_backends.service.detect"
    cls_target = "{}.strategy.{}.{}".format(package_name, algorithms_target, _type)
    try:
        cls = import_string(cls_target)
    except ImportError:
        logger.error("detector load error: {}".format(cls_target))
        cls = None
    return cls


class DetectMixin(object):
    def detect(self, data_points):
        if not data_points:
            return []

        algorithm_group = defaultdict(list)
        for _config in self.algorithm_list:
            level = int(_config["level"])
            algorithm_group[level].append(_config)

        levels = sorted(algorithm_group.keys())

        # 初始化检测结果
        detected_result_dict = OrderedDict()

        for level in levels:
            detector_list = []
            for detect_config in algorithm_group[level]:
                algorithm_type = detect_config["algorithm_type"]
                algorithm_unit = detect_config.get("algorithm_unit", "")
                detector_cls = load_detector_cls(algorithm_type)
                detector = detector_cls(detect_config["algorithm_config"], algorithm_unit)
                if hasattr(detector, "history_point_fetcher"):
                    # query history point
                    detector.query_history_points(data_points)
                detector_list.append(detector)

            if len(detector_list) == 1:
                anomaly_records = detector_list[0].detect_records(data_points, level)
            else:
                # 组合策略
                anomaly_records = []
                for data_point in data_points:
                    ap = None
                    prefix = suffix = ""
                    for d in detector_list:
                        try:
                            single_ret = d.detect(data_point)
                            if not single_ret:
                                ap = None
                                break

                            single_ap = d.gen_anomaly_point(data_point, single_ret, level, auto_format=False)
                            if not prefix:
                                prefix, suffix = d.anomaly_message_template_tuple(data_point)
                                print(prefix, suffix)
                            if ap:
                                ap.anomaly_message += _(" 同时 ") + single_ap.anomaly_message
                            else:
                                ap = single_ap

                        except Exception:
                            ap = None
                            break

                    if ap:
                        ap.anomaly_message = prefix + ap.anomaly_message + suffix
                        logger.info(
                            _("[detect] strategy({}) item({}) level[{}] 发现异常点: {}").format(
                                ap.data_point.item.strategy.id, ap.data_point.item.id, level, ap.__dict__
                            )
                        )
                        anomaly_records.append(ap)

            self._update_monitor_dimensions_checkpoint(data_points, anomaly_records, level)

            for ar in anomaly_records:
                collection = detected_result_dict.setdefault(ar.data_point.record_id, {})
                collection.update(self._update_anomaly_info_with_point(ar, level, collection))

        return list(detected_result_dict.values())

    def _update_anomaly_info_with_point(self, anomaly_point, level, info_collection=None):
        info_collection = info_collection or {
            "data": anomaly_point.data_point.as_dict(),
            "anomaly": {},
            "strategy_snapshot_key": self.strategy.snapshot_key,
        }

        info_collection["anomaly"].update(
            {
                str(level): {
                    "anomaly_message": anomaly_point.anomaly_message,
                    "anomaly_id": anomaly_point.anomaly_id,
                    "anomaly_time": anomaly_point.anomaly_time,
                }
            }
        )
        return info_collection

    def _update_monitor_dimensions_checkpoint(self, records, anomaly_records, level):
        redis_pipeline = None
        last_checkpoints = {}
        anomaly_record_ids = {i.data_point.record_id for i in anomaly_records}
        latest_point_with_all = 0
        for d in records:
            # data_record 的record_id规则： {dimensions_md5}.{timestamp}
            dimensions_md5, timestamp = d.record_id.split(".")
            timestamp = int(timestamp)
            latest_point_with_all = max([latest_point_with_all, d.timestamp])

            check_result = CheckResult(self.strategy.id, self.id, dimensions_md5, level)
            if redis_pipeline is None:
                redis_pipeline = check_result.CHECK_RESULT

            if d.record_id in anomaly_record_ids:
                name = "{}|{}".format(timestamp, ANOMALY_LABEL)
            else:
                name = "{}|{}".format(timestamp, str(d.value))

            try:
                # 1. 缓存数据(检测结果缓存) type:SortedSet
                kwargs = {name: timestamp}
                check_result.add_check_result_cache(**kwargs)

                # 2. 缓存最后checkpoint type:Hash，先放到内存里，最后再一次性写入redis
                last_point = last_checkpoints.setdefault(dimensions_md5, 0)
                if last_point < timestamp:
                    last_checkpoints[dimensions_md5] = timestamp

            except Exception as e:
                msg = "set check result cache error:%s" % e
                logger.exception(msg)

        if redis_pipeline:
            check_result.expire_key_to_dimension()
            redis_pipeline.execute()

        if latest_point_with_all:
            last_checkpoints[LATEST_POINT_WITH_ALL_KEY] = latest_point_with_all

        # 更新last_checkpoint
        for _dimensions_md5, point_timestamp in list(last_checkpoints.items()):
            try:
                CheckResult.update_last_checkpoint_by_dimensions_md5(
                    self.strategy.id, self.id, _dimensions_md5, point_timestamp, level
                )
            except Exception as e:
                msg = "set check result cache last_check_point error:%s" % e
                logger.exception(msg)
        CheckResult.expire_last_checkpoint_cache()
