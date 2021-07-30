import { ILegendItem, IChartInstance } from './type-interface'
import MonitorBaseSeries from './base-chart-option'
import deepMerge from 'deepmerge'
import { pieOptions } from './echart-options-config'
export default class MonitorPieSeries extends  MonitorBaseSeries implements IChartInstance {
  public defaultOption: any
  public constructor(props: any) {
    super(props)
    this.defaultOption = deepMerge(deepMerge(pieOptions, {
      color: this.colors
    }, { arrayMerge: this.overwriteMerge }), this.chartOption, { arrayMerge: this.overwriteMerge })
  }
  public getOptions(data: any, otherOptions = {}) {
    let { series } = data || {}
    series = deepMerge([], series)
    const hasSeries = series && series.length > 0
    const legendData: any = []
    const options =  {
      series: hasSeries ? series.map((item: any, index: number) => {
        item.data.forEach((seriesItem: any) => {
          const legendItem: ILegendItem = {
            name: '',
            max: 0,
            min: 0,
            avg: 0,
            total: 0,
            color: this.colors[index % this.colors.length],
            show: true
          }
          if (seriesItem?.name) {
            const curValue = +seriesItem.value
            legendItem.max = Math.max(legendItem.max, curValue)
            legendItem.min = Math.min(+legendItem.min, curValue)
            legendItem.total = (legendItem.total + curValue)
            legendItem.name = seriesItem.name
          }
          legendItem.avg = +(legendItem.total / 1).toFixed(2)
          legendItem.total = +(legendItem.total).toFixed(2)
          legendItem.name && legendData.push(legendItem)
        })
        const seriesItem = {
          radius: ['50%', '70%'],
          avoidLabelOverlap: false,
          label: {
            show: false,
            position: 'center'
          },
          labelLine: {
            show: false
          },
          type: this.chartType,
          ...item
        }
        return seriesItem
      }) : []
    }
    return {
      options: deepMerge(deepMerge(
        this.defaultOption, otherOptions,
        { arrayMerge: this.overwriteMerge }
      ), options, { arrayMerge: this.overwriteMerge }),
      legendData
    }
  }
}
