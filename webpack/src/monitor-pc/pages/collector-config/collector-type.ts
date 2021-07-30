export interface ICollectorTaskData {
  status: 'STOPPED' | 'STARTED' // 采集任务启停状态
  id: number | string // 任务id
  name: string
}

export interface IDeletingStepListItem {
  type: 'collect' | 'strategy',
  loading: boolean,
  title: string,
  data?: any
}
