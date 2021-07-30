/* eslint-disable no-restricted-syntax */
/* eslint-disable no-param-reassign */
// @ts-nocheck
import { typeTools } from '../../../monitor-common/utils/utils.js'
import { ITableRow, IOption, IFieldConfig, ITableOptions, IConditionValue, CheckType } from './performance-type'
const IP_LIST_MATCH = new RegExp(/((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}/, 'g')

export default class TableStore {
  public loading = false
  public page = 1
  public pageSize: number = +localStorage.getItem('__common_page_size__') || 10
  public pageList: Array<number> = [10, 20, 50, 100]
  public stickyValue = {}
  public panelKey = ''
  public sortKey = 'totalAlarmCount'
  public order = 'descending'
  public keyWord = ''
  public total = 0
  public unresolveData = []
  public cpuData = []
  public menmoryData = []
  public diskData = []
  public checkType: CheckType = 'current'
  // public selections: ITableRow[] = []
  public conditionsList: IOption[] = [
    {
      name: '>',
      id: '>'
    },
    {
      name: '>=',
      id: '>='
    },
    {
      name: '<',
      id: '<'
    },
    {
      name: '<=',
      id: '<='
    },
    {
      name: '=',
      id: '='
    }
  ]

  public fieldData: Array<IFieldConfig> = [
    {
      name: window.i18n.t('内网IP'),
      id: 'bk_host_innerip',
      checked: true,
      disable: true,
      filterChecked: true,
      filterDisable: true,
      type: 'textarea',
      value: '',
      fuzzySearch: true,
      show: false
    },
    {
      name: window.i18n.t('外网IP'),
      id: 'bk_host_outerip',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      type: 'textarea',
      value: '',
      fuzzySearch: true,
      show: false
    },
    {
      name: window.i18n.t('采集状态'),
      id: 'status',
      checked: true,
      disable: true,
      filterChecked: true,
      filterDisable: true,
      type: 'checkbox',
      options: [
        {
          name: window.i18n.t('未知'),
          id: -1
        },
        {
          name: window.i18n.t('正常'),
          id: 0
        },
        {
          name: window.i18n.t('无数据上报'),
          id: 3
        },
        {
          name: window.i18n.t('Agent未安装'),
          id: 2
        }
      ],
      value: [],
      show: false
    },
    {
      name: window.i18n.t('主机名'),
      id: 'bk_host_name',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      options: [],
      type: 'select',
      value: '',
      fuzzySearch: true,
      allowEmpt: true, // 允许空筛选选项出现
      show: false
    },
    {
      name: window.i18n.t('OS名称'),
      id: 'bk_os_name',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      options: [],
      type: 'select',
      value: '',
      fuzzySearch: true,
      allowEmpt: true,
      show: false
    },
    {
      name: window.i18n.t('云区域'),
      id: 'bk_cloud_name',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      options: [],
      type: 'select',
      value: '',
      show: false
    },
    {
      name: window.i18n.t('集群模块'),
      id: 'cluster_module',
      filterChecked: true,
      filterDisable: false,
      options: [],
      type: 'cascade',
      value: [],
      multiple: true,
      show: false
    },
    {
      name: window.i18n.t('集群名'),
      id: 'bk_cluster',
      filterChecked: true,
      filterDisable: false,
      checked: false,
      disable: false,
      options: [],
      type: 'select',
      value: '',
      fuzzySearch: true,
      multiple: true,
      show: false
    },
    {
      name: window.i18n.t('模块名'),
      id: 'bk_inst_name',
      filterChecked: true,
      filterDisable: false,
      checked: false,
      disable: false,
      options: [],
      type: 'select',
      value: '',
      fuzzySearch: true,
      multiple: true,
      show: false
    },
    {
      name: window.i18n.t('未恢复告警'),
      id: 'alarm_count',
      checked: true,
      disable: false,
      type: 'number',
      show: false
    },
    {
      name: window.i18n.t('CPU五分钟负载'),
      id: 'cpu_load',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('CPU使用率'),
      id: 'cpu_usage',
      checked: false,
      disable: false,
      filterChecked: true,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('磁盘空间使用率'),
      id: 'disk_in_use',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('磁盘IO使用率'),
      id: 'io_util',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('应用内存使用率'),
      id: 'mem_usage',
      checked: true,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('物理内存使用率'),
      id: 'psc_mem_usage',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      conditions: this.conditionsList,
      type: 'condition',
      value: [],
      show: false
    },
    {
      name: window.i18n.t('业务名'),
      id: 'bk_biz_name',
      checked: false,
      disable: false,
      filterChecked: false,
      filterDisable: false,
      type: 'text',
      value: '',
      fuzzySearch: true,
      show: false
    },
    {
      name: window.i18n.t('进程'),
      id: 'display_name',
      checked: true,
      disable: true,
      filterChecked: false,
      filterDisable: false,
      options: [],
      type: 'select',
      value: '',
      fuzzySearch: true,
      allowEmpt: true,
      show: false
    }
  ]
  // 缓存options数据的字段
  public cacheFieldOptionsSet = {
    bk_host_name: new Set(),
    bk_os_name: new Set(),
    bk_cloud_name: new Set(),
    display_name: new Set() // 进程选项缓存
  }
  public cacheModuleMap = new Map()
  public cacheClusterMap = new Map()
  // 缓存当前筛选数据
  public filterData!: Readonly<Array<ITableRow>>
  public allData!: Readonly<Array<ITableRow>>
  private bizList: any[] = []
  public constructor(data: Array<any>, options: ITableOptions, bizList: any[]) {
    this.bizList = bizList
    this.updateData(data, options)
  }

  public get columns() {
    const columns = {}
    this.fieldData.forEach((field) => {
      columns[field.id] = field
    })
    return columns
  }

  public setState(rowId: string, key: string, value: any) {
    const row = this.allData.find(item => item.rowId === rowId)
    if (Object.prototype.hasOwnProperty.call(row, key)) {
      row[key] = value
    }
  }

  public updateData(data: Array<any>, options?: ITableOptions) {
    this.stickyValue = options?.stickyValue || {}
    this.panelKey = options?.panelKey || ''
    this.unresolveData = []
    this.cpuData = []
    this.menmoryData = []
    this.diskData = []
    this.allData = Object.freeze(data.map(item => Object.seal(this.initRowData(item))))
    this.updateFieldDataOptions()
  }

  public updateFieldDataOptions() {
    for (const key in this.cacheFieldOptionsSet) {
      const cacheFieldSet = this.cacheFieldOptionsSet[key]
      const fieldData = this.fieldData.find(item => item.id === key)
      if (cacheFieldSet.size && fieldData) {
        fieldData.options = []
        for (const val of cacheFieldSet.values()) {
          fieldData.options.push({
            id: val,
            name: val
          })
        }
      }
      // 添加空项筛选
      if (fieldData?.allowEmpt) {
        fieldData.options.unshift({ id: '__empt__', name: window.i18n.t('- 空 -') })
      }
    }
    const moduleFieldData = this.fieldData.find(item => item.id === 'bk_inst_name')
    moduleFieldData && (moduleFieldData.options = [])
    for (const value of this.cacheModuleMap.values()) {
        moduleFieldData?.options?.push(value)
    }

    this.fieldData.filter(item => ['bk_cluster', 'cluster_module'].includes(item.id)).forEach((fieldData) => {
      fieldData.options = []
      for (const value of this.cacheClusterMap.values()) {
        fieldData.options?.push(value)
      }
    })
    // // forEach性能低
    // for (const key in this.cacheFieldOptionsData) {
    //   this.cacheFieldOptionsData[key].clear()
    // }
    // this.cacheModule.clear()
    // this.cacheCluster.clear()
  }

  // 初始化行属性（扩展属性）
  public initRowData(item) {
    // 集群名称
    item.bk_cluster = []
    // 填充options数据
    // forEach性能低
    for (const key in this.cacheFieldOptionsSet) {
      if (item[key] || key === 'display_name') {
        item[key] && this.cacheFieldOptionsSet[key].add(item[key])
        // 进程添加可选项
        if (key === 'display_name') {
          // item?.component?.forEach(com => this.cacheFieldOptionsSet[key].add(com?.['display_name'] || ''))
          for (const com of (item?.component || [])) {
            this.cacheFieldOptionsSet[key].add(com?.display_name || '')
          }
        }
      }
    }
    const module = item.module || []
    // eslint-disable-next-line @typescript-eslint/prefer-for-of
    for (let i = 0; i < module.length; i++) {
      const currentModule = module[i]
      const {
        id: moduleId,
        bk_inst_name: moduleName,
        topo_link: topoLink,
        topo_link_display: topoLinkDisplay } = currentModule

      if (moduleId && moduleName) {
        this.cacheModuleMap.set(moduleId, {
          id: moduleId,
          name: moduleName
        })
      }

      if (topoLink && topoLink.length > 1) {
        const clusterId = topoLink[topoLink.length - 2]
        const clusterName = topoLinkDisplay[topoLink.length - 2]
        if (!item.bk_cluster.find(i => i.id === clusterId)) {
          item.bk_cluster.push({
            name: clusterName,
            id: clusterId
          })
        }
        if (!this.cacheClusterMap.has(clusterId)) {
          this.cacheClusterMap.set(clusterId, {
            name: clusterName,
            id: clusterId,
            children: [
              {
                id: moduleId,
                name: moduleName
              }
            ]
          })
        } else {
          const cacheClusterMap = this.cacheClusterMap.get(clusterId)
          const moduleIndex = cacheClusterMap.children.findIndex(i => i.id === moduleId)
          moduleIndex === -1 && cacheClusterMap.children.push({
            id: moduleId,
            name: moduleName
          })
        }
      }
    }

    // this.fieldData.forEach((set) => {
    //   if (set.id === 'bk_inst_name') {
    //     // 填充模块options数据
    //     item.module.forEach((m) => {
    //       const { id, bk_inst_name } = m
    //       if (!set.options.find(i => i.id === id)) {
    //         set.options.push({
    //           name: bk_inst_name,
    //           id
    //         })
    //       }
    //     })
    //   } else if (set.id === 'display_name') {
    //     // 填充进程options数据
    //     item.component.forEach((m) => {
    //       const { display_name: name } = m
    //       if (!set.options.find(i => i.name === name)) {
    //         set.options.push({
    //           name,
    //           id: name
    //         })
    //       }
    //     })
    //   } else if (set.id === 'bk_cluster' || set.id === 'cluster_module') {
    //     // 填充集群options数据
    //     const module = item.module || []
    //     module.forEach((m) => {
    //       const topoLink = m.topo_link
    //       const topoLinkDisplay = m.topo_link_display
    //       const moduleName = m.bk_inst_name // 模块名
    //       const moduleId = m.id // 模块ID
    //       if (topoLink && topoLink.length > 1) {
    //         const clusterId = topoLink[topoLink.length - 2]
    //         const clusterName = topoLinkDisplay[topoLink.length - 2]
    //         if (!item.bk_cluster.find(i => i.id === clusterId)) {
    //           item.bk_cluster.push({
    //             name: clusterName,
    //             id: clusterId
    //           })
    //         }
    //         const clusterIndex = set.options.findIndex(i => i.id === clusterId)
    //         if (clusterIndex === -1) {
    //           set.options.push({
    //             name: clusterName,
    //             id: clusterId,
    //             children: [
    //               {
    //                 id: moduleId,
    //                 name: moduleName
    //               }
    //             ]
    //           })
    //         } else {
    //           const moduleIndex = set.options[clusterIndex].children.findIndex(i => i.id === moduleId)
    //           moduleIndex === -1 && set.options[clusterIndex].children.push({
    //             id: moduleId,
    //             name: moduleName
    //           })
    //         }
    //       }
    //     })
    //   } else if (!set.conditions && set.options && item[set.id]) {
    //     // 填充其他不带条件的options数据
    //     const val = item[set.id]
    //     if (!set.options.find(i => i.id === val)) {
    //       set.options.push({
    //         name: val,
    //         id: val
    //       })
    //     }
    //   }
    // })
    // 行Id
    item.rowId = `${item.bk_host_innerip}|${item.bk_cloud_id}`
    // 未恢复告警总数
    item.totalAlarmCount = item?.alarm_count?.reduce((pre, cur) => pre + cur.count, 0)
    // 当前悬浮状态
    // item.hover = false
    item.mark = Object.prototype.hasOwnProperty.call(this.stickyValue, item.rowId)
    // item.order = this.sticky[item.rowId] ? 99999 : i
    // todo 排序进程
    item?.component?.forEach((com) => {
      switch (+com.status) {
        case -1:
          com.status = 2
          break
        case 0:
          com.status = 3
          break
        default:
          com.status = 1
      }
      // com.status = +com.status === -1 ? 2 : (+com.status === 0 ? 3 : 1)
    })
    item?.component?.sort((b, a) => b.status - a.status)
    // 进程数量过多时是否省略
    // item.overflow = false
    // 业务名
    const bizItem = this.bizList.find(set => +set.id === +item.bk_biz_id)
    item.bk_biz_name = bizItem ? bizItem.text : '--'
    // 模块名
    item.bk_inst_name = item?.module.length
      ? item.module.map(m => m.bk_inst_name).join(' , ') : '--'
    // checkedbox
    item.selection = false
    // 新增模糊搜索字段属性
    item.moduleInstNames = item.module ? item.module.map(m => m.bk_inst_name).join() : ''
    item.componentNames = item.component ? item.component.map(com => com.display_name).join() : ''
    item.clusterNames = item.bk_cluster.map(cluster => cluster.name).join()
    // 分类数据
    if (item.alarm_count && item.alarm_count.findIndex(data => (+data.count) > 0) > -1) {
      this.unresolveData.push(item)
    }
    if (item.cpu_usage >= 80) {
      this.cpuData.push(item)
    }
    if (item.mem_usage >= 80) {
      this.menmoryData.push(item)
    }
    if (item.disk_in_use >= 80) {
      this.diskData.push(item)
    }
    return item
  }

  public getTableData() {
    let data = [...(this.panelKey ? this[this.panelKey] : this.allData)]
    const fieldData = this.fieldData.filter(field => (Array.isArray(field.value)
      ? !!field.value.length
      : field.value !== '' && field.value !== undefined))

    fieldData.forEach((field) => {
      data = data.filter(item => this.isMatchedCondition(item, field))
    })

    if (this.keyWord.trim() !== '') {
      data = this.filterDataByKeyword(data)
    }
    const sortData = this.sortDataByKey(data)
    this.total = sortData.length
    // 缓存当前过滤后数据，用于分页、换页、指标对比、采集下发和复制IP操作
    this.filterData = Object.freeze(sortData)

    return JSON.parse(JSON.stringify(this.pagination(sortData)))
  }
  // 重新排序缓存数据
  public reOrderData() {
    this.filterData = Object.freeze(this.sortDataByKey([...this.filterData]))
    return JSON.parse(JSON.stringify(this.pagination(this.filterData)))
  }
  // 重新分页数据
  public reLimitData() {
    // return this.reOrderData()
    return JSON.parse(JSON.stringify(this.pagination([...this.filterData])))
  }

  // 关键字匹配
  public filterDataByKeyword(data: ITableRow[]) {
    // const keyWord = this.keyWord.trim().toLocaleLowerCase()
    const keyWord = this.keyWord.trim()
    const fieldData = this.fieldData.filter(item => item.fuzzySearch)
    // 多IP精确/单IP模糊筛选
    const ips = keyWord.match(IP_LIST_MATCH)
    if (ips?.length > 1) {
      return data.filter(item => ips.includes(item.bk_host_innerip))
    } if (ips?.length === 1) {
      return data.filter(item => item.bk_host_innerip.includes(ips[0]))
    }
    return data.filter((item) => {
      for (let i = 0, len = fieldData.length; i < len; i++) {
        const field = fieldData[i]
        let val = ''
        if (field.id === 'bk_inst_name') {
          // 模块
          val = item.moduleInstNames
        } else if (field.id === 'display_name') {
          // 进程名
          val = item.componentNames
        } else if (field.id === 'bk_cluster') {
          // 集群名
          val = item.clusterNames
        } else {
          val = item[field.id] || ''
        }
        if (typeof val === 'number') {
          val = `${val}`
        }
        // 耗时操作
        // val = val.toLocaleLowerCase()
        if (val.includes(keyWord)) {
          return true
        }
      }
      return false
    })
  }

  // 条件匹配
  public isMatchedCondition(item: ITableRow, field: IFieldConfig) {
    const { curValue, originValue } = this.getCompareValue(item, field)
    // 处理空值
    if (curValue === '__empt__' || curValue[0] === '__empt__') {
      // 允许筛选空值的选项(进程)
      if (['display_name'].includes(field.id)) {
        return !originValue.length
      }
      // 允许筛选空值的选项(主机名，os名)
      if (['bk_host_name', 'bk_os_name'].includes(field.id)) {
        return !originValue
      }
    }
    if (Array.isArray(curValue) && !Array.isArray(originValue)) { // 原始值是当前值的子集
      // 当前值类型为 array，原始值类型为 string | number (eg: ip类型、CPU使用率等类型)
      if (field.conditions && field.conditions.length > 0) {
        // 匹配使用率类型
        return (curValue as IConditionValue[]).every((data) => {
          // 空条件不匹配
          if (typeTools.isNull(data.value) || typeTools.isNull(data.condition)) return true
          switch (data.condition) {
            case '>':
              return originValue > data.value
            case '>=':
              return originValue >= data.value
            case '<':
              return originValue < data.value
            case '<=':
              return originValue <= data.value
            case '=':
              return `${originValue}` === `${data.value}`
            default:
              return false
          }
        })
      }
      // IP单个模糊/多个精确筛选
      if (['bk_host_innerip', 'bk_host_outerip'].includes(field.id)) {
        const valueStr = curValue.toString()
        const targetIp = item[field.id]
        const ips = valueStr.match(IP_LIST_MATCH)
        const len = ips?.length
        if (len > 1) {
          return ips.includes(targetIp)
        } if (len === 1) {
          return targetIp.includes(ips[0])
        }
        return targetIp.includes(valueStr)
      }
      // 匹配子集关系（eg: IP）
      return curValue.includes(originValue)
    } if (!Array.isArray(curValue) && Array.isArray(originValue)) { // 当前值是原始值的子集
      // 当前值类型为 string, 原始值为 array（eg: 模块名、进程名、集群名）
      return originValue.includes(curValue)
    } if (Array.isArray(curValue) && Array.isArray(originValue)) {
      return curValue.some((val) => {
        if (Array.isArray(val)) {
          return val.every(v => originValue.includes(v))
        }
        return originValue.includes(val)
      })
    }

    return originValue === curValue
  }

  public getCompareValue(item: ITableRow, field: IFieldConfig) {
    let originValue = item[field.id] === undefined ? '' : item[field.id]// 当 field.id 为 模块、进程、集群、模块\集群时，该值为undefined
    let curValue = field.value === '' ? '' : field.value // 筛选条件的值
    if (['bk_host_innerip', 'bk_host_outerip'].includes(field.id)) {
      // IP类型的值
      curValue = (field.value as string)
        .replace(/\n|,/g, '|')
        .replace(/\s+/g, '')
        .split('|')
    } else if (field.id === 'bk_inst_name') {
      // 模块ID
      originValue = item.module ? item.module.map(m => m.id) : []
    } else if (field.id === 'display_name') {
      // 进程名
      originValue = item.component ? item.component.map(com => com[field.id]) : []
    } else if (field.id === 'bk_cluster') {
      // 集群ID（集群字段是前端拼接的，在initRowData方法里面）
      originValue = item.bk_cluster.map(cluster => cluster.id)
    } else if (field.id === 'cluster_module') {
      // 集群\模块（级联输入）
      const moduleIds = item.module ? item.module.map(m => m.id) : []
      const clusterIds = item.bk_cluster.map(cluster => cluster.id)
      originValue = moduleIds.concat(clusterIds)
    }
    return {
      originValue,
      curValue
    }
  }

  public sortDataByKey(data: ITableRow[]) {
    data.sort((pre, next) => {
      const isPreTop = Object.prototype.hasOwnProperty.call(this.stickyValue, pre.rowId) ? 1 : 0
      const isNextTop = Object.prototype.hasOwnProperty.call(this.stickyValue, next.rowId) ? 1 : 0
      if (isPreTop === isNextTop) {
        return this.order === 'ascending'
          ? (+pre[this.sortKey]) - (+next[this.sortKey])
          : (+next[this.sortKey]) - (+pre[this.sortKey])
      }
      return isNextTop - isPreTop
    })
    return data
  }

  public pagination(data: ITableRow[]) {
    return data.slice(this.pageSize * (this.page - 1), this.pageSize * this.page)
  }
}
