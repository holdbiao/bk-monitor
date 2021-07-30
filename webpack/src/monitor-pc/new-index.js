/* eslint-disable max-len */
/* eslint-disable no-param-reassign */
// @ts-ignore
import './public-path'
import './tsx.ts'
import Vue from 'vue'
import './common/import-magicbox-ui'
import '../monitor-static/icons/monitor-icons.css'
import './static/css/reset.scss'
import './static/css/global.scss'
import router from './router/router'
import store from './store/store'
import Api from '../monitor-api/api'
import Axios from '../monitor-api/axios/axios'
import App from './pages/monitor-navigation/monitor-navigation.vue'
import i18n from './i18n/i18n'
import { getUrlParam } from '../monitor-common/utils/utils'
import * as serviceWorker from '../monitor-common/service-worker/service-wroker'
import { handleSetPageShow } from './router/router-config'
import './directive/index'
import './common/global'
import '../monitor-static/svg-icons'
const hasRouteHash = getUrlParam('routeHash')
// 邮件订阅相关页面可无权限无业务进入
const isEmailSubscriptions = location.hash.indexOf('email-subscriptions') > -1
let bizId = +getUrlParam('bizId')
// 通知人可无权限进入事件详情
if (hasRouteHash) {
  const isSpecEvent = hasRouteHash.indexOf('event-center') > -1
  location.href = `${location.origin}${location.pathname}?bizId=${bizId}${isSpecEvent ? '&specEvent=1' : ''}${hasRouteHash.match(/^#/) ? hasRouteHash : `#/${hasRouteHash}`}`
}
// 设置全局业务ID
const setGlobalBizId = () => {
  const isSpicialEvent = !!getUrlParam('specEvent')
  const isNoBusiness = location.hash.indexOf('no-business') > -1
  const localBizId = localStorage.getItem('__biz_id__')
  const bizList = window.cc_biz_list || []
  const authList = bizList.filter(item => !item.is_demo)
  const hasAuth = id => authList.some(item => +id === +item.id)
  const setBizId = (id) => {
    window.cc_biz_id = +id
    window.bk_biz_id = +id
    + id > -1 && localStorage.setItem('__biz_id__', +id)
  }
  if (!isSpicialEvent && !hasRouteHash && !isEmailSubscriptions) {
    const isDemoBizId = bizList.some(item => +item.id === +bizId && item.is_demo)
    if (!isDemoBizId && (!bizId || !hasAuth(bizId))) {
      if (localBizId && hasAuth(localBizId)) {
        bizId = +localBizId
        location.href = `${location.origin}${location.pathname}?bizId=${bizId}#/`
      } else if (authList.length) {
        bizId = +authList[0].id
        location.href = `${location.origin}${location.pathname}?bizId=${bizId}#/`
      } else if (!bizId) {
        bizId = -1
        if (!isNoBusiness) location.href = `${location.origin}${location.pathname}#/no-business`
      } else  {
        const isDemoBizId = bizList.some(item => +item.id === +bizId && item.is_demo)
        if (!isDemoBizId) {
          location.href = `${location.origin}${location.pathname}?bizId=${bizId}#/no-business`
        } else if (isNoBusiness) {
          location.href = `${location.origin}${location.pathname}?bizId=${bizId}#/`
        }
      }
    } else if (isNoBusiness) {
      location.href = `${location.origin}${location.pathname}?bizId=${bizId}#/`
    }
  } else if (!bizId) {
    bizId = -1
  }
  setBizId(bizId)
  return bizId
}
// 全局图表数量变量
window.slimit = 500
if (process.env.NODE_ENV === 'development') {
  window.site_url = '/'
  Api.commons.getContext().then((data) => {
    Object.keys(data).forEach((key) => {
      window[key.toLocaleLowerCase()] = data[key]
    })
    data.IS_SUPERUSER = data.IS_SUPERUSER === 'true'
    data.ENABLE_MESSAGE_QUEUE = data.ENABLE_MESSAGE_QUEUE === 'true'
    window.enable_message_queue = data.ENABLE_MESSAGE_QUEUE
    window.is_superuser = data.IS_SUPERUSER
    window.cc_biz_list = window.bk_biz_list
    window.job_url = window.bk_job_url
    window.username = window.uin
    const bizId = setGlobalBizId()
    store.commit('app/SET_APP_STATE', {
      userName: data.UIN,
      isSuperUser: data.IS_SUPERUSER,
      bizId,
      bizList: data.BK_BIZ_LIST,
      csrfCookieName: data.CSRF_COOKIE_NAME,
      enableMessageQueue: data.ENABLE_MESSAGE_QUEUE,
      siteUrl: data.SITE_URL,
      messageQueueDSN: data.MESSAGE_QUEUE_DSN,
      maxAvailableDurationLimit: data.MAX_AVAILABLE_DURATION_LIMIT,
      upgradeAllowed: data.UPGRADE_ALLOWED,
      cmdbUrl: data.BK_CC_URL,
      bkLogSearchUrl: data.BKLOGSEARCH_HOST,
      bkUrl: data.BK_URL,
      bkNodemanHost: data.BK_NODEMAN_HOST,
      collectingConfigFileMaxSize: data.COLLECTING_CONFIG_FILE_MAXSIZE,
      enable_cmdb_level: true
    })
    handleSetPageShow('upgrade-config', data.UPGRADE_ALLOWED)
    handleSetPageShow('email-subscriptions', +data.MAIL_REPORT_BIZ > 0)
    // eslint-disable-next-line no-new
    new Vue({
      el: '#app',
      router,
      store,
      i18n,
      render: h => h(App)
    })
    Vue.prototype.$bus = new Vue()
    Vue.prototype.$bus.$originRouter = router
    Vue.prototype.$platform = window.platform
    Vue.prototype.$api = Api
    Vue.prototype.$http = Axios
    window.Vue = Vue
    serviceWorker.unregister()
  })
} else if (!hasRouteHash) {
  const pathname = `${window.location.pathname}`
  if (pathname !== window.site_url) {
    location.pathname = window.site_url
  } else {
    setGlobalBizId()
    store.commit('app/SET_APP_STATE', {
      userName: window.user_name,
      isSuperUser: window.userInfo.isSuperuser,
      bizId: window.cc_biz_id,
      bizList: window.cc_biz_list,
      csrfCookieName: window.csrf_cookie_name || [],
      siteUrl: window.site_url,
      enableMessageQueue: window.enable_message_queue,
      messageQueueDSN: window.message_queue_dsn,
      maxAvailableDurationLimit: window.max_available_duration_limit,
      upgradeAllowed: window.upgrade_allowed,
      cmdbUrl: window.cmdb_url,
      bkLogSearchUrl: window.bk_log_search_url,
      bkUrl: window.bk_url,
      bkNodemanHost: window.bk_nodeman_host,
      collectingConfigFileMaxSize: window.collecting_config_file_maxsize,
      enable_cmdb_level: !!window.enable_cmdb_level
    })
    handleSetPageShow('upgrade-config', window.upgrade_allowed)
    handleSetPageShow('email-subscriptions', +window.mail_report_biz > 0)
    // eslint-disable-next-line no-new
    new Vue({
      el: '#app',
      router,
      store,
      i18n,
      render: h => h(App)
    })
    Vue.prototype.$bus = new Vue()
    Vue.prototype.$platform = window.platform
    Vue.prototype.$api = Api
    Vue.prototype.$http = Axios
    serviceWorker.register()
  }
}
