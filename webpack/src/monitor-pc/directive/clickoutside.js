/* eslint-disable no-param-reassign */
const nodeList = []
const clickctx = '$clickoutsideCtx'
let beginClick // 确保鼠标按下和松开时是同一个目标

document.addEventListener('mousedown', event => (beginClick = event))

document.addEventListener('mouseup', (event) => {
  nodeList.forEach((node) => {
    node[clickctx].clickoutsideHandler(event, beginClick)
  })
})

export default {
  bind(el, binding, vnode) {
    const id = nodeList.push(el) - 1
    const clickoutsideHandler = (mouseup = {}, mousedown = {}) => {
      if (!vnode.context // 点击在 vue 实例之外的 DOM 上
                || !mouseup.target
                || !mousedown.target
                || el.contains(mouseup.target) // 鼠标按下时的 DOM 节点是当前展开的组件的子元素
                || el.contains(mousedown.target) // 鼠标松开时的 DOM 节点是当前展开的组件的子元素
                || el === mouseup.target // 鼠标松开时的 DOM 节点是当前展开的组件的根元素
                || (vnode.context.popup // 当前点击元素是有弹出层的
                    && (
                      vnode.context.popup.contains(mouseup.target) // 鼠标按下时的 DOM 节点是当前有弹出层元素的子节点
                        || vnode.context.popup.contains(mousedown.target) // 鼠标松开时的 DOM 节点是当前有弹出层元素的子节点
                    )
                )
      ) {
        return
      }

      if (binding.expression // 传入了指令绑定的表达式
                && el[clickctx].callbackName // 当前元素的 clickoutside 对象中有回调函数名
                && vnode.context[el[clickctx].callbackName] // vnode 中存在回调函数
      ) {
        vnode.context[el[clickctx].callbackName](mousedown, mouseup, el)
      } else {
        el[clickctx].bindingFn && el[clickctx].bindingFn(mousedown, mouseup, el)
      }
    }

    el[clickctx] = {
      id,
      clickoutsideHandler,
      callbackName: binding.expression,
      callbackFn: binding.value
    }
  },
  update(el, binding) {
    el[clickctx].callbackName = binding.expression
    el[clickctx].callbackFn = binding.value
  },
  unbind(el) {
    for (let i = 0, len = nodeList.length; i < len; i++) {
      if (nodeList[i][clickctx].id === el[clickctx].id) {
        nodeList.splice(i, 1)
        break
      }
    }
  }
}
