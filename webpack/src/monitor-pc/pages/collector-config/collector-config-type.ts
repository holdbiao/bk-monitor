export interface IDrag {
  width: number
  minWidth: number
  maxWidth: number
}

export interface IStatusData {
  success: IStatus
  failed: IStatus
  nodata: IStatus
  all: IStatus
}

export interface IStatus {
  count: number
  data: any
}

export interface ITabList {
  name?: string
  type: string
  tips?: string
}

export interface IDetailInfo {
  bkBizId?: number
  collectType?: string
  createTime?: string
  createUser?: string
  deploymentId?: number
  id?: number
  label?: string
  labelInfo?: string
  name?: string
  params?: any
  pluginInfo?: any
  remoteCollectingHost?: any
  subscriptionId?: number
  target?: any
  targetNodeType?: string
  targetNodes?: any
  targetObjectType?: string
  updateTime?: string
  updateUser?: string
}

export interface IHostTopoStatus {
  host: boolean
  topo: boolean
}

export interface ICustomData {
  list: any
  page: number
  limit: number
  searchKey: string
  total: number
}

export interface IVariableData {
  '$bk_target_ip'?: string | number
  '$bk_target_cloud_id'?: string | number
  '$bk_target_service_instance_id'?: string[]
  '$target'?: string
  '$bk_inst_id'?: string
  '$bk_obj_id'?: string
  '$method'?: string
}

export interface ITargetList {
  id: string
  name: string
}
