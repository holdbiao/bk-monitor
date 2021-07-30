import { EChartOption } from 'echarts'

export interface ILegendItem {
  name: string;
  min: number | string;
  max: number;
  avg: number;
  total: number;
  color: string;
  show:  boolean;
  hidden?: boolean
}
export type ChartType = 'bar'| 'line' | 'pie' | 'map' | 'status' | 'text'
export interface IChartOptionPorps {
  chartType: ChartType
  colors: string[]
  showExtremum: boolean
  chartOption: EChartOption
  lineWidth: number
}


export interface IChartInstance {
  getOptions: (data: any, otherOptions?: EChartOption) => ({options: EChartOption, legendData: ILegendItem[]})
}

export interface IMoreToolItem {
  name: string;
  checked: boolean;
  id: string;
  nextName?: string;
}

export interface IAnnotation {
  x: number;
  y: number;
  show: boolean;
  title: string;
  name: string;
  color: string;
  list?: IAnnotationListItem[]
}
export interface IAnnotationListItem {
  id: string; value: any; show: boolean
}
export interface IStatusSeries {
  value: number | string;
  status: number | string
}
export interface IStatusChartOption {
  series: IStatusSeries[]
}

export interface ITextSeries {
  value?: number | string;
  unit?: string;
}

export interface ITextChartOption {
  series: ITextSeries
}
export type MoreChartToolItem = 'explore' | 'set' | 'strategy' | 'area'
