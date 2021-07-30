/* eslint-disable max-len */
import * as eventCenterAuth from '../../pages/event-center/authority-map'
import { RouteConfig } from 'vue-router'
const EventCenter = () => import(/* webpackChunkName: 'EventCenter' */'@page/event-center/event-center.vue')
const EventCenterDetail = () => import(/* webpackChunkName: 'EventCenterDetail' */'@page/event-center/event-center-detail/event-center-detail.vue')
const isSpecEvent = location.search.indexOf('specEvent') > -1
export default [
  {
    path: '/event-center',
    name: 'event-center',
    component: EventCenter,
    meta: Object.assign({}, {
      title: '事件中心',
      navId: 'event-center',
      authority: {
        map: eventCenterAuth
      }
    }, !isSpecEvent ? {
      authorityList: ['view_event'],
      authority: {
        page: eventCenterAuth.VIEW_AUTH
      } } : {})
  },
  {
    path: '/event-center/detail/:id',
    name: 'event-center-detail',
    props: true,
    beforeEnter(to, from, next) {
      !!to.params.id ?  next() : next(false)
    },
    component: EventCenterDetail,
    meta: Object.assign({}, {
      title: '告警详情',
      navId: 'event-center',
      needBack: true,
      navClass: 'event-center-nav',
      authority: {
        map: eventCenterAuth
      }
    }, !isSpecEvent ? {
      authority: {
        page: eventCenterAuth.VIEW_AUTH
      }
    } : {})
  }
] as RouteConfig[]
