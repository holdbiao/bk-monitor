// import * as alarmShieldAuth from '../../pages/alarm-shield/authority-map'
import { RouteConfig } from 'vue-router'
const EmailSubscriptions = () => import(
  /* webpackChunkName: 'EmailSubscriptions' */'../../pages/email-subscriptions/email-subscriptions.vue')
const EmailSubscriptionsSet = () => import(
  /* webpackChunkName: 'EmailSubscriptionsSet' */'../../pages/email-subscriptions/email-subscriptions-set.vue')

export default [
  {
    path: '/email-subscriptions',
    name: 'email-subscriptions',
    components: {
      noCache: EmailSubscriptions
    },
    meta: {
      title: '邮件订阅',
      navId: 'email-subscriptions'
    }
  },
  {
    path: '/email-subscriptions/add',
    name: 'email-subscriptions-add',
    components: {
      noCache: EmailSubscriptionsSet
    },
    meta: {
      title: '新建订阅',
      navId: 'email-subscriptions-add',
      needBack: true
    }
  },
  {
    path: '/email-subscriptions/edit/:id',
    name: 'email-subscriptions-edit',
    components: {
      noCache: EmailSubscriptionsSet
    },
    props: true,
    meta: {
      title: '编辑订阅',
      navId: 'email-subscriptions-edit',
      needBack: true
    }
  }
] as RouteConfig[]
