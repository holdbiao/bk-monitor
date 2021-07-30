<template>
  <bk-dialog class="main-dialog"
             :value="visiable"
             :width="setting.width"
             :show-footer="setting.showFooter"
             :position="position"
             @value-change="handleVisiableChange">
    <div class="content" v-bkloading="{ isLoading: setting.loading }">
      <div class="content-left">
        <div class="content-left-title" :title="leftSide.title">
          {{leftSide.title}}
        </div>
        <div v-for="(item, index) in leftSide.list" :key="index" class="content-left-item" :class="{ 'active': item.index_id === leftSide.currData.index_id }" @click="leftSide.currData = item">
          {{item.category}}
        </div>
      </div>
      <div class="content-right">
        <!-- 图表时间选择 -->
        <div class="content-right-select">
          <bk-select :popover-min-width="160" style="margin-right: 4px;" v-model="refreshOption.time" :clearable="false" :popover-width="110">
            <bk-option v-for="(opt, index) in refreshOption.timeList" :key="index" :disabled="opt.disabled" :name="opt.name" :id="opt.id"></bk-option>
          </bk-select>
          <monitor-date-range offset="right" @add-option="handleAddOption" v-model="refreshOption.timeRange" :options="refreshOption.timeRangeList" @change="changeTimeRange"></monitor-date-range>
        </div>
        <!-- 图表时间选择end -->
        <div class="content-right-chart" :key="renderKey" v-if="needRenderChart">
          <!-- <monitor-charts
            :title="chartTitle"
            show-legend-when-one
            :width="view.chart.style.width"
            :height="view.chart.style.height"
            :get-series-data="renderChart"
            :reflesh-time-interval="refreshOption.time">
          </monitor-charts>  -->
          <monitor-charts
            :title="chartTitle"
            :height="view.chart.style.height"
            :options="chartOptions"
            :get-series-data="renderChart"
            :reflesh-interval="refreshOption.time">
          </monitor-charts>
        </div>
        <div class="content-right-footer">
          <div class="content-right-footer-button" v-for="(item,index) in rightSide.list" :key="index">
            <bk-popover v-if="item.dimension_field" theme="light" trigger="click" placement="top">
              <bk-button :theme="rightSide.currData.index_id === item.index_id ? 'primary' : 'default'" @click="getIndexDimensionlist(item)" style="font-size: 12px;">
                {{item.description}}
              </bk-button>
              <div slot="content" class="tip-content">
                <bk-button v-if="rightSide.dimensionLoading" size="small" icon="loading" style="border: 0" class="tip-content-demension-loading"></bk-button>
                <div v-if="rightSide.dimensionList.length && !rightSide.dimensionLoading" class="bk-text-primary" style="margin-top: -5px;margin-right: -5px;">
                  <bk-button v-for="(name,i) in rightSide.dimensionList" :key="i" size="small" :theme="item.index_id === rightSide.currData.index_id && rightSide.currDimensionName === name ? 'primary' : 'default'" class="mr5 mt5" @click="handleChangeIndexDimension(item,name)">
                    {{name}}
                  </bk-button>
                </div>
                <div v-if="!rightSide.dimensionList.length && !rightSide.dimensionLoading"> {{ $t('无维度信息') }} </div>
              </div>
            </bk-popover>
            <bk-button v-else :theme="rightSide.currData.index_id === item.index_id ? 'primary' : 'default'" @click="handleChangeDimension(item)" style="font-size: 12px;">
              {{item.description}}
            </bk-button>
          </div>
        </div>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
import moment from 'moment'
// import MonitorCharts from '../../../components/monitor-charts/monitor-charts.vue'
import MonitorCharts from '../../../../monitor-ui/monitor-echarts/monitor-echarts-new'
import MonitorDateRange from '../../../components/monitor-date-range/monitor-date-range'
import { createNamespacedHelpers, mapMutations } from 'vuex'
import { getFieldValuesByIndexId, hostIndex } from '../../../../monitor-api/modules/performance'
import { timeSeriesQuery } from '../../../../monitor-api/modules/grafana'
const { mapGetters } = createNamespacedHelpers('performance')
// 限制最大指标对比数量
const MAX_IPS_COUNT = 100

export default {
  name: 'MetricContrastDialog',
  components: {
    MonitorCharts,
    MonitorDateRange
  },
  model: {
    prop: 'visiable',
    event: 'change'
  },
  props: {
    visiable: {
      type: Boolean,
      required: true,
      default: false
    },
    selectIps: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      setting: {
        width: 1190,
        showFooter: false,
        loading: false
      },
      position: {
        top: 100
      },
      leftSide: {
        title: this.$t('指标对比'),
        list: [],
        currData: {
          index_id: -1
        }
      },
      rightSide: {
        list: [],
        currData: {
          index_id: -1
        },
        dimensionList: [],
        currDimensionData: {
          index_id: -1
        },
        dimensionLoading: false,
        currDimensionName: null
      },
      dimensionDict: {},
      renderKey: null,
      view: {
        params: {
          ip_list: [],
          index_id: '',
          time_range: '',
          dimension_field: '',
          dimension_field_value: '',
          filter_dict: {},
          group_fields: ['ip', 'bk_cloud_id']
        },
        dimensionParams: {
          index_id: '',
          field: '',
          condition: {
            ip_list: [],
            time__gte: '1h'
          }
        },
        chart: {
          chartLoading: false,
          hasData: false,
          style: {
            width: 1000,
            height: 490
          },
          width: 0,
          origin: 0,
          data: {
            title: { text: null }
          }
        }
      },
      timeRange: [moment().subtract(1, 'hours')
        .format(), moment().format()],
      refreshOption: {
        timeList: [
          {
            name: this.$t('不刷新'),
            id: -1,
            disabled: false
          },
          {
            name: this.$t('每一分钟'),
            id: 60000,
            disabled: false
          },
          {
            name: this.$t('每五分钟'),
            id: 300000,
            disabled: false
          }
        ],
        timeRangeList: [
          {
            value: 1,
            name: this.$t('1小时')
          },
          {
            value: 24,
            name: this.$t('1天')
          },
          {
            value: 168,
            name: this.$t('7天')
          }, {
            value: 720,
            name: this.$t('1个月')
          }
        ],
        time: -1,
        timeRange: 1
      },
      needRenderChart: false
    }
  },
  computed: {
    ...mapGetters({
      hostIndexList: 'hostList'
    }),
    // 图表title
    chartTitle() {
      const item = this.rightSide.list.find(item => item.index_id === this.rightSide.currData.index_id)
      return item ? item.description : ''
    },
    chartOptions() {
      return {
        legend: {
          asTable: false
        },
        tool: {
          list: ['screenshot', 'area']
        }
      }
    }
  },
  watch: {
    selectIps: {
      handler() {
        // this.leftSide.currData = { index_id: -1 }
        this.setParamsIps()
      },
      deep: true
    },
    visiable: {
      handler(flag) {
        if (flag) {
          // 打开提示指标对比限制的最大数量
          if (this.selectIps.length > MAX_IPS_COUNT) {
            this.$bkMessage({
              showClose: true,
              message: this.$t('指标对比最大支持主机数量: ') + MAX_IPS_COUNT,
              theme: 'warning'
            })
          }
          this.dimensionDict = {}
          this.getHostIndexList().then(() => {
            this.needRenderChart = true
          })
        }
      },
      immediate: true
    },
    'leftSide.currData': {
      handler(o) {
        this.handleChangeIndex(o)
      },
      deep: true
    }
  },
  methods: {
    ...mapMutations('performance', ['SET_PERFORMANCE_HOST']),
    setParamsIps() {
      // 指标对比添加最大数量限制 MAX_IPS_COUNT
      const maxSelectIps = this.selectIps.length > MAX_IPS_COUNT
        ? this.selectIps.slice(0, MAX_IPS_COUNT) : this.selectIps
      const ips = maxSelectIps.map(item => ({
        ip: item.bk_host_innerip,
        bk_cloud_id: item.bk_cloud_id
      }))
      this.view.params.ip_list = ips
      this.view.dimensionParams.condition.ip_list = ips
    },
    setParamsGetChartData() {
      this.view.params.index_id = this.rightSide.currData.index_id
      this.view.params.result_table_id = this.rightSide.currData.result_table_id
      this.view.params.metric_field = this.rightSide.currData.metric_field

      if (this.rightSide.currDimensionName) {
        this.renderKey = `${this.selectIps.length}`
        + `-${this.rightSide.currData.index_id}-${this.rightSide.currDimensionName}`
      } else {
        this.renderKey = `${this.selectIps.length}-${this.rightSide.currData.index_id}`
      }
    },
    handleChangeIndex(obj) {
      // this.leftSide.currData = obj
      this.view.params.filter_dict = {}
      this.rightSide.currDimensionName = ''
      this.getDimensionlistbyIndex(obj)
    },
    handleChangeDimension(obj) {
      this.view.params.filter_dict = {}
      this.rightSide.currDimensionName = ''
      this.rightSide.currData = obj
      this.setParamsGetChartData()
    },
    handleChangeIndexDimension(metric, name) {
      this.rightSide.currData = metric
      this.rightSide.currDimensionName = name
      this.view.params.filter_dict = { [metric.dimension_field]: name }
      this.setParamsGetChartData()
    },
    async renderChart(startTime = '', endTime = '', isSelection = false) {
      this.view.chart.chartLoading = true
      this.view.params.time_range = this.handleTimeRangeStr()
      // 当图表选择时间段
      if (isSelection) {
        this.view.params.time_range = `${moment(startTime).format()} -- ${moment(endTime).format()}`
      }
      const params = this.transferParams(this.view.params)
      const data = await timeSeriesQuery(params).catch(() => [])
      data.forEach((item) => {
        const { dimensions: { bk_cloud_id: bkCloudId, ip } } = item
        item.target = `${bkCloudId}:${ip}`
      })
      return data
    },
    // 图表接口参数转换
    transferParams(parmas) {
      const res = {}
      const filterDict = parmas.filter_dict
      const filterDictKeys = Object.keys(parmas.filter_dict)
      // 目标
      res.target = parmas.ip_list.map(item => ({
        bk_target_cloud_id: item.bk_cloud_id,
        bk_target_ip: item.ip
      }))
      // 查询条件
      res.where = filterDictKeys.length ? (filterDictKeys.map((key, index) => {
        const obj = {
          key,
          method: 'eq',
          value: [filterDict[key]]
        }
        index > 0 && (obj.condition = 'and')
        return obj
      })) : []
      // 指标数据
      res.metric_field = parmas.metric_field
      res.result_table_id = parmas.result_table_id
      res.data_source_label = 'bk_monitor'
      res.data_type_label = 'time_series'
      // 维度
      res.group_by = parmas.group_fields
      // 聚合方法
      res.method = 'MAX'
      // 聚合周期
      res.interval = 60
      // 时间范围
      const times = parmas.time_range.split('--')
      res.start_time = moment(times[0].trim()).unix()
      res.end_time = moment(times[1].trim()).unix()
      return res
    },
    handleTimeRangeStr() {
      let beforeTimeStr = moment().subtract(1, 'hours')
        .format()
      let timeRangeStr = ''
      const { timeRange } = this.refreshOption
      const now = moment().format()
      if (Number.isInteger(timeRange)) {
        const num = timeRange
        beforeTimeStr = moment().subtract(num, 'hours')
          .format()
        timeRangeStr = `${beforeTimeStr}--${now}`
      } else if (Array.isArray(timeRange)) {
        timeRangeStr = `${timeRange[0]}--${timeRange[1]}`
      } else if (typeof timeRange === 'string' && timeRange.split('--').length) {
        timeRangeStr = timeRange
      }
      return timeRangeStr
    },
    async getHostIndexList() {
      if (this.hostIndexList.length === 0) {
        const list = await hostIndex().catch(() => [])
        this.SET_PERFORMANCE_HOST(list)
      }
      const data = {}
      this.hostIndexList.forEach((item) => {
        if (item.category_id !== 'process') {
          data[item.category_id] = { ...item, category: item.category_id === 'system_env'
            ? this.$t('系统进程') : item.category }
        }
      })
      this.leftSide.list = Object.values(data)
      this.leftSide.currData = this.leftSide.list[0]
    },
    /**
     * 指标过滤后加载第一位的图表
     */
    async getDimensionlistbyIndex(obj) {
      this.rightSide.list = this.hostIndexList.filter(item => item.category_id === obj.category_id)
      this.rightSide.currData = this.rightSide.list[0]
      if (this.rightSide.currData.dimension_field) {
        await this.getIndexDimensionlist(this.rightSide.currData)
        if (this.rightSide.dimensionList.length > 0) {
          this.rightSide.currDimensionName = this.rightSide.dimensionList[0]
          this.view.params.filter_dict = { [this.rightSide.currData.dimension_field]: this.rightSide.dimensionList[0] }
        } else {
          this.rightSide.currDimensionName = '-1'
          this.view.params.filter_dict = {}
        }
      }
      this.setParamsGetChartData()
    },
    async getIndexDimensionlist(metric) {
      const name = `${this.leftSide.currData.index_id}-${metric.index_id}`
      this.view.dimensionParams.index_id = metric.index_id
      this.view.dimensionParams.field = metric.dimension_field
      this.rightSide.dimensionLoading = true
      if (!this.dimensionDict[name]) {
        const data = await getFieldValuesByIndexId(this.view.dimensionParams)
        this.dimensionDict[name] = data
        this.rightSide.dimensionList = data
        this.rightSide.dimensionLoading = false
      } else {
        this.rightSide.dimensionList = this.dimensionDict[name]
        this.rightSide.dimensionLoading = false
      }
    },
    // 点击自定义新增option
    handleAddOption(item) {
      item && this.refreshOption.timeRangeList.push(item)
    },
    changeTimeRange() {
      const num = this.refreshOption.timeRange
      const isNum = Number.isInteger(this.refreshOption.timeRange)
      this.refreshOption.timeList.forEach((item, index) => {
        index !== 0 && (item.disabled = !isNum)
      })
      if (isNum) {
        this.timeRange = [moment().subtract(num, 'hours')
          .format(), moment().format()]
      } else {
        this.refreshOption.time = -1
      }
      // 更新图表
      this.renderKey = this.handleTimeRangeStr()
    },
    handleVisiableChange(v) {
      this.$emit('change', v)
    }
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.main-dialog {
  /deep/ .bk-dialog-wrapper {
    .bk-dialog {
      .bk-dialog-tool {
        position: absolute;
        right: 0;
      }
      .bk-dialog-body {
        padding: 0;
        min-height: 460px;
      }
    }
  }
  .content {
    display: flex;
    height: 100%;
    &-left {
      width: 160px;
      border-right: 1px solid #dcdee5;
      background-color: #fafbfd;
      width: 0 0 160px;
      &-title {
        height: 61px;
        padding-left: 20px;
        font-size: 24px;
        color: #444;
        line-height: 61px;
        border-bottom: 1px solid #dcdee5;

        @include ellipsis;
      }
      &-item {
        cursor: pointer;
        height: 41px;
        line-height: 41px;
        padding-left: 20px;
        border-bottom: 1px solid #dcdee5;
      }
    }
    &-right {
      height: 100%;
      flex: 1 1 46em;
      &-select {
        position: relative;
        display: flex;
        padding: 24px 24px 0 24px;
        font-size: 12px;
        /deep/.date-picker-chart {
          width: 0;
          .bk-date-picker-rel {
            display: none;
          }
        }
      }
      &-chart {
        padding: 15px 24px 24px 24px;
        &-container {
          height: 280px;
          background-color: #444;
        }
        &-error {
          width: 596px;
          height: 320px;
          font-size: 24px;
          text-align: center;
          line-height: 320px;
          color: #444;
          // background:#ddd;
        }
      }
      &-footer {
        flex: 1;
        padding: 0px 0px 45px 24px;
        &-button {
          margin: 0 0 10px 10px;
          display: inline-block;
        }
      }
    }
    .active {
      position: relative;
      color: #3a84ff;
      background-color: #fff;
      &:after {
        position: absolute;
        top: 0;
        right: -1px;
        height: 100%;
        content: "";
        border-right: 1px solid #fff;
      }
    }
    .mr5 {
      margin-right: 5px;
    }
    .mt5 {
      margin-top: 5px;
    }
  }
}
.tip-content-demension-loading {
  /deep/ .bk-button-icon-loading::before {
    content: none;
  }
}
</style>
