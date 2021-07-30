type InTopOrBottom = boolean | undefined
export default class ChartInView {
  public chartInTop: InTopOrBottom
  public chartInBottom: InTopOrBottom
  public timer: any
  public rect: DOMRect
  public constructor(inTop: InTopOrBottom, inBottom: InTopOrBottom, rect: DOMRect) {
    this.setCharInView(inTop, inBottom, rect)
  }
  public setCharInView(inTop: InTopOrBottom, inBottom: InTopOrBottom, rect: DOMRect) {
    this.chartInTop = inTop
    this.chartInBottom = inBottom
    this.rect = rect
    this.timer && clearTimeout(this.timer)
    this.timer = setTimeout(() => {
      this.chartInTop = undefined
      this.chartInBottom = undefined
    }, 5000)
  }
}
