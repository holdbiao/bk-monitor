/* eslint-disable import/prefer-default-export */
import Vue from 'vue'

export const bkMessage = (message, theme = 'error') => Vue.prototype.$bkMessage({
  message,
  theme,
  ellipsisLine: 0
})

export const authorityStore = () => Vue.prototype.$authorityStore
