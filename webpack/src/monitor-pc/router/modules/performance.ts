/* eslint-disable max-len */
import * as performanceAuth from '../../pages/performance/authority-map'
import { RouteConfig } from 'vue-router'
const Performance = () => import(/* webpackChunkName: 'Performance' */'../../pages/performance/performance.vue')
const PerformanceDetailNew = () => import(/* webpackChunkName: 'PerformanceDetailNew' */'../../pages/performance/performance-detail/performance-detail-new.vue')

export default [
  {
    path: '/performance',
    name: 'performance',
    props: true,
    component: Performance,
    meta: {
      title: '主机监控',
      navId: 'performance',
      authority: {
        page: performanceAuth.VIEW_AUTH
      }
    }
  },
  // {
  //   path: '/performance/detail/:id?/:processId?',
  //   name: 'performance-detail',
  //   component: PerformanceDetail,
  //   beforeEnter(to, from, next) {
  //     to.meta.title = to.params.title || to.params.id.slice(0, to.params.id.indexOf('-')) || '主机监控详情'
  //     next()
  //   },
  //   meta: {
  //     title: '主机监控详情',
  //     needBack: true,
  //     navId: 'performance'
  //   }
  // },
  {
    path: '/performance/detail/:id/:processId?',
    name: 'performance-detail',
    component: PerformanceDetailNew,
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || to.params.id.slice(0, to.params.id.indexOf('-')) || '主机监控详情'
      next()
    },
    props: route => ({
      ...route.params,
      ...route.query
    }),
    meta: {
      title: '主机监控详情',
      needBack: true,
      navId: 'performance',
      authority: {
        map: performanceAuth,
        page: performanceAuth.VIEW_AUTH
      },
      customContent: true
    }
  }
] as RouteConfig[]
