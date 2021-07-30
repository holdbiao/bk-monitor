import BarChartOption from './bar-chart-option'
import LineChartOption from './line-chart-option'
import PieChartOption from './pie-chart-option'
import MapChartOption from './echart-map-options'
import { IChartOptionPorps } from './type-interface'
export default class MonitorChartOption {
  public chartOptionInstance: any = null
  public constructor(props: IChartOptionPorps) {
    switch (props.chartType) {
      case 'bar':
        this.chartOptionInstance = new BarChartOption(props)
        break
      case 'pie':
        this.chartOptionInstance = new PieChartOption(props)
        break
      case 'map':
        this.chartOptionInstance = new MapChartOption(props)
        break
      case 'line':
      default:
        this.chartOptionInstance = new LineChartOption(props)
    }
  }
  public getOptions(data: any)  {
    return this.chartOptionInstance.getOptions(data)
  }
}
