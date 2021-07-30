/* eslint-disable no-param-reassign */
import Vue from 'vue'
import Loading from '../components/monitor-loading/monitor-loading.vue'
const MonitorLoading = Vue.extend(Loading)

const loadingDirective = {}
loadingDirective.install = (Vue) => {
  const toggleLoading = (el, options) => {
    if (!el.$vm) {
      el.$vm = el.instance.$mount()
      el.appendChild(el.$vm.$el)
    }
    if (options.isLoading) {
      Vue.nextTick(() => {
        el.$vm.visible = true
      })
    } else {
      el.$vm.visible = false
    }
    el.domInserted = true
  }
  Vue.directive('monitorLoading', {
    inserted(el, binding) {
      const data = Object.assign({}, binding.value, { visible: false })
      const instance = new MonitorLoading({ data })
      el.instance = instance
      binding.value && toggleLoading(el, binding.value)
    },

    update(el, binding) {
      toggleLoading(el, binding.value)
    },

    unbind(el) {
      if (el.domInserted) {
        el.mask
                && el.mask.parentNode
                && el.mask.parentNode.removeChild(el.mask)
        toggleLoading(el, { isLoading: false })
      }
      el.instance && el.instance.$destroy()
    }
  })
}

export default loadingDirective
