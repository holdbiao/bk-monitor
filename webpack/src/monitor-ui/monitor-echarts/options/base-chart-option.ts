import moment from 'moment'
import { IChartOptionPorps, ChartType } from './type-interface'
export default class EchartsSeries {
  public  lineWidth = 1
  public chartType: ChartType
  public colors: string[] = []
  public showExtremum = false
  public chartOption = {}
  public constructor({ chartType, colors, showExtremum, chartOption, lineWidth }: IChartOptionPorps) {
    this.chartType = chartType
    this.colors = colors
    this.showExtremum = showExtremum
    this.chartOption = chartOption || {}
    this.lineWidth = lineWidth || 1
  }
  // 设置x轴label formatter方法
  public handleSetFormatterFunc(seriesData: any) {
    let formatterFunc = null
    // eslint-disable-next-line prefer-destructuring
    const firstItem = seriesData[0]
    const lastItem = seriesData[seriesData.length - 1]
    const isArray = Array.isArray(firstItem)
    const minX = isArray ? firstItem[0] : firstItem?.value[0]
    const maxX = isArray ? lastItem[0] : lastItem?.value[0]
    minX && maxX && (formatterFunc = (v: any) => {
      const duration = moment.duration(moment(maxX).diff(moment(minX))).asSeconds()
      if (duration < 60 * 60 * 24) {
        return moment(v).format('HH:mm:ss')
          .replace(/:00$/, '')
      } if (duration < 60 * 60 * 24 * 2) {
        return moment(v).format('HH:mm')
      } if (duration < 60 * 60 * 24 * 8) {
        return moment(v).format('MM-DD HH:mm')
      } if (duration <= 60 * 60 * 24 * 30 * 12) {
        return moment(v).format('MM-DD')
      }
      return moment(v).format('YYYY-MM-DD')
    })
    return formatterFunc
  }
  public overwriteMerge(destinationArray: any, sourceArray: any) {
    return sourceArray
  }
  public handleYxisLabelFormatter(num: number): string {
    const si = [
      { value: 1, symbol: '' },
      { value: 1E3, symbol: 'K' },
      { value: 1E6, symbol: 'M' },
      { value: 1E9, symbol: 'G' },
      { value: 1E12, symbol: 'T' },
      { value: 1E15, symbol: 'P' },
      { value: 1E18, symbol: 'E' }
    ]
    const rx = /\.0+$|(\.[0-9]*[1-9])0+$/
    let i
    for (i = si.length - 1; i > 0; i--) {
      if (num >= si[i].value) {
        break
      }
    }
    return (num / si[i].value).toFixed(3).replace(rx, '$1') + si[i].symbol
  }
}
