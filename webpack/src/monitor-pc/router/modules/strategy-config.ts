/* eslint-disable max-len */
import * as ruleAuth from '../../pages/strategy-config/authority-map'
import { RouteConfig, Route } from 'vue-router'
const StrategyConfig = () => import(/* webpackChunkName: 'StrategyConfig' */'@page/strategy-config/strategy-config.vue')
const StrategyConfigSet = () => import(/* webpackChunkName: 'StrategyConfigSet' */'@page/strategy-config/strategy-config-set/strategy-config-set.vue')
const StrategyConfigDetail = () => import(/* webpackChunkName: 'StrategyConfigDetail' */'@page/strategy-config/strategy-config-detail/strategy-config-detail.vue')
// const StrategyConfigTarget = () => import(/* webpackChunkName: 'StrategyConfigTarget' */'@page/strategy-config/strategy-config-target/strategy-config-target.vue')
export default [
  {
    path: '/strategy-config',
    name: 'strategy-config',
    props: (route: Route) => ({ ...route.params, ...route.query }),
    component: StrategyConfig,
    meta: {
      title: '策略配置',
      navId: 'strategy-config',
      authority: {
        map: ruleAuth,
        page: ruleAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/strategy-config/edit/:id',
    name: 'strategy-config-edit',
    props: true,
    component: StrategyConfigSet,
    meta: {
      title: '编辑策略配置',
      navId: 'strategy-config',
      needBack: true,
      authority: {
        map: ruleAuth,
        page: ruleAuth.MANAGE_AUTH
      }
    }
  },
  {
    path: '/strategy-config/add',
    name: 'strategy-config-add',
    component: StrategyConfigSet,
    meta: {
      title: '新建策略配置',
      navId: 'strategy-config',
      needBack: true,
      authority: {
        map: ruleAuth,
        page: ruleAuth.MANAGE_AUTH
      }
    }
  },
  {
    path: '/strategy-config/detail/:id',
    name: 'strategy-config-detail',
    components: {
      noCache: StrategyConfigDetail
    },
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '策略详情'
      next()
    },
    meta: {
      title: '策略详情',
      navId: 'strategy-config',
      needBack: true,
      navClass: 'strategy-detail-nav',
      authority: {
        map: ruleAuth,
        page: ruleAuth.VIEW_AUTH
      }
    }
  }
] as RouteConfig[]
