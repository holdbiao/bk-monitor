import 'core-js/stable'
import 'regenerator-runtime/runtime'
import Vue from 'vue'
import './common/import-email-magicbox-ui'
import './static/assets/css/global.scss'
import './static/css/reset.scss'
import './static/css/global.scss'
import MonitorEcharts from '../monitor-ui/monitor-echarts/monitor-echarts-new.vue'
import moment from 'moment'
moment.locale('zh-cn')
Vue.prototype.$t = v => v
Vue.prototype.$tc = v => v
Vue.prototype.$moment = moment
window.Vue = Vue
window.moment = moment
Vue.component('MonitorEcharts', MonitorEcharts)
