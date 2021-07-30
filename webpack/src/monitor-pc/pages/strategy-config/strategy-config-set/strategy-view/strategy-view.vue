<template>
  <div class="strategy-view">
    <strategy-view-tool
      ref="tool"
      @change="handleToolPanelChange"
      @on-immediate-reflesh="handleRefreshView">
    </strategy-view-tool>
    <div class="strategy-view-content">
      <!-- <strategy-view-alarm class="monitor-echarts-title"></strategy-view-alarm>
      <monitor-divider></monitor-divider> -->
      <!-- 系统事件无视图 -->
      <template v-if="showChart">
        <monitor-echarts
          class="monitor-echarts-metric"
          :title="curMetricItem.metricAliaName"
          :get-series-data="getSeriesData"
          :chart-type="chartType"
          :key="metricViewChartKey"
          :reflesh-interval="tools.refleshInterval"
          :options="chartOptions"
          :line-width="2"
          :get-alarm-status="getAlarmStatus"
          @export-data-retrieval="handleExportToRetrieval"
          @collect-chart="handleCollectSingleChart">
        </monitor-echarts>
        <monitor-divider></monitor-divider>
        <strategy-view-dimensions
          class="mt20"
          :dimension-data="dimensionData"
          :current-dimension-map="currentDimensionScopeMap"
          :key="dimensionsPanelKey"
          @change="handleDimensionsChange">
        </strategy-view-dimensions>
      </template>
      <div class="chart-empty" v-else>
        <i class="icon-chart icon-monitor icon-mc-line"></i>
        <span class="text">{{ $t('暂无数据') }}</span>
      </div>
      <!-- 自定义事件和日志显示日志详情 -->
      <div class="strategy-view-log" v-if="showLogContent">
        <bk-alert type="info" :title="$t('默认展示最近20条')" class="mb10"></bk-alert>
        <strategy-view-log
          :data="logData"
          :is-last="isLast"
          v-bkloading="{ isLoading }"
          @load-more="handleLoadMore">
        </strategy-view-log>
      </div>
    </div>
    <collect-chart
      :show="collect.show"
      :collect-list="collect.list"
      :total-count="collect.count"
      is-single
      @close="handleCloseCollect">
    </collect-chart>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Watch, Ref } from 'vue-property-decorator'
import StrategyViewTool from './strategy-view-tool.vue'
import MonitorEcharts from '../../../../../monitor-ui/monitor-echarts/monitor-echarts-new.vue'
// import { getValueFormat } from '../../../../../monitor-ui/monitor-echarts/valueFormats'
import MonitorDivider from '../../../../components/divider/divider.vue'
import StrategyViewDimensions from './strategy-view-dimensions.vue'
import StrategyViewLog from './strategy-view-log.vue'
import { random, typeTools, transformDataKey } from '../../../../../monitor-common/utils/utils'
import { timeSeriesQuery, getVariableValue, logQuery } from '../../../../../monitor-api/modules/grafana'
import { getUnitInfo, fetchItemStatus } from '../../../../../monitor-api/modules/strategies'
import { handleTimeRange } from '../../../../utils/index'
import StrategyViewAlarm from './strategy-view-alarm.vue'
import moment from 'moment'
import CollectChart from '../../../data-retrieval/data-retrieval-view/collect-chart.vue'

@Component({
  name: 'strategy-view',
  components: {
    StrategyViewTool,
    MonitorEcharts,
    MonitorDivider,
    StrategyViewDimensions,
    StrategyViewLog,
    StrategyViewAlarm,
    CollectChart
  }
})
export default class StrategyView extends Vue {
  @Prop({ default: () => ({}), type: Object }) private readonly curMetricItem!: any
  @Prop({ default: () => [], type: Array }) private readonly targetList: any[]
  @Prop({ default: () => [], type: Array }) private readonly dimensionList!: any[]
  @Prop({ default: () => [], type: Array }) private readonly where: any[]
  @Prop({ default: false, type: Boolean }) private readonly loading!: boolean

  @Ref('tool') private readonly toolRef!: StrategyViewTool

  private tools: { timeRange: any, refleshInterval: number } = {
    timeRange: 1 * 60 * 60 * 1000,
    refleshInterval: 60000
  }
  // 原始时间范围，用于图表双击还原
  private lastTimeRange: number | number[] = 1 * 60 * 60 * 1000
  private metricViewChartKey = random(10)
  private dimensionsPanelKey = random(10)
  // 指标项对应的下拉列表项（原始值）
  private dimensionsScopeMap: { [prop: string]: any[] } = {}
  // 当前指标项对应的下拉列表值（当前值）
  private currentDimensionScopeMap: { [prop: string]: any[] } = {}
  private dimensions = {}
  // 当前图表指标项
  private chartDimensions = {}
  private collect = {
    show: false,
    list: [],
    count: 0
  }
  private logData = []
  private limit = 20
  // private offset = 0
  private isLast = false
  // 日志表格loading
  private isLoading = false
  private methodMap = {
    gte: '>=',
    gt: '>',
    lte: '<=',
    lt: '<',
    eq: '=',
    neq: '!='
  }

  // 柱形图不支持面积图和y轴固定
  private get chartOptions() {
    const { startTime, endTime } =  handleTimeRange(this.tools.timeRange)
    let list = []
    if (this.chartType === 'line') {
      list = this.isCustomEvent ? ['screenshot', 'set', 'area'] : ['save', 'screenshot', 'explore', 'set', 'area']
    } else {
      list = this.isCustomEvent ? ['screenshot'] : ['save', 'screenshot', 'explore']
    }
    return {
      tool: {
        list
      },
      xAxis: {
        // 大于 1 天时，坐标轴标签数量建议值减少
        splitNumber: (endTime - startTime) > 86400 ? 6 : 10
      }
    }
  }

  private get dimensionData() {
    if (!this.dimensionList) return []
    return this.dimensionList.map(item => ({
      ...item,
      list: this.dimensionsScopeMap[item.id] || []
    }))
  }

  private get chartType() {
    return this.showLogContent ? 'bar' : 'line'
  }

  private get showLogContent() {
    return this.curMetricItem?.dataTypeLabel === 'log'
               || (this.curMetricItem?.dataSourceLabel === 'custom' && this.curMetricItem?.dataTypeLabel === 'event')
  }

  private get showChart() {
    return this.curMetricItem && !this.loading
        && !(this.curMetricItem.dataSourceLabel === 'bk_monitor' && this.curMetricItem.dataTypeLabel === 'event')
  }

  private get isLogSearch() {
    // 判断是否为日志平台日志
    return this.showLogContent
      && (this.curMetricItem?.dataSourceLabel === 'bk_log_search' && this.curMetricItem?.dataTypeLabel === 'log')
  }

  private get isCustomEvent() {
    return this.curMetricItem?.dataSourceLabel === 'custom' && this.curMetricItem?.dataTypeLabel === 'event'
  }

  @Watch('curMetricItem')
  handleCurMetricItemChange() {
    this.handleQueryChart()
  }

  handleToolPanelChange({ tools, type }) {
    this.tools = tools
    type !== 'interval' && (this.lastTimeRange = tools.timeRange)
    if (type === 'timeRange') {
      this.handleRefreshView()
    }
  }
  // 刷新策略视图
  handleRefreshView() {
    this.metricViewChartKey = random(10)
  }
  // 触发图表查询
  async handleQueryChart(refreshDimension = true) {
    try {
      // 重置数据
      this.dimensions = {}
      refreshDimension && (this.dimensionsScopeMap = {})
      this.currentDimensionScopeMap = {}
      this.limit = 20
      this.logData = []
      this.dimensionsPanelKey = random(10)

      this.handleRefreshView()
    } catch (err) {
      console.log(err)
    }
  }
  // 获取告警状态信息
  async getAlarmStatus(id) {
    const data = await fetchItemStatus({ metric_ids: [id] }).catch(() => ({ [id]: 0 }))
    return data?.[id]
  }
  async handleGetVariableValue(type: 'original' | 'current' = 'original') {
    const { metric_field, result_table_id, data_source_label, data_type_label, query_string } = this.getTargetParams()
    const promiseList = []
    const { startTime, endTime } =  handleTimeRange(this.tools.timeRange)
    // 接口不支持批量，需要逐个发请求拿维度可选值信息
    this.dimensionList.forEach(async (item) => {
      const params = {
        type: 'dimension',
        params: {
          data_source_label,
          data_type_label,
          result_table_id,
          metric_field,
          field: item.id,
          where: this.where,
          start_time: startTime,
          end_time: endTime,
          query_string,
          // target: this.targetList || [],
          filter_dict: type === 'current' ? this.dimensions : {}
        }
      }
      promiseList.push(getVariableValue(params))
    })
    const data = await Promise.all(promiseList).catch(() => [])

    this.dimensionList.forEach((dimension, index) => {
      if (data[index] && Array.isArray(data[index])) {
        const obj = type === 'original' ? this.dimensionsScopeMap : this.currentDimensionScopeMap
        const value = data[index].map(item => ({ id: item.value, name: item.label }))
        this.$set(obj, dimension.id, value)
      }
    })
  }
  // 获取策略辅助视图数据
  async getSeriesData(startTime, endTime) {
    // 框选图表后更新时间框
    if (startTime && endTime) {
      const timeRange = [startTime, endTime]
      this.tools.timeRange = timeRange
    } else {
      this.tools.timeRange = this.lastTimeRange
    }
    this.toolRef.handleSetTimeRange(this.tools.timeRange)
    // 日志平台日志且检索语句为空时不执行搜索
    if (this.isLogSearch && !this.curMetricItem.indexStatement) return []
    // 汇聚类型为实时不支持图表查询
    if (this.curMetricItem.aggMethod === 'REAL_TIME') return []

    // 刷新日志
    this.showLogContent && this.handleLogQuery()

    if (!Object.keys(this.dimensionsScopeMap).length) {
      await this.handleGetVariableValue()
    }
    const target = {
      ...this.getTargetParams(),
      start_time: moment(startTime).unix(),
      end_time: moment(endTime).unix()
      // target: this.targetList || []
    }
    const { extendFields: ef, algorithm: alg } = this.curMetricItem
    const extendFields = transformDataKey(ef, true)
    const algorithm = Object.keys(alg).map(key => alg[key])
    // const algorithm2bound = {
    //   deadly: 1,
    //   warning: 2,
    //   remind: 3
    // }
    const hasIntelligentDetect = !!extendFields?.['intelligent_detect']?.['result_table_id']
    && algorithm?.some(item => item?.length > 0 && item.some(set => set.type === 'IntelligentDetect'))
    if (hasIntelligentDetect) {
      target.data_source_label = 'bk_data'
      target.metric_field = 'value'
      target.extend_metric_fields = [
        'lower_bound',
        'is_anomaly',
        'upper_bound']
      target.result_table_id = extendFields.intelligent_detect.result_table_id
      target.function =  { max_point_number: 0 }
    }

    if (!startTime || !endTime) {
      const timeRange = handleTimeRange(this.tools.timeRange)
      target.start_time = timeRange.startTime
      target.end_time = timeRange.endTime
    }
    let firstData = undefined
    const queryData = await timeSeriesQuery(target).catch(() => [])
    if (!hasIntelligentDetect) {
      [firstData] = queryData
    } else {
      firstData = queryData.find(item => item?.metric?.['metric_field'] === 'value')
    }
    if (firstData) {
      firstData.thresholds = await this.getThresholds()
      this.chartDimensions = firstData.dimensions || {}
    }
    if (!hasIntelligentDetect) {
      return [firstData]
    }
    // 智能异常检测算法 边界画图设置
    const { dimensions } = firstData
    const boundaryList = []
    const coverList = []
    const algorithm2Level = {
      deadly: 5,
      warning: 4,
      remind: 3
    }
    algorithm.filter(item => item?.some(set => set.type === 'IntelligentDetect')).forEach((alg) => {
      const algItem = alg?.find(item => item.type === 'IntelligentDetect')
      const upBoundary = queryData?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
    && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
    && item.metric.metric_field === 'upper_bound')
    ?.datapoints?.map(item => ([item[1], item[0]])) || []
      const lowBoundary = queryData?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
    && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
    && item.metric.metric_field === 'lower_bound')
    ?.datapoints.map(item => ([item[1], item[0]])) || []
      boundaryList.push({
        upBoundary,
        lowBoundary,
        color: '#e6e6e6',
        stack: `boundary-${algItem?.id || ''}`,
        z: algorithm2Level[algItem?.id] || 1
      })
      const coverData = queryData?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
    && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
    && item.metric.metric_field === 'is_anomaly')
    ?.datapoints
      if (coverData?.length) {
        coverList.push({
          data: coverData
            .map((item, index) => [firstData?.datapoints[index][1],
              item[0] > 0
                ? firstData?.datapoints[index][0]
                : null]),
          color: '#ff3d3f',
          z: +algorithm2Level[algItem?.id] + 10,
          name: `cover-${algItem?.id}`
        })
      }
    })
    return [{
      ...firstData,
      boundary: boundaryList,
      coverSeries: coverList
    }]
  }
  // 获取阈值信息
  async getThresholds() {
    if (!this.curMetricItem || !this.curMetricItem.algorithm) return []

    const lineColor = {
      deadly: '#ea3636',
      remind: '#ffd000',
      warning: '#ff8000'
    }
    const { deadly = [], remind = [], warning = [] } = this.curMetricItem.algorithm
    const data = [
      ...deadly.map((item) => {
        item.id = 'deadly'
        return item
      }),
      ...remind.map((item) => {
        item.id = 'remind'
        return item
      }),
      ...warning.map((item) => {
        item.id = 'warning'
        return item
      })]
    let unitSeries = []
    if (this.curMetricItem.unit) {
      const data = await getUnitInfo({ unit_id: this.curMetricItem.unit }).catch(() => ({}))
      unitSeries = data.unit_series || []
    }
    // 目前仅支持静态阈值
    return data.reduce((pre, next) => {
      if (next.type === 'Threshold' && Array.isArray(next.config)) {
        const unitConversion = unitSeries.find(item => item.suffix === next.algorithmUnit)
        next.config.forEach((cfg) => {
          const thresholdTitle = this.methodMap[cfg.method] ? `(${this.methodMap[cfg.method]}${cfg.threshold})` : ''
          pre.push({
            name: `${next.title}${thresholdTitle}`,
            // 动态单位转换
            yAxis: unitConversion ? unitConversion.unit_conversion * cfg.threshold : cfg.threshold,
            method: cfg.method,
            condition: cfg.condition,
            lineStyle: {
              color: lineColor[next.id]
            },
            label: {
              color: lineColor[next.id]
            },
            itemStyle: {
              color: lineColor[next.id],
              opacity: 0.1
            }
          })
        })
      }
      return pre
    }, [])
  }
  // 获取指标参数
  getTargetParams(): any {
    if (!this.curMetricItem) return {}
    const {
      dataSourceLabel,
      dataTypeLabel,
      aggInterval,
      aggMethod,
      indexStatement,
      indexSetId
    } = this.curMetricItem

    let filterDict = Object.keys(this.dimensions).reduce((pre, key) => {
      if (!typeTools.isNull(this.dimensions[key])) {
        pre[key] = this.dimensions[key]
      }
      return pre
    }, {})

    let { resultTableId, metricName } = this.curMetricItem
    // 自定义事件和日志平台日志[指标]和[result_table_id]需要特殊处理
    if (dataSourceLabel === 'custom' && dataTypeLabel === 'event') {
      resultTableId = `${this.$store.getters.bizId}_bkmonitor_event_${resultTableId}`
      metricName = '_index'

      if (this.curMetricItem.extendFields?.['custom_event_name']) {
        filterDict["event_name"] = this.curMetricItem.extendFields.custom_event_name
      }

    } else if (dataSourceLabel === 'bk_log_search' && dataTypeLabel === 'log') {
      resultTableId = indexSetId
      metricName = '_index'
    }

    return {
      data_source_label: dataSourceLabel,
      data_type_label: dataTypeLabel,
      group_by: this.dimensionList.map(item => item.id),
      interval: aggInterval,
      method: aggMethod,
      metric_field: metricName,
      result_table_id: resultTableId,
      where: this.where,
      filter_dict: filterDict,
      query_string: indexStatement
    }
  }
  // 监控维度变更
  handleDimensionsChange(dimensions) {
    this.dimensions = dimensions
    this.handleGetVariableValue('current')
    this.handleRefreshView()
  }
  // 查询日志内容
  async handleLogQuery() {
    const { dataSourceLabel, dataTypeLabel, resultTableId, indexSetId, indexStatement } = this.curMetricItem
    const { startTime, endTime } = handleTimeRange(this.tools.timeRange)
    // 如果是日志平台的日志就取indexSetId，否则就取resultTableId
    let setId = resultTableId
    if (dataSourceLabel === 'custom' && dataTypeLabel === 'event') {
      setId = `${this.$store.getters.bizId}_bkmonitor_event_${resultTableId}`
    } else if (dataSourceLabel === 'bk_log_search' && dataTypeLabel === 'log') {
      setId = indexSetId
    }
    const params = {
      data_source_label: dataSourceLabel,
      data_type_label: dataTypeLabel,
      query_string: indexStatement,
      index_set_id: setId,
      where: this.where,
      start_time: startTime,
      end_time: endTime,
      limit: this.limit,
      filter_dict: this.dimensions
      // target: this.targetList || []
      // offset: this.offset
    }
    this.isLoading = true
    const data = await logQuery(params).catch(() => [])
    this.isLoading = false

    this.logData = data
  }

  handleLoadMore() {
    this.handleLogQuery()
  }

  // 跳转数据检索
  handleExportToRetrieval() {
    const monitorParams = this.getTargetParams()
    if (this.isLogSearch) {
      const retrieveParams =  { // 检索参数
        keyword: monitorParams.query_string, // 搜索关键字
        addition: monitorParams.where?.map(set => ({
          field: set.key,
          operator: set.method,
          value: (set.value || []).join(',')
        })) || []
      }
      // eslint-disable-next-line vue/max-len
      window.open(`${this.$store.getters.bkLogSearchUrl}#/retrieve/${monitorParams.result_table_id}?bizId=${this.$store.getters.bizId}&retrieveParams=${encodeURI(JSON.stringify(retrieveParams))}`)
    } else {
      const targets = [{
        data: {
          ...monitorParams,
          // 兼容数据检索逻辑
          where: Object.keys(this.chartDimensions).map((key, index) => ({
            condition: index === 0 ? '' : 'and',
            key,
            method: 'eq',
            value: [this.chartDimensions[key]]
          }))
        }
      }]
      window.open(`${location.href.replace(location.hash, '#/data-retrieval')}?targets=${JSON.stringify(targets)}`)
    }
  }

  // 收藏到仪表盘
  handleCollectSingleChart() {
    this.collect.list = [{
      targets: [
        {
          datasourceId: 'time_series',
          name: this.$t('时序数据'),
          data: {
            ...this.getTargetParams(),
            where: Object.keys(this.chartDimensions).map((key, index) => ({
              condition: index === 0 ? '' : 'and',
              key,
              method: 'eq',
              value: [this.chartDimensions[key]]
            }))
          }
        }
      ],
      title: this.curMetricItem.metricAliaName,
      type: 'graph'
    }]
    this.collect.show = true
  }

  handleCloseCollect() {
    this.collect.show = false
    this.collect.list = []
  }
}
</script>
<style lang="scss" scoped>
.strategy-view {
  &-content {
    padding: 14px 0;
    .monitor-echarts {
      &-title {
        height: 210px;
        padding: 0 20px;
      }
      &-metric {
        height: 310px;
        padding: 0 20px;
        /deep/ .echart-legend {
          margin-left: 0;
          display: flex;
          justify-content: center;
        }
      }
    }
    .chart-empty {
      height: 300px;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      background: #fafbfd;
      margin: 0 20px;
      .icon-chart {
        font-size: 38px;
        color: #dcdee6;
      }
      .text {
        color: #979ba5;
      }
    }
    .strategy-view-log {
      margin-top: 15px;
      padding: 0 14px;
    }
  }
}
</style>
