# bkmonitorbeat_test.conf
output.console:
logging.level: debug
bkmonitorbeat:
  node_id: 0
  ip: 127.0.0.1
  bk_cloud_id: 0
  bk_biz_id: 0
  clean_up_timeout: 1s
  event_buffer_size: 10
  mode: check
  heart_beat:
    global_dataid: 1100001
    child_dataid: 1100002
    period: 60s
  ping_task:
    dataid: {{ data_id | default(1100003, true) }}
    max_buffer_size: {{ max_buffer_size | default(10240, true) }}
    max_timeout: {{ max_timeout | default("100s", true) }}
    min_period: {{ min_period | default("3s", true) }}
    tasks: {% for task in tasks %}
      - task_id: {{ task.task_id }}
        bk_biz_id: {{ task.bk_biz_id }}
        period: {{ task.period }}
        timeout: {{ task.timeout | default("3s", true) }}
        max_rtt: {{ task.max_rtt }}
        total_num: {{ task.total_num }}
        size: {{ task.size }}
        targets: {% for host in task.target_hosts %}
            - target: {{ host.ip}}
              target_type: {{ host.target_type | default("ip", true)}}{% endfor %}{% endfor %}
