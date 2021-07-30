export interface IDataSource {
  'bk_monitor_time_series': IDataSourceItem,
  'log_time_series': IDataSourceItem,
  'bk_data_time_series': IDataSourceItem,
  'custom_time_series': IDataSourceItem,
  'bk_monitor_log': IDataSourceItem
}
export interface IDataSourceItem {
  count: number,
  dataSourceLabel: string,
  dataTypeLabel: string,
  sourceType: string,
  sourceName: string,
  list: any[]
}
export interface IPage  {
  'bk_monitor_time_series': number,
  'bk_data_time_series': number,
  'custom_time_series': number,
  'log_time_series': number
}

export interface ISearchObj {
  keyWord: { values: { id: string, name: string }[], id: string, name: string }[],
  data: ISearchOption[]
}

export interface IMetric {
  dataSourceLabel: string,
  dataTypeLabel: string,
  id: number,
  metricName: string,
  resultTableId: string,
  relatedId: string,
  relatedName: string
}

export interface ITimeSelect {
  value: number,
  list: { id: number, name: string }[]
}

export type ITag = {
  value: string,
  list: ITimeSelect['list']
}

export interface ISearchOption {
  id: string,
  name: string,
  children: any[]
}

export interface IStaticParams {
  'bk_biz_id': number,
  'data_source_label': string,
  'data_type_label': string,
  'result_table_label': string
}

