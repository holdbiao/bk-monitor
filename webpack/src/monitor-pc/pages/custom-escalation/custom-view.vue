<template>
  <div
    v-bkloading="{ 'isLoading': pageLoading }"
    class="collector-view-wrapper">
    <!-- 左侧区域 -->
    <div
      :style="{ 'flex-basis': drag.width + 'px', width: drag.width + 'px' }"
      class="left-container"
      data-tag="resizeTarget">
      <div
        class="resize-line"
        @mousedown="handleMouseDown">
      </div>
      <control-wrapper
        ref="controlRef"
        :id="id"
        :name="name"
        :route-type="routeType"
        :detail-info="detailInfo"
        :host-topo-status="hostTopoStatus"
        @on-task-change="handleTaskChange"
        @on-target-list-change="handleTargetChange"
        @on-select-node="handleSelectNode">
      </control-wrapper>
    </div>
    <!-- 右侧图表区域 -->
    <div
      :style="{ 'flex-basis': `calc(100% - ${drag.width}px)`, width: `calc(100% - ${drag.width}px)` }"
      class="right-container">
      <view-wrapper
        :key="viewKey"
        :order-list="orderData"
        :variable-data="variableData"
        :groups-data="dashboardConfigList"
        :detail-info="detailInfo"
        :search-select-list="typeList"
        :target-list="handleTargetList"
        :left-show="drag.width !== 0"
        :compare="compare"
        :route-type="routeType"
        :cur-host="curHost"
        @show-left="drag.width = 270"
        @sort-change="handleSortChange"
        @on-compare-change="handleCompareChange"
        @on-immediate-reflesh="handleImmediateReflesh">
      </view-wrapper>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Ref, Mixins, Provide } from 'vue-property-decorator'
import { collectConfigDetail } from '../../../monitor-api/modules/collecting'
import { getCustomReportDashboardConfig } from '../../../monitor-api/modules/custom_report'
import { transformDataKey, random } from '../../../monitor-common/utils/utils'
import { IDrag, IDetailInfo, IHostTopoStatus
  , IVariableData, ITargetList } from '../collector-config/collector-config-type'
import viewWrapper from '../collector-config/collector-view/view-wrapper.vue'
import controlWrapper from '../collector-config/collector-view/control-wrapper.vue'
import { IHostGroup, ISearchSelectList, IGroupItem } from '../performance/performance-type'
import  authorityMixinCreate from '../../mixins/authorityMixin'
import { MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../grafana/authority-map'
import { MANAGE_CUSTOM_METRIC as MANAGE_AUTH } from './authority-map'
const authMap = {
  GRAFANA_MANAGE_AUTH,
  MANAGE_AUTH
}
@Component({
  name: 'custom-escalation-view',
  components: {
    viewWrapper,
    controlWrapper
  }
})
export default class CollectorView extends  Mixins(authorityMixinCreate(authMap)) {
  // 路由参数 id、 name
  @Prop({ default: '', required: true }) readonly id: string | number
  @Prop({ default: '' }) readonly name: string | number
  @Ref('controlRef') readonly controlRef: controlWrapper

  @Provide('authority') authority
  @Provide('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Provide('authorityMap') authorityMap
  private viewKey = random(8)
  private routeType = 'custom'
  // 拖动配置数据
  private drag: IDrag = {
    width: 270,
    minWidth: 100,
    maxWidth: 500
  }

  private dataInitialized = false
  private isKeepAlive = false
  private pageLoading = false
  private detailInfo: IDetailInfo = {}
  private variableData: IVariableData = null
  private configListData: IHostGroup[] = []
  private orderData: IHostGroup[] = []
  private typeList: ISearchSelectList[] = []
  private targetList: any = []
  private curHost = null
  private compare: any = {
    type: 'none',
    value: ''
  }
  private immediateReflesh = 0
  private timeRange = ''
  private isOverview = true

  // 处理图表数据
  get dashboardConfigList(): IHostGroup[] {
    const list = this.configListData || []
    return list.map((item: IHostGroup) => {
      if (item.type === 'row') {
        return {
          ...item,
          panels: item.panels.map((child: IGroupItem) => ({
            ...child,
            key: random(8) + this.immediateReflesh
        + JSON.stringify(this.timeRange)
        + JSON.stringify(this.variableData)
          })),
          key: item.id
        }
      }
      return {
        ...item,
        key: random(8) + this.immediateReflesh
        + JSON.stringify(this.timeRange)
        + JSON.stringify(this.variableData)
      }
    })
  }

  // 主机、topo展示状态
  get hostTopoStatus(): IHostTopoStatus {
    return {
      host: false,
      topo: false
    }
  }

  get handleTargetList(): ITargetList[] {
    const cacheList: ITargetList[] = []
    const value = this.variableData ? this.variableData.$target : ''
    const list = this.targetList.filter(item => (item !== value)).map(item => ({
      id: item,
      name: item
    }))

    list.forEach((item) => {
      if (!cacheList.some(so => so.id === item.id)) {
        cacheList.push(item)
      }
    })
    return cacheList
  }

  // get viewKey(): string {
  //   let key = 'viewKey'
  //   if (this.id) {
  //     key = random(8)
  //   }
  //   return key
  // }


  @Watch('id')
  handleIdChange(v, ov) {
    if (+v !== +ov) {
      this.initData()
      this.viewKey = random(8)
    }
  }

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.isOverview = true
      if (from.name !== 'view-detail') {
        !vm.dataInitialized && vm.initData()
      } else {
        !vm.isKeepAlive && vm.initData()
      }
    })
  }

  mounted() {
    this.isKeepAlive = true
  }

  async initData() {
    this.curHost = null
    this.dataInitialized = false
    await this.$nextTick()
    // 初始化左侧操作栏数据
    this.controlRef.initData()
    // 查询视图配置
    this.handleQuery()
  }

  // drag触发
  handleMouseDown(e) {
    let { target } = e
    while (target && target.dataset.tag !== 'resizeTarget') {
      target = target.parentNode
    }
    const rect = target.getBoundingClientRect()
    document.onselectstart = function () {
      return false
    }
    document.ondragstart = function () {
      return false
    }
    const handleMouseMove = (event) => {
      if (event.clientX - rect.left < this.drag.minWidth) {
        this.drag.width = 0
      } else {
        this.drag.width = Math.min(Math.max(this.drag.minWidth, event.clientX - rect.left), this.drag.maxWidth)
      }
    }
    const handleMouseUp = () => {
      document.body.style.cursor = ''
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.onselectstart = null
      document.ondragstart = null
    }
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // 获取详情信息
  getInfo(): Promise<any> {
    return new Promise((resolve, reject) => {
      this.pageLoading = true
      collectConfigDetail({ id: this.$route.params.id }).then((data) => {
        this.detailInfo = transformDataKey(data)
        this.typeList = this.detailInfo.pluginInfo.metricJson.map(item => ({
          name: item.tableName,
          id: item.tableName
        }))
        resolve(data)
      })
        .catch((err) => {
          reject(err)
        })
        .finally(() => {
          this.pageLoading = false
        })
    })
  }

  handleCompareChange(compare) {
    this.compare = compare.compare
    const map = ['timeRange', 'interval']
    if (!map.includes(compare.type)) {
      this.handleQuery()
    } else if (compare.type === 'timeRange') {
      this.timeRange = compare.tools.timeRange
    }
  }

  // 查询视图配置
  async handleQuery() {
    await this.$nextTick()
    const params  = {
      view_type: this.controlRef.host.active === null ? 'overview' : 'leaf_node',
      id: this.id,
      compare_config: this.handleGetCompareParams(this.compare)
    }
    getCustomReportDashboardConfig(params, { needRes: true }).then(({ data, tips }) => {
      if (tips?.length) {
        this.$bkMessage({
          theme: 'warning',
          message: tips
        })
      }
      this.configListData = data.panels
      this.orderData = data.order
    })
  }
  // 选择节点
  handleSelectNode(host) {
    let variableData: IVariableData = null

    if (host === null) {
      this.curHost = null
      this.compare.value = []
      this.isOverview = true
      this.handleQuery()
      return
    }
    variableData = {
      $target: host
    }
    if (this.isOverview) {
      this.configListData = []
      this.isOverview = false
      this.variableData = variableData
      this.handleQuery()
    } else {
      this.variableData = variableData
    }
    if (Array.isArray(this.compare.value)) {
      const value = variableData.$target
      const index = this.compare.value.indexOf(value)
      index !== -1 && this.compare.value.splice(index, 1)
    }
    this.curHost = {
      ip: host,
      type: 'custom'
    }
  }

  handleSortChange() {
    this.handleQuery()
  }

  handleTargetChange(list: any) {
    this.targetList = list
  }

  handleTaskChange() {
    this.isOverview = true
    this.compare = { type: 'none', value: '' }
    this.variableData = null
  }

  // 获取compare-config参数
  handleGetCompareParams(compareParam) {
    if (!compareParam) return
    const { value, type } = compareParam
    const compareParams: any = { type }
    if (type === 'time') {
      compareParams.time_offset = value || '1h'
    } else if (type === 'target') {
      compareParams.targets = Array.isArray(value) ? value : []
      if (this.curHost !== null) {
        compareParams.targets = compareParams.targets.filter(item => (this.curHost.ip !== item))
      }
    }
    return compareParams
  }

  handleImmediateReflesh() {
    this.immediateReflesh = Date.now()
    // this.handleQuery()
  }
}

</script>

<style lang="scss" scoped>
.collector-view-wrapper {
  display: flex;
  flex-direction: row;
  height: calc(100vh - 52px);
  overflow: hidden;
  background-color: #f5f6fa;
  .left-container {
    position: relative;
    flex: 0 0 270px;
    background: #fff;
    border-right: 1px solid #f0f1f5;
    overflow: hidden;
    // z-index: 10;
    .resize-line {
      right: 0;
      background: none;
      cursor: col-resize;
    }
  }
  .right-container {
    flex: 1;
    z-index: 1;
    // overflow-y: auto;
  }
}

// 左侧栏动画
.task-list-enter-active,
.task-list-leave-active {
  transition: all .3s ease-in-out;
}
.task-list-enter,
.task-list-leave-to {
  transform: translateX(-100%);
  //   opacity: .5;
}
</style>
