import Vue from 'vue'
import Router, { RouteConfig } from 'vue-router'
Vue.use(Router)
const AlarmInfo = () => import(/* webpackChunkName: "alarm-info" */ '../pages/alarm-info/alarm-info.vue')
const AlarmDetail = () => import(/* webpackChunkName: "alarm-detail" */ '../pages/alarm-detail/alarm-detail.vue')
const EventCenter = () => import(/* webpackChunkName: "event-center" */ '../pages/event-center/event-center.vue')
const TendencyChart = () => import(
  /* webpackChunkName: "tendency-chart" */
  '../pages/tendency-chart/tendency-chart.vue')
const QuickAlarmShield = () => import(
  /* webpackChunkName: "quick-alarm-shield" */
  '../pages/quick-alarm-shield/quick-alarm-shield.vue')

export const routerConfig: RouteConfig[] = [
  {
    path: '/alarm-info',
    name: 'alarm-info',
    props: true,
    component: AlarmInfo,
    meta: {
      title: '告警信息'
    }
  },
  {
    path: '/detail/:id?',
    name: 'alarm-detail',
    props: true,
    component: AlarmDetail,
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || window.i18n.tc('告警详情')
      next()
    },
    meta: {
      title: '告警详情'
    }
  },
  {
    path: '/event-center',
    name: 'event-center',
    component: EventCenter,
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '事件中心'
      next()
    },
    meta: {
      title: '事件中心'
    }
  },
  {
    path: '/tendency-chart/:id?',
    name: 'tendency-chart',
    props: true,
    component: TendencyChart,
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '趋势图'
      next()
    },
    meta: {
      title: '趋势图'
    }
  },
  {
    path: '/quick-alarm-shield/:eventId?',
    name: 'quick-alarm-shield',
    props: true,
    component: QuickAlarmShield,
    beforeEnter(to, from, next) {
      if (to.params.eventId) {
        to.meta.title = to.params.title || '快捷屏蔽'
        next()
      } else {
        next('/')
      }
    },
    meta: {
      title: '快捷屏蔽'
    }
  },
  {
    path: '*',
    redirect: {
      name: 'alarm-info'
    }
  }
]

const createRouter = () => new Router({
  scrollBehavior: (to, from, savedPosition) => {
    if (savedPosition) {
      return savedPosition
    }
    return { x: 0, y: 0 }
  },
  mode: 'hash',
  routes: routerConfig
})

const router = createRouter()
router.beforeEach((to, from, next) => {
  document.title = to.params.title || to.meta.title || '监控平台'
  next()
})
export default router
