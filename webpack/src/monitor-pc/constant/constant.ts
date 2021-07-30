export const PERFORMANCE_CHART_TYPE = '__chart_view_type__' // 主机视图图表显示类型 localstorage key值
export const COLLECT_CHART_TYPE = '__chart_view_type__' // 采集视图图表显示类型 localstorage key值
export const DATARETRIEVAL_CHART_TYPE = '__chart_view_type__' // 数据检索视图图表显示类型 localstorage key值
// 仪表盘页面缓存各业务的仪表盘默认显示 localstorage key值 string | {[业务id]: [仪表盘id]}
export const DASHBOARD_ID_KEY = '___grafana_dashboard_id___'
// 监控条件方法列表
export const CONDITION_METHOD_LIST = [
  { id: 'eq', name: '=' },
  { id: 'gt', name: '>' },
  { id: 'gte', name: '>=' },
  { id: 'lt', name: '<' },
  { id: 'lte', name: '<=' },
  { id: 'neq', name: '!=' },
  { id: 'include', name: 'include' },
  { id: 'exclude', name: 'exclude' },
  { id: 'reg', name: 'regex' }
]
