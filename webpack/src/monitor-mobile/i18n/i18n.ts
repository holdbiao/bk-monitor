import Vue from 'vue'
import VueI18n from 'vue-i18n'
import { getCookie } from '../../monitor-common/utils/utils'
import chineseJson from '../lang/zh-cn.json'
import englishJson from '../lang/en.json'
import enUS from 'vant/lib/locale/lang/en-US'
Vue.use(VueI18n)
const i18n = new VueI18n({
  locale: getCookie('blueking_language') || 'zh-cn',
  fallbackLocale: 'zh-cn',
  messages: {
    en: Object.assign({}, enUS, englishJson),
    'zh-cn': Object.assign({}, chineseJson)
  }
})
export default i18n
