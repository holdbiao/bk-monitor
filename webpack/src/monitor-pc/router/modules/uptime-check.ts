/* eslint-disable max-len */
import * as uptimeAuth from '../../pages/uptime-check/authority-map'
import { RouteConfig } from 'vue-router'
const UptimeCheckDetail = () => import(/* webpackChunkName: 'UptimeCheckDetail' */'../../pages/uptime-check/uptime-check-task/uptime-check-detail/uptime-check-detail.vue')
const UptimeCheckForm = () => import(/* webpackChunkName: 'UptimeCheckForm' */'../../pages/uptime-check/uptime-check-task/uptime-check-form/task-form.vue')
const UptimeCheckNodeEdit = () => import(/* webpackChunkName: 'UptimeCheckNodeEdit' */'../../pages/uptime-check/uptime-check-nodes/uptime-check-node-edit.vue')
const UptimeCheck = () => import(/* webpackChunkName: 'UptimeCheck' */'../../pages/uptime-check/uptime-check.vue')
export default [
  // {
  //   path: '/uptime-check-task',
  //   name: 'uptime-check-task',
  //   component: UptimeCheckTask,
  //   meta: {
  //     title: '拨测任务',
  //     navId: 'uptime-check-task'
  //   }
  // },
  {
    path: '/uptime-check/task-detail/:taskId',
    name: 'uptime-check-task-detail',
    props: true,
    components: {
      noCache: UptimeCheckDetail
    },
    meta: {
      needBack: true,
      title: '任务详情',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.VIEW_AUTH]
      }
    }
  },
  {
    path: '/uptime-check/group-detail/:groupId',
    name: 'uptime-check-group-detail',
    props: true,
    components: {
      noCache: UptimeCheckDetail
    },
    meta: {
      needBack: true,
      title: '任务详情',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.VIEW_AUTH]
      }
    }
  },
  {
    path: '/uptime-check/task-add',
    name: 'uptime-check-task-add',
    component: UptimeCheckForm,
    meta: {
      needBack: true,
      title: '新建拨测任务',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/uptime-check/task-edit/:id',
    name: 'uptime-check-task-edit',
    props: true,
    components: {
      noCache: UptimeCheckForm
    },
    meta: {
      needBack: true,
      title: '编辑拨测任务',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.VIEW_AUTH]
      }
    }
  },
  // {
  //   path: '/uptime-check-node',
  //   name: 'uptime-check-node',
  //   component: UptimeCheckNodes,
  //   meta: {
  //     title: '拨测节点',
  //     navId: 'uptime-check-node'
  //   }
  // },
  {
    path: '/uptime-check/node-add',
    name: 'uptime-check-node-add',
    components: {
      noCache: UptimeCheckNodeEdit
    },
    meta: {
      needBack: true,
      title: '新建拨测节点',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/uptime-check/node-edit/:id',
    name: 'uptime-check-node-edit',
    components: {
      noCache: UptimeCheckNodeEdit
    },
    meta: {
      needBack: true,
      title: '编辑拨测节点',
      navId: 'uptime-check',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.MANAGE_AUTH]
      }
    }
  },
  {
    path: '/uptime-check/:id?',
    name: 'uptime-check',
    component: UptimeCheck,
    props: true,
    meta: {
      title: '服务拨测',
      navId: 'uptime-check',
      navClass: 'uptime-check-nav',
      authority: {
        map: uptimeAuth,
        page: [uptimeAuth.VIEW_AUTH]
      }
    }
  }
] as RouteConfig[]
