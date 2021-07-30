import * as AlarmGroupAuth from '../../pages/alarm-group/authority-map'
import { RouteConfig, Route } from 'vue-router'
import Vue from 'vue'
const AlarmGroup = () => import(/* webpackChunkName: 'AlarmGroup' */'@page/alarm-group/alarm-group.vue')
const AlarmGroupAdd = () => import(
  /* webpackChunkName: 'AlarmGroupAdd' */
  '@page/alarm-group/alarm-group-add/alarm-group-add.vue')

export default [
  {
    path: '/alarm-group',
    name: 'alarm-group',
    component: AlarmGroup,
    meta: {
      title: '告警组',
      navId: 'alarm-group',
      authority: {
        map: AlarmGroupAuth,
        page: [AlarmGroupAuth.VIEW_AUTH]
      }
    }
  },
  {
    path: '/alarm-group/add',
    name: 'alarm-group-add',
    components: {
      noCache: AlarmGroupAdd
    },
    meta: {
      title: '新建告警组',
      navId: 'alarm-group',
      needBack: true,
      authority: {
        map: AlarmGroupAuth,
        page: [AlarmGroupAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/alarm-group/edit/:id',
    name: 'alarm-group-edit',
    components: {
      noCache: AlarmGroupAdd
    },
    props: {
      noCache: true
    },
    beforeEnter(
      to: Route, from: Route
      , next:  (to?: string | false | void | Location | ((vm: Vue) => any) | undefined) => void
    ) {
      to.meta.title = to.params.title || '加载中...'
      next()
    },
    meta: {
      title: '加载中...',
      navId: 'alarm-group',
      needBack: true,
      authority: {
        map: AlarmGroupAuth,
        page: [AlarmGroupAuth.MANAGE_AUTH]
      }
    }
  }
] as RouteConfig[]
