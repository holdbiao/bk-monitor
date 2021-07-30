<template>
  <div class="chart-tool">
    <ComparePanel
      @change="handleToolChange"
      @chart-change="handleChartChange"
      @add-timerange-option="handleAddTimeRangeOption"
      @add-timeshift-option="handleAddTimeshifOption"
      @on-immediate-reflesh="handleImmediateReflesh"
      :value="value"
      :chart-type="chartType"
      :compare-list="compareList"
      :target-list="targetList"
      :timeshift-list="timeshiftList"
      :timerange-list="timerangeList"
      :need-split="needSplit"
      :need-search-select="true"
      :cur-host="curNode">
      <template #pre>
        <span class="tool-icon right" v-show="!listVisible" @click="handleShowList">
          <i class="arrow-right icon-monitor icon-double-up"></i>
        </span>
        <div class="chart-tool-left bk-button-group">
          <bk-button
            :class="{ 'is-selected': viewType === 'host' }"
            @click="handleViewChange('host')">
            {{ $t('主机') }}
          </bk-button>
          <bk-button
            :class="{ 'is-selected': viewType === 'process' }"
            @click="handleViewChange('process')">
            {{ $t('进程') }}
          </bk-button>
        </div>
        <div class="chart-tool-agg" v-if="curNode.type === 'node'">
          <span class="label">{{ $t('汇聚') }}：</span>
          <drop-down-menu class="content" v-model="method" :list="aggMethods" @change="handleAggMethodChange"></drop-down-menu>
        </div>
      </template>
      <template #search>
        <div class="tool-search">
          <i class="bk-icon icon-search tool-search-icon"></i>
          <input
            :style="{ width: search.focus || search.value ? '140px' : '40px' }"
            class="tool-search-input"
            @focus="search.focus = true"
            @blur="search.focus = false"
            :placeholder="$t('搜索')"
            v-model="search.value"
            @input="searchFn" />
        </div>
      </template>
      <template #append>
        <div class="chart-tool-right">
          <span
            v-if="groupsData.length"
            v-authority="{ active: !authority.MANAGE_AUTH }"
            class="tool-icon"
            @click="authority.MANAGE_AUTH ? handleSettingChart() : handleShowAuthorityDetail(authorityMap.MANAGE_AUTH)">
            <i class="icon-monitor icon-setting"></i>
          </span>
          <span class="tool-icon" v-show="!detailVisible" @click="handleShowDetail">
            <i class="arrow-left icon-monitor icon-double-up"></i>
          </span>
        </div>
      </template>
    </ComparePanel>
    <SortPanel
      v-if="groupsData.length"
      v-model="showSetting"
      :groups-data="groupsData"
      @save="handleSortChange"
      @undo="handleUndo"
      :loading="sortLoading"
      :need-group="viewType === 'host'">
    </SortPanel>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop, Inject } from 'vue-property-decorator'
import { IHostGroup, IOption, ICompareOption, IToolsOption, ViewType } from '../performance-type'
import SortPanel from './sort-panel.vue'
import ComparePanel from './compare-panel.vue'
import PerformanceModule, { ICurNode } from '../../../store/modules/performance'
import { debounce } from 'throttle-debounce'
import DropDownMenu from './dropdown-menu.vue'
@Component({
  name: 'chart-filter-tool',
  components: {
    SortPanel,
    ComparePanel,
    DropDownMenu
  }
})
export default class ChartFilterTool extends Vue {
  @Prop({ default: () => [], type: Array }) readonly groupsData: IHostGroup[]
  @Prop({ default: true }) readonly listVisible: boolean
  @Prop({ default: true }) readonly detailVisible: boolean
  @Prop({ default: false }) readonly needSplit: boolean
  @Prop({ default: 0 }) readonly chartType: 0 | 1 | 2
  @Prop({ required: true }) readonly viewType: ViewType
  @Prop({ required: true }) readonly value: {compare: ICompareOption; tools: IToolsOption}
  @Prop({ required: true }) readonly curNode: ICurNode
  @Prop({ type: String, default: '' }) readonly defaultMethod!: string

  @Inject('authority') authority
  @Inject('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Inject('authorityMap') authorityMap
  private showSetting = false
  private sortLoading = false
  // private compareList: IOption[] = []
  private timeshiftList: IOption[] = []
  private timerangeList: IOption[] = []
  private search: {focus: false; value: string} = { focus: false, value: '' }
  private searchFn: Function = null
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
  // 主机IP列表
  get targetList() {
    if (this.curNode.type === 'node') return []

    return PerformanceModule.hosts.map(item => ({ id: `${item.bk_cloud_id}-${item.bk_host_innerip}`,
      name: item.bk_host_innerip })).filter(item => item.id !== `${this.curNode.cloudId}-${this.curNode.ip}`)
  }
  created() {
    this.timerangeList = [
      {
        name: this.$t('近{n}分钟', { n: 5 }),
        value: 5 * 60 * 1000
      },
      {
        name: this.$t('近{n}分钟', { n: 15 }),
        value: 15 * 60 * 1000
      },
      {
        name: this.$t('近{n}分钟', { n: 30 }),
        value: 30 * 60 * 1000
      },
      {
        name: this.$t('近{n}小时', { n: 1 }),
        value: 1 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}小时', { n: 3 }),
        value: 3 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}小时', { n: 6 }),
        value: 6 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}小时', { n: 12 }),
        value: 12 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}小时', { n: 24 }),
        value: 24 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}天', { n: 2 }),
        value: 2 * 24 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}天', { n: 7 }),
        value: 7 * 24 * 60 * 60 * 1000
      },
      {
        name: this.$t('近{n}天', { n: 30 }),
        value: 30 * 24 * 60 * 60 * 1000
      },
      {
        name: this.$t('今天1'),
        value: 'today'
      },
      {
        name: this.$t('昨天1'),
        value: 'yesterday'
      },
      {
        name: this.$t('前天1'),
        value: 'beforeYesterday'
      },
      {
        name: this.$t('本周1'),
        value: 'thisWeek'
      }
    ]
    this.timeshiftList = [
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
    this.searchFn = debounce(300, false, this.handleSearchValueChange)
  }
  get compareList(): IOption[] {
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

    if (this.curNode?.type === 'host') {
      list.push({
        id: 'target',
        name: this.$t('目标对比')
      })
    }
    // if (this.viewType === 'host') {
    //   list.push({
    //     id: 'target',
    //     name: this.$t('目标对比')
    //   })
    // }
    return list
  }
  @Emit('view-change')
  handleViewChange(v) {
    return v
  }

  @Emit('tool-change')
  handleToolChange(params) {
    return params
  }

  // 图表设置
  handleSettingChart() {
    this.showSetting = true
  }
  // 显示左侧主机列表
  @Emit('show-list')
  handleShowList() {
    return true
  }

  @Emit('show-detail')
  handleShowDetail() {
    return true
  }

  @Emit('sort-change')
  async handleSortChange(data: IHostGroup[]) {
    this.sortLoading = true
    const success = await PerformanceModule.saveDashboardOrder({
      order: data,
      id: this.viewType
    })
    this.sortLoading = false
    if (success) {
      this.showSetting = false
    }
  }

  @Emit('sort-change')
  async handleUndo() {
    this.sortLoading = true
    const success = await PerformanceModule.deletePanelOrder(this.viewType)
    this.sortLoading = false
    if (success) {
      this.showSetting = false
    }
  }
  // 图表类型转换
  @Emit('chart-change')
  handleChartChange(type: number) {
    return type
  }
  // 添加自定义时间对比
  handleAddTimeshifOption(v: string) {
    v.trim().length && !this.timeshiftList.some(item => item.id === v) && this.timeshiftList.push({
      id: v,
      name: v
    })
  }
  handleAddTimeRangeOption(option: IOption) {
    this.timerangeList.push(option)
  }
  // 刷新数据
  @Emit('immediate-reflesh')
  handleImmediateReflesh() {
    return this.viewType
  }
  @Emit('search-change')
  handleSearchValueChange() {
    return this.search.value
  }
  @Emit('method-change')
  handleAggMethodChange() {
    return this.method
  }
}
</script>
<style lang="scss" scoped>
@mixin icon-arrow($rotate: 0) {
  font-size: 24px;
  color: #979ba5;
  cursor: pointer;
  transform: rotate($rotate);
}

.chart-tool {
  height: 42px;
  background: #fff;
  &-agg {
    border-right: 1px solid #f0f1f5;
    width: 120px;
    display: flex;
    align-items: center;
    .label {
      padding-left: 10px;
    }
    .content {
      flex: 1;
      position: relative;
      top: 1px;
      /deep/ .dropdown-trigger {
        padding: 0 10px 0 5px;
      }
    }
  }
  .arrow-right {
    @include icon-arrow(90deg);
  }
  .arrow-left {
    @include icon-arrow(-90deg);
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
  }
  &-left {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 14px;
    border-right: 1px solid #f0f1f5;
    /deep/ & .bk-button {
      font-size: 12px;
    }
  }
  &-right {
    display: flex;
  }
  .tool-search {
    display: flex;
    align-items: center;
    height: 32px;
    min-width: 78px;
    padding-left: 18px;
    color: #63656e;
    font-size: 12px;
    &-icon {
      font-size: 14px;
      color: #737987;
      margin-right: 5px;
    }
    &-input {
      border: 0;
      width: 40px;
    }
  }
}
</style>
