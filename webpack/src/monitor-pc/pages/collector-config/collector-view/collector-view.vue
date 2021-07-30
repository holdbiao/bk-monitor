<template>
  <div class="view" v-bkloading="{ 'isLoading': rightLoading || leftLoading }">
    <div class="left-container"
         :style="{ 'flex-basis': left.width + 'px', width: left.width + 'px' }"
         data-tag="resizeTarget"
         @mousedown="handleMouseDown"
         @mousemove="handleMouseMove"
         @mouseout="handleMouseOut">
      <div class="search">
        <bk-input left-icon="bk-icon icon-search" @change="search" :placeholder="$t('请输入关键词')" v-model="searchText"></bk-input>
      </div>
      <div class="hosts" v-show="!leftLoading">
        <div class="title">
          <div class="bk-button-group">
            <bk-button class="first" :class="{ 'is-selected': selectedScope === 'all' }" @click="handleStatusScope('all')" size="small"> {{ $t('全部') }} </bk-button>
            <bk-button size="small" :class="{ 'is-selected': selectedScope === 'success' }" @click="handleStatusScope('success')">
              <div v-bk-tooltips="{ content: $t('正常 (近3个周期数据）') }">
                <span class="status success"></span><span>{{success.count}}</span>
              </div>
            </bk-button>
            <bk-button size="small" :class="{ 'is-selected': selectedScope === 'failed' }" @click="handleStatusScope('failed')">
              <div class="count" v-bk-tooltips="{ content: $t('异常（下发采集失败）') }">
                <span class="status failed"></span><span>{{failed.count}}</span>
              </div>
            </bk-button>
            <bk-button class="last" :class="{ 'is-selected': selectedScope === 'nodata' }" @click="handleStatusScope('nodata')" size="small">
              <div class="count" v-bk-tooltips="{ content: $t('无数据（近3个周期）') }">
                <span class="status nodata"></span><span>{{nodata.count}}</span>
              </div>
            </bk-button>
          </div>
        </div>
        <div class="list-wrapper">
          <div class="total-data-view" :class="{ 'selected': !host.active }" @click="handleSelectTotal('all')"> {{ $t('数据总览') }} </div>
          <ul v-if="objectType === 'HOST' && nodeType === 'INSTANCE'">
            <li :class="['item', item.ip === host.active ? 'active' : '']" v-for="(item, index) in host.data" :key="index" @click="handleSelectHost(item)">
              <span :class="['status', item.status.toLocaleLowerCase()]"></span> {{item.ip}}
              <span class="host-name" v-if="item.bk_host_name">({{item.bk_host_name}})</span>
            </li>
          </ul>
          <div class="big-tree-wrapper" v-if="nodeType === 'TOPO' && treeData.length">
            <bk-big-tree
              ref="bkBigTree"
              :filter-method="filterMethod"
              :default-expanded-nodes="defaultExpandedNodes"
              :data="treeData">
              <template v-slot="node">
                <div v-if="node.data && node.data.status" :class="['bk-tree-node', { 'active': node.data.service_instance_id === host.active || node.data.instance_id === host.active }]">
                  <span style="padding-right: 5px;" @click="handleSelectNode(node.data)">
                    <span :class="['status', node.data.status.toLocaleLowerCase()]"></span>
                    {{node.data.ip}}<span class="host-name" v-if="node.data.bk_host_name">({{node.data.bk_host_name}})</span>
                  </span>
                </div>
                <span v-else-if="node.data">{{node.data.name}}</span>
              </template>
            </bk-big-tree>
          </div>
        </div>
      </div>
      <div class="resize-line"
           v-show="resizeState.show"
           :style="{ left: resizeState.left + 'px' }">
      </div>
    </div>
    <div class="right-container" :class="{ 'full-screen': isFullScreen }" ref="collectorView">
      <div class="header">
        <div class="title"> {{ $t('监控图表') }} </div>
        <div class="operator-group">
          <div class="algorithm">
            <bk-select :clearable="false" v-model="algorithm.active">
              <bk-option v-for="(item, index) in algorithm.list" :key="index" :id="item" :name="item" @change="handleAlgorthmChange"></bk-option>
            </bk-select>
          </div>

          <div class="metric">
            <metric-selector @change="handleSelectMetric" :data="metric.list"></metric-selector>
          </div>
          <div class="date-rang">
            <monitor-date-range @add-option="handleAddOption" v-model="dateObject.value" :options="dateObject.options"></monitor-date-range>
          </div>
        </div>
      </div>
      <div class="chart-container" ref="viewChart">
        <div class="chart-item" v-for="(chart, index) in chartList" :key="index">
          <!-- <monitor-charts
            @full-screen="handleFullScreen"
            :title="chart.title"
            :subtitle="chart.subtitle"
            :key="renderKey"
            :show-legend-when-one="true"
            :reflesh-time-interval="refresh"
            :get-series-data="getChartData(chart)"
            :height="292"
            :time-range="+dateObject.value * 60 * 60 * 1000"
            :observe-parent="true"
            :width="chart.width">
          </monitor-charts> -->
          <monitor-echarts
            :key="renderKey"
            :height="292"
            chart-type="line"
            :reflesh-interval="refresh * 100000"
            @full-screen="handleFullScreen"
            :get-series-data="getChartData(chart)">
            <div slot="title">
              {{chart.title.text}}
              <div class="chart-item-subtitle">{{chart.subtitle.text || chart.title.text}}</div>
            </div>
          </monitor-echarts>
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
import { debounce } from 'throttle-debounce'
import moment from 'moment'
import MonitorDateRange from '../../../components/monitor-date-range/monitor-date-range'
import MetricSelector from '../../../components/metric-select/metric-select'
import { collectConfigDetail, frontendTargetStatusTopo, graphPoint } from '../../../../monitor-api/modules/collecting'
import { resizeMixin } from '../../../common/mixins'
import MonitorEcharts from '../../../../monitor-ui/monitor-echarts/monitor-echarts'

export default {
  name: 'collector-view',
  components: {
    MonitorDateRange,
    MetricSelector,
    MonitorEcharts
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
      objectType: 'SERVICE',
      nodeType: '',
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
      defaultExpandedNodes: [],
      key: '',
      metric: {
        list: [],
        value: 'all metric'
      },
      selectedScope: 'all',
      chartList: [],
      cachAllChartElement: [],
      host: {
        cacheData: [],
        cacheTreeData: [],
        data: [],
        param: [],
        active: '',
        status: ''
      },
      success: {
        count: 0,
        data: []
      },
      failed: {
        count: 0,
        data: []
      },
      nodata: {
        count: 0,
        data: []
      },
      treeData: [],
      search() {},
      left: {
        width: 240
      }
    }
  },
  computed: {
    renderKey() {
      return `${this.host.active}-${this.algorithm.active}`
      + '-'
      + `${this.metric.value}-${this.dateObject.value}-${this.selectedScope}`
    }
  },
  async created() {
    this.search = debounce(300, v => this.handleSearch(v))
    this.refresh = 60000
    this.treeData = []
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
    await Promise.all([this.getInfo(), this.getTargetHost()]).then((data) => {
      if (this.objectType === 'HOST' && this.nodeType === 'INSTANCE') {
        const statusMap = ['SUCCESS', 'FAILED', 'NODATA']
        const [, setData] = data
        this.host.cacheData = setData
        this.host.data = setData
        statusMap.forEach((status) => {
          const successList = this.host.data.filter(item => item.status === status)
          const key = status.toLocaleLowerCase()
          this[key].count = successList.length
          this[key].data = successList
        })
      } else {
        const [, setData] = data
        this.treeData = setData
        this.host.cacheTreeData = setData
        this.traverseTree(this.treeData)
      }
      // 第一次进入默认选择全部
      this.handleStatusScope('all')
      this.getChartTotal(data[0].plugin_info.metric_json)
      this.$store.commit(
        'app/SET_NAV_TITLE',
        `${this.$t('route-' + '检查视图').replace('route-', '')} - #${this.$route.params.id} ${this.collectName}`
      )
    })
      .finally(() => {
        this.leftLoading = false
        this.rightLoading = false
      })
  },
  methods: {
    // 点击自定义新增option
    handleAddOption(item) {
      item && this.dateObject.options.push(item)
    },
    handleFullScreen(isFullScreen) {
      this.isFullScreen = isFullScreen
    },
    handleAlgorthmChange(v) {
      this.algorithm.active = v
    },
    filterMethod(keyword, node) {
      if (this.selectedScope === 'all') {
        return node.data.name.indexOf(keyword) > -1
      }
      return node.data.name.indexOf(keyword) > -1 && node.data.status === this.host.status
    },
    handleSearch(v) {
      if (this.objectType === 'HOST' && this.nodeType === 'INSTANCE') {
        if (v) {
          this.host.data = this.host.cacheData.filter(item => item.ip.indexOf(v) > -1
          || item.bk_host_name.toLocaleLowerCase().indexOf(v) > -1
          || item.bk_host_name.indexOf(v) > -1)
        } else {
          this.host.data = this.host.cacheData
        }
      } else if (this.$refs.bkBigTree) {
        this.$refs.bkBigTree.filter(this.searchText)
      }
    },
    handleStatusScope(status) {
      if (status !== 'all' && this[status].count === 0) return
      this.selectedScope = status
      this.handleSelectTotal()
      this.searchText = ''
      if (status === 'all') {
        this.host.status = ''
        if (this.objectType === 'HOST' && this.nodeType === 'INSTANCE') {
          this.host.data = this.host.cacheData
        } else {
          this.treeData = this.host.cacheTreeData
        }
        return
      }
      this.host.status = status
      if (this.objectType === 'HOST' && this.nodeType === 'INSTANCE') {
        this.host.data = this[status].data
      } else {
        this.treeData = this.trimTree()
      }
    },
    handleSelectTotal() {
      let result = []
      this.host.active = ''
      if (this.selectedScope === 'all') {
        result = []
      } else {
        result = this[this.selectedScope].data
      }
      this.host.param = result.map((item) => {
        if (typeof item.service_instance_id !== 'undefined') {
          return item.service_instance_id
        }
        return { ip: item.ip, bk_cloud_id: item.bk_cloud_id }
      })
    },
    handleSelectHost(data) {
      this.host.active = data.ip
      this.host.param = [{ ip: data.ip, bk_cloud_id: data.bk_cloud_id }]
    },
    handleSelectNode(node) {
      if (this.objectType === 'HOST') {
        this.host.active = node.instance_id
        this.host.param = [{ ip: node.ip, bk_cloud_id: node.bk_cloud_id }]
      } else {
        this.host.active = node.service_instance_id
        this.host.param = [node.service_instance_id]
      }
    },
    handleSelectMetric(v, metric) {
      const width = (this.$refs.viewChart.clientWidth / 2) - 12
      this.chartList = v.map(item => ({
        width,
        name: item.name,
        title: this.setTitle(item.description, item.name, item.unit).title,
        subtitle: this.setTitle(item.description, item.name, item.unit).subtitle
      }))
      this.metric.value = metric
    },
    getInfo() {
      return new Promise((resolve, reject) => {
        collectConfigDetail({ id: this.$route.params.id }).then((data) => {
          this.objectType = data.target_object_type
          this.nodeType = data.target_node_type
          this.collectName = data.name
          this.metric.list = []
          this.chartList = []
          // this.getChartTotal(data.plugin_info.metric_json)
          resolve(data)
        })
          .catch((err) => {
            this.rightLoading = false
            reject(err)
          })
      })
    },
    getTargetHost() {
      return new Promise((resolve, reject) => {
        frontendTargetStatusTopo({ id: this.$route.params.id }).then((data) => {
          resolve(data)
        })
          .catch((err) => {
            this.leftLoading = false
            reject(err)
          })
      })
    },
    /**
     * 根据metric数据生成对应的图表容器与指标选择器数据
     */
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
          if (data.monitor_type === 'metric' && data.is_active) {
            startCollector = true
            // 指标选择器数据
            groupItem.children.push({
              unit: data.unit,
              id: data.name,
              name: data.name,
              // description: data.description ? `${data.description}(${data.name})` : data.name
              description: data.description ? data.description : data.name
            })
            // 图表容器数据
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
      this.cachAllChartElement = this.chartList
    },
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
          style: {
            color: '#63656E',
            fontSize: '14px',
            fontWeight: 'bold'
          },
          align: 'left',
          y: 20
        },
        subtitle: {
          text: subtitle,
          style: {
            color: '#979BA5',
            fontSize: '12px',
            fontWeight: 'bold'
          },
          align: 'left',
          y: 34
        }
      }
    },
    /**
     * 根据目标状态过滤tree数据
     */
    trimTree() {
      let stack = []
      const result = []
      const treeData = JSON.parse(JSON.stringify(this.host.cacheTreeData))
      const traverse = (node) => {
        stack.unshift(node)
        if (node.children) {
          node.children.forEach((item) => {
            traverse(item)
          })
        } else {
          node.isDelete = node.status.toLocaleLowerCase() !== this.host.status
        }
      }
      treeData.forEach((node) => {
        stack = []
        traverse(node)
        stack.forEach((item) => {
          if (item.children) {
            item.children = item.children.filter(node => !node.isDelete)
            item.isDelete = !item.children.length
          }
        })
        const rootNode = stack[stack.length - 1]
        if (!rootNode.isDelete) {
          result.push(rootNode)
        }
      })
      return result
    },
    traverseTree(treeData) {
      const hosts = new Set()
      const expandeds = new Set()
      const key = this.objectType === 'HOST' ? 'name' : 'service_instance_id'
      const recursiveTraverse = (node) => {
        if (expandeds.size < 4) {
          expandeds.add(node.id)
        }
        if (node.children) {
          node.children.forEach((item) => {
            recursiveTraverse(item)
          })
        } else if ((node.ip || node.instance_name) && !hosts.has(node[key])) {
          hosts.add(node[key])
          if (node.status === 'SUCCESS') {
            this.success.count += 1
            this.success.data.push(node)
          } else if (node.status === 'FAILED') {
            this.failed.count += 1
            this.failed.data.push(node)
          } else if (node.status === 'NODATA') {
            this.nodata.count += 1
            this.nodata.data.push(node)
          }
        }
      }
      treeData.forEach((node) => {
        recursiveTraverse(node)
      })
      this.defaultExpandedNodes = [...expandeds]
    },
    getChartData(chart) {
      return (startTime, endTime, isSelection = false) => new Promise((resolve, reject) => {
        const params = {
          id: this.$route.params.id,
          method: this.algorithm.active,
          metric: chart.name,
          time_range: `${moment(startTime).format()} -- ${moment(endTime).format()}`
        }
        if (this.objectType === 'HOST') {
          params.host_list = this.host.param
        } else if (this.objectType === 'SERVICE') {
          params.instance_list = this.host.param
        }
        if (!isSelection) {
          if (Array.isArray(this.dateObject.value)) {
            params.time_range = [moment(this.dateObject.value[0]).format(), moment(this.dateObject.value[1])
              .format()].join(' -- ')
          } else {
            params.time_range = [moment().subtract(+this.dateObject.value * 60 * 60 * 1000, 'ms')
              .format(), moment().format()].join(' -- ')
          }
        }
        graphPoint(params).then((data) => {
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
      padding: 0 6px;
      .title {
        display: flex;
        align-items: center;
        padding: 10px 0 10px 14px;
        color: #63656e;
        .bk-button {
          min-width: 54px;
          &.first {
            border-radius: 12px 0 0 12px;
          }
          &.last {
            border-radius: 0 12px 12px 0;
          }
          &.bk-button-small {
            height: 24px;
          }
          &.is-selected {
            background-color: #3a84ff;
            color: #fff;
          }
        }
        .status {
          display: inline-block;
          width: 8px;
          height: 8px;
          margin-right: 4px;
          border-radius: 50%;
          border: 1px solid;
          &.success {
            background-color: #94f5a4;
            border-color: #2dcb56;
          }
          &.failed {
            background-color: #fd9c9c;
            border-color: #ea3636;
          }
          &.nodata {
            background-color: #dcdee5;
            border-color: #c4c6cc;
          }
        }
      }
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
        .host-name {
          color: #c4c6cc;
        }
        .item {
          padding-left: 16px;
          height: 32px;
          line-height: 32px;
          white-space: nowrap;
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
          &.failed {
            background-color: #fd9c9c;
            border-color: #ea3636;
          }
          &.nodata {
            background-color: #dcdee5;
            border-color: #c4c6cc;
          }
        }
        .big-tree-wrapper {
          width: 100%;
          height: calc(100vh - 194px);
          overflow: auto;
        }
        /deep/ .bk-big-tree {
          width: max-content;
          min-width: 100%;
          .is-root {
            .node-options {
              margin-left: 26px;
            }
          }
          .bk-big-tree-node {
            cursor: default;
            padding-left: calc(var(--level) * 40px);
            &:hover {
              background-color: #e1ecff;
            }
          }
          .bk-big-tree-node.is-leaf {
            padding-left: 0;
            cursor: default;
            .bk-tree-node {
              width: max-content;
              padding-left: calc(var(--level) * 40px);
              &:hover {
                background-color: #e1ecff;
                color: #3a84ff;
              }
              &.active {
                color: #3a84ff;
                background-color: #e1ecff;
                width: 100%;
              }
              span {
                cursor: pointer;
              }
            }
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
      .algorithm {
        width: 100px;
      }
      .operator-group {
        flex: 1;
        display: flex;
        justify-content: flex-end;
        .metric {
          display: inline-block;
          height: 32px;
          margin-left: 5px;
          vertical-align: top;
          text-align: left;
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
      margin-right: -15px;
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
    .chart-item {
      box-sizing: border-box;
      margin-top: 16px;
      border: 1px solid #f0f1f5;
      transition: width .33s cubic-bezier(.23, 1, .32, 1);
      flex: 0 0 calc(50% - 15px);
      margin: 0 15px 15px 0;
      max-width: calc(50% - 15px);
      &-subtitle {
        color: #979ba5;
        font-size: 12px;
        font-weight: bold;
      }
    }
  }
}
</style>
