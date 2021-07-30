import { Component, Vue } from 'vue-property-decorator'

@Component
export default class collapseMixin extends Vue {
  public beforeEnter(el) {
    el.classList.add('collapse-transition')
    el.style.height = '0'
  }
  public enter(el) {
    el.dataset.oldOverflow = el.style.overflow
    if (el.scrollHeight !== 0) {
      el.style.height = `${el.scrollHeight}px`
      setTimeout(() => {
        el.style.height = ''
      }, 300)
    } else {
      el.style.height = ''
    }
    el.style.overflow = 'hidden'
  }

  public afterEnter(el) {
    el.classList.remove('collapse-transition')
    el.style.height = ''
    el.style.overflow = el.dataset.oldOverflow
  }

  public beforeLeave(el) {
    el.dataset.oldOverflow = el.style.overflow
    el.style.height = `${el.scrollHeight}px`
    el.style.overflow = 'hidden'
  }

  public leave(el) {
    if (el.scrollHeight !== 0) {
      el.classList.add('collapse-transition')
      el.style.height = 0
    }
  }

  public afterLeave(el) {
    el.classList.remove('collapse-transition')
    el.style.height = ''
    el.style.overflow = el.dataset.oldOverflow
  }
}
