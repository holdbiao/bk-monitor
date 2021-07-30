<template>
  <div class="uptime-time-detail" v-bkloading="{ isLoading: pageLoading }">
    <div class="detail-left" v-bkloading="{ isLoading: leftLoading }">
      <div class="detail-left-search">
        <span class="bk-icon icon-search"></span>
        <input type="text" :placeholder="$t('请输入关键词')" :value="keyword" @input="handleSearch" />
      </div>
      <ul class="detail-left-list">
        <template v-if="leftListData.length">
          <li class="list-item"
              v-for="(item,index) in leftListData"
              :key="index"
              :class="{ 'item-active': left.active === item.id, 'item-disabled': item.status === 'stoped' }"
              @click="handleLeftItemClick(item.id)">
            <span class="list-item-name" v-bk-overflow-tips>{{item.name}}</span>
            <span class="list-item-num">{{item.available !== null ? item.available + '%' : (item.status === 'stoped' ? $t('已停用') : '--')}}</span>
          </li>
        </template>
        <template v-else>
          <div class="list-empty"> {{ $t('搜索无结果') }} </div>
        </template>
      </ul>
    </div>
    <div class="detail-right" ref="detailRight">
      <div class="detail-right-panel" v-bkloading="{ isLoading: basicLoading }" v-if="activeItem">
        <div class="panel-row"
             v-for="(item, key) in columnMap"
             :key="key">
          <span class="panel-row-name">{{item}}：</span>
          <div v-if="key === 'url'" class="item-center">
            {{targetMessage.title}} <span class="item-center-sub">{{targetMessage.subTitle}}</span><span v-if="targetMessage.isMore" @click="handleShowTarget" class="item-target-btn">{{ $t('查看目标') }}</span>
          </div>
          <span v-else-if="!Array.isArray(activeItem[key])" v-bk-overflow-tips class="panel-row-val">{{activeItem[key] || '--'}}</span>
          <div v-else>
            <span class="panel-row-label" v-for="(set,index) in activeItem[key]" :key="index">{{set.name}}</span>
            <span v-if="!activeItem[key].length">--</span>
          </div>
        </div>
      </div>
      <div class="detail-right-select" ref="panelSelect">
        <div class="select-area">
          <span class="select-area-input">
            {{select.area.selected.length ? select.area.selected.join(',') : $t('选择地区')}}
            <i class="icon-monitor icon-arrow-down"></i>
            <bk-select
              class="select-area-select"
              :popover-min-width="150"
              @change="handleAreaChange"
              multiple
              :show-select-all="select.area.list.length > 1"
              v-model="select.area.selected">
              <bk-option
                v-for="(option, index) in select.area.list"
                :key="index"
                :id="option.name"
                :name="option.name">
              </bk-option>
            </bk-select>
          </span>
        </div>
        <div class="select-area">
          <span class="select-area-input">
            {{select.operator.selected.length ? select.operator.selected.join(',') : $t('选择运营商')}}
            <i class="icon-monitor icon-arrow-down"></i>
            <bk-select
              class="select-area-select"
              multiple
              @change="handleOperatorChange"
              :popover-min-width="150"
              :show-select-all="select.operator.list.length > 1"
              v-model="select.operator.selected">
              <bk-option
                v-for="(option, index) in select.operator.list"
                :key="index"
                :id="option.name"
                :name="option.name">
              </bk-option>
            </bk-select>
          </span>
        </div>
        <div
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="edit-task"
          @click="authority.MANAGE_AUTH ? handleEditTask() : handleShowAuthorityDetail()">
          {{ $t('编辑拨测任务') }}
        </div>
        <div class="select-strategy" @click="handleStrategyConfig"> {{ $t('关联告警策略') }}（{{ strategyNum }}） </div>
        <div class="time-shift">
          <monitor-date-range
            icon="icon-mc-time-shift"
            class="time-shift-select"
            dropdown-width="96"
            v-model="timeRange"
            :options="timerangeList"
            show-name
            @change="handleDateRangeChange">
          </monitor-date-range>
        </div>
        <div class="time-interval">
          <drop-down-menu
            show-name="true"
            :icon="refleshInterval === -1 ? 'icon-mc-alarm-recovered' : 'icon-zidongshuaxin'"
            v-model="refleshInterval"
            :text-active="refleshInterval !== -1"
            :list="refleshList"
            @on-icon-click="getTopNodeList">
          </drop-down-menu>
        </div>
        <div class="select-icon">
          <span class="icon-monitor icon-trend" :class="{ 'select-active': select.activeView === 0 }" @click="select.activeView = 0"></span>
          <span class="icon-monitor" :class="[{ 'select-active': select.activeView === 1 }, select.activeView === 1 ? 'icon-map-fill' : 'icon-map']" @click="select.activeView = 1"></span>
        </div>
      </div>
      <div class="detail-right-content" v-bkloading="{ isLoading: content.loading }">
        <div class="content-left">
          <div class="content-left-card" ref="contentLeft">
            <div class="card-title"> {{ $t('可用率top5') }} <span class="icon-monitor" :class="[content.availableSort ? 'icon-paixu-shang' : 'icon-paixu-xia']" @click="content.availableSort = !content.availableSort"></span>
            </div>
            <ul class="card-list" v-if="sortAvailableList.length">
              <li class="card-list-item" v-for="(item,index) in sortAvailableList" :key="index">
                <span class="item-name">{{item.name}}</span>
                <span class="item-num">{{item.available * 100}}%</span>
              </li>
            </ul>
            <div v-else class="card-empty"> {{ $t('查询无数据') }} </div>
          </div>
          <div class="content-left-card">
            <div class="card-title"> {{ $t('响应时长top5') }} <span class="card-title-unit">(ms)</span><span class="icon-monitor" :class="[content.durationSort ? 'icon-paixu-shang' : 'icon-paixu-xia']" @click="content.durationSort = !content.durationSort"></span>
            </div>
            <ul class="card-list" v-if="sortDurationList.length">
              <li class="card-list-item" v-for="(item,index) in sortDurationList" :key="index">
                <span class="item-name" :title="item.name">{{item.name}}</span>
                <span class="item-num">{{item.task_duration}}ms</span>
              </li>
            </ul>
            <div v-else class="card-empty"> {{ $t('查询无数据') }} </div>
          </div>
        </div>
        <div class="content-right">
          <div v-show="select.activeView === 0" style="display: flex; flex: 1;flex-direction: column;">
            <div class="content-right-chart" :style="{ width: content.chart.width + 'px' }">
              <monitor-echarts
                :title="$t('平均可用率')"
                :unit="content.chart.available.unit"
                :options="content.chart.availableOption"
                :key="content.chart.key"
                :height="content.chart.height"
                :series="content.chart.available.series || []"
                @dblclick="handleRestore"
                @data-zoom="handleDataZoom">
              </monitor-echarts>
            </div>
            <div class="content-right-chart">
              <monitor-echarts
                :unit="content.chart.taskDuration.unit"
                :options="content.chart.taskDurationOption"
                :title="$t('平均响应时长')"
                :key="content.chart.key"
                :height="content.chart.height"
                :series="content.chart.taskDuration.series || []"
                @dblclick="handleRestore">
              </monitor-echarts>
            </div>
          </div>
          <div v-if="content.map.available.data.length">
            <div class="content-right-map" v-show="select.activeView === 1 ">
              <div class="content-btns">
                <bk-button :theme="content.map.active === 0 ? 'primary' : 'default'" @click="content.map.active = 0" class="content-btns-first"> {{ $t('可用率') }} </bk-button>
                <bk-button :theme="content.map.active === 1 ? 'primary' : 'default'" @click="content.map.active = 1"> {{ $t('响应时长') }} </bk-button>
              </div>
              <monitor-echarts
                :key="left.active + 1"
                class="content-map"
                chart-type="map"
                :height="content.map.height"
                :series="content.map.active === 0 ? [content.map.available] : [content.map.taskDuration]">
              </monitor-echarts>
              <div class="content-msg">
                <div class="content-msg-data">
                  <div class="msg-time">
                    <div class="msg-time-num">
                      <span class="time-num-mark" style="background: #2dcb56;"></span>
                      <span>{{sortMaxColor}}</span>{{content.map.active === 0 ? '%' : 'ms'}}
                    </div>
                    <div class="msg-time-desc">{{content.map.active === 0 ? $t('最大可用率') : $t('最快响应时长') }}</div>
                  </div>
                  <div class="msg-time">
                    <div class="msg-time-num">
                      <span class="time-num-mark" style="background: #ea3636;"></span>
                      <span>{{sortMinColor}}</span>{{content.map.active === 0 ? '%' : 'ms'}}
                    </div>
                    <div class="msg-time-desc">{{content.map.active === 0 ? $t('最小可用率') : $t('最慢响应时长') }}</div>
                  </div>
                </div>
                <div class="content-msg-legend">
                  <div class="legend-title">
                    {{content.map.active === 0 ? $t('可用率图例') : $t('响应时长图例')}}
                  </div>
                  <ul class="legend-list">
                    <li class="legend-list-item" v-for="(item,index) in content.map.legend" :key="index">
                      <span class="item-status" :style="{ background: item.color }"></span>
                      {{content.map.active === 0 ? item.availableName : item.name}}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <template v-else>
            <div v-show="select.activeView === 1" class="content-right-empty"> {{ $t('查询无数据') }} </div>
          </template>
        </div>
      </div>
    </div>
    <!-- 监控目标组件 -->
    <monitor-dialog
      v-if="target.target && target.target.length"
      width="960"
      :title="$t('查看监控目标')"
      :need-footer="false"
      :value.sync="targetShow">
      <strategy-config-detail-table :table-data="target.target" :target-type="target.bkTargetType" :obj-type="target.bkObjType"></strategy-config-detail-table>
    </monitor-dialog>
  </div>
</template>
<script>
import { debounce } from 'throttle-debounce'
import { taskGraphAndMap, uptimeCheckTargetDetail } from '../../../../../monitor-api/modules/uptime_check'
import { strategyConfigList } from '../../../../../monitor-api/modules/strategies'
import { addListener, removeListener } from 'resize-detector'
import { createNamespacedHelpers } from 'vuex'
import { SET_KEY_WORD } from '../../../../store/modules/uptime-check-task'
import authorityMixinCreate from '../../../../mixins/authorityMixin'
import * as uptimeAuth from '../../authority-map'
import MonitorEcharts from '../../../../../monitor-ui/monitor-echarts/monitor-echarts-new'
import { retrieveUptimeCheckTask  } from '../../../../../monitor-api/modules/model'
import MonitorDialog from '../../../../../monitor-ui/monitor-dialog/monitor-dialog'
import strategyConfigDetailTable from '../../../strategy-config/strategy-config-detail/strategy-config-detail-table'
import { transformDataKey } from '../../../../../monitor-common/utils/utils'
import MonitorDateRange from '../../../../components/monitor-date-range/monitor-date-range.vue'
import DropDownMenu from '../../../performance/performance-detail/dropdown-menu.vue'
import { handleTimeRange } from '../../../../utils/index'
import moment from 'moment'
const { mapGetters, mapMutations, mapActions } = createNamespacedHelpers('uptime-check-task')
export default {
  name: 'UptimeCheckDetail',
  components: {
    // MonitorChart,
    // MonitorMap,
    MonitorEcharts,
    MonitorDialog,
    strategyConfigDetailTable,
    MonitorDateRange,
    DropDownMenu
  },
  mixins: [authorityMixinCreate(uptimeAuth)],
  props: {
    taskId: {
      type: [String, Number],
      default: 0
    },
    groupId: {
      type: [String, Number],
      default: 0
    }

  },
  data() {
    const availableSeries = this.getDefaultAvailableMapSeries()
    const durationSeries = this.getDefaultDurationMapSeries()
    return {
      id: 0,
      pageLoading: true,
      left: {
        active: 0
      },
      columnMap: {
        name: this.$t('任务名'),
        protocol: this.$t('协议'),
        url: this.$t('拨测地址'),
        create_user: this.$t('创建人'),
        groups: this.$t('所属任务组'),
        create_time: this.$t('创建时间')
      },
      select: {
        area: {
          list: [],
          selected: []
        },
        operator: {
          list: [],
          selected: []
        },
        activeView: 0,
        date: '',
        dateOpen: false
      },
      content: {
        chart: {
          width: 0,
          height: 0,
          available: {},
          availableOption: {
            grid: {
              top: 36
            },
            tool: {
              list: ['screenshot', 'area']
            },
            yAxis: {
              max: 1
            }
          },
          taskDurationOption: {
            grid: {
              top: 36
            },
            tool: {
              list: ['screenshot', 'area']
            }
          },
          taskDuration: {},
          taskDurationPoints: [],
          availablePoints: [],
          key: 0
        },
        map: {
          legend: [
            {
              color: '#2DCB56',
              name: '< 100ms',
              availableName: '99% ~ 100%'
            },
            {
              color: '#FFEB00',
              name: '< 200ms',
              availableName: '95% ~ 99%'
            },
            {
              color: '#FF9C01',
              name: '< 300ms',
              availableName: '80% ~ 95%'
            },
            {
              color: '#EA3636',
              name: '≥ 300ms',
              availableName: '0% ~ 80%'
            }
          ],
          width: 0,
          height: 0,
          available: availableSeries,
          taskDuration: durationSeries,
          sortAvailable: [],
          sortTaskDuration: [],
          active: 0,
          availableMax: 0,
          availableMin: 0,
          taskDurationMax: 0,
          taskDurationMin: 0
        },
        availableSort: true,
        durationSort: true,
        loading: false
      },
      top: {
        available: [],
        response: []
      },
      lisenResize: null,
      handleSearch: () => {},
      activeItem: {},
      strategyNum: 0,
      targetMessage: {
        title: '',
        subTitle: '',
        isMore: false
      },
      target: {
      }, // 监控指标数据
      targetShow: false,
      basicLoading: false,

      timerangeList: [
        {
          name: this.$t('1小时'),
          value: 1 * 60 * 60 * 1000
        },
        {
          name: this.$t('1天'),
          value: 24 * 60 * 60 * 1000
        },
        {
          name: this.$t('7天'),
          value: 168 * 60 * 60 * 1000
        },
        {
          name: this.$t('1个月'),
          value: 720 * 60 * 60 * 1000
        }
      ],
      refleshList: [
        {
          name: this.$t('刷新'),
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
      ],
      timeRange: 1 * 60 * 60 * 1000,
      refleshInterval: 60000,
      resizeHandler: null,
      refleshIntervalInstance: 0,
      // 用于双击还原
      lastTimeRange: 1 * 60 * 60 * 1000,
      leftLoading: false
    }
  },
  computed: {
    ...mapGetters(['searchData', 'keyword']),
    leftListData() {
      if (this.groupId) {
        return this.searchData.filter(item => item.groups.find(set => +set.id === +this.groupId))
      }
      return this.searchData
    },
    activeData() {
      return this.leftListData.find(item => item.id === this.left.active)
    },
    sortMinColor() {
      return this.content.map.active === 0 ? this.content.map.availableMin : this.content.map.taskDurationMax
    },
    sortMaxColor() {
      return this.content.map.active === 0 ? this.content.map.availableMax : this.content.map.taskDurationMin
    },
    sortAvailableList() {
      if (this.content.availableSort) {
        return this.content.map.sortAvailable.slice().sort((a, b) => b.available - a.available)
          .slice(0, 5)
      }
      return this.content.map.sortAvailable.slice().sort((b, a) => b.available - a.available)
        .slice(0, 5)
    },
    sortDurationList() {
      if (this.content.durationSort) {
        return this.content.map.sortTaskDuration.slice().sort((a, b) => a.task_duration - b.task_duration)
          .slice(0, 5)
      }
      return this.content.map.sortTaskDuration.slice().sort((b, a) => a.task_duration - b.task_duration)
        .slice(0, 5)
    }
  },
  watch: {
    'left.active': {
      handler: 'handleActiveChange'
    },
    activeData: {
      handler: 'handleActiveDataChange',
      deep: true
    },
    refleshInterval: {
      handler(v) {
        if (this.refleshIntervalInstance) {
          window.clearInterval(this.refleshIntervalInstance)
        }
        if (v <= 0) return
        this.refleshIntervalInstance = window.setInterval(() => {
          this.getTopNodeList()
        }, this.refleshInterval)
      },
      immediate: true
    }
  },
  async created() {
    this.pageLoading = true
    await this.getUptimeCheckTask()
    if (this.taskId) {
      await this.getNodesByTemplateInfo(this.taskId, true)
    }
    this.left.active = !this.taskId ? this.leftListData[0].id : +this.taskId
    this.handleSearch = debounce(300, this.handleSideKeyChange)
    this.pageLoading = false
  },
  mounted() {
    this.lisenResize = debounce(300, v => this.handleWindowResize(v))
    this.handleWindowResize()
    addListener(this.$refs.detailRight, this.lisenResize)
  },
  beforeDestroy() {
    this.refleshIntervalInstance && window.clearInterval(this.refleshIntervalInstance)
    removeListener(this.$refs.detailRight, this.lisenResize)
  },
  methods: {
    ...mapMutations([SET_KEY_WORD]),
    ...mapActions(['getUptimeCheckTask', 'setKeyword']),
    // 获取getNodesByTemplate
    async getNodesByTemplateInfo(id, isCreate) {
      if (isCreate) {
        this.basicLoading = false
      } else {
        this.basicLoading = true
      }
      const data = await retrieveUptimeCheckTask(id).catch(() => {
        this.noDataMsg()
      })
      if (data) {
        const { hosts } = data.config
        if (hosts) {
          const type = this.targetNodeTypeInfo(hosts)
          const params = {
            bk_biz_id: this.$store.getters.bizId,
            bk_obj_id: type,
            target_hosts: hosts
          }
          const targetData = await uptimeCheckTargetDetail(params).catch(() => {
            this.noDataMsg()
          })
          if (targetData) {
            this.target = {
              bkObjType: 'HOST',
              bkTargetType: type,
              target: transformDataKey(targetData.bk_target_detail)
            }
            this.targetMessage.isMore = true
            // 添加展示自定义输入不存在的主机
            if (type === 'INSTANCE') {
              this.targetMessage.subTitle = ''
              hosts.forEach((item) => {
                const isExit = this.target.target.find(set => item.ip === set.ip)
                !isExit && this.target.target.push({
                  ip: item.ip,
                  agentStatus: '',
                  bkCloudName: ''
                })
              })
            }
            this.targetInfo(this.target)
          } else {
            this.noDataMsg()
          }
        } else {
          this.target = {}
          this.targetMessage = {
            title: data.config.urls,
            subTitle: '',
            isMore: false
          }
        }
      } else {
        this.noDataMsg()
      }
      this.basicLoading = false
    },
    noDataMsg() {
      this.$bkMessage({
        theme: 'error',
        message: this.$t('没有找到对应的数据')
      })
      this.$router.push({
        name: 'uptime-check'
      })
    },
    // 判断当前targetNodeType
    targetNodeTypeInfo(nodes) {
      let result = ''
      const { INSTANCE, TOPO, SERVICE_TEMPLATE, SET_TEMPLATE } = {
        INSTANCE: 'INSTANCE',
        TOPO: 'TOPO',
        SERVICE_TEMPLATE: 'SERVICE_TEMPLATE',
        SET_TEMPLATE: 'SET_TEMPLATE'
      }
      if (nodes) {
        const firstNode = nodes[0]
        if (firstNode.bk_obj_id !== 0 && typeof(firstNode.bk_obj_id) !== 'undefined') {
          switch (firstNode.bk_obj_id) {
            case 'biz':
            case 'set':
            case 'module':
              result = TOPO
              break
            case 'SET_TEMPLATE':
              result = SET_TEMPLATE
              break
            case 'SERVICE_TEMPLATE':
              result = SERVICE_TEMPLATE
              break
            default:
              result = INSTANCE
          }
        } else {
          result = INSTANCE
        }
      }
      return result
    },
    targetInfo(v) {
      const { target, bkTargetType, bkObjType } = v
      if (target?.length) {
        const len = target.length
        if (['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
          const count = target.reduce((pre, item) => {
            const allHost = item.allHost || []
            return Array.from(new Set([...pre, ...allHost]))
          }, []).length
          const textMap = {
            TOPO: `${this.$t('个')}${this.$t('节点')}`,
            SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
            SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
          }
          this.targetMessage.title = `${len} ${textMap[bkTargetType]}`
          const res = bkObjType === 'SERVICE' ? `${this.$t('个')}${this.$t('实例')}` : `${this.$t('台')}${this.$t('主机')}`
          this.targetMessage.subTitle = `（ ${count} ${res}）`
        } else {
          this.targetMessage.title = `${len} ${this.$t('台主机')} `
        }
      }
    },
    handleShowTarget() {
      this.targetShow = true
    },
    getDefaultAvailableMapSeries() {
      return {
        data: [],
        name: this.$t('可用率'),
        joinBy: 'name'
      }
    },
    getDefaultDurationMapSeries() {
      return {
        data: [],
        name: this.$t('响应时长'),
        joinBy: 'name'
      }
    },
    getTopNodeList() {
      this.content.loading = true
      this.handleEmptyData()
      this.content.chart.key = +Date.now()
      const { startTime, endTime } = handleTimeRange(this.timeRange)
      this.select.date = `${this.formatUnixTime(startTime)}--${this.formatUnixTime(endTime)}`
      taskGraphAndMap({
        bk_biz_id: this.activeItem.bk_biz_id,
        task_id: this.left.active,
        time_range: this.select.date,
        carrieroperator: this.select.operator.selected,
        location: this.select.area.selected
      }).then(async (data) => {
        const fun = this.handleChartAnnotationPoint(data.chart.task_duration.series)
        this.content.chart.taskDurationPoints = Object.freeze(fun)
        this.content.chart.availablePoints = Object.freeze(this.handleChartAnnotationPoint(data.chart.available.series))
        if (data.chart.task_duration.series && data.chart.task_duration.series.length) {
          data.chart.task_duration.series = data.chart.task_duration.series.map(item => ({
            ...item,
            markPoint: {
              data: [
                {
                  type: 'max',
                  symbolRotate: 45
                }
              ]
            },
            unit: data.chart.task_duration.unit || 'short'
          }))
        }
        if (data.chart.available.series && data.chart.available.series.length) {
          data.chart.available.series = data.chart.available.series.map(item => ({
            ...item,
            markPoint: {
              data: [
                { type: 'max' }
              ],
              symbolRotate: 190
            },
            unit: data.chart.available.unit || 'short'
          }))
        }
        this.content.chart.taskDuration = Object.freeze(data.chart.task_duration)
        this.content.chart.available = Object.freeze(data.chart.available)
        this.content.map.available = this.getDefaultAvailableMapSeries()
        this.content.map.taskDuration = this.getDefaultDurationMapSeries()
        data.map.forEach((item) => {
          if (+item.available > 0) {
            this.content.map.available.data.push({
              name: item.location,
              value: item.available * 100,
              ...this.handleMapColor(+item.available * 100)
            })
          }
          if (+item.task_duration > 0) {
            this.content.map.taskDuration.data.push({
              name: item.location,
              value: item.task_duration,
              ...this.handleMapColor(+item.task_duration, true)
            })
          }
        })
        this.content.map.availableMax = data.max_and_min.available_max * 100
        this.content.map.availableMin = data.max_and_min.available_min * 100
        this.content.map.taskDurationMax = data.max_and_min.task_duration_max
        this.content.map.taskDurationMin = data.max_and_min.task_duration_min
        this.content.map.sortAvailable = data.map.slice().sort((a, b) => b.available - a.available)
        this.content.map.sortTaskDuration = data.map.slice().sort((a, b) => a.task_duration - b.task_duration)
        this.content.loading = false
        this.leftLoading = true
        await this.getUptimeCheckTask()
        this.leftLoading = false
      })
        .catch(() => {
          this.content.loading = false
          this.handleEmptyData()
        })
    },
    handleEmptyData() {
      this.content.chart.available = {}
      this.content.chart.taskDuration = {}
      this.content.chart.taskDurationPoints = []
      this.content.chart.availablePoints = []
      this.content.map.available = {
        data: [],
        name: this.$t('可用率')
      }
      this.content.map.taskDuration = {
        data: [],
        name: this.$t('响应时长')
      }
      this.content.map.sortAvailable = []
      this.content.map.sortTaskDuration = []
    },
    handleSideKeyChange(e) {
      this.setKeyword(e.target.value || '')
    },
    handleMapColor(v, duration = false) {
      if ((duration && v < 100) || (!duration && (v <= 100 && v >= 99))) {
        return {
          itemStyle: {
            color: 'rgba(45, 203, 86, 0.2)',
            areaColor: '#f7f7f7',
            borderColor: '#c4c6cc',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              color: 'rgba(255, 235, 0, 0.2)',
              areaColor: 'rgba(45, 203, 86, 0.4)',
              borderColor: 'rgba(45, 203, 86, 0.4)',
              borderWidth: 1
            }
          }
        }
      } if ((duration && v < 200) || (!duration && (v < 99 && v >= 95))) {
        return {
          itemStyle: {
            color: 'rgba(255, 235, 0, 0.2)',
            areaColor: '#f7f7f7',
            borderColor: '#c4c6cc',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              color: 'rgba(255, 235, 0, 0.2)',
              areaColor: 'rgba(255, 235, 0, 0.4)',
              borderColor: 'rgba(255, 235, 0, 0.4)',
              borderWidth: 1
            }
          }
        }
      } if ((duration && v < 300) || (!duration && (v < 95 && v >= 90))) {
        return {
          itemStyle: {
            color: 'rgba(255, 156, 1, 0.2)',
            areaColor: '#f7f7f7',
            borderColor: '#c4c6cc',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              color: 'rgba(234, 54, 54, 0.2)',
              areaColor: 'rgba(255, 156, 1, 0.4)',
              borderColor: 'rgba(255, 156, 1, 0.4)',
              borderWidth: 1
            }
          }
        }
      }
      return {
        itemStyle: {
          color: 'rgba(234, 54, 54, 0.2)',
          areaColor: '#f7f7f7',
          borderColor: '#c4c6cc',
          borderWidth: 1
        },
        emphasis: {
          itemStyle: {
            color: 'rgba(234, 54, 54, 0.2)',
            areaColor: 'rgba(234, 54, 54, 0.4)',
            borderColor: 'rgba(234, 54, 54, 0.4)',
            borderWidth: 1
          }
        }
      }
    },
    handleChartSeriesMarker(data) {
      data.forEach((series) => {
        const index = series.max_index
        const maxData = series.data[index]
        series.data.splice(index, 1, {
          x: maxData[0],
          y: maxData[1],
          id: 'max',
          marker: {
            enabled: true,
            fillColor: null,
            radius: 3,
            symbol: 'circle'
          }
        })
      })
    },
    handleChartAnnotationPoint(data) {
      const result = data.map((series) => {
        const maxData = series.data[series.max_index]
        return {
          xAxis: 0,
          yAxis: 0,
          x: maxData[0] || 0,
          y: maxData[1] || 0
        }
      })
      const sort = (object1, object2) => {
        const value1 = object1.y
        const value2 = object2.y
        if (value1 < value2) {
          return 1
        } if (value1 > value2) {
          return -1
        }
        return 0
      }
      result.sort(sort)
      return result.splice(0, 1)
    },
    async handleActiveChange(v) {
      this.select.area.list = []
      this.select.operator.list = []
      this.select.area.selected = []
      this.select.operator.selected = []
      this.select.date = ''
      if (this.left.active && this.activeData) {
        this.activeData.nodes.forEach((item) => {
          if (item.locationData && item.locationData.city
          && !this.select.area.list.find(set => set.city === item.locationData.city)) {
            this.select.area.list.push({
              ...item.locationData,
              name: item.locationData.city
            })
          }
          if (item.carrieroperator && !this.select.operator.list.find(set => set.name === item.carrieroperator)) {
            this.select.operator.list.push({
              name: item.carrieroperator
            })
          }
        })
        const params = {
          page: 1,
          page_size: 10,
          search: '',
          data_source_list: [],
          order_by: '-update_time',
          task_id: v,
          bk_biz_id: this.$store.getters.bizId
        }
        this.content.loading = true
        const data = await strategyConfigList(params).catch(() => 0)
        this.strategyNum = data.scenario_list ? data.scenario_list.reduce((res, item) => res + item.count, 0) : data
        this.getTopNodeList()
      }
    },
    handleAreaChange() {
      this.getTopNodeList()
    },
    handleOperatorChange() {
      this.getTopNodeList()
    },
    async handleLeftItemClick(id) {
      this.left.active = id
      if (this.left.active) {
        await this.getNodesByTemplateInfo(this.left.active)
      }
    },
    handleWindowResize() {
      const ref = this.$refs.panelSelect.getBoundingClientRect()
      const left = this.$refs.contentLeft.getBoundingClientRect()
      this.content.chart.width = ref.width - 240
      this.content.chart.height = left.height - 2
      this.content.map.width = Math.min(this.content.chart.width, this.content.chart.height * 2)
      this.content.map.height = Math.min(this.content.chart.width, this.content.chart.height * 2)
    },
    handleEditTask() {
      this.$router.push({
        name: 'uptime-check-task-edit',
        params: {
          id: this.activeItem.id,
          bizId: this.activeItem.bk_biz_id
        }
      })
    },
    // 关联策略告警
    handleStrategyConfig() {
      this.$router.push({
        name: 'strategy-config',
        params: {
          taskId: this.left.active
        }
      })
    },
    handleActiveDataChange(newVal, oldVal) {
      this.activeItem = newVal || oldVal || this.activeItem
    },
    handleDateRangeChange(range) {
      if (Array.isArray(range) || this.refleshInterval === -1) {
        this.handleResetRefleshInterval()
      }
      this.lastTimeRange = range
      this.getTopNodeList()
    },
    formatUnixTime(unixTime) {
      return moment(unixTime * 1000).format('YYYY-MM-DD HH:mm')
    },
    handleDataZoom(timeRange) {
      this.timeRange = timeRange
      this.handleResetRefleshInterval()
      this.getTopNodeList()
    },
    handleRestore() {
      this.timeRange = this.lastTimeRange
      this.handleResetRefleshInterval()
      this.getTopNodeList()
    },
    handleResetRefleshInterval() {
      this.refleshInterval = Array.isArray(this.timeRange) ? -1 : 60000
    }
  }
}
</script>
<style lang="scss" scoped>
.dropdown-select-list {
  margin: 0;
  padding: 0;
  max-height: 216px;
  overflow: auto;
  &-item {
    min-width: 200px;
    height: 32px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    font-size: 12px;
    span {
      flex: 1;
    }
    .bk-icon {
      color: #3a84ff;
    }
    &:hover {
      color: #3a84ff;
      background-color: rgba(234, 243, 255, .7);
      cursor: pointer;
    }
  }
}
.uptime-time-detail {
  display: flex;
  max-height: calc(100vh - 52px);
  height: calc(100vh - 52px);
  margin: -20px -24px 0;
  .detail-left {
    background: linear-gradient(270deg, #dcdee5 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%);
    background-size: 100% 100%;
    display: flex;
    flex-direction: column;
    flex: 0 0 240px;
    background-color: #fafbfd;
    color: #63656e;
    &-search {
      flex: 0 0 52px;
      display: flex;
      align-items: center;
      padding: 0 15px;
      color: #c4c6cc;
      input {
        border: 0;
        font-size: 14px;
        padding-left: 10px;
        background: #fafbfd;
        flex: 1;
        color: #63656e;
        &::placeholder {
          color: #c4c6cc;
        }
      }
      .icon-search {
        font-size: 18px;
      }
    }
    &-list {
      flex: 1;
      width: 240px;
      max-height: 100%;
      overflow: auto;
      display: flex;
      flex-direction: column;
      padding: 0;
      margin: 0;
      font-size: 14px;
      background: linear-gradient(180deg, #dcdee5 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%);
      background-size: 100% 100%;
      .list-item {
        flex: 0 0 42px;
        height: 42px;
        display: flex;
        width: 100%;
        align-items: center;
        padding: 0 20px;
        &-name {
          flex-grow: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        &-num {
          color: #979ba5;
          margin-left: 10px;
        }
        &:hover {
          background: #dcdee5;
          cursor: pointer;
        }
        &.item-active {
          background: #3a84ff;
          color: #fff;
          width: calc( 100% + 2px );
          margin: 0 -2px;
          .list-item-num {
            color: #fff;
          }
        }
        &:first-child.item-active {
          margin-top: -1px;
          height: 43px;
        }
      }
      .list-empty {
        flex: 0 0 42px;
        height: 42px;
        display: flex;
        width: 100%;
        align-items: center;
        padding: 0 20px;
      }
    }
  }
  .detail-right {
    flex: 1;
    background: #fff;
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: 14px;
    color: #63656e;
    overflow: auto;
    &-panel {
      flex: 0 0 160px;
      display: flex;
      align-items: center;
      padding: 30px 40px;
      border-bottom: 1px solid #dcdee5;
      flex-wrap: wrap;
      .panel-row {
        width: 50%;
        height: 20px;
        display: flex;
        align-items: center;
        &-name {
          flex: 0 0 85px;
          color: #979ba5;
          margin-right: 24px;
          text-align: right;
        }
        &-label {
          border: 1px solid #dcdee5;
          border-radius: 2px;
          background: #fafbfd;
          height: 24px;
          text-align: center;
          line-height: 24px;
          color: #63656e;
          padding: 2px 10px;
          margin-right: 5px;
        }
        &-val {
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }
        .item-center {
          flex: 1;
          .item-target-btn {
            cursor: pointer;
            color: #3a84ff;
            display: inline-block;
            margin-left: 10px;
          }
          &-sub {
            color: #979ba5;
          }
        }
      }
    }
    &-select {
      flex: 0 0 40px;
      display: flex;
      align-items: center;
      background: #fafbfd;
      padding-left: 40px;
      border-bottom: 1px solid #dcdee5;
      .select-area {
        cursor: pointer;
        margin-right: 70px;
        position: relative;
        i {
          color: #979ba5;
          font-size: 20px;
          position: absolute;
        }
        &-input {
          height: 40px;
          display: inline-block;
          line-height: 40px;
          min-width: 100px;
          &:hover {
            color: #3a84ff;
            i {
              color: #3a84ff;
            }
          }
        }
        &-date {
          width: 100%;
          position: absolute;
          left: 0px;
          top: 0px;
          /deep/ .bk-picker-panel-body {
            min-width: 522px;
          }
        }
        &-select {
          opacity: 0;
          position: absolute;
          top: 4px;
          width: 100%;
        }
      }
      .edit-task {
        color: #3a84ff;
        padding-right: 20px;
        border-right: 1px solid #dcdee5;
        margin-left: auto;
        cursor: pointer;
      }
      .select-strategy {
        margin-left: 20px;
        color: #3a84ff;
        padding-right: 20px;
        border-right: 1px solid #dcdee5;
        cursor: pointer;
      }
      .select-icon {
        margin: 0 20px;
        cursor: pointer;
        .icon-monitor {
          font-size: 20px;
        }
        :first-child {
          margin-right: 12px;
        }
      }
      .select-active {
        color: #3a84ff;
      }
      .time-shift {
        font-size: 12px;
        flex-shrink: 0;
        min-width: 100px;
        border-right: 1px solid #dcdee5;
        height: 20px;
        display: flex;
        align-items: center;
        &-select {
          width: 100%;
        }
        /deep/ .date {
          border: 0;
          background: transparent;
          &.is-focus {
            box-shadow: none;
          }
        }
      }
      .time-interval {
        font-size: 12px;
        height: 20px;
        border-right: 1px solid #dcdee5;
        display: flex;
        align-items: center;
      }
    }
    &-content {
      display: flex;
      flex: 1;
      overflow: auto;
      .content-left {
        flex: 0 0 240px;
        display: flex;
        flex-direction: column;
        border-right: 1px solid #dcdee5;
        &-card {
          flex: 1;
          padding-top: 35px;
          display: flex;
          flex-direction: column;
          overflow: auto;
          &:first-child {
            border-bottom: 1px solid #dcdee5;
          }
          .card-title {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 19px;
            color: #63656e;
            font-size: 14px;
            font-weight: bold;
            flex: 0 0 19px;
            .icon-monitor {
              color: #c4c6cc;
              font-size: 24px;
              margin-left: 6px;
              &:hover {
                color: #3a84ff;
                cursor: pointer;
              }
            }
            &-unit {
              font-size: 12px;
              font-weight: normal;
              display: inline-block;
              margin-left: 5px;
            }
          }
          .card-list {
            flex: 1;
            overflow: auto;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            font-size: 12px;
            margin-top: 16px;
            &-item {
              display: flex;
              justify-content: flex-start;
              align-items: center;
              height: 28px;
              padding-right: 30px;
              .item-name {
                margin-right: 10px;
                flex: 1;
                max-width: 110px;
                min-width: 110px;
                margin-left: 40px;
                text-overflow: ellipsis;
                white-space: nowrap;
                overflow: hidden;
                text-align: left
              }
              .item-num {
                text-align: right;
                flex: 1;
              }
            }
          }
          .card-empty {
            text-align: center;
            margin: auto;
            font-size: 12px;
            color: #979ba5;
          }
        }
      }
      .content-right {
        flex: 1;
        display: flex;
        flex-direction: column;
        &-chart {
          flex: 1;
          display: flex;
          &:first-child {
            border-bottom: 1px solid #dcdee5;
          }
        }
        &-map {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          .content-btns {
            position: absolute;
            left: 16px;
            top: 16px;
            font-size: 0;
            z-index: 20;
            /deep/ .bk-button.bk-default:hover,
            .bk-button.bk-default.hover {
              border-color: #3a84ff;
              color: #3a84ff;
            }
            &-first {
              border-top-right-radius: 0;
              border-bottom-right-radius: 0;
              border-right: 0;
              margin-right: -1px;
            }
          }
          .content-msg {
            position: absolute;
            right: 25px;
            bottom: 25px;
            width: 120px;
            &-data {
              border: 1px solid #dcdee5;
              border-radius: 2px;
              display: flex;
              flex-direction: column;
              height: 134px;
              .msg-time {
                flex: 1;
                color: #63656e;
                font-size: 12px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                &-num {
                  margin-left: 22px;
                  position: relative;
                  .time-num-mark {
                    position: absolute;
                    left: -22px;
                    top: 5px;
                    width: 5px;
                    height: 12px;
                    background: #3a84ff
                  }
                  span {
                    font-size: 16px;
                    font-weight: bold;
                  }
                }
                &-desc {
                  color: #979ba5;
                  margin-left: 22px;
                  margin-top: 4px;
                }
                &:first-child {
                  border-bottom: 1px solid #dcdee5;
                }
              }
            }
            &-legend {
              border: 1px solid #dcdee5;
              border-radius: 2px;
              margin-top: 10px;
              height: 154px;
              padding: 15px 0px 15px 15px;
              .legend-title {
                color: #63656e;
                font-weight: bold;
              }
              .legend-list {
                margin: 0;
                padding: 0;
                &-item {
                  display: flex;
                  align-items: center;
                  height: 16px;
                  margin: 10px 0px 10px 0;
                  font-size: 12px;
                  .item-status {
                    width: 16px;
                    height: 16px;
                    margin-right: 10px;
                  }
                }
              }
            }
          }
        }
        &-empty {
          display: flex;
          flex: 1;
          align-items: center;
          justify-content: center;
          font-size: 12px;
        }
      }
    }
  }
}
</style>
