import { RouteConfig } from 'vue-router'
const NoBusiness = () => import(/* webpackChunkName: 'no-business' */'@page/no-business/no-business.vue')
export default [
  {
    name: 'no-business',
    path: '/no-business',
    components: {
      noCache: NoBusiness
    },
    meta: {
      title: '无业务',
      navId: ''
    }
  }
] as RouteConfig[]
