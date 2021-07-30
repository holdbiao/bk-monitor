/* eslint-disable max-len */
import * as customAuth from '../../pages/custom-escalation/authority-map'
import { RouteConfig } from 'vue-router'
const CustomEscalation = () => import(/* webpackChunkName: 'CustomEscalation' */'@page/custom-escalation/custom-escalation.vue')
const CustomEscalationSet = () => import(/* webpackChunkName: 'CustomEscalationAdd' */'@page/custom-escalation/custom-escalation-set.vue')
const CustomEscalationDetail = () => import(/* webpackChunkName: 'CustomEscalationDetail' */ '@page/custom-escalation/custom-escalation-detail.vue')
const CustomEscalationView = () => import(/* webpackChunkName: 'CustomEscalationView' */ '@page/custom-escalation/custom-view.vue')
export default [
  {
    path: '/custom-escalation',
    name: 'custom-escalation',
    component: CustomEscalation,
    meta: {
      title: '自定义上报',
      navId: 'custom-escalation',
      navClass: 'escalation-content',
      authority: {
        map: customAuth,
        page: [customAuth.VIEW_CUSTOM_EVENT, customAuth.VIEW_CUSTOM_METRIC]
      }
    }
  },
  {
    path: '/custom-escalation-set/event',
    name: 'custom-set-event',
    props: {
      noCache: true
    },
    components: {
      noCache: CustomEscalationSet
    },
    meta: {
      title: '新建自定义事件',
      navId: 'custom-escalation',
      needBack: true,
      authority: {
        map: customAuth,
        page: customAuth.MANAGE_CUSTOM_EVENT
      }
    }
  },
  {
    path: '/custom-escalation-set/timeseries',
    name: 'custom-set-timeseries',
    props: {
      noCache: true
    },
    components: {
      noCache: CustomEscalationSet
    },
    meta: {
      title: '新建自定义指标',
      navId: 'custom-escalation',
      needBack: true,
      authority: {
        map: customAuth,
        page: customAuth.MANAGE_CUSTOM_METRIC
      }
    }
  },
  {
    path: '/custom-escalation-detail/event/:id',
    name: 'custom-detail-event',
    props: {
      noCache: true
    },
    components: {
      noCache: CustomEscalationDetail
    },
    meta: {
      title: '自定义详情',
      navId: 'custom-escalation',
      needBack: true,
      authority: {
        map: customAuth,
        page: customAuth.VIEW_CUSTOM_EVENT
      }
    }
  },
  {
    path: '/custom-escalation-detail/timeseries/:id',
    name: 'custom-detail-timeseries',
    props: {
      noCache: true
    },
    components: {
      noCache: CustomEscalationDetail
    },
    meta: {
      title: '自定义详情',
      navId: 'custom-escalation',
      needBack: true,
      authority: {
        map: customAuth,
        page: customAuth.VIEW_CUSTOM_METRIC
      }
    }
  },
  {
    path: '/custom-escalation-view/:id',
    name: 'custom-escalation-view',
    props: true,
    component: CustomEscalationView,
    meta: {
      title: '检查视图',
      navId: 'custom-escalation',
      needBack: true,
      customContent: true,
      authority: {
        map: customAuth,
        page: customAuth.VIEW_CUSTOM_METRIC
      }
    }
  }
] as RouteConfig[]
