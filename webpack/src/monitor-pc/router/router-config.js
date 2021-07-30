export const routeConfig = [
  {
    name: '首页',
    icon: 'icon-monitor icon-menu-home menu-icon',
    id: 'home',
    path: '/',
    href: '#/'
  },
  {
    name: '仪表盘',
    icon: 'icon-monitor icon-menu-chart menu-icon',
    id: 'grafana',
    path: '/grafana'
  },
  {
    name: '监控场景',
    shortName: '场景',
    id: 'uptimecheck',
    children: [
      {
        name: '主机监控',
        icon: 'icon-monitor icon-menu-performance menu-icon',
        id: 'performance',
        path: '/performance',
        href: '#/performance'
      },
      {
        name: '服务拨测',
        icon: 'icon-monitor icon-menu-uptime menu-icon',
        navName: '服务拨测',
        id: 'uptime-check',
        path: '/uptime-check',
        href: '#/uptime-check'
      }
      // {
      //   name: '拨测任务',
      //   icon: 'icon-monitor icon-menu-task menu-icon',
      //   navName: '拨测任务',
      //   id: 'uptime-check-task',
      //   path: '/uptime-check-task',
      //   href: '#/uptime-check-task'
      // },
      // {
      //   name: '拨测节点',
      //   navName: '拨测节点',
      //   icon: 'icon-monitor icon-menu-node menu-icon',
      //   id: 'uptime-check-node',
      //   path: '/uptime-check-node',
      //   href: '#/uptime-check-node'
      // }
    ]
  },
  {
    name: '分析定位',
    id: 'uptimecheck',
    shortName: '定位',
    children: [
      {
        name: '数据检索',
        icon: 'icon-monitor icon-mc-retrieval menu-icon',
        id: 'data-retrieval',
        path: '/data-retrieval',
        href: '#/data-retrieval'
      },
      {
        name: '事件中心',
        icon: 'icon-monitor icon-menu-event menu-icon',
        id: 'event-center',
        path: '/event-center',
        href: '#/event-center'
      }
    ]
  },
  {
    name: '监控配置',
    shortName: '配置',
    id: 'config',
    children: [
      {
        name: '插件管理',
        navName: '插件',
        icon: 'icon-monitor icon-menu-plugin menu-icon',
        id: 'plugin-manager',
        path: '/plugin-manager',
        href: '#/plugin-manager'
      },
      {
        name: '采集配置',
        navName: '采集',
        icon: 'icon-monitor icon-menu-collect menu-icon',
        id: 'collect-config',
        path: '/collect-config',
        href: '#/collect-config'
      },
      {
        name: '策略配置',
        navName: '策略',
        icon: 'icon-monitor icon-menu-strategy menu-icon',
        id: 'strategy-config',
        path: '/strategy-config',
        href: '#/strategy-config'
      },
      {
        name: '告警组',
        navName: '告警组',
        icon: 'icon-monitor icon-menu-group menu-icon',
        id: 'alarm-group',
        path: '/alarm-group',
        href: '#/alarm-group'
      },
      {
        name: '告警屏蔽',
        navName: '屏蔽',
        icon: 'icon-monitor icon-menu-shield menu-icon',
        id: 'alarm-shield',
        path: '/alarm-shield',
        href: '#/alarm-shield'
      },
      {
        name: '服务分类',
        navName: '分类',
        icon: 'icon-monitor icon-menu-classify menu-icon',
        id: 'service-classify',
        path: '/service-classify',
        href: '#/service-classify'
      },
      {
        name: '导入导出',
        icon: 'icon-monitor icon-menu-export menu-icon',
        id: 'export-import',
        path: '/export-import',
        href: '#/export-import'
      },
      {
        name: '自定义上报',
        icon: 'icon-monitor icon-menu-custom menu-icon',
        id: 'custom-escalation',
        path: '/custom-escalation',
        href: '#/custom-escalation',
        hidden: false
      }
    ]
  },
  {
    name: '系统管理',
    id: 'biz-manager',
    shortName: '管理',
    children: [
      // {
      //   name: '权限设置',
      //   navName: '权限设置',
      //   icon: 'icon-monitor icon-menu-auth menu-icon',
      //   id: 'auth',
      //   path: '/auth',
      //   href: '#/auth'
      // },
      {
        name: '全局配置',
        navName: '全局配置',
        icon: 'icon-monitor icon-menu-setting menu-icon',
        id: 'global-config',
        path: '/global-config',
        href: '#/global-config'
      },
      {
        name: '配置升级',
        icon: 'icon-monitor icon-menu-upgrade menu-icon',
        id: 'upgrade-config',
        path: '/upgrade-config',
        href: '#/upgrade-config',
        hidden: false
      },
      {
        name: '自监控',
        icon: 'icon-monitor icon-menu-self menu-icon',
        id: 'healthz',
        path: '/healthz',
        href: '#/healthz'
      },
      {
        name: '邮件订阅',
        icon: 'icon-monitor icon-mc-youjian menu-icon',
        id: 'email-subscriptions',
        path: '/email-subscriptions',
        href: '#/email-subscriptions',
        hidden: false
      }
      //   {
      //     name: '功能开关',
      //     id: 'function-switch',
      //     path: '/function-switch',
      //     href: '#/function-switch'
      //   },
      // {
      //   name: '迁移仪表盘',
      //   id: 'migrate-dashboard',
      //   path: '/migrate-dashboard',
      //   href: '#/migrate-dashboard'
      // }
    ]
  }
]

export const createRouteConfig = () => routeConfig

export const handleSetPageShow = (routeId, isShow) => {
  const globalConfigParentRoute = routeConfig.find(item => item.children
    && item.children.some(set => set.id === routeId))
  if (globalConfigParentRoute) {
    const globalConfigRoute = globalConfigParentRoute.children.find(item => item.id === routeId)
    globalConfigRoute.hidden = !isShow
  }
}
