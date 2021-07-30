<template>
  <div class="event-center-detail" v-bkloading="{ isLoading: loading }" :class="{ 'detail-loading': loading }">
    <!-- 事件详情基本信息 -->
    <!-- detail panel start -->
    <div class="detail-panel" v-if="detail">
      <div class="detail-panel-status" :class="'status-' + detail.eventStatus.toLocaleLowerCase()">
        <i class="icon-monitor panel-icon" :class="'icon-mc-alarm-' + detail.eventStatus.toLocaleLowerCase()"></i>
        <span class="panel-status">{{eventStatusMap[detail.eventStatus]}}<span v-if="detail.isAck"> {{ $t('（已确认）') }} </span></span>
      </div>
      <div class="detail-form">
        <div class="detail-form-item">
          <div class="item-col">
            <span class="item-label"> {{ $t('告警ID：') }} </span>
            <div class="item-content">{{detail.id}}</div>
          </div>
          <div class="item-col">
            <span class="item-label"> {{ $t('告警级别：') }} </span>
            <div class="item-content">
              <span class="info-mark" :class="'status-' + detail.level"></span>
              <span class="info-status" :class="'status-' + detail.level"> {{ $t(eventLevelMap[detail.level]) }} </span>
            </div>
          </div>
        </div>
        <div class="detail-form-item">
          <div class="item-col">
            <span class="item-label"> {{ $t('首次异常时间：') }} </span>
            <div class="item-content">{{detail.firstAnomalyTime}} ({{ $t('持续时长') }} {{detail.holdTime}})</div>
          </div>
          <div class="item-col">
            <span class="item-label"> {{ $t('告警状态：') }} </span>
            <div class="item-content">
              {{eventStatusMap[detail.eventStatus]}}<span v-if="detail.isAck"> {{ $t('（已确认）') }} </span>
              <span class="info-affirm"
                    v-if="!detail.isAck && detail.eventStatus === 'ABNORMAL'"
                    @click="handleShowAlarmConfirm">
                {{ $t('告警确认') }}
              </span>
              <span
                v-authority="{ active: !authority.ALARM_SHIELD_MANAGE_AUTH }"
                class="info-shield"
                v-if="!detail.isShielded && (detail.eventStatus === 'ABNORMAL' || detail.eventStatus === 'RECOVERED')"
                @click="authority.ALARM_SHIELD_MANAGE_AUTH ? handleShowQuickShield() : handleShowAuthorityDetail()"> {{ $t('快捷屏蔽') }}
              </span>
            </div>
          </div>
        </div>
        <div class="detail-form-item">
          <div class="item-col">
            <span class="item-label"> {{ $t('事件产生时间：') }} </span>
            <div class="item-content">{{detail.eventBeginTime}}</div>
          </div>
          <div class="item-col">
            <span class="item-label"> {{ $t('通知状态：') }} </span>
            <div class="item-content">
              {{ `${detail.alertInfo.count} ${$t('次')}` }}
              <span v-if="detailAlertInfo">（ {{detailAlertInfo}}）</span>
              <span v-show="detail.alertInfo.count !== 0"
                    class="info-detail"
                    @click="handleNoticeDetail(true)"
                    :style="{ marginLeft: detailAlertInfo ? '' : '6px' }"> {{ $t('详情') }} </span>
            </div>
          </div>
        </div>
        <div class="detail-form-item">
          <div class="item-col">
            <span class="item-label"> {{ $t('策略名称：') }} </span>
            <div class="item-content">
              {{detail.strategyName}}
              <span
                class="info-check"
                v-authority="{ active: !authority.STRATEGY_VIEW_AUTH }"
                @click="authority.STRATEGY_VIEW_AUTH ? handleGotoStrategy() : handleShowAuthorityDetail()">
                {{ $t('查看告警策略') }}
              </span>
            </div>
          </div>
        </div>
        <div class="detail-form-item">
          <div class="item-col item-col-dimensions">
            <span class="item-label"> {{ $t('维度信息：') }} </span>
            <!-- <div class="item-content">{{detail.dimensions || '--'}}</div> -->
            <div class="item-content dimensions">
              <span class="nowrap" v-for="(item, index) in filterDemisions" :key="index">
                <span v-if="index !== 0"> - </span>
                <span>{{ item.displayName }}</span>
                (<span
                  :class="{ 'info-check': item.name === 'bk_target_ip' }"
                  style="margin-left: 0;"
                  v-authority="{ active: !authority.PERFORMANCE_VIEW_AUTH }"
                  @click="authority.PERFORMANCE_VIEW_AUTH ? handleToPerformance(item) : handleShowAuthorityDetail()">{{ item.displayValue }}</span>)
              </span>
              <span v-show="logRetrieval.isCanClick" class="icon-monitor icon-guanlian" @click="handleLogRetrieval"></span>
            </div>
          </div>
        </div>
        <div class="detail-form-item">
          <div class="item-col item-col-dimensions">
            <span class="item-label"> {{ $t('告警内容：') }} </span>
            <div class="item-content">{{detail.eventMessage || '--'}}</div>
          </div>
        </div>
        <div class="detail-form-item" v-if="detail.relationInfo">
          <div class="item-col item-col-dimensions">
            <span class="item-label"> {{ $t('关联信息：') }} </span>
            <div class="item-content">{{detail.relationInfo}}</div>
          </div>
        </div>
      </div>
      <!-- 通知状态明细 -->
      <template>
        <alarm-notice-detail
          v-model="notice.show"
          :biz-id="detail.bkBizId"
          :id="detail.id"
          :default-select-action-id="notice.defaultSelectActionId">
        </alarm-notice-detail>
      </template>
    </div>
    <!-- detail panel end -->
    <!-- 事件详情关联信息tab -->
    <!-- detail tab start -->
    <ul class="detail-tab">
      <li class="detail-tab-item"
          :class="{ 'item-active': index === tab.active, 'item-last': index === tab.list.length - 1 }"
          @click="handleTabChange(index)"
          v-for="(item, index) in tab.list"
          :key="index">
        {{ item.name }}
      </li>
      <bk-popover ref="setPopover" placement="bottom" width="515" theme="light alarm-filter" trigger="click" :offset="200" :on-hide="handleSetPopoverHide">
        <span v-show="tab.active === 2" class="detail-tab-icon"><i class="icon-monitor icon-mc-alarm-filter"></i></span>
        <template slot="content">
          <div class="set-filter">
            <div class="set-filter-title"> {{ $t('设置显示类型') }} </div>
            <ul class="set-filter-list">
              <li v-for="item in filter.list" :key="item.id" class="list-item">
                <bk-checkbox :value="item.checked" :disabled="item.disabled" @change="handleCheckChange($event, item)">{{item.name}}</bk-checkbox>
              </li>
            </ul>
            <div class="set-filter-footer">
              <bk-button theme="primary" class="footer-btn" @click="handleConfirmSet" :disabled="!isChecked"> {{ $t('确认') }} </bk-button>
              <bk-button @click="handleCancelSet"> {{ $t('取消') }} </bk-button>
            </div>
          </div>
        </template>
      </bk-popover>
    </ul>
    <!-- detail tab end -->
    <!-- 事件详情关联信息content -->
    <!-- detail content start -->
    <div class="detail-content">
      <div class="detail-content-chart" v-show="tab.active === 0" ref="chartWrap">
        <monitor-echart
          v-if="detail"
          height="340"
          :title="chart.title"
          :subtitle="chart.subtitle"
          :key="id"
          :options="chartOption"
          :empty-text="chart.emptyText"
          :get-series-data="handleGetSeriesData"
          :chart-type="chart.chartType"
          :get-alarm-status="getAlarmStatus"
          @export-data-retrieval="handleExportToRetrieval(item)"
          @full-screen="handleFullScreen(item)"
          @collect-chart="handleCollectSingleChart(item)">
        </monitor-echart>
      </div>
      <div v-show="tab.active === 1" v-bkloading="{ isLoading: advise.loading }">
        <editor height="400px" class="detail-content-editor" v-model="advise.text"></editor>
        <bk-button theme="primary" :disabled="!isAdviseChange" @click="handleSaveAdvise"> {{ $t('保存') }} </bk-button>
      </div>
      <div class="detail-content-log" v-show="tab.active === 2" v-bkloading="{ isLoading: !log.list.length && log.loading }" :class="{ 'content-log-empty': !log.list.length }">
        <!-- 流转记录 -->
        <alarm-log-list
          ref="logList"
          v-if="log.list.length"
          :list="log.list"
          :loading="log.scroll"
          :default-click-collapse-index="log.defaultClickCollapseIndex"
          @log-resize="handleLogListResize"
          @notice-detail="handleNoticeDetail"
          @goto-strategy="handleGotoShieldStrategy"
          @change-list="handleInsertItemIntoLogList">
        </alarm-log-list>
        <template v-else>
          <div class="log-empty">
            <span><i class="icon-monitor log-empty-icon" :class="[logEmptyIcon]"></i></span>
            <label class="log-empty-label">{{ log.abnormal ? $t('数据加载异常') : $t('查询无数据') }}</label>
          </div>
        </template>
      </div>
    </div>
    <!-- detail content end -->
    <!-- 告警确认弹窗 -->
    <!-- alarm confirm start -->
    <bk-dialog v-if="!loading" :title="$t('告警确认')" width="480" v-model="confirm.show" :loading="confirm.scroll" @confirm="handleAlarmConfirm">
      <div class="alarm-confirm">
        <div class="alarm-confirm-desc"> {{ $t('重要提醒：告警确认后，异常持续未恢复的情况下，') }} <span class="desc-mark"> {{ $t('将不会再发起通知；') }} </span>{{ $t('注意！请及时处理故障，以免影响业务正常运行。') }} </div>
        <bk-input v-model="confirm.content" type="textarea" class="alarm-config-content" :placeholder="$t('填写告警确认备注信息')" :rows="5"></bk-input>
      </div>
    </bk-dialog>
    <!-- alarm confirm end -->
    <!-- 告警屏蔽 -->
    <template v-if="detail">
      <alarm-shield-event
        :detail="detail"
        :is-show.sync="isShow"
        :event-id="id"
        @change-is-shielded="handleChangeIsShielded">
      </alarm-shield-event>
    </template>
    <collect-chart
      is-single
      :total-count="1"
      :show="collect.show"
      :collect-list="collect.list" />
    <log-retrieval-dialog v-if="logRetrieval.isMounted"
                          :show="logRetrieval.show"
                          :index-list="logRetrieval.indexList"
                          :show-tips="logRetrieval.isShowTip"
                          :ip="logRetrieval.ip"
                          @showChange="handleLogDialogShow" />
  </div>
</template>
<script>
import MonitorEchart from '../../../../monitor-ui/monitor-echarts/monitor-echarts-new'
import AlarmLogList from './alarm-log-list'
import AlarmNoticeDetail from './alarm-notice-detail'
import Editor from '../../../components/markdown-editor/markdown-edior'
import { addListener, removeListener } from 'resize-detector'
import { debounce } from 'throttle-debounce'
import { createNamespacedHelpers } from 'vuex'
import { ackEvent, getSolution, saveSolution, eventGraphQuery,
  listIndexByHost } from '../../../../monitor-api/modules/alert_events'
import AlarmShieldEvent from '../../alarm-shield/quick-alarm-shield/quick-alarm-shield-event'
import CollectChart from '../../data-retrieval/data-retrieval-view/collect-chart'
import formLabelMixin from '../../../mixins/formLabelMixin'
import authorityMinxinCreate from '../../../mixins/authorityMixin.ts'
import moment from 'moment'
import { transformDataKey } from '../../../../monitor-common/utils/utils'
import * as eventAuth from '../authority-map.ts'
import { MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../../grafana/authority-map'
import authorityStore from '../../../store/modules/authority'
import { fetchItemStatus } from '../../../../monitor-api/modules/strategies'
import LogRetrievalDialog from './log-retrieval-dialog/log-retrieval-dialog'

const authMap = {
  ...eventAuth,
  GRAFANA_MANAGE_AUTH
}
const { mapActions } = createNamespacedHelpers('event-center')
export default {
  name: 'EventCenterDetail',
  components: {
    Editor,
    AlarmLogList,
    AlarmNoticeDetail,
    AlarmShieldEvent,
    MonitorEchart,
    CollectChart,
    LogRetrievalDialog
  },
  mixins: [formLabelMixin, authorityMinxinCreate(authMap)],
  props: {
    id: [Number, String]
  },
  data() {
    return {
      isShow: false,
      loading: false,
      detail: null,
      tab: {
        list: [
          {
            name: this.$t('视图信息')
          },
          {
            name: this.$t('处理建议')
          },
          {
            name: this.$t('流转记录')
          }
        ],
        active: 0
      },
      // 告警确认
      confirm: {
        show: false,
        loading: false,
        content: ''
      },
      // 通知状态明细
      notice: {
        show: false,
        defaultSelectActionId: -1
      },
      // 流转状态类型
      filter: {
        list: [
          {
            id: 'ACK',
            name: this.$t('告警确认'),
            checked: true,
            mockChecked: true,
            disabled: false
          },
          {
            id: 'ANOMALY_NOTICE',
            name: this.$t('告警通知'),
            checked: true,
            mockChecked: true,
            disabled: false
          }, {
            id: 'CREATE',
            name: this.$t('告警触发'),
            checked: true,
            mockChecked: true,
            disabled: false
          }, {
            id: 'CONVERGE',
            name: this.$t('告警收敛'),
            checked: true,
            mockChecked: true,
            disabled: false
          }, {
            id: 'RECOVER',
            name: this.$t('告警恢复'),
            checked: true,
            mockChecked: true,
            disabled: false
          },
          {
            id: 'CLOSE',
            name: this.$t('告警关闭'),
            checked: true,
            mockChecked: true,
            disabled: false
          }
        ]
      },
      chart: {
        width: 0,
        colors: ['#FDB980'],
        first: true,
        key: 0,
        renderChart: true,
        selectForFetch: true,
        observeIntersection: true,
        emptyText: this.$t('查询无数据'),
        title: '',
        subtitle: '',
        chartType: 'line'
      },
      log: {
        list: [],
        offset: 0,
        limit: 10,
        operate: [],
        scroll: false,
        isAll: false,
        first: true,
        loading: false,
        abnormal: false,
        defaultClickCollapseIndex: -1
      },
      // log中上一次 offset（解决event_log重复请求的偶先问题）
      lastLogOffset: -1,
      advise: {
        text: '',
        mockText: '',
        loading: false,
        first: true
      },
      listenResize() {

      },
      eventStatusMap: {
        RECOVERED: this.$t('已恢复'),
        ABNORMAL: this.$t('未恢复'),
        CLOSED: this.$t('已关闭')
      },
      strategyStatusMap: {
        UPDATED: this.$t('（配置已被修改）'),
        DELETED: this.$t('（配置已被删除）')
      },
      // 无需提示错误的状态码
      noGraphCode: [3314003, 3314004, 3308005],
      collect: {
        show: false,
        list: []
      },
      authorityMap: authMap,
      logRetrieval: {
        show: false,
        isMounted: false,
        isCanClick: false,
        isShowTip: false,
        isJumpDirectly: false, // 是否直接跳转到日志
        indexId: 0,
        indexList: [],
        ip: '0.0.0.0'
      }
    }
  },
  computed: {
    detailAlertInfo() {
      if (this.detail?.alertInfo && this.detail.alertInfo.count > 0) {
        const list = []
        Object.keys(this.detail.alertInfo).forEach((key) => {
          const count = this.detail.alertInfo[key]
          if (count > 0) {
            if (key === 'failedCount') {
              list.push(`${count}${this.$t('次失败')}`)
            } else if (key === 'partialCount') {
              list.push(`${count}${this.$t('次部分失败')}`)
            } else if (key === 'successCount') {
              list.push(`${count}${this.$t('次成功')}`)
            } else if (key === 'shieldedCount') {
              list.push(`${count}${this.$t('次被屏蔽')}`)
            } else if (key === 'emptyReceiverCount') {
              list.push(`${count}${this.$t('次通知状态为空')}`)
            }
          }
        })
        return list.join('，')
      }
      return ''
    },
    isAdviseChange() {
      return this.advise.text !== this.advise.mockText
    },
    isChecked() {
      return this.filter.list.filter(item => item.checked).length > 0
    },
    logEmptyIcon() {
      return this.log.abnormal ? 'icon-mc-abnormal' : 'icon-mc-empty'
    },
    eventLevelMap() {
      return this.$store.getters['constant/eventLevelMap']
    },
    chartOption() {
      if (this.chart.chartType === 'bar') {
        return  {
          tool: { list: ['save', 'screenshot', 'fullscreen', 'explore', 'set'] }
        }
      }
      return {
        tool: { list: ['save', 'screenshot', 'fullscreen', 'explore', 'set', 'area'] }
      }
    },
    filterDemisions() {
      return this.detail.dimensions.filter(item => !(item.name === 'bk_target_cloud_id' && item.value === '0'))
    }
  },
  watch: {
    'tab.active': {
      handler(v) {
        if (v === 2 && this.log.first) {
          this.log.first = false
          this.initLogList()
          this.handleGetLogList()
        } else if (v === 1 && this.advise.first) {
          this.handleGetAdivseData()
        }
      },
      immediate: true
    }
  },
  async activated() {
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
    await this.handleGetDetailData()
    this.tab.active === 2 ? this.initLogList() && this.handleGetLogList() : this.log.first = true
    this.tab.active === 1 ? this.handleGetAdivseData() : this.advise.first = true

    this.chart.selectForFetch = true
    this.chart.observeIntersection = true
    this.chart.emptyText = this.$t('查询无数据')
    this.chart.renderChart = true
  },
  deactivated() {
    this.chart.renderChart = false
    this.lastLogOffset = -1
  },
  mounted() {
    this.chart.width = this.$refs.chartWrap.clientWidth
    this.listenResize = debounce(300, v => this.handleChartResize(v))
    addListener(this.$refs.chartWrap, this.listenResize)
    this.handleAddScollListener()
    this.initFormLabelWidth()
    this.logRetrieval.isMounted = true
  },
  beforeDestroy() {
    removeListener(this.$refs.chartWrap, this.listenResize)
    this.handleRemoveScollListener()
  },
  methods: {
    ...mapActions(['getEventDetailData', 'getlistEventLog', 'getListConvergeLog']),
    handleToPerformance(item) {
      if (item.name === 'bk_target_ip') {
        const cloudId = this.detail.dimensions.find(item => item.name === 'bk_target_cloud_id')
        this.$router.push({
          name: 'performance-detail',
          params: {
            title: item.value,
            id: `${item.value}-${cloudId === undefined ? 0 : cloudId.value}`
          }
        })
      }
    },
    async  handleGetDetailData() {
      this.loading = true
      this.detail = null
      const detailData = await this.getEventDetailData({
        id: this.id,
        bk_biz_id: this.$store.getters.bizId // 非必填项（有全局bizId）
      })
      if (!detailData) {
        this.$router.push({
          name: 'error-exception'
        })
      } else {
        this.detail = detailData
        this.$store.commit(
          'app/SET_NAV_TITLE',
          `${this.$t('route-' + '告警详情').replace('route-', '')} - #${detailData.id}`
        )
        this.logRetrievalInit()
      }
      this.loading = false
    },
    async handleGetAdivseData() {
      this.advise.loading = this.advise.first
      this.advise.first = false
      const data = await getSolution({
        bk_biz_id: this.detail.bkBizId,
        id: this.detail.id
      }).catch(() => ({}))
      this.advise.text = data.solution || ''
      this.advise.mockText = this.advise.text
      this.advise.loading = false
    },
    async handleSaveAdvise() {
      this.advise.loading = true
      const success = await saveSolution({
        bk_biz_id: this.detail.bkBizId,
        id: this.detail.id,
        solution: this.advise.text
      }, { needRes: true }).catch(() => false)
      this.$bkMessage({
        theme: success?.result ? 'success' : 'error',
        message: success?.result ? this.$t('保存成功') : this.$t('保存失败')
      })
      this.advise.loading = false
    },
    // 获取告警状态信息
    async getAlarmStatus(id) {
      const data = await fetchItemStatus({ metric_ids: [id] }).catch(() => ({ [id]: 0 }))
      return data?.[id]
    },
    async handleGetSeriesData(startTime = '', endTime = '', range = false) {
      const { graphPanel } = this.detail
      const params = {
        bk_biz_id: this.$store.getters.bizId,
        id: this.detail.id
        // start_time: moment(event_begin_time).add(-1, 'h')
        //   .unix(),
        // end_time: moment()
        //   .unix()
      }
      if (range && startTime && endTime) {
        params.start_time = moment(startTime).unix()
        params.end_time = moment(endTime).unix()
      }
      if (graphPanel) {
        const [{ data: queryConfig, alias }] = graphPanel.targets
        this.chart.title = graphPanel.title || ''
        this.chart.subtitle = graphPanel.subTitle || ''
        this.chart.chartType = graphPanel.type === 'bar' ? 'bar' : 'line'
        if (queryConfig.extendMetricFields?.some(item => item.includes('is_anomaly'))) {
          queryConfig.function =  { ...queryConfig.function, max_point_number: 0 }
        }
        const chartQueryConfig = transformDataKey(queryConfig, true)
        const res = await eventGraphQuery(
          { ...chartQueryConfig, ...params }
          , { needRes: true, needMessage: false }
        ).catch((err) => {
          if (err && this.noGraphCode.includes(err.code)) {
            this.chart.selectForFetch = false
            this.chart.observeIntersection = false
            this.chart.emptyText = err.message
          } else {
            this.$bkMessage({
              message: err.message,
              theme: 'error',
              ellipsisLine: 0
            })
          }
        })
        this.chart.first = false
        const { level } = this.detail
        // const algorithmValue = algorithmList?.find(item => item?.level === level)?.algorithmConfig?.sensitivityValue
        // 异常检测图表转换
        // eslint-disable-next-line camelcase
        if (chartQueryConfig?.extend_fields?.intelligent_detect?.result_table_id && res?.data?.length) {
          const chartSeries = res.data.find(item => item?.metric?.metric_field === 'value'
          && item?.time_offset === 'current')
          if (!chartSeries) return []
          // 智能异常检测算法 边界画图设置
          const { dimensions } = chartSeries
          const coverList = []
          const algorithm2Level = {
            1: 15,
            2: 14,
            3: 13
          }
          const upBoundary = res.data?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
          && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
          && item.metric.metric_field === 'upper_bound')
            ?.datapoints?.map(item => ([item[1], item[0]])) || []
          const lowBoundary = res.data?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
          && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
          && item.metric.metric_field === 'lower_bound')
            ?.datapoints.map(item => ([item[1], item[0]])) || []
          const coverData = res.data?.find(item => item.dimensions.bk_target_ip === dimensions.bk_target_ip
          && item.dimensions.bk_target_cloud_id === dimensions.bk_target_cloud_id
          && item.metric.metric_field === 'is_anomaly')?.datapoints
          if (coverData?.length) {
            coverList.push({
              data: coverData.map((item, index) => ([chartSeries?.datapoints[index][1], item[0] > 0
                ? chartSeries?.datapoints[index][0]
                : null])),
              color: '#ea3636',
              z: algorithm2Level[level] + 10,
              name: `${level}-cover`
            })
          }
          const allData = res.data.filter(item => item?.metric?.metric_field === 'value')
            .map(({ target, datapoints, ...setData }) => {
              const item =  {
                datapoints,
                ...setData,
                target: this.handleBuildLegend(alias, {
                  ...setData,
                  tag: setData.dimensions,
                  metric: setData.metric,
                  formula: params.method,
                  ...params
                }) || target
              }
              if (setData.time_offset === 'current') {
                return {
                  ...item,
                  boundary: [
                    {
                      upBoundary,
                      lowBoundary,
                      color: '#e6e6e6',
                      stack: `${level}-boundary-${item.target}`,
                      z: algorithm2Level[level]
                    }
                  ],
                  coverSeries: coverList.map(set => ({ ...set, name: `${set.name}-${item.target}` }))
                }
              }
              return item
            })

          return allData
        }
        return res.data.map(({ target, datapoints, ...setData }) => ({
          datapoints,
          ...setData,
          target: this.handleBuildLegend(alias, {
            ...setData,
            tag: setData.dimensions,
            metric: setData.metric,
            formula: params.method,
            ...params
          }) || target
        }))
      }
      return []
    },
    handleFullScreen() {
      const { graphPanel } = this.detail
      const copyPanel = transformDataKey(graphPanel, true)
      // delete copyPanel.targets[0].alias
      this.$router.push({ name: 'view-detail',
        query: { config: JSON.stringify(copyPanel),
          compareValue: JSON.stringify({
            compare: { type: 'time', value: graphPanel.targets[0].data.function.timeCompare },
            tools: { timeRange: [this.detail.eventBeginTime.substr(0, 19), moment().format('YYYY-MM-DD HH:mm:s')] }
          }) } })
    },
    handleExportToRetrieval() {
      const { targets } = this.detail.graphPanel
      const [targetData] = targets
      // 日志平台跳转
      if (targetData?.data?.dataSourceLabel === 'bk_log_search') {
        const monitorParams = transformDataKey(targetData.data, true)
        const retrieveParams =  { // 检索参数
          keyword: monitorParams.query_string, // 搜索关键字
          addition: monitorParams?.where?.map(set => ({
            field: set.key,
            operator: set.method,
            value: (set.value || []).join(',')
          })) || []
        }
        // eslint-disable-next-line vue/max-len
        window.open(`${this.$store.getters.bkLogSearchUrl}#/retrieve/${monitorParams.result_table_id}?bizId=${this.$store.getters.bizId}&retrieveParams=${encodeURI(JSON.stringify(retrieveParams))}`)
      } else {
        window.open(`${location.href.replace(
          location.hash,
          '#/data-retrieval'
        )}?targets=${JSON.stringify(transformDataKey(targets, true))}`)
      }
    },
    async handleCollectSingleChart() {
      if (!this.authority.GRAFANA_MANAGE_AUTH) {
        authorityStore.getAuthorityDetail(this.authorityMap.GRAFANA_MANAGE_AUTH)
        return
      }
      if (this.collect.show) {
        this.collect.show = false
        this.collect.list = []
      }
      await this.$nextTick()
      const { graphPanel } = this.detail
      const copyPanel = transformDataKey(graphPanel, true)
      this.collect.list.push(copyPanel)
      this.collect.show = true
    },
    handleBuildLegend(alia, compareData = {}) {
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
    },
    handleChartResize() {
      const width = this.$refs.chartWrap.clientWidth
      if (width > 0) {
        this.chart.width = width
      }
    },
    handleGotoStrategy() {
      this.$router.push({
        name: 'strategy-config-detail',
        params: {
          eventId: this.detail.id,
          id: this.detail.strategyId,
          bizId: this.detail.bkBizId
        }
      })
    },
    handleShowAlarmConfirm() {
      this.confirm.show = true
    },
    async handleAlarmConfirm() {
      this.confirm.loading = true
      await ackEvent({
        bk_biz_id: this.detail.bkBizId,
        id: this.detail.id,
        message: this.confirm.content
      }, {
        needRes: true,
        needMessage: false
      }).then(() => {
        this.$bkMessage({
          message: this.$t('告警确认成功'),
          theme: 'success'
        })
        this.detail.isAck = true
      })
        .catch((err) => {
          this.$bkMessage({
            message: err.message || this.$t('告警确认失败'),
            theme: 'error',
            ellipsisLine: 0
          })
        })
      this.confirm.loading = false
      this.confirm.show = false
    },
    handleNoticeDetail(v = true, actionId = -1) {
      this.notice.defaultSelectActionId = actionId
      this.notice.show = v
    },
    handleTabChange(active) {
      this.tab.active = active
    },
    async handleGetLogList(conditions) {
      // 解决发两次event_log请求的问题
      if (this.lastLogOffset === this.log.offset) return
      this.log.loading = true
      this.log.abnormal = false
      const operate = conditions || this.handleGetConditions()
      const list = await this.getlistEventLog({
        bk_biz_id: this.detail.bkBizId,
        id: this.detail.id,
        offset: this.log.offset,
        limit: this.log.limit,
        operate
      }).catch(() => {
        this.log.loading = false
        this.log.abnormal = true
      })
      if (list?.length) {
        this.log.list.push(...list)
        // 保留上一次的ID
        this.lastLogOffset = this.log.offset
        // 记录最后一位ID
        this.log.offset = list[list.length - 1].actionId
      } else {
        this.log.isAll = true
      }
      this.log.scroll = false
      this.log.loading = false
    },
    handleScroll() {
      if (this.tab.active === 2 && !this.log.isAll) {
        const { scrollHeight } = this.$el
        const { scrollTop } = this.$el
        const { clientHeight } = this.$el
        if (clientHeight + scrollTop >= scrollHeight && !this.log.scroll) {
          this.log.scroll = true
          this.$el.scrollTo(0, scrollTop - 130)
          this.handleGetLogList()
        }
      }
    },
    handleLogListResize() {
      if (this.tab.active === 2 && !this.log.isAll) {
        setTimeout(() => {
          const { scrollHeight } = this.$el
          const { clientHeight } = this.$el
          if (clientHeight === scrollHeight && !this.log.scroll) {
            this.log.scroll = true
            this.handleGetLogList()
          }
        }, 30)
      }
    },
    handleCheckChange(v, item) {
      if (item) {
        item.checked = v
      }
      const checkedList = this.filter.list.filter(item => item.checked)
      if (checkedList.length === 1) {
        checkedList[0].disabled = true
      } else {
        checkedList.forEach((item) => {
          item.disabled = false
        })
      }
    },
    handleGetConditions() {
      const condition = []
      this.filter.list.forEach((item) => {
        if (item.checked) {
          condition.push(item.id)
        }
        item.mockChecked = item.checked
      })
      return condition
    },
    handleSetPopoverHide() {
      this.filter.list.forEach((item) => {
        item.checked = item.mockChecked
      })
      this.handleCheckChange()
    },
    handleConfirmSet() {
      this.filter.list.forEach((item) => {
        item.mockChecked = item.checked
      })
      const conditions = this.handleGetConditions()
      this.lastLogOffset = -1
      this.log.scroll = false
      this.log.list = []
      this.log.isAll = false
      this.log.offset = 0
      this.log.defaultClickCollapseIndex = -1
      this.$refs.setPopover.instance.hide(0)
      this.handleGetLogList(conditions)
    },
    handleCancelSet() {
      this.$refs.setPopover.instance.hide(0)
    },
    handleRemoveScollListener() {
      this.$el.removeEventListener('scroll', this.handleScroll, { passive: true })
    },
    handleAddScollListener() {
      this.$el.addEventListener('scroll', this.handleScroll, { passive: true })
    },
    handleShowQuickShield() {
      this.isShow = true
    },
    handleChangeIsShielded(v) {
      this.detail.isShielded = v
    },
    // 屏蔽策略详情
    handleGotoShieldStrategy(id) {
      this.$router.push({ name: 'alarm-shield-detail', params: { id, eventId: this.detail.id } })
    },
    initLogList() {
      this.log.list = []
      this.log.offset = 0
      this.log.operate = []
      this.log.scroll = false
      this.log.isAll = false
      this.log.first = false
      this.log.abnormal = false
      return true
    },
    async handleInsertItemIntoLogList(item, index) {
      const convergeData = await this.getListConvergeLog({
        bk_biz_id: this.$store.getters.bizId,
        id: this.id,
        time_range: `${item.beginTime} -- ${item.time}`
      })
      // 将要展开的数据插入list中并设置next属性
      this.log.list.splice(index + 1, 0, ...convergeData)
      this.log.list[index].next = index + convergeData.length
      // 数据更新完毕通知alarm-log-list组件执行点击事件
      this.log.defaultClickCollapseIndex = index
    },
    handleLogRetrieval() {
      if (this.logRetrieval.isJumpDirectly) {
        const host = window.bk_log_search_url || window.bklogsearch_host
        window.open(`${host}#/retrieve/${this.logRetrieval.indexId}?bizId=${this.$store.getters.bizId}`)
      } else {
        this.logRetrieval.show = true
      }
    },
    handleLogDialogShow(v) {
      this.logRetrieval.show = v
    },
    async logRetrievalInit() {
      const ipMap = ['bk_target_ip', 'ip']
      const cloudMap = ['bk_target_cloud_id', 'bk_cloud_id']
      this.logRetrieval.isCanClick = false
      this.logRetrieval.isJumpDirectly = false
      // 如果有logIndexId则可直接跳转到日志
      if (this.detail.logIndexId) {
        this.logRetrieval.indexId = this.detail.logIndexId
        this.logRetrieval.isJumpDirectly = true
        this.logRetrieval.isCanClick = true
        return
      }
      // 是否显示跳转到日志的icon
      this.logRetrieval.isCanClick = this.detail.dimensions.some(item => ipMap.includes(item.name) && item.value)
      if (!this.logRetrieval.isCanClick) return
      let cloudId = 0
      let ip = '0.0.0.0'
      this.detail.dimensions.forEach((item) => {
        if (cloudMap.includes(item.name) && item.value) {
          cloudId = item.value
        }
        if (ipMap.includes(item.name) && item.value) {
          ip = item.value
        }
      })
      const params = {
        ip,
        bk_cloud_id: +cloudId
      }
      this.logRetrieval.ip = ip
      this.logRetrieval.indexList = await listIndexByHost(params).catch(() => ([]))
      // 如果查不到索引集则显示提示
      if (!this.logRetrieval.indexList.length) {
        this.logRetrieval.isShowTip = true
      }
    }
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common";
$statusColors: $deadlyAlarmColor $warningAlarmColor $remindAlarmColor;
$statusBgColors: $deadlyAlarmColor $warningAlarmColor $remindAlarmColor;

.event-center-detail {
  font-size: 12px;
  color: #63656e;
  overflow: auto;
  height: calc(100vh - 60px);
  margin: -20px -25px -20px -20px;
  padding: 20px 25px 20px 20px;
  &.detail-loading {
    min-height: calc(100vh - 100px);
  }
  .detail-panel {
    display: flex;
    flex-direction: column;
    min-height: 252px;
    border: 1px solid #dcdee5;
    background: #fff;
    border-radius: 2px;
    padding: 16px 14px;
    margin-bottom: 4px;
    &-status {
      height: 32px;
      display: flex;
      flex: 0 0 32px;
      align-items: center;
      justify-content: center;
      border: 1px solid #ffc1c1;
      background: #fdd;
      border-radius: 2px;
      color: #ff5656;
      margin-bottom: 8px;
      .panel-icon {
        font-size: 16px;
        margin-right: 6px;
      }
      &.status-recovered {
        border-color: #94f5a4;
        background-color: #dcffe2;
        color: #2dcb56;
      }
      &.status-abnormal {
        border-color: #ffc1c1;
        background-color: #fdd;
        color: #ff5656;
      }
      &.status-closed {
        border-color: #d9dbe2;
        background-color: #fafbfd;
        color: #979ba5;
      }
    }
    .detail-form {
      &-item {
        display: flex;
        align-items: center;
        width: 100%;
        .item-col {
          flex: 1;
          height: 36px;
          display: flex;
          align-items: center;
          font-size: 14px;
          .item-label {
            color: #000;
            text-align: right;
            flex: 0 0 98px;
          }
          .item-content {
            margin: 0 44px 0 24px;
            display: flex;
            align-items: center;
            &.dimensions {
              flex-wrap: wrap;
              .nowrap {
                white-space: nowrap;
              }
            }
            .info-mark {
              width: 4px;
              height: 14px;
              border-radius: 4px;

              @for $i from 1 through length($statusColors) {
                &.status-#{$i} {
                  background: nth($statusColors, $i);
                }
              }
            }
            .info-status {
              margin-left: 4px;

              @for $i from 1 through length($statusColors) {
                &.status-#{$i} {
                  color: nth($statusColors, $i);
                }
              }
            }
            .info-shield,
            .info-affirm,
            .info-check {
              color: #3a84ff;
              margin-left: 6px;
              cursor: pointer;
            }
            .info-detail {
              color: #3a84ff;
              cursor: pointer;
            }
            .icon-guanlian {
              color: #3a84ff;
              font-size: 12px;
              margin-left: 8px;
              margin-top: 4px;
              cursor: pointer;
            }
          }
        }
        .item-col-dimensions {
          // align-items: flex-start;
          min-height: 36px;
          height: auto;
          .item-content {
            word-break: break-all;
          }
        }
      }
    }
  }
  .detail-tab {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #dcdee5;
    &-item {
      width: 130px;
      height: 50px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 2px solid transparent;
      font-size: 14px;
      margin-bottom: -1px;
      &.item-active {
        color: #3a84ff;
        border-bottom-color: #3a84ff;
      }
      &.item-last {
        margin-right: auto;
      }
      &:hover {
        color: #3a84ff;
        cursor: pointer;
      }
    }
    &-icon {
      margin-left: auto;
      height: 32px;
      width: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #c4c6cc;
      border-radius: 2px;
      color: #63656e;
      font-size: 16px;
      cursor: pointer;
      .icon-monitor {
        height: 15px;
        width: 15px;
      }
    }
  }
  .detail-content {
    padding-top: 16px;
    &-editor {
      border-radius: 2px;
      margin-bottom: 16px;
    }
    &-chart {
      border: 1px solid #dcdee5;
      border-radius: 2px;
      padding: 10px;
      background: white;
    }
    &-log {
      background: #fff;
      border: 1px solid #dcdee5;
      border-radius: 2px;
      min-height: calc(100vh - 500px);
      margin-bottom: 10px;
    }
    .log-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #c4c6cc;
      &-icon {
        font-size: 32px;
      }
      &-label {
        margin-top: 10px;
      }
    }
    .content-log-empty {
      display: flex;
      justify-content: center;
      align-items: center;
    }
  }
}
.alarm-filter-theme {
  .set-filter {
    display: flex;
    flex-direction: column;
    margin: -7px -14px;
    &-title {
      color: #313238;
      font-size: 20px;
      margin: 18px 0  26px 24px;
    }
    &-list {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      margin-left: 24px;
      .list-item {
        margin-right: 76px;
        margin-bottom: 18px;
      }
    }
    &-footer {
      background-color: #fafbfd;
      border-top: 1px solid #dcdee5;
      display: flex;
      align-items: center;
      height: 50px;
      margin-top: 30px;
      padding-right: 24px;
      .footer-btn {
        margin-left: auto;
        margin-right: 10px;
      }
    }
  }
}
.alarm-confirm {
  font-size: 12px;
  color: #63656e;
  &-desc {
    height: 50px;
    padding: 5px 6px;
    line-height: 20px;
    background-color: #f6f6f6;
    margin-bottom: 14px;
    .desc-mark {
      color: #313238;
    }
  }
}
</style>
