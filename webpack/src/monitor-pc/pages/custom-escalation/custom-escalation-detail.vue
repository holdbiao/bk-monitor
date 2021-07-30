<template>
  <div class="custom-detail" v-bkloading="{ isLoading: loading }">
    <!-- 详情信息，名字可修改 -->
    <div class="detail-information">
      <div class="detail-information-title">{{ $t('基本信息') }}</div>
      <div class="detail-information-row">
        <span class="row-label">{{ $t('数据ID：') }}</span>
        <span class="row-content">{{ detailData.bk_data_id }}</span>
      </div>
      <div class="detail-information-row">
        <span class="row-label">{{ $t('Token：') }}</span>
        <span class="row-content">{{ detailData.access_token }}</span>
      </div>
      <div class="detail-information-row">
        <span class="row-label">{{ $t('名称：') }}</span>
        <div v-if="!isShowEditName" style="display: flex">
          <span class="row-content">{{ detailData.name }}</span>
          <i v-if="detailData.name" class="icon-monitor icon-bianji edit-name" @click="handleShowEdit"></i>
        </div>
        <bk-input v-else v-model="copyName" style="width: 240px" @blur="handleEditName" ref="nameInput"></bk-input>
      </div>
      <div class="detail-information-row last-row">
        <span class="row-label">{{ $t('监控对象：') }}</span>
        <span class="row-content">{{ scenario }}</span>
      </div>
    </div>
    <!-- 自定义事件展示 -->
    <template v-if="type === 'customEvent'">
      <!-- 拉取的事件列表 -->
      <div class="detail-information detail-list">
        <div class="list-header">
          <div class="list-header-title">{{ $t('事件列表') }}</div>
          <bk-select class="list-header-refresh" v-model="refreshList.value" :clearable="false" @change="handleRefreshChange">
            <bk-option v-for="(opt, index) in refreshList.list" :key="index" :name="opt.name" :id="opt.value"></bk-option>
          </bk-select>
          <bk-select :popover-min-width="110" class="list-header-date" v-model="shortcuts.value" :clearable="false" @change="handleTimeChange">
            <bk-option v-for="(opt, index) in shortcuts.list" :key="index" :name="opt.name" :id="opt.value"></bk-option>
          </bk-select>
        </div>
        <bk-table :data="eventData" :outer-border="false">
          <bk-table-column :label="$t('事件名称')" prop="custom_event_name" min-width="100"></bk-table-column>
          <bk-table-column :label="$t('目标数量')" min-width="50">
            <template #default="{ row }">
              <div class="num-set">{{ row.target_count }}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('事件数量')" min-width="50">
            <template #default="{ row }">
              <div class="num-set"> {{ row.event_count }}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('关联策略')" min-width="50">
            <template #default="{ row }">
              <span :class="['num-set', { 'col-btn': row.related_strategies.length > 0 }]" @click="handleGotoStrategy(row)">{{ row.related_strategies.length }}</span>
              <!-- <div class="num-set"> {{ row.related_strategies.length }}</div> -->
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('最近变更时间')" min-width="100">
            <template #default="{ row }">
              <span>{{ row.last_change_time || '--' }}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作')" min-width="80">
            <template #default="{ row }">
              <bk-button ext-cls="col-operator" theme="primary" text
                         @click="handleOpenSideslider(row.last_event_content, row.custom_event_name)"> {{ $t('查看原始数据') }} </bk-button>
              <bk-button
                ext-cls="col-operator"
                theme="primary" text
                @click="handleAddStrategy(row)"> {{ $t('添加策略') }} </bk-button>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <!-- 查看原始数据侧滑栏 -->
      <bk-sideslider :is-show.sync="sideslider.isShow" :quick-close="true" :width="656">
        <div slot="header" class="sideslider-title">
          <span>{{ sideslider.title + $t('-原始数据') }}</span>
          <span class="title-explain">{{ $t('（仅支持查看当前事件中最近一条的原始数据信息）') }}</span>
        </div>
        <div slot="content">
          <monaco-editor
            :language="'json'"
            :value="JSON.stringify(sideslider.data, null , '\t')"
            :options="{ readOnly: true }"
            style="height: calc(100vh - 61px)">
          </monaco-editor>
        </div>
      </bk-sideslider>
    </template>
    <!-- 自定义指标展示 -->
    <template v-else>
      <div class="detail-information detail-list">
        <div class="list-header mb16">
          <div class="list-header-title">
            <span>{{ $t('时序列表') }}</span>
            <span class="title-desc">{{ `（${$t('包括')}${metricNum}${$t('个指标')}，${dimensionNum}${$t('个维度')}）` }}</span>
          </div>
        </div>
        <div class="button-control-wrap">
          <div class="button-control-left">
            <group-select
              :list="groupSelectList"
              :disabled="!selectionLeng"
              v-model="batchGroupValue"
              @change="handleBatchValueChange"
              @list-change="list => groupSelectList = list">
              <bk-button
                icon-right="icon-angle-down"
                :disabled="!selectionLeng">{{$t('批量分组')}}<span v-show="selectionLeng">{{`(${selectionLeng})`}}</span></bk-button>
            </group-select>
            <monitor-import
              style="margin-right: 0; margin-left: 10px;"
              accept="application/json"
              :return-text="true"
              :base64="false"
              @change="handleImportMetric">
              <bk-button>{{$t('导入')}}</bk-button>
            </monitor-import>
            <monitor-export @click="handleExportMetric">
              <bk-button>{{$t('导出')}}</bk-button>
            </monitor-export>
          </div>
          <div class="list-header-time">{{ $t('数据时间：') }}{{ detailData.last_time || $t('暂时无数据') }}</div>
          <div class="list-header-button">{{ $t('数据预览') }}</div>
          <bk-switcher v-model="isShowData" size="small" theme="primary" @change="handleShowDataChange"></bk-switcher>
        </div>
        <!-- 指标/维度表 -->
        <div class="table-box">
          <div class="left-table" :class="{ 'left-active': isShowData }">
            <bk-table :data="metricTable" :outer-border="true">
              <bk-table-column
                :render-header="renderSelectionHeader"
                width="80"
                align="center">
                <template #default="{ row }">
                  <bk-checkbox
                    v-model="row.selection"
                    :disabled="row.monitor_type === 'dimension'"
                    @change="handleRowCheck($event, row)">
                  </bk-checkbox>
                </template>
              </bk-table-column>
              <!-- 指标/维度 -->
              <bk-table-column
                :render-header="renderMetricHeader"
                :label="$t('指标/维度')"
                width="150">
                <template slot-scope="scope">
                  {{ scope.row.monitor_type === 'metric' ? $t('指标') : $t('维度') }}
                </template>
              </bk-table-column>
              <!-- 分组 -->
              <bk-table-column
                :render-header="renderGroupHeader"
                :label="$t('分组')"
                min-width="160">
                <template slot-scope="scope">
                  <div style="display: flex;">
                    <template v-if="scope.row.monitor_type === 'metric'">
                      <group-select
                        style="margin-left: -8px;"
                        v-model="scope.row.label"
                        :list="groupSelectList"
                        @list-change="list => groupSelectList = list">
                        <div class="table-group-select">{{scope.row.label || $t('未分组')}}<i class="icon-monitor icon-arrow-down"></i></div>
                      </group-select>
                    </template>
                    <template v-else>--</template>
                  </div>
                </template>
              </bk-table-column>
              <!-- 英文名 -->
              <bk-table-column :label="$t('英文名')" min-width="100" prop="name">
                <template slot-scope="scope">
                  <div class="overflow-tips" v-bk-overflow-tips>{{ scope.row.name }}</div>
                </template>
              </bk-table-column>
              <!-- 别名 -->
              <bk-table-column :label="$t('别名')" min-width="100" prop="description">
                <template slot-scope="scope">
                  <div class="cell-margin name">
                    <bk-input v-model="scope.row.description" size="small"
                              :placeholder="scope.row.monitor_type === 'metric' ? $t('输入指标别名') : $t('输入维度别名')"
                              @blur="handleCheckDescName(scope.row, scope.$index)" :class="{ 'input-err': scope.row.descReValue }">
                    </bk-input>
                    <bk-popover class="change-name" placemnet="top-start" trigger="mouseenter" :tippy-options="{ a11y: false }">
                      <i v-if="scope.row.descReValue" class="icon-monitor icon-remind"></i>
                      <div slot="content">
                        <template v-if="scope.row.descReValue">{{ $t('别名有冲突') }}</template>
                      </div>
                    </bk-popover>
                  </div>
                </template>
              </bk-table-column>
              <!-- 类型 -->
              <bk-table-column :label="$t('类型')" width="120" prop="type"></bk-table-column>
              <!-- 单位 -->
              <bk-table-column :label="$t('单位')" width="170" prop="unit">
                <template slot-scope="scope">
                  <div class="cell-margin" v-if="unit.value && unit.index === scope.$index && scope.row.monitor_type === 'metric'" @mouseleave="handleMouseLeave">
                    <bk-select v-model="scope.row.unit" :clearable="false" :popover-width="180" @toggle="handleToggleChange">
                      <bk-option-group
                        v-for="(group, index) in unitList"
                        :name="group.name"
                        :key="index">
                        <bk-option v-for="option in group.formats"
                                   :key="option.id"
                                   :id="option.id"
                                   :name="option.name">
                        </bk-option>
                      </bk-option-group>
                    </bk-select>
                  </div>
                  <div v-else class="cell-span" @mouseenter="handleMouseenter(scope.$index)">
                    {{ scope.row.monitor_type === 'metric' ? handleFindUnitName(scope.row.unit) : '--' }}
                  </div>
                </template>
              </bk-table-column>
              <!-- 空数据 -->
              <div slot="empty" class="empty">
                <i class="icon-monitor icon-remind empty-icon"></i>
                <div>{{ $t('暂无指标/维度') }}</div>
              </div>
            </bk-table>
          </div>
          <!-- 数据预览 -->
          <div class="right-data" v-show="isShowData">
            <ul class="ul-head">
              <li class="host-type">{{ $t('数据') }}</li>
            </ul>
            <template v-if="metricTable.length">
              <div v-bkloading="{ isLoading: dataLoading }">
                <div class="data-preview" v-for="(item, index) in metricTable" :key="index">
                  {{ metricValue[item.name] }}
                </div>
              </div>
            </template>
            <div v-else class="no-data-preview"></div>
          </div>
        </div>
        <bk-pagination
          v-show="metricTable.length"
          class="list-pagination"
          align="right"
          size="small"
          show-total-count
          pagination-able
          @change="handlePageChange"
          @limit-change="handleLimitChange"
          :current="pagination.page"
          :limit="pagination.pageSize"
          :count="pagination.total"
          :limit-list="pagination.pageList">
        </bk-pagination>
      </div>
    </template>
    <!-- 右边展开收起按钮 -->
    <div class="right-button" @click="isShowRightWindow = !isShowRightWindow" :class="{ 'active-buttom': isShowRightWindow }">
      <i v-if="isShowRightWindow" class="icon-monitor icon-double-up icon"></i>
      <i v-else class="icon-monitor icon-double-down icon"></i>
    </div>
    <!-- 展开内容 -->
    <div class="right-window" :class="{ 'active': isShowRightWindow }">
      <div class="right-window-title">{{ type === 'customEvent' ? $t('自定义事件帮助') : $t('自定义指标帮助') }}</div>
      <div class="right-window-content">
        <div class="content-title">{{ $t('注意事项') }}</div>
        <span>{{ $t('API频率限制 1000/min，单次上报Body最大为500KB') }}</span>
        <div class="content-title content-interval">{{ $t('使用方法') }}</div>
        <div class="content-row">
          <span>{{ $t('不同云区域Proxy信息') }}</span>
          <div class="content-example">
            <div v-for="(item, index) in proxyInfo" :key="index">
              {{ $t('云区域') }} {{ item.bkCloudId }} <span style="margin-left: 10px">{{ item.ip }}</span>
            </div>
          </div>
        </div>
        <div class="content-row">
          <span>{{ $t('命令行直接调用样例') }}</span>
          <div class="content-example">curl -X POST http://${PROXY_IP}:10205/v2/push/ -d '${REPORT_DATA}'</div>
        </div>
        <div class="content-row">
          <span>{{ $t('数据上报格式样例') }}</span>
          <pre class="content-example">{{ preData }}</pre>
          <div class="content-copy" @click="handleCopyData"> {{ $t('复制') }} </div>
          <textarea ref="textCopy" class="copy-textarea"></textarea>
        </div>
      </div>
    </div>
    <bk-button
      v-if="type === 'customTimeSeries'"
      @click="authority.MANAGE_CUSTOM_METRIC ? handleSubmit() : handleShowAuthorityDetail(customAuthMap.MANAGE_CUSTOM_METRIC) "
      v-authority="{ active: !authority.MANAGE_CUSTOM_METRIC }"
      theme="primary"
      class="mc-btn-add">
      {{ $t('提交') }}
    </bk-button>
  </div>
</template>

<script lang="ts">
import { Component, Mixins, Ref, Watch } from 'vue-property-decorator'
import moment from 'moment'
import MonacoEditor from '../../components/editors/monaco-editor.vue'
import { ISideslider, IParams, IEditParams,
  IDetailData, IShortcuts, IRefreshList } from '../../types/custom-escalation/custom-escalation-detail'
import GroupSelect from './group-select.vue'
import MonitorExport from '../../components/monitor-export/monitor-export.vue'
import MonitorImport from '../../components/monitor-import/monitor-import.vue'
import * as customAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
import { CreateElement } from 'vue'
import ColumnCheck from '../performance/column-check/column-check.vue'
import TableFiter from '../../components/table-filter/table-filter-new.vue'

@Component({
  components: {
    MonacoEditor,
    MonitorExport,
    MonitorImport,
    GroupSelect
  }
})
export default class customEscalationDetail extends Mixins(authorityMixinCreate(customAuth))  {
  @Ref('nameInput') readonly nameInput!: HTMLInputElement
  @Ref('textCopy') readonly textCopy!: HTMLTextAreaElement
  private customAuthMap = customAuth
  private loading = false
  private isCreat = '' // 是否从创建过来
  // private type = 'customEvent' // 展示类型：customEvent 自定义事件 customTimeSeries 自定义指标
  private copyName = '' // 修改的名字
  private isShowEditName = false // 是否显示名字编辑框
  private isShowRightWindow = false // 是否显示右侧帮助栏
  private scenario = '' // 分类
  private proxyInfo = [] // 云区域分类数据
  private preData = '' // 数据上报格式样例
  private timer = null // 定时器
  //  详情数据
  private detailData: IDetailData = {
    bk_data_id: '',
    access_token: '',
    name: '',
    scenario: '',
    scenario_display: []
  }

  //  侧滑栏内容数据 事件数据
  private sideslider: ISideslider = {
    isShow: false,
    title: '',
    data: {} //  原始数据
  }

  //  事件列表数据 事件数据
  private eventData = []

  //  指标维度数据 时序数据
  private metricData = []
  private isShowData = true // 是否展示数据预览 时序数据
  private unitList = [] // 单位list
  private unit = {
    value: true,
    index: -1,
    toggle: false
  }

  //  时间选择器选择项
  private shortcuts: IShortcuts = {
    list: [],
    value: 1
  }
  private refreshList: IRefreshList
  private pagination = {
    page: 1,
    pageSize: 20,
    total: 100,
    pageList: [10, 20, 50, 100]
  }
  private tableId = ''
  private metricValue = {}
  private dataLoading = false

  private batchGroupValue = ''

  private groupSelectList: any = [
    {
      id: '',
      name: '未分组'
    }
  ]

  private allCheckValue: 0 | 1 | 2 = 0  // 0: 取消全选 1: 半选 2: 全选
  private metricCheckList: any = []
  private groupFilterList: string[] = []
  private metricFilterList: string[] = []
  //  指标数量
  get metricNum() {
    return this.metricData.filter(item => item.monitor_type === 'metric').length
  }

  //  维度数量
  get dimensionNum() {
    return this.metricData.filter(item => item.monitor_type === 'dimension').length
  }

  //  别名列表
  get descNameList() {
    return this.metricData.map(item => item.description)
  }
  get metricTable() {
    const leng1 = this.groupFilterList.length
    const leng2 = this.metricFilterList.length
    const fiterList = this.metricData.filter(item => (leng1
      ? (this.groupFilterList.includes(item.label) && item.monitor_type === 'metric')
      : true))
      .filter(item => (leng2 ? this.metricFilterList.includes(item.monitor_type) : true))
    this.changePageCount(fiterList.length)
    this.handleGroupList(fiterList)
    return fiterList.slice(
      this.pagination.pageSize * (this.pagination.page - 1),
      this.pagination.pageSize * this.pagination.page
    )
  }

  get selectionLeng() {
    const selectionlist = this.metricTable.filter(item => item.selection)
    return selectionlist.length
  }

  get type() {
    return this.$route.name === 'custom-detail-event' ? 'customEvent' : 'customTimeSeries'
  }
  @Watch('metricTable')
  async handleMetricTableChange(v) {
    if (this.type === 'customTimeSeries'
    && this.isShowData
    && v.some(item =>  this.metricValue[item.name] === undefined)) {
      this.dataLoading = true
      const fieldList = v.map(set => set.name) || []
      const data = await this.$store.dispatch(
        'custom-escalation/getCustomTimeSeriesLatestDataByFields'
        , {
          result_table_id: this.tableId,
          fields_list: fieldList
        }
      )
      // eslint-disable-next-line camelcase
      this.metricValue = data?.fields_value || {}
      this.dataLoading = false
    }
  }
  created() {
    this.getDetailData()
    this.shortcuts.list = [
      {
        value: 1,
        name: this.$tc('近1小时')
      },
      {
        value: 12,
        name: this.$tc('近12小时')
      },
      {
        value: 24,
        name: this.$tc('近1天')
      },
      {
        value: 168,
        name: this.$tc('近7天')
      }
    ]
    this.refreshList = {
      list: [
        {
          value: 0,
          name: this.$tc('不刷新')
        },
        {
          value: 60,
          name: this.$tc('每一分钟')
        },
        {
          value: 300,
          name: this.$tc('每五分钟')
        }
      ],
      value: 0
    }
  }

  beforeDestroy() {
    clearTimeout(this.timer)
    this.timer = null
  }

  renderGroupHeader(h: CreateElement) {
    return h(TableFiter, {
      props: {
        title: this.$t('分组'),
        value: this.groupFilterList,
        list: this.groupSelectList
      },
      on: {
        change: (v) => {
          setTimeout(() => {
            this.pagination.page = 1
            this.groupFilterList = v
            this.updateAllSelection()
          }, 300)
        }
      }
    })
  }

  renderMetricHeader(h: CreateElement) {
    return h(TableFiter, {
      props: {
        title: this.$t('指标/维度'),
        value: this.metricFilterList,
        list: [
          { id: 'metric', name: this.$t('指标') },
          { id: 'dimension', name: this.$t('维度') }
        ]
      },
      on: {
        change: (v) => {
          setTimeout(() => {
            this.pagination.page = 1
            this.metricFilterList = v
            this.updateAllSelection()
          }, 300)
        }
      }
    })
  }

  renderSelectionHeader(h: CreateElement) {
    return h(ColumnCheck, {
      props: {
        list: [],
        value: this.allCheckValue,
        defaultType: 'current'
      },
      on: {
        change: this.handleCheckChange
      }
    })
  }

  changePageCount(count: number) {
    this.pagination.total = count
  }

  handleGroupList(list) {
    list.forEach((item) => {
      const res = this.groupSelectList.find(g => item.label == g.id)
      if (!res && item.monitor_type === 'metric' && item.label) {
        this.groupSelectList.push({
          id: item.label,
          name: item.label
        })
      }
    })
  }

  handleRowCheck() {
    this.updateCheckValue()
  }

  updateAllSelection(v = false) {
    this.metricTable.forEach(item => item.monitor_type === 'metric' && (item.selection = v))
    this.updateCheckValue()
  }

  handleCheckChange({ value }) {
    this.updateAllSelection(value === 2)
    this.updateCheckValue()
  }

  updateCheckValue() {
    const metricLiist = this.metricTable.filter(item => item.monitor_type === 'metric')
    const checkedLeng = metricLiist.filter(item => item.selection).length
    const allLeng = metricLiist.length
    this.allCheckValue = checkedLeng > 0
      ? (checkedLeng < allLeng ? 1 : 2)
      : 0
  }

  handleBatchValueChange(v) {
    if (v === '') return
    this.metricTable.forEach((item) => {
      item.selection && (item.label = v)
    })
    this.$nextTick(() => {
      this.batchGroupValue = ''
      this.updateAllSelection()
    })
  }
  handleShowDataChange(v) {
    if (v && !this.dataLoading) {
      this.handleMetricTableChange(this.metricData)
    }
  }
  handlePageChange(v) {
    this.updateAllSelection()
    this.pagination.page = v
  }
  handleLimitChange(v) {
    this.updateAllSelection()
    this.pagination.page = 1
    this.pagination.pageSize = v
  }
  //  从新建和列表页进来会去获取最近 1小时 拉取的事件
  getTimeParams() {
    const dateNow = moment().format('YYYY-MM-DD HH:mm:ss')
    const lastDate = moment(dateNow).add(-this.shortcuts.value, 'h')
      .format('YYYY-MM-DD HH:mm:ss')
    return `${lastDate} -- ${dateNow}`
  }

  //  获取详情
  async getDetailData() {
    this.loading = true
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
    // this.type = this.$route.params.type === 'customEvent' ? 'customEvent' : 'customTimeSeries'
    this.isShowRightWindow = this.$route.params.isCreat === 'creat' // 在第一次进来的时候展示右侧帮助栏
    const promiseItem: Promise<any>[] = [this.$store.dispatch('custom-escalation/getProxyInfo')]
    let title = ''
    if (this.type === 'customEvent') {
      const params: IParams = { // 自定义事件初次进入会请求最近1小时的数据
        time_range: this.getTimeParams(),
        bk_event_group_id: this.$route.params.id
      }
      promiseItem.push(this.$store.dispatch('custom-escalation/getCustomEventDetail', params))
    } else {
      promiseItem.push(this.$store.dispatch(
        'custom-escalation/getCustomTimeSeriesDetail'
        , { time_series_group_id: this.$route.params.id }
      ))
      promiseItem.push(this.$store.dispatch('strategy-config/getUnitList'))
    }
    try {
      const data = await Promise.all(promiseItem)
      this.proxyInfo = data[0] // 云区域展示数据
      this.detailData = data[1]
      if (this.type === 'customTimeSeries') {
        this.unitList = data[2] // 单位list
        // eslint-disable-next-line vue/max-len
        title = `${this.$tc('route-' + '自定义指标').replace('route-', '')} - #${this.detailData.time_series_group_id} ${this.detailData.name}`
      } else {
        // eslint-disable-next-line vue/max-len
        title = `${this.$tc('route-' + '自定义事件').replace('route-', '')} - #${this.detailData.bk_event_group_id} ${this.detailData.name}`
      }
      this.$store.commit('app/SET_NAV_TITLE', title)
      this.handleDetailData(this.detailData)
      this.loading = false
    } catch (error) {
      this.loading = false
    }
  }

  //  处理详情数据
  handleDetailData(detailData: IDetailData) {
    if (this.type === 'customTimeSeries') {
      this.tableId = detailData.table_id
      this.metricData = detailData.metric_json[0].fields.map((item) => {
        item.label === undefined && this.$set(item, 'label', '')
        return {
          ...item,
          selection: false,
          descReValue: false
        }
      })
      this.pagination.total = this.metricData.length
      if (!this.metricData.length) {
        this.isShowData = false
      }
    }
    this.scenario = `${detailData.scenario_display[0]} - ${detailData.scenario_display[1]}`
    this.eventData = detailData.event_info_list
    this.copyName = this.detailData.name
    const str = this.type === 'customEvent'
      ? `# ${this.$t('事件标识名，最大长度128')}
                "event_name": "input_your_event_name",
                "event": {
                    # ${this.$t('事件内容，必需项')}
                    "content": "user xxx login failed"
                },`
      : `# ${this.$t('指标，必需项')}
        "metrics": {
            "cpu_load": 10
        },`
    this.preData = `{
    # ${this.$t('数据通道标识，必需项')}
    "data_id": ${detailData.bk_data_id},
    # ${this.$t('数据通道标识验证码，必需项')}
    "access_token": "${detailData.access_token}",
    "data": [{
        ${str}
        # ${this.$t('来源标识如IP，必需项')}
        "target": "127.0.0.1",
        # ${this.$t('自定义维度，非必需项')}
        "dimension": {
            "module": "db",
            "location": "guangdong",
            # ${this.$t('event_type 为非必须项，用于标记事件类型，默认为异常事件')}
            # ${this.$t('recovery:恢复事件，abnormal:异常事件')}
            "event_type": "abnormal" 
        },
        # ${this.$t('数据时间，精确到毫秒，非必需项')}
        "timestamp": ${new Date().getTime()}
    }]
}`
  }

  //  点击icon展示name编辑
  handleShowEdit() {
    this.isShowEditName = true
    this.$nextTick(() => {
      this.nameInput.focus()
    })
  }

  //  编辑名字
  async handleEditName() {
    if (!(this.copyName && this.copyName !== this.detailData.name)) {
      this.copyName = this.detailData.name
      this.isShowEditName = false
      return
    }
    //  名字是否重复校验
    let isOkName = true
    const res = this.type === 'customEvent'
      ? await this.$store.dispatch(
        'custom-escalation/validateCustomEventName'
        , { name: this.copyName }
      ).catch(() => false)
      : await this.$store.dispatch(
        'custom-escalation/validateCustomTimetName'
        , { name: this.copyName }
      ).catch(() => false)
    if (!res) {
      isOkName = false
      this.$bkMessage({
        theme: 'error',
        message: this.$t('名称已存在')
      })
    }
    if (!isOkName) {
      this.copyName = this.detailData.name
      this.$nextTick(() => {
        this.nameInput.focus()
      })
      return
    }
    if (this.type === 'customEvent') {
      const params: IEditParams = {
        bk_event_group_id: this.detailData.bk_event_group_id,
        name: this.copyName,
        scenario: this.detailData.scenario,
        is_enable: true
      }
      this.loading = true
      await this.$store.dispatch('custom-escalation/editCustomEvent', params)
    }
    this.detailData.name = this.copyName
    this.isShowEditName = false
    this.loading = false
  }

  //  查看原始数据侧滑栏
  handleOpenSideslider(data: {}, title: string) {
    this.sideslider.isShow = true
    this.sideslider.data = data
    this.sideslider.title = title
  }

  // 添加策略
  handleAddStrategy(row) {
    const data: any = {
      data_source_label: 'custom',
      data_type_label: 'event',
      interval: 60,
      method: 'COUNT',
      metric_field: row.custom_event_id,
      result_table_id: this.detailData.bk_data_id,
      result_table_label: this.detailData.scenario
    }
    this.$router.push({
      name: 'strategy-config-add',
      params: {
        data
      }
    })
  }
  // 跳转关联策略
  handleGotoStrategy(row) {
    if (!row.related_strategies.length) return
    this.$router.push({
      name: 'strategy-config',
      params: {
        bkStrategyId: row.related_strategies.map(id => ({ id, name: id }))
      }
    })
  }

  //  改变事件列表刷新时间
  handleRefreshChange(value: number) {
    if (value === 0) return
    clearTimeout(this.timer)
    this.timer = null
    this.timer = setTimeout(async () => {
      const params: IParams = { // 自定义事件初次进入会请求最近半小时的数据
        time_range: this.getTimeParams(),
        bk_event_group_id: this.$route.params.id
      }
      const detailData: Promise<any> = await this.$store.dispatch('custom-escalation/getCustomEventDetail', params)
      this.eventData = detailData.event_info_list
      this.handleRefreshChange(value)
    }, 1000 * value)
  }

  //  改变事件列表时间选择
  async handleTimeChange() {
    const timeRange = this.getTimeParams()
    const params: IParams = {
      bk_event_group_id: this.$route.params.id,
      time_range: timeRange
    }
    try {
      this.detailData = await this.$store.dispatch('custom-escalation/getCustomEventDetail', params)
      this.handleDetailData(this.detailData)
      this.loading = false
    } catch (error) {
      this.loading = false
    }
  }

  //  复制数据上报样例
  handleCopyData() {
    const str = this.type === 'customEvent'
      ? `"event_name": "input_your_event_name",
        "event": {
            "content": "user xxx login failed"
        },`
      : `"metrics": {
            "cpu_load": 10
        },`
    const example = `{
    "data_id": ${this.detailData.bk_data_id},
    "access_token": "${this.detailData.access_token}",
    "data": [{
        ${str}
        "target": "127.0.0.1",
        "dimension": {
            "module": "db",
            "location": "guangdong"
        },
        "timestamp": ${new Date().getTime()}
    }]
}`
    this.textCopy.value = example
    this.textCopy.select()
    document.execCommand('copy')
    this.$bkMessage({
      theme: 'success',
      message: this.$t('样例复制成功')
    })
  }

  //  自定义指标保存
  async handleSubmit() {
    this.loading = true
    const params = {
      time_series_group_id: this.detailData.time_series_group_id,
      name: this.copyName,
      metric_json: [{
        fields: this.metricData,
        table_name: 'base',
        table_desc: '默认分类'
      }]
    }
    const data = await this.$store.dispatch('custom-escalation/editCustomTime', params)
    if (data) {
      this.$bkMessage({ theme: 'success', message: '变更成功' })
    }
    this.loading = false
  }

  //  别名失焦校验
  handleCheckDescName(row) {
    // 校验别名是否冲突
    if (row.description !== '') {
      if (this.descNameList.filter(item => item === row.description).length > 1) {
        row.descReValue = true
      } else {
        row.descReValue = false
      }
    }
  }

  //  指标/维度表交互
  handleMouseenter(index) {
    this.unit.value = true
    this.unit.index = index
  }

  //  指标/维度表交互
  handleMouseLeave() {
    if (!this.unit.toggle) {
      this.unit.value = false
      this.unit.index = -1
    }
  }

  //  指标/维度表交互
  handleToggleChange(value) {
    this.unit.toggle = value
  }

  //  找到单位值对应的name
  handleFindUnitName(id) {
    let name = 'none'
    this.unitList.forEach((group) => {
      const res = group.formats.find(item => item.id === id)
      if (res) {
        name = res.name
      }
    })
    return name
  }
  handleExportMetric(cb) {
    typeof cb === 'function' && cb(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
      this.metricData.map(({ descReValue, ...item }) => (item)),
      `${this.detailData.name}-${moment().format('YYYY-MM-DD HH-mm-ss')}.json`
    )
  }
  handleImportMetric(data: string) {
    let dataJson = null
    try {
      dataJson = JSON.parse(data as any)
    } catch (error) {
      this.$bkMessage({
        message: this.$t('导入文件语法错误'),
        theme: 'error'
      })
    }
    if (dataJson?.length) {
      dataJson.forEach((item) => {
        if (item.name) {
          const setItem = this.metricData.find(set => set.name === item.name)
          if (setItem) {
            setItem.monitor_type === 'metric' && (setItem.unit = item.unit || '')
            setItem.description = item.description || ''
            setItem.label = item.label || ''
            setItem.selection = item.selection || false
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
    @import "../../static/css/common";

    .custom-detail {
      font-size: 12px;
      position: relative;
      height: calc(100vh - 72px);
      .detail-information {
        padding: 20px 20px 4px 37px;
        border-radius: 2px;
        background: $whiteColor;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, .1);
        margin-bottom: 16px;

        @include  border-1px($color: $defaultBorderColor);
        &-title {
          font-weight: bold;
          color: $defaultFontColor;
          margin-bottom: 16px;
        }
        &-row {
          height: 32px;
          margin-bottom: 4px;
          display: flex;
          align-items: center;
          line-height: 16px;
          .row-label {
            text-align: right;
            width: 79px;
            margin-right: 26px;
          }
          .row-content {
            color: #313238;
          }
          .edit-name {
            color: $defaultBorderColor;
            font-size: 24px;
            &:hover {
              color: $primaryFontColor;
              cursor: pointer;
            }
          }
        }
        .last-row {
          margin-bottom: 12px;
        }
      }
      .detail-list {
        // padding-bottom: 24px;
        .list-header {
          display: flex;
          align-items: center;
          margin: 3px 0 25px 0;
          &-title {
            flex-grow: 1;
            font-weight: bold;
            .title-desc {
              color: $unsetIconColor;
              font-weight: normal;
            }
          }
          &-time {
            margin-right: 10px;
          }
          &-button {
            color: $primaryFontColor;
            margin-right: 8px;
          }
          &-refresh {
            margin-right: 10px;
            width: 110px;
          }
          &-date {
            width: 110px;
          }
        }
        .mb16 {
          margin-bottom: 16px;
        }
        .button-control-wrap {
          display: flex;
          align-items: center;
          margin-bottom: 16px;
          .button-control-left {
            flex: 1;
            display: flex;
          }
        }
        .num-set {
          text-align: right;
          width: 48px;
        }
        .col-btn {
          color: #3a84ff;
          cursor: pointer;
        }
        .table-box {
          display: flex;
          overflow-y: hidden;
          /deep/ {
            .bk-form-input,
            .bk-select {
              border: 1px solid #fff;
              &:hover {
                background: #f5f6fa;
                border: 1px solid #f5f6fa;
              }
            }
            .bk-form-input[disabled] {
              color: #63656e;

              /* stylelint-disable-next-line declaration-no-important */
              background: #fff !important;

              /* stylelint-disable-next-line declaration-no-important */
              border-color: #fff !important;
              cursor: no-drop;
            }
            .is-focus {
              border-color: #3a84ff;
              box-shadow: none;
              &:hover {
                background: #fff;
                border-color: #3a84ff;
              }
            }
            .bk-table-empty-text {
              padding: 29px 0 0 0;
              height: 92px;
            }
          }
          .left-table {
            margin-right: 4px;
            width: 100%;
            transition: width .5s;
            .overflow-tips {
              text-overflow: ellipsis;
              overflow: hidden;
              white-space: nowrap;
            }
            .cell-margin {
              margin-left: -10px;
              .icon-change {
                color: #ea3636;
              }
            }
            .cell-span {
              height: 26px;
              line-height: 26px;
              padding-left: 1px;
            }
            .name {
              position: relative;
              .change-name {
                position: absolute;
                right: 10px;
                top: 0;
                font-size: 20px;
                color: #ea3636;
                i {
                  font-size: 16px;
                  margin-top: 5px;
                }
                .icon-remind {
                  display: inline-block;
                  cursor: pointer;
                }
              }
            }
            .input-err {
              /deep/ .bk-form-input {
                padding: 0 30px 0 10px;
              }
            }
            /deep/ .bk-table-row td {
              /* stylelint-disable-next-line declaration-no-important */
              background: #fff !important;
            }
            .table-group-select {
              position: relative;
              min-width: 160px;
              height: 26px;
              padding-right: 40px;
              line-height: 26px;
              white-space: nowrap;
              padding-left: 8px;
              .icon-arrow-down {
                display: none;
                position: absolute;
                right: 8px;
                top: 0;
                font-size: 24px;
              }
              &:hover {
                background: #f0f1f5;
                .icon-arrow-down {
                  display: inline-block;
                }
              }
            }
          }
          .left-active {
            width: calc(100% - 420px);
          }
          .right-data {
            width: 420px;
            display: flex;
            flex-direction: column;
            .ul-head {
              display: flex;
              background: #000;
              .host-type {
                display: flex;
                align-items: center;
                justify-content: center;
                color: $whiteColor;
                height: 42px;
                width: 71px;
                background: #313238;
                position: relative;
                &:after {
                  content: "";
                  width: 71px;
                  height: 2px;
                  position: absolute;
                  background: $primaryFontColor;
                  top: 0;
                }
              }
            }
            .data-preview {
              height: 42px;
              line-height: 42px;
              color: $unsetIconColor;
              background: #313238;
              padding: 0 20px;
              border-bottom: 1px solid #3b3c42;
            }
            .no-data-preview {
              height: 93px;
              width: 420px;
              background: #313238;
            }
          }
        }
        /deep/ .bk-table-linear::before {
          display: none;
        }
        .list-pagination {
          height: 64px;
          padding: 15px 0;
        }
      }
      .right-button {
        position: absolute;
        right: -24px;
        top: 38%;
        z-index: 2;
        width: 24px;
        height: 96px;

        /* stylelint-disable-next-line declaration-no-important */
        border: 1px solid #dcdee5 !important;
        border-radius: 8px 0 0 8px;
        background: $defaultBgColor;
        transition: right .5s;
        padding-top: 44px;
        display: flex;
        flex-direction: column;
        line-height: 1.2;

        @include hover($cursor: pointer)
        ;
        .icon {
          transform: rotate(90deg);
          font-size: 13px;
        }
        div {
          margin: -4px 0 0 6px;
        }}
      .right-window {
        background: $whiteColor;
        z-index: 2;
        border: 0;
        overflow-x: hidden;
        overflow-y: scroll;
        transition: width .5s;

        @include common-svg($h: calc(100vh - 51px),$t: -21px,$w: 0,$r: -24px);
        &-title {
          height: 40px;
          width: 100%;
          font-size: 14px;
          color: #313238;
          line-height: 40px;
          padding-left: 24px;
          background: $defaultBgColor;
          border-bottom: 1px solid #dcdee5;
        }
        &-content {
          padding: 16px 23px 0;
          color: $defaultFontColor;
          .content-title {
            font-weight: bold;
            margin-bottom: 10px;
          }
          .content-interval {
            margin-top: 25px;
          }
          .content-row {
            position: relative;
            margin-bottom: 16px;
            .content-example {
              margin-top: 6px;
              padding: 10px 14px;
              background: #f4f4f7;
            }
            .content-copy {
              position: absolute;
              top: 30px;
              right: 10px;

              @include hover($cursor: pointer);
            }
            .copy-textarea {
              height: 0px;
              opacity: 0;
            }
          }
          pre {
            margin: 0;
            line-height: 20px;
          }
        }
      }
      .active-buttom {
        right: 375px;
        overflow: hidden;
      }
      .active {
        width: 400px;

        @include border-1px($color: $defaultBorderColor);
      }
      /deep/ .bk-sideslider-wrapper {
        background: #313239;
      }
      .sideslider-title {
        display: flex;
        align-items: center;
        .title-explain {
          color: $unsetIconColor;
          font-size: 12px;
        }
      }
      ::-webkit-scrollbar {
        display: none;
      }
    }
</style>
