## 事件推送消息队列

### 简介

该模块支持向指定的消息队列推送异常事件。

目前，它支持redis和kafka的URI。

### URI格式
#### Redis
Redis的URI为: `redis://:password@127.0.0.1:6279/0/queue/`

从前到后分别为
* 密码
* 域名/IP
* 端口
* DB
* 队列key

#### KafKa
KafKa的URI为: `kafka://username:password@127.0.0.1:9092/topic/`

从左到右分别为
* 用户
* 密码
* 域名/IP
* 端口
* 队列topic

### 消息格式

```json
{
    "event": {
        "bk_biz_id": 2,
        "strategy_id": 1,
        "event_id": "2b826f64639406580054ba94488fd8e3.1572875400.5.7.1",
        "begin_time": "2019-01-01 01:01:01",
        "create_time": "2019-01-01 01:01:01",
        "end_time": null,
        "level": 1
    },
    "anomaly_record": {
      "source_time":"2019-01-01 01:01:01",
      "anomaly_id":"508fe0c3c524b3dbe87ff4d8271653ad.1572854580.28.50.1",
      "origin_alarm":{
        "data":{
          "record_id":"508fe0c3c524b3dbe87ff4d8271653ad.1572854580",
          "values":{"disk_usage":4.5,"time":1572854580},
          "dimensions":{"bk_obj_id":"biz","bk_inst_id":"2"},
          "value":4.5,
          "time":1572854580
        },
        "anomaly":{
          "1":{
            "anomaly_message":"sum(disk_usage) >= 0.1, \\u5f53\\u524d\\u503c4.5",
            "anomaly_time":"2019-11-04 08:05:00",
            "anomaly_id":"508fe0c3c524b3dbe87ff4d8271653ad.1572854580.28.50.1"
          }
        }
      }
    },
    "type": "ANOMALY_NOTICE",
    "operate_statistics": {
        "CREATE": 1,
        "ANOMALY_NOTICE": 2
    }
}
```
