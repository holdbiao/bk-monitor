<template>
  <div class="data-retrieval-view">
    <div class="view-header-wrapper">
      <!-- 右侧顶部组件 -->
      <compare-panel
        style="width: 100%"
        :need-target="false"
        :need-split="false"
        :value="compareValue"
        :compare-list="dynamicCompareList"
        :tools-prop="toolsObj"
        :chart-type="chartType"
        :reflesh-list="refleshList"
        :timerange-list="timerangeList"
        :timeshift-list="timeshiftList"
        @on-immediate-reflesh="handleImmediateReflesh"
        @add-timerange-option="handleAddTimeRangeOption"
        @change="handleComparePanelChange"
        @chart-change="handleChartChange">
        <template #pre>
          <span class="tool-icon right" v-show="!leftShow" @click="handleLeftShow">
            <i class="arrow-right icon-monitor icon-double-up"></i>
          </span>
        </template>
      </compare-panel>
    </div>
    <div :class="['charts-view-wrapper', { 'padding-top-0': searchTipsObj.show }]" v-bkloading="{ isLoading: loading }">
      <!-- 图表组件 -->
      <dashboard-panels
        v-if="Object.keys(queryConfigs).length"
        :search-tips-obj="searchTipsObj"
        :chart-option="chartOption"
        :groups-data="queryConfigs"
        :compare-value="compareValue"
        :chart-type="chartType"
        @on-split="onSplitChange"
        @on-add-strategy="handleAddStrategy">
      </dashboard-panels>
      <bk-exception v-else style="margin-top: 15%" type="empty">
        <span>{{$t('暂无数据')}}</span>
      </bk-exception>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'
import DashboardPanels from '../../performance/performance-detail/dashboard-panels.vue'
import ComparePanel from '../../performance/performance-detail/compare-panel.vue'
import { chartType } from '../index'
import DataRetrieval from '../../../store/modules/data-retrieval'
import { deepClone, random } from '../../../../monitor-common/utils/utils'
import { ISearchTipsObj } from '../../performance/performance-type'
import { DATARETRIEVAL_CHART_TYPE } from '../../../constant/constant'
@Component({
  name: 'data-retrieval-view',
  components: {
    ComparePanel,
    DashboardPanels
  }
})
export default class DataRetrievalView extends Vue {
  // 左侧栏是否显示
  @Prop({ default: false }) leftShow: boolean
  timerangeList: { name: any, value: string | number }[] = []
  timeshiftList: { id: string, name: any }[] = []
  private chartType: chartType = +localStorage.getItem(DATARETRIEVAL_CHART_TYPE) % 3

  private chartOption: any = {
    tool: {
      list: ['save', 'screenshot', 'fullscreen', 'set', 'strategy', 'area'] // 要显示的多工具栏的配置id 空数组则为不显示
    },
    annotation: {
      show: true,
      list: ['ip', 'process', 'strategy']
    }
  }
  private refleshList: { name: string; id: number }[] = [
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
  private compareList: any = [ // 对比类型列表
    {
      id: 'none',
      name: window.i18n.t('不对比')
    },
    {
      id: 'target',
      name: window.i18n.t('目标对比')
    },
    {
      id: 'time',
      name: window.i18n.t('时间对比')
    },
    {
      id: 'metric',
      name: window.i18n.t('指标对比')
    }
  ]
  private immediateReflesh = 0

  get searchTipsObj(): ISearchTipsObj {
    return {
      value: !DataRetrieval.queryDataGetter.compareConfig.split,
      show: true,
      time: DataRetrieval.queryTimeGetter,
      showSplit: DataRetrieval.queryDataGetter.compareConfig.type === 'none',
      showAddStrategy: DataRetrieval.queryDataGetter.queryConfigs.length === 1
    }
  }

  get loading() {
    return DataRetrieval.loading
  }

  get queryData() {
    return DataRetrieval.queryDataGetter
  }

  get queryConfigsGetter() {
    return DataRetrieval.queryData.queryConfigs
  }

  get dynamicCompareList() {
    if (this.queryConfigsGetter.length <= 1) {
      return this.compareList.slice(0, 3)
    }
    return this.compareList
  }

  get compareValue() {
    const curCompare = DataRetrieval.queryDataGetter.compareConfig
    const curTools = DataRetrieval.queryDataGetter.tools
    if (Array.isArray(curTools.timeRange)) {
      this.handleTimerangeList(curTools.timeRange)
    }
    if (curCompare.type === 'time') {
      this.handleTimeshiftList(curCompare.timeOffset)
    }
    const compareMap = {
      none: { type: 'none', value: curCompare.split },
      time: { type: 'time', value: curCompare.timeOffset },
      target: { type: 'target' },
      metric: { type: 'metric' }
    }
    return {
      compare: compareMap[curCompare.type],
      tools: curTools
    }
  }

  //  查询结果 图表查询接口入参
  get queryConfigs() {
    if (!Object.keys(DataRetrieval.queryConfigs).length) return {}
    return DataRetrieval.queryConfigs.panels.map(item => ({
      ...item,
      key: `${random(10)}-${this.immediateReflesh}`
    }))
  }

  get toolsObj() {
    const tools = deepClone(DataRetrieval.queryDataGetter.tools)
    return tools
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
        name: this.$t('1小时前')
      },
      {
        id: '1d',
        name: this.$t('昨天')
      },
      {
        id: '1w',
        name: this.$t('上周')
      },
      {
        id: '1M',
        name: this.$t('一月前')
      }
    ]
  }
  handleTimerangeList(value) {
    const valStr = `${value[0]} -- ${value[1]}`
    const item = this.timerangeList.find(item => item.name === valStr)
    if (!item) {
      this.timerangeList.push({
        name: valStr,
        value: valStr
      })
    }
  }
  handleTimeshiftList(val) {
    if (typeof val === 'string') {
      const item = this.timeshiftList.find(item => item.id === val)
      if (!item) {
        this.timeshiftList.push({
          name: val,
          id: val
        })
      }
    } else if (Array.isArray(val)) {
      const itemList = val.filter(id => !this.timeshiftList.some(item => item.id === id))
      if (itemList.length) {
        itemList.forEach((id) => {
          this.timeshiftList.push({
            name: id,
            id
          })
        })
      }
    }
  }

  //  对比类型change
  handleComparePanelChange(obj) {
    const { compare, tools, type: eventType } = obj
    const { type } = compare
    const doNotQueryMap = ['interval']
    const keepSplitStatusMap = ['interval', 'timeRange']
    const neeedQuery =  !doNotQueryMap.includes(eventType) && JSON.stringify(this.compareValue) !== JSON.stringify(obj)
    const compareMap = {
      none: { type: 'none', split: keepSplitStatusMap.includes(eventType) ? compare.value : true },
      time: { type: 'time', timeOffset: compare.value },
      target: { type: 'target' },
      metric: { type: 'metric' }
    }
    // 对比类型
    DataRetrieval.setData({ expr: 'queryData.compareConfig', value: compareMap[type] })
    // 时间范围
    DataRetrieval.setData({ expr: 'queryData.tools', value: tools })
    // 更新start_time end_time
    DataRetrieval.updateStartEndTime(tools.timeRange)
    // 重新查询
    if (neeedQuery) {
      DataRetrieval.handleQuery()
    }
  }

  // 视图拆分
  onSplitChange(value) {
    DataRetrieval.setData({ expr: 'queryData.compareConfig.split', value: !value })
    DataRetrieval.handleQuery()
  }

  //  图表排列格式变化
  handleChartChange(chartType) {
    this.chartType = chartType
  }

  handleAddTimeRangeOption(obj) {
    this.timerangeList.push(obj)
  }

  handleImmediateReflesh() {
    this.immediateReflesh = Date.now()
    // DataRetrieval.handleQuery()
  }

  handleAddStrategy() {
    const queryData = DataRetrieval.queryDataGetter
    const [query] = queryData.queryConfigs
    const data: any = {
      bk_biz_id: queryData.bkBizId,
      where: query.where,
      group_by: query.groupBy,
      interval: query.interval,
      method: query.method,
      data_source_label: query.dataSourceLabel,
      data_type_label: query.dataTypeLabel,
      metric_field: query.metricField,
      result_table_id: query.resultTableId
    }
    this.$router.push({
      name: 'strategy-config-add',
      params: {
        data
      }
    })
  }
  // 点击显示左侧栏
  @Emit('show-left')
  handleLeftShow() {
    return !this.leftShow
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

/deep/ .dashboard-panels {
  margin-bottom: 0;
}
.data-retrieval-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  .view-header-wrapper {
    flex: 0 0 42px;
    box-sizing: border-box;
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .1);
    background-color: #fff;
    display: flex;
    align-items: center;
  }
  .charts-view-wrapper {
    flex: 1;
    max-height: calc(100vh - 52px - 42px);
    width: 100%;
    overflow-y: scroll;
    padding: 10px 10px 0 10px
  }
  .padding-top-0 {
    padding-top: 0;
  }
  .arrow-right {
    font-size: 24px;
    color: #979ba5;
    cursor: pointer;
    transform: rotate(90deg);
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
}
</style>
