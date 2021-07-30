<template>
  <div class="performance" v-monitor-loading="{ isLoading }">
    <!-- 筛选面板 -->
    <OverviewPanel
      :active="tableInstance.panelKey"
      :panel-statistics="panelStatistics"
      :loading="tableInstance.loading"
      @click="handlePanelClick">
    </OverviewPanel>
    <!-- 筛选工具栏 -->
    <PerformanceTool
      :check-type="checkType"
      :selection-data="selectionData"
      :exclude-data-ids="excludeDataIds"
      :selections-count="selectionsCount"
      @search-change="handleSearchChange">
    </PerformanceTool>
    <!-- 表格区域 -->
    <PerformanceTable
      ref="table"
      :key="tableKey"
      :columns="columns"
      :data="pagingData"
      :page-config="pageConfig"
      :all-check-value="allCheckValue"
      :check-type="checkType"
      :selection-data="selectionData"
      :exclude-data-ids="excludeDataIds"
      :selections-count="selectionsCount"
      @sort-change="handleSortChange"
      @limit-change="handleLimitChange"
      @page-change="handlePageChange"
      @ip-mark="handleIpMark"
      @row-check="handleRowCheck"
      @check-change="handleCheckChange">
    </PerformanceTable>
  </div>
</template>

<script lang="ts">
import commonPageSizeMixin from '../../mixins/commonPageSizeMixin'
import OverviewPanel from './components/overview-panel.vue'
import PerformanceTool from './components/performance-tool.vue'
import PerformanceTable from './components/performance-table.vue'
import { Component, Mixins, Ref, Provide, Prop } from 'vue-property-decorator'
import PerformanceModule from '../../store/modules/performance'
import TableStore from './table-store'
import { Route } from 'vue-router'
import {
  IPanelStatistics,
  IPageConfig,
  ICheck,
  ISearchItem,
  ITableRow,
  ISort
} from './performance-type'
import { typeTools } from '../../../monitor-common/utils/utils'

Component.registerHooks([
  'beforeRouteLeave',
  'beforeRouteEnter'
])
@Component({
  name: 'performance',
  components: {
    OverviewPanel,
    PerformanceTool,
    PerformanceTable
  }
})
export default class Performance extends Mixins(commonPageSizeMixin) {
  @Prop({ default: () => [], type: Array }) private readonly search: ISearchItem[]
  @Ref('table') private readonly tableRef: PerformanceTable
  private isLoading = false
  private tableInstance: TableStore = new TableStore([], {}, this.bizList)
  // 置顶信息
  private sticky = {
    key: 'userStikyNote',
    id: -1,
    value: {}
  }

  // 字段显示设置存储Key
  private colStorageKey = `${this.$store.getters.userName}-${this.$store.getters.bizId}`
  // 选中项
  // private selections: ITableRow[] = []
  private tableKey = +new Date()
  // 获取当前分页的数据
  private pagingData: ITableRow[] = []
  // 当前页选中项
  private selectionData: ITableRow[] = []
  // 跨页全选排除法数据ID集合
  private excludeDataIds: string[] = []
  private panelKeyFieldMap = {
    cpuData: 'cpu_usage',
    menmoryData: 'mem_usage',
    diskData: 'disk_in_use',
    unresolveData: 'alarm_count'
  }

  @Provide('tableInstance') private readonly tableStore = this.tableInstance

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (from.name !== 'performance-detail' && !vm.isLoading) {
        vm.initCondition()
        vm.handleInitColChecked()
        vm.getHostList()
      }
    })
  }

  private get bizList() {
    return this.$store.getters.bizList
  }
  private get checkType() {
    return this.tableInstance.checkType
  }

  // 0: 取消全选 1: 半选 2: 全选
  private get allCheckValue() {
    if (this.checkType === 'current') {
      if (this.selectionData.length === 0) {
        return 0
      } if (this.selectionData.length === this.pagingData.length) {
        return 2
      }
      return 1
    }
    if (this.excludeDataIds.length === 0) {
      return 2
    } if (this.excludeDataIds.length === this.tableInstance.total) {
      return 0
    }
    return 1
  }

  // 筛选面板统计信息
  private get panelStatistics(): IPanelStatistics {
    return {
      unresolveData: this.tableInstance.unresolveData.length,
      cpuData: this.tableInstance.cpuData.length,
      menmoryData: this.tableInstance.menmoryData.length,
      diskData: this.tableInstance.diskData.length
    }
  }

  // 字段显示设置
  private get fieldData() {
    return this.tableInstance.fieldData
  }

  // 表格列配置
  private get columns() {
    return this.tableInstance.columns
  }
  // 当前选中条数统计
  private get selectionsCount() {
    if (this.checkType === 'current') {
      return this.selectionData.length
    }
    return this.pageConfig.total - this.excludeDataIds.length
  }
  // 分页配置
  private get pageConfig(): IPageConfig {
    return {
      page: this.tableInstance.page,
      pageSize: this.tableInstance.pageSize,
      pageList: this.tableInstance.pageList,
      total: this.tableInstance.total
    }
  }

  private created() {
    this.initCondition()
    this.handleInitColChecked()
    this.getHostList()
  }

  private beforeRouteLeave(to: Route, from: Route, next: () => void) {
    if (to.name !== 'performance-detail') {
      // 除进入详情页外跳转其他的界面需要清空条件
      this.tableInstance.panelKey = ''
      this.tableInstance.fieldData.forEach((item) => {
        item.value = Array.isArray(item.value) ? [] : ''
      })
      PerformanceModule.setConditions()
    }
    next()
  }

  // 初始化回显条件
  private initCondition() {
    // 优先级：props > url > store
    let conditions: ISearchItem[] = []
    const searchArr = this.getRouteSearchQuery()
    const storeConditions = PerformanceModule.conditions
    if (this.search && this.search.length) {
      conditions = this.search
    } else if (searchArr) {
      conditions = searchArr
    } else if (storeConditions) {
      try {
        conditions = storeConditions
      } catch {
        console.error('parse store searchQuery error')
      }
    }
    conditions.forEach((item) => {
      const data = this.tableInstance.fieldData.find(data => data.id === item.id)
      if (data && !typeTools.isNull(item.value)) {
        data.value = item.value
        data.filterChecked = true
      }
    })
  }

  // 解析路由的query
  private getRouteSearchQuery(): ISearchItem[] {
    const searchStr = this.$route.query.search as string
    let arr = null
    searchStr && (arr = JSON.parse(searchStr))
    return arr
  }
  // 无状态数据
  private async getHostPerformance() {
    this.isLoading = true
    const hostData = await PerformanceModule.getHostPerformance()
    if (!this.tableInstance?.allData?.some?.(item => item?.status > 0)) {
      // 更新tableInstance
      this.tableInstance.updateData(hostData, {
        stickyValue: this.sticky.value,
        panelKey: ''
      })
      this.getTableData()
    }
    this.isLoading = false
  }
  // 获取主机信息
  private async getHostList() {
    console.time()
    this.isLoading = true
    const stickyList = await PerformanceModule.getUserConfigList({
      key: this.sticky.key
    })
    if (!stickyList.length) {
      // 如果用户配置不存在就创建配置
      PerformanceModule.createUserConfig({
        key: this.sticky.key,
        value: JSON.stringify({})
      }).then((data) => {
        this.sticky.id = data.id || -1
      })
    } else {
      // 获取当前用户的置顶配置
      try {
        this.sticky.id = stickyList[0].id
        this.sticky.value = JSON.parse(stickyList[0].value)
      } catch (_) {
        console.error('parse user stiky note error')
      }
    }
    await Promise.race([this.getHostPerformance(), this.getMetricHostList()])
    this.isLoading = false

    // 默默的加载带有指标信息的全量数据
    // this.getMetricHostList()
    this.$nextTick(() => {
      console.timeEnd()
    })
  }

  // 获取全部主机信息（性能问题，异步获取）
  private async getMetricHostList() {
    this.tableInstance.loading = true
    const hostData = await PerformanceModule.getHostPerformanceMetric()
    // 更新tableInstance
    this.tableInstance.updateData(hostData.hosts, {
      stickyValue: this.sticky.value,
      panelKey: ''
    })
    this.getTableData()
    this.tableInstance.loading = false
  }

  // 根据 localStorage 初始化字段显示配置
  private handleInitColChecked() {
    try {
      const storeCol = JSON.parse(localStorage.getItem(this.colStorageKey)) || {}

      Object.keys(storeCol).forEach((key) => {
        const index = this.tableInstance.fieldData.findIndex(item => item.id === key)
        if (index > -1) {
          this.tableInstance.fieldData[index].checked = true
        }
      })
    } catch {
      console.error('init col checked failed')
    }
  }

  // 筛选面板点击事件
  private handlePanelClick(key: string) {
    this.tableInstance.page = 1
    this.tableInstance.panelKey = key

    const fieldKey = this.panelKeyFieldMap[key]
    this.tableRef && this.tableRef.clearSort()
    if (fieldKey) {
      const fieldData = this.tableInstance.fieldData.find(item => item.id === fieldKey)
      // 默认展示筛选的列
      fieldData.checked = true
      this.tableRef && this.tableRef.sort({ prop: fieldKey, order: 'descending' })
    }
    // 切换panel无需更新分类数据
    this.handleSearchChange()
  }

  // 排序
  private handleSortChange({ prop, order }: ISort) {
    this.tableInstance.sortKey = prop
    this.tableInstance.order = order
    this.reOrderData()
  }

  // 每页条数
  private handleLimitChange(limit: number) {
    this.tableInstance.page = 1
    this.tableInstance.pageSize = limit
    this.handleSetCommonPageSize(String(limit))
    this.handleResetCheck()
    this.reLimitData()
  }

  // 分页
  private handlePageChange(page: number) {
    this.tableInstance.page = page
    this.checkType === 'current' && this.handleResetCheck()
    this.reLimitData()
  }

  // 搜索表更事项
  private handleSearchChange() {
    this.handleResetCheck()
    this.getTableData()
  }

  // 重置勾选项
  private handleResetCheck() {
    this.selectionData = []
    this.excludeDataIds = []
  }

  private async handleIpMark(row: ITableRow) {
    this.isLoading = true
    if (this.sticky.value[row.rowId]) {
      delete this.sticky.value[row.rowId]
    } else {
      this.sticky.value[row.rowId] = 1
    }
    const result = await PerformanceModule.updateUserConfig({
      id: this.sticky.id,
      value: JSON.stringify(this.sticky.value)
    })
    if (result) {
      const data = this.pagingData.find(item => item.rowId === row.rowId)
      this.tableInstance.stickyValue = this.sticky.value
      this.tableInstance.setState(row.rowId, 'mark', !data.mark)
      this.tableKey = +new Date()
      this.$nextTick(() => {
        this.handleSearchChange()
      })
    }
    this.isLoading = false
  }

  // 行勾选事件
  private handleRowCheck({ value, row }: { value: boolean, row: ITableRow }) {
    const { checkType } = this.tableInstance
    if (checkType === 'current') {
      if (value) {
        this.selectionData.push(row)
      } else {
        const index = this.selectionData.findIndex(item => item.rowId === row.rowId)
        index > -1 && this.selectionData.splice(index, 1)
      }
    } else {
      if (value) {
        const index = this.excludeDataIds.findIndex(id => id === row.rowId)
        index > -1 && this.excludeDataIds.splice(index, 1)
      } else {
        this.excludeDataIds.push(row.rowId)
      }
    }
  }

  // 全选或者取消全选
  private handleCheckChange({ value, type }: ICheck) {
    this.tableInstance.checkType = type
    this.selectionData = type === 'current' && value === 2 ? [...this.pagingData] : []
    this.excludeDataIds = []
    this.$nextTick(() => {
      this.tableRef.updateDataSelection()
    })
  }
  // 重新获取表格数据（耗时操作）
  private getTableData() {
    this.pagingData = this.tableInstance.getTableData()
  }
  // 重新分页数据
  private reLimitData() {
    this.pagingData = this.tableInstance.reLimitData()
  }
  // 重新排序缓存数据
  private reOrderData() {
    this.pagingData = this.tableInstance.reOrderData()
  }
}
</script>

<style lang="scss" scoped>
.performance {
  background: #fff;
  /deep/ * {
    .progress-bar {
      box-shadow: none;
    }
  }
  &.performance-laoding {
    min-height: calc(100vh - 80px)
  }
}
</style>
