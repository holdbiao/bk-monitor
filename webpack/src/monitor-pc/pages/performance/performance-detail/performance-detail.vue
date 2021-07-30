<template>
  <div class="performance-detail" @animationend="handleAnimationEnd" v-bkloading="{ 'isLoading': left.panelLoading || right.loading }">
    <div class="performance-detail-left"
         :style="{ 'flex-basis': left.width + 'px', width: left.width + 'px' }"
         data-tag="resizeTarget"
         @mousedown="handleMouseDown"
         @mousemove="handleMouseMove"
         @mouseout="handleMouseOut">
      <bk-tab :active.sync="left.active" class="left-tab">
        <bk-tab-panel
          v-for="(panel, index) in left.panels"
          v-bind="panel"
          :key="index">
          <ul class="list" v-if="panel.list.length">
            <li v-for="(item,childIndex) in panel.list" @click="handleClickItem(panel,childIndex)" class="list-item" :key="childIndex"
                :class="{ 'is-active': panel.active === childIndex }">
              <span class="process-status-icon"
                    v-if="panel.name === 'process'"
                    :style="{ 'background-color': item.color }">
              </span>
              <span class="list-item-name">{{item.name}}</span>
              <div v-if="panel.name === 'performance'">
                <span class="list-item-val " v-if="item.type !== 'net'">{{item.value}}</span>
                <span class="list-item-val" v-else>
                  <i class="bk-icon icon-arrows-up" :style="{ color: panel.active === childIndex ? '#FFFFFF' : '#3A84FF' }"></i>{{item.upLink}}
                  <i class="bk-icon icon-arrows-down" :style="{ color: panel.active === childIndex ? '#FFFFFF' : '#3A84FF' }"></i>{{item.downLink}}</span>
              </div>
            </li>
          </ul>
          <div class="list-empty" v-else>
            <bk-exception type="empty" scene="part"></bk-exception>
          </div>
        </bk-tab-panel>
      </bk-tab>
      <div class="process-guide" @click="handleGotoLink('processMonitoring')">
        <a class="bk-icon icon-cog-shape"></a>
        <span>{{ $t('进程监控配置指引') }}</span>
      </div>
      <div id="guide-template" class="guide-template">
      </div>
      <div class="resize-line"
           v-show="resizeState.show"
           :style="{ left: resizeState.left + 'px' }">
      </div>
    </div>
    <div ref="performanceDetail" class="performance-detail-view">
      <div class="view-title">
        <span class="view-title-name"> {{ $t('监控视图') }} </span>
        <div class="view-title-list">
          <bk-select
            v-show="left.active === 'process'"
            class="processs-pid-selector"
            searchable
            multiple
            @change="handleSelectPid"
            v-model="processPids.value">
            <bk-option v-for="pid in processPids.list" :key="pid" :name="pid" :id="pid"></bk-option>
          </bk-select>
          <bk-select :popover-min-width="160" style="margin-right: 4px;" v-model="refreshOption.value" :clearable="false" :popover-width="110">
            <!-- <span slot="extension">刷新间隔</span> -->
            <bk-option v-for="(opt, index) in refreshOption.list" :disabled="opt.disabled" :key="index" :name="opt.name" :id="opt.id"></bk-option>
          </bk-select>
          <monitor-date-range class="date-range" @add-option="handleAddOption" v-model="view.title.value" :options="view.title.list" @change="changeTimeRange"></monitor-date-range>
        </div>
      </div>
      <div class="view-processid-status" v-if="left.active === 'process'">
        <div class="process-port" v-for="(item, index) in processPorts.viewList" :key="index">
          <div v-if="item.status !== 2">
            <span class="status-dot" :style="{ 'background-color': item.color }"></span>
            <span>{{item.port}}</span>
          </div>
          <div v-else v-bk-tooltips="item.toolTips">
            <span class="status-dot" :style="{ 'background-color': item.color }"></span>
            <span>{{item.port}}</span>
          </div>
        </div>
      </div>
      <!-- 生成唯一key， 切换时间或者图表类型时保证图表更新  -->
      <div :class="['view-chart', { 'empty': !view.chart.list.length }]" ref="viewChart">
        <template v-if="view.chart.list.length">
          <div v-for="(chart,index) in view.chart.list"
               v-bkloading="{ 'isLoading': left.active === 'process' ? !processPids.load : false }"
               class="view-chart-item"
               :key="index"
               :style="{ 'margin-right': '15px' }">
            <div :style="{ 'width': `${view.chart.width}px`, 'height': '250px' }">
              <monitor-charts :ref="'chart-' + index"
                              v-if="left.active === 'process' ? processPids.load : true"
                              :title="chart.description"
                              :reflesh-time-interval="refreshOption.value"
                              :get-series-data="getNewChartData(index)"
                              :width="`${view.chart.width}`"
                              :height="250"
                              :key="processName + '-' + chart.index_id + '-' + processPids.value.join('-') + '-' + view.title.value"
                              :observe-parent="true"
                              :time-range="+view.title.value * 60 * 60 * 1000"
                              :unit="chart.unit_display">
              </monitor-charts>
            </div>

            <div class="view-chart-item-list">
              <top-list :show="chart.show"></top-list>
            </div>
          </div>
        </template>
        <div class="view-empty" v-else>
          <bk-exception type="empty" scene="part"></bk-exception>
        </div>
      </div>
    </div>
    <transition name="slide">
      <div class="performance-detail-right" :class="{ 'show': right.show }" v-show="right.show">
        <ul v-show="right.show">
          <li v-for="(item, index) in right.hostInfo" :key="index">
            <span class="title">{{item.title}}:</span>
            <span v-if="item.type === 'status'" class="content" :style="{ 'color': item.value === 0 ? '#2dcb56' : '#ea3636' }">{{item.name}}</span>
            <bk-popover placement="right">
              <span v-if="item.type !== 'status' && item.type !== 'module' && index < 3 && item.value !== '--'" class="info"
                    @click="item.type === 'innerip' && handleToCmdbHost()" :class="{ 'inner-ip': item.type === 'innerip' }">
                <template v-if="item.type === 'innerip'">{{item.value}}&nbsp;<i class="icon-monitor icon-mc-link"></i></template>
                <template v-else>{{item.value}}</template>
              </span>
              <div slot="content"><span style="cursor: pointer;" @click="copy(item.value)"> {{ $t('复制') }} </span></div>
            </bk-popover>
            <span v-if="item.type !== 'status' && item.type !== 'module' && index < 3 && item.value === '--'" class="info">{{item.value}}</span>
            <span v-if="item.type !== 'status' && item.type !== 'module' && index > 2" class="info">{{item.value}}</span>
            <div v-if="item.type === 'module'" class="module-text-wrapper">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <span v-html="item.value"
                    class="content"
                    :title="item.len <= 2 ? item.text : ''"
                    :class="{ 'module-text': !right.showAllModuleContent }">
              </span>
              <bk-button v-if="item.len > 2" style="position: relative; top: -5px; line-height: 1; margin-left: -8px;" @click="right.showAllModuleContent = !right.showAllModuleContent" :text="true" title="primary">{{ right.showAllModuleContent ? $t('收起') : $t('展开')}}</bk-button>
            </div>
          </li>
          <li>
            <div class="alarm-info">
              <div class="unrestored-alarm-count">
                <div
                  v-authority="{ active: alarmInfo.alarmCount > 0 && !authority.EVENT_VIEW_AUTH }"
                  class="count"
                  :style="{ 'color': alarmInfo.alarmCount > 0 ? '#FF9C01' : '#979BA5' }"
                  :class="{ 'pointer-tolink': alarmInfo.alarmCount > 0 }"
                  @click="alarmInfo.alarmCount === 0 || authority.EVENT_VIEW_AUTH
                    ? handleToEventCenter()
                    : handleShowAuthorityDetail(performanceAuth.EVENT_VIEW_AUTH)">
                  {{alarmInfo.alarmCount}}
                </div>
                <div class="desc"> {{ $t('未恢复告警') }} </div>
              </div>
              <div class="start-stop-count">
                <div
                  v-authority="{ active: (alarmInfo.enabled > 0 || alarmInfo.disabled > 0) && !authority.RULE_VIEW_AUTH }"
                  class="count"
                  :class="{ 'pointer-tolink': alarmInfo.enabled > 0 || alarmInfo.disabled > 0 }"
                  @click="!(alarmInfo.enabled > 0 || alarmInfo.disabled > 0) || authority.RULE_VIEW_AUTH
                    ? handleToStrategyConfig()
                    : handleShowAuthorityDetail(performanceAuth.RULE_VIEW_AUTH)">
                  <span :style="{ 'color': alarmInfo.enabled > 0 ? '#2DCB56' : '#979BA5' }">{{alarmInfo.enabled}}</span>
                  /{{alarmInfo.disabled}}
                </div>
                <div class="desc"> {{ $t('启停告警策略') }} </div>
              </div>
            </div>
          </li>
        </ul>
        <div class="eject-right-sidebar positon-arrow" @click="handleRightClick">
          <span class="bk-icon icon-angle-right"></span>
        </div>
      </div>
    </transition>
    <div class="hide-right-sidebar positon-arrow" @click="handleRightClick" v-show="!right.show">
      <span class="bk-icon icon-angle-left"></span>
    </div>
  </div>
</template>

<script>
import TopList from '../top-list/top-list'
import { debounce } from 'throttle-debounce'
import { resizeMixin } from '../../../common/mixins.js'
import documentLinkMixin from '../../../mixins/documentLinkMixin'
import moment from 'moment'
import MonitorCharts from '../../../components/monitor-charts/monitor-charts.vue'
import MonitorDateRange from '../../../components/monitor-date-range/monitor-date-range'
import { copyText } from '../../../../monitor-common/utils/utils'
import { addListener, removeListener } from 'resize-detector'
import {
  SET_PERFORMANCE_VIEWTYPE,
  SET_PERFORMANCE_PROCESS,
  SET_PERFORMANCE_HOST } from '../../../store/modules/performance.ts'
import { createNamespacedHelpers } from 'vuex'
import { hostIndex,
  hostPerformanceDetail,
  hostProcessStatus,
  graphPoint,
  hostComponentInfo,
  getFieldValuesByIndexId } from '../../../../monitor-api/modules/performance'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import * as performanceAuth from '../authority-map'
const { mapGetters, mapMutations } = createNamespacedHelpers('performance')
export default {
  name: 'performance-detail',
  components: {
    TopList,
    MonitorCharts,
    MonitorDateRange
  },
  mixins: [resizeMixin, documentLinkMixin, authorityMixinCreate(performanceAuth)],
  data() {
    return {
      performanceAuth,
      innerip: '',
      hostId: '',
      routeParams: {
        view: 'performance',
        ip: null,
        cloudId: null
      },
      left: {
        panels: [
          {
            name: 'performance',
            label: this.$t('主机视角'),
            list: [],
            active: 0
          },
          {
            name: 'process',
            label: this.$t('进程视角'),
            list: [],
            active: 0
          }
        ],
        panelLoading: true,
        active: 'performance',
        width: this.$i18n.locale === 'en' ? 280 : 230
      },
      osName: '',
      processGuideTpl: {
        allowHtml: true,
        width: 240,
        trigger: 'click',
        theme: 'light',
        content: '#process-guide',
        placement: 'top-start',
        relative: true
      },
      processPorts: {
        value: [],
        viewList: []
      },
      processPids: {
        value: [],
        list: [],
        load: false
      },
      refreshOption: {
        list: [
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
        popoverMinWidth: 110,
        value: -1
      },
      alarmInfo: {
        alarmCount: 0,
        disabled: 0,
        enabled: 0
      },
      view: {
        title: {
          list: [
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
            },
            {
              value: 720,
              name: this.$t('1个月')
            }
          ],
          value: 1,
          active: 0
        },
        chart: {
          list: [],
          style: {
            width: 500,
            height: 250
          },
          width: 0,
          origin: 0
        }
      },
      right: {
        show: true,
        showAllModuleContent: false,
        hostInfo: [],
        loading: true
      },
      lisenResize: null,
      htmlConfig: {
        allowHtml: true,
        width: 240,
        trigger: 'click',
        theme: 'light',
        content: '#demo-html1',
        placement: 'top',
        relative: true,
        onShow: () => {}
      },
      setIntervalPerformance: null
    }
  },
  computed: {
    ...mapGetters(['process', 'hostList', 'viewType']),
    performanceItemIndex() {
      return this.left.panels[0].active
    },
    processItemIndex() {
      return this.left.panels[1].active
    },
    processName() {
      if (this.left.panels[1].list.length) {
        return this.left.panels[1].list[this.processItemIndex].name
      }
      return ''
    }
  },
  watch: {
    'right.show': {
      handler: 'handleChartsResize'
    },
    async 'left.active'(val) {
      this.generationGraphElement(this.left.active)
      if (val === 'process') {
        this.getProcessPortsStatus()
        await this.getFieldValues().catch(() => {})
      }
    },
    processItemIndex(val) {
      this.getProcessPorts(val)
    },
    'refreshOption.value'(val) {
      if (val > 0 && this.left.active === 'performance') {
        this.setIntervalPerformance = setInterval(() => {
          hostPerformanceDetail({
            ip: this.routeParams.ip,
            bk_cloud_id: this.routeParams.cloudId
          }).then((data) => {
            this.getPerformanceItemVal(data)
          })
            .catch(() => {
              this.left.panelLoading = false
              this.right.loading = false
            })
        }, val)
      } else {
        clearInterval(this.setIntervalPerformance)
      }
    }
  },
  mounted() {
    if (this.routeParams.ip) {
      this.view.chart.origin = this.$refs.viewChart.clientWidth
      this.lisenResize = debounce(300, v => this.handleWindowResize(v))
      addListener(this.$refs.performanceDetail, this.lisenResize)
    }
  },
  async created() {
    const { params } = this.$route
    if (params.id) {
      this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      this.handleRouteParams(params)
      if (!this.hostList.length) {
        await this.getHostIndexList()
      }
      await Promise.all([this.getPerformanceInfo(), this.getProcessInfo()]).catch(() => {})
      if (this.process) {
        this.openSpecifyView()
      }
      this.$store.commit('app/SET_NAV_TITLE', `${this.$t('route-' + '主机详情').replace('route-', '')} - ${this.innerip}`)
    } else {
      this.$router.push({ name: 'performance' })
    }
  },
  beforeDestroy() {
    this.$refs.performanceDetail && removeListener(this.$refs.performanceDetail, this.lisenResize)
  },
  methods: {
    ...mapMutations([SET_PERFORMANCE_VIEWTYPE, SET_PERFORMANCE_PROCESS, SET_PERFORMANCE_HOST]),
    handleToCmdbHost() {
      window.open(`${this.$store.getters.cmdbUrl}/#/resource/host/${this.hostId}`, '_blank')
    },
    handleAnimationEnd() {
      this.handleWindowResize()
    },
    copy(val) {
      copyText(val)
      this.bkMessage('success', this.$t('复制成功'))
    },
    bkMessage(theme, message) {
      this.$bkMessage({
        theme,
        message,
        ellipsisLine: 0
      })
    },
    handleRightClick() {
      this.right.show = !this.right.show
    },
    /**
             * @description 获取hostlist
             */
    async getHostIndexList() {
      await hostIndex().then((data) => {
        this[SET_PERFORMANCE_HOST](data)
      })
        .catch((err) => {
          console.error(err)
        })
    },
    async handleClickItem(panel, index) {
      panel.active = index
      if (this.left.active === 'process') {
        this.processPids.value = []
        this.getProcessPortsStatus()
        await this.getFieldValues().catch(() => {})
      }
      this.generationGraphElement(this.left.active)
    },
    handleRouteParams(params) {
      const index = params.id.indexOf('-')
      const ip = params.id.slice(0, index)
      const id = params.id.slice(index + 1)
      const process = params.processId || ''
      this[SET_PERFORMANCE_VIEWTYPE](!process || process === 'system' ? 'performance' : 'process')
      this[SET_PERFORMANCE_PROCESS](process)
      this.routeParams.ip = ip
      this.routeParams.cloudId = parseInt(id, 10)
    },
    handleSelectPid() {
      this.generationGraphElement(this.left.active)
    },
    handleChartsResize(v) {
      this.$nextTick(() => {
        const width = v ? (this.$refs.performanceDetail.clientWidth - 232 - 24) : this.$refs.viewChart.clientWidth
        this.view.chart.origin = width
        const nextWidth = v ? width - 360 : width + 360
        if (nextWidth > 1246) {
          this.view.chart.width = +((nextWidth - 35) / 2).toFixed(0)
        } else {
          this.view.chart.width = nextWidth - 18
        }
      })
    },
    handleWindowResize() {
      if (!this.$refs.viewChart) return
      const width = this.$refs.viewChart.clientWidth
      this.view.chart.origin = width
      this.view.chart.width = width
      if (width > 1246) {
        this.view.chart.width = +((width - 35) / 2).toFixed(0)
      } else {
        this.view.chart.width = width - 18
      }
      // if (this.$refs.daterange.visible) {
      //     this.setBkDatePosition()
      // }
    },
    handleSeriesClick(e, o) {
      o.show = !o.show
    },
    async getPerformanceInfo() {
      await hostPerformanceDetail({
        ip: this.routeParams.ip,
        bk_cloud_id: this.routeParams.cloudId
      }).then((data) => {
        this.innerip = data.bk_host_innerip
        this.hostId = data.bk_host_id
        this.osName = data.bk_os_name
        this.getPerformanceItemVal(data)
        // 如果默认打开进程视图，则主机视图图表不渲染
        if (this.left.active === this.viewType) {
          this.generationGraphElement('performance')
        }
        this.alarmInfo.alarmCount = data.alarm_count
        this.alarmInfo.disabled = data.alarm_strategy.disabled
        this.alarmInfo.enabled = data.alarm_strategy.enabled
        this.right.hostInfo = [
          { title: this.$t('主机名'), value: data.bk_host_name || '--', type: 'hostName' },
          { title: this.$t('内网IP'), value: data.bk_host_innerip || '--', type: 'innerip' },
          { title: this.$t('外网IP'), value: data.bk_host_outerip || '--', type: 'outerip' },
          { title: this.$t('所属业务'), value: data.bk_biz_name, type: 'bizName' },
          { title: this.$t('主机运营'), value: data.bk_state || '--', type: 'state' },
          { title: this.$t('采集状态'), value: data.status !== null ? data.status : '--',
            name: this.collectorStatus(data.status), type: 'status' },
          { title: this.$t('OS类型'), value: data.bk_os_name || '--', type: 'osName' },
          { title: this.$t('云区域'), value: data.bk_cloud_name || '--', type: 'cloudName' }
        ]
        this.osName = data.bk_os_name
        this.right.hostInfo.push({ title: this.$t('所属模块'),
          text: data.module.map(item => item.topo_link_display.join('-')).join('\n'),
          value: data.module.map(item => item.topo_link_display.join('-')).join('<br/>'),
          type: 'module',
          len: data.module.length })
      })
        .catch(() => {})
        .finally(() => {
          this.left.panelLoading = false
          this.right.loading = false
        })
    },
    /**
             * @param {string} viewType
             * @description 获取某指标项的所有图表容器
             */
    generationGraphElement(viewType) {
      const viewTypeIndex = viewType === 'performance' ? 0 : 1
      const index = this.left.panels[viewTypeIndex].active
      const graphId = viewType === 'performance' ? this.left.panels[viewTypeIndex].list[index].type : 'process'
      this.view.chart.list = []
      this.view.chart.list = this.hostList.filter((host) => {
        host.show = false
        const osName = this.osName || 'linux'
        const os = host.os.find(item => osName.toLocaleLowerCase().includes(item.toLocaleLowerCase()))
        return host.category_id === graphId && os
      })
      this.$nextTick(() => {
        this.handleWindowResize()
      })
    },
    getPerformanceItemVal(data) {
      const list = [
        {
          name: 'CPU',
          type: 'cpu',
          value: data.cpu_usage.val !== null ? `${data.cpu_usage.val}${data.cpu_usage.unit}` : '--'
        },
        {
          name: this.$t('内存'),
          type: 'mem',
          value: data.mem_usage.val !== null ? `${data.mem_usage.val}${data.mem_usage.unit.replace(/\s+/, '')}` : '--'
        },
        {
          name: this.$t('网络'),
          type: 'net',
          downLink: data.net.speed_recv.val !== null ? `${data.net.speed_recv.val}${data.net.speed_recv.unit}` : '--',
          upLink: data.net.speed_sent.val ? `${data.net.speed_sent.val}${data.net.speed_sent.unit}` : '--'
        },
        {
          name: this.$t('磁盘'),
          type: 'disk',
          value: data.disk_usage.val !== null ? `${data.disk_usage.val}${data.disk_usage.unit}` : '--'
        },
        {
          name: this.$t('系统进程'),
          type: 'system_env',
          value: data.component_count.val !== null ? `${data.component_count.val}${data.component_count.unit}` : '--'
        }
      ]
      this.left.panels[0].list = list
    },
    async getProcessInfo() {
      await hostProcessStatus({
        ip: this.routeParams.ip,
        bk_cloud_id: this.routeParams.cloudId
      }).then((data) => {
        data.forEach((process) => {
          this.left.panels[1].list.push({
            name: process.display_name,
            status: process.status,
            ports: process.ports,
            protocol: process.protocol,
            color: this.statusColor(process.status)
          })
        })
      })
        .catch(() => {})
    },
    handleTimeRangeStr() {
      let timeRangeStr = ''
      let timeRange = this.view.title.value
      const now = moment().format()
      if (Number.isInteger(timeRange)) {
        const beforeTimeStr = moment().subtract(timeRange, 'hours')
          .format()
        timeRangeStr = `${beforeTimeStr} -- ${now}`
      } else {
        Array.isArray(timeRange) && (timeRange = `${timeRange[0]} -- ${timeRange[1]}`)
        timeRangeStr = timeRange
      }
      return timeRangeStr
    },
    getNewChartData(index) {
      return async (startTime, endTime, isSelection = false) => new Promise((resolve) => {
        const chartObj = this.view.chart.list[index]
        const params = {
          ip_list: [{ ip: this.routeParams.ip, bk_cloud_id: this.routeParams.cloudId }],
          index_id: chartObj.index_id,
          dimension_field_value: '',
          time_range: this.handleTimeRangeStr()
        }
        // 当图表选择时间段
        if (isSelection) {
          params.time_range = `${moment(startTime).format()} -- ${moment(endTime).format()}`
        }
        if (this.left.active === 'process') {
          params.dimension_field_value = this.processName
          params.dimension_field = 'display_name'
          params.filter_dict = { pid: this.processPids.value }
          if (this.processPids.value) {
            params.group_fields = ['pid']
          }
        }
        graphPoint(params, { needMessage: false }).then((data) => {
          if (data?.data) {
            resolve(data.data)
          } else {
            resolve({})
          }
        })
          .catch(() => {
            resolve({})
          })
      })
    },
    setPortStatus(data) {
      this.processPorts.viewList.forEach((item) => {
        item.status = data[item.port] ? data[item.port].status : -1
        item.color = this.statusColor(item.status)
        if (item.status === 2) {
          item.toolTips = {
            // eslint-disable-next-line vue/max-len
            content: `${this.$t('监听端口')}${data[item.port].actual_ip}:${item.port}${this.$t('存在,但端口绑定IP与CMDB配置')}${data[item.port].config_ip}:${item.port}${this.$t('不符')}`,
            showOnInit: false,
            placements: ['top']
          }
        }
      })
    },
    getProcessPorts(index) {
      this.processPorts.viewList = []
      const { ports } = this.left.panels[1].list[index]
      ports.forEach((port) => {
        const item = {
          port,
          status: -1
        }
        item.color = this.statusColor(item.status)
        this.processPorts.viewList.push(item)
      })
    },
    getProcessPortsStatus() {
      if (this.left.panels[1].list.length) {
        hostComponentInfo({
          ip: this.routeParams.ip,
          bk_cloud_id: this.routeParams.cloudId,
          name: this.left.panels[1].list[this.processItemIndex].name
        }).then((data) => {
          this.getProcessPorts(this.processItemIndex)
          this.setPortStatus(data.ports)
        })
      }
    },
    async getFieldValues() {
      if (this.left.panels[1].list.length) {
        this.processPids.load = false
        const condition = {
          ip: this.routeParams.ip,
          bk_cloud_id: this.routeParams.cloudId,
          display_name: this.left.panels[1].list[this.processItemIndex].name,
          time__gte: `${this.view.title.value}h`
        }
        await getFieldValuesByIndexId({
          index_id: this.view.chart.list[0].index_id,
          field: 'pid',
          condition
        }).then((data) => {
          if (data.length) {
            this.processPids.list = data
            this.processPids.value.push(...data)
          }
        })
          .catch(() => {})
          .finally(() => {
            this.processPids.load = true
          })
      } else {
        this.processPids.load = true
      }
    },
    openSpecifyView() {
      this.left.active = this.viewType
      const name = this.left.active === 'process' ? this.process : 'system_env'
      const panels = this.left.active === 'process' ? this.left.panels[1] : this.left.panels[0]
      const processIndex = panels.list.findIndex(item => item.name === name)
      if (processIndex > -1) {
        panels.active = processIndex
      } else {
        panels.active = 0
      }
    },
    statusColor(status) {
      const colors = {
        '-1': '#DCDEE5',
        0: '#2DCB56',
        1: '#EA3636',
        2: '#FFEB00'
      }
      return colors[status]
    },
    collectorStatus(status) {
      const statusObj = {
        '-1': this.$t('未知'),
        0: this.$t('正常'),
        1: this.$t('离线'),
        2: this.$t('Agent未安装'),
        3: this.$t('数据未上报')
      }
      return statusObj[status]
    },
    handleToEventCenter() {
      if (this.alarmInfo.alarmCount > 0) {
        const endTime = moment().format('YYYY-MM-DD HH:mm:ss')
        const beginTime = moment(endTime).add(-7, 'd')
          .format('YYYY-MM-DD HH:mm:ss')
        this.$router.push({ name: 'event-center',
          params: { ip: this.right.hostInfo[1].value, status: 'ABNORMAL', beginTime, endTime } })
      }
    },
    handleToStrategyConfig() {
      if (this.alarmInfo.enabled > 0 || this.alarmInfo.disabled > 0) {
        this.$router.push({
          name: 'strategy-config',
          params: {
            ip: this.right.hostInfo[1].value,
            bkCloudId: `${this.routeParams.cloudId}`
          }
        })
      }
    },
    // 点击自定义新增option
    handleAddOption(item) {
      item && this.view.title.list.push(item)
    },
    // 改变时间段
    changeTimeRange(time) {
      if (Number.isInteger(time)) {
        this.refreshOption.list.forEach((item) => {
          item.disabled = false
        })
      } else {
        this.view.title.value = Array.isArray(time) ? (`${time[0]} -- ${time[1]}`) : time
        this.refreshOption.value = -1
        this.refreshOption.list.forEach((item) => {
          if (item.id !== -1) {
            item.disabled = true
          }
        })
      }
      // this.generationGraphElement(this.left.active)
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../../home/common/mixins";

  .performance-detail {
    margin: -20px -24px 0;
    position: relative;
    background: #fff;
    height: calc(100vh - 52px);
    display: flex;
    overflow: hidden;
    border: 1px solid #dcdee5;
    border-bottom: 0;
    border-top: 0;
    /deep/ .bk-select-name {
      min-width: 84px;
      white-space: normal;
    }
    &-left {
      position: relative;
      flex: 0 0 230px;
      border-right: 1px solid #dcdee5;
      /deep/ .bk-tab {
        &-section {
          padding: 0;
          border: 0;
          height: calc(100vh - 147px);
          overflow: auto;
        }
        &-border-card {
          .bk-tab-header {
            border: 0;
            background-image: linear-gradient(transparent 42px, #dcdee5 0)
          }
        }
        .bk-tab-label-list {
          display: flex;
          width: 100%;
          .bk-tab-label-item {
            flex: 1;
            .bk-tab-label {
              width: 100%;

              @include ellipsis;
            }
          }
        }
      }
      /deep/ .bk-tab-label-item.active:after {
        left: 0;
        width: 100%;
      }
      .list {
        display: flex;
        flex-direction: column;
        height: 100%;
        overflow: auto;
        flex-wrap: nowrap;
        margin: 10px 0;
        padding: 0;
        &-item {
          flex: 1 1 42px;
          display: flex;
          flex-direction: row;
          align-items: center;
          justify-content: flex-start;
          padding: 0 16px;
          border-bottom: 1px solid #dcdee5;

          @include hover();
          &.is-active {
            background: $primaryFontColor;
            color: #fff;
            .list-item-name {
              color: #fff;
            }
            .list-item-text {
              color: #fff;
            }
            .list-item-val {
              color: #fff;
            }
          }
          &:first-child {
            border-top: 1px solid #dcdee5;
          }
          &-name {
            font-size: 14px;
            color: #313238;
            flex: 1;

            @include ellipsis();
          }
          &-val {
            font-size: 12px;
            color: #979ba5;
            flex: 1;
          }
          &-text {
            font-size: 12px;
            color: #979ba5;
          }
          .process-status-icon {
            margin-right: 5px;
            margin-top: 4px;
            display: inline-block;
            width: 4px;
            height: 12px;
            border-radius: 2px;
          }
        }
      }
      .process-guide {
        position: absolute;
        bottom: 0;
        width: 100%;
        height: 42px;
        line-height: 42px;
        text-align: center;
        border-top: 1px solid #dcdee5;
        color: #63656e;
        font-size: 12px;
        cursor: pointer;
        a {
          color: #63656e;
          position: relative;
          top: -1px;
        }
      }
      .list-empty {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
      }
    }
    &-view {
      flex: 1 1 auto;
      background: #fafbfd;
      padding: 0 20px;
      max-height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      &::-webkit-scrollbar {
        width: 0px;
        height: 5px;
      }
      /deep/ .bk-date-picker {
        width: 0;
        .bk-date-picker-rel {
          display: none;
        }
      }
      &::-webkit-scrollbar-thumb {
        border-radius: 20px;
        background: #a5a5a5;
        box-shadow: inset 0 0 6px rgba(204, 204, 204, .3);
      }
      .view-title {
        display: flex;
        height: 34px;
        margin: 12px 0;
        align-items: center;
        justify-content: flex-start;
        transition: width .33s cubic-bezier(.23, 1, .32, 1);
        &-name {
          color: #000;
          font-size: 18px;
        }
        &-list {
          position: relative;
          flex: 1 1 auto;
          height: 32px;
          display: flex;
          justify-content: flex-end;
          &-item {
            flex: 0 0 60px;
            height: 32px;
            text-align: center;
            line-height: 32px;
            background: #fff;
            border: 1px solid #c4c6cc;
            border-right: 0;
            color: $defaultFontColor;
            font-size: 14px;

            @include hover();
            &.is-active {
              background: $primaryFontColor;
              color: #fff;
            }
            &:first-child {
              border-top-left-radius: 2px;
              border-bottom-left-radius: 2px;
            }
            &:last-child {
              border-top-right-radius: 2px;
              border-bottom-right-radius: 2px;
              border-right: 1px solid #c4c6cc;
            }
          }
          .processs-pid-selector {
            margin-right: 4px;
            /deep/ .bk-select-name {
              width: 240px;
            }
          }
          /deep/ .bk-select {
            background-color: #fff;
          }
        }
      }
      .view-processid-status {
        display: flex;
        justify-content: flex-end;
        padding-bottom: 10px;
        .process-port {
          display: inline-block;
          padding: 0 6px;
          border: 1px solid #dcdee5;
          margin-right: 5px;
          border-radius: 10px;
          &:last-child {
            margin-right: 0;
          }
          .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
          }
        }
      }
      .view-chart {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        position: relative;
        margin-right: -15px;
        &.empty {
          height: calc(100% - 80px);
        }
        &-item {
          position: relative;
          border: 1px solid #f0f1f5;
          border-radius: 2px;
          margin-bottom: 15px;
          flex: 0 0 auto;
          .error-message {
            position: absolute;
            top: 48%;
            left: 48%;
            z-index: 100;
          }
          &-list {
            width: 240px;
            position: absolute;
            right: 0;
            top: 0;
            z-index: 10;
          }
        }
      }
      .view-empty {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
    }
    &-right {
      position: relative;
      flex: 0 0 0;
      background: #fff;
      height: calc(100vh - 52px);
      &.show {
        flex: 0 0 360px;
        padding: 14px 20px 20px 10px;
        border-left: 1px solid #dcdee5;
      }
      ul {
        height: 100%;
        padding-left: 0;
        margin: 0;
        font-size: 12px;
        overflow-y: auto;
        li {
          display: flex;
          min-height: 32px;
          line-height: 32px;
          .title {
            display: inline-block;
            width: 80px;
            height: 100%;
            color: #313238;
            text-align: right;
          }
          .content {
            margin-left: 12px;
          }
          .info {
            color: #63656e;
            margin-left: 12px;
          }
          .inner-ip {
            color: #3a84ff;
            cursor: pointer;
            .icon-mc-link {
              font-weight: 600;
            }
          }
          .normal {
            color: #2dcb56;
          }
          .abnormal {
            color: #ea3636;
          }
          .module-text-wrapper {
            display: flex;
            flex-direction: column;
            width: 249px;
            padding-top: 7px;
            span {
              display: block;
              line-height: 1.5;
            }
            .module-text {
              vertical-align: text-top;
              overflow: hidden;
              text-overflow: ellipsis;

              /* stylelint-disable-next-line value-no-vendor-prefix */
              display: -webkit-box;

              /* stylelint-disable-next-line property-no-vendor-prefix */
              -webkit-box-orient: vertical;
              -webkit-line-clamp: 2;
            }
          }
          &:last-child {
            margin-top: 30px;
            height: 90px;
            .alarm-info {
              display: flex;
              flex-direction: row;
              height: 90px;
              width: 100%;
              text-align: center;
              border-radius: 2px;
              border: 1px solid #dcdee5;
              margin-left: 10px;
              .unrestored-alarm-count {
                flex: 1;
                padding-top: 16px;
                border-right: 1px solid #dcdee5;
              }
              .start-stop-count {
                flex: 1;
                padding-top: 16px;
              }
              .desc {
                color: #979ba5;
                line-height: 1.2;
              }
              .count {
                font-size: 24px;
                color: #979ba5;
                line-height: 1.4;
              }
            }
          }
        }
      }
      .eject-right-sidebar {
        left: -10px;
      }
    }
    .slide-enter-active {
      transition: all .33s cubic-bezier(.23, 1, .32, 1);
    }
    .slide-enter {
      transform: translate(360px, 0);
    }
    .slide-leave-active {
      transition: all .33s cubic-bezier(.23, 1, .32, 1);
    }
    .slide-leave-to {
      transform: translate(370px, 0);
    }
    /deep/.bk-tab-label-wrapper .bk-tab-label-list .bk-tab-label-item {
      min-width: 115px;
      &.is-last {
        border-right: 0;
      }
    }
    .positon-arrow {
      position: absolute;
      top: 50%;
      width: 10px;
      height: 32px;
      line-height: 32px;
      border: 1px solid #ddd;
      border-radius: 4px 0px 0px 4px;
      border-right: 0;
      text-align: center;
      font-size: 12px;
      color: #979ba5;
      background: #fff;
      cursor: pointer;
      z-index: 1;
      &:hover {
        color: #3a84ff
      }
    }
    .hide-right-sidebar {
      right: -1px;
    }
    .pointer-tolink {
      cursor: pointer;
    }
  }
</style>
