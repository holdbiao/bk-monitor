<!--
 * @Author:
 * @Date: 2021-06-10 11:55:13
 * @LastEditTime: 2021-06-21 11:27:44
 * @LastEditors:
 * @Description:
-->
<template>
  <div class="performance" v-bkloading="{ isLoading }">
    <div class="performance-table">
      <bk-table
        ref="table"
        v-if="Object.keys(columns).length"
        :key="tableKey"
        :data="tableData"
        :empty-text="$t('查询无数据')"
        @sort-change="handleSortChange"
        @row-mouse-enter="handleRowEnter"
        @row-mouse-leave="handleRowLeave">
        <template #prepend>
          <transition name="fade">
            <div class="selection-tips" v-show="allCheckValue === 2">
              <i18n path="已选主机">
                <span class="tips-num">{{ selectionsCount }}</span>
              </i18n>
              <bk-button
                v-if="checkType === 'current'"
                ext-cls="tips-btn"
                text
                @click="handleSelectAll">
                <i18n path="选择所有主机">
                  <span class="tips-num">{{ pageConfig.total }}</span>
                </i18n>
              </bk-button>
              <bk-button
                ext-cls="tips-btn"
                text
                v-else
                @click="handleClearAll">
                {{ $t('清除所有数据') }}
              </bk-button>
            </div>
          </transition>
        </template>
        <bk-table-column
          :render-header="renderSelectionHeader"
          width="80"
          align="center">
          <template #default="{ row }">
            <bk-checkbox
              v-model="row.selection"
              @change="handleRowCheck($event, row)">
            </bk-checkbox>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_host_innerip.name"
          v-if="columns.bk_host_innerip.checked" min-width="120">
          <template #default="{ row }">
            <div class="ip-col" @mouseenter="handleRowEnter(row)" @mouseleave="handleRowLeave(row)">
              <router-link
                class="ip-col-main"
                :to="{
                  name: 'performance-detail',
                  params: {
                    title: row.bk_host_innerip,
                    id: `${row.bk_host_innerip}-${row.bk_cloud_id}`,
                    osType: Number(row.bk_os_type)
                  }
                }">
                {{row.bk_host_innerip}}
              </router-link>
              <svg viewBox="0 0 28 16"
                   class="ip-col-mark"
                   v-show="hoverMarkId === row.rowId || row.mark"
                   @click.stop.prevent="handleIpMark(row)"
                   v-if="$i18n.locale !== 'enUS'">
                <path :class="[row.mark ? 'path-primary' : 'path-default']" d="M26,0H2C0.9,0,0,0.9,0,2v12c0,1.1,0.9,2,2,2h24c1.1,0,2-0.9,2-2V2C28,0.9,27.1,0,26,0z" />
                <path fill="#FFFFFF" d="M5.1,11.3h1V7.5h2.6V7.1H5.3V6.3h3.4V5.9H5.7V4h7.7v2h-3.3v0.4h3.6v0.8h-3.6v0.4h2.8v3.8h1v0.8H5.1V11.3z M6.8,5.2h1.1V4.7H6.8V5.2z M11.7,8.2H7.3v0.3h4.4V8.2z M7.3,9.5h4.4V9.1H7.3V9.5z M7.3,10.4h4.4V10H7.3V10.4z M7.3,11.3h4.4v-0.3H7.3V11.3z M9,5.2h1.1V4.7H9V5.2z M12.2,5.2V4.7h-1.1v0.5H12.2z" />
                <path fill="#FFFFFF" d="M14.1,4.1h3.1v1.2h-0.8v5.4c0,0.4-0.1,0.6-0.2,0.8c-0.1,0.2-0.3,0.3-0.5,0.4s-0.7,0.1-1.4,0.1c0-0.4-0.1-0.7-0.2-1.1c0.3,0,0.5,0,0.8,0c0.2,0,0.4-0.1,0.4-0.4V5.3h-1.1V4.1z M19.4,7.5h1.2c0,0.9-0.1,1.6-0.2,2.1c0.8,0.5,1.7,1.1,2.5,1.7l-0.7,0.9c-0.6-0.5-1.3-1-2.2-1.7c-0.4,0.7-1.2,1.2-2.5,1.7c-0.2-0.3-0.4-0.7-0.7-1.1c0.6-0.2,1.2-0.4,1.6-0.7c0.4-0.3,0.7-0.7,0.8-1.1C19.3,8.9,19.4,8.3,19.4,7.5z M17.4,4h5.4v1.1h-2.3l-0.2,0.8h2.2v4h-1.2V7h-2.7v3h-1.2V5.9h1.5l0.2-0.8h-1.7V4z" />
              </svg>
              <svg-icon icon-name="top"
                        v-show="hoverMarkId === row.rowId || row.mark"
                        @click.stop.prevent="handleIpMark(row)"
                        class="ip-col-mark"
                        :class="[row.mark ? 'path-primary' : 'path-default']"
                        v-else>
              </svg-icon>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_host_outerip.name"
          min-width="120"
          v-if="columns.bk_host_outerip.checked">
          <template #default="{ row }">
            <div class="ip-col">
              <span>{{row.bk_host_outerip | emptyStringFilter}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.status.name"
          min-width="120"
          v-if="columns.status.checked">
          <template #default="{ row }">
            <div class="status-col" v-if="statusMap[row.status]">
              <span :class="'status-' + statusMap[row.status].status"></span>
              <span class="status-name" @mouseenter="handleTipsMouseenter($event, row, 'Host')">{{ statusMap[row.status].name }}</span>
            </div>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_host_name.name"
          min-width="140"
          v-if="columns.bk_host_name.checked">
          <template #default="{ row }">
            <div class="ip-col">
              <span>{{row.bk_host_name || '--'}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_os_name.name"
          min-width="140"
          v-if="columns.bk_os_name.checked">
          <template #default="{ row }">
            <div class="ip-col">
              <span>{{row.bk_os_name}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_cloud_name.name"
          v-if="columns.bk_cloud_name.checked"
          min-width="120px">
          <template #default="{ row }">
            <span>{{row.bk_cloud_name}}</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_cluster.name"
          min-width="140px"
          v-if="columns.bk_cluster.checked">
          <template #default="{ row }">
            <span v-bk-tooltips="{
              content: row.bk_cluster.map(item => item.name).join(),
              showOnInit: false,
              placements: ['top'],
              interactive: false
            }">
              {{row.bk_cluster.map(item => item.name).join()}}
            </span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_inst_name.name"
          min-width="120px"
          v-if="columns.bk_inst_name.checked">
          <template #default="{ row }">
            <span v-bk-tooltips="{
              content: row.bk_inst_name,
              showOnInit: false,
              placements: ['top'],
              interactive: false
            }">{{row.bk_inst_name}}</span>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="totalAlarmCount"
          min-width="120"
          :label="columns.alarm_count.name"
          v-if="columns.alarm_count.checked">
          <template #default="{ row }">
            <span class="status-label"
                  @mouseenter="row.totalAlarmCount && handleUnresolveEnter(row, $event)"
                  @mouseleave="row.totalAlarmCount && handleUnresolveLeave()"
                  @click="handleGoEventCenter(row)"
                  :class="{ 'status-unresolve': !!row.totalAlarmCount }">
              {{row.totalAlarmCount >= 0 ? row.totalAlarmCount : '--'}}
            </span>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="cpu_load"
          align="right"
          min-width="140"
          :label="columns.cpu_load.name"
          v-if="columns.cpu_load.checked">
          <template #default="{ row }">
            <div class="cpu-col">
              <span>{{row.cpu_load | isNumberFilter}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="cpu_usage"
          min-width="180"
          :label="columns.cpu_usage.name"
          v-if="columns.cpu_usage.checked">
          <template #default="{ row }">
            <div>
              <div class="rate-name">
                {{row.cpu_usage | emptyNumberFilter}}
              </div>
              <bk-progress
                :color="row.cpu_usage | progressColors"
                :show-text="false"
                :percent="+(row.cpu_usage * 0.01).toFixed(2) || 0">
              </bk-progress>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="disk_in_use"
          min-width="180"
          :label="columns.disk_in_use.name"
          v-if="columns.disk_in_use.checked">
          <template #default="{ row }">
            <div>
              <div class="rate-name">
                {{row.disk_in_use | emptyNumberFilter}}
              </div>
              <bk-progress
                :color="row.disk_in_use | progressColors"
                :show-text="false"
                :percent="+(row.disk_in_use * 0.01).toFixed(2) || 0">
              </bk-progress>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="io_util"
          min-width="180"
          :label="columns.io_util.name"
          v-if="columns.io_util.checked">
          <template #default="{ row }">
            <div>
              <div class="rate-name">
                {{row.io_util | emptyNumberFilter}}
              </div>
              <bk-progress
                :color="row.io_util | progressColors"
                :show-text="false"
                :percent="+(row.io_util * 0.01).toFixed(2) || 0">
              </bk-progress>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="mem_usage"
          min-width="180"
          :label="columns.mem_usage.name"
          v-if="columns.mem_usage.checked">
          <template #default="{ row }">
            <div>
              <div class="rate-name">
                {{row.mem_usage | emptyNumberFilter}}
              </div>
              <bk-progress
                :color="row.mem_usage | progressColors"
                :show-text="false"
                :percent="+(row.mem_usage * 0.01).toFixed(2) || 0">
              </bk-progress>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          sortable="custom"
          prop="psc_mem_usage"
          min-width="180"
          :label="columns.psc_mem_usage.name"
          v-if="columns.psc_mem_usage.checked">
          <template #default="{ row }">
            <div>
              <div class="rate-name">
                {{row.psc_mem_usage | emptyNumberFilter}}
              </div>
              <bk-progress
                :show-text="false"
                :color="row.psc_mem_usage | progressColors"
                :percent="+(row.psc_mem_usage * 0.01).toFixed(2) || 0">
              </bk-progress>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="columns.bk_biz_name.name"
          min-width="110"
          v-if="columns.bk_biz_name.checked">
          <template #default="{ row }">
            <div class="ip-col">
              <span>{{row.bk_biz_name}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :resizable="false"
          :label="columns.display_name.name"
          v-if="columns.display_name.checked"
          min-width="310">
          <template #default="{ row, $index }">
            <div class="process-module">
              <div class="process-module-wrap" :ref="'table-row-' + $index">
                <span
                  v-for="item in row.component"
                  :key="item.display_name"
                  :class="['process-status', item.status === -1 ? 'process-status-default' : `process-status-${item.status}`]"
                  @click.stop="openProcessView(row, item.display_name)"
                  @mouseenter="handleTipsMouseenter($event, item, 'Thread')">
                  {{item.display_name}}
                </span>
                <span
                  v-if="overflowRowIds.includes(row.rowId)"
                  @click="openProcessView(row,'row-overflow')"
                  class="process-status-3 process-overflow">
                  {{ `...` }}
                </span>
              </div>
            </div>
          </template>
        </bk-table-column>
      </bk-table>
    </div>
    <div class="performance-footer" v-if="data.length">
      <bk-pagination
        size="small"
        class="performance-footer-pagination"
        align="right"
        pagination-able
        show-total-count
        :current="pageConfig.page"
        :limit="pageConfig.pageSize"
        @change="handlePageChange"
        @limit-change="handleLimitChange"
        :count="pageConfig.total"
        :limit-list="pageConfig.pageList">
      </bk-pagination>
    </div>
    <div v-show="false">
      <tips-tpl
        ref="tipsTpl"
        :tips-text="tipsData.tipsText"
        :link-text="tipsData.linkText"
        :link-url="tipsData.linkUrl"
        :doc-link="tipsData.docLink">
      </tips-tpl>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Watch, Ref } from 'vue-property-decorator'
import UnresolveList from '../unresolve-list/unresolve-list.vue'
import ColumnCheck from '../column-check/column-check.vue'
import { typeTools } from '../../../../monitor-common/utils/utils.js'
import moment from 'moment'
import MonitorVue from '../../../types/index'
import { CreateElement } from 'vue'
import { IPageConfig, ICheck, ISort, ITableRow, CheckType } from '../performance-type'
// import AbnormalTips from '../../../components/abnormal-tips/abnormal-tips.vue'
import TipsTpl from '../../../components/abnormal-tips/tips-tpl.vue'
import PerformanceModule from '../../../store/modules/performance'

@Component({
  name: 'performance-table',
  components: {
    TipsTpl
  },
  filters: {
    progressColors(v) {
      if (v > 85 && v < 95) {
        return '#FF8000'
      } if (v >= 95) {
        return '#EA3636'
      }
      return '#2DCB56'
    },
    emptyStringFilter(v) {
      return typeTools.isNull(v) ? '--' : v
    },
    emptyNumberFilter(v) {
      return v > 0 ? `${v}%` : '--'
    },
    isNumberFilter(v) {
      return typeof v === 'number' ? v : '--'
    }
  }
})
export default class PerformanceTable extends Vue<MonitorVue> {
  // 表格数据
  @Prop({ default: () => [], type: Array }) private readonly data: any[]
  // 显示列配置
  @Prop({ default: () => ({}), type: Object }) private readonly columns: any
  // 分页配置
  @Prop({
    default: () => ({
      page: 1,
      pageSize: 10,
      pageList: [10, 20, 50, 100],
      total: 0
    }),
    type: Object
  }) private readonly pageConfig: IPageConfig
  @Prop({ default: 0, type: Number }) private readonly allCheckValue: 0 | 1 | 2  // 0: 取消全选 1: 半选 2: 全选
  @Prop({ default: 'current', type: String }) private readonly checkType: CheckType
  @Prop({ default: () => [], type: Array }) private readonly selectionData: ITableRow[]
  @Prop({ default: () => [], type: Array }) private readonly excludeDataIds: string[]
  @Prop({ default: 0, type: Number }) private readonly selectionsCount: number

  @Ref('table') private readonly tableRef!: any
  @Ref('tipsTpl') private readonly tipsTplTef: any

  // 提示组件实例
  private tipsPopoverInstance = null
  private tipsData: any = {
    tipsText: '',
    linkText: '',
    linkUrl: '',
    docLink: ''
  }
  // 未恢复告警组件实例
  private unresolveInstance = null
  // 未恢复详情面板弹窗实例
  private popoverInstance = null
  // 表格Key（用于刷新表格数据）
  private tableKey = +new Date()
  private statusMap = {
    '-1': {
      name: window.i18n.t('未知'),
      status: '3'
    },
    0: {
      name: window.i18n.t('正常'),
      status: '1'
    },
    1: {
      name: window.i18n.t('离线'),
      status: '1'
    },
    2: {
      name: window.i18n.t('Agent未安装'),
      status: '2',
      tips: window.i18n.t('原因: Agent未安装或者状态异常'),
      url: `${this.$store.getters.bkNodemanHost}#/agent-manager/status`
    },
    3: {
      name: window.i18n.t('无数据上报'),
      status: '3',
      tips: window.i18n.t('原因：basereport未安装或者状态异常'),
      url: `${this.$store.getters.bkNodemanHost}#/plugin-manager/list`
    }
  }

  private selectList = [
    {
      id: 'current',
      name: window.i18n.t('本页全选')
    },
    {
      id: 'all',
      name: window.i18n.t('跨页全选')
    }
  ]

  private overflowRowIds: string[] = []
  private hoverMarkId = ''
  // 表格数据
  private tableData: ITableRow[] = []

  private componentStatusMap: any = {
    1: { // 异常
      tipsText: window.i18n.t('原因：查看进程本身问题或者检查进程配置是否正常'),
      docLink: 'processMonitor'
    },
    2: { // 无数据
      tipsText: window.i18n.t('原因：processbeat进程采集器未安装或者状态异常'),
      linkText: window.i18n.t('前往节点管理处理'),
      linkUrl: `${this.$store.getters.bkNodemanHost}#/plugin-manager/list`
    },
    3: {}
  }
  private isLoading = false

  activated() {
    this.tableData = JSON.parse(JSON.stringify(this.data))
    this.unresolveInstance = new Vue(UnresolveList).$mount()
  }

  public updateDataSelection() {
    this.tableData.forEach((item) => {
      if (this.checkType === 'current') {
        item.selection = this.selectionData.some(item => item.rowId === item.rowId)
      } else {
        item.selection = !this.excludeDataIds.includes(item.rowId)
      }
    })
  }

  @Watch('data')
  private async handleDataChange(data) {
    const tableData = JSON.parse(JSON.stringify(data))
    const [firstItem] = tableData
    // 状态不存在则需要拉取当前页状态并合并
    if (firstItem && !this.statusMap[firstItem.status]) {
      PerformanceModule.searchHostMetric({
        ips: tableData.map(item => ({
          ip: item.bk_host_innerip,
          bk_cloud_id: item.bk_cloud_id,
          bk_host_id: item.bk_host_id
        }))
      }).then((hostsMap) => {
        // 解决全量数据先返回的时序问题
        const [first] = this.tableData
        if (!first || !this.statusMap[first.status]) {
          const data = this.tableData.map((item) => {
            const resetData = hostsMap[`${item.bk_host_innerip}|${item.bk_cloud_id}`] || {}
            return {
              ...item,
              ...resetData
            }
          })
          this.setTableData(data)
        }
      })
    }
    this.setTableData(tableData)
  }

  private async setTableData(tableData) {
    this.tableData = tableData.map((item) => {
      if (this.checkType === 'all') {
        item.selection = !this.excludeDataIds.includes(item.rowId)
      }
      return item
    })

    await this.$nextTick()
    this.overflowRowIds = []
    this.tableData.forEach((item, index) => {
      const ref = this.$refs[`table-row-${index}`]
      const overflow = ref && (ref as HTMLElement).clientHeight > 30
      overflow && this.overflowRowIds.push(item.rowId)
    })
  }

  @Emit('sort-change')
  private handleSortChange({ order, prop }: ISort) {
    return {
      order,
      prop
    }
  }

  private handleRowEnter(row) {
    this.hoverMarkId = row.rowId
  }

  private handleRowLeave() {
    this.hoverMarkId = ''
  }

  // 自定义check表头
  private renderSelectionHeader(h: CreateElement) {
    return h(ColumnCheck, {
      props: {
        list: this.selectList,
        value: this.allCheckValue,
        defaultType: this.checkType
      },
      on: {
        change: this.handleCheckChange
      }
    })
  }

  @Emit('check-change')
  private handleCheckChange({ value, type }: ICheck) {
    return {
      value,
      type
    }
  }

  @Emit('ip-mark')
  private handleIpMark(row) {
    return row
  }

  @Emit('limit-change')
  private handleLimitChange(limit: number) {
    return limit
  }

  @Emit('page-change')
  private handlePageChange(page: number) {
    return page
  }

  // 未恢复列表
  private handleUnresolveEnter(data, e) {
    if (!data.alarm_count || !data.alarm_count.length) {
      return false
    }
    this.unresolveInstance.list = data.alarm_count
    this.popoverInstance = this.$bkPopover(e.target, {
      content: this.unresolveInstance.$el,
      arrow: true,
      placement: 'right',
      maxWidth: 520
    })
    this.popoverInstance?.show(100)
  }

  private handleUnresolveLeave() {
    if (this.popoverInstance) {
      this.popoverInstance.hide(100)
      this.popoverInstance.destroy()
      this.popoverInstance = null
    }
  }

  // 行勾选事件
  @Emit('row-check')
  private handleRowCheck(value: boolean, row: ITableRow) {
    return {
      value,
      row
    }
  }

  private updateTableKey() {
    this.$nextTick(() => {
      this.tableKey = +new Date()
    })
  }

  // 主机详情--进程视图
  private openProcessView(row: ITableRow, process) {
    this.$router.push({
      name: 'performance-detail',
      params: {
        title: row.bk_host_innerip,
        id: `${row.bk_host_innerip}-${row.bk_cloud_id}`,
        osType: Number(row.bk_os_type),
        processId: process
      }
    })
  }

  private handleGoEventCenter(row) {
    if (!row.bk_host_innerip || !row.totalAlarmCount) return
    const endTime = moment().format('YYYY-MM-DD HH:mm:ss')
    const beginTime = moment(endTime).add(-7, 'd')
      .format('YYYY-MM-DD HH:mm:ss')
    this.$router.push({
      name: 'event-center',
      params: {
        query: row.bk_host_innerip, // 事件列表自定义搜索ip
        status: 'ABNORMAL',
        beginTime,
        endTime
      }
    })
  }

  // 跨页全选操作
  private handleSelectAll() {
    this.handleCheckChange({
      value: 2,
      type: 'all'
    })
  }

  // 清除勾选
  private handleClearAll() {
    this.handleCheckChange({
      value: 0,
      type: 'current'
    })
  }

  private handleTipsMouseenter(e: MouseEvent, item, type: 'Host' | 'Thread') {
    if (type === 'Host' && [2, 3].includes(item.status)) {
      this.tipsData.tipsText = this.statusMap[item.status].tips
      this.tipsData.linkText = this.$t('前往节点管理处理')
      this.tipsData.linkUrl = this.statusMap[item.status].url
      this.tipsData.docLink = ''
    } else if (type === 'Thread' && [2, 1].includes(item.status)) {
      this.tipsData.tipsText = this.componentStatusMap[item.status].tipsText
      this.tipsData.linkText = this.componentStatusMap[item.status].linkText
      this.tipsData.linkUrl = this.componentStatusMap[item.status].linkUrl
      this.tipsData.docLink = this.componentStatusMap[item.status].docLink
    } else {
      return
    }
    this.initTipsPopover(e.target)
  }

  private initTipsPopover(target) {
    if (!this.tipsPopoverInstance) {
      this.tipsPopoverInstance = this.$bkPopover(target, {
        content: this.tipsTplTef.$el,
        interactive: true,
        arrow: true,
        placement: 'top',
        onHidden: () => {
          this.tipsPopoverInstance?.destroy()
          this.tipsPopoverInstance = null
        }
      })
      this?.tipsPopoverInstance?.show()
    }
  }

  private hiddenPopover() {
    this?.tipsPopoverInstance?.hide()
  }

  // eslint-disable-next-line @typescript-eslint/member-ordering
  public sort({ prop, order }: ISort) {
    this?.tableRef?.sort(prop, order)
  }

  // eslint-disable-next-line @typescript-eslint/member-ordering
  public clearSort() {
    this?.tableRef?.clearSort()
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

$statusBorderColors: #2dcb56 #c4c6cc #ea3636;
$statusColors: #94f5a4 #f0f1f5 #fd9c9c;
$processBorderColors: #fd9c9c #dcdee5 #dcdee5;
$processColors: #ea3636 #c4c6cc #63656e;

.performance {
  &-table {
    .selection-tips {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 30px;
      background: #ebecf0;
      .tips-num {
        font-weight: bold;
      }
      .tips-btn {
        font-size: 12px;
        margin-left: 5px;
      }
    }
    /deep/ .bk-table td,
    .bk-table th {
      padding: 0;
      font-size: 12px;
    }
    /deep/ .bk-table-header {
      .is-first {
        .bk-table-header-label {
          overflow: visible;
        }
      }
    }
    .select-count {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 30px;
      margin-bottom: 5px;
      font-size: 12px;
      color: #63656e;
      background-color: #f0f1f5;
      .select-all {
        color: #3a84ff;
        cursor: pointer;
      }
    }
    .ip-col {
      color: $defaultFontColor;
      font-size: 12px;
      display: flex;
      align-items: center;
      &-main {
        color: #3a84ff;
        cursor: pointer;
        display: inline-block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      &-mark {
        width: 28px;
        height: 16px;
        margin-left: 6px;

        @include hover();
        &.path-primary {
          color: #3a84ff;
        }
        &.path-default {
          color: #979ba5;
        }
        .path-primary {
          fill: #3a84ff;
        }
        .path-default {
          fill: #979ba5;
        }
      }
    }
    .status-col {
      display: flex;
      align-items: center;
      height: 20px;

      @for $i from 1 through length($statusColors) {
        .status-#{$i} {
          display: inline-block;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: nth($statusColors, $i);
          border: 1px solid nth($statusBorderColors, $i);
          margin-right: 5px;
        }
      }
      .status-name {
        font-size: 12px;
        color: $defaultFontColor;
      }
    }
    .status-label {
      display: inline-block;
      padding: 2px 7px;
      background: #dcdee5;
      text-align: center;
      font-size: 12px;
      color: #fff;
      border-radius: 2px;
    }
    .status-unresolve {
      background: #ff9c01;

      @include hover();
    }
    .rate-name {
      font-size: 12px;
      color: $defaultFontColor;
      line-height: 16px;
    }
    .process-module {
      height: 30px;
      position: relative;
      &-wrap {
        overflow: hidden;
        margin-right: 25px;

        @for $i from 1 through length($processColors) {
          .process-status-#{$i} {
            padding: 3px 7px;
            border-radius: 2px;
            background: #fafbfd;
            font-size: 12px;
            text-align: center;
            margin: 3px;
            line-height: 16px;
            cursor: pointer;
            color: nth($processColors,$i);
            border: 1px solid nth($processBorderColors,$i);
            float: left;
          }
        }
        .process-status-default {
          padding: 3px 7px;
          border-radius: 2px;
          background: #fafbfd;
          font-size: 12px;
          text-align: center;
          margin: 3px;
          line-height: 16px;
          cursor: pointer;
          color: #63656e;
          border: 1px solid #dcdee5;
          float: left;
        }
        .process-overflow {
          position: absolute;
          top: 0;
        }
      }
    }
  }
  &-footer {
    display: flex;
    height: 60px;
    align-items: center;
    justify-content: flex-start;
    padding: 0 20px;
    border: 1px solid $defaultBorderColor;
    border-top: 0;
    &-pagination {
      flex: 1;
    }
  }
}
</style>
