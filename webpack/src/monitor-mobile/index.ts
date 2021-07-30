/* eslint-disable no-new */
/* eslint-disable new-cap */
/* eslint-disable @typescript-eslint/camelcase */
import './public-path.ts'
import Vue from 'vue'
import { getUrlParam } from '../monitor-common/utils/utils'
import router from './router/router'
import store from './store/store'
import i18n from './i18n/i18n'
import App from './pages/app.vue'
import * as serviceWorker from '../monitor-common/service-worker/service-wroker'
import '../monitor-static/icons/monitor-icons.css'
import 'vant/lib/icon/local.css'
import './static/scss/global.scss'
import 'vant/lib/index.css'
import { Notify } from 'vant'
interface IMessageParam {message: string; theme: 'primary' | 'success' | 'danger' | 'warning' | 'error'}
Vue.config.devtools = process.env.NODE_ENV === 'development'
const bizId = getUrlParam('bizId')
const enableConsole = getUrlParam('console')
window.cc_biz_id = bizId
if (process.env.NODE_ENV !== 'production') {
  window.site_url = '/weixin/'
}
enableConsole && import('vconsole').then((module) => {
  new module.default()
})
Vue.prototype.$bkMessage = (params: IMessageParam) => {
  Notify({
    type: params.theme === 'error' ? 'danger' : params.theme,
    message: params.message
  })
}
window.i18n = i18n
store.commit('app/SET_APP_DATA', {
  bizId,
  collectId: getUrlParam('collectId')
})
// eslint-disable-next-line no-new
new Vue({
  el: '#app',
  router,
  store,
  i18n,
  render: h => h(App)
})
Vue.prototype.$bus = new Vue()
process.env.NODE_ENV === 'production' ? serviceWorker.register() : serviceWorker.unregister()
