import { RouteConfig } from 'vue-router'
const Auth = () => import(/* webpackChunkName: 'Auth' */'@page/auth/auth.vue')
export default [
  {
    name: 'auth',
    path: '/auth',
    components: {
      noCache: Auth
    },
    meta: {
      title: '权限设置',
      navId: 'auth',
      authorityList: ['view_business']
    }
  }
] as RouteConfig[]
