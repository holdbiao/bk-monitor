<template>
  <div class="event-center" ref="wrapper" v-bkloading="{ isLoading: loading }" :class="{ 'event-loading': loading || firstLoading }">
    <!-- 未恢复告警数据标签 -->
    <div class="event-center-tag">
      <div class="event-tag"
           :class="{ 'tag-active': tag.active === item.id }"
           @click="handleTagClick(item, index)"
           v-for="(item, index) in tag.list"
           :key="index">
        <span class="event-tag-name">{{item.name}}</span>
        <span class="event-tag-num" :class="{ 'num-active': tag.active === item.id, 'status-default': index === 2 || index === 0 }">{{item.num}}</span>
      </div>
      <bk-button style="margin-left: auto;" :theme="'default'" @click="handleShowConfirm" :disabled="!checkedIds.length" :loading="batchLoading">{{$t('批量确认')}}</bk-button>
      <bk-button
        type="submit"
        class="export-btn"
        :disabled="!table.data.length"
        :loading="exportLoading"
        @click="handleExportClick">
        {{ $t('导出') }}
      </bk-button>
    </div>
    <!-- 搜索条件 -->
    <div class="event-center-search">
      <bk-search-select
        ref="searchSelect"
        v-model="search.value"
        class="search-input"
        :show-condition="false"
        :data="searchList" :placeholder="$t('搜索ID，来源，内容')">
      </bk-search-select>
      <bk-checkbox :value="tag.checked" @change="handleCheckChange" style="margin-left: 10px;"> {{ $t('我的') }} </bk-checkbox>
      <bk-date-picker
        ref="searchDate"
        v-model="search.date"
        :clearable="false"
        :shortcuts="search.shortcuts"
        @open-change="handleOpenChange"
        @pick-success="handlePickSuccess"
        class="search-date"
        format="yyyy-MM-dd HH:mm:ss"
        :placeholder="$t('选择日期时间范围')"
        type="datetimerange">
      </bk-date-picker>
      <span class="icon-monitor icon-mc-event-chart search-icon"
            v-bk-tooltips.bottom-start="$t('告警变化趋势')"
            @click="handleShowChart"
            :class="{ 'active-icon': search.showChart }">
      </span>
      <!-- <span class="bk-icon icon-order search-icon"
                @click="search.tableSet = !search.tableSet"
                :class="{ 'active-icon': search.tableSet }">
            </span> -->
    </div>
    <!-- 告警变化趋势堆叠图 -->
    <div class="event-center-chart" v-show="search.showChart" ref="chartWrap" v-bkloading="{ isLoading: loadingChart }">
      <keep-alive>
        <monitor-echart
          v-if="search.showChart"
          chart-type="bar"
          :series="chartSeries"
          height="310"
          :title="$t('告警变化趋势')"
          :colors="['#E27676', '#95CC73', '#DCDEE5']">
        </monitor-echart>
      </keep-alive>
    </div>
    <!-- 表格 -->
    <div class="event-center-table" :style="{ 'border-bottom': table.loading ? '1px solid #DCDEE5' : 'none' }" v-bkloading="{ isLoading: table.loading }">
      <div class="table-head">
        <span class="table-row-col head-col col-mark"></span>
        <span class="table-row-col head-col col-checkbox">
          <bk-checkbox
            :indeterminate="isIndeterminate"
            :checked="isAllChecked"
            @change="handleAllCheckedChange">
          </bk-checkbox>
        </span>
        <span class="table-row-col head-col col-tips"></span>
        <span class="table-row-col head-col col-id sort" @click="handleSortChange('id')">
          ID
          <sort-caret :active="sort.name === 'id' ? sort.list[sort.active] : 'normal'"></sort-caret>
        </span>
        <!-- <span class="table-row-col head-col col-bussiness">业务</span> -->
        <span class="table-row-col head-col col-times"> {{ $t('告警次数') }} </span>
        <span class="table-row-col head-col col-continue"> {{ $t('持续时长') }} </span>
        <span class="table-row-col head-col col-date sort" @click="handleSortChange('create_time')">
          {{ $t('发生时间') }}
          <sort-caret :active="sort.name === 'create_time' ? sort.list[sort.active] : 'normal'"></sort-caret>
        </span>
        <span class="table-row-col head-col col-origin">
          {{ $t('触发策略') }}
          <!-- <filter-funnel></filter-funnel> -->
        </span>
        <span class="table-row-col head-col col-content"> {{ $t('通知内容') }} </span>
        <span class="table-row-col head-col col-content"> {{ $t('关联信息') }} </span>
        <span class="table-row-col head-col col-notice"> {{ $t('最近通知状态') }} </span>
        <span class="table-row-col head-col col-status"> {{ $t('告警状态') }} </span>
      </div>
      <template v-if="table.data.length">
        <div class="table-row" v-for="(item, index) in table.data" :key="index">
          <div class="table-row-col col-mark">
            <span class="icon-monitor icon-double-down"
                  :class="{ 'collapse-icon': !item.collapse }"
                  v-if="item.children && item.children.length"
                  @click="handleRowCollapse(item, index)">
            </span>
          </div>
          <div class="table-row-col col-checkbox">
            <bk-checkbox v-model="item.checked" :disabled="item.eventStatus !== 'ABNORMAL' || item.isAck"></bk-checkbox>
          </div>
          <div class="table-row-col col-tips">
            <span class="event-status" :class="'status-' + item.level"></span>
          </div>
          <div class="table-row-col col-id">
            <span class="event-id" @click="handleGotoDetail(item.id, item)">#{{ item.id }}</span>
          </div>
          <!-- <div class="table-row-col col-bussiness">{{ item.bizName }}</div> -->
          <div class="table-row-col col-times">
            <div class="col-times-content">
              <span>{{ item.anomalyCount }}</span>
            </div>
          </div>
          <div class="table-row-col col-continue">{{ item.duration }}</div>
          <div class="table-row-col col-date">{{ item.beginTime }}</div>
          <div class="table-row-col col-origin">
            <span v-bk-overflow-tips="{ content: item.strategyName }"
                  class="col-origin-content">
              {{ item.strategyName }}
            </span>
          </div>
          <div class="table-row-col col-content col-content-line-feed">
            <span v-for="(msg, i) in item.eventMessage" :key="i" class="line-feed-content" :title="msg">
              {{ msg }}
            </span>
          </div>
          <!-- 关联信息 -->
          <div class="table-row-col col-content col-content-line-topo">
            <template v-if="item.topoInfo">
              <!-- 主机 -->
              <div v-if="item.topoInfo.type === 'host'">
                <div class="line-topo-content">{{`${$t('主机名：')}${item.topoInfo.hostname}`}}</div>
                <div class="line-topo-content">{{`${$t('节点信息：')}${item.topoInfo.topo_info}`}}<span class="link more" @click="handleGotoMore(item.topoInfo)">{{$t('更多')}}</span></div>
              </div>
              <!-- 日志 -->
              <div v-else-if="item.topoInfo.type === 'log_search'">
                <span class="link" @click="handleGotoMore(item.topoInfo)">{{$t('查看更多相关的日志数据')}}</span>
              </div>
              <!-- 事件 -->
              <div v-else-if="item.topoInfo.type === 'custom_event'">
                <span class="link" @click="handleGotoMore(item.topoInfo)">{{$t('查看更多相关的事件数据')}}</span>
              </div>
              <!-- 数据检索 -->
              <div v-else-if="item.topoInfo.type === 'bkdata'">
                <span class="link" @click="handleGotoMore(item.topoInfo)">{{$t('查看更多相关的数据')}}</span>
              </div>
            </template>
            <template v-else>--</template>
          </div>
          <div class="table-row-col col-notice" :class="{ 'notice-success': item.alertStatus === 'SUCCESS' }">{{ table.alertStatusMap[item.alertStatus] || '--' }}</div>
          <div class="table-row-col col-status" @mouseover="item.isAck && handleMouseOver(item, $event)" @mouseleave="item.isAck && handleMouseLeave(item, $event)">
            <span class="event-operate" :class="'operate-' + item.eventStatus.toLocaleLowerCase()">{{ table.eventStatusMap[item.eventStatus] }}</span>
            <span class="event-checked" v-if="item.isAck && item.eventStatus === 'ABNORMAL'"> {{ $t('（已确认）') }} </span>
            <span class="event-checked" v-if="!item.isAck && item.isShielded && item.shieldType === 'saas_config' && item.eventStatus === 'ABNORMAL'"> {{ $t('（已屏蔽）') }} </span>
            <span class="event-checked" v-if="!item.isAck && item.isShielded && item.shieldType !== 'saas_config' && item.eventStatus === 'ABNORMAL'"> {{ $t('（已抑制）') }} </span>
          </div>
          <div class="child-wrapper" v-if="item.children && item.children.length">
            <transition :css="false"
                        @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
                        @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave">
              <div v-show="item.collapse" class="child-wrapper-collaspe">
                <template v-for="(child, childIndex) in item.children">
                  <div class="table-row child-row" :class="{ 'analyze-row': child.showAnalyze }" :key="childIndex" v-if="!child.isLastRow">
                    <div class="table-row-col col-mark" :class="{ 'no-border': childIndex < item.children.length - 1 }">
                    </div>
                    <div class="table-row-col col-tips">
                      <span class="event-status" :class="'status-' + item.level"></span>
                      <span v-if="child.showAnalyze" class="event-mark"> {{ $t('以下为最近24小时分析') }} </span>
                    </div>
                    <div class="table-row-col col-id">
                      <span class="event-id" @click="handleGotoDetail(child.id, child)">{{ child.id }}</span>
                    </div>
                    <div class="table-row-col col-bussiness">{{ child.bizName}}</div>
                    <div class="table-row-col col-times">{{ child.anomalyCount }}</div>
                    <div class="table-row-col col-continue">{{ child.duration }}</div>
                    <div class="table-row-col col-date">{{ child.beginTime }}</div>
                    <div class="table-row-col col-origin">{{ child.strategyName }}</div>
                    <div class="table-row-col col-content">{{ child.eventMessage }}</div>
                    <div class="table-row-col col-notice" :class="{ 'notice-success': child.alertStatus === 'SUCCESS' }">{{ table.alertStatusMap[child.alertStatus] }}</div>
                    <div class="table-row-col col-status">
                      <span class="event-operate">{{ table.eventStatusMap[child.eventStatus] }}</span>
                    </div>
                  </div>
                  <div v-else class="table-row child-row empty-row" :key="childIndex"> {{ $t('由于数量过多，剩余2359条已为您自动隐藏（可进入流转记录查看明细）') }} </div>
                </template>
              </div>
            </transition>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="table-empty">
          <i class="bk-icon icon-empty"></i>
          <span> {{ $t('查询无数据') }} </span>
        </div>
      </template>
    </div>
    <!-- 分页 -->
    <template v-if="table.total">
      <bk-pagination
        v-show="table.data.length"
        class="event-center-pagination list-pagination"
        align="right"
        size="small"
        pagination-able
        :count="table.total"
        :current="table.page"
        :limit="table.pageSize"
        :limit-list="table.pageList"
        show-total-count
        @change="handlePageChange"
        @limit-change="handleLimitChange">
      </bk-pagination>
    </template>
    <div class="event-center-footer" v-if="false">
      <span class="footer-total" v-if="table.data.length"> {{ $t('已加载') }} {{table.data.length}} {{ $t('条')}} {{$t('（共100条）') }} </span>
      <div class="footer-loading" v-show="scroll.show">
        <img src="../../../static/images/svg/spinner.svg" /> {{ $t('正加载更多内容…') }} </div>
    </div>
    <bk-dialog :title="$t('告警确认')" width="480" v-model="confirm.show" @confirm="handleBatch">
      <div class="alarm-confirm">
        <div class="alarm-confirm-desc"> {{ $t('重要提醒：告警确认后，异常持续未恢复的情况下，') }} <span class="desc-mark"> {{ $t('将不会再发起通知；') }} </span>{{ $t('注意！请及时处理故障，以免影响业务正常运行。') }} </div>
        <bk-input v-model="confirm.content" type="textarea" class="alarm-config-content" :placeholder="$t('填写告警确认备注信息')" :rows="5"></bk-input>
      </div>
    </bk-dialog>
  </div>
</template>
<script lang="js">
import moment from 'moment'
import { collapseMixin, commonPageSizeMixin } from '../../common/mixins'
import { addListener, removeListener } from 'resize-detector'
import { debounce } from 'throttle-debounce'
import { createNamespacedHelpers } from 'vuex'
import SortCaret from './sort-caret.vue'
import MonitorEchart from '../../../monitor-ui/monitor-echarts/monitor-echarts.vue'
import authorityMinxinCreate from '../../mixins/authorityMixin.ts'
import * as eventAuth from './authority-map.ts'
import { downFile } from '../../utils/index.ts'
import { ackEvent, eventRelatedInfo } from '../../../monitor-api/modules/alert_events'
import { CancelToken } from '../../../monitor-api/index'
const { mapActions, mapGetters } = createNamespacedHelpers('event-center')

export default {
  name: 'EventCenter',
  components: {
    MonitorEchart,
    SortCaret
    // FilterFunnel
  },
  // 公共过渡效果钩子函数
  mixins: [collapseMixin, commonPageSizeMixin, authorityMinxinCreate(eventAuth)],
  data() {
    const dateNow = moment().format('YYYY-MM-DD HH:mm:ss')
    const lastDate = moment(dateNow).add(-1, 'd')
      .format('YYYY-MM-DD HH:mm:ss')
    return {
    //   cancelFn: null,
      batchLoading: false,
      loading: false,
      firstLoading: false,
      exportLoading: false, // 导出loading
      confirm: {
        show: false,
        loading: false,
        content: ''
      },
      // 未恢复告警数据标签
      tag: {
        list: [
          {
            name: this.$t('全部'),
            num: 0,
            status: 3,
            id: 'ALL'
          },
          {
            name: this.$t('未恢复'),
            num: 0,
            status: 0,
            id: 'ABNORMAL'
          },
          {
            name: this.$t('已屏蔽未恢复'),
            num: 0,
            status: 1,
            id: 'SHIELD_ABNORMAL'
          }
        ],
        active: 'ALL',
        checked: false
      },
      chart: {
        width: 0,
        refresh: false
      },
      // 搜索条件
      search: {
        showChart: false,
        tableSet: false,
        value: [],
        routerSearchParams: [],
        routerDateParams: null,
        date: [lastDate, dateNow],
        mockDate: [lastDate, dateNow],
        shortcuts: [
          {
            text: this.$t('近1小时'),
            value() {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - (3600 * 1000))
              return [start, end]
            },
            onClick: this.handleShortcutClick
          },
          {
            text: this.$t('近12小时'),
            value() {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - (3600 * 1000 * 12))
              return [start, end]
            },
            onClick: this.handleShortcutClick
          },
          {
            text: this.$t('近1天'),
            value() {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - (3600 * 1000 * 24))
              return [start, end]
            },
            onClick: this.handleShortcutClick
          },
          {
            text: this.$t('近7天'),
            value() {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - (3600 * 1000 * 24 * 7))
              return [start, end]
            },
            onClick: this.handleShortcutClick
          }
        ]
      },
      sort: {
        name: '',
        active: 0,
        list: ['normal', 'asc', 'desc']
      },
      // 表格
      table: {
        loading: true,
        data: [],
        total: 100,
        page: 1,
        pageSize: this.handleGetCommonPageSize(),
        pageList: [10, 20, 50, 100],
        collapseIndex: -1,
        alertStatusMap: {
          SUCCESS: this.$t('成功'),
          FAILED: this.$t('失败'),
          SHIELDED: this.$t('已屏蔽'),
          PARTIAL_SUCCESS: this.$t('部分失败'),
          EMPTY_RECEIVER: this.$t('通知人为空')
        },
        eventStatusMap: {
          RECOVERED: this.$t('已恢复'),
          ABNORMAL: this.$t('未恢复'),
          CLOSED: this.$t('已关闭')
        }
      },
      scroll: {
        show: false
      },
      // 弹出提示框
      popoverInstance: null,
      lisenResize() {

      },
      chartOptions: {
        tooltip: {
          crosshairs: null,
          shared: false,
          followPointer: false,
          followTouchMove: false
        }
      },
      chartSeries: null,
      loadingChart: false,
      // 回显Params Map
      levelObj: {
        1: this.$t('致命'),
        2: this.$t('预警'),
        3: this.$t('提醒')
      },
      backDisplayParamsMap: {
        status: {
          id: 'event_status',
          name: this.$t('告警状态'),
          statusName: this.$t('未恢复')
        },
        strategyId: {
          id: 'strategy_id',
          name: this.$t('触发策略')
        },
        //  策略跳转事件中心IP
        ip: {
          id: 'ip',
          name: this.$t('主机ip')
        },
        metricId: {
          id: 'metric_id',
          name: this.$t('指标ID')
        },
        level: {
          id: 'level',
          name: this.$t('告警级别')
        },
        collectId: {
          id: 'alert_collect_id',
          name: this.$t('告警汇总ID')
        },
        id: {
          id: 'id',
          name: this.$t('事件ID')
        },
        query: {
          id: 'query'
        }
      },
      // 回显Url Map
      backDisplayUrlMap: {
        // URL参数 事件ID
        id: {
          id: 'id',
          name: this.$t('事件ID')
        },
        // URL参数 告警汇总ID
        collectId: {
          id: 'alert_collect_id',
          name: this.$t('告警汇总ID')
        }
      }
    }
  },
  computed: {
    ...mapGetters(['searchList']),
    // todo delete logical
    collaspseItem() {
      if (this.table.collapseIndex > -1) {
        return this.table.data[this.table.collapseIndex]
      }
      return null
    },
    isIndeterminate() {
      const checkedCount = this.table.data
        .filter(item => item.eventStatus === 'ABNORMAL' && !item.isAck).filter(item => item.checked).length
      const leng = this.table.data.filter(item => item.eventStatus === 'ABNORMAL' && !item.isAck).length
      return checkedCount > 0 ? checkedCount < leng : false
    },
    isAllChecked() {
      const checkedCount = this.table.data
        .filter(item => item.eventStatus === 'ABNORMAL' && !item.isAck).filter(item => item.checked).length
      const leng = this.table.data.filter(item => item.eventStatus === 'ABNORMAL' && !item.isAck).length
      return checkedCount > 0 ? checkedCount === leng : false
    },
    checkedIds() {
      const ids = this.table.data.filter(item => item.checked).map(item => item.id)
      return ids
    }
  },
  watch: {
    'search.value': {
      async handler() {
        this.$nextTick().then(() => {
          this.$refs.searchSelect.hidePopper()
          this.table.page = 1
          this.handleGetEventList()
          this.firstLoading = false
        })
      },
      deep: true
    }
  },
  created() {
    this.handleActivated()
  },
  mounted() {
    this.lisenResize = debounce(300, v => this.handleChartResize(v))
    addListener(this.$refs.chartWrap, this.lisenResize)
  },
  beforeDestroy() {
    removeListener(this.$refs.chartWrap, this.lisenResize)
    this.handleMouseLeave()
    // this.handleRemoveScollListener()
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      const params = to.query ||  to.params
      vm.handleHomeDateParam(params)
      !vm.firstLoading && vm.handleActivated(from.name, true)
    })
  },
  methods: {
    ...mapActions(['getSearchList', 'getEventList', 'getChartData']),
    // 点击导出按钮
    async handleExportClick() {
      this.exportLoading = true
      const data = await this.getEventList(this.handleGetParams(true)).catch(() => null)
      if (!data) return
      let url = data.download_path
      if (data.download_path.indexOf('http') !== 0) {
        url = process.env.NODE_ENV === 'development'
          ? `${process.env.proxyUrl}/media${data.download_path}`
          : `${window.location.origin}${window.site_url}media${data.download_path}`
      }
      // 下载文件
      downFile(`${url}/${data.download_name}`, data.download_name)
      this.exportLoading = false
    },
    async handleGetEventList(fromPageChange = false, needLoading = false) {
      // this.loading = true
      this.$store.commit('app/SET_MAIN_LOADING', needLoading)
      this.table.loading = !needLoading
      this.table.data = []
      const promiseList = []
      if (this.searchList.length < 1) {
        promiseList.push(this.getSearchList({
          bk_biz_ids: [this.$store.getters.bizId]
        }))
      }
      if (this.search.showChart && !fromPageChange) {
        promiseList.push(this.handleGetChartData(false))
      } else if (!fromPageChange) {
        // 下次展开更新
        this.chart.refresh = true
      }
      promiseList.push((async () => {
        // 以确保关联信息跟事件详情接口数据一一对应, 避免网络问题导致数据错乱
        if (this.cancelFn) this.cancelFn()
        const data = await this.getEventList(this.handleGetParams())
        if (data?.eventList.length) {
          const ids = data.eventList.map(item => item.id)
          this.handleGetEventRelatedInfo(ids)
        }
        this.table.data = data.eventList.map((item) => {
          this.$set(item, 'checked', false)
          return item
        })
        this.tag.list[0].num = data.tagData.allCount
        this.tag.list[1].num = data.tagData.anomalyCount
        this.tag.list[2].num = data.tagData.shieldAnomalyCount
        // this.table.total = data.tagData.total
        this.table.total = this.tag.list.find(item => item.id === this.tag.active).num
      })())
      const res = await Promise.all(promiseList)
      this.$store.commit('app/SET_MAIN_LOADING', false)
      // this.loading = false
      this.table.loading = false
      return res
    },
    // 获取关联信息
    async handleGetEventRelatedInfo(ids) {
      eventRelatedInfo({ ids }, { cancelToken: new CancelToken(c => this.cancelFn = c) }).then((data) => {
        for (const key in data) {
          const res = this.table.data.find(item => item.id === +key)
          res && this.$set(res, 'topoInfo', data[key])
        }
      })
    },
    handleInitActivatedData() {
      this.search.showChart = false
      this.tag.active = 'ALL'
      this.tag.checked = false
      const dateNow = moment().format('YYYY-MM-DD HH:mm:ss')
      const lastDate = moment(dateNow).add(-1, 'd')
        .format('YYYY-MM-DD HH:mm:ss')
      this.search.date = [lastDate, dateNow]
      this.search.mockDate = [lastDate, dateNow]
      this.search.value = []
    },
    // 获取变化趋势图数据
    async handleGetChartData(loading = true) {
      this.loadingChart = loading
      const data = await this.getChartData(this.handlerGetChartParams())
      this.chartSeries = data.series.map(item => ({ ...item, stack: 'event-alram' }))
      await this.$nextTick()
      this.loadingChart = false
    },
    async handleActivated(routeName) {
      this.firstLoading = true
      const values = []
      Object.keys(this.backDisplayParamsMap).forEach((key) => {
        const params = { ...this.$route.params, ...this.$route.query }
        if (params[key]) {
          let name = this.backDisplayParamsMap[key].statusName || params[key]
          if (key === 'level') {
            name = this.levelObj[params[key]]
          }
          // 策略跳转
          if (key === 'strategyId') {
            name = params.strategyName
          }
          // 自定义搜索条件
          if (key === 'query') {
            values.push({
              id: params[key],
              name: params[key]
            })
          } else {
            values.push({
              id: this.backDisplayParamsMap[key].id,
              name: this.backDisplayParamsMap[key].name,
              values: [{
                id: params[key],
                name
              }]
            })
          }
        }
      })
      if (values.length === 0) {
        this.handleConditionCache(routeName)
      } else {
        // 从链接进入到事件中心 时间设为近30天
        const end = moment().format('YYYY-MM-DD HH:mm:ss')
        const start = moment(end).add(-30, 'd')
          .format('YYYY-MM-DD HH:mm:ss')
        this.search.date = [start, end]
        this.search.value = values
      }
      // await this.handleGetEventList()
      // this.firstLoading = false
    },
    async handleConditionCache(fromRoute) {
      this.$nextTick().then(async () => {
        if (fromRoute !== 'event-center-detail' && fromRoute !== 'home') {
          this.handleInitActivatedData()
        } else {
          await this.handleGetEventList()
          this.firstLoading = false
        }
      })
    },
    // 处理从首页图表跳转到事件中心的时间路由参数
    handleHomeDateParam(params) {
      if (params.metricId) {
        const dateNow = moment().format('YYYY-MM-DD HH:mm:ss')
        const lastDate = moment(dateNow).add(`-${params.date}`, 'd')
          .format('YYYY-MM-DD HH:mm:ss')
        this.search.routerDateParams = [lastDate, dateNow]
        this.search.date = this.search.routerDateParams
        return
      }
      if (params.beginTime && params.endTime) {
        this.search.routerDateParams = [params.beginTime, params.endTime]
        this.search.date = this.search.routerDateParams
      }
      this.search.routerDateParams = null
    },
    // 时间控件语义时间查询事件
    handleShortcutClick() {
      this.$refs.searchDate.visible = false
      this.search.date = this.$refs.searchDate.publicStringValue
      this.search.mockDate = this.$refs.searchDate.publicStringValue
      this.table.page = 1
      this.handleGetEventList()
    },
    handleOpenChange(v) {
      if (v) {
        this.search.mockDate = this.search.date
      } else if (this.search.mockDate !== this.search.date) {
        this.search.mockDate = this.search.date
        this.handleGetEventList()
      }
    },
    handlePickSuccess() {
      this.search.mockDate = this.search.date
      this.table.page = 1
      this.handleGetEventList()
    },
    handleTagClick(item) {
      if (this.tag.active === item.id) return
      this.tag.active = item.id
      this.table.page = 1
      this.handleGetEventList()
    },
    async handleShowChart() {
      this.search.showChart = !this.search.showChart
      // 搜索条件变更时查询趋势图
      if (this.search.showChart && this.chart.refresh) {
        await this.$nextTick()
        this.chart.width = this.$refs.chartWrap.clientWidth
        this.chart.refresh = false
        this.handleGetChartData()
      }
    },
    handleRowCollapse(item, index) {
      if (index === this.table.collapseIndex) {
        item.collapse = !item.collapse
      } else {
        if (this.collaspseItem) {
          this.collaspseItem.collapse = false
        }
        item.collapse = !item.collapse
        this.table.collapseIndex = index
      }
    },
    handleScroll() {
      const { scrollHeight } = this.$el
      const { scrollTop } = this.$el
      const { clientHeight } = this.$el
      if (clientHeight + scrollTop >= scrollHeight && !this.scroll.show) {
        this.scroll.show = true
        this.$el.scrollTo(0, scrollTop - 100)
        setTimeout(() => {
          this.scroll.show = false
          // this.table.data.push(...getData(5))
        }, 2000)
      }
    },
    handleGotoDetail(id) {
      this.$router.push({
        name: 'event-center-detail',
        params: {
          id
        }
      })
    },
    handleRemoveScollListener() {
      this.$el.removeEventListener('scroll', this.handleScroll, { passive: true })
    },
    handleAddScollListener() {
      this.$el.addEventListener('scroll', this.handleScroll, { passive: true })
    },
    handleChartResize() {
      const width = this.$refs.chartWrap.clientWidth
      if (width > 0) {
        this.chart.width = width
      }
    },
    handlePageChange(v) {
      this.table.page = v
      this.handleGetEventList(true)
    },
    handleLimitChange(v) {
      this.table.page = 1
      this.table.pageSize = v
      this.handleSetCommonPageSize(v)
      this.handleGetEventList()
    },
    handleCheckChange(v) {
      this.tag.checked = v
      this.table.page = 1
      this.handleGetEventList()
    },
    handleMouseOver(item, e) {
      if (!item.ackMessage) return
      if (!this.popoverInstance) {
        this.popoverInstance = this.$bkPopover(e.target, {
          content: item.ackMessage,
          arrow: true,
          lazy: false
        })
      } else {
        this.popoverInstance.popperInstance.reference = e.target
        this.popoverInstance.reference = e.target
        this.popoverInstance.setContent(item.ackMessage)
        this.popoverInstance.popperInstance.update()
      }
      this.popoverInstance.show(100)
    },
    handleMouseLeave() {
      this.popoverInstance && this.popoverInstance.hide(0)
      this.popoverInstance && this.popoverInstance.destroy()
      this.popoverInstance = null
    },
    handleGetCommonParams() {
      const bizIds = [this.$store.getters.bizId]
      const { date } = this.search
      const RANGE_SEPARATOR = ' -- '
      const timeRange = date.length === 2 && this.$refs.searchDate
        ? (this.$refs.searchDate.formatDate(new Date(date[0])) || this.search.date[0])
        + RANGE_SEPARATOR
        + (this.$refs.searchDate.formatDate(new Date(date[1])) || this.search.date[1])
        : this.search.date[0] + RANGE_SEPARATOR + this.search.date[1]
      const receiver = this.tag.checked ? this.$store.getters.userName : ''
      const status = this.tag.active === 'ALL' ? '' : this.tag.active
      const conditions = this.handleGetCondition()
      return {
        bizIds,
        timeRange,
        receiver,
        status,
        conditions
      }
    },
    // 变化趋势图参数
    handlerGetChartParams() {
      const params = this.handleGetCommonParams()
      return {
        bk_biz_ids: params.bizIds,
        time_range: params.timeRange,
        receiver: params.receiver,
        // 'status': params.status,
        conditions: params.conditions
      }
    },
    handleGetParams(isExport = false) {
      const params = this.handleGetCommonParams()
      const ret = {
        bk_biz_ids: params.bizIds,
        time_range: params.timeRange,
        receiver: params.receiver,
        status: params.status === 'ALL' ? '' : params.status,
        conditions: params.conditions,
        page_size: this.table.pageSize,
        page: this.table.page,
        export: isExport
      }
      if (this.sort.active !== 0) {
        ret.order =  `${this.sort.list[this.sort.active] === 'desc' ? '-' : ''}${this.sort.name}`
      }
      return ret
    },
    handleGetCondition() {
      const { value } = this.search
      if (!value || value.length < 1) {
        return []
      }
      return this.search.value.map((item) => {
        if (!item.values && item.id === item.name) {
          return { key: 'query', value: item.id }
        }
        return {
          key: item.id,
          value: item.values.map(set => set.id)
        }
      })
    },
    handleSortChange(name) {
      if (this.sort.name !== name) {
        this.sort.active = 0
      }
      this.sort.name = name
      this.sort.active = (this.sort.active + 1) % 3
      this.handleGetEventList()
    },
    handleAllCheckedChange(v) {
      this.table.data.forEach(item => item.eventStatus === 'ABNORMAL' && !item.isAck && (item.checked = v))
    },
    handleShowConfirm() {
      this.confirm.show = true
    },
    handleBatch() {
      const params = {
        ids: this.checkedIds,
        message: this.confirm.content
      }
      this.batchLoading = true
      ackEvent(params).then(() => {
        this.$bkMessage({ theme: 'success', message: this.$t('告警确认成功') })
        // eslint-disable-next-line vue/max-len
        this.table.data.forEach(item => item.eventStatus === 'ABNORMAL' && this.checkedIds.includes(item.id) && (item.isAck = true, item.ackMessage = this.confirm.content))
        this.table.data.forEach(item => item.eventStatus === 'ABNORMAL' && (item.checked = false))
      })
        .finally(() => this.batchLoading = false)
    },
    handleGotoMore(topoInfo) {
      const typeMap = {
        // 跳转主机详情
        host: () => {
          this.$router.push({
            name: 'performance-detail',
            params: {
              title: topoInfo.ip,
              id: `${topoInfo.ip}-${topoInfo.bk_cloud_id === undefined ? 0 : topoInfo.bk_cloud_id}`
            }
          })
        },
        // 跳转数据检索
        bkdata: () => {
          const targets = topoInfo.query_configs.map(config => ({
            data: config
          }))
          window.open(`${location.href.replace(location.hash, '#/data-retrieval')}?targets=${JSON.stringify(targets)}`)
        },
        // 跳转日志检索
        log_search: () => {
          const retrieveParams =  { // 检索参数
            keyword: topoInfo.query_string, // 搜索关键字
            addition: topoInfo.agg_condition?.map(set => ({
              field: set.key,
              operator: set.method,
              value: (set.value || []).join(',')
            })) || []
          }
          // eslint-disable-next-line vue/max-len
          window.open(`${this.$store.getters.bkLogSearchUrl}#/retrieve/${topoInfo.index_set_id}?bizId=${this.$store.getters.bizId}&retrieveParams=${encodeURI(JSON.stringify(retrieveParams))}`)
        },
        custom_event: () => {
          const id = topoInfo.bk_event_group_id
          window.open(`${location.href.replace(location.hash, '#/custom-escalation-detail/event/') + id}`)
        }
      }
      typeMap[topoInfo.type] && typeMap[topoInfo.type]()
    }
  }
}
</script>
<style lang="scss" scoped>
    @import "../../static/css/common.scss";
    $statusColors: $deadlyAlarmColor $warningAlarmColor $remindAlarmColor;

    .event-center {
      font-size: 12px;
      color: $defaultFontColor;
      &.event-loading {
        min-height: calc(100vh - 80px);
      }
      &-tag {
        display: flex;
        align-items: center;
        padding-bottom: 16px;
        border-bottom: 1px solid $defaultBorderColor;
        margin-bottom: 16px;
        .event-tag {
          border: 1px solid #c4c6cc;
          height: 32px;
          box-sizing: border-box;
          border-radius: 32px;
          font-size: 14px;
          display: flex;
          align-items: center;
          padding: 0 10px;
          margin-right: 10px;
          cursor: pointer;
          &.tag-active {
            background: #3a84ff;
            color: #fff;
            border-color: #3a84ff;
          }
          &-name {
            margin-right: 6px;
          }
          &-num {
            background: $deadlyAlarmColor;
            border-radius: 16px;
            font-size: 12px;
            color: #fff;
            height: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 16px;
            padding: 0 6px;
            &.status-default {
              background: #dadada;
              color: #63656e;
            }
            &.num-active {
              background: #fff;
              color: #3a84ff;
              border-color: #fff;
            }
          }
        }
        .export-btn {
          margin-left: 10px;
        }
      }
      &-search {
        display: flex;
        align-items: center;
        margin-bottom: 18px;
        .search-input {
          min-width: 410px;
          max-width: calc(100vw - 600px);
          background: #fff;
        }
        .search-date {
          margin-left: auto;
          width: 352px;
        }
        .search-icon {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #c4c6cc;
          border-radius: 2px;
          font-size: 18px;
          margin-left: 10px;
          cursor: pointer;
          &.active-icon {
            background: #979ba5;
            border-color: #979ba5;
            color: #fff;
          }
        }
      }
      &-chart {
        display: flex;
        height: 312px;
        border: 1px solid $defaultBorderColor;
        border-radius: 2px;
        box-shadow: 0px 1px 4px 0px rgba(99,101,110,.06);
        margin-bottom: 20px;
      }
      &-table {
        display: flex;
        flex-direction: column;
        width: 100%;
        // height: 100%;
        border: 1px solid $defaultBorderColor;
        border-bottom: 0;
        border-radius: 2px;
        overflow: auto;
        .table-row {
          min-width: 1200px;
          flex: 0 0 42px;
          box-sizing: border-box;
          display: flex;
          align-items: center;
          background: #fff;
          // flex-wrap: wrap;
          &:hover {
            background-color: #f0f1f5;
          }
          &-col {
            display: flex;
            flex: 1;
            align-items: center;
            position: relative;
            border-bottom: 1px solid $defaultBorderColor;
            height: 42px;
            &.head-col {
              font-weight: 700;
              &.sort {
                cursor: pointer;
                &:hover {
                  background-color: #f0f1f5;
                }
              }
            }
            &.col-mark {
              flex: 0 0 54px;
              padding-left: 16px;
              .icon-monitor {
                font-size: 16px;
                color: #979ba5;
                cursor: pointer;
                transition: transform .2s linear;
                &.collapse-icon {
                  transform: rotate(-90deg)
                }
              }
            }
            &.col-tips {
              flex: 0 0 26px;
              .event-status {
                width: 4px;
                height: 14px;
                border-radius: 2px;

                @for $i from 1 through length($statusColors) {
                  &.status-#{$i} {
                    background: nth($statusColors, $i);
                  }
                }
              }
            }
            &.col-checkbox {
              flex: 0 0 48px;
            }
            &.col-id {
              flex: 0 0 100px;
              .event-id {
                color: #3a84ff;
                cursor: pointer;
              }
            }
            .col-times-content {
              width: 48px;
              text-align: right;
            }
            &.col-times,
            &.col-continue {
              flex: 0 0 90px;
            }
            &.col-bussiness,
            &.col-status {
              flex: 0 0 130px;
            }
            &.col-notice {
              flex: 0 0 100px;
              &.notice-success {
                color: #c4c6cc;
              }
            }
            &.col-origin {
              .col-origin-content {
                padding-right: 10px;

                @include box-ellipsis;
              }
            }
            &.col-date {
              flex: 0 0 180px;
            }
            &.col-content {
              flex-grow: 2;
            }
            &.col-content-line-feed,
            &.col-content-line-topo {
              flex-direction: column;
              align-items: flex-start;
              justify-content: center;
              .line-feed-content,
              .line-topo-content {
                padding-right: 10px;
                vertical-align: text-top;

                @include box-ellipsis;
              }
            }
            &.col-content-line-topo {
              .line-topo-content {
                .more {
                  margin-left: 5px;
                }
              }
              .link {
                color: #3a84ff;
                cursor: pointer;
              }
            }
            &.no-border {
              border-bottom-color: transparent;
            }
            .event-operate {
              color: #c4c6cc;
              &.operate-recovered {
                color: #2dcb56;
              }
              &.operate-abnormal {
                color: $deadlyAlarmColor;
              }
              &.operate-closed {
                color: #c4c6cc;
              }
            }
            .event-checked {
              color: #c4c6cc;
              cursor: default;
            }
            .event-mark {
              color: #979ba5;
              position: absolute;
              top: -8px;
              width: 126px;
              line-height: 16px;
              background: #fbfbfb;
            }
            .event-tip {
              width: 100%;
              color: #c4c6cc;
              text-align: center
            }
          }
          > .table-row-col {
            height: 54px;
          }
          &.analyze-row {
            flex-basis: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            .table-row-col {
              height: 48px;
            }
          }
        }
        .table-head {
          min-width: 1200px;
          background: #fafbfd;
          color: #313238;
          flex: 0 0 42px;
          box-sizing: border-box;
          display: flex;
          align-items: center;
          flex-wrap: wrap;
        }
        .child-row {
          background: #fbfbfb;
        }
        .child-wrapper {
          min-width: 100%;
          background: #fbfbfb;
          &-collaspe {
            position: relative;
            &::after {
              content: " ";
              height: 1px;
              width: 100%;
              position: absolute;
              background: #fbfbfb;
              box-shadow: 0px 0px 6px 0px rgba(0,0,0,.2);
            }
            &::before {
              top: -1px;

              /* stylelint-disable-next-line scss/at-extend-no-missing-placeholder */
              @extend ::after;
            }
          }
        }
        .empty-row {
          display: flex;
          height: 48px;
          align-items: center;
          justify-content: center;
          border-bottom: 1px solid $defaultBorderColor;
          color: #c4c6cc;
          margin-left: 54px;
        }
        .table-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border-bottom: 1px solid $defaultBorderColor;
          min-height: 400px;
          background-color: #fff;
          .icon-empty {
            font-size: 65px;
            color: #c3cdd7;
          }
        }
      }
      &-pagination {
        margin-bottom: 10px;
        padding: 15px;
        background: #fff;
        border: 1px solid $defaultBorderColor;
        border-top: 0;
      }
      &-footer {
        margin-top: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        height: 32px;
        .footer-total {
          position: absolute;
          left: 0;
          line-height: 16px;
        }
        .footer-loading {
          background: #ebedf0;
          height: 32px;
          width: 160px;
          border-radius: 2px;
          display: flex;
          align-items: center;
          color: #979ba5;
          padding-left: 22px;
          z-index: 100;
          img {
            width: 14px;
            margin-right: 6px;
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
