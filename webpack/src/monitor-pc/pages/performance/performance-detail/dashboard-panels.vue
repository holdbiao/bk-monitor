<template>
  <!-- 主机视图 -->
  <ul class="dashboard-panels">
    <div class="total-tips" v-if="searchTipsObj.show">
      <div class="tips-text">
        <span>{{`${$t('找到 {count} 条结果，用时 {time} 毫秒', { count: totalCount, time: searchTipsObj.time })}`}}</span>
        <span v-if="searchTipsObj.showAddStrategy">{{$t('，将搜索条件 ')}}<span class="add-strategy-btn" @click="handleQueryAddStrategy">{{$t('添加监控策略')}}</span></span>
      </div>
      <div class="split-btn-wrapper" v-if="searchTipsObj.showSplit">
        <span class="btn-text">{{$t('合并视图')}}</span>
        <bk-switcher
          :value="searchTipsObj.value"
          size="small"
          theme="primary"
          @change="changeSplit">
        </bk-switcher>
      </div>
    </div>
    <li v-for="group in groupList" :key="group.key">
      <template v-if="group.type === 'row' && group.id !== '__UNGROUP__'">
        <bk-collapse v-model="activeName">
          <bk-collapse-item
            class="mb10"
            hide-arrow
            :name="group.id"
            :key="group.id">
            <div class="group-item-title">
              <i :class="[
                'icon-monitor icon-arrow-right',
                { 'expand': activeName.includes(group.id) }
              ]">
              </i>
              <!-- 分组名称 -->
              <span class="ml5">{{ group.title }}</span>
            </div>
            <template #content>
              <div class="chart-wrapper">
                <template v-for="(item,index) in group.panels">
                  <div
                    :class="[
                      `chart-type-${chartType}`,
                      'group-type',
                      { 'border-bottom': group.panels.length - index <= chartType + 1 && group.panels.length - index <= (group.panels.length % (chartType + 1) || chartType + 1) },
                      { 'border-right': chartType > 0 && ((index + 1) % (chartType + 1)) },
                      {
                        'is-collect': needCollect && getHasCollected(item.id),
                        'is-collect-row': needCollect && getHasCollected(item.id),
                        'collect-wrapper': needCollect
                      }]"
                    v-if="!item.hidden"
                    :key="item.key">
                    <monitor-echarts
                      :height="chartType > 0 ? 210 : 210"
                      :options="handleChartOptions(item)"
                      :chart-type="item.type === 'graph' ? 'line' : item.type"
                      :title="item.title"
                      :subtitle="item.subTitle"
                      :get-series-data="getSeriesData(item)"
                      :reflesh-interval="compareValue.tools.refleshInterval"
                      :get-alarm-status="getAlarmStatus"
                      @add-strategy="handleAddStrategy(item)"
                      @export-data-retrieval="handleExportToRetrieval(item)"
                      @collect-chart="handleCollectSingleChart(item)"
                      @on-yaxis-set-scale="needScale => handleOnYAxisSetScale(item, needScale)"
                      @on-transform-area="isArea => handleTransformArea(item, isArea)"
                      @full-screen="handleFullScreen(item)">
                    </monitor-echarts>
                    <span
                      class="collect-wrapper-mark"
                      v-authority="{ active: !authority.GRAFANA_MANAGE_AUTH }"
                      @click="authority.GRAFANA_MANAGE_AUTH ? handleCollectChart(item) : handleShowAuthorityDetail(authorityMap.GRAFANA_MANAGE_AUTH)">
                    </span>
                  </div>
                </template>
              </div>
            </template>
          </bk-collapse-item>
        </bk-collapse>
      </template>
      <div class="chart-wrapper" :key="group.key" v-else>
        <template v-for="item in group.panels">

          <div
            class="common-chart"
            v-if="!item.hidden"
            :class="[`chart-type-${chartType}`, {
              'is-collect': needCollect && item.type === 'graph' && getHasCollected(item.id),
              'collect-wrapper': needCollect && item.type === 'graph',
              'has-child': item.panels && item.panels.length
            }]"
            :key="item.key">
            <div
              v-if="item.panels && item.panels.length"
              :class="{ 'column-wrapper': chartType > 0 }"
              class="child-wrapper">
              <div
                v-for="child in item.panels"
                :key="child.key"
                class="child-chart">
                <monitor-echarts
                  v-if="!child.hidden"
                  :height="chartType > 0 ? 130 : 105"
                  :chart-type="child.type === 'graph' ? 'line' : child.type"
                  :options="chartOptions"
                  :title="child.title"
                  :subtitle="child.subTitle"
                  :get-series-data="getSeriesData(child)"
                  :reflesh-interval="compareValue.tools.refleshInterval"
                  :get-alarm-status="getAlarmStatus"
                  @add-strategy="handleAddStrategy(child)"
                  @export-data-retrieval="handleExportToRetrieval(child)"
                  @collect-chart="handleCollectSingleChart(child)"
                  @on-yaxis-set-scale="needScale => handleOnYAxisSetScale(item, needScale)"
                  @on-transform-area="isArea => handleTransformArea(item, isArea)"
                  @full-screen="handleFullScreen(child)">
                </monitor-echarts>
              </div>
            </div>
            <monitor-echarts
              v-else-if="!item.hidden"
              :height="chartType > 0 ? 210 : 210"
              :options="handleChartOptions(item)"
              :chart-type="item.type === 'graph' ? 'line' : item.type"
              :title="item.title"
              :subtitle="item.subTitle"
              :get-series-data="getSeriesData(item)"
              :reflesh-interval="compareValue.tools.refleshInterval"
              :get-alarm-status="getAlarmStatus"
              @add-strategy="handleAddStrategy(item)"
              @export-data-retrieval="handleExportToRetrieval(item)"
              @collect-chart="handleCollectSingleChart(item)"
              @on-yaxis-set-scale="needScale => handleOnYAxisSetScale(item, needScale)"
              @on-transform-area="isArea => handleTransformArea(item, isArea)"
              @full-screen="handleFullScreen(item)">
            </monitor-echarts>
            <span
              v-if="item.type === 'graph'"
              class="collect-wrapper-mark"
              v-authority="{ active: !authority.GRAFANA_MANAGE_AUTH }"
              @click="authority.GRAFANA_MANAGE_AUTH ? handleCollectChart(item) : handleShowAuthorityDetail(authorityMap.GRAFANA_MANAGE_AUTH)">
            </span>
          </div>
        </template>
      </div>
    </li>
    <template v-if="groupList.length">
      <collect-chart
        :is-single="isSingleChart"
        :show="collectShow"
        :collect-list="collectList"
        :total-count="totalCount"
        @collect-all="handleCollectionAll"
        @close="handleCloseCollect"
        @view-detail="handleGotoViewDetail"
        @data-retrieval="handleGotoDataRetrieval">
      </collect-chart>
    </template>
    <template v-else>
      <bk-exception style="margin-top: 15%" type="empty">
        <span>{{$t('暂无数据')}}</span>
      </bk-exception>
    </template>
  </ul>
</template>
<script lang="ts">
import { Vue, Component, Prop, Watch, Inject } from 'vue-property-decorator'
import { IHostGroup, ChartType, IQueryOption, ISearchTipsObj } from '../performance-type'
import MonitorEcharts from '../../../../monitor-ui/monitor-echarts/monitor-echarts-new.vue'
import CollectChart from '../../data-retrieval/data-retrieval-view/collect-chart.vue'
import { timeSeriesQuery } from '../../../../monitor-api/modules/grafana'
import { hostComponentInfo } from '../../../../monitor-api/modules/performance'
import { fetchItemStatus } from '../../../../monitor-api/modules/strategies'
import { random, deepClone } from '../../../../monitor-common/utils/utils.js'
import { handleTimeRange } from '../../../utils/index'
import moment from 'moment'
import deepMerge from 'deepmerge'
import authorityStore from '../../../store/modules/authority'

@Component({
  name: 'dashboard-panels',
  components: {
    MonitorEcharts,
    CollectChart
  }
})
export default class DashboardPanels extends Vue {
  // dashboard配置数据
  @Prop({ required: true }) readonly groupsData: IHostGroup[]
  // 图表样式
  @Prop({ default: 1 }) readonly chartType: ChartType
  // 变量数据 属性以 $开始
  @Prop() readonly variableData: {}
  // 对比工具栏数据
  @Prop({ required: true }) readonly compareValue: IQueryOption
  // 是否需要收藏功能
  @Prop({ default: true }) readonly needCollect: boolean
  // 图表配置设置
  @Prop() readonly chartOption: object
  // 搜索提示数据
  @Prop({ default: () => ({
    value: true,
    show: false,
    time: 0,
    showSplit: true,
    showAddStrategy: false
  }), type: Object })
  searchTipsObj: ISearchTipsObj

  @Prop({ default: '' }) keyword: string
  @Inject('authority') authority
  @Inject('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Inject('authorityMap') authorityMap
  private activeName = []
  private groupList = []
  private collectList = []
  private collectShow = false
  private totalCount = 0
  private isSingleChart = false
  get chartOptions()  {
    return deepMerge({
      tool: {
        list: ['save', 'screenshot', 'fullscreen', 'explore', 'set', 'strategy', 'area']
      },
      legend: {
        asTable: this.chartType === 0,
        toTheRight: this.chartType === 0,
        maxHeight: 50
      }
    }, this.chartOption || {}, {
      arrayMerge: (destinationArray, sourceArray)  => sourceArray
    })
  }
  getTimerange() {
    const { tools } = this.compareValue
    const { startTime, endTime } = handleTimeRange(tools.timeRange)
    return {
      start_time: startTime,
      end_time: endTime
    }
  }

  @Watch('groupsData', { immediate: true })
  onGroupDataChange(v) {
    this.handleGroupDataChange(v)
  }
  @Watch('keyword')
  onKeywordChange() {
    this.handleGroupDataChange(this.groupsData)
  }
  // 获取图表数据
  getSeriesData(config) {
    return async (startTime?, endTime?) => {
      const dataList = await Promise.all((config.targets || []).map(async (item) => {
        let params = item.data
        let timerange = this.getTimerange()
        if (this.variableData) {
          params = this.compileVariableData(params)
        }
        if (startTime && endTime) {
          timerange = {
            start_time: moment(startTime).unix(),
            end_time: moment(endTime).unix()
          }
        }
        if (item.datasourceId  === 'process_port') {
          return await hostComponentInfo({
            ...params,
            name: params.process_name
          }).then(data => Object.keys(data.ports).map(port => ({
            value: port,
            status: data.ports[port].status
          })))
            .catch(() => ({
              ports: {}
            }))
        }
        return await timeSeriesQuery({
          ...params,
          ...timerange,
          slimit: window.slimit || 500
        }, { needRes: true }).then(({ data, tips }) => {
          if (data?.length >= window.slimit) {
            this.$bkNotify({
              theme: 'warning',
              title: this.$t('注意：单图中的数据量过多!!!'),
              limitLine: 0,
              message: `${this.$t(
                '[{title}] 单图中的数据条数过多，为了避免查询和使用问题只显示了{slimit}条。'
                , { title: config.title, slimit: window.slimit || 500 }
              )}${this.$route.name === 'data-retrieval' ? this.$t('可以改变查询方式避免单图数量过大。') : ''}`
            })
          }
          if (tips?.length) {
            this.$bkMessage({
              theme: 'warning',
              message: tips
            })
          }
          return (data || []).map(({ target, datapoints, ...setData }) => ({
            datapoints,
            ...setData,
            target: this.handleBuildLegend(item.alias, {
              ...setData,
              tag: setData.dimensions,
              metric: setData.metric,
              formula: params.method,
              ...params
            }) || target
          }))
        })
          .catch(() => [])
      }))
      const sets = dataList.reduce<any[]>((data, item) => data.concat(item), [])
      return sets
    }
  }
  // 获取告警状态信息
  async getAlarmStatus(id) {
    const data = await fetchItemStatus({ metric_ids: [id] }).catch(() => ({ [id]: 0 }))
    return data?.[id]
  }
  handleChartOptions(item) {
    // 跳转数据检索、新增策略不支持多指标
    if (item.targets && item.targets.length > 1 && this.chartOptions?.tool?.list) {
      const { list } = this.chartOptions.tool
      return deepMerge(this.chartOptions, {
        tool: {
          list: list.filter(item => item !== 'strategy')
        }
      }, {
        arrayMerge: (destinationArray, sourceArray)  => sourceArray
      })
    }
    return this.chartOptions
  }
  handleBuildLegend(alia: string, compareData = {}) {
    if (!alia) return alia
    let alias = alia
    Object.keys(compareData).forEach((key) => {
      const val = compareData[key] || {}
      if (key === 'time_offset') {
        if (val && alias.match(/\$time_offset/g)) {
          const timeMatch = val.match(/(-?\d+)(\w+)/)
          const hasMatch = timeMatch && timeMatch.length > 2
          alias = alias.replace(
            /\$time_offset/g,
            hasMatch
              ? moment().add(-timeMatch[1], timeMatch[2])
                .fromNow()
                .replace(/\s*/g, '')
              : val.replace('current', this.$t('当前'))
          )
        }
      } else if (typeof val === 'object') {
        Object.keys(val).sort((a, b) => b.length - a.length)
          .forEach((valKey) => {
            const variate = `$${key}_${valKey}`
            alias = alias.replace(new RegExp(`\\${variate}`, 'g'), val[valKey])
          })
      } else {
        alias = alias.replace(`$${key}`, val)
      }
    })
    while (/\|\s*\|/g.test(alias)) {
      alias = alias.replace(/\|\s*\|/g, '|')
    }
    return alias.replace(/\|$/g, '')
  }
  // 变量替换
  compileVariableData(data) {
    let params = JSON.stringify(data)
    this.variableData && Object.keys(this.variableData).forEach((key) => {
      params = params.replace(new RegExp(`\\${key}`, 'g'), this.variableData[key])
    })
    params = JSON.parse(params)
    return params
  }

  // 多选跳转大图
  handleGotoViewDetail() {
    const config = this.collectList.reduce((config, item) => {
      if (!config) {
        // eslint-disable-next-line no-param-reassign
        config = item
      } else {
        config.targets.push(...item.targets)
        config.title = this.$t('大图对比')
        config.subTitle = ''
      }
      return config
    }, null)

    this.$router.push({
      name: 'view-detail',
      query: {
        config: JSON.stringify(config),
        compareValue: JSON.stringify(this.compareValue)
      }
    })
  }

  // 多选跳转数据检索
  handleGotoDataRetrieval() {
    if (this.$route?.name === 'data-retrieval') return

    const targets = this.collectList.reduce((pre, item) => {
      pre.push(...item.targets)
      return pre
    }, [])
    window.open(`${location.href.replace(location.hash, '#/data-retrieval')}?targets=${JSON.stringify(targets)}`)
  }

  //  跳转数据大图
  handleFullScreen(item) {
    const query = deepClone(item)
    if (this.variableData) {
      query.targets = query.targets.map(item => this.compileVariableData(item))
    }
    this.$router.push({ name: 'view-detail',
      query: { config: JSON.stringify(query), compareValue: JSON.stringify(this.compareValue) } })
  }

  // 导出到数据检索
  handleExportToRetrieval(item) {
    if (this.$route?.name === 'data-retrieval') return
    let { targets } = item
    if (this.variableData) {
      targets = this.compileVariableData(targets)
    }
    window.open(`${location.href.replace(location.hash, '#/data-retrieval')}?targets=${JSON.stringify(targets)}`)
  }
  // 跳转新增策略
  handleAddStrategy(item) {
    const { targets } = item
    if (targets.length === 1) {
      let [{ data }] = targets
      if (this.variableData) {
        data = this.compileVariableData(data)
      }
      if (data?.where?.length) {
        data.where.forEach((where, index) => {
          if (index > 0 && where && !where.condition) {
            where.condition = 'and'
          }
        })
      }
      window.open(`${location.href.replace(location.hash, '#/strategy-config/add')}?data=${JSON.stringify(data)}`)
    }
  }
  //  全部收藏
  handleCollectionAll() {
    let setList = []
    this.groupList.forEach((item) => {
      if (item.panels) {
        setList = [...setList, ...item.panels]
      } else {
        setList.push(item)
      }
    })
    this.collectList = setList.filter(item => !item.hidden).map(item => this.compileVariableData(item))
  }

  //   点击收藏
  handleCollectChart(item) {
    const index = this.collectList.findIndex(set => set.id === item.id)
    index === - 1 ? this.collectList.push(this.compileVariableData(item)) : this.collectList.splice(index, 1)
    this.isSingleChart = false
    this.collectShow = true
    if (!this.collectList.length) this.collectShow = false
  }

  async handleCollectSingleChart(item) {
    if (!this.authority.GRAFANA_MANAGE_AUTH) {
      authorityStore.getAuthorityDetail(this.authorityMap.GRAFANA_MANAGE_AUTH)
      return
    }
    if (this.collectShow) {
      this.collectShow = false
      this.collectList = []
    }
    await this.$nextTick()
    this.collectList.push(this.compileVariableData(item))
    this.isSingleChart = true
    this.collectShow = true
  }

  handleTransformArea(item: any, isArea: boolean) {
    item.fill = isArea
  }

  handleOnYAxisSetScale(item: any, needScale: boolean) {
    item.min_y_zero = !needScale
  }

  //   点击关闭收藏
  handleCloseCollect(v: boolean) {
    this.collectShow = v
    this.collectList = []
  }

  //  是否已经被收藏
  getHasCollected(id) {
    return this.collectList.some(item => item.id === id)
  }

  changeSplit(val) {
    this.$emit('on-split', val)
  }

  handleQueryAddStrategy() {
    this.$emit('on-add-strategy')
  }
  handleGroupDataChange(v) {
    this.collectList = []
    this.collectShow = false
    this.groupList = []
    const groupsData = JSON.parse(JSON.stringify(v))
    let setList = []
    let count = 0
    const specialGroup = {
      type: 'special',
      panels: []
    }
    const hasKeyword  = (item) => {
      this.keyword.trim() && item.panels.forEach((child) => {
        child.hidden = (child.title || '').toLocaleLowerCase().indexOf(this.keyword) === -1
        && (child.targets || []).every(set => (set?.data['metric_field'] || '')
          .toLocaleLowerCase().indexOf(this.keyword) === -1)
      })
    }
    groupsData.forEach((item) => {
      if (item.type === 'row') {
        if (item.id !== '__UNGROUP__') {
          setList.length && this.groupList.push({
            type: 'list',
            panels: setList,
            key: random(10)
          })
          setList = []
          this.groupList.push(item)
          hasKeyword(item)
          count += item.panels.filter(set => !set.hidden).length
          !this.activeName.length && this.activeName.push(item.id)
        } else {
          setList = setList.concat(item.panels)
          hasKeyword(item)
          count += item.panels.filter(set => !set.hidden).length
        }
      } else if (['status', 'text'].includes(item.type)) {
        specialGroup.panels.push(item)
      } else {
        setList.push(item)
        item.hidden = (item.title || '').toLocaleLowerCase().indexOf(this.keyword) === -1
        || (item.targets || []).every(set => (set?.data['metric_field'] || '')
          .toLocaleLowerCase().indexOf(this.keyword) === -1)
        count += !item.hidden ? 1 : 0
      }
    })
    setList.length && this.groupList.push({
      type: 'list',
      panels: setList,
      key: random(10)
    })
    specialGroup.panels.length && this.groupList[0].panels.unshift(specialGroup)
    this.totalCount = count
  }
}
</script>
<style lang="scss" scoped>
/deep/ .bk-collapse-item-hover {
  background: #fff;
  border-radius: 2px;
  box-shadow: 0px 1px 2px 0px rgba(0,0,0,.05);
  &:hover {
    color: #63656e;
  }
}
/deep/ .bk-collapse-item-content {
  background: #fff;
  box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
  margin-top: 1px;
}
.group-item-title {
  display: flex;
  align-items: center;
  .icon-arrow-right {
    font-size: 24px;
    color: #979ba5;
    transition: transform .2s ease-in-out;
    &.expand {
      transform: rotate(90deg);
    }
  }
}
.dashboard-panels {
  position: relative;
  margin-bottom: 25px;
  .chart-wrapper {
    display: flex;
    flex-wrap: wrap;
    margin-right: -10px;
    width: calc(100% + 10px);

    @for $i from 0 through 2 {
      .chart-type-#{$i} {

        border-bottom: 1px solid #ddd;
        padding: 10px;
        background-color: white;

        @if $i == 1 {
          width: calc(#{(100% / ($i + 1))} - 10px);
          flex: 0 0 calc(#{(100% / ($i + 1))} - 10px);
          &.group-type {
            width: calc(#{(100% / ($i + 1))} - 5px);
            flex: 0 0 calc(#{(100% / ($i + 1))} - 5px);
          }
        }

        @else {
          width: calc(#{(100% / ($i + 1))} - 10px);
          flex: 0 0 calc(#{(100% / ($i + 1))} - 10px);
        }
        &.border-bottom {
          border-bottom: 0;
        }
        &.border-right {
          border-right: 1px solid #ddd;
        }
      }
    }
    .common-chart {
      display: flex;
      border-radius: 2px;
      box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
      margin-right: 10px;
      margin-bottom: 10px;
      border: 0;
      &.has-child {
        box-shadow: none;
        background: transparent;
        padding-right: 0;
      }
      .child-wrapper {
        display: flex;
        width: 100%;
        margin: -10px;
        .child-chart {
          display: flex;
          border-radius: 2px;
          box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
          border: 0;
          flex: 1;
          height: 100px;
          padding: 10px;
          background: white;
          margin-right: -10px;
          &:first-child {
            margin-right: 10px;
          }
        }
        &.column-wrapper {
          flex-direction: column;
          .child-chart {
            &:first-child {
              margin-bottom: 10px;
              margin-right: -10px;
            }
          }
        }
      }
    }
    .collect-wrapper {
      position: relative;
      // border: 1px solid transparent;
      &:hover {
        box-shadow: 0px 2px 2px 0px rgba(0,0,0,.1);
        .collect-wrapper-mark {
          display: block;
        }
      }
      &-mark {
        position: absolute;
        left: 0;
        top: 0;
        border-width: 16px;
        border-color: #dcdee5 transparent transparent #dcdee5;
        border-style: solid;
        display: none;
        border-radius: 2px;
        &::after {
          content: " ";
          width: 4px;
          height: 8px;
          border-bottom: 2px solid white;
          border-right: 2px solid white;
          position: absolute;
          top: -12px;
          left: -9px;
          transform: rotate(45deg) scaleY(1);
        }
      }
      &.is-collect {
        box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
        .collect-wrapper-mark {
          border-color: #3a84ff transparent transparent #3a84ff;
          border-width: 12px;
          display: block;
          &::after {
            top: -10px;
            left: -8px;
          }
        }
      }
    }
  }
  /deep/ .bk-collapse-item-content {
    padding: 0;
  }
  .total-tips {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    line-height: 20px;
    padding: 8px 0 10px 0;
    .split-btn-wrapper {
      display: flex;
      align-items: center;
      .btn-text {
        margin-right: 7px;
      }
    }
    .tips-text {
      .add-strategy-btn {
        color: #3a84ff;
        cursor: pointer;
      }
    }
  }
  /deep/ .monitor-echart-wrap .echart-header .sub-title {
    font-weight: normal;
  }
}
</style>
