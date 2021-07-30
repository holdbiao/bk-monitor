/* eslint-disable max-len */
import * as serviceClassifyAuth from '../../pages/service-classify/authority-map'
import { RouteConfig } from 'vue-router'
const ServiceClassify = () => import(/* webpackChunkName: 'ServiceClassify' */'@page/service-classify/service-classify.vue')

export default [
  {
    path: '/service-classify',
    name: 'service-classify',
    components: {
      noCache: ServiceClassify
    },
    meta: {
      title: '服务分类',
      navId: 'service-classify',
      authority: {
        map: serviceClassifyAuth,
        page: serviceClassifyAuth.VIEW_AUTH
      }
    }
  }
] as RouteConfig[]
