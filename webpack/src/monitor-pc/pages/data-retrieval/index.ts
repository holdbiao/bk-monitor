export type chartType = 0 | 1 | 2
export interface IGetQueryConfigParams {
  bkBizId: number; // 业务id
  queryConfigs: IQueryConfigsItem[];
  compareConfig: { // 对比配置
    type: string; // time, metric, target
    timeOffset?: string; // 时间偏移量
    split?: boolean; // 视图分割
    target?: any;
  },
  target: any; // 监控目标
  targetType: 'INSTANCE' | 'TOPO';
  startTime: number; // 开始时间
  endTime: number; // 结束时间
  tools: ITools
}

export interface IQueryConfigsItem {
  key?: string; // v-for的唯一key
  merticId?: number,
  relatedId?: number;
  relatedName?: string;
  hidden: boolean; // 是否生效
  label: string; // 监控对象
  metricField: string; // 指标名
  method: string; // 聚合方法(计算公式)
  interval: number; // 聚合周期(监控周期)
  resultTableId: string; // 结果表
  dataSourceLabel: string; // 数据源标签
  dataTypeLabel: string; // 数据类型
  groupBy: string[]; // 聚合字段
  where: any; // 查询条件(监控条件)
//   merticVal: string // 指标级联选择器材值绑定
}

export interface ITools {
  timeRange: number | string;
  refleshInterval: number;
}

export interface ITargetListItem {
  'bk_cloud_id': number,
  'bk_supplier_id': string,
  ip: string
}

export interface IHistoryListItem {
  id?: string;
  name?: string;
  show?: boolean;
  bkBizId: string;
  config: IGetQueryConfigParams;
}

export interface IAggIntervalListItem {
  id: number,
  name: string
}

export interface IMethodListItem {
  id: string;
  name: string;
  show: boolean;
}

export interface IDimensionsListItem {
  id: string;
  name: string;
  show: boolean;
}

export interface IConditionsItem {
  condition?: string;
  key: string;
  method: string;
  value: string[];
}

export interface IAggMethodList {
  name: string,
  id: string
}

export interface ICheckedDashboard {
  id?: number;
  uid?: string;
}
