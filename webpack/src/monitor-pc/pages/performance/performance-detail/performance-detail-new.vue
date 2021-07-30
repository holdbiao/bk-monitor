<template>
  <div class="performance-detail">
    <!-- 主机列表 -->
    <transition name="slide">
      <HostList
        v-bkloading="{ isLoading }"
        class="performance-detail-left"
        :cur-node="curNode"
        v-model="listVisible"
        v-show="listVisible"
        @node-change="handleNodeChange">
      </HostList>
    </transition>
    <!-- 内容区域 -->
    <div class="performance-detail-content">
      <!-- 工具栏 -->
      <ChartFilterTool
        :view-type="viewType"
        :chart-type="chartType"
        :groups-data="dashboardOrderList"
        :list-visible="listVisible"
        :detail-visible="detailVisible"
        :value="compareValue"
        :cur-node="curNode"
        :default-method="aggMethod"
        @tool-change="handleToolChange"
        @chart-change="handleChartChange"
        @show-list="handleShowList"
        @show-detail="handleShowDetail"
        @sort-change="handleSortChange"
        @view-change="handleViewChange"
        @immediate-reflesh="handleImmediateFeflesh"
        @search-change="handleSearchChange"
        @method-change="handleMethodChange">
      </ChartFilterTool>
      <!-- 图表 -->
      <ViewContent
        :groups-data="dashboardConfigList"
        :type="viewType"
        :chart-type="chartType"
        :loading="contentLoading"
        :cur-node="curNode"
        :compare-value="compareValue"
        :keyword="keyword"
        :method="aggMethod"
        @process-change="handleProcessChange">
      </viewcontent>
    </div>
    <!-- 主机详情 -->
    <transition name="slide">
      <HostDetail
        class="performance-detail-right"
        :data="curNode"
        v-model="detailVisible"
        v-show="detailVisible">
      </HostDetail>
    </transition>
  </div>
</template>
<script lang="ts">
import { Component, Prop, Watch, Mixins, Provide } from 'vue-property-decorator'
import HostList from './host-list.vue'
import ChartFilterTool from './chart-filter-tool.vue'
import HostDetail from './host-detail.vue'
import ViewContent from './view-content.vue'
import PerformanceModule, { ICurNode } from '../../../store/modules/performance'
import { IHostGroup, ViewType,
  IQueryOption, ChartType, IToolsOption, ICompareOption } from '../performance-type'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import { VIEW_AUTH as GRAFANA_VIEW_AUTH, MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../../grafana/authority-map'
import { MANAGE_AUTH } from '../authority-map'
import { PERFORMANCE_CHART_TYPE } from '../../../constant/constant'
import { chartType } from '../../data-retrieval'
const authorityMap = { MANAGE_AUTH, GRAFANA_VIEW_AUTH, GRAFANA_MANAGE_AUTH }
@Component({
  name: 'performance-detail',
  components: {
    HostList,
    ChartFilterTool,
    HostDetail,
    ViewContent
  }
})
export default class DetailTool extends Mixins(authorityMixinCreate(authorityMap)) {
  @Prop({ default: '' }) readonly id: string // 节点ID（主机：IP + 云区域， 节点：bk_inst_id + bk_obj_id）
  @Prop({ default: 'host', type: String }) type: 'host' | 'node' // 当前节点类型（主机或节点）
  @Prop({ default: 'host', type: String }) defaultViewType!: ViewType //
  @Prop({ type: Number, default: 0 }) readonly osType: number // 操作系统
  @Prop({ default: '' }) readonly processId: string // 进程
  @Prop({ default: '' }) readonly title: string // 进程
  @Provide('authority') authority
  @Provide('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Provide('authorityMap') authorityMap
  private listVisible = true
  private isLoading = false
  private detailVisible = true
  private chartType: ChartType = (+localStorage.getItem(PERFORMANCE_CHART_TYPE) % 3) as ChartType
  private contentLoading = false
  // 视图类型
  private viewType: ViewType = 'host'
  private compareValue: {compare: ICompareOption; tools: IToolsOption} = {
    compare: {
      type: 'none',
      value: ''
    },
    tools: {
      refleshInterval: -1,
      timeRange: 60 * 60 * 1000
    }
  }
  private keyword = ''
  private authorityMap = authorityMap
  private immediadateReflesh = 0
  private aggMethod = 'avg'
  // 分组数据
  get dashboardConfigList(): IHostGroup[] {
    const list  = this.viewType === 'host'
      ? PerformanceModule.dashboardConfigList
      : PerformanceModule.processDashboardConfigList
    const osTypeList = ['linux', 'windows', 'aix']
    const curOsType = !!this.osType ? osTypeList[this.osType - 1] : ''
    const targetList = list.map((item) => {
      if (item.type === 'row') {
        return {
          ...item,
          panels: item.panels.filter(child => !child.os_type || !curOsType || child.os_type.includes(curOsType))
        }
      }
      return {
        ...item,
        targets: item.targets.filter(child => !child.os_type || !curOsType || child.os_type.includes(curOsType))
      }
    })
    return targetList.map((item) => {
      if (item.type === 'row') {
        return {
          ...item,
          panels: item.panels.map(child => ({
            ...child,
            key: JSON.stringify(child.targets)
            + JSON.stringify(this.compareValue.tools.timeRange)
             + JSON.stringify(this.curNode)
             + this.immediadateReflesh
          })),
          key: item.id
        }
      }
      return {
        ...item,
        key: JSON.stringify(item.targets)
        + JSON.stringify(this.compareValue.tools.timeRange)
        + JSON.stringify(this.curNode)
      }
    })
  }
  get dashboardOrderList(): IHostGroup[] {
    return this.viewType === 'host'
      ? PerformanceModule.dashboardHostOrderList
      : PerformanceModule.dashboardProcessOrderList
  }
  // 主机列表数据
  get hosts() {
    return PerformanceModule.hosts
  }
  // 主机指标数据
  get hostIndex() {
    return PerformanceModule.list
  }
  get curNode() {
    return PerformanceModule.curNode
  }

  @Watch('id', { immediate: true })
  async handleIdChange(v) {
    if (v) {
      await this.$nextTick()
      if (this.type === 'host') {
        // 主机类型
        const [ip, cloudId = -1] = this.id.split('-')
        PerformanceModule.setCurNode({
          id: this.id,
          type: this.type,
          ip,
          cloudId,
          osType: this.osType,
          processId: this.processId
        })
        // 云区域不存在时从全部IP中找到第一个相同IP的云区域作为ID
        cloudId === -1 && await PerformanceModule.getHostPerformance()
      } else {
        // 节点类型
        const [bkInstId, bkObjId] = this.id.split('-')
        PerformanceModule.setCurNode({
          id: this.id,
          type: this.type,
          bkInstId,
          bkObjId,
          osType: this.osType,
          processId: this.processId
        })
      }
      PerformanceModule.setProcessList([])
      PerformanceModule.SET_PERFORMANCE_HOST([])
      this.handleViewChange(this.viewType)
    }
  }
  @Watch('processId', { immediate: true })
  onProcessIdChange(v) {
    if (!!v) {
      this.viewType = 'process'
      PerformanceModule.setProcessId(v)
    }
  }
  created() {
    this.viewType = this.defaultViewType
  }
  //   beforeRouteEnter(to, from, next) {
  //     next(async (vm) => {
  //       if (from.name !== 'view-detail') {
  //         !vm.contentLoading && vm.handleIdChange(vm.id)
  //       }
  //     })
  //   }
  activated() {
    this.chartType = (+localStorage.getItem(PERFORMANCE_CHART_TYPE) % 3) as chartType
  }
  handleImmediateFeflesh() {
    this.immediadateReflesh = Date.now()
  }
  handleShowList(v: boolean) {
    this.listVisible = v
  }

  handleShowDetail(v: boolean) {
    this.detailVisible = v
  }

  async handleNodeChange(data: ICurNode) {
    if (this.curNode.id === data.id) return

    // 清空对比信息
    this.compareValue.compare = {
      type: 'none',
      value: ''
    }
    // 路由跳转
    this.$router.replace({
      name: 'performance-detail',
      params: {
        title: data.type === 'host' ? data.ip : '',
        id: data.id,
        osType: String(data.osType ? Number(data.osType) : 0)
      },
      query: {
        type: data.type
      }
    })

    // PerformanceModule.setCurNode({ ...data })
    // if (this.viewType === 'process') {
    //   PerformanceModule.setProcessList([])
    // }
    // this.handleViewChange(this.viewType, false)
    // this.$store.commit('app/SET_NAV_TITLE', data.type === 'host' ? data.ip : data.id)
  }
  // 排序保存
  handleSortChange() {
    this.handleViewChange(this.viewType)
  }
  // 获取compare-config参数
  handleGetCompareParams() {
    const { compare: { value, type } } = this.compareValue
    const compareParams: any = { type }
    if (type === 'time') {
      compareParams.time_offset = value || ['1h']
    } else if (type === 'target') {
      compareParams.hosts = Array.isArray(value) ? value.map((item) => {
        const val = item.split('-')
        return {
          bk_target_ip: val[1],
          bk_target_cloud_id: val[0]
        }
      }) : []
    }
    return compareParams
  }
  async handleViewChange(view: ViewType, needGetConfig = true) {
    const promiseList = []
    this.viewType = view
    // if (view === 'process') {
    //   const { compare } = this.compareValue
    //   if (compare.type === 'target') {
    //     compare.type = 'none'
    //     compare.value = ''
    //   }
    // }
    if (!this.hosts.length) {
      this.isLoading = true
      promiseList.push(PerformanceModule.getHostPerformance())
    }
    this.contentLoading = true
    // const needSetConfigEmpty = !this.dashboardConfigList.length && needRelesh
    if (view === 'host') {
      if (needGetConfig) {
        PerformanceModule.setHostConfigList([])
        promiseList.push(PerformanceModule.getHostDashboardConfig({ type: view,
          compare_config: this.handleGetCompareParams() }))
      }
    } else if (view === 'process') {
      PerformanceModule.setProcessConfigList([])
      if (!PerformanceModule.curProcessList?.length) {
        const params = this.curNode.type === 'host'
          ? {
            bk_cloud_id: this.curNode.cloudId,
            ip: this.curNode.ip
          }
          : {
            bk_obj_id: this.curNode.bkObjId,
            bk_inst_id: this.curNode.bkInstId
          }
        await PerformanceModule.getProcessDetail(params)
      }
      if (PerformanceModule.curProcessList?.length) {
        promiseList.push(PerformanceModule.getHostDashboardConfig({ type: view,
          compare_config: this.handleGetCompareParams() }))
      }
    }
    await Promise.all(promiseList)
    this.isLoading = false
    this.contentLoading = false
  }
  handleToolChange(parmas: IQueryOption) {
    this.compareValue = parmas
    !['interval', 'timeRange'].includes(parmas.type) && this.handleViewChange(this.viewType)
  }
  // 图表类型切换触发
  handleChartChange(chartType: ChartType) {
    this.chartType = chartType
  }
  handleProcessChange() {

  }
  handleSearchChange(v: string) {
    this.keyword = v
  }
  handleMethodChange(method: string) {
    this.aggMethod = method
    this.handleImmediateFeflesh()
  }
}
</script>
<style lang="scss" scoped>
.performance-detail {
  display: flex;
  background: #fafbfd;
  height: 100%;
  overflow: hidden;
  &-left {
    // flex: 0 0 280px;
    background: #fff;
    // width: 380px;
  }
  &-content {
    flex: 1;
    min-width: 620px;
  }
  &-right {
    flex: 0 0 280px;
    background: #fff;
    width: 280px;
  }
}
.slide-enter-active,
.slide-leave-active {
  transition: all .25s ease;
}
.slide-enter,
.slide-leave-to {
  &.performance-detail-left {
    transform: translateX(-100%);
  }
  &.performance-detail-right {
    transform: translateX(100%);
  }
}
</style>
