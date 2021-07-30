export interface Itab {
  active: string,
  list: IList[]
}

export interface ISearchValue {
  customEvent: string,
  customTimeSeries: string
}

export interface IPanelList {
  name: string,
  id: string,
  href: boolean
}

export interface ITableData {
  loading: boolean,
  customEvent: any[],
  customTimeSeries: any[]
}

export interface ISearchParams {
  'search_key': string,
  page: number,
  'page_size': number
}

export interface IList {
  name: string,
  id: string,
  hasActive: boolean
}
