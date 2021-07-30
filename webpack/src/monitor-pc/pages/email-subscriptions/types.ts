export interface IRadioMap {
  id: number
  name: string
}

export interface IGraphValueItem {
  id: string
  name: string
}

export const enum EWeek { Sun = 7, Mon = 1, Tue = 2, Wed = 3, Thu = 4, Fri = 5, Sat = 6 }

export const enum EType { 'once', 'day', 'week', 'month'}

export interface ITimePeriodValue {
  type: EType
  runTime: string
  dayList: number[]
  weekList: number[]
}

export interface IContentFormData {
  contentTitle: string
  contentDetails: string
  rowPicturesNum: 1 | 2
  graphs: string[]
}

export interface ISelectChartValue {
  title?: string
  bkBizId: number
  dashboardUid: number
  panelId: number
}

export interface IAddChartToolData {
  show: boolean
  active: string,
  tabList: any
}

export interface IToolTabListItem {
  label: string,
  name: 'default' | 'grafana'
}

export interface IChartListAllItem {
  id: number
  name: string
  panels: IChartDataItem[],
  text: string
  uid: string
  title?: string
  'bk_biz_id'?: number
}

export interface IChartDataItem {
  id: number,
  title: string,
  key?: string,
  fatherId?: string
}

export interface ITableColumnItem {
  label: string
  key: string,
  formatter?: Function
  width?: number
}

export interface IDefaultRadioList {
  id: string,
  text: string,
  title: string
}
