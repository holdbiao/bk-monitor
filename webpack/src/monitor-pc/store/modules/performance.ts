import { VuexModule, Module, Action, getModule, Mutation } from 'vuex-module-decorators'
import {
  hostPerformance,
  hostIndex,
  hostPerformanceDetail,
  graphPoint,
  hostProcessStatus,
  hostComponentInfo,
  getHostDashboardConfig,
  getTopoNodeDashboardConfig,
  searchHostInfo,
  searchHostMetric,
  hostTopoNodeDetail,
  topoNodeProcessStatus
} from '../../../monitor-api/modules/performance'
import { getTopoTree } from '../../../monitor-api/modules/commons'
import { listUserConfig, createUserConfig, partialUpdateUserConfig } from '../../../monitor-api/modules/model'
import { savePanelOrder, deletePanelOrder } from '../../../monitor-api/modules/data_explorer'
import store from '../store'
import { transformDataKey } from '../../../monitor-common/utils/utils'
import Vue from 'vue'

interface IHostData {
  hosts: any[]
}
interface IUserConfig {
  id?: number
  value: string
  key: string
  username?: string
}

interface IUpdateConfig {
  id: number
  value: string
}

interface IConditionValue {
  condition: '>' | '>=' | '<' | '<=' | '='
  value: number
}
interface ISearchItem {
  id: string
  value: string | number | (string | number)[] | IConditionValue[]
}

export interface ICurNode {
  id: string; // ip + cloudId 或者 bkInstId + bkObjId
  ip?: string;
  cloudId?: string | number;
  bkInstId?: number | string
  bkObjId?: string
  type: 'host' | 'node'; // host类型时：IP、bkCloudId不为空；node类型时：bkInstId、bkObjId不为空
  processId?: string | number;
  osType?: number;
}
// todo 老代码
export const SET_PERFORMANCE_HOST = 'SET_PERFORMANCE_HOST'
export const SET_PERFORMANCE_ROW = 'SET_PERFORMANCE_ROW'
export const SET_PERFORMANCE_PROCESS = 'SET_PERFORMANCE_PROCESS'
export const SET_PERFORMANCE_VIEWTYPE = 'SET_PERFORMANCE_VIEWTYPE'
export const SET_URL_QUERY = 'SET_URL_QUERY'

// eslint-disable-next-line new-cap
@Module({ name: 'performance', dynamic: true, namespaced: true, store })
class Performance extends VuexModule {
  // todo 老代码
  public list: any[] = []
  public rows: any = null
  public proc = ''
  public type = 'performance'
  // 列表条件
  public conditions: ISearchItem[] = []

  // 主机列表
  public hosts: Readonly<any[]> = []
  // 主机拓扑树数据
  public hostToppTreeData = []
  // 主机视角指标信息
  public hostIndex = []

  // 主机进程列表
  public processList = []
  // 主机仪表盘配置列表
  public hostConfigList = []
  // 主机仪表盘配置排序列表
  public hostOrderList = []
  // 进程仪表盘视图配置列表
  public processConfigList = []
  // 进程仪表盘配置排序列表
  public processOrderList = []
  // 当前节点信息
  public curNode: ICurNode = { id: '', type: 'host' }

  public storeKeyword = ''
  public storeFilterList: Readonly<any[]> = []

  public get hostList() {
    return this.list
  }

  public get curProcessList() {
    return this.processList || []
  }
  public get curProcess() {
    return this.curNode?.processId
  }

  public get targetList() {
    return this.list.map(item => ({ id: `${item.bk_cloud_id}-${item.bk_host_innerip}`, name: item.bk_host_innerip }))
  }

  public get dashboardConfigList() {
    return this.hostConfigList
  }
  public get processDashboardConfigList() {
    return this.processConfigList
  }

  public get dashboardHostOrderList() {
    return this.hostOrderList
  }
  public get dashboardProcessOrderList() {
    return this.processOrderList
  }


  public get row() {
    return this.rows
  }

  public get process() {
    return this.proc
  }

  public get viewType() {
    return this.type
  }

  // 获取URL参数
  public get urlQuery() {
    return this.conditions.length ? `?search=${JSON.stringify(this.conditions)}` : ''
  }
  // 搜索keyword
  public get keyword() {
    return this.storeKeyword
  }
  // 筛选主机列表
  public get filterHostList() {
    return this.storeFilterList
  }

  // 拓扑树
  public get filterHostTopoTreeList() {
    return this.hostToppTreeData
  }

  @Mutation
  public [SET_PERFORMANCE_HOST](hostList = []) {
    this.list = hostList
  }

  @Mutation
  public [SET_PERFORMANCE_ROW](row) {
    this.rows = row
  }

  @Mutation
  public [SET_PERFORMANCE_PROCESS](process = '') {
    this.proc = process
  }

  @Mutation
  public [SET_PERFORMANCE_VIEWTYPE](viewType = 'performance') {
    this.type = viewType
  }

  @Mutation
  public setConditions(data = []) {
    this.conditions = data
  }

  // 主机列表数据
  @Mutation
  public setHostList(data: any[] = []) {
    this.hosts = Object.freeze(data)
  }

  // 设置主机进程缓存
  @Mutation
  public setProcessList(data) {
    this.processList = data
  }

  // 设置主机仪表盘配置列表
  @Mutation
  public setHostConfigList(data) {
    this.hostConfigList = data
  }
  // 设置进程仪表盘配置列表
  @Mutation
  public setProcessConfigList(data) {
    this.processConfigList = data
  }

  @Mutation
  public setHostOrderList(data) {
    this.hostOrderList = data
  }
  @Mutation
  public setProcessOrderList(data) {
    this.processOrderList = data
  }

  // 设置主机进程缓存
  @Mutation
  public setProcessId(processId: string | number) {
    this.curNode = {
      ...this.curNode,
      processId
    }
  }

  @Mutation
  public setCurNode(data: ICurNode) {
    this.curNode = data
  }

  @Mutation
  public setKeyWord(keyword: string) {
    this.storeKeyword = keyword
    this.storeFilterList = keyword
      ? this.hosts.filter(item => ['bk_host_innerip', 'bk_host_outerip', 'k_host_name',
        'bk_os_name', 'bk_biz_name', 'bk_cluster',
        'module', 'component'].some((key) => {
        let hostProp = item[key] || ''
        if (typeof hostProp === 'string') {
          return hostProp.includes(keyword)
        } if (key === 'module' || key === 'bk_cluster') {
          hostProp = item.module
          return hostProp.some(set => set.topo_link_display.some(child => child.includes(keyword)))
        }
        return hostProp.some(set => set.display_name.includes(keyword))
      }))
      : this.hosts
  }

  @Mutation
  public setTopoTreeList(treeData: any) {
    this.hostToppTreeData = treeData
  }

  // 获取用户置顶配置
  @Action
  public async getUserConfigList(params): Promise<IUserConfig[]> {
    const data = await listUserConfig(params).catch(() => [])
    return data
  }

  // 创建用户置顶配置
  @Action
  public async createUserConfig(params: IUserConfig) {
    const result = await createUserConfig(params).catch(() => ({}))
    return result
  }
  // 更新用户置顶配置
  @Action
  public async updateUserConfig(params: IUpdateConfig) {
    const result = await partialUpdateUserConfig(params.id, { value: params.value })
      .then(() => true)
      .catch(() => false)
    return result
  }
  // 获取主机列表信息
  @Action
  public async getHostPerformance(): Promise<any[]> {
    const hosts: any[] = await searchHostInfo().catch(() => [])
    if (this.curNode.cloudId === -1) {
      this.setCurNode({
        ...this.curNode,
        cloudId: (hosts.find((item: any) => item.bk_host_innerip === this.curNode.ip)
         || { bk_cloud_id: -1 }).bk_cloud_id
      })
    }
    // 大数据排序有性能问题
    // this.setHostList(data.hosts.sort((a: any, b: any) => {
    //   const ip1 = a.bk_host_innerip.split('.').map(el => el.padStart(3, '0'))
    //     .join('')
    //   const ip2 = b.bk_host_innerip.split('.').map(el => el.padStart(3, '0'))
    //     .join('')
    //   return ip1 - ip2
    // }))
    this.setHostList(hosts)
    this.setKeyWord(this.storeKeyword)
    return hosts
  }

  // 带有指标的全量主机信息
  @Action
  public async getHostPerformanceMetric(): Promise<IHostData> {
    const data: IHostData = await hostPerformance().catch(() => ({
      hosts: [],
      update_time: ''
    }))
    return data
  }

  @Action
  public async searchHostMetric(params: any) {
    const hostsMap = await searchHostMetric(params).catch(() => [])
    return hostsMap
  }

  @Action
  public async getHostIndex() {
    const result = await hostIndex().catch(() => [])
    this[SET_PERFORMANCE_HOST](result)
    return result
  }

  // 获取主机拓扑树列表
  @Action
  public async getTopoTree(params = {
    instance_type: 'host',
    remove_empty_nodes: true
  }) {
    const data = await getTopoTree(params).catch(() => [])
    this.setTopoTreeList(data)
    return data
  }

  @Action
  public async getHostDashboardConfig(params) {
    const { data, tips } = this.curNode.type === 'host'
      ? await getHostDashboardConfig(params, { needRes: true })
        .catch(() => ({ data: { panels: [], order: [] } }))
      : await getTopoNodeDashboardConfig(params, { needRes: true })
        .catch(() => ({ data: { panels: [], order: [] } }))
    if (tips?.length) {
      Vue.prototype.$bkMessage({
        theme: 'warning',
        message: tips
      })
    }
    if (params.type === 'host') {
      this.setHostConfigList(data.panels)
      this.setHostOrderList(data.order)
    } else if (params.type === 'process') {
      this.setProcessConfigList(data.panels)
      this.setProcessOrderList(data.order)
    }
  }

  // 获取主机详情
  @Action
  public async getHostDetail(params) {
    const data = await hostPerformanceDetail(params).catch(() => ({}))
    return data
  }

  // 获取节点详情
  @Action
  public async getNodeDetail(params) {
    const data = await hostTopoNodeDetail(params).catch(() => ({}))
    return data
  }

  @Action
  public async graphPoint(params) {
    const data = await graphPoint(params).catch(() => ({}))
    return data
  }

  @Action
  public async getProcessDetail(params) {
    let data = this.curNode.type === 'host'
      ? await hostProcessStatus(params).catch(() => [])
      : await topoNodeProcessStatus(params).catch(() => [])

    data = transformDataKey(data)
    this.setProcessList(data)
    if (!this.curNode?.processId) {
      this.setProcessId(data[0] ? data[0].displayName : '')
    }
    return data
  }

  @Action
  // 获取进程端口的运行状态
  public async getHostProcessPortDetail() {
    const { ip, cloudId, processId } = this.curNode
    const data = await hostComponentInfo({
      bk_cloud_id: cloudId,
      ip,
      name: processId
    }).catch(() => ({
      ports: {}
    }))
    return Object.keys(data.ports).map(port => ({
      value: port,
      status: data.ports[port].status
    }))
  }
  @Action
  public async saveDashboardOrder(params: object) {
    const data = await savePanelOrder(params).then(() => true)
      .catch(() => false)
    return data
  }
  @Action
  public async deletePanelOrder(id: string) {
    const data = await deletePanelOrder({ id }).then(() => true)
      .catch(() => false)
    return data
  }
}

export default getModule(Performance)
