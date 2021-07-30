# alarm_backends 

```
worker
├── bin        # 启动脚本相关
├── conf       # 配置相关，这个目录目前放在外层
├── common     # 公共服务，组件的使用
│   ├── cache
│   ├── db
│   └── queue
├── service    # 后台进程
│   ├── access
│   ├── detect
│   ├── event
│   ├── notice
│   ├── recovery
│   └── selmon
└── tests      # 单元测试
    ├── __init__.py
    ├── test_access.py
    ├── test_detect.py
    └── test_trigger.py

```


## 功能点
- 主体功能
- 流控
- 单元测试
- 自监控
    - 日志轮转
    - 数据处理链路，各个阶段的指标数据上报
    - 工具，包括简单的分析，做辅助排查
- 升级方案
    - DB结构迁移方案
    - 策略配置数据迁移方案
    - 代码部署的升级方案


## 本地启动方式
统一走django的manage启动方式

- 设置环境变量(修改一下变量参数)

```
export DJANGO_SETTINGS_MODULE=settings
export DJANGO_CONF_MODULE=conf.worker.development.enterprise

export APP_TOKEN=replace-me-to-your-app-token
export BK_PAAS_HOST=https://replace.me
```

- 启动run_access

```
python manage.py run_access -s access --access-type=data --min-interval 30
```

- 启动其他服务run_service

```
python manage.py run_service -s detect
```

- 采用celery异步任务的方式运行（默认在当前进程启动）

```
python manage.py run_service -s detect -H celery
```


## supervisor启动方式

- 通过命令生成好配置文件`supervisord.conf`，目录在`alarm_backends/conf`下

```bash
# 根据settings相关配置，生成supervisor启动配置文件
python manage.py gen_config
```

- 启动supervisor

```bash
supervisord -c alarm_backends/conf/supervisord.conf
``` 