<template>
  <div class="view" v-bkloading="{ 'isLoading': rightLoading || leftLoading }">
    <div class="left-container"
         :style="{ 'flex-basis': left.width + 'px', width: left.width + 'px' }"
         data-tag="resizeTarget">
      <div class="search">
        <bk-input
          left-icon="bk-icon icon-search"
          @change="search"
          :placeholder="$t('请输入关键词')"
          v-model="searchText">
        </bk-input>
      </div>
      <div class="hosts" v-show="!leftLoading">
        <div class="list-wrapper">
          <div class="total-data-view"
               :class="{ 'selected': !host.active }"
               @click="handleSelectTotal">
            {{ $t('数据总览') }}
          </div>
          <ul>
            <li :class="['item', item === host.active ? 'active' : '']"
                v-for="(item, index) in host.data"
                :key="index"
                @click="handleSelectHost(item)">
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="right-container" :class="{ 'full-screen': isFullScreen }" ref="collectorView">
      <div class="header">
        <div class="title"> {{ $t('监控图表') }} </div>
        <div class="operator-group">
          <div class="algorithm">
            <bk-select :clearable="false" v-model="algorithm.active">
              <bk-option v-for="(item, index) in algorithm.list"
                         :key="index"
                         :id="item"
                         :name="item"
                         @change="handleAlgorthmChange">
              </bk-option>
            </bk-select>
          </div>
          <div class="date-rang">
            <monitor-date-range
              @add-option="handleAddOption"
              v-model="dateObject.value"
              :options="dateObject.options">
            </monitor-date-range>
          </div>
        </div>
      </div>
      <div class="chart-container" ref="viewChart">
        <div class="chart-item" v-for="(chart, index) in chartList" :key="index">
          <monitor-charts
            @full-screen="handleFullScreen"
            :title="chart.title"
            :subtitle="chart.subtitle"
            :key="renderKey"
            :show-legend-when-one="true"
            :reflesh-time-interval="refresh"
            :get-series-data="getChartData(chart)"
            :height="292"
            :time-range="+dateObject.value * 60 * 60 * 1000"
            :observe-parent="false"
            :width="chart.width">
          </monitor-charts>
        </div>
        <div v-show="!chartList.length" class="empty-data">
          <i class="icon-monitor icon-hint"></i>
          <p class="text"> {{ $t('筛选结果为空') }} </p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import MonitorCharts from '../../components/monitor-charts/monitor-charts.vue'
import { debounce } from 'throttle-debounce'
import moment from 'moment'
import MonitorDateRange from '../../components/monitor-date-range/monitor-date-range'
import { customTimeSeriesGraphPoint } from '../../../monitor-api/modules/custom_report'
import { addListener, removeListener } from 'resize-detector'
import { resizeMixin } from '../../common/mixins'
const dateNow = moment().format('YYYY-MM-DD HH:mm:ss')
const lastDate = moment(dateNow).add(-1, 'h')
  .format('YYYY-MM-DD HH:mm:ss')
export default {
  name: 'collector-view',
  components: {
    MonitorCharts,
    MonitorDateRange
  },
  mixins: [resizeMixin],
  data() {
    return {
      rightLoading: true,
      leftLoading: true,
      isFullScreen: false,
      searchText: '',
      algorithm: {
        list: ['SUM', 'AVG', 'MAX', 'MIN'],
        active: 'AVG',
        index: 1
      },
      refresh: 60000,
      dateObject: {
        value: 1,
        options: [
          {
            name: this.$t('1小时'),
            value: 1
          },
          {
            name: this.$t('1天'),
            value: 24
          },
          {
            name: this.$t('7天'),
            value: 168
          },
          {
            name: this.$t('1个月'),
            value: 720
          }
        ]
      },
      metric: {
        list: [],
        value: 'all metric'
      },
      chartList: [],
      host: {
        cacheData: [],
        data: [],
        param: [],
        active: '',
        status: ''
      },
      search() {},
      left: {
        width: 240
      }
    }
  },
  computed: {
    renderKey() {
      return `${this.host.active}-${this.algorithm.active}-${this.metric.value}-${this.dateObject.value}`
    }
  },
  async created() {
    this.search = debounce(300, v => this.handleSearch(v))
    this.refresh = 60000
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
    const params = { // 检查视图初次进入会请求最近1小时的数据
      time_range: `${lastDate} -- ${dateNow}`,
      time_series_group_id: this.$route.params.id
    }
    const detailData = await this.$store.dispatch('custom-escalation/getCustomTimeSeriesDetail', params)
    this.host.cacheData = []
    this.host.data = detailData.target
    this.host.status = 'SUCCESS'
    this.getChartTotal(detailData.metric_json)
    this.$store.commit(
      'app/SET_NAV_TITLE',
      `${this.$t('route-' + '检查视图').replace('route-', '')} - #${this.$route.params.id} ${detailData.name}`
    )
    this.leftLoading = false
    this.rightLoading = false
    this.lisenResize = debounce(300, v => this.handleChartResize(v))
    addListener(this.$refs.collectorView, this.lisenResize)
  },
  beforeDestroy() {
    removeListener(this.$refs.collectorView, this.lisenResize)
  },
  methods: {
    //  点击自定义新增option
    handleAddOption(item) {
      item && this.dateObject.options.push(item)
    },
    //  图表是否全屏事件
    handleFullScreen(isFullScreen) {
      this.isFullScreen = isFullScreen
    },
    //  计算方法变化事件
    handleAlgorthmChange(v) {
      this.algorithm.active = v
    },
    handleChartResize() {
      if (this.$refs.viewChart) {
        const width = (this.$refs.viewChart.clientWidth / 2) - 10
        this.chartList.forEach((item) => {
          item.width = width
        })
      }
    },
    //  左侧主机搜索事件
    handleSearch(v) {
      if (v) {
        this.host.data = this.host.cacheData.filter(item => item.indexOf(v) > -1)
      } else {
        this.host.data = this.host.cacheData
      }
    },
    //  数据总览点击事件
    handleSelectTotal() {
      this.host.active = ''
      this.host.param = []
    },
    //  单个主机点击事件
    handleSelectHost(data) {
      this.host.active = data
      this.host.param = [data]
    },
    //  根据metric数据生成对应的图表容器与指标选择器数据
    getChartTotal(metrics) {
      const width = (this.$refs.viewChart.clientWidth / 2) - 12
      this.metric.list.unshift({ name: 'all metric', description: this.$t('全部指标'), children: [] })
      metrics.forEach((item) => {
        const groupItem = {
          name: item.table_name,
          description: item.table_desc,
          children: []
        }
        let startCollector = false
        item.fields.forEach((data) => {
          if (data.monitor_type === 'metric') {
            startCollector = true
            //  指标选择器数据
            groupItem.children.push({
              unit: data.unit,
              id: data.name,
              name: data.name,
              description: data.description ? data.description : data.name
            })
            //  图表容器数据
            this.chartList.push({
              width,
              name: data.name,
              unit: data.unit,
              title: this.setTitle(data.description, data.name, data.unit).title,
              subtitle: this.setTitle(data.description, data.name, data.unit).subtitle
            })
          }
        })
        if (startCollector) {
          this.metric.list.push(groupItem)
          this.metric.list[0].children.push(...groupItem.children)
        }
      })
      if (!this.metric.list[0].children.length) {
        this.metric.list.splice(0)
      }
    },
    //  设置图表title
    setTitle(description, name) {
      let title = ''
      let subtitle = ''
      if (description) {
        title = description
        subtitle = name
      } else if (name) {
        title = name
      }
      return {
        title: {
          text: title,
          style: { color: '#63656E', fontSize: '14px', fontWeight: 'bold' },
          align: 'left',
          y: 20
        },
        subtitle: {
          text: subtitle,
          style: { color: '#979BA5', fontSize: '12px', fontWeight: 'bold' },
          align: 'left',
          y: 34
        }
      }
    },
    //  图表数据获取接口
    getChartData(chart) {
      return (startTime, endTime, isSelection = false) => new Promise((resolve, reject) => {
        const params = {
          time_series_group_id: this.$route.params.id,
          method: this.algorithm.active,
          metric: chart.name,
          time_range: `${moment(startTime).format()} -- ${moment(endTime).format()}`
        }
        const target = this.host.param
        if (target.length) {
          params.target = target
        } else {
          params.target = this.host.cacheData
        }
        if (Array.isArray(this.dateObject.value) && !isSelection) {
          const startData = moment(this.dateObject.value[0]).format()
          const endData = moment(this.dateObject.value[1]).format()
          params.time_range = `${startData} -- ${endData}`
        }
        customTimeSeriesGraphPoint(params).then((data) => {
          resolve(data)
        })
          .catch((err) => {
            reject(err.message)
          })
      })
    }
  }
}
</script>
<style lang="scss" scoped>
.view {
  display: flex;
  flex-direction: row;
  margin: -20px -24px;
  height: calc(100vh - 52px);
  overflow: hidden;
  .left-container {
    padding-top: 8px;
    flex: 0 0 240px;
    background: #fafbfd;
    position: relative;
    /deep/ .bk-form-input {
      height: 50px;
      padding-left: 43px;
      font-size: 14px;
      border: 0;
      background-color: #fafbfd;
    }
    /deep/ .control-icon.left-icon {
      left: 16px;
      top: 17px;
      transform: none;
      font-size: 17px;
    }
    .hosts {
      border-top: 1px solid #dcdee5;
      .list-wrapper {
        padding-left: 0;
        font-size: 12px;
        color: #63656e;
        height: calc(100vh - 162px);
        overflow-y: scroll;
        .total-data-view {
          height: 32px;
          line-height: 32px;
          padding-left: 14px;
          color: #63656e;
          &:hover {
            background-color: #e1ecff;
            color: #3a84ff;
            cursor: pointer;
          }
          &.selected {
            background-color: #e1ecff;
            color: #3a84ff;
          }
        }
        .item {
          padding-left: 16px;
          height: 32px;
          line-height: 32px;
          cursor: pointer;
          &.active {
            background-color: #e1ecff;
            color: #3a84ff;
          }
          &:hover {
            background-color: #e1ecff;
            color: #3a84ff;
          }
        }
        .status {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          border: 1px solid;
          margin-right: 4px;
          &.success {
            background-color: #94f5a4;
            border-color: #2dcb56;
          }
        }
      }
    }
  }
  .right-container {
    flex: 1;
    background: #fff;
    padding: 20px 25px 12px 30px;
    box-shadow: -40px 0 30px 0 rgba(99,101,110,.06);
    z-index: 1;
    overflow-y: auto;
    &.full-screen {
      z-index: 2001;
    }
    .header {
      display: flex;
      margin-top: 10px;
      margin-bottom: 4px;
      .title {
        flex: 0 0 140px;
        color: #000;
        font-size: 18px;
        line-height: 32px;
      }
      .operator-group {
        flex: 1;
        display: flex;
        justify-content: flex-end;
        .algorithm {
          width: 100px;
        }
        .date-rang {
          display: inline-block;
          position: relative;
          vertical-align: top;
          margin-left: 5px;
          min-width: 86px;
        }
      }
    }
    .chart-container {
      display: flex;
      flex-flow: wrap;
      justify-content: space-between;
    }
    .chart-item {
      box-sizing: border-box;
      margin-top: 16px;
      border: 1px solid #f0f1f5;
      transition: width .33s cubic-bezier(.23, 1, .32, 1);
    }
    .empty-data {
      width: 100%;
      margin-top: 185px;
      text-align: center;
      font-size: 18px;
      color: #63656e;
      .icon-hint {
        color: #dcdee5;
        font-size: 32px;
      }
      .text {
        margin-top: 6px;
        line-height: 1;
        color: #63656e;
        font-size: 14px;
      }
    }
  }
}
</style>
