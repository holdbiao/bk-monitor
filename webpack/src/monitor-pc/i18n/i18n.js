import Vue from 'vue'
import VueI18n from 'vue-i18n'
import { getCookie } from '../../monitor-common/utils/utils'
import { locale, lang } from 'bk-magic-vue'
import chineseJson from '../lang/translate-zh.json'
import englishJson from '../lang/translate-en.json'
import moment from 'moment'
Vue.use(VueI18n)

let currentLang = getCookie('blueking_language') || 'zhCN'
if (currentLang === 'en') {
  currentLang = 'enUS'
  moment.locale('en')
} else {
  currentLang = 'zhCN'
  moment.locale('zh-cn')
}

const i18n = new VueI18n({
  locale: currentLang,
  fallbackLocale: 'zhCN',
  messages: {
    enUS: englishJson,
    zhCN: chineseJson
  }
})

locale.use(lang[currentLang])
window.i18n = i18n
export default i18n
