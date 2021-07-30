/* eslint-disable max-len */
import Vue from 'vue'
import VueRouter, { RouteConfig } from 'vue-router'
import store from '../store/store'
import { getUrlParam, random } from '../../monitor-common/utils/utils'
import authorityStore from '../store/modules/authority'
import PluginMangerRoutes from './modules/plugin-manager'
import UptimeCheckRoutes from './modules/uptime-check'
import PerformanceRoutes from './modules/performance'
import EventCenterRoutes from './modules/event-center'
import AlarmGroupRoutes from './modules/alarm-group'
import ServiceClassify from './modules/service-classify'
import CollectorConfigRoutes from './modules/collector-config'
import StrategyConfigRoutes from './modules/strategy-config'
import AlarmShieldRoutes from './modules/alarm-shield'
import ExportImport from './modules/export-import'
import CustomEscalation from './modules/custom-escalation'
import NoBusiness from './modules/no-business'
import EmailSubscriptions from './modules/email-subscriptions'
import Auth from './modules/auth'

import * as globalConfigAuth from '../pages/global-config/authority-map'
import * as grafanaAuth from '../pages/grafana/authority-map'
import * as homeAuth from '../pages/home/authority-map'
import * as healthzAuth from '../pages/healthz/authority-map'
import * as upgradeAuth from '../pages/upgrade-config/authority-map'
import * as functionAuth from '../pages/function-switch/authority-map'
import * as migrateDashbordAuth from '../pages/migrate-dashboard/authority-map'
import * as dataRetrievalAuth from '../pages/data-retrieval/authority-map'
Vue.use(VueRouter)
const Home = () => import(/* webpackChunkName: 'Home' */'../pages/home/Home.vue')
const MoHealthzView = () => import(/* webpackChunkName: 'MoHealthzView' */'../pages/healthz/healthz.vue')
const ExceptionPage = () => import(/* webpackChunkName: 'ExceptionPage' */'../pages/exception-page/exception-page.vue')
// const UpgradePage = () => import(/* webpackChunkName: 'UpgradePage' */
// '@page/collector-upgrade/collector-upgrade.vue')
// const LogRetrieval = () => import(/* webpackChunkName: 'LogRetrieval' */'../pages/log-retrieval/log-retrieval.vue')
const Grafana = () => import(/* webpackChunkName: 'Grafana' */'../pages/grafana/grafana.vue')
const GlobalConfig = () => import(/* webpackChunkName: 'GlobalConfig' */'../pages/global-config/global-config.vue')
const UpgradeConfig = () => import(/* webpackChunkName: 'UpgradeConfig' */'../pages/upgrade-config/upgrade-config.vue')
const DataRetrieval = () => import(/* webpackChunkName: 'DataRetrieval'*/'../pages/data-retrieval/data-retrieval.vue')
const FunctionSwitch = () => import(/* webpackChunkName: 'FunctionSwitch' */'../pages/function-switch/function-switch.vue')
const ViewDetail = () => import(/* webpackChunkName: 'ViewDetail' */'../pages/view-detail/view-detail.vue')
// const FunctionSwitch = () => import(
//   /* webpackChunkName: 'FunctionSwitch' */
//   '../pages/function-switch/function-switch.vue')

const MigrateDashboard = () => import(
  /* webpackChunkName: 'MigrateDashboard' */
  '../pages/migrate-dashboard/migrate-dashboard.vue')
const routes: RouteConfig[] = [
  {
    path: '/',
    name: 'home',
    components: {
      noCache: Home
    },
    meta: {
      title: '首页',
      navId: 'home',
      authority: {
        page: homeAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/healthz',
    name: 'healthz',
    components: {
      noCache: MoHealthzView
    },
    meta: {
      title: '自监控',
      navId: 'healthz',
      authority: {
        page: healthzAuth.VIEW_AUTH
      }
    }
  },
  // {
  //   path: '/function-switch',
  //   name: 'function-switch',
  //   components: {
  //     noCache: FunctionSwitch
  //   },
  //   meta: {
  //     title: '功能开关',
  //     navId: 'function-switch'
  //   }
  // },
  // {
  //   path: '/log-retrieval',
  //   name: 'log-retrieval',
  //   component: LogRetrieval,
  //   meta: {
  //     title: '日志检索',
  //     navId: 'log-retrieval'
  //   }
  // },
  {
    path: '/data-retrieval',
    name: 'data-retrieval',
    component: DataRetrieval,
    meta: {
      title: '数据检索',
      navId: 'data-retrieval',
      navClass: 'data-retrieval-nav',
      needClearQuery: true, // 需要清空query搜索条件
      authority: {
        map: dataRetrievalAuth,
        page: dataRetrievalAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/grafana',
    name: 'grafana',
    components: {
      noCache: Grafana
    },
    meta: {
      title: '仪表盘',
      navId: 'grafana',
      authority: {
        map: grafanaAuth,
        page: grafanaAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/global-config',
    name: 'global-config',
    components: {
      noCache: GlobalConfig
    },
    meta: {
      title: '全局配置',
      navId: 'global-config',
      authority: {
        map: globalConfigAuth,
        page: globalConfigAuth.VIEW_AUTH
      }
    }
  },
  ...PerformanceRoutes,
  ...PluginMangerRoutes,
  ...UptimeCheckRoutes,
  ...EventCenterRoutes,
  ...AlarmGroupRoutes,
  ...ServiceClassify,
  ...CollectorConfigRoutes,
  ...StrategyConfigRoutes,
  ...AlarmShieldRoutes,
  ...ExportImport,
  ...CustomEscalation,
  ...Auth,
  ...NoBusiness,
  ...EmailSubscriptions,
  {
    path: '/upgrade-config',
    name: 'upgrade-config',
    components: {
      noCache: UpgradeConfig
    },
    meta: {
      title: '配置升级',
      navId: 'upgrade-config',
      authority: {
        map: upgradeAuth,
        page: upgradeAuth.MANAGE_AUTH
      }
    }
  },
  {
    path: '/function-switch',
    name: 'function-switch',
    components: {
      noCache: FunctionSwitch
    },
    meta: {
      title: '功能开关',
      navId: 'function-switch',
      authority: {
        map: functionAuth,
        page: functionAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/exception/:type?/:queryUid?',
    name: 'error-exception',
    component: ExceptionPage,
    props: true,
    beforeEnter(to, from, next) {
      to.meta.title = to.params.type === '403' ? '无权限' : to.params.title || to.params.type || '404'
      next()
    },
    meta: {
      title: '404',
      navId: 'exception'
    }
  },
  {
    path: '/migrate-dashboard',
    name: 'migrate-dashboard',
    components: {
      noCache: MigrateDashboard
    },
    meta: {
      title: '迁移仪表盘',
      navId: 'migrate-dashboard',
      authority: {
        map: migrateDashbordAuth,
        page: migrateDashbordAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/view-detail',
    name: 'view-detail',
    components: {
      noCache: ViewDetail
    },
    meta: {
      title: '视图详情',
      navId: 'view-detail'
    }
  },
  {
    path: '*',
    redirect: '/exception'
  }
]

const isAuthority = async (page: string | string[]) => {
  const data: {isAllowed: boolean}[] = await authorityStore.checkAllowedByActionIds({
    action_ids: Array.isArray(page) ? page : [page]
  })
  return !!data.length && data.some(item => item.isAllowed)
}

const router = new VueRouter({
  mode: 'hash',
  routes
})

router.beforeEach(async (to, from, next) => {
  store.commit('app/SET_NAV_ID', to.meta.navId)

  // 无业务页面跳转处理
  const isEmailSubscriptions = (from.path || from.name || '').indexOf('email-subscriptions') > -1
  const toEmailSubscriptionsPage = (to.path || to.name || '').indexOf('email-subscriptions') > -1
  if (isEmailSubscriptions) {
    const bizId = getUrlParam('bizId')
    if (toEmailSubscriptionsPage || (bizId !== null && bizId > -1)) {
      next()
    } else {
      const { origin, pathname } = location
      const bizid = localStorage.getItem('__biz_id__') || -1
      location.href = `${origin}${pathname}?bizId=${bizid}#${to.fullPath}`
      return
    }
  }

  const { fromUrl, actionId } = to.query
  if (to.name === 'error-exception' && actionId) {
    let hasAuthority = false
    if (!from.name) {
      hasAuthority = await isAuthority(actionId as string | string[])
    }
    if (hasAuthority) {
      next(`/${fromUrl}`)
    } else {
      next()
    }
    return
  }

  let hasAuthority = true
  const { authority } = to.meta
  if (authority?.page && to.name !== 'error-exception') {
    hasAuthority = await isAuthority(authority?.page)
  }
  if (hasAuthority) {
    if (!store.getters.upgradeAllowed && to.name === 'upgrade-config') {
      next('/')
    } else {
      next()
    }
  } else {
    next({
      path: `/exception/403/${random(10)}`,
      query: {
        actionId: authority.page || '',
        fromUrl: to.path.replace(/^\//, '')
      },
      params: {
        title: '无权限'
      }
    })
  }
})
router.afterEach((to) => {
  store.commit('app/SET_NAV_TITLE', to.params.title || to.meta.title)
})

export default router
