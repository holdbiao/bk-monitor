/* eslint-disable max-len */
import * as collectConfigAuth from '../../pages/collector-config/authority-map'
import { RouteConfig } from 'vue-router'
const CollectorConfig = () => import(/* webpackChunkName: 'CollectorConfig' */'@page/collector-config/collector-config.vue')
// const CollectorConfigView = () => import(/* webpackChunkName: 'CollectorConfigView' */'@page/collector-config/collector-view/collector-view.vue')
const CollectorConfigViewNew = () => import(/* webpackChunkName: 'CollectorConfigViewNew' */'@page/collector-config/collector-view/collector-view-new.vue')
const CollectorConfigAdd = () => import(/* webpackChunkName: 'CollectorConfigAdd' */'@page/collector-config/collector-add/collector-add.vue')
const CollectorConfigNode = () => import(/* webpackChunkName: 'CollectorConfigNode' */'@page/collector-config/collector-target-add-del/add-del.vue')
const CollectorConfigUpdate = () => import(/* webpackChunkName: 'CollectorConfigUpdate' */'@page/collector-config/collector-stop-start/stop-start-view.vue')
const CollectorConfigOperateDetail = () => import(/* webpackChunkName: 'CollectorConfigOperateDetail' */'@page/collector-config/collector-host-detail/collector-host-detail.vue')
export default [
  {
    path: '/collect-config',
    name: 'collect-config',
    component: CollectorConfig,
    meta: {
      title: '采集配置',
      navId: 'collect-config',
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.VIEW_AUTH]
      }
    }
  },
  //   {
  //     path: '/collect-config/view/:id',
  //     name: 'collect-config-view',
  //     props: true,
  //     components: {
  //       noCache: CollectorConfigView
  //     },
  //     beforeEnter(to, from, next) {
  //       to.meta.title = to.params.title || '检查视图'
  //       next()
  //     },
  //     meta: {
  //       title: '检查视图',
  //       navId: 'collect-config',
  //       needBack: true
  //     }
  //   },
  {
    path: '/collect-config/view/:id',
    name: 'collect-config-view',
    props: true,
    component: CollectorConfigViewNew,
    // components: {
    //   noCache: CollectorConfigViewNew
    // },
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '检查视图'
      next()
    },
    meta: {
      title: '检查视图',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.VIEW_AUTH]
      },
      customContent: true
    }
  },
  {
    path: '/collect-config/add',
    name: 'collect-config-add',
    props: true,
    components: {
      noCache: CollectorConfigAdd
    },
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '新建配置'
      next()
    },
    meta: {
      title: '新建配置',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/collect-config/edit/:id/:pluginId',
    name: 'collect-config-edit',
    props: true,
    components: {
      noCache: CollectorConfigAdd
    },
    beforeEnter(to, from, next) {
      to.meta.title = to.params.title || '编辑配置'
      next()
    },
    meta: {
      title: '编辑配置',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/collect-config/node',
    name: 'collect-config-node',
    props: true,
    components: {
      noCache: CollectorConfigNode
    },
    beforeEnter(to, from, next) {
      if (!to.params.data) {
        next({ path: '/collect-config' })
      } else {
        next()
      }
    },
    meta: {
      title: '增删目标',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/collect-config/update',
    name: 'collect-config-update',
    props: true,
    components: {
      noCache: CollectorConfigUpdate
    },
    beforeEnter(to, from, next) {
      if (!to.params.data) {
        next({ path: '/collect-config' })
      } else {
        to.meta.title = to.params.title || '启用采集配置'
        next()
      }
    },
    meta: {
      title: '启用采集配置',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/collect-config/operate-detail/:id',
    name: 'collect-config-operate-detail',
    props: true,
    components: {
      noCache: CollectorConfigOperateDetail
    },
    beforeEnter(to, from, next) {
      if (!to.params.id) {
        next({ path: '/collect-config' })
      } else {
        to.meta.title = to.params.title || '执行详情'
        next()
      }
      next()
    },
    meta: {
      title: '执行详情',
      navId: 'collect-config',
      needBack: true,
      authority: {
        map: collectConfigAuth,
        page: [collectConfigAuth.VIEW_AUTH]
      }
    }
  }
] as RouteConfig[]

