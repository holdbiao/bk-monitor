/* eslint-disable max-len */
import * as pluginAuth from '../../pages/plugin-manager/authority-map'
import { RouteConfig } from 'vue-router'
const PluginManager = () => import(/* webpackChunkName: 'PluginManager' */'../../pages/plugin-manager/plugin-manager.vue')
const PluginInfo = () => import(/* webpackChunkName: 'PluginInfo' */'../../pages/plugin-manager/plugin-info/plugin-info.vue')
const PluginInstance = () => import(/* webpackChunkName: 'PluginInstance' */'../../pages/plugin-manager/plugin-instance/plugin-instance.vue')
const PluginSetmetric = () => import(/* webpackChunkName: 'PluginInstance' */'../../pages/plugin-manager/plugin-setmetric.vue')
export default [
  {
    path: '/plugin-manager',
    name: 'plugin-manager',
    component: PluginManager,
    meta: {
      title: '插件管理',
      navId: 'plugin-manager',
      authority: {
        map: pluginAuth,
        page: pluginAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/plugin/add',
    name: 'plugin-add',
    components: {
      default: null,
      noCache: PluginInstance
    },
    meta: {
      needBack: true,
      navId: 'plugin-manager',
      authority: {
        map: pluginAuth,
        page: pluginAuth.MANAGE_AUTH
      }
    }
  },
  {
    path: '/plugin/edit/:pluginId',
    name: 'plugin-edit',
    components: {
      default: null,
      noCache: PluginInstance
    },
    meta: {
      needBack: true,
      navId: 'plugin-manager',
      authority: {
        map: pluginAuth,
        page: pluginAuth.MANAGE_AUTH
      }
    }
  },
  {
    path: '/plugin/update',
    name: 'plugin-update',
    components: {
      default: null,
      noCache: PluginInstance
    },
    meta: {
      needBack: true,
      navId: 'plugin-manager'
    }
  },
  {
    path: '/plugin/detail/:pluginId',
    name: 'plugin-detail',
    props: true,
    components: {
      noCache: PluginInfo
    },
    meta: {
      needBack: true,
      navId: 'plugin-manager',
      navClass: 'plugin-detail-nav',
      authority: {
        map: pluginAuth,
        page: pluginAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/plugin/setmetric/:pluginId',
    name: 'plugin-setmetric',
    components: {
      noCache: PluginSetmetric
    },
    meta: {
      needBack: true,
      navId: 'plugin-manager',
      title: '设置指标&维度',
      authority: {
        map: pluginAuth,
        page: pluginAuth.MANAGE_AUTH
      }
    }
  }
] as RouteConfig[]
