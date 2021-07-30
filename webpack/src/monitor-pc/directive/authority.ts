import { DirectiveBinding } from 'vue/types/options'
import { VueConstructor } from 'vue'

interface IElement extends HTMLElement {
  [prop: string]: any
}
interface IOptions {
  active: boolean
  offset: number[]
  cls: string
}

const DEFAULT_OPTIONS: IOptions = {
  active: true,
  offset: [12, 0],
  cls: 'cursor-element'
}

function init(el: IElement, options: IOptions) {
  el.mouseEnterHandler = function () {
    const element = document.createElement('div')
    element.id = 'directive-ele'
    element.style.position = 'absolute'
    element.style.zIndex = '2501'
    el.element = element
    document.body.appendChild(element)

    element.classList.add(options.cls || DEFAULT_OPTIONS.cls)
    el.addEventListener('mousemove', el.mouseMoveHandler)
  }
  el.mouseMoveHandler = function (event: MouseEvent) {
    const { pageX, pageY } = event
    const elLeft = pageX + DEFAULT_OPTIONS.offset[0]
    const elTop = pageY + DEFAULT_OPTIONS.offset[1]
    el.element.style.left = `${elLeft}px`
    el.element.style.top = `${elTop}px`
  }
  el.mouseLeaveHandler = function () {
    el.element && el.element.remove()
    el.element = null
    el.removeEventListener('mousemove', el.mouseMoveHandler)
  }
  if (options.active) {
    el.addEventListener('mouseenter', el.mouseEnterHandler)
    el.addEventListener('mouseleave', el.mouseLeaveHandler)
  }
}

function destroy(el: IElement) {
  el.element && el.element.remove()
  el.element = null
  el.removeEventListener('mouseenter', el.mouseEnterHandler)
  el.removeEventListener('mousemove', el.mouseMoveHandler)
  el.removeEventListener('mouseleave', el.mouseLeaveHandler)
}


export default class AuthorityDirective {
  public static install(Vue: VueConstructor) {
    Vue.directive('authority', {
      bind(el: IElement, binding: DirectiveBinding) {
        const options: IOptions = Object.assign({}, DEFAULT_OPTIONS, binding.value)
        init(el, options)
      },
      update(el: IElement, binding: DirectiveBinding) {
        const options: IOptions = Object.assign({}, DEFAULT_OPTIONS, binding.value)
        destroy(el)
        init(el, options)
      },
      unbind(el: IElement) {
        destroy(el)
      }
    })
  }
}
