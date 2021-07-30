<template>
  <div class="strategy-config" v-monitor-loading="{ isLoading: loading }">
    <div class="content">
      <div class="content-left"
           data-tag="resizeTarget"
           v-show="showFilterPanel"
           :style="{ 'flex-basis': drapWidth + 'px', width: drapWidth + 'px' }">
        <FilterPanel
          class="content-left-filter"
          :show.sync="showFilterPanel"
          :data="filterPanelData"
          :checked-data="header.keywordObj"
          @change="handleSearchSelectChange">
        </FilterPanel>
        <div class="content-left-drag"
             v-show="showFilterPanel"
             @mousedown="handleMouseDown"
             @mousemove="handleMouseMove">
        </div>
      </div>
      <div class="content-right">
        <div class="strategy-config-header">
          <bk-badge class="badge" dot theme="success" :visible="header.keywordObj.length !== 0" v-show="!showFilterPanel">
            <span class="folding" @click="handleShowFilterPanel()">
              <i class="icon-monitor icon-double-up"></i>
            </span>
          </bk-badge>
          <bk-button
            class="header-btn mc-btn-add"
            theme="primary"
            v-authority="{
              active: !authority.MANAGE_AUTH
            }"
            @click="authority.MANAGE_AUTH ? handleAddStategyConfig() : handleShowAuthorityDetail()">
            {{ $t('新建') }}
          </bk-button>
          <bk-dropdown-menu class="header-select" @show="header.dropdownShow = true" @hide="header.dropdownShow = false" :disabled="!table.select.length" trigger="click">
            <div class="header-select-btn" slot="dropdown-trigger" :class="{ 'btn-disabled': !table.select.length }">
              <span class="btn-name"> {{ $t('批量操作') }} </span>
              <i class="icon-monitor" :class="[header.dropdownShow ? 'icon-arrow-up' : 'icon-arrow-down']"></i>
            </div>
            <ul
              v-authority="{
                active: !authority.MANAGE_AUTH
              }"
              class="header-select-list"
              slot="dropdown-content"
              @click="!authority.MANAGE_AUTH && handleShowAuthorityDetail()">
              <!-- 批量操作监控目标需要选择相同类型的监控对象 -->
              <li v-for="(option, index) in header.list"
                  :key="index"
                  :class="['list-item', { disabled: option.id === 8 && !isSameObjectType }]"
                  v-bk-tooltips="{
                    disabled: !(option.id === 8 && !isSameObjectType),
                    content: $t('监控对象不一致')
                  }"
                  @click="authority.MANAGE_AUTH && handleHeadSelectChange(option.id)">
                {{option.name}}
              </li>
            </ul>
          </bk-dropdown-menu>

          <bk-search-select
            class="header-search"
            v-model="header.keywordObj"
            :show-condition="false"
            :data="conditionList"
            :placeholder="$t('任务ID/告警组名称/服务分类/IP/指标ID')"
            @change="header.handleSearch"
            @clear="header.handleSearch"
            clearable>
          </bk-search-select>
        </div>
        <div class="strategy-config-wrap">
          <div class="config-wrap-setting">
            <bk-popover
              placement="bottom"
              width="515"
              theme="light strategy-setting"
              trigger="click"
              offset="0, 20">
              <div class="setting-btn">
                <i class="icon-monitor icon-menu-set"></i>
              </div>
              <div slot="content" class="tool-popover">
                <div class="tool-popover-title">
                  {{ $t('字段显示设置') }}
                </div>
                <ul class="tool-popover-content">
                  <li v-for="item in fieldSettingData"
                      :key="item.id"
                      class="tool-popover-content-item">
                    <bk-checkbox
                      :value="item.checked"
                      @change="handleCheckColChange(item)"
                      :disabled="item.disable">
                      {{ item.name }}
                    </bk-checkbox>
                  </li>
                </ul>
              </div>
            </bk-popover>
          </div>
          <!-- <ul class="tab-list">
            <li class="tab-list-item" v-for="(item, index) in tab.list"
                @click="handleTabChange(index)"
                :key="item.name"
                :class="{ 'tab-active': index === tab.active }">
              <span class="tab-name">{{item.name}}</span>
              <span class="tab-num">{{item.count}}</span>
            </li>
            <li class="tab-list-blank"></li>
          </ul> -->
          <bk-table
            class="strategy-table"
            :empty-text="$t('查询无数据')"
            v-bkloading="{ isLoading: table.loading }"
            @selection-change="handleSelectionChange"
            @header-dragend="handleHeaderDragend"
            ref="strategyTable"
            :data="table.data">
            <bk-table-column
              type="selection"
              align="center"
              width="50">
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.id.checked"
              label="ID"
              prop="id"
              width="100">
              <template slot-scope="scope">
                #{{ scope.row.id }}
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.strategyName.checked"
              :label="$t('策略名')"
              min-width="120">
              <template slot-scope="scope">
                <div class="col-name">
                  <div class="col-name-desc" @click="handleOpenStategydetail(scope.row)">
                    <span class="col-name-desc-text" v-bk-tooltips="{ content: scope.row.strategyName, delay: 200 }">{{scope.row.strategyName}}</span>
                    <template v-if="scope.row.enabled">
                      <i
                        v-if="scope.row.legacy"
                        v-bk-tooltips.right="$t('策略已失效')"
                        class="icon-monitor icon-sunhuai">
                      </i>
                      <i
                        v-if="scope.row.abnormalAlertCount > 0 && !scope.row.legacy"
                        class="icon-monitor icon-gaojing1"
                        v-bk-tooltips.right="$t('当前有{n}个未恢复事件', { n: scope.row.abnormalAlertCount })"
                        @click.stop="handleToEventCenter(scope.row)">
                      </i>
                    </template>
                  </div>
                  <div class="col-name-type">{{scope.row.firstLabelName}}-{{scope.row.secondLabelName}}</div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column v-if="false" :label="$t('所属')" width="80">
              <template slot-scope="scope">
                <span>{{scope.row.bizName}}</span>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.itemDescription.checked"
              :label="$t('监控项')"
              min-width="120">
              <template slot-scope="scope">
                <div v-bk-tooltips="scope.row.itemDescription.tip">
                  {{scope.row.itemDescription.val}}
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.dataOrigin.checked"
              :label="$t('数据来源')"
              width="80">
              <!-- class-name="label-title" :render-header="renderHeader" -->
              <template slot-scope="scope">
                <span>{{scope.row.dataOrigin}}</span>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.target.checked"
              :label="$t('监控目标')" width="150">
              <template slot-scope="scope">
                <div class="col-name">
                  <div class="col-name-label">{{scope.row.target || $t('本业务')}}</div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.labels.checked"
              :label="$t('标签')">
              <template slot-scope="scope">
                <div class="col-classifiy">
                  <div v-if="scope.row.labels.length > 0" class="col-classifiy-wrap" :ref="'table-labels-' + scope.$index">
                    <span
                      class="classifiy-label gray"
                      v-for="(item, index) in scope.row.labels"
                      :key="`${item}-${index}`">
                      {{item}}
                    </span>
                    <span v-if="scope.row.overflowLabel" class="classifiy-overflow gray">...</span>
                  </div>
                  <div v-else>--</div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.noticeGroupList.checked"
              :label="$t('告警组')">
              <!-- :render-header="renderHeaderNoticeGroup" -->
              <template slot-scope="scope">
                <div class="col-classifiy">
                  <div class="col-classifiy-wrap" :ref="'table-row-' + scope.$index">
                    <span
                      class="classifiy-label"
                      v-for="item in scope.row.noticeGroupList"
                      :key="item.id"
                      v-bk-tooltips="{ content: item.display_name, delay: 200 }">
                      {{item.display_name}}
                    </span>
                    <span v-if="scope.row.overflow" class="classifiy-overflow">...</span>
                  </div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="false"
              :label="$t('监控项')">
              <template slot-scope="scope">
                <div v-bk-tooltips="{ content: scope.row.metricDescriptionList ? scope.row.metricDescriptionList[0] : '--', delay: 200 }">
                  {{scope.row.metricDescriptionList ? scope.row.metricDescriptionList[0] : '--'}}
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.updator.checked"
              :label="$t('更新记录')" width="150">
              <template slot-scope="scope">
                <div class="col-name">
                  <div class="col-name-label">{{scope.row.updator || '--'}}</div>
                  <div>{{scope.row.updateTime || '--'}}</div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.enabled.checked"
              :label="$t('启/停')" width="70">
              <template slot-scope="scope">
                <div class="switch-wrap">
                  <bk-switcher
                    :key="scope.row.id"
                    v-model="scope.row.enabled"
                    size="small"
                    theme="primary"
                    @change="handleSwitchChange(scope.row)">
                  </bk-switcher>
                  <div v-if="!authority.MANAGE_AUTH"
                       v-authority="{ active: !authority.MANAGE_AUTH }"
                       class="switch-wrap-modal"
                       @click.stop.prevent="!authority.MANAGE_AUTH && handleShowAuthorityDetail()">
                  </div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="fieldSettingData.operator.checked"
              :label="$t('操作')" width="150">
              <template slot-scope="scope">
                <div class="col-operator">
                  <span
                    class="col-operator-btn"
                    v-authority="{ active: !authority.MANAGE_AUTH }"
                    @click="authority.MANAGE_AUTH ? handleEditStrategy(scope.row) : handleShowAuthorityDetail()">
                    {{ $t('编辑') }}
                  </span>
                  <span
                    class="col-operator-btn col-operator-adddel"
                    :class="{ 'col-operator-disabled': !scope.row.addAllowed }"
                    v-authority="{ active: !authority.MANAGE_AUTH }"
                    @click="authority.MANAGE_AUTH ? handleAddTarget(scope.row) : handleShowAuthorityDetail()">
                    {{ $t('增删目标') }}
                  </span>
                  <span class="col-operator-more"
                        v-authority="{ active: !authority.MANAGE_AUTH }"
                        @click="authority.MANAGE_AUTH ? handleOperatorOver(scope.row, $event, scope.$index) : handleShowAuthorityDetail()"
                        data-popover="true">
                    <i data-popover="true" class="bk-icon icon-more"></i>
                  </span>
                </div>
              </template>
            </bk-table-column>
          </bk-table>
          <template v-if="table.data && table.data.length">
            <bk-pagination
              v-show="tableInstance.total"
              class="strategy-pagination list-pagination"
              align="right"
              size="small"
              pagination-able
              :current="tableInstance.page"
              :limit="tableInstance.pageSize"
              :count="pageCount"
              :limit-list="tableInstance.pageList"
              @change="handlePageChange"
              @limit-change="handleLimitChange"
              show-total-count>
            </bk-pagination>
          </template>
        </div>
      </div>
    </div>
    <div v-show="false">
      <ul class="operator-group" ref="operatorGroup">
        <li v-if="!popover.data.shieldInfo.is_shielded" class="operator-group-btn" @click="handleShowStrategy"> {{ $t('快捷屏蔽') }} </li>
        <li v-else class="operator-group-btn" @click="handleDeleteShield"> {{ $t('解除屏蔽') }} </li>
        <li class="operator-group-btn" @click="handleDeleteRow"> {{ $t('删除') }} </li>
        <li class="operator-group-btn" @click="handleCopy"> {{ $t('克隆') }} </li>
      </ul>
    </div>
    <!-- <keep-alive> -->
    <strategy-config-dialog
      :loading="dialogLoading"
      :checked-list="idList"
      :group-list="groupList"
      :dialog-show="dialog.show"
      :set-type="header.value"
      @get-group-list="getGroupList"
      @confirm="handleMuchEdit"
      @hide-dialog="handleDialogChange">
    </strategy-config-dialog>
    <!-- </keep-alive> -->
    <AlarmShieldStrategy :is-show-strategy.sync="isShowStrategy" :strategy-id="strategyId"></AlarmShieldStrategy>
    <table-filter
      :filter-type="filterType"
      :show="isShowTableFilter"
      :target="label.target"
      :menu-list="dataSourceList"
      :radio-list="dataSourceList"
      :value="label.value"
      @selected="handleSelectedDataSource"
      @hide="handleChangeValue"
      @confirm="handleFilterDataSourece"
      @reset="handleResetSourceFilter(true)">
    </table-filter>
    <strategy-set-target
      v-if="targetSet.show"
      :dialog-show.sync="targetSet.show"
      :biz-id="targetSet.bizId"
      :strategy-id="targetSet.strategyId"
      :object-type="targetSet.objectType"
      :title="targetSet.title"
      @show-change="handleTargetShowChange"
      @targets-change="handleTargetsChange"
      @target-type-change="handleTargetTypeChange">
    </strategy-set-target>
  </div>
</template>
<script>
import TableStore from './store'
import { strategyConfigList, deleteStrategyConfig, bulkEditStrategy,
  cloneStrategyConfig, getScenarioList } from '../../../monitor-api/modules/strategies'
import { noticeGroupList } from '../../../monitor-api/modules/notice_group'
import StrategyConfigDialog from './strategy-config-dialog/strategy-config-dialog'
import TableFilter from '../../components/table-filter/table-filter'
import AlarmShieldStrategy from '../alarm-shield/quick-alarm-shield/quick-alarm-shield-strategy'
import { disableShield } from '../../../monitor-api/modules/shield'
import { debounce } from 'throttle-debounce'
import StrategySetTarget from './strategy-config-set/strategy-set-target/strategy-set-target'
import commonPageSizeMixin from '../../mixins/commonPageSizeMixin'
import authorityMixinCreate from '../../mixins/authorityMixin'
import * as ruleAuth from './authority-map'
import FilterPanel from './strategy-config-list/filter-panel.tsx'
import { handleMouseDown, handleMouseMove } from './util'

export default {
  name: 'StrategyConfig',
  components: {
    StrategyConfigDialog,
    AlarmShieldStrategy,
    TableFilter,
    StrategySetTarget,
    FilterPanel
  },
  mixins: [commonPageSizeMixin, authorityMixinCreate(ruleAuth)],
  props: {
    // 告警组回显
    noticeName: {
      type: String,
      default: ''
    },
    // 服务分类回显
    serviceCategory: {
      type: String,
      default: ''
    },
    // 拨测任务回显
    taskId: {
      type: [String, Number],
      default: ''
    },
    // IP回显
    ip: {
      type: String,
      default: ''
    },
    bkCloudId: {
      type: [String, Number],
      default: ''
    },
    // 自定义事件回显
    bkEventGroupId: {
      type: Number,
      default: 0
    },
    // 指标ID回显
    metricId: {
      type: String,
      default: ''
    },
    // 策略id [{ id: 12, name: 12 }, { id: 11, name: 11 }]
    bkStrategyId: {
      type: Array,
      default: null
    },
    // 数据来源
    dataSource: {
      type: Array,
      default: null
    }
  },
  data() {
    return {
      showFilterPanel: true,
      ruleAuth,
      dashboardValue: '',
      header: {
        value: 0,
        dropdownShow: false,
        list: [
          { id: 0, name: this.$t('修改告警组') },
          { id: 1, name: this.$t('修改触发条件') },
          { id: 5, name: this.$t('修改恢复条件') },
          { id: 2, name: this.$t('修改通知间隔') },
          // { id: 3, name: this.$t('修改无数据告警') },
          { id: 4, name: this.$t('修改告警恢复通知') },
          { id: 6, name: this.$t('启用/停用策略') },
          { id: 7, name: this.$t('删除策略') },
          { id: 9, name: this.$t('批量修改告警模板') },
          { id: 8, name: this.$t('增删目标') }
        ],
        keyword: '',
        keywordObj: [], // 搜索框绑定值
        condition: [], // 搜索条件接口参数
        conditionList: [], // 搜索可选项
        handleSearch() {}
      },
      dataSourceList: [
        {
          value: '',
          id: 'bk_monitor',
          checked: 'bk_monitor',
          cancel: '',
          name: this.$t('监控采集')
        },
        {
          value: '',
          id: 'log',
          checked: 'bk_monitor',
          cancel: '',
          name: this.$t('日志采集')
        }
      ],
      label: {
        target: null,
        isSelected: false,
        selectedLabels: '',
        serviceCategory: '',
        noticeName: ''
      },
      //   tab: {
      //     active: 0,
      //     list: []
      //   },
      popover: {
        instance: null,
        hover: -1,
        edit: false,
        status: '',
        data: {
          shieldInfo: {
            is_shielded: true
          }
        }
      },
      table: {
        data: [],
        loading: false,
        select: []
      },
      pageCount: 0,
      dialog: {
        show: false,
        selectList: []
      },
      tableInstance: {},
      loading: false,
      isShowStrategy: false,
      isShowTableFilter: false,
      isStrategyRoute: false,
      strategyId: 0,
      // 策略回显Map（key需要和props的保持一致）
      backDisplayMap: {
        bkStrategyId: {
          name: this.$t('策略ID'),
          value: [],
          id: 'strategy_id'
        },
        // 告警组
        noticeName: {
          name: this.$t('告警组'), // 输入框回显的名称
          value: this.noticeName, // 回显的值
          id: 'notice_group_name' // 传给后端的字段名
        },
        // 服务分类
        serviceCategory: {
          name: this.$t('服务分类'),
          value: this.serviceCategory,
          id: 'service_category'
        },
        // 拨测任务
        taskId: {
          name: this.$t('拨测任务ID'),
          value: this.taskId,
          id: 'task_id'
        },
        // 主机监控
        ip: {
          name: 'IP',
          value: this.ip,
          id: 'IP'
        },
        // 云区域id
        bkCloudId: {
          name: this.$t('云区域ID'),
          value: this.bkCloudId,
          id: 'bk_cloud_id'
        },
        // 自定义事件
        bkEventGroupId: {
          name: this.$t('分组ID'),
          value: this.bkEventGroupId,
          id: 'bk_event_group_id'
        },
        // 仪表盘
        metricId: {
          name: this.$t('指标ID'),
          value: this.metricId,
          id: 'metric_id'
        },
        metricAlias: {
          name: this.$t('指标别名'),
          value: '',
          id: 'metric_alias'
        },
        metricName: {
          name: this.$t('指标名'),
          value: '',
          id: 'metric_name'
        },
        creators: {
          name: this.$t('创建人'),
          value: '',
          id: 'creators'
        },
        updaters: {
          name: this.$t('修改人'),
          value: '',
          id: 'updaters'
        },
        strategyState: {
          name: this.$t('状态'),
          value: '',
          id: 'strategy_status',
          list: [
            {
              name: this.$t('告警中'),
              id: 'ALERT'
            },
            {
              name: this.$t('失效'),
              id: 'LEGACY'
            },
            {
              name: this.$t('停用'),
              id: 'OFF'
            },
            {
              name: this.$t('启用'),
              id: 'ON'
            }
          ]
        },
        dataSource: {
          name: this.$t('数据来源'),
          value: '',
          id: 'data_source_list',
          list: []
        },
        scenario: {
          name: this.$t('监控对象'),
          value: '',
          id: 'scenario',
          list: []
        },
        strategyLabels: {
          name: this.$t('标签'),
          value: '',
          id: 'label_name',
          list: []
        }
      },
      targetSet: {
        show: false,
        strategyId: '',
        bizId: '',
        objectType: '',
        title: this.$t('监控目标'),
        nodeType: ''
      },
      // 标签筛选俩表
      strategyLabelList: [],
      // 数据来源筛选列表
      sourceList: [],
      // 分类可筛选列表
      typeList: [],
      // 筛选列表类型
      filterType: 'checkbox',
      // 当前筛选类型
      curFilterType: this.$t('数据来源'),
      dialogLoading: false,
      // 告警组数据列表
      groupList: [],
      // 监控对象
      scenarioList: [],
      // 设置功能
      fieldSettingData: {
        id: {
          checked: true,
          disable: true,
          name: 'ID',
          id: 'id'
        },
        strategyName: {
          checked: true,
          disable: true,
          name: this.$t('策略名'),
          id: 'strategyName'
        },
        itemDescription: {
          checked: true,
          disable: false,
          name: this.$t('监控项'),
          id: 'itemDescription'
        },
        dataOrigin: {
          checked: false,
          disable: false,
          name: this.$t('数据来源'),
          id: 'dataOrigin'
        },
        target: {
          checked: true,
          disable: false,
          name: this.$t('监控目标'),
          id: 'target'
        },
        labels: {
          checked: true,
          disable: false,
          name: this.$t('标签'),
          id: 'labels'
        },
        noticeGroupList: {
          checked: true,
          disable: false,
          name: this.$t('告警组'),
          id: 'noticeGroupList'
        },
        updator: {
          checked: false,
          disable: false,
          name: this.$t('更新记录'),
          id: 'updator'
        },
        enabled: {
          checked: true,
          disable: true,
          name: this.$t('启/停'),
          id: 'enabled'
        },
        operator: {
          checked: true,
          disable: true,
          name: this.$t('操作'),
          id: 'operator'
        }
      },
      drapWidth: 214
    }
  },
  computed: {
    bizList() {
      return this.$store.getters.bizList
    },
    idList() {
      return this.table.select.map(item => item.id)
    },
    isSameObjectType() {
      const list = this.table.select
      return list.length
        && list.every((item, index) => {
          if (index === 0) return true

          const preItem = list[index - 1]
          return item.objectType === preItem.objectType
        })
    },
    // 筛选面板数据
    filterPanelData() {
      // 过滤需要展示的分组（监控对象、数据来源、告警组）
      const displayKeys = ['scenario', 'dataSource', 'noticeName', 'strategyLabels']
      return displayKeys.map((key) => {
        const { id, name, list } = this.backDisplayMap[key]
        return {
          id,
          name,
          data: key === 'noticeName' ? this.groupList.map(({ name, count }) => ({ id: name, name, count })) :  list
        }
      })
    }
  },
  watch: {
    'table.data': {
      handler: 'handleTableDataChange'
    },
    'strategyLabelList'(v) {
      if (v) {
        this.backDisplayMap.strategyLabels.list = v
        this.createdConditionList()
      }
    },
    'sourceList'(v) {
      if (v) {
        this.backDisplayMap.dataSource.list = v
        this.createdConditionList()
      }
    },
    'groupList'(v) {
      if (v) {
        this.backDisplayMap.noticeName.list = v.map(item => ({
          id: item.name,
          name: item.name
        }))
        this.createdConditionList()
      }
    }
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (![
        'strategy-config-edit',
        'strategy-config-add',
        'strategy-config-detail',
        'strategy-config-target'].includes(from.name)) {
        if (vm.tableInstance.setDefaultStore) {
          vm.tableInstance.setDefaultStore()
        }
        vm.header.keyword = ''
        // vm.handleClearQueryParam()
      }
      vm.CheckColInit()
      vm.handleSetDashboard()
      // 判断是否需要重置页数
      //   const resetPage = Object.keys(vm.backDisplayMap).some(key => !!vm.backDisplayMap[key].value)
      //   const page = resetPage ? 1 : vm.tableInstance.page
      vm.handleSearchBackDisplay()
      vm.handleGetListData(true, 1)
      vm.getGroupList()
    })
  },
  beforeRouteLeave(to, from, next) {
    // 离开页面清空groupList
    this.groupList = []
    this.isStrategyRoute = [
      'strategy-config-edit',
      'strategy-config-add',
      'strategy-config-detail',
      'strategy-config-target'].includes(to.name)
    next()
  },
  created() {
    this.header.handleSearch = debounce(300, () => {
      this.handleGetListData(false, 1)
    })
    this.createdConditionList()
  },
  methods: {
    // 表格设置
    CheckColInit() {
      let fieldSettingData = localStorage.getItem('strategy_config_setting')
      if (fieldSettingData) {
        fieldSettingData = JSON.parse(fieldSettingData)
        fieldSettingData.forEach((item) => {
          this.fieldSettingData[item.id].checked = item.checked
        })
      }
    },
    handleCheckColChange(item) {
      this.fieldSettingData[item.id].checked = !item.checked
      const result = Object.keys(this.fieldSettingData).map(key => (
        { id: key, checked: this.fieldSettingData[key].checked }
      ))
      localStorage.setItem('strategy_config_setting', JSON.stringify(result))
    },
    async handleHeaderDragend(newWidth, oldWidth, column) {
      if (column.label === this.$t('告警组') || column.label === this.$t('标签')) {
        await this.$nextTick()
        this.handleTableDataChange(this.table.data)
      }
    },
    // 回显搜索条件
    handleSearchBackDisplay() {
      const temp = []
      const map = this.backDisplayMap
      Object.keys(map).forEach((key) => {
        if (this[key]) {
          temp.push({
            id: map[key].id,
            name: map[key].name,
            values: Array.isArray(this[key])
              ? this[key].map(item => ({ id: item.id, name: item.name }))
              : [{ id: this[key], name: this[key] }]
          })
        }
      })
      this.header.keywordObj = temp
    },
    // 处理搜索条件
    handleSearchCondition(data = this.header.keywordObj) {
      const res = []
      data.forEach((item) => {
        const temp = {
          key: item.values ? item.id : 'query',
          value: item.values ? item.values.map(val => val.id) : item.id
        }
        res.push(temp)
      })
      this.header.condition = res
    },
    // 创建搜索可选列表
    createdConditionList() {
      const res = []
      const map = this.backDisplayMap
      Object.keys(map).forEach((key) => {
        const { name, id, list } = map[key]
        if (id === 'scenario') {
          const resChildren = []
          list.forEach((listItem) => {
            if (listItem.children) {
              listItem.children.forEach((item) => {
                resChildren.push(item)
              })
            }
          })
          res.push({
            name,
            id,
            multiable: true,
            children: resChildren ? resChildren : []
          })
        } else {
          res.push({
            name,
            id,
            multiable: true,
            children: list ? list : []
          })
        }
      })
      this.conditionList = res
    },
    /**
   * 初始化查询参数
   * @param {String} metricId（指标ID有可能从sessionStorage中来）
   */
    handleInitQueryParams(metricId) {
      Object.keys(this.backDisplayMap).forEach((key) => {
        // 判断props中是否存在该属性
        if (metricId && key === 'metricId') {
          this.backDisplayMap[key].value = metricId
          const index = this.header.keywordObj.findIndex(item => item.id === this.backDisplayMap[key].id)
          if (index > 0) {
            this.header.keywordObj[index].values = [{ id: metricId, name: metricId }]
          } else {
            this.header.keywordObj[index] = {
              id: this.backDisplayMap.metricId.id,
              name: this.backDisplayMap.metricId.name,
              values: [{ id: metricId, name: metricId }]
            }
          }
        }
      })
    },
    handleSetDashboard() {
      let metricId = this.$route.query.metricId || sessionStorage.getItem('__dashboard-Metric-Id__')
      if (metricId) {
        metricId = metricId.replace(/"/gmi, '')
        sessionStorage.removeItem('__dashboard-Metric-Id__')
      }
      this.handleInitQueryParams(metricId)
    },
    getTargetString(tableData) {
      const textMap = {
        TOPO: `${this.$t('个')}${this.$t('节点')}`,
        SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
        SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
      }
      tableData.forEach((item) => {
        if (item.objectType === 'HOST') {
          if (['SERVICE_TEMPLATE', 'SET_TEMPLATE', 'TOPO'].includes(item.targetNodeType)) {
            // eslint-disable-next-line vue/max-len
            item.target = `${item.targetNodesCount}${textMap[item.targetNodeType]} （${this.$t('共')} ${item.totalInstanceCount} ${this.$t('台主机')}）`
          } else if (item.targetNodeType === 'INSTANCE') {
            item.target = ` ${item.totalInstanceCount} ${this.$t('台主机')}`
          }
        } else if (item.objectType === 'SERVICE') {
          if (['SERVICE_TEMPLATE', 'SET_TEMPLATE', 'TOPO'].includes(item.targetNodeType)) {
            // eslint-disable-next-line vue/max-len
            item.target = `${item.targetNodesCount}${textMap[item.targetNodeType]} （${this.$t('共')} ${item.totalInstanceCount} ${this.$t('个实例')}）`
          }
        }
      })
      return tableData
    },
    setTableFilterSelect(filterType) {
      this.curFilterType = filterType
      const displayMap = this.backDisplayMap
      const mapKeys = Object.keys(displayMap)
      const keyMap = {
        [this.$t('数据来源')]: () => (mapKeys.find(key =>  displayMap[key].name === filterType)),
        [this.$t('告警组')]: () => (mapKeys.find(key =>  displayMap[key].name === filterType))
      }
      // const backDisplayMapKey = keyMap[filterType]()
      const searchKey = displayMap[keyMap[filterType]()].id
      const res = this.header.keywordObj.find(item => item.id === searchKey)
      if (res) {
        this.handleFilterDataSourece(res.values.map(item => item.id), false)
      } else {
        this.handleResetSourceFilter(false)
      }
    },
    handleGetListData(needLoading = false, defPage, defPageSize) {
      this.setTableFilterSelect(this.$t('数据来源'))
      this.setTableFilterSelect(this.$t('告警组'))
      this.handleSearchCondition()
      this.loading = needLoading
      this.table.loading = !needLoading
      this.table.data = []
      const page = defPage || this.tableInstance.page || 1
      const pageSize = defPageSize || this.tableInstance.pageSize || this.handleGetCommonPageSize()
      const params = {
        page,
        page_size: pageSize,
        // search: this.header.keyword,
        conditions: this.header.condition,
        // data_source_list: this.label.selectedLabels || [],
        order_by: '-update_time'
        // service_category: this.label.serviceCategory
      }

      //   if (this.tab.active > 0) {
      //     params.scenario = this.tab.list[this.tab.active].id
      //   }
      strategyConfigList(params).then(async (data) => {
        // this.getTypeFilterList(data.service_category_list)
        this.tableInstance = new TableStore(data.strategy_config_list, this.bizList)
        this.tableInstance.page = page
        this.tableInstance.pageSize = pageSize
        this.tableInstance.keyword = this.header.keyword
        const tableData = this.tableInstance.getTableData()
        this.table.data = this.getTargetString(tableData)
        this.handleTableDataChange(this.table.data)
        const total = await this.handelScenarioList(data)
        // todo
        this.pageCount = total
        // this.pageCount = this.tab.active > 0 ? this.tab.list[this.tab.active].count : total
        this.sourceList = data.data_source_list.map((item) => {
          const { type, name, count } = item
          return { id: type, name, count: count ? count : 0 }
        }).sort((pre, next) => (next.count - pre.count))
        this.strategyLabelList = data.strategy_label_list.map((item) => {
          const { id, count } = item
          return { id, count, name: item.label_name }
        }).sort((pre, next) => (next.count - pre.count))
        this.groupList = data.notice_group_list.map((item) => {
          const { count } = item
          return { count, name: item.notice_group_name, id: item.notice_group_id }
        }).sort((pre, next) => (next.count - pre.count))
        this.$refs.strategyTable.doLayout()
      })
        .finally(() => {
          this.loading = false
          this.table.loading = false
        })
    },
    // 监控对象处理
    async handelScenarioList(data) {
      // let total = 0
      // this.backDisplayMap.scenario.list = data.scenario_list.map((item) => {
      //   total += item.count
      //   return { name: item.display_name, id: item.id, count: item.count }
      // })
      // return total
      if (this.scenarioList.length === 0) {
        this.scenarioList = await getScenarioList().catch(() => ([]))
      }
      let total = 0
      const scenarioFather = this.scenarioList.map((item) => {
        const { name, id, index } = item
        return { name, id, sort: `${index}`, children: [], count: 0 }
      })
      const scenarioList = data.scenario_list.map(item => ({ ...item, sort_msg: (`${item.sort_msg}`).split('.') }))
      scenarioFather.forEach((item) => {
        let count = 0
        item.children = scenarioList.filter(scenario => (scenario.sort_msg[0] === item.sort)).map((opt) => {
          count += opt.count
          total += opt.count
          return { name: opt.display_name, id: opt.id, count: opt.count }
        })
        item.count = count
      })
      this.backDisplayMap.scenario.list = scenarioFather
      return total
    },
    handleTableDataChange(v) {
      setTimeout(() => {
        v.forEach((item, index) => {
          const ref = this.$refs[`table-row-${index}`]
          item.overflow = ref && ref.clientHeight > 32
          const refLabel = this.$refs[`table-labels-${index}`]
          item.overflowLabel = refLabel && refLabel.clientHeight > 32
        })
      }, 50)
    },
    handlePageChange(page) {
      this.handleGetListData(false, page)
    },
    handleLimitChange(limit) {
      this.handleSetCommonPageSize(limit)
      this.handleGetListData(false, 1, limit)
    },
    handleHeadSelectChange(v) {
      // 批量增删目标
      if (v === 8) {
        // 增删目标禁用状态
        if (!this.isSameObjectType) return

        this.targetSet.show = true
        this.targetSet.objectType = this.table.select[0].objectType
        this.targetSet.title = this.$t('批量增删目标')
        this.targetSet.strategyId = ''
      } else {
        this.header.value = v
        this.dialog.show = true
      }
    },
    handleTargetTypeChange(nodeType) {
      this.targetSet.nodeType = nodeType
    },
    // 批量编辑监控目标
    async handleTargetsChange(targets) {
      // 修改单条策略时不走此处逻辑
      if (this.targetSet.strategyId) return

      let field = ''
      const hostTargetFieldType = {
        TOPO: 'host_topo_node',
        INSTANCE: 'ip',
        SERVICE_TEMPLATE: 'host_service_template',
        SET_TEMPLATE: 'host_set_template'
      }
      const serviceTargetFieldType = {
        TOPO: 'service_topo_node',
        SERVICE_TEMPLATE: 'service_service_template',
        SET_TEMPLATE: 'service_set_template'
      }
      if (this.targetSet.objectType === 'HOST') {
        field = hostTargetFieldType[this.targetSet.nodeType]
      } else {
        field = serviceTargetFieldType[this.targetSet.nodeType]
      }
      if (!field) return

      const params = {
        id_list: this.table.select.map(item => item.id),
        edit_data: {
          target: [[{
            field,
            method: 'eq',
            value: this.handleSelectorData(this.targetSet.nodeType, targets)
          }]]
        }
      }
      const success = await bulkEditStrategy(params).catch(() => false)
      success && this.$bkMessage({ theme: 'success', message: this.$t('修改成功') })
      this.handleGetListData(true)
    },
    // 精简数据给到后端
    handleSelectorData(type, data) {
      const checkedData = []
      if (type === 'INSTANCE') {
        data.forEach((item) => {
          checkedData.push({
            ip: item.ip,
            bk_cloud_id: item.bk_cloud_id,
            bk_supplier_id: item.bk_supplier_id
          })
        })
      } else {
        data.forEach((item) => {
          checkedData.push({
            bk_inst_id: item.bk_inst_id,
            bk_obj_id: item.bk_obj_id
          })
        })
      }
      return checkedData
    },
    // handleTabChange(index) {
    //   if (this.tab.active !== index) {
    //     this.tab.active = index
    //     this.handleGetListData(false, 1)
    //   }
    // },
    handleOperatorOver(data, e, index) {
      if (this.popover.index === index) {
        return
      }
      this.popover.hover = index
      this.popover.edit = data.needUpdate
      this.popover.status = data.status
      this.popover.data = data
      if (!this.popover.instance) {
        this.popover.instance = this.$bkPopover(e.target, {
          content: this.$refs.operatorGroup,
          arrow: false,
          trigger: 'manual',
          placement: 'bottom',
          theme: 'light common-monitor',
          maxWidth: 520,
          duration: [275, 0],
          onHidden: () => {
            this.popover.instance.destroy()
            this.popover.hover = -1
            this.popover.instance = null
          }
        })
      } else {
        this.popover.instance.reference = e.target
      }
      this.popover.instance && this.popover.instance.show(100)
    },
    handleDialogChange(v) {
      this.dialog.show = v
    },
    handleMuchEdit(v) {
      this.loading = true
      const { idList } = this
      if (this.header.value === 7) {
        deleteStrategyConfig({ ids: idList }).then(() => {
          this.$bkMessage({ theme: 'success', message: this.$t('批量删除成功') })
          this.handleGetListData(false, 1)
        })
          .catch(() => {
            this.loading = false
          })
      } else {
        bulkEditStrategy({ id_list: idList, edit_data: { ...v } }).then(() => {
          const msg = {
            0: this.$t('批量修改告警组成功'),
            1: this.$t('批量修改触发条件成功'),
            2: this.$t('批量修改通知间隔成功'),
            3: this.$t('批量修改无数据告警成功'),
            4: this.$t('批量修改告警恢复通知成功'),
            5: this.$t('批量修改恢复条件成功'),
            6: '',
            9: this.$t('批量修改告警模板成功')
          }
          this.handleGetListData()
          if (this.header.value === 6) {
            msg[6] = v.is_enabled ? this.$t('批量启用策略成功') : this.$t('批量停用策略成功')
          }
          this.$bkMessage({ theme: 'success', message: msg[this.header.value], ellipsisLine: 0 })
        })
          .catch(() => {
            this.loading = false
          })
      }
    },
    handleSwitchChange(v) {
      if (!this.authority.MANAGE_AUTH) {
        v.enabled = !v.enabled
        this.handleShowAuthorityDetail()
        return
      }
      if (!v.enabled) {
        this.$bkInfo({
          title: this.$t('请确认是否停用'),
          confirmFn: () => {
            this.loading = true
            this.$nextTick(() => {
              bulkEditStrategy({ id_list: [v.id], edit_data: { is_enabled: v.enabled } }).then(() => {
                this.handleGetListData(true)
                this.$bkMessage({ theme: 'success', message: this.$t('停用成功') })
              })
                .catch(() => {
                  v.enabled = !v.enabled
                  this.loading = false
                })
            })
          },
          cancelFn: () => {
            v.enabled = !v.enabled
          }
        })
      } else {
        this.loading = true
        bulkEditStrategy({ id_list: [v.id], edit_data: { is_enabled: v.enabled } }).then(() => {
          this.handleGetListData(true)
          this.$bkMessage({ theme: 'success', message: this.$t('启用成功') })
        })
          .catch(() => {
            v.enabled = !v.enabled
            this.loading = false
          })
      }
    },
    handleDeleteRow() {
      this.$bkInfo({
        type: 'warning',
        title: this.$t('确认要删除？'),
        maskClose: true,
        escClose: true,
        confirmFn: () => {
          this.loading = true
          deleteStrategyConfig({ id: this.popover.data.id }).then(() => {
            this.table.loading = false
            this.$bkMessage({ theme: 'success', message: this.$t('删除成功') })
            this.handleGetListData(false, 1)
          })
            .catch(() => {
              this.loading = false
            })
        }
      })
    },
    // 拷贝策略
    handleCopy() {
      this.loading = true
      cloneStrategyConfig({ id: this.popover.data.id }).then(() => {
        this.$bkMessage({ theme: 'success', message: this.$t('克隆成功') })
        this.handleGetListData(false, 1)
      })
        .catch(() => {
          this.loading = false
        })
    },
    handleAddStategyConfig() {
    //   const tabItem = this.tab.list[this.tab.active]
    //   this.$router.push({
    //     name: 'strategy-config-add',
    //     params: {
    //       objectId: tabItem && tabItem.id !== 'ALL' ? tabItem.id : ''
    //     }
    //   })
      this.$router.push({
        name: 'strategy-config-add',
        params: {
          objectId: ''
        }
      })
    },
    // 点击增删目标触发
    handleAddTarget({ addAllowed, id, objectType }) {
      if (addAllowed) {
        this.targetSet.show = true
        this.targetSet.strategyId = id
        this.targetSet.objectType = objectType
        this.targetSet.title = this.$t('监控目标')
      }
    },
    // 增删目标显示变化触发
    handleTargetShowChange(v) {
      this.targetSet.show = v
      this.handleGetListData(true)
    },
    handleOpenStategydetail(item) {
      this.$router.push({
        name: 'strategy-config-detail',
        params: {
          title: item.strategyName,
          id: item.id
        }
      })
    },
    handleSelectionChange(selection) {
      this.table.select = selection
    },
    handleEditStrategy(data) {
      this.$router.push({
        name: 'strategy-config-edit',
        params: {
          id: data.id
        }
      })
    },
    handleShowStrategy() {
      this.isShowStrategy = true
      this.strategyId = this.popover.data.id
    },
    handleDeleteShield() {
      const { id } = this.popover.data.shieldInfo
      this.$bkInfo({
        title: this.$t('是否解除该屏蔽?'),
        confirmFn: () => {
          this.loading = true
          disableShield({ id }).then(() => {
            this.handleGetListData()
            this.$bkMessage({ theme: 'success', message: this.$t('解除屏蔽成功') })
          })
            .catch(() => {
              this.loading = false
            })
        }
      })
    },
    // handleGetActiveIndex(id) {
    //   const index = this.tab.list.findIndex(item => item.id === id)
    //   return index > 0 ? index : 0
    // },
    handleSelectedDataSource(v) {
      this.label.isSelected = Boolean(v.length)
    },
    setHeaderKeyword(value) {
      const displayMap = this.backDisplayMap
      const mapKeys = Object.keys(displayMap)
      const keyMap = {
        [this.$t('数据来源')]: () => (mapKeys.find(key =>  displayMap[key].name === this.curFilterType)),
        [this.$t('告警组')]: () => (mapKeys.find(key =>  displayMap[key].name === this.curFilterType))
      }
      const backDisplayMapKey = keyMap[this.curFilterType]()
      const searchKey = displayMap[keyMap[this.curFilterType]()].id
      const hasKey = this.header.keywordObj.find(item => item.id === searchKey)
      const { list } = displayMap[backDisplayMapKey]
      const name = this.curFilterType
      if (value) {
        const values = value.map(item => ({
          id: item,
          name: list ? list.find(set => set.id === item).name : item
        }))
        const obj = {
          id: searchKey,
          multiable: true,
          name,
          values
        }
        if (hasKey) {
          const index = this.header.keywordObj.findIndex(item => item.id === searchKey)
          this.header.keywordObj.splice(index, 1, obj)
        } else {
          this.header.keywordObj.push(obj)
        }
      } else {
        const index = this.header.keywordObj.findIndex(item => item.id === searchKey)
        this.header.keywordObj.splice(index, 1)
      }
    },
    handleFilterDataSourece(labels, needSetSearch = true) {
      // 更新搜索条件
      const listMap = {
        [this.$t('数据来源')]: () => {
          this.label.selectedLabels = labels
          return labels
        },
        // [this.$t('分类')]: () => (this.label.serviceCategory = labels),
        [this.$t('告警组')]: () => {
          this.label.noticeName = labels
          return labels
        }
      }
      const value = listMap[this.curFilterType]()

      // 同步搜索框
      if (needSetSearch) {
        this.setHeaderKeyword(value)
        this.handleGetListData()
      }
    },
    handleResetSourceFilter(needSetSearch = true) {
      const listMap = {
        [this.$t('数据来源')]: () => (this.label.selectedLabels = []),
        // [this.$t('分类')]: () => (this.label.serviceCategory = ''),
        [this.$t('告警组')]: () => (this.label.noticeName = '')
      }
      listMap[this.curFilterType]()
      if (needSetSearch) {
        this.setHeaderKeyword(null)
        this.handleGetListData()
      }
    },
    /**
     * @description 显示数据来源的过滤面板
     */
    handleShowTableFilter(e, type, title) {
      this.filterType = type
      const listMap = {
        [this.$t('数据来源')]: {
          list: this.sourceList,
          value: this.label.selectedLabels
        },
        // [this.$t('分类')]: this.typeList,
        [this.$t('告警组')]: {
          list: this.groupList.map(item => ({
            id: item.name,
            name: item.name
          })),
          value: this.label.noticeName
        }
      }
      this.curFilterType = title
      this.dataSourceList = listMap[title].list
      this.label.target = e.target
      this.isShowTableFilter = !this.isShowTableFilter
      this.label.value = listMap[title].value
    },
    handleChangeValue() {
      this.isShowTableFilter = false
    },
    // 数据来源表头
    // renderHeader() {
    //   return this.renderHeaderTemplate(this.$t('数据来源'), 'checkbox', this.label.selectedLabels.length)
    // },
    // 分类表头
    // renderHeaderType() {
    //   return this.renderHeaderTemplate(this.$t('分类'), 'radio', this.label.serviceCategory)
    // },
    // 告警组表头
    // renderHeaderNoticeGroup() {
    //   return this.renderHeaderTemplate(this.$t('告警组'), 'checkbox', this.label.noticeName.length)
    // },
    renderHeaderTemplate(title, type, active) {
      if (!this.typeList.length && title === this.$t('分类')) {
        return title
      }
      // eslint-disable-next-line vue-i18n/no-dynamic-keys
      const titleStr = this.$t(title)
      return <span
        onClick={e => this.handleShowTableFilter(e, type, title)}
        class={{ 'dropdown-trigger': true, ' plugin-label': true, selected: active }}
        slot="dropdown-trigger">
        {titleStr}
        <i class="icon-monitor icon-filter-fill"></i>
      </span>
    },
    // 获取分类的筛选列表
    // getTypeFilterList(allList) {
    //   allList.filter(item => item.bk_parent_id === 0).forEach((firstItem) => {
    //     const firstName = firstItem.name
    //     allList.forEach((secondItem) => {
    //       const secondName = secondItem.name
    //       firstItem.id === secondItem.bk_parent_id && this.typeList.push(`${firstName}-${secondName}`)
    //     })
    //   })
    //   // 去重
    //   this.typeList = [...new Set(this.typeList)]
    // },
    // 获取告警组列表
    async getGroupList() {
      // 有数据缓存则不请求数据
      if (this.groupList.length) return
      this.dialogLoading = true
      await noticeGroupList().then((data) => {
        this.groupList = data.map(item => ({
          id: item.id,
          name: item.name,
          count: item.related_strategy
        })).sort((pre, next) => (next.count - pre.count))
      })
      this.dialogLoading = false
    },
    handleToEventCenter(item) {
      this.$router.push({
        name: 'event-center',
        params: {
          strategyName: item.strategyName,
          strategyId: item.id,
          status: 'ABNORMAL'
        }
      })
    },
    // 筛选面板勾选change事件
    handleSearchSelectChange(data = []) {
      data.forEach((item) => {
        const obj = this.header.keywordObj.find(obj => obj.id === item.id)
        const index = this.header.keywordObj.findIndex(obj => obj.id === item.id)
        if (obj) {
          const values = item.values || []
          values.length === 0 ? this.header.keywordObj.splice(index, 1) : obj.values = values
          // values.forEach((value) => {
          //   const index = (obj.values || []).findIndex(objValue => objValue.id === value.id)
          //   index === -1 && obj.values && obj.values.push(value)
          // })
        } else {
          this.header.keywordObj.push(item)
        }
      })
      this.handleGetListData(false, 1)
    },
    handleShowFilterPanel() {
      this.drapWidth = 214
      this.showFilterPanel = true
    },
    handleMouseDown(e) {
      handleMouseDown(e, 'resizeTarget', 114, { min: 214, max: 500 }, (width) => {
        this.showFilterPanel = width !== 0
        this.drapWidth = width
      })
    },
    handleMouseMove(e) {
      handleMouseMove(e)
    }
  }
}
</script>
<style lang="scss" scoped>
@import "../home/common/mixins";

@mixin basecontent {
  background: #fff;
  border-radius: 2px;
  box-shadow: 0px 1px 2px 0px rgba(0,0,0,.05);
}

.strategy-config {
  font-size: 12px;
  height: 100%;
  .content {
    height: 100%;
    min-height: calc(100vh - 90px);
    display: flex;
    &-left {
      position: relative;
      margin-right: 8px;
      &-filter {
        height: 100%;
        padding: 24px 16px;

        @include basecontent;
      }
      &-drag {
        position: absolute;
        right: -3px;
        top: calc(50% - 50px);
        width: 6px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-items: center;
        background-color: #dcdee5;
        border-radius: 3px;
        z-index: 2;
        &::after {
          content: " ";
          height: 80px;
          width: 0;
          border-left: 2px dotted white;
          position: absolute;
          left: 2px;
        }
        &:hover {
          cursor: col-resize;
        }
      }
    }
    &-right {
      width: 0;
      flex: 1;
      // padding: 20px;
      padding: 0 20px 20px 20px;
      overflow-y: auto;

      @include basecontent;
    }
  }
  &-header {
    top: 0;
    width: 100%;
    padding: 20px 0 16px 0;
    opacity: 1;
    background: rgb(255, 255, 255);
    position: sticky;
    z-index: 5;
    display: flex;
    .badge {
      display: flex;
      margin-right: 16px;
      width: 24px;
      /deep/ .bk-badge {
        top: 8px;
        right: 2px;
      }
    }
    .folding {
      transform: rotate(90deg);
      display: inline-block;
      cursor: pointer;
      i {
        font-size: 24px;
        color: #979ba5;
      }
    }
    .header-btn {
      margin-right: 10px;
    }
    .header-search {
      margin-left: 14px;
      flex: 1;
      width: 360px;
      /deep/.bk-search-select {
        background: #fff;
      }
    }
    .header-select {
      color: #63656e;
      &-btn {
        background: #fff;
        display: flex;
        align-items: center;
        border-radius: 2px;
        border: 1px solid #c4c6cc;
        padding: 0 12px;
        height: 32px;
        cursor: pointer;
        .icon-monitor {
          color: #979ba5;
          margin-left: 4px;
          font-size: 22px;
        }
        &.btn-disabled {
          background: #fafafa;
          cursor: not-allowed;
          color: #c4c6cc;
          .icon-monitor {
            color: #c4c6cc;
          }
        }
      }
      &-list {
        display: flex;
        width: 220px;
        flex-direction: column;
        .list-item {
          flex: 0 0 32px;
          display: flex;
          align-items: center;
          padding-left: 15px;
          &:hover {
            background: #e1ecff;
            color: #3a84ff;
            cursor: pointer;
          }
          &.disabled {
            cursor: not-allowed;
            color: #c4c6cc;
          }
        }
      }
    }
  }
  &-wrap {
    border-radius: 2px;
    background: #fff;
    position: relative;
    .config-wrap-setting {
      position: absolute;
      top: 2px;
      right: 0;
      width: 40px;
      height: 40px;
      background: #f5f6fa;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1;
      border-left: 1px solid #e7e8ed;
      .setting-btn {
        position: relative;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .icon-menu-set {
        position: relative;
        top: 1px;
        font-size: 12px;
        color: #979ba5;
      }
      &:hover {
        cursor: pointer;
        background: #f0f1f5;
      }
    }
    // @include border-1px();
    .tab-list {
      display: flex;
      flex-direction: row;
      justify-content: flex-start;
      align-items: center;
      line-height: 60px;
      padding: 0;
      margin: 0;
      font-size: 14px;
      &-item {
        padding: 0 10px;
        min-width: 120px;
        // border-right: 1px solid #dcdee5;
        // border-bottom: 1px solid #dcdee5;
        text-align: center;
        .tab-num {
          font-size: 12px;
          color: #fff;
          display: inline-block;
          padding: 2px 5px;
          background: #c4c6cc;
          line-height: 10px;
          border-radius: 8px;
        }
        &.tab-active {
          position: relative;
          color: #3a84ff;
          background: #fff;
          border-bottom-color: transparent;
          &:after {
            content: "";
            position: absolute;
            bottom: -1px;
            top: auto;
            left: 50%;
            transform: translateX(-50%);
            height: 2px;
            width: 80px;
            background-color: #3a84ff;
            z-index: 1;
          }
          // border-bottom: 1px solid #3a84ff;
          .tab-num {
            background: #3a84ff;
          }
        }
        &:hover {
          cursor: pointer;
          color: #3a84ff;
        }
      }
      &-blank {
        flex: 1 1 auto;
        height: 60px;
        // border-bottom: 1px solid #dcdee5;
      }
    }
    .strategy-table {
      border-left: 0;
      border-right: 0;
      /deep/ .cell {
        color: #63656e;
        label {
          margin: 0px;
        }
      }
      /deep/ .label-title {
        .cell {
          padding: 0;
        }
        span {
          padding: 0 15px;
        }
      }
      .switch-wrap {
        position: relative;
        &-modal {
          position: absolute;
          left: 0;
          right: 0;
          top: 0;
          bottom: 0;
          background: transparent;
          z-index: 29;
          &:hover {
            cursor: pointer;
          }
        }
      }
      .plugin-label {
        display: inline-block;
        width: 100%;
        cursor: pointer;
        &.selected {
          color: #3a84ff;
        }
        .bk-icon {
          margin-left: 6px;
        }
      }
      .icon-filter-fill {
        margin-left: 6px;
      }
      .col-name {
        height: 58px;
        display: flex;
        justify-content: center;
        flex-direction: column;
        &-desc {
          display: flex;
          color: #3a84ff;
          font-weight: bold;
          margin-bottom: 3px;
          cursor: pointer;
          &-text {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .icon-monitor {
            margin-left: 5px;
          }
        }
        &-type {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        &-label {
          margin-bottom: 3px;
        }
        .icon-sunhuai {
          font-size: 14px;
          color: #ffb848;
        }
        .icon-gaojing1 {
          font-size: 14px;
          color: #ea3636;
        }
      }
      .col-classifiy {
        height: 30px;
        position: relative;
        &-wrap {
          overflow: hidden;
          margin-right: 25px;
          .classifiy-label {
            height: 24px;
            line-height: 24px;
            padding: 0 5px;
            border: 1px solid #dcdee5;
            border-radius: 2px;
            background: #fafbfd;
            font-size: 12px;
            float: left;
            margin: 3px;
            &.gray {
              padding: 0 11px;
              background: #f0f1f5;
              border: 0px;
            }
            &:first-child {
              margin-left: 0;
            }
            .label-name {
              display: inline-block;
              height: 24px;
              line-height: 24px;
              padding: 0 7px;
              text-align: center;
              &:first-child {
                border-right: 1px solid #dcdee5;
                background: #fff;
              }
            }
          }
          .classifiy-overflow {
            position: absolute;
            top: 0;
            border: 1px solid #dcdee5;
            border-radius: 2px;
            background: #fafbfd;
            font-size: 12px;
            padding: 3px 7px;
            margin: 3px;
            height: 24px;
            &.gray {
              background: #f0f1f5;
              border: 0px;
            }
            &.count {
              width: 28px;
              line-height: 24px;
              text-align: center;
              padding: 0;
            }
          }
        }
      }
      .col-operator {
        display: flex;
        align-items: center;
        .btn-disabled {
          color: #c4c6cc;
          cursor: not-allowed;
          &:hover {
            background: transparent;
            cursor: not-allowed;
          }
          i {
            color: #c4c6cc;

          }
        }
        &-btn {
          color: #3a84ff;
          cursor: pointer;
          margin-right: 12px;
        }
        &-adddel {
          margin-right: 0;
        }
        &-disabled {
          color: #c4c6cc;
          cursor: not-allowed;
        }
        &-more {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          margin-left: 12px;
          .icon-more {
            color: #3a84ff;
            font-size: 14px;
          }
          &:hover {
            background: #ddd;
            cursor: pointer;
          }
          &.operator-active {
            background: #ddd;
          }
        }
      }
      // .col-operator {
      //     display: flex;
      //     align-items: center;
      //     .btn-disabled {
      //         color: #C4C6CC;
      //         cursor: not-allowed;
      //     }
      //     &-btn {
      //         color: #3A84FF;
      //         cursor: pointer;
      //         margin-right: 12px;
      //     }
      // }
      &:after {
        width: 0;
      }
    }
    .strategy-pagination {
      margin: 16px 15px 0 15px;
    }
  }
  /deep/ .bk-table::before {
    height: 0;
  }
  /deep/ .bk-table th {
    background-color: #f5f6fa;
  }
  /deep/ .bk-table-header-label .dropdown-trigger {
    display: flex;
    align-items: center;
    .icon-monitor {
      font-size: 14px;
    }
  }
}
.operator-group {
  display: flex;
  flex-direction: column;
  width: 68px;
  color: #63656e;
  font-size: 12px;
  border: 1px solid #dcdee5;
  padding: 6px 0;
  &-btn {
    flex: 1;
    display: flex;
    align-items: center;
    padding-left: 10px;
    height: 32px;
    line-height: 32px;
    background: #fff;
    &:hover {
      background: #e1ecff;
      color: #3a84ff;
      cursor: pointer;
    }
    &.btn-disabled {
      cursor: not-allowed;
      color: #c4c6cc;

      /* stylelint-disable-next-line declaration-no-important */
      background: #fff !important;
    }
  }
}
.tool-popover {
  margin: -7px -14px;
  color: #63656e;
  &-title {
    color: #444;
    font-size: 24px;
    line-height: 32px;
    margin: 15px 24px 0;
  }
  &-content {
    padding: 0;
    margin: 15px 20px 22px 24px;
    display: flex;
    flex-flow: row;
    flex-wrap: wrap;
    align-items: center;
    &-item {
      max-width: 200px;
      flex-flow: 0;
      flex-shrink: 0;
      flex-basis: 33.33%;
      margin: 8px 0;

      @include ellipsis;
      /deep/ .bk-form-checkbox {
        margin-bottom: 0;
        .bk-checkbox {
          &::after {
            box-sizing: content-box;
          }
        }
        .bk-checkbox-text {
          width: 130px;

          @include ellipsis;
        }
      }
    }
  }
}
</style>
