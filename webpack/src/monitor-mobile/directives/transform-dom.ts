/* eslint-disable indent */
import { DirectiveOptions } from 'vue'
import { DirectiveBinding } from 'vue/types/options'

function getTarget(selector: string) {
  let target = document.querySelector(selector)
  if (!target) {
    target = document.body
  }
  return target
}

const transferDom: DirectiveOptions = {
  inserted(el: HTMLElement, binding: DirectiveBinding) {
    el.className = el.className ? `${el.className} v-transfer-dom` : 'v-transfer-dom'
    const { parentNode } = el
    const targetNode = getTarget(binding.value)
    if (!parentNode || !targetNode) return

    const comment = document.createComment('')
    parentNode.replaceChild(comment, el) // moving out, el is no longer in the document
    targetNode.appendChild(el) // moving into new place
  },
  unbind(el: HTMLElement) {
    el.className = el.className.replace('v-transfer-dom', '')
  }
}

export default transferDom
