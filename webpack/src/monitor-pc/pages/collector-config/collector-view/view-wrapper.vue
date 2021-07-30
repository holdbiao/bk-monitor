<template>
  <div class="view-wrapper">
    <!-- 工具栏 -->
    <compare-panel
      :need-search-select="true"
      :need-split="false"
      :search-select-list="searchSelectList"
      :value="compareValue"
      :reflesh-list="refleshList"
      :timerange-list="timerangeList"
      :chart-type="chartType"
      :target-list="targetList"
      :timeshift-list="timeshiftList"
      :cur-host="curHost"
      :compare-list="compareList"
      @add-timerange-option="addTimerangeOption"
      @add-timeshift-option="addTimeshiftOption"
      @change="handleChangeCompare"
      @chart-change="handleChartChange"
      @on-immediate-reflesh="handleImmediateReflesh">
      <template #append>
        <span
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="chart-tool-setting"
          @click="authority.MANAGE_AUTH ? handleShowChartSort() : handleShowAuthorityDetail(authorityMap.MANAGE_AUTH)">
          <i class="icon-monitor icon-setting"></i>
        </span>
      </template>
      <template #pre>
        <span class="tool-icon right" v-show="!leftShow" @click="handleLeftShow">
          <i class="arrow-right icon-monitor icon-double-up"></i>
        </span>
        <div class="tool-method" v-if="viewType === 'topo_node'">
          <span class="label">{{ $t('汇聚') }}：</span>
          <drop-down-menu class="content" v-model="method" :list="aggMethods" @change="handleAggMethodChange"></drop-down-menu>
        </div>
      </template>
    </compare-panel>
    <!-- 图表组件 -->
    <dashboard-panels
      class="dashboard-wrapper"
      :groups-data="handleGroupsData"
      :variable-data="variableData"
      :compare-value="compareValue"
      :chart-option="chartOption"
      :chart-type="chartType">
    </dashboard-panels>
    <!-- 图表排序组件 -->
    <sort-panel
      v-model="showChartSort"
      :groups-data="orderList"
      :need-group="true"
      @save="handleSortChange"
      @undo="handleUndo">
    </sort-panel>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Emit, Watch, Inject } from 'vue-property-decorator'
import ComparePanel from '../../performance/performance-detail/compare-panel.vue'
import SortPanel from '../../performance/performance-detail/sort-panel.vue'
import { IQueryOption,
  ChartType,
  IHostGroup,
  ISearchSelectList,
  IOption,
  ICompareOption } from '../../performance/performance-type'
import { IDetailInfo, IVariableData } from '../collector-config-type'
import DashboardPanels from '../../performance/performance-detail/dashboard-panels.vue'
import PerformanceModule from '../../../store/modules/performance'
import { deepClone } from '../../../../monitor-common/utils/utils'
import { COLLECT_CHART_TYPE } from '../../../constant/constant'
import DropDownMenu from '../../performance/performance-detail/dropdown-menu.vue'
@Component({
  name: 'view-wrapper',
  components: {
    ComparePanel,
    SortPanel,
    DashboardPanels,
    DropDownMenu
  }
})
export default class ViewWrapper extends Vue {
  // 图表所需数据
  @Prop({ default: () => [], type: Array }) readonly groupsData: any
  // 图表渲染变量
  @Prop({ default: null, type: Object }) readonly variableData: IVariableData
  // 排序数据
  @Prop({ default: () => [], type: Array }) readonly orderList: any
  // 采集详情
  @Prop({ required: true, type: Object }) readonly detailInfo: IDetailInfo
  // 搜索下拉选择数据
  @Prop({ default: () => [], required: true, type: Array }) readonly searchSelectList: ISearchSelectList[]
  // 目标数据
  @Prop({ default: () => [], type: Array }) readonly targetList: IOption
  // 展开左侧操作栏
  @Prop({ required: true, default: false, type: Boolean }) readonly leftShow: boolean
  // 对比数据
  @Prop({ default: () => ({ type: 'none', value: '' }), type: Object }) readonly compare: ICompareOption
  // 当前调用的路由页面
  @Prop({ type: String }) readonly routeType: 'collect' | 'custom'
  @Prop({ type: Object }) readonly curHost
  @Prop({ default: 'leaf_node', type: String }) readonly viewType: 'leaf_node' | 'topo_node' | 'overview'
  @Prop({ default: 'avg', type: String }) readonly defaultMethod!: string

  @Inject('authority') authority
  @Inject('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Inject('authorityMap') authorityMap
  private compareValue: IQueryOption = {
    compare: { type: 'none', value: '' },
    tools: {
      timeRange: 1 * 60 * 60 * 1000,
      refleshInterval: -1,
      searchValue: []
    }
  }

  private chartOption: any = {
    annotation: {
      show: true,
      list: ['strategy']
    }
  }

  private showChartSort = false

  private timerangeList: IOption[] = []
  private refleshList: IOption[] = [
    {
      name: window.i18n.t('刷新'),
      id: -1
    },
    {
      name: '1m',
      id: 60 * 1000
    },
    {
      name: '5m',
      id: 5 * 60 * 1000
    },
    {
      name: '15m',
      id: 15 * 60 * 1000
    },
    {
      name: '30m',
      id: 30 * 60 * 1000
    },
    {
      name: '1h',
      id: 60 * 60 * 1000
    },
    {
      name: '2h',
      id: 60 * 2 * 60 * 1000
    },
    {
      name: '1d',
      id: 60 * 24 * 60 * 1000
    }
  ]
  private timeshiftList: IOption[] = [
    {
      id: '1h',
      name: window.i18n.t('1小时前')
    },
    {
      id: '1d',
      name: window.i18n.t('昨天')
    },
    {
      id: '1w',
      name: window.i18n.t('上周')
    },
    {
      id: '1M',
      name: window.i18n.t('一月前')
    }
  ]
  private chartType: ChartType =  +localStorage.getItem(COLLECT_CHART_TYPE) % 3

  private sortLoading = false

  private searchTypeMap: string[] = []
  private aggMethods: IOption[] = [
    {
      id: 'AVG',
      name: 'AVG'
    },
    {
      id: 'SUM',
      name: 'SUM'
    },
    {
      id: 'MIN',
      name: 'MIN'
    },
    {
      id: 'MAX',
      name: 'MAX'
    }
  ]
  private method = this.defaultMethod

  @Watch('compare')
  handleCompareValue() {
    this.compareValue.compare = this.compare
  }

  get compareList() {
    const list = [
      {
        id: 'none',
        name: this.$t('不对比')
      },
      {
        id: 'time',
        name: this.$t('时间对比')
      }
    ]

    if (this.viewType !== 'topo_node') {
      list.push({
        id: 'target',
        name: this.$t('目标对比')
      })
    }
    return list
  }

  get handleGroupsData() {
    const data = deepClone(this.groupsData)
    if (!data.length) return []
    const len = this.searchTypeMap.length
    if (len && this.groupsData.length) {
      data.forEach((item) => {
        item.panels = item.panels.filter((pan) => {
          const arr = this.searchTypeMap[0].split('.')
          const tar = pan.id.split('.')
          let hidden = false
          if (this.routeType === 'collect') {
            if  (arr.length > 1) {
              !(tar[0].indexOf(arr[0]) > -1 && tar[1].indexOf(arr[1]) > -1) && (hidden = true)
            } else {
              !(tar[1].indexOf(arr[0]) > -1) && (hidden = true)
            }
          } else {
            !(pan.title.indexOf(arr[0]) > -1) && (hidden = true)
          }
          return !hidden
        })
      })
    }
    return data
  }

  created() {
    this.timerangeList = [
      {
        name: `${this.$t('近{n}分钟', { n: 5 })}`,
        value: 5 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}分钟', { n: 15 })}`,
        value: 15 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}分钟', { n: 30 })}`,
        value: 30 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}小时', { n: 1 })}`,
        value: 1 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}小时', { n: 3 })}`,
        value: 3 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}小时', { n: 6 })}`,
        value: 6 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}小时', { n: 12 })}`,
        value: 12 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}小时', { n: 24 })}`,
        value: 24 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}天', { n: 2 })}`,
        value: 2 * 24 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}天', { n: 7 })}`,
        value: 7 * 24 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('近{n}天', { n: 30 })}`,
        value: 30 * 24 * 60 * 60 * 1000
      },
      {
        name: `${this.$t('今天1')}`,
        value: 'today'
      },
      {
        name: `${this.$t('昨天1')}`,
        value: 'yesterday'
      },
      {
        name: `${this.$t('前天1')}`,
        value: 'beforeYesterday'
      },
      {
        name: `${this.$t('本周1')}`,
        value: 'thisWeek'
      }
    ]
  }

  // 点击显示左侧栏
  @Emit('show-left')
  handleLeftShow() {
    return !this.leftShow
  }

  // 图表排序
  handleShowChartSort() {
    this.showChartSort = true
  }

  handleChangeCompare(v: IQueryOption) {
    this.compareValue = v
    if (v.type === 'compare' || v.type === 'timeRange') {
      this.$emit('on-compare-change', v)
    } else if (v.type === 'search') {
      if (v.tools.searchValue.length) {
        v.tools.searchValue.forEach((item) => {
          if (item.values) {
            item.values.forEach((v) => {
              if (!this.searchTypeMap.includes(`${item.id}.${v.id}`)) {
                this.searchTypeMap.push(`${item.id}.${v.id}`)
              }
            })
          } else {
            if (!this.searchTypeMap.includes(item.id)) {
              this.searchTypeMap.push(item.id)
            }
          }
        })
      } else {
        this.searchTypeMap = []
      }
    }
  }

  //   // 获取compare-config参数
  //   handleGetCompareParams() {
  //     const { compare: { value, type } } = this.compareValue
  //     const compareParams: any = { type }
  //     if (type === 'time') {
  //       compareParams.time_offset = value || '1h'
  //     } else if (type === 'target') {
  //       if (this.detailInfo.targetObjectType === 'HOST') {
  //         compareParams.hosts = Array.isArray(value) ? value.map((item) => {
  //           const val = item.split('-')
  //           return {
  //             bk_target_ip: val[1],
  //             bk_target_cloud_id: val[0]
  //           }
  //         }) : []
  //       } else if (this.detailInfo.targetObjectType === 'SERVICE') {
  //         compareParams.service_instance_ids = Array.isArray(value) ? value.map((item) => {
  //           const val = item.split('-')
  //           return {
  //             bk_target_instance_id: val[0]
  //           }
  //         }) : []
  //       }
  //     }
  //     return compareParams
  //   }

  handleChartChange(v: ChartType) {
    this.chartType = v
  }

  @Emit('sort-change')
  async handleSortChange(data: IHostGroup[]) {
    let id
    if (this.routeType ===  'collect') {
      id = `collect_config_${this.detailInfo.id}`
    } else {
      id = `custom_report_${this.$route.params.id}`
    }
    this.sortLoading = true
    const success = await PerformanceModule.saveDashboardOrder({
      order: data,
      id
    })
    this.sortLoading = false
    if (success) {
      this.showChartSort = false
    }
  }

  @Emit('sort-change')
  async handleUndo() {
    this.sortLoading = true
    const success = await PerformanceModule.deletePanelOrder(`collect_config_${this.detailInfo.id}`)
    this.sortLoading = false
    if (success) {
      this.showChartSort = false
    }
  }

  addTimeshiftOption(val: string) {
    this.timeshiftList.push({
      id: val,
      name: val
    })
  }

  addTimerangeOption(val: IOption) {
    this.timerangeList.push(val)
  }

  @Emit('on-immediate-reflesh')
  handleImmediateReflesh() {}

  @Emit('method-change')
  handleAggMethodChange() {
    return this.method
  }
}

</script>

<style lang="scss" scoped>
.view-wrapper {
  height: 100%;
  .dashboard-wrapper {
    height: calc(100% - 42px);
    padding: 16px;
    overflow-y: scroll;
  }
  .chart-tool-setting {
    width: 48px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #979ba5;
    cursor: pointer;
    border-left: 1px solid #f0f1f5;
  }
  .tool-icon {
    width: 48px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #979ba5;
    cursor: pointer;
    border-left: 1px solid #f0f1f5;
    &.right {
      border-right: 1px solid #f0f1f5;
    }
    .arrow-right {
      font-size: 24px;
      color: #979ba5;
      cursor: pointer;
      transform: rotate(90deg);
    }
  }
  .tool-method {
    padding-left: 14px;
    border-right: 1px solid #f0f1f5;
  }
}
</style>
