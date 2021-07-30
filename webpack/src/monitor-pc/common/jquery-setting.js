window.jQuery = window.$

window.$.ajaxSetup({
  error(xhr, status, error) {
    console.info(xhr, status, error, '-----------', window.Vue.prototype.$bkMessage)
  }
})
