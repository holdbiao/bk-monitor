import * as alarmShieldAuth from '../../pages/alarm-shield/authority-map'
import { RouteConfig } from 'vue-router'
const AlarmShield = () => import(/* webpackChunkName: 'AlarmShield' */'@page/alarm-shield/alarm-shield.vue')
const AlarmShieldConfigSet = () => import(
  /* webpackChunkName: 'AlarmShield' */'@page/alarm-shield/alarm-shield-set/alarm-shield-set.vue')
const AlarmShieldDetail = () => import(
  /* webpackChunkName: 'AlarmShield' */
  '@page/alarm-shield/alarm-shield-detail/alarm-shield-detail.vue')
export default [
  {
    path: '/alarm-shield',
    name: 'alarm-shield',
    component: AlarmShield,
    meta: {
      title: '告警屏蔽',
      navId: 'alarm-shield',
      authority: {
        map: alarmShieldAuth,
        page: [alarmShieldAuth.VIEW_AUTH]
      }
    }
  },
  {
    path: '/alarm-shield-add',
    name: 'alarm-shield-add',
    components: {
      noCache: AlarmShieldConfigSet
    },
    meta: {
      title: '新建屏蔽',
      needBack: true,
      navId: 'alarm-shield',
      authority: {
        map: alarmShieldAuth,
        page: [alarmShieldAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/alarm-shield-edit/:id/:type',
    name: 'alarm-shield-edit',
    components: {
      noCache: AlarmShieldConfigSet
    },
    meta: {
      title: '编辑屏蔽',
      needBack: true,
      navId: 'alarm-shield',
      authority: {
        map: alarmShieldAuth,
        page: [alarmShieldAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/alarm-shield-detail/:id',
    name: 'alarm-shield-detail',
    props: true,
    components: {
      noCache: AlarmShieldDetail
    },
    beforeEnter(to, from, next) {
      if (!to.params.id) {
        next({ path: '/alarm-shield' })
      } else {
        to.meta.title = to.params.id || '告警详情'
        next()
      }
      next()
    },
    meta: {
      title: '告警详情',
      needBack: true,
      navId: 'alarm-shield',
      authority: {
        map: alarmShieldAuth,
        page: [alarmShieldAuth.VIEW_AUTH]
      }
    }
  }
] as RouteConfig[]
