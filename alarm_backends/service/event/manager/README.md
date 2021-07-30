# Recovery

模块负责检测事件的恢复状态

## 功能

- 支持的恢复触发方式：
    - 连续x个周期数据正常


## 模块设计

待补充

## 数据处理流程
- 从 redis 中拉取一条状态为未恢复的 event 记录
- 判断状态status是否已恢复
    - 是，不处理
- 判断 EVENT_ID_CACHE 的 event_id 是否与当前 event_id 匹配
    - 否，则恢复。写入一条EventAction（原因：数据已恢复），删除 EVENT_ID_CACHE
- 获取对应 event_id 的 AnomalyRecord 最新的一条记录（按 source_time 排序）
- 计算恢复窗口偏移量 offset = recovery_window * recovery_window_unit - 1
- 设置容错时长 fault_tolerance_seconds = 300
- 判断 now - source_time 是否大于 offset + fault_tolerance_seconds
    - 是，则恢复，写入一条EventAction（原因：数据已恢复），删除 EVENT_ID_CACHE
    - 否，不处理

## 相关数据说明

### 标准输入数据

待补充

### 标准输出数据

无


## 其他

- 模块需统计指标数据，能代表目前的处理能力
- 完善的日志记录
- 单元测试