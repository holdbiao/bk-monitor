import EventCenter from './event-center/event-center'
import BizManage from './biz-manange/biz-manage'
import Home from './home/Home'
import CalendarTooltips from './event-center/event-center-calendar/calendar-tooltips'
import LogCollectorImport from './log-collector/log-collector-import'
import CollectorUpgrade from './collector-upgrade/collector-upgrade'
import PluginManager from './plugin-manager/plugin-manager.vue'
import Performance from './performance/performance'
import CollectorConfig from './collector-config/collector-config.vue'
import UptimeCheckTask from './uptime-check/uptime-check-task/uptime-check-task.vue'
import UptimeCheckNodes from './uptime-check/uptime-check-nodes/uptime-check-nodes.vue'
import MonitorNavigation from './monitor-navigation/monitor-navigation.vue'
import StrategyConfig from './strategy-config/strategy-config.vue'
import AlarmGroup from './alarm-group/alarm-group.vue'
import ServiceClassify from './service-classify/service-classify.vue'

const Components = [
  EventCenter,
  BizManage,
  Home,
  CalendarTooltips,
  // ShellCollector,
  LogCollectorImport,
  CollectorUpgrade,
  PluginManager,
  Performance,
  CollectorConfig,
  UptimeCheckTask,
  UptimeCheckNodes,
  MonitorNavigation,
  StrategyConfig,
  AlarmGroup,
  ServiceClassify

]

class Containers {
  constructor() {
    if (typeof window !== 'undefined' && window.Vue) {
      this.install(window.Vue)
    }
  }

  install(Vue) {
    Components.forEach((component) => {
      Vue.component(component.name, component)
    })
  }
}

export default new Containers()
