import { Component, Vue } from 'vue-property-decorator'
import { getDocLink } from '../../monitor-api/modules/commons'
//  文档链接的Mixin
@Component
export default class documentLinkMixin extends Vue {
  public linkMap: Object = {
    processMonitoring: 'guide/process_monitor.md', //  主机监控-主机详情 左下角 进程监控配置指引
    strategyTemplate: 'guide/notify_case.md', //  新建策略 高级设置-通知模版-模板使用说明
    globalConfiguration: 'guide/notify_setting.md', //  全局配置
    Script: 'guide/script_collect.md', //  插件管理 script 链接
    JMX: 'guide/plugin_jmx.md', //  插件管理 JMX 链接
    Exporter: 'guide/import_exporter.md', //  插件管理 exporter 链接
    DataDog: 'guide/import_datadog_online.md', //  插件管理 datadog 链接
    Pushgateway: 'guide/howto_bk-pull.md', //  插件管理 bk-pull 链接
    api: 'functions/conf/custom-report.md', //  自定义上报 API
    python: '',
    quickStartDial: 'functions/scene/dial.md', //  5分钟快速上手"服务拨测" 功能 前往查看
    bestPractices: 'quickstart/best-practices.md', //  了解"快速接入"方法
    processMonitor: 'guide/process_monitor.md', //  了解进程的配置方法
    scriptCollect: 'guide/script_collect.md', //  如何使用脚本进行服务监控？
    multiInstanceMonitor: 'guide/multi_instance_monitor.md', //  如何实现多实例采集？
    componentMonitor: 'guide/component_monitor.md', //  如何对开源组件进行监控？
    monitorUpdate: '应用运维文档/安装指南/monitor_update.md', //  迁移页面内容
    homeLink: 'intro/README.md', //  首页链接
    callbackLink: 'guide/http_callback.md', // 告警组-回调地址链接
    fromDataSource: 'guide/bigdata_monitor.md ', // 指标选择器-数据源平台的来源
    formLogPlatform: 'guide/log_monitor.md', // 指标选择器-日志平台的来源
    fromCustomRreporting: 'functions/conf/custom-report.md', // 指标选择器-自定义上报的来源
    fromMonitor: 'faq/collect_faq.md', // 指标选择器-监控采集的来源
    collectorConfigMd: 'functions/conf/collect-tasks.md' // 采集产品不白皮书
  }

  public handleGotoLink(id: string): void {
    const link = this.linkMap[id]
    if (link) {
      getDocLink({ md_path: link }).then((data) => {
        window.open(data, '_blank')
      })
        .catch(() => false)
    }
  }
}
