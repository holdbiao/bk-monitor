<template>
  <div class="view-detail">
    <monitor-dialog
      :value="true"
      :full-screen="true"
      :need-footer="false"
      :need-header="false"
      :before-close="handleBackStep">
      <div :class="['view-box', { 'reduce-box': navToggle }]" v-bkloading="{ isLoading: loading }">
        <!-- 头部选项栏 -->
        <header class="view-box-header">
          <compare-panel
            class="compare-panel"
            :need-split="false"
            :has-view-change-icon="false"
            :compare-list="compareList"
            :value="compareValue"
            :reflesh-list="refleshList"
            :timeshift-list="timeshiftList"
            :timerange-list="timerangeList"
            @change="handleComparePanelChange"
            @add-timeshift-option="handleAddTimeshifOption"
            @on-immediate-reflesh="handleImmediateReflesh">
          </compare-panel>
          <div class="right-title" :class="{ 'right-title-active': !isRightBoxShow }">
            <i class="icon-monitor icon-double-up"
               :class="{ 'icon-active': !isRightBoxShow }"
               @click="handleHideRightBox"></i>
            <span v-show="isRightBoxShow">{{ $t('设置') }}</span>
          </div>
        </header>
        <!-- content -->
        <section class="view-box-content">
          <!-- 左边部分 视图展示部分 -->
          <div class="box-left"
               :class="{ 'box-left-active': !isRightBoxShow }">
            <!-- 图表组件 -->
            <div class="section-chart" data-tag="resizeTarget"
                 :style="{ height: drag.height + 'px' }">
              <monitor-echarts
                :chart-type="type === 'graph' ? 'line' : type"
                :key="renderKey"
                :height="drag.height - 20"
                :reflesh-interval="compareValue.tools.refleshInterval"
                :title="title"
                :subtitle="subtitle"
                :options="chartOptions"
                :need-full-screen="false"
                :get-alarm-status="getAlarmStatus"
                :get-series-data="getSeriesData(queryconfig)"
                @add-strategy="handleAddStrategy(queryconfig)">
              </monitor-echarts>
              <div class="chart-drag"
                   @mousedown="handleMouseDown"
                   @mousemove="handleMouseMove">
              </div>
            </div>
            <!-- 原始数据 -->
            <div class="section-box">
              <div class="section-box-title">
                <span>{{ $t('原始数据') }}</span>
                <span class="title-count">{{ $t('共') }} {{ dataListLength }} {{ $t('条数据') }}</span>
              </div>
              <div class="section-box-content">
                <table cellspacing="0" cellpadding="0" border="0" style="width: 100%">
                  <thead>
                    <tr class="table-head">
                      <th class="table-content" v-for="(item, index) in tableThArr" :key="index">
                        <div class="table-item" :style="index === 0 ? 'text-align: left' : ''">
                          {{ item }}
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, index) in tableTdArr" :key="index">
                      <td class="table-content" v-for="(item, tdIndex) in row" :key="tdIndex">
                        <div class="table-item" :style="tdIndex === 0 ? 'text-align: left' : ''">
                          {{ item.value === null ? '--' : item.value }}
                          <img
                            v-if="tdIndex > 0 && (item.max || item.min)"
                            class="item-max-min"
                            :src="require(`../../static/images/svg/${item.min ? 'min.svg' : 'max.svg'}`)">
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="box-right" v-show="isRightBoxShow">
            <!-- 右边部分 设置部分 -->
            <query-criteria-item
              v-for="(item, index) in rightData"
              :key="index"
              :query-config="item"
              :group-index="index"
              @change-status="handleChangeStatus"
              @query-change="handleQueryChange"
              @checked-change="handleCheckedChange"
              @change-loading="handleChangeLoading">
            </query-criteria-item>
          </div>
        </section>
      </div>
    </monitor-dialog>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Mixins } from 'vue-property-decorator'
import MonitorDialog from '../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import ComparePanel from '../../../monitor-pc/pages/performance/performance-detail/compare-panel.vue'
import MonitorEcharts from '../../../monitor-ui/monitor-echarts/monitor-echarts-new.vue'
import QueryCriteriaItem from './query-criteria-item.vue'
import { timeSeriesQuery } from '../../../monitor-api/modules/grafana'
import moment from 'moment'
import { handleTimeRange } from '../../utils/index'
import authorityMixinCreate from '../../mixins/authorityMixin'
import { VIEW_AUTH as GRAFANA_VIEW_AUTH, MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../grafana/authority-map'
import { fetchItemStatus } from '../../../monitor-api/modules/strategies'
const authorityMap = {  GRAFANA_VIEW_AUTH, GRAFANA_MANAGE_AUTH }
@Component({
  name: 'view-detail',
  components: {
    MonitorDialog,
    MonitorEcharts,
    ComparePanel,
    QueryCriteriaItem
  }
})
export default class MigrateDashboard extends Mixins(authorityMixinCreate(authorityMap)) {
  private loading = false
  private drag = { height: 550, minHeight: 300, maxHeight: 550 }
  private title = '' // 图表名称
  private subtitle = '' // 图表名称
  private type = '' //  图表类型
  private chartOptions = {
    legend: { asTable: true, maxHeight: 156 },
    tool: { list: ['screenshot', 'set', 'strategy', 'area'] },
    annotation: { show: true }
  } //  图表类型
  private refleshKey = 'refleshKey' // 图表刷新控制
  private isRightBoxShow = true // 是否收起右侧指标栏
  private rightData = [] // 右侧指标数据
  private queryconfig: any = [] // 图表查询参数
  private tableThArr = [] // 原始数据表头数据
  private tableTdArr = [] // 原始数据表格数据
  private timeshiftList = [] // 时间对比候选值列表
  private timerangeList = [] // 图表刷新列表
  private compareValue = { // 图表顶部工具栏
    compare: {
      type: 'none', // 对比类型 目前只支持 时间对比
      value: '' // 对应对比类型的值
    },
    tools: {
      refleshInterval: -1, // 刷新间隔 -1是不刷新
      timeRange: 60 * 60 * 1000 // 图表横轴时间范围
    }
  }
  private compareList: any = [ // 对比类型列表
    {
      id: 'none',
      name: window.i18n.t('不对比')
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
  private refleshList: { name: string; id: number }[] = [ // 刷新间隔列表
    {
      name: window.i18n.tc('刷新'),
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

  private tableTdMaxMinMap = []

  //  原始数据数目
  get dataListLength() {
    return this.tableTdArr.length
  }

  //  渲染Key 查询参数 + 图表横轴时间范围 + 时间对比值
  get renderKey() {
    return JSON.stringify(this.queryconfig)
    + JSON.stringify(this.compareValue.tools.timeRange)
    + JSON.stringify(this.compareValue.compare.value)
    + this.refleshKey
  }

  // 是否展开导航
  get navToggle() {
    return this.$store.getters.navToggle
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

    this.handleQueryConfig()
  }

  mounted() {
    const { clientHeight } = document.body
    this.drag.height = clientHeight - 173
  }

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (from.name === 'performance-detail') {
        vm.chartOptions.annotation = {
          show: true,
          list: ['strategy']
        }
      }
    })
  }

  //  处理入参
  handleQueryConfig() {
    const { targets, title, type, subTitle = '' } = JSON.parse(`${this.$route.query.config}`)
    this.title = title
    this.subtitle = subTitle
    this.type = type
    this.queryconfig = targets
    this.queryconfig.forEach((item, index) => {
      this.$set(this.queryconfig[index].data, 'filter_dict', {})
    })
    const str = 'ABCDEFGHIJKLNMOPQRSTUVWXYZ'
    this.rightData = this.queryconfig.map((item, index) => ({
      ...item,
      show: index === 0,
      name: str[index]
    }))
    const { compare, tools } = JSON.parse(`${this.$route.query.compareValue}`)
    if (compare.type === 'time') {
      if (typeof compare.value === 'string' && !this.timeshiftList.find(item => item.id === compare.value)) {
        this.timeshiftList.push({
          id: compare.value,
          name: compare.value
        })
      } else if (Array.isArray(compare.value)) {
        const itemList = compare.value.filter(id => !this.timeshiftList.some(item => item.id === id))
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
    this.compareValue.compare = {
      type: ['time', 'metric'].includes(compare.type) ? compare.type : 'none',
      value: compare.type === 'time' ? compare.value : 'false'
    }

    if (Array.isArray(tools.timeRange)) {
      const valStr = `${tools.timeRange[0]} -- ${tools.timeRange[1]}`
      const item = this.timerangeList.find(item => item.name === valStr)
      if (!item) {
        this.timerangeList.push({
          name: valStr,
          value: valStr
        })
      }
    }
    this.compareValue.tools.timeRange = tools.timeRange
  }

  //  获取图表时间范围
  getTimerange() {
    const { tools } = this.compareValue
    const res = handleTimeRange(tools.timeRange)
    return {
      start_time: res.startTime,
      end_time: res.endTime
    }
  }
  // 获取告警状态信息
  async getAlarmStatus(id) {
    const data = await fetchItemStatus({ metric_ids: [id] }).catch(() => ({ [id]: 0 }))
    return data?.[id]
  }
  //  图表数据请求方法
  getSeriesData(targets) {
    return async (startTime?, endTime?) => {
      this.loading = true
      const dataList = await Promise.all((targets || []).map(async (item) => {
        const params = item.data
        let timerange = this.getTimerange()
        if (startTime && endTime) {
          timerange = {
            start_time: moment(startTime).unix(),
            end_time: moment(endTime).unix()
          }
        }
        return await timeSeriesQuery({
          ...params,
          ...timerange
        }).then(data => (data || []).map(({
          datapoints, dimensions,  metric, target, ...setData
        }) => {
          const { filter_dict: filterDict } = params
          const aliasArr = [metric.metric_field]
          Object.keys(dimensions || {}).forEach(key => aliasArr.push(dimensions[key]))
          Object.keys(filterDict || {}).forEach(key => aliasArr.push(filterDict[key]))
          const alias = aliasArr.join('-')
          return ({
            metric,
            dimensions,
            datapoints,
            ...setData,
            target: alias || target
          })
        }))
          .catch(() => {
            this.loading = false
            return []
          })
      }))
      const res = dataList.reduce<any[]>((data, item) => data.concat(item), [])
      this.handleRawData(res)
      return res
    }
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
  //  处理原始数据
  handleRawData(data) {
    if (data.length === 0) {
      this.loading = false
      return
    }
    this.tableThArr = data.map(item => item.target) // 原始数据表头
    this.tableThArr.unshift('time')
    //  原始数据表格数据
    this.tableTdArr = data[0].datapoints.map(set => [{
      value: moment(set[1]).format('YYYY-MM-DD HH:mm:ss')
    }])
    data.forEach((item) => {
      item.datapoints.forEach((set, index) => {
        this.tableTdArr[index].push({
          max: false,
          min: false,
          value: set[0]
        })
      })
    })
    // 计算极值
    const maxMinMap = this.tableThArr.map(() => ({
      max: null,
      min: null
    }))
    this.tableThArr.forEach((th, index) => {
      if (index > 0) {
        const map =  maxMinMap[index]
        map.min = this.tableTdArr[0][index].value
        map.max = map.min
        this.tableTdArr.forEach((td) => {
          const cur = td[index].value
          cur > map.max && cur !== null && (map.max = cur)
          cur < map.min && cur !== null && (map.min = cur)
        })
      }
    })
    this.tableTdArr.forEach((th) => {
      th.forEach((td, i) => {
        if (i > 0) {
          if (maxMinMap[i].max !== null && td.value === maxMinMap[i].max) {
            td.max = true
            maxMinMap[i].max = null
          }
          if (maxMinMap[i].min !== null && td.value === maxMinMap[i].min) {
            td.min = true
            maxMinMap[i].min = null
          }
          td.min && td.max && (td.max = false)
        }
      })
    })
    this.loading = false
  }

  //  图表顶部工具栏数据变更触发
  handleComparePanelChange(params) {
    (this.queryconfig || []).forEach((item) => {
      if (params.compare.type === 'time') {
        if (!item.alias?.includes('$time_offset')) {
          item.alias = item.alias ? `$time_offset-${item.alias}` : '$time_offset'
        }
      } else {
        item.alias = item.alias.replace('$time_offset-', '').replace('$time_offset', '')
      }
    })
    this.compareValue = params
    //  自定义时间范围
    const curTools = params.tools
    if (Array.isArray(curTools.timeRange)) {
      const valStr = `${curTools.timeRange[0]} -- ${curTools.timeRange[1]}`
      const item = this.timerangeList.find(item => item.name === valStr)
      if (!item) {
        this.timerangeList.push({
          name: valStr,
          value: valStr
        })
      }
    }

    //  时间对比处理 不对比 value 是 false || ''
    const { value } = params.compare
    if (!value) {
      this.queryconfig.forEach((item) => {
        Vue.delete(item.data, 'function')
      })
      return
    }
    // const unit = value.replace(/[^a-z]+/ig, '')
    // const number = value.replace(/[^0-9]/ig, '')
    // if (['d', 'day', 'days', '天'].includes(unit)) {
    //   value = `${number}d`
    // }
    this.queryconfig.forEach((item) => {
      item.data.function = { time_compare: value }
    })
  }

  handleAddTimeshifOption(v: string) {
    v.trim().length && !this.timeshiftList.some(item => item.id === v) && this.timeshiftList.push({
      id: v,
      name: v
    })
  }

  //  处理method和interval变化派发出来的事件 变更图表查询参数
  handleQueryChange(value, type, groupIndex) {
    if (type === 'method') {
      this.queryconfig[groupIndex].data.method = value
    }
    if (type === 'interval') {
      this.queryconfig[groupIndex].data.interval = value
    }
  }

  handleCheckedChange(groupIndex: number, obj) {
    const key = Object.keys(obj)[0]
    const filterDict = this.queryconfig[groupIndex].data.filter_dict
    if (obj[key] !== 'all') {
      this.$set(filterDict, key, obj[key])
      return
    }
    if (Object.prototype.hasOwnProperty.call(filterDict, key)) {
      Vue.delete(filterDict, key)
    }
  }

  // 跳转新增策略
  async handleAddStrategy(item) {
    if (item.length === 1) {
      await this.$nextTick()
      const [{ data }] = item
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

  handleChangeLoading(status: boolean) {
    this.loading = status
  }

  //  图表大小拖拽
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
      this.drag.height = Math.max(this.drag.minHeight, event.clientY - rect.top)
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

  handleMouseMove(e) {
    let { target } = e
    while (target && target.dataset.tag !== 'resizeTarget') {
      target = target.parentNode
    }
  }

  //  面板折叠事件
  handleChangeStatus(name) {
    const data = this.rightData.find(item => item.name === name)
    data && (data.show = !data.show)
  }

  //  右侧面板 隐藏/展开 事件
  handleHideRightBox() {
    this.isRightBoxShow = !this.isRightBoxShow
  }

  handleBackStep() {
    this.$router.back()
  }

  dataMax(index, item) {
    return this.tableTdMaxMinMap[index].max === item
  }

  dataMin(index, item) {
    return this.tableTdMaxMinMap[index].min === item
  }

  handleImmediateReflesh() {
    this.refleshKey =  String(+new Date())
  }
}
</script>

<style lang="scss" scoped>
.view-detail {
  /deep/ .monitor-dialog-mask .monitor-dialog {
    border-radius: 0;
    background: #f5f7fa;
  }
}
.view-box {
  padding: 30px 56px 0;
  overflow: auto;
  &.reduce-box {
    padding-left: 260px;
  }
  &-header {
    display: flex;
    .compare-panel {
      width: 100%;
    }
    .right-title {
      height: 42px;
      min-width: 360px;
      width: 360px;
      background: #fff;
      border-left: 1px solid #f0f1f5;
      border-bottom: 1px solid #f0f1f5;
      display: flex;
      align-items: center;
      transition: width .3s;
      .icon-double-up {
        color: #979ba5;
        transform: rotate(90deg);
        font-size: 24px;
        padding: 4px;
        cursor: pointer;
      }
      .icon-active {
        transform: rotate(-90deg);
      }
    }
    .right-title-active {
      min-width: 54px;
      width: 54px;
      justify-content: center;
    }
  }
  &-content {
    display: flex;
    .box-left {
      width: calc(100% - 359px);
      padding: 16px 16px 16px 0;
      transition: width .3s;
      overflow-y: scroll;
      max-height: calc(100vh - 90px);
      .section-chart {
        margin-bottom: 16px;
        padding: 15px 20px 20px;
        background: white;
        position: relative;
        /deep/ .echart-legend {
          margin-left: 0;
          .chart-legend {
            margin-bottom: 6px;
          }
        }
        /deep/ .content-wrapper {
          /* stylelint-disable-next-line declaration-no-important */
          width: auto !important;
        }
        /deep/ .chart-tools .icon-mc-mark {
          display: none;
        }
        .chart-drag {
          position: absolute;
          right: calc(50% - 50px);
          bottom: -3px;
          width: 100px;
          height: 6px;
          display: flex;
          align-items: center;
          justify-items: center;
          background-color: #dcdee5;
          border-radius: 3px;
          cursor: row-resize;
          &::after {
            content: " ";
            height: 3px;
            width: 80px;
            border-bottom: 2px dotted white;
            position: absolute;
            bottom: 2px;
            left: 10px;
          }
        }
      }
      .section-box {
        background: #fff;
        border-radius: 2px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, .1);
        padding: 0 20px 20px 20px;
        min-height: 160px;
        &-title {
          width: 100%;
          height: 54px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-weight: bold;
          .title-count {
            font-weight: normal;
            color: #979ba5;
          }
        }
        &-content {
          overflow-x: scroll;
          .table-item {
            min-width: 170px;
            padding: 10px 20px;
            text-align: right;
            .item-max-min {
              display: inline-block;
              width: 28px;
              height: 16px;
              vertical-align: middle;
              margin-right: -28px;
            }
            &:last-child {
              padding-right: 30px;
            }
          }
          .table-head {
            background: #f5f6fa;
          }
          .table-content {
            border-bottom: 1px solid #e7e8ed;
          }
        }
      }
    }
    .box-left-active {
      width: 100%;
      padding-right: 0;
    }
    .box-right {
      overflow-y: scroll;
      width: 359px;
      background: #fff;
      height: calc(100vh - 89px);
      box-shadow: 0 1px 2px 0 rgba(0, 0, 0, .1);
    }
  }
}
</style>
