/* eslint-disable no-underscore-dangle */
/* eslint-disable no-param-reassign */
/* eslint-disable @typescript-eslint/no-require-imports */
const Clipboard = require('clipboard/dist/clipboard.min.js') // FIXME: workaround for browserify

const VueClipboardConfig = {
  autoSetContainer: false,
  appendToBody: true // This fixes IE, see #50
}

const VueClipboard = {
  install(Vue) {
    Vue.prototype.$clipboardConfig = VueClipboardConfig
    Vue.prototype.$copyText = function (text, container) {
      return new Promise(((resolve, reject) => {
        const fakeElement = document.createElement('button')
        const clipboard = new Clipboard(fakeElement, {
          text() {
            return text
          },
          action() {
            return 'copy'
          },
          container: typeof container === 'object' ? container : document.body
        })
        clipboard.on('success', (e) => {
          clipboard.destroy()
          resolve(e)
        })
        clipboard.on('error', (e) => {
          clipboard.destroy()
          reject(e)
        })
        if (VueClipboardConfig.appendToBody) document.body.appendChild(fakeElement)
        fakeElement.click()
        if (VueClipboardConfig.appendToBody) document.body.removeChild(fakeElement)
      }))
    }

    Vue.directive('clipboard', {
      bind(el, binding) {
        if (binding.arg === 'success') {
          el._vClipboard_success = binding.value
        } else if (binding.arg === 'error') {
          el._vClipboard_error = binding.value
        } else {
          const clipboard = new Clipboard(el, {
            text() {
              return binding.value
            },
            action() {
              return binding.arg === 'cut' ? 'cut' : 'copy'
            },
            container: VueClipboardConfig.autoSetContainer ? el : undefined
          })
          clipboard.on('success', (e) => {
            const callback = el._vClipboard_success
            callback?.(e)
          })
          clipboard.on('error', (e) => {
            const callback = el._vClipboard_error
            callback?.(e)
          })
          el._vClipboard = clipboard
        }
      },
      update(el, binding) {
        if (binding.arg === 'success') {
          el._vClipboard_success = binding.value
        } else if (binding.arg === 'error') {
          el._vClipboard_error = binding.value
        } else {
          el._vClipboard.text = function () {
            return binding.value
          }
          el._vClipboard.action = function () {
            return binding.arg === 'cut' ? 'cut' : 'copy'
          }
        }
      },
      unbind(el, binding) {
        if (binding.arg === 'success') {
          delete el._vClipboard_success
        } else if (binding.arg === 'error') {
          delete el._vClipboard_error
        } else {
          el._vClipboard.destroy()
          delete el._vClipboard
        }
      }
    })
  },
  config: VueClipboardConfig
}

export default VueClipboard
