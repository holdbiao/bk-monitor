# 3.2.176
- 参考发布公告
    
# 1.5.26
- bug fix:
    - 修复国际化翻译问题

# 1.5.12
- feature
    - 磁盘类事件告警过滤对应配置磁盘类型的告警

# 1.5.11
- bug fix
    - 修复mysql重启后，后台进程仍然持有原来的连接导致执行sql出错的问题
    - 修复自定义字符型配置集群模块后不能告警的问题
    - 修复事件型告警配置集群模块后不能告警的问题

# 1.5.4
- bug fix
    - 修复配置集群模块范围过滤的监控，不能告警的问题
    - 修复自定义字符型告警范围配置IP后不能告警的问题

# 1.5.2
- feature
    - 更新migrate规范

# 1.5.1
- feature
    - 补充翻译，国际化（多语言和多时区）

# 1.4.21
- bug fix
    - 优化业务量大的情况下告警拉取慢的问题

# 1.4.19
- bug fix
    - 修复部分环境汇总告警无通知的情况

# 1.4.18
- feature
    - 去除Ping/Agent告警的合并规则

# 1.4.17
- bug fix
    - 修复汇总告警时间不正确的问题
    - 修复部分告警会丢失的问题
    - 修复告警通知人同步配置平台失败的问题

# 1.4.15
- bug fix
    - 修复日志关键字部分情况下不告警的问题
    - 修复拉取cmdb接口类型不一致的问题

# 1.4.13
- bug fix
    - 修复告警汇总失败问题

# 1.4.7
- bug fix
    - 修复job调用失败的问题
    - 修复通过告警时间屏蔽不生效的问题

# 1.4.1
- 功能优化
    - 变更架构，性能提升

# 1.2.10
- bug fix
    - 修复告警范围匹配部分失败的问题

# 1.2.9
- bug fix
    - 修复邮件告警部分未翻译的问题

# 1.2.7
- bug fix
    - 修复模块引入错误的问题

# 1.2.6
- 优化功能
    - 日志新增错误码

# 1.2.5
- bug fix
    - 修复事件型告警时区不对的问题

# 1.2.4
- bug fix
    - 修复业务id不正确导致自愈处理失败的问题

# 1.2.3
- bug fix
    - 合并1.x版本的改动到1.2

# 1.2.2
- 新增功能
    - 增加对多时区的支持

# 1.2.1
- 新增功能
    - 增加对多语言的支持

# 1.1.16
- bug fix
    - 修改由于进程运行异常后有可能不重启的问题。

# 1.1.15
- bug fix
    - 解决告警维度匹配有可能失败的问题

# 1.1.14
- bug fix
    - 解决ping等事件数据格式时间不正确的问题

# 1.1.13
- bug fix
    - 解决ping等事件数据格式导致自愈无法使用问题

# 1.1.12
- bug fix
    - 解决ping等事件数据格式导致自愈无法使用问题

# 1.1.11
- 新增功能
    - 无

- 优化功能
    - 日志队列已满告警信息优化

- bug fix
    - 解决监控异常的问题
    
# 1.1.10
- 新增功能
    - 无

- 优化功能
    - 优化日志大小设置10G -> 200M

- bug fix
    - 无
    
# 1.1.9
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 解决告警策略配置告警范围可能无法告警的问题
    
# 1.1.8
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 修复生成的告警content中当前指标值不正确的问题

# 1.1.7
- 新增功能
    - 短信通知定制模板

- 优化功能
    - 无

- bug fix
    - 无
    
# 1.1.6
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - esb组件调用域名使用内网域名
    
# 1.1.5
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 解决自动处理无法禁用的问题。

# 1.1.4
- 新增功能
    - 无

- 优化功能
    - 为告警实例表添加一个索引，优化接口查询效率

- bug fix
    - 无

# 1.1.3
- 新增功能
    - 无

- 优化功能
    - ping不可达告警调整为非直连区域告警才需要判断告警机器是否属于同一个业务

- bug fix
    - 告警列表变量未定义导致基础告警拉取失败
    - 待检测数据队列长度判断阈值设置不合理

# 1.1.2
- 新增功能
    - 无

- 优化功能
    - 优化数据拉取进程和检测进程的启动方式
    - 修改配置文件中的数据库IP变量名
    - 数据拉取进程新增缓存锁 防止多个进程对同一段时间的数据进行多次读取

- bug fix
    - 无

# 1.1.1
- 新增功能
    - 无

- 优化功能
    - 日志自动删除时间由10天改为7天

- bug fix
    - 数据接入模块拉取数据时 无数据时会触发一个写入错误的告警

# 1.1.0
- 新增功能
    - 统一监控源实时数据获取模式 优化循环 提高监控源数据处理效率

- 优化功能
    - 优化数据写入缓存模式 改为批量写入
    - 简化机器重启监控逻辑

- bug fix
    - 修改配置文件中的错误变量导致部署初始化失败的问题
    - 修改进程端口从mysql拉取数据聚合函数错误的问题

# 1.0.9
- 新增功能
    - 无

- 优化功能
    - 数据平台db模式查询返回时间从字符型日期改为时间戳
    - 后台升级脚本变更 默认业务改为自行从cc获取
    - 初始化配置文件名称变更 beanstalk参数变量变更
    - 监控待检测数据队列增加长度判断 防止爆redis
    - 数据拉取和数据检测流程取消落地文件存储模式 通过checkpoint进行failover恢复控制

- bug fix
    - 无

# 1.0.8
- 新增功能
    - 无

- 优化功能
    - 更新单元测试用例

- bug fix
    - 无


# 1.0.7
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 修复因redis切换sentinel模式引起的部分功能问题

# 1.0.6
- 新增功能
    - 无

- 优化功能
    - 管理脚本调整

- bug fix
    - 监控维度条件过滤兼容整形和字符型转换的问题

# 1.0.5
- 新增功能
    - 无

- 优化功能
    - 修改部分缓存key 保持前缀一致性

- bug fix
    - 无

# 1.0.4
- 新增功能
    - 无

- 优化功能
    - 微信发送通知接口变更 (未测试)
    - 删除重构后的多余代码

- bug fix
    - 无

# 1.0.3
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 修复日志无法写入redis的问题
    - 修复定时任务执行命令错误的问题
    - 修复监控锁抛出异常时未捕获的问题
    - 修复关键字告警维度不对的问题

# 1.0.2
- 新增功能
    - 默认自监控策略由原上报模式改为新的快照模式

- 优化功能
    - 无

- bug fix
    - 升级脚本出错 部分函数依赖关系未调整导致

# 1.0.1
- 新增功能
    - 新增日志关键字监控
    - 新增机器重启监控
    - 新增进程端口存在监控
    - 代码重构 新增数据接入层 将监控源数据处理从检测模块解耦

- 优化功能
    - redis改为sentinel方式

- bug fix
    - 修改告警读取方式 解决读取告警时因部分告警解析失败而导致当前批次所有告警全部没有处理的问题

# 0.0.19
- 新增功能
    - 无

- 优化功能
    - 删除多余的配置目录及文件

- bug fix
    - 无

# 0.0.18
- 新增功能
    - 无

- 优化功能
    - 版本脱敏
    - 修改告警类型优先级

- bug fix
    - 无

# 0.0.17
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 取消监控内部运营数据写入缓存队列

# 0.0.16
- 新增功能
    - 新增SELF_CONTAINED_PIP_PKG文件 安装组件由项目自身提供

- 优化功能
    - 修改pip pkgs安装包目录 和其他项目保持一致

- bug fix
    - 无

# 0.0.15
- 新增功能
    - 新增子监控体系默认监控策略
    - 新增后台数据库升级功能
    - 新增数据库升级配置文件
    - 新增蓝鲸监控变量BK_BIZ_ID
    - 调整监控orm model
    - 新增数据库升级脚本(bin/upgrade.sh) 降级脚本(bin/downgrade.sh)
    - 新增alembic库及安装包

- 优化功能
    - 无

- bug fix
    - 无

# 0.0.14
- 新增功能
    - 无

- 优化功能
    - 增加未通知状态 因告警不在通知时间段内而不发出的状态记录为未通知状态

- bug fix
    - 修复简单环比和高级环比告警内容为空的问题
    - 修复因时间字段重名导致部分情况下无法取出数据的问题
    - 修复维度分割符不合理导致的告警无法发出问题

# 0.0.13
- 新增功能
    - 无

- 优化功能
    - 测试脚本调整

- bug fix
    - 无

# 0.0.12
- 新增功能
    - 无

- 优化功能
    - 测试用例修改

- bug fix
    - 无

# 0.0.11
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 进程端口告警流程修改 目前缺少参数导致无法告警
    - 自定义指标采用count聚合时 因原始表没有count字段 导致无法聚合 需要特殊处理
    - 自定义告警中添加了额外维度 拼装告警内容时需要去掉额外维度的信息
    - 进程端口告警内容缺少失效端口信息

# 0.0.10
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 基础告警的告警列表被覆盖 导致agent告警发送失败
    - 自定义指标告警缺少单位导致告警信息拼装错误

# 0.0.9
- 新增功能
    - 当主机负责人或者备份负责人未填写时 会将通知人替换为模块负责人或者备份负责人

- 优化功能
    - 无

- bug fix
    - 无

# 0.0.8
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 处理表映射错误 导致告警无法使用job处理
    - 自定义字符型告警的source_id生成方式会导致该类型告警无法使用自动处理
    - 告警处理配置中需带上operator用户 否则无法调用jobs作业

# 0.0.7
- 新增功能
    - 无

- 优化功能
    - 测试用例新增定时任务巡检
    - 测试用例新增基础告警检测
    - 测试用例新增自定义字符型告警检测

- bug fix
    - 无


# 0.0.6
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 基础告警去掉公共区域匹配逻辑
    - 自定义字符型告警去掉公共区域匹配逻辑

# 0.0.5
- 新增功能
    - 无

- 优化功能
    - 检测脚本增加基础告警队列检查

- bug fix
    - 无


# 0.0.4
- 新增功能
    - 无

- 优化功能
    - 无

- bug fix
    - 外部版table没有unit字段
    - 缓存更新时间过长 可能导致监控刚启动时 缓存不存在的情况 已兼容
    - query_bk_data文件未和内部版同步 导致少了一个参数


# 0.0.3
- 新增功能
    - 无

- 优化功能
    - 修改基础告警队列获取方式
    - 修改redis配置
    - 调整beanstalkd队列名称

- bug fix
    - 自定义告警告警源配置错误
    - 按角色获取主机主备负责人时 拿到了错误的业务操作者的帐号

# 0.0.2
- 新增功能
    - 无

- 优化功能
    - paas cmdb job域名前缀需要可配置化

- bug fix
    - 网络流量单位错误
    - 取消邮件中的图片
    - 内部job server调用地址绑定错误


# 0.0.1
- 新增功能
    - 基础性能指标监控
    - 自定义数值型指标监控
    - 同比,环比等5种基本监控策略
    - 支持防抖,收敛,汇总,屏蔽等告警处理方式
    - 支持短信,邮件,微信等多种通知渠道
    - 支持按配置中心角色进行告警通知

- 优化功能
    - 无

- bug fix
    - 无
