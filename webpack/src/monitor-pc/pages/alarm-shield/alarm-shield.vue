<template>
  <div class="strategy-list-wrapper" v-monitor-loading="{ 'isLoading': loading }">
    <div class="top-container">
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH }"
        class="left mc-btn-add"
        theme="primary"
        @click="authority.MANAGE_AUTH ? handleAddShield() : handleShowAuthorityDetail()">
        {{ $t('新建') }}
      </bk-button>
      <div class="right">
        <bk-date-picker
          :placeholder="$t('选择屏蔽时间范围')"
          format="yyyy-MM-dd HH:mm:ss"
          v-model="right.dateRange"
          type="datetimerange"
          @clear="handleClearDate"
          @open-change="handleHideDatePicker"
          @pick-success="handleDateRangeChange">
        </bk-date-picker>
        <bk-input :placeholder="$t('请输入屏蔽内容、ID')"
                  v-model="right.keyword"
                  right-icon="bk-icon icon-search"
                  @change="handleSearch">
        </bk-input>
      </div>
    </div>
    <div class="content-wrapper">
      <ul class="tab-list">
        <li class="tab-list-item" v-for="(item, index) in tab.list"
            @click="handleTabChange(index)"
            :key="item.name"
            :class="{ 'tab-active': index === tab.active }">
          <span class="tab-name">{{item.name}}</span>
        </li>
        <li class="tab-list-blank"></li>
      </ul>
      <div v-bkloading="{ isLoading: table.loading }">
        <!-- 屏蔽中 -->
        <bk-table v-show="tab.active === 0"
                  class="shield-table"
                  :empty-text="$t('查询无数据')"
                  :data="table.data"
                  @sort-change="handleSort">
          <bk-table-column width="100" sortable="custom" label="ID" prop="id" v-slot="scope">
            <span class="shield-id" @click="handleToDetail(scope.row.id)">#{{scope.row.id}}</span>
          </bk-table-column>
          <bk-table-column width="150" class="shield-type" :render-header="renderHeader" prop="shieldTypeName">
          </bk-table-column>
          <bk-table-column min-width="250" class-name="shield-content" :label="$t('屏蔽内容')" v-slot="scope">
            <!-- <span v-if="scope.row.shieldType === 'strategy'" class="link">{{scope.row.shieldContent}}<i class="icon-monitor icon-mc-wailian" @click="handleToOtherPages(scope.row)"></i></span> -->
            <span class="content">{{scope.row.shieldContent}}</span>
          </bk-table-column>
          <bk-table-column v-if="!tab.active" min-width="150" :label="$t('开始时间')" prop="beginTime" sortable="custom"></bk-table-column>
          <bk-table-column v-if="!tab.active" min-width="150" :label="$t('持续周期及时长')" prop="cycleDuration"></bk-table-column>
          <bk-table-column min-width="230" :label="$t('屏蔽原因')" prop="description" v-slot="scope">
            <span class="content">{{scope.row.description || '--'}}</span>
          </bk-table-column>
          <bk-table-column width="120" :label="$t('操作')" v-slot="scope">
            <bk-button
              class="edit-btn"
              :text="true"
              theme="primary"
              v-authority="{ active: !authority.MANAGE_AUTH }"
              @click="authority.MANAGE_AUTH ? handleEditShield(scope.row.id, scope.row.shieldType) : handleShowAuthorityDetail()">
              {{ $t('编辑') }}
            </bk-button>
            <bk-button
              v-authority="{ active: !authority.MANAGE_AUTH }"
              :text="true"
              theme="primary"
              @click="authority.MANAGE_AUTH ? handleDeleteShield(scope.row.id) : handleShowAuthorityDetail()">
              {{ $t('解除') }}
            </bk-button>
          </bk-table-column>
        </bk-table>
        <!-- 屏蔽失效 -->
        <bk-table v-show="tab.active === 1" class="shield-table" :data="table.data" @sort-change="handleSort">
          <bk-table-column width="100" sortable="custom" label="ID" prop="id" v-slot="scope">
            <span class="shield-id" @click="handleToDetail(scope.row.id)">#{{scope.row.id}}</span>
          </bk-table-column>
          <bk-table-column width="150" class="shield-type" :render-header="renderHeader" prop="shieldTypeName">
          </bk-table-column>
          <bk-table-column min-width="250" class-name="shield-content" :label="$t('屏蔽内容')" v-slot="scope">
            <!-- <span v-if="scope.row.shieldType === 'strategy'" class="link">{{scope.row.shieldContent}}<i class="icon-monitor icon-mc-wailian" @click="handleToOtherPages(scope.row)"></i></span> -->
            <span class="content">{{scope.row.shieldContent}}</span>
          </bk-table-column>
          <bk-table-column width="180" :label="$t('失效时间')" prop="failureTime" sortable="custom"></bk-table-column>
          <bk-table-column min-width="230" :label="$t('屏蔽原因')" prop="description" v-slot="scope">
            <span class="content">{{scope.row.description || '--'}}</span>
          </bk-table-column>
          <bk-table-column width="120" :label="$t('状态')" v-slot="scope">
            <span :class="statusMap[scope.row.status].className">{{statusMap[scope.row.status].des}}</span>
          </bk-table-column>
        </bk-table>
      </div>
      <template v-if="tableInstance">
        <bk-pagination
          v-show="table.data.length"
          class="shield-pagination list-pagination"
          align="right"
          size="small"
          pagination-able
          :current="tableInstance.page"
          :limit="tableInstance.pageSize"
          :count="tableInstance.count"
          :limit-list="tableInstance.pageList"
          @change="handlePageChange"
          @limit-change="handleLimitChange"
          show-total-count>
        </bk-pagination>
      </template>
    </div>
    <div v-show="false">
      <div class="label-menu-wrapper" ref="labelMenu">
        <ul class="label-menu-list" ref="labelMenu">
          <li class="item" v-for="(item, index) in shieldType.list" :key="index" @click="handleSelectType(item)">
            <bk-checkbox :value="item.value" :true-value="item.checked" :false-value="item.cancel"></bk-checkbox>
            <span class="name">{{item.name}}</span>
          </li>
        </ul>
        <div class="footer">
          <div class="btn-group">
            <bk-button :text="true" @click="handleTypeChange"> {{ $t('确定') }} </bk-button>
            <bk-button :text="true" @click="handleResetSelected"> {{ $t('重置') }} </bk-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import TableStore from './store.ts'
import { frontendShieldList, disableShield } from '../../../monitor-api/modules/shield'
import { debounce } from 'throttle-debounce'
import moment from 'moment'
import { commonPageSizeMixin } from '../../common/mixins'
import * as alarmShieldAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
export default {
  name: 'AlarmShield',
  mixins: [commonPageSizeMixin, authorityMixinCreate(alarmShieldAuth)],
  data() {
    return {
      loading: false,
      isShow: false,
      tab: {
        active: 0,
        list: [
          { name: this.$t('屏蔽中'), id: 0, type: 'effct' },
          { name: this.$t('屏蔽失效'), id: 1, type: 'overdue' }
        ]
      },
      shieldType: {
        list: [
          { name: this.$t('告警事件屏蔽'), id: 'event', checked: 'event', value: '', cancel: '' },
          { name: this.$t('范围屏蔽'), id: 'scope', checked: 'scope', value: '', cancel: '' },
          { name: this.$t('策略屏蔽'), id: 'strategy', checked: 'strategy', value: '', cancel: '' }
        ],
        instance: null,
        effct: new Set(),
        overdue: new Set(),
        selectedLabels: []
      },
      right: {
        dateRange: [],
        keyword: ''
      },
      table: {
        loading: false,
        data: [],
        effct: {
          isFilter: false
        },
        overdue: {
          isFilter: false
        }
      },
      cache: {
        dateRange: [],
        overdueData: [],
        effectiveData: []
      },
      cacheDate: [],
      order: {
        effct: {
          isTimeSort: false,
          isIdSort: false,
          id: 'id',
          effct: 'begin_time',
          overdue: 'failure_time'
        },
        overdue: {
          isTimeSort: false,
          isIdSort: false,
          id: 'id',
          effct: 'begin_time',
          overdue: 'failure_time'
        }
      },
      tableInstance: null,
      statusMap: {
        1: {
          des: this.$t('屏蔽中'),
          className: 'shield',
          code: 1
        },
        2: {
          des: this.$t('已过期'),
          className: 'overdue',
          code: 2
        },
        3: {
          des: this.$t('被解除'),
          className: 'release',
          code: 3
        }
      },
      handleSearch() {}
    }
  },
  computed: {
    shieldTypeStr() {
      return this.shieldType.list.filter(item => item.value).map(item => item.value)
        .join(',')
    },
    tabName() {
      return this.tab.list[this.tab.active].type
    },
    curOrder() {
      return this.order[this.tabName]
    },
    curTable() {
      return this.table[this.tabName]
    }
  },
  created() {
    this.handleSearch = debounce(300, () => this.handleGetShiledList())
    !this.loading && this.handleGetShiledList(false, true)
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (!['alarm-shield-add', 'alarm-shield-edit', 'alarm-shield-detail'].includes(from.name)) {
        vm.right.keyword = ''
        vm.tableInstance && vm.tableInstance.setDefaultStore()
        vm.right.dateRange = []
        vm.tab && vm.handleTabChange(0)
      }
      !vm.loading && vm.handleGetShiledList(false, true)
    })
  },
  deactivated() {
    this.handleDestroyFilterPopover()
  },
  beforeDestroy() {
    this.handleDestroyFilterPopover()
  },
  methods: {
    handleToDetail(id) {
      this.$router.push({ name: 'alarm-shield-detail', params: { id } })
    },
    handleAddShield() {
      this.$router.push({ name: 'alarm-shield-add' })
    },
    // ID和时间的筛选
    handleSort(v) {
      if (!v.order) {
        this.curOrder.isIdSort = false
        this.curOrder.isTimeSort = false
      } else {
        v.column.label === 'ID' ? this.handleIdOrder(v) : this.handleTimeOrder(v)
      }
      this.handleGetShiledList()
    },
    handleTimeOrder(sort) {
      this.curOrder.isIdSort = false
      this.curOrder.isTimeSort = true
      if (this.tab.active === 0) {
        this.curOrder.effct = sort.order === 'descending' ? '-begin_time' : 'begin_time'
      } else {
        this.curOrder.overdue = sort.order === 'descending' ? '-failure_time' : 'failure_time'
      }
    },
    handleIdOrder(sort) {
      this.curOrder.isIdSort = true
      this.curOrder.isTimeSort = false
      this.curOrder.id = sort.order === 'descending' ? '-id' : 'id'
    },
    // 日历面板选择事件
    handleDateRangeChange() {
      this.cache.dateRange = this.right.dateRange.join('')
      this.handleGetShiledList(true)
    },
    // 日历面板弹出收起事件
    handleHideDatePicker(state) {
      const dateRangeStr = this.right.dateRange.join('')
      if (!state && !!dateRangeStr && dateRangeStr !== this.cache.dateRange) {
        this.handleGetShiledList(true)
        this.cache.dateRange = this.right.dateRange.join('')
      }
    },
    handleEditShield(id, type) {
      this.$router.push({
        name: 'alarm-shield-edit',
        params: { id, type }
      })
    },
    // 解除告警屏蔽事件
    handleDeleteShield(id) {
      this.$bkInfo({
        title: this.$t('是否解除该屏蔽?'),
        confirmFn: () => {
          this.loading = true
          disableShield({ id }).then(() => {
            this.handleGetShiledList(true)
            this.$bkMessage({ theme: 'success', message: this.$t('解除屏蔽成功') })
          })
            .catch(() => {
              this.loading = false
            })
        }
      })
    },
    // tab栏切换事件
    handleTabChange(index) {
      if (this.tab.active !== index) {
        this.tab.active = index
        this.table.data = []
        this.handleUpdateFilterVal()
        this.handleGetShiledList(true)
        this.handleDestroyFilterPopover()
      }
    },
    handleDestroyFilterPopover() {
      if (this.shieldType.instance) {
        this.shieldType.instance.hide(0)
        this.shieldType.instance.destroy()
        this.shieldType.instance = null
      }
    },
    async handleGetShiledList(needReset = false, needLoading = false) {
      this.loading = needLoading
      this.table.loading = !needLoading
      this.table.data = []
      const params = {
        page: needReset || !this.tableInstance ? 1 : this.tableInstance.page,
        page_size: needReset || !this.tableInstance ? this.handleGetCommonPageSize() : this.tableInstance.pageSize,
        categories: this.shieldType.selectedLabels,
        search: this.right.keyword,
        is_active: this.tab.active === 0
      }
      if (this.curOrder.isTimeSort) {
        params.order = this.tab.active === 0 ? this.curOrder.effct : this.curOrder.overdue
      }
      if (this.curOrder.isIdSort) {
        params.order = this.curOrder.id
      }
      if (this.right.dateRange.join('').length) {
        params.time_range = `${moment(this.right.dateRange[0]).format('YYYY-MM-DD HH:mm:ss')}`
        + '--'
        + `${moment(this.right.dateRange[1]).format('YYYY-MM-DD HH:mm:ss')} `
      }
      const data = await frontendShieldList(params).catch(() => ({ shield_list: [], count: 0 }))
      if (!this.tableInstance) {
        this.tableInstance = new TableStore(data.shield_list)
      } else {
        this.tableInstance.setDefaultData(data.shield_list)
      }
      this.tableInstance.count = data.count
      this.table.data = this.tableInstance.getTableData()
      this.loading = false
      this.table.loading = false
    },
    handlePageChange(page) {
      this.tableInstance.page = page
      this.handleGetShiledList()
    },
    handleLimitChange(pageSize) {
      this.handleSetCommonPageSize(pageSize)
      this.tableInstance.pageSize = pageSize
      this.handleGetShiledList()
    },
    handleTypeChange() {
      if (this.shieldTypeStr.length) {
        this.shieldType.instance.hide(100)
        this.shieldType.selectedLabels = this.shieldTypeStr.split(',')
        this.curTable.isFilter = true
        this.handleGetShiledList()
      } else if (this.curTable.isFilter) {
        this.handleResetSelected()
      }
    },
    handleResetSelected() {
      this.shieldType.instance.hide(100)
      this.shieldType.list.forEach((item) => {
        item.value = ''
      })
      this.shieldType.selectedLabels = []
      if (this.curTable.isFilter) {
        this.curTable.isFilter = false
        this.handleGetShiledList()
      }
      this.shieldType[this.tabName] = new Set()
    },
    handleUpdateFilterVal() {
      const labelSet = this.shieldType[this.tabName]
      this.shieldType.selectedLabels = []
      this.shieldType.list.forEach((item) => {
        if (labelSet.has(item.id)) {
          item.value = item.id
          this.shieldType.selectedLabels.push(item.value)
        } else {
          item.value = ''
        }
      })
    },
    handleShow(e) {
      const target = e.target.tagName === 'SPAN' ? e.target : e.target.parentNode
      if (!this.shieldType.instance) {
        this.shieldType.instance = this.$bkPopover(target, {
          content: this.$refs.labelMenu,
          trigger: 'click',
          arrow: false,
          theme: 'light common-monitor shield',
          maxWidth: 520,
          offset: '0, -11',
          sticky: true,
          duration: [275, 0],
          interactive: true,
          onHidden: () => {
            this.shieldType.instance.destroy()
            this.shieldType.instance = null
            this.shieldType[this.tabName] = new Set(this.shieldType.selectedLabels)
            this.shieldType.list.forEach((item) => {
              item.value = this.shieldType.selectedLabels.includes(item.id) ? item.id : ''
            })
          }
        })
      }
      this.shieldType.instance && this.shieldType.instance.show(100)
    },
    handleSelectType(item) {
      const labelSet = this.shieldType[this.tabName]
      if (!labelSet.has(item.value)) {
        item.value = item.id
        labelSet.add(item.value)
      } else {
        labelSet.delete(item.value)
        item.value = ''
      }
    },
    renderHeader() {
      return <span onClick={e => this.handleShow(e)}
        class={{ 'dropdown-trigger': true, ' plugin-label': true, selected: this.shieldTypeStr }}>
        {this.$t('分类')}
        <i class="icon-monitor icon-filter-fill"></i>
      </span>
    },
    handleToOtherPages(row) {
      if (row.shieldType === 'strategy') {
        this.$router.push({ name: 'strategy-config-detail', params: { id: row.dimensionConfig.id } })
      } else if (row.shieldType === 'event') {
        this.$router.push({ name: 'event-center-detail', params: { id: row.dimensionConfig.id } })
      }
    },
    handleClearDate() {
      this.right.dateRange = []
      this.cache.dateRange = this.right.dateRange.join('')
      this.handleGetShiledList()
    }
  }
}
</script>
<style lang="scss" scope>
.strategy-list-wrapper {
  min-height: calc(100vh - 80px);
  .top-container {
    display: flex;
    justify-content: space-between;
    .right {
      display: flex;
      .bk-date-picker {
        margin-right: 10px;
        width: 301px;
        .bk-picker-confirm {
          .bk-picker-confirm-time {
            text-decoration: none;
          }
          .confirm {
            text-decoration: none;
          }
        }
      }
      .bk-form-control {
        width: 301px;
      }
    }
  }
  .content-wrapper {
    margin-top: 16px;
    border: 1px solid #dcdee5;
    background: #fff;
    .tab-list {
      display: flex;
      flex-direction: row;
      justify-content: flex-start;
      align-items: center;
      line-height: 42px;
      background: #fafbfd;
      padding: 0;
      margin: 0 0 16px 0;
      font-size: 14px;
      &-item {
        flex: 0 0 120px;
        border-right: 1px solid #dcdee5;
        border-bottom: 1px solid #dcdee5;
        text-align: center;
        color: #63656e;
        &.tab-active {
          color: #3a84ff;
          background: #fff;
          border-bottom-color: transparent;
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
        height: 42px;
        border-bottom: 1px solid #dcdee5;
      }
    }
    .shield-table {
      border-left: 0;
      border-right: 0;
      &::before {
        width: 0;
      }
      &::after {
        width: 0;
      }
      .content {
        overflow: hidden;
        text-overflow: ellipsis;

        /* stylelint-disable-next-line value-no-vendor-prefix */
        display: -webkit-box;

        /* stylelint-disable-next-line property-no-vendor-prefix */
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        margin: 12px 0;
      }
      .link {
        display: flex;
        align-items: center;
      }
      .shield-id {
        color: #3a84ff;
        cursor: pointer;
        &:hover {
          color: #699df4;
        }
      }
      .edit-btn {
        padding-left: 0;
        padding-right: 0;
        margin-right: 8px;
      }
      .dropdown-trigger {
        cursor: pointer;
        display: inline-block;
        height: 42px;
        width: 100%;
        .icon-filter-fill {
          margin-left: 6px;
          color: #64656e;
        }
        &.selected {
          color: #3a84ff;
          .icon-filter-fill {
            color: #3a84ff;
          }
        }
      }
      .bk-dropdown-content {
        left: -16px;
        background: #fff;
      }
      .dropdown-menu-list {
        display: flex;
        width: 150px;
        flex-direction: column;
        padding: 6px 0;
        background: #fff;
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
        }
      }
      .icon-mc-wailian {
        margin-left: 2px;
        font-size: 22px;
        cursor: pointer;
        color: #c4c6cc;
        &:hover {
          color: #3a84ff;
        }
      }
      .release {
        color: #ff9c01;
      }
      .overdue {
        color: #c4c6cc;
      }
    }
    .shield-pagination {
      margin: 15px;
    }
  }
}
.label-menu-wrapper {
  .label-menu-list {
    display: flex;
    flex-direction: column;
    background-color: #fff;
    border-radius: 2px;
    padding: 6px 0;
    .item {
      display: flex;
      align-items: center;
      height: 32px;
      min-height: 32px;
      padding: 0 10px;
      color: #63656e;
      cursor: pointer;
      .name {
        display: inline-block;
        height: 18px;
        line-height: 18px;
        margin-left: 6px;
      }
      &:hover {
        background: #e1ecff;
        color: #3a84ff;
      }
    }
  }
  .footer {
    display: flex;
    justify-content: center;
    height: 29px;
    border-top: solid 2px #f0f1f5;
    background-color: #fff;
    .btn-group {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 70px;
      height: 100%;
    }
    .bk-button-text {
      font-size: 12px;
      line-height: 22px;
      position: relative;
      top: -1px;
      padding: 0;
    }
  }
}
</style>
