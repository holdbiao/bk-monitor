export interface ISideslider {
  isShow: boolean,
  title: string,
  data: {}
}

export interface IParams {
  'time_range': string
  'bk_event_group_id'?: string,
  'time_series_group_id'?: string
}

export interface IEditParams {
  'bk_event_group_id'?: string,
  'time_series_group_id'?: string
  name: string,
  scenario: string,
  'is_enable': boolean
}

export interface IDetailData {
  'bk_data_id': string,
  'access_token': string,
  name: string,
  scenario: string,
  'bk_event_group_id'?: string,
  'time_series_group_id'?: string
  'scenario_display': string[],
  'event_info_list'?: any[],
  'metric_json'?: any[],
  'last_time'?: number
  'table_id'?: string
}

export interface IShortcuts {
  list: { value: number, name: string }[],
  value: number
}

export interface IRefreshList {
  list: { value: number, name: string }[],
  value: number
}
