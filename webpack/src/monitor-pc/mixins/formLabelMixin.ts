import { Vue, Component } from 'vue-property-decorator'

interface IFormLabelConfig {
  el?: HTMLElement
  safePadding?: number
  labelClass?: string
}

@Component
export default class formLabelMixin extends Vue {
  public maxFormLabelWidth = 120

  public initFormLabelWidth(config: IFormLabelConfig = {}) {
    const { el = this.$el, safePadding = 0, labelClass = '.item-label' } = config
    if (!el || this.$i18n.locale === 'zhCN') return
    let max = 0
    let maxTextLabelNode = null
    const $labelEleList = el.querySelectorAll<HTMLElement>(labelClass)
    $labelEleList.forEach((item) => {
      const text = item.innerText
      if (text.length > max) {
        maxTextLabelNode = item
      }
      max = Math.max(max, text.length)
    })
    if (!maxTextLabelNode) return

    const cloneNode = maxTextLabelNode.cloneNode(true)
    const newNode = document.body.appendChild(cloneNode) as HTMLElement
    newNode.style.cssText = 'display: inline-block; font-size: 14px; visibility: hidden;'
    let { width } = newNode.getBoundingClientRect()
    document.body.removeChild(newNode)

    if (width >= this.maxFormLabelWidth) {
      width = this.maxFormLabelWidth
    }
    width = Math.ceil(width + safePadding)

    this.setFormLabelWidth($labelEleList, width)
    return width
  }

  public setFormLabelWidth($labelEleList: NodeListOf<HTMLElement>, width) {
    $labelEleList.forEach((item) => {
      item.style.width = `${width}px`
      item.style.flexBasis = `${width}px`
    })
  }
}
