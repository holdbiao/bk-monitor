<template>
  <div class="collector-config" v-monitor-loading="{ isLoading: loading }">
    <page-tips
      style="margin-bottom: 16px"
      :tips-text="$t('监控数据采集是通过下发监控插件来实现数据采集的全生命周期管理，该功能依赖服务器安装bkmonitorbeat采集器')"
      :link-text="$t('采集器安装前往节点管理')"
      :link-url="`${$store.getters.bkNodemanHost}#/plugin-manager/list`"
      doc-link="collectorConfigMd">
    </page-tips>
    <div>
      <div class="collector-config-panel" v-if="tabData.length">
        <ul class="panel-tab">
          <li class="panel-tab-item" v-for="(item,index) in tabData"
              :key="index" :class="{ 'tab-active': index === panel.active }"
              :style="{ borderRightColor: index === panel.active - 1 ? '#DCDEE5' : '' }"
              @click="index !== panel.active && handleTabItemClick(index)">
            <span class="tab-name">{{item.name}}</span>
            <span class="tab-mark">{{item.total}}</span>
          </li>
          <li class="panel-tab-blank"></li>
        </ul>
        <ul class="panel-content" v-if="activeTabItem.data">
          <li class="panel-content-item"
              :class="{ 'active-num': key === panel.itemActive }"
              v-for="(num,key) in activeTabItem.data"
              @click="handleTabNumClick(key,num)"
              :key="key">
            <span class="content-num">{{num}}</span>
            <span class="content-desc">{{tabItemMap[key]}}</span>
          </li>
        </ul>
      </div>
      <div class="collector-config-tool">
        <div class="tool-btn">
          <bk-button
            v-authority="{ active: !authority.MANAGE_AUTH }"
            theme="primary"
            @click="authority.MANAGE_AUTH ? handleShowAdd('add') : handleShowAuthorityDetail()"
            class="mc-btn-add"
            style="margin-right: 8px;">
            {{ $t('新建') }}
          </bk-button>
          <bk-button theme="default" @click="handleToLogCollection"> {{ $t('日志采集') }} </bk-button>
        </div>
        <bk-input :placeholder="$t('采集配置名称/ID')" right-icon="bk-icon icon-search" class="tool-search" v-model="panel.keyword" @change="handleSearch"></bk-input>
      </div>
      <div ref="tableWrapper" class="collector-config-table">
        <div class="table-wrap">
          <bk-table class="config-table"
                    ref="table" :empty-text="$t('查询无数据')"
                    @row-mouse-enter="i => table.hoverIndex = i"
                    @row-mouse-leave="i => table.hoverIndex = -1"
                    :row-style="handleStoppedRow"
                    @sort-change="handleSortChange"
                    :data="table.data">
            <bk-table-column
              label="ID"
              prop="id"
              sortable
              width="70">
              <template slot-scope="scope">
                {{ `#${scope.row.id}` }}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('名称')"
                             min-width="150">
              <template slot-scope="scope">
                <div class="col-name">
                  <span class="col-name-desc" v-if="scope.$index !== table.editIndex" @click.stop="handleShowDetail(scope.row)">{{scope.row.name}}</span>
                  <span v-if="scope.row.needUpdate && scope.$index !== table.editIndex && scope.row.status !== 'STOPPED'" class="col-name-update" @click="handleConfigUpdate(scope.row)"><span> {{ $t('升级') }} </span></span>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              v-if="false" :label="$t('所属')"
              prop="bizName"
              min-width="90">
            </bk-table-column>
            <bk-table-column :label="$t('方式')"
                             prop="collectName"
                             width="100">
            </bk-table-column>
            <bk-table-column :label="$t('运行状态')"
                             width="140">
              <template slot-scope="scope">
                <span class="col-status" :class="'status-' + scope.row.status" :style="{ color: ['PREPARING', 'STOPPED'].includes(scope.row.status) ? '#C4C6CC' : '#63656E' }">
                  <img src="../../static/images/svg/spinner.svg" v-if="scope.row.doingStatus" class="status-loading" />
                  <div v-if="['FAILED','WARNING','SUCCESS','STOPPED'].includes(scope.row.taskStatus)" class="col-status-circle" :style="{ backgroundColor: startedBack[scope.row.taskStatus] ,borderColor: startedBorder[scope.row.taskStatus] }"></div>
                  <span :class="{ 'pointer-active': !['PREPARING', 'STOPPED'].includes(scope.row.status) }" @click="!['PREPARING', 'STOPPED'].includes(scope.row.status) && handleCheckStatus(scope.row)">{{scope.row.statusName}}</span>
                </span>
                <!-- 临时处理：部署中置灰 -->
                <!-- <span class="col-status" :class="'status-' + scope.row.status" :style="{ color: ['STOPPED', 'DEPLOYING'].includes(scope.row.status) ? '#C4C6CC' : '#63656E' }">
                  <img src="../../static/images/svg/spinner.svg" v-if="scope.row.doingStatus" class="status-loading" />
                  <div v-if="['FAILED','WARNING','SUCCESS','STOPPED'].includes(scope.row.taskStatus)" class="col-status-circle" :style="{ backgroundColor: startedBack[scope.row.taskStatus] ,borderColor: startedBorder[scope.row.taskStatus] }"></div>
                  <span :class="{ 'pointer-active': !['STOPPED', 'DEPLOYING'].includes(scope.row.status) }" @click="!['DEPLOYING'].includes(scope.row.status) && handleCheckStatus(scope.row)">{{scope.row.statusName}}</span>
                </span> -->
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('对象')"
                             prop="objectLabel"
                             min-width="150">
            </bk-table-column>
            <bk-table-column :label="$t('目标')"
                             min-width="180">
              <template slot-scope="scope">
                <span class="col-target">
                  {{ scope.row.status === 'PREPARING' ? '--' : scope.row.targetString || '--'}}
                </span>
              </template>
            </bk-table-column>
            <!-- <bk-table-column :label="$t('分类')"
                             min-width="200">
              <template slot-scope="scope">
                <div v-if="scope.row.serverceTypeList.length" class="col-classifiy">
                  <div class="col-classifiy-wrap" :ref="'table-row-' + scope.$index">
                    <span v-for="(item, index) in scope.row.serverceTypeList"
                          :key="index"
                          class="classifiy-label">
                      {{item.first}}：{{item.second}}
                    </span>
                    <span v-if="scope.row.overflow" class="classifiy-overflow">...</span>
                  </div>
                </div>
                <span v-else>--</span>
              </template>
            </bk-table-column> -->
            <bk-table-column :label="$t('更新记录')" width="180">
              <template slot-scope="scope">
                <div class="col-update-log">
                  <div class="col-update-log-label">{{scope.row.updateUser || '--'}}</div>
                  <div>{{scope.row.updateTime || '--'}}</div>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="$t('操作')"
              width="200">
              <template slot-scope="scope">
                <div class="col-operator">
                  <span
                    v-authority="{ active: !authority.MANAGE_AUTH && !(scope.row.taskStatus === 'STOPPED' || scope.row.doingStatus) }"
                    class="col-operator-btn"
                    :class="{ 'btn-disabled': scope.row.taskStatus === 'STOPPED' || scope.row.doingStatus }"
                    @click="authority.MANAGE_AUTH || (scope.row.taskStatus === 'STOPPED' || scope.row.doingStatus) ? scope.row.taskStatus !== 'STOPPED' && !scope.row.doingStatus && handleUpdateTarget(scope.row) : handleShowAuthorityDetail()">
                    {{ $t('增删目标') }}
                  </span>
                  <span
                    class="col-operator-btn"
                    style="margin-right: 0;"
                    :class="{ 'btn-disabled': scope.row.taskStatus === 'STOPPED' }"
                    @click="scope.row.taskStatus !== 'STOPPED' && handleCheckView(scope.row)">
                    {{ $t('检查视图') }}
                  </span>
                  <span style="color: #ea3636; min-width: 23px;" :style="{ visibility: !!scope.row.errorNum ? 'visible' : 'hidden' }">({{scope.row.errorNum}})</span>
                  <span
                    v-authority="{ active: !authority.MANAGE_AUTH && !scope.row.doingStatus }"
                    class="col-operator-more"
                    data-popover="true"
                    :ref="'operator-' + scope.$index"
                    :class="{ 'operator-active': popover.hover === scope.$index, 'btn-disabled': scope.row.doingStatus }"
                    @click="authority.MANAGE_AUTH || scope.row.doingStatus ? !scope.row.doingStatus && handleOperatorOver(scope.row, $event, scope.$index) : handleShowAuthorityDetail()">
                    <i data-popover="true" class="bk-icon icon-more"></i>
                  </span>
                </div>
              </template>
            </bk-table-column>
          </bk-table>
          <template v-if="tableInstance.data && tableInstance.data.length">
            <bk-pagination
              v-show="tableInstance.total"
              class="config-pagination"
              align="right"
              size="small"
              pagination-able
              :current="tableInstance.page"
              :limit="tableInstance.pageSize"
              :count="tableInstance.total"
              :limit-list="tableInstance.pageList"
              @change="handlePageChange"
              @limit-change="handleLimitChange"
              show-total-count>
            </bk-pagination>
          </template>
        </div>
      </div>
    </div>
    <collector-config-detail
      v-if="side.show"
      :side-data="side.data"
      :side-show="side.show"
      @update-name="handleChangeCollectName"
      @edit-plugin="handleEditPlugin"
      @edit="handleToEdit"
      @set-hide="handleSideHidden"></collector-config-detail>
    <bk-dialog v-model="dialog.update.show" :show-footer="false" width="850">
      <collector-config-update v-if="dialog.update.params" :update-params="dialog.update.params" @on-submit="handleOpenUpgradePage" @close-update="handleCloseUpdate"></collector-config-update>
    </bk-dialog>
    <bk-dialog v-model="dialog.delete.show" :show-footer="false">
      <div class="dialog-del">
        <div class="dialog-del-title"> {{ $t('确定删除该采集配置？') }} </div>
        <div class="dialog-del-content"> {{ $t('删除该采集配置后将无法撤消！') }} </div>
        <div class="dialog-del-footer">
          <bk-button theme="primary" class="footer-btn" :loading="dialog.delete.loading" @click="handleSubmitDelete" style="margin-right: 10px;"> {{ $t('确定') }} </bk-button>
          <bk-button @click="dialog.delete.show = false" class="footer-btn"> {{ $t('取消') }} </bk-button>
        </div>
      </div>
    </bk-dialog>
    <div v-show="false">
      <div class="operator-group" ref="operatorGroup">
        <span class="operator-group-btn" @click="popover.status !== 'STOPPED' && handleShowAdd('edit')" :class="{ 'table-edit-disbaled': popover.status === 'STOPPED' }"> {{ $t('编辑') }} </span>
        <span class="operator-group-btn" @click="handleDeleteRow"> {{ $t('删除') }} </span>
        <span class="operator-group-btn" @click="handleOpenOrClose">{{popover.status === 'STOPPED' ? $t('启用') : $t('停用')}}</span>
        <span class="operator-group-btn" @click="handleCloneConfig"> {{ $t('克隆') }} </span>
      </div>
    </div>
    <delete-collector
      :collector-task-data="collectorTaskData"
      :show.sync="delDialogShow"></delete-collector>
  </div>
</template>
<script>
import CollectorConfigDetail from './collector-config-detail/collector-config-detail'
import CollectorConfigUpdate from './collector-config-update/collector-config-update'
import DeleteCollector from './collector-dialog-delete/collector-dialog-delete'
// import { isCancel } from 'axios'
import { debounce } from 'throttle-debounce'
import { addListener, removeListener } from 'resize-detector'
import TableStore  from './store.ts'
import { commonPageSizeMixin } from '../../common/mixins'
import { SET_ADD_MODE, SET_ADD_DATA, SET_OBJECT_TYPE } from '../../store/modules/collector-config'
import { createNamespacedHelpers } from 'vuex'
import { collectConfigList, deleteCollectConfig, cloneCollectConfig } from '../../../monitor-api/modules/collecting'
import * as collectAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
import pageTips from '../../components/pageTips/pageTips'
const { mapMutations } = createNamespacedHelpers('collector-config')
export default {
  name: 'CollectorConfig',
  components: {
    CollectorConfigDetail,
    CollectorConfigUpdate,
    DeleteCollector,
    pageTips
  },
  mixins: [commonPageSizeMixin, authorityMixinCreate(collectAuth)],
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail
    }
  },
  data() {
    return {
      loading: false,
      tableInstance: {},
      panel: {
        name: this.$t('全部'),
        active: 0,
        itemActive: '',
        keyword: '',
        handleSearch() {

        }
      },
      topology: {
        show: false
      },
      table: {
        data: [],
        statusMap: [],
        loading: false,
        hoverIndex: -1,
        editIndex: -1
      },
      popover: {
        instance: null,
        hover: -1,
        edit: false,
        status: '',
        data: {}
      },
      view: {
        show: false
      },
      addAndDel: {
        show: false
      },
      dialog: {
        delete: {
          show: false,
          loading: false
        },
        update: {
          show: false,
          params: null,
          data: null
        }
      },
      side: {
        pluginId: '',
        show: false,
        data: null
      },
      headTitle: null,
      headBack: null,
      add: {
        show: false,
        mode: 'add',
        data: {}
      },
      stopStart: {
        show: false,
        type: 'STOPPED',
        upgradeParams: {}
      },
      lisenResize: null,
      timer: null,
      startedBack: {
        SUCCESS: '#94F5A4',
        WARNING: '#FFD695',
        FAILED: '#FD9C9C',
        STOPPED: '#F0F1F5'
      },
      startedBorder: {
        SUCCESS: '#2DCB56',
        WARNING: '#FF9C01',
        FAILED: '#EA3636',
        STOPPED: '#C4C6CC'
      },
      isLeave: false,
      filterEnterRouter: [
        'service-classify',
        'plugin-manager',
        'plugin-edit',
        'export-configuration'
      ],
      cancelFetch: null,
      delDialogShow: false,
      collectorTaskData: {
        status: 'STARTED',
        id: ''
      }
    }
  },
  computed: {
    tabData() {
      return this.tableInstance.tabData || []
    },
    activeTabItem() {
      return this.tableInstance.tabData[this.panel.active] || {}
    },
    tabItemMap() {
      return this.tableInstance.tabItemMap || {}
    },
    retrievalUrl() {
      if (process.env.NODE_ENV === 'development') {
        return `${process.env.loginHost}/t/log-search-4#/manage/collect?bizId=${this.$store.getters.bizId}`
      }
      return `${this.$store.getters.bkLogSearchUrl}#/manage/collect?bizId=${this.$store.getters.bizId}`
    }
  },
  watch: {
    delDialogShow(bool) {
      if (!bool) {
        this.handleGetListData()
      }
    }
  },
  created() {
    this.handleGetListData()
    this.handleSearch = debounce(300, this.handleKeywordChange)
    this.lisenResize = debounce(100, this.handleTableWrapperChange)
  },
  activated() {
    this.isLeave = false
  },
  deactivated() {
    this.isLeave = true
    this.timer && window.clearTimeout(this.timer)
    this.timer = 0
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (!['collect-config-view', 'collect-config-add',
        'collect-config-edit', 'collect-config-node',
        'collect-config-update', 'collect-config-operate-detail'].includes(from.name)) {
        vm.panel.keyword = ''
        vm.panel.active = 0
        vm.panel.itemActive = ''
        if (vm.tableInstance.setDefaultStore) {
          vm.tableInstance.setDefaultStore()
          vm.table.data = vm.tableInstance.getTableData()
          vm.handleTableDataChange(vm.table.data, false, true)
        }
      }
      if (to.query.id) {
        vm.panel.keyword = `ID：${to.query.id}`
      }
      if (vm.filterEnterRouter.includes(from.name)) {
        if (to.params.serviceCategory) {
          vm.panel.keyword = vm.$t('分类：') + to.params.serviceCategory
        } else if (to.params.pluginId) {
          vm.panel.keyword = vm.$t('插件ID：') + to.params.pluginId
        }
        if (vm.tableInstance) {
          vm.tableInstance.keyword = vm.panel.keword
        }
      }
      if (!vm.loading) {
        vm.handleInterGetListData(true, false)
      }
    })
  },
  beforeRouteLeave(to, from, next) {
    // this.timer && window.clearTimeout(this.timer)
    typeof this.cancelFetch === 'function' && this.cancelFetch()
    next()
  },
  mounted() {
    addListener(this.$refs.tableWrapper, this.lisenResize)
  },
  beforeDestroy() {
    this.isLeave = true
    removeListener(this.$refs.tableWrapper, this.lisenResize)
    this.timer && window.clearTimeout(this.timer)
  },
  errorCaptured() {
    this.timer && window.clearTimeout(this.timer)
  },
  methods: {
    ...mapMutations([SET_ADD_DATA, SET_ADD_MODE, SET_OBJECT_TYPE]),
    getCollectionConfigList(status = false) {
      return collectConfigList(
        {
          bk_biz_id: this.$store.getters.bizId,
          refresh_status: status,
          order: '-create_time'
        },
        {
          needCancel: true,
          cancelFn: c => (this.cancelFetch = c)
        }
      ).catch(() => {
      })
    },
    getTargetString(tableData) {
      const textMap = {
        TOPO: `${this.$t('个')}${this.$t('节点')}`,
        SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
        SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
      }
      tableData.forEach((item) => {
        if (item.objectTypeEn === 'HOST') {
          if (['SERVICE_TEMPLATE', 'SET_TEMPLATE', 'TOPO'].includes(item.nodeType)) {
            // eslint-disable-next-line vue/max-len
            item.targetString = `${item.targetNodesCount}${textMap[item.nodeType]} （${this.$t('共')} ${item.totalInstanceCount} ${this.$t('台主机')}）`
          } else if (item.nodeType === 'INSTANCE') {
            item.targetString = ` ${item.totalInstanceCount} ${this.$t('台主机')}`
          }
        } else if (item.objectTypeEn === 'SERVICE') {
          if (['SERVICE_TEMPLATE', 'SET_TEMPLATE', 'TOPO'].includes(item.nodeType)) {
            // eslint-disable-next-line vue/max-len
            item.targetString = `${item.targetNodesCount}${textMap[item.nodeType]} （${this.$t('共')} ${item.totalInstanceCount} ${this.$t('个实例')}）`
          }
        }
      })
      return tableData
    },
    handleGetListData(needLoading = true) {
      this.loading = needLoading
      this.getCollectionConfigList().then((data) => {
        this.tableInstance = new TableStore(data, this.$store.getters.bizList)
        this.tableInstance.keyword = this.panel.keyword || ''
        const tableData = this.tableInstance.getTableData('All', '', this.$route.params.searchType || null)
        this.table.data = this.getTargetString(tableData)
        this.handleTableDataChange(this.table.data, false)
        if (this.$route.query.id && this.table.data.length) {
          const [{ id, name, status }] = this.table.data
          const params = { id, name, status }
          this.handleShowDetail(params)
        }
        this.loading = false
        if (!this.isLeave) {
          const timer = setTimeout(() => {
            this.handleInterGetListData()
            window.clearTimeout(timer)
          }, 1000)
        }
      })
        .finally(() => {
          this.loading = false
        })
    },
    handleInterGetListData(needLoading = false, refleshStatus = true) {
      this.loading = needLoading
      this.getCollectionConfigList(refleshStatus).then((data) => {
        // eslint-disable-next-line camelcase
        if (data?.config_list?.length) {
          const instance = new TableStore(data, this.$store.getters.bizList)
          instance.keyword = this.panel.keyword || this.tableInstance.keyword || ''
          instance.page = this.tableInstance.page || 1
          instance.pageSize = this.tableInstance.pageSize || 10
          this.tableInstance = instance
          const tableData = this.tableInstance.getTableData(
            this.tableInstance.tabData[this.panel.active].key
            , this.panel.itemActive
          )
          this.table.data = this.getTargetString(tableData)
          this.handleTableDataChange(this.table.data, false)
        }
        this.loading = false
        this.timer && window.clearTimeout(this.timer)
        if (!this.isLeave) {
          this.timer = setTimeout(() => {
            this.handleInterGetListData()
          }, 5000)
        }
      })
    },
    handleTabNumClick(key) {
      if (this.panel.keyword) {
        this.panel.keyword = ''
        this.handleKeywordChange('')
      }
      this.panel.itemActive = key === this.panel.itemActive ? '' : key
      const { tableInstance } = this
      tableInstance.page = 1
      this.table.data = tableInstance.getTableData(tableInstance.tabData[this.panel.active].key, this.panel.itemActive)
      this.handleTableDataChange(this.table.data)
    },
    handleTableDataChange(v, needLoading = true) {
      this.table.loading = needLoading
      setTimeout(() => {
        v.forEach((item, index) => {
          const ref = this.$refs[`table-row-${index}`]
          item.overflow = ref && ref.clientHeight > 32
        })
        this.table.loading = false
      }, 50)
    },
    handleOperatorOver(data, e, index) {
      if (this.popover.index === index) {
        return
      }
      this.popover.hover = index
      this.popover.edit = data.needUpdate
      this.popover.status = data.status
      this.popover.data = data
      this.popover.collectType = data.collectType
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
      this.popover?.instance?.show?.(100)
    },
    handleUpdateTarget(data) {
      // 更新采集对象组的类型
      this[SET_OBJECT_TYPE](data.objectTypeEn)
      this.$router.push({
        name: 'collect-config-node',
        params: {
          data
        }
      })
    },
    handleCheckView(data) {
      this.$router.push({
        name: 'collect-config-view',
        params: {
          id: data.id,
          title: data.name
        }
      })
    },
    handleConfigUpdate(data) {
      if (data.doingStatus) {
        this.$bkNotify({
          title: this.$t('配置升级'),
          message: this.$t('正在执行中的配置暂不能升级'),
          theme: 'warning',
          offsetY: 80,
          position: 'bottom-left'
        })
      } else {
        const { update } = this.dialog
        update.show = true
        update.params = data.updateParams
        update.data = data
      }
    },
    handleShowDetail({ id, name, status }) {
      this.side.data = { id, name, status }
      this.side.show = true
    },
    handleChangeCollectName(id, name) {
      const curCollect = this.table.data.find(item => item.id === id)
      curCollect && (curCollect.name = name)
    },
    handleShowAdd(mode) {
      this[SET_ADD_MODE](mode)
      if (mode === 'edit' && this.popover.data.needUpdate) {
        const h = this.$createElement
        const deleteInfoInstance = this.$bkInfo({
          title: this.$t('插件已变更，请先升级'),
          type: 'warning',
          showFooter: false,
          maskClose: true,
          escClose: true,
          extCls: 'dialog-delete',
          subHeader: h('div', {
            class: {
              'dialog-delete-content': true
            },
            on: {
              click: () => {
                this.handleConfigUpdate(this.popover.data)
                deleteInfoInstance.close()
              }
            }
          }, this.$t('前去升级配置'))
        })
        return false
      }
      const params = { title: mode === 'edit' ? this.popover.data.name : this.$t('新建配置') }
      if (mode === 'edit') {
        this[SET_ADD_DATA](this.popover.data)
        params.id = this.popover.data.id
        params.pluginId = this.popover.data.updateParams.pluginId
      }
      if (this.panel.active > 0 && mode === 'add') {
        params.pluginType = this.tabData[this.panel.active].name
        if (params.pluginType === 'Process') {
          params.objectId = 'host_process'
        }
      }
      this.$router.push({
        name: mode === 'edit' ? 'collect-config-edit' : 'collect-config-add',
        params
      })
    },
    handleTargetChange() {
      this.targetPage.show = false
    },
    handlePageChange(page) {
      this.tableInstance.page = page
      this.table.data = this.tableInstance.getTableData(
        this.tableInstance.tabData[this.panel.active].key
        , this.panel.itemActive
      )
      this.table.data = this.getTargetString(this.table.data)
      this.handleTableDataChange(this.table.data)
    },
    handleLimitChange(limit) {
      this.tableInstance.page = 1
      this.tableInstance.pageSize = limit
      this.handleSetCommonPageSize(limit)
      this.table.data = this.tableInstance.getTableData(
        this.tableInstance.tabData[this.panel.active].key
        , this.panel.itemActive
      )
      this.handleTableDataChange(this.table.data)
    },
    handleTabItemClick(index) {
      if (this.panel.keyword) {
        this.panel.keyword = ''
        this.handleKeywordChange('')
      }
      this.panel.active = index
      const { tableInstance } = this
      tableInstance.page = 1
      this.table.data = tableInstance.getTableData(tableInstance.tabData[index].key, this.panel.itemActive)
      this.handleTableDataChange(this.table.data)
    },
    handleKeywordChange(v) {
      this.tableInstance.keyword = v
      this.tableInstance.page = 1
      this.table.data = this.tableInstance.getTableData(
        this.tableInstance.tabData[this.panel.active].key
        , this.panel.itemActive
      )
      this.handleTableDataChange(this.table.data)
    },
    handleTableWrapperChange() {
      this.table.data.length && this.handleTableDataChange(this.table.data, false)
    },
    handleSideHidden() {
      this.side.show = false
    },
    handleCloseUpdate(v) {
      const { update } = this.dialog
      update.show = false
      if (v && update.data) {
        update.data.needUpdate = false
        const allItem = this.tableInstance.tabData.find(item => item.key === 'All')
        const curItem = this.tableInstance.tabData.find(item => item.key === update.data.collectType)
        allItem.data.needUpdateNum -= 1
        curItem.data.needUpdateNum -= 1
      }
      update.data = null
    },
    handleDeleteRow() {
      const { data } = this.popover
      this.collectorTaskData.status = data.status
      this.collectorTaskData.id = data.id
      this.collectorTaskData.name = data.name
      this.delDialogShow = true
    //   const { data } = this.popover
    //   if (data.status === 'STOPPED') {
    //     const deleteData = this.dialog.delete
    //     deleteData.show = true
    //   } else if (data.status === 'STARTED') {
    //     const h = this.$createElement
    //     const deleteInfoInstance = this.$bkInfo({
    //       title: this.$t('仅可删除已停用的配置'),
    //       type: 'warning',
    //       showFooter: false,
    //       maskClose: true,
    //       escClose: true,
    //       extCls: 'dialog-delete',
    //       subHeader: h('div', {
    //         class: {
    //           'dialog-delete-content': true
    //         },
    //         on: {
    //           click: () => {
    //             this.handleOpenOrClose()
    //             deleteInfoInstance.close()
    //           }
    //         }
    //       }, this.$t('前往停用配置'))
    //     })
    //   }
    },
    // 克隆采集配置
    handleCloneConfig() {
      this.loading = true
      cloneCollectConfig({ id: this.popover.data.id }).then(() => {
        this.handleInterGetListData(true, false)
        this.tableInstance.page = 1
        this.table.data = this.tableInstance.getTableData(
          this.tableInstance.tabData[this.panel.active].key
          , this.panel.itemActive
        )
        this.handleTableDataChange(this.table.data)
        this.$bkMessage({
          theme: 'success',
          message: this.$t('克隆成功')
        })
      })
        .finally(() => {
          this.loading = false
        })
    },
    handleSubmitDelete() {
      const deleteData = this.dialog.delete
      deleteData.loading = true
      deleteCollectConfig({
        id: this.popover.data.id
      }).then(() => {
        this.tableInstance.deleteDataById(this.popover.data.id)
        this.table.data = this.tableInstance.getTableData(
          this.tableInstance.tabData[this.panel.active].key
          , this.panel.itemActive
        )
        this.handleTableDataChange(this.table.data)
        this.$bkMessage({
          theme: 'success',
          message: this.$t('删除成功')
        })
      })
        .finally(() => {
          deleteData.loading = false
          deleteData.show = false
        })
    },
    handleOpenOrClose() {
      const { data } = this.popover
      this.stopStart.type = data.status
      this.$router.push({
        name: 'collect-config-update',
        params: {
          title: data.status === 'STARTED' ? this.$t('停用采集配置') : this.$t('启用采集配置'),
          data,
          stopStart: this.stopStart
        }
      })
    },
    handleOpenUpgradePage(params) {
      this.dialog.update.show = false
      this.popover.data = this.dialog.update.data
      this.stopStart.params = params
      this.stopStart.type = 'UPGRADE'
      this.$router.push({
        name: 'collect-config-update',
        params: {
          title: this.$t('升级采集配置'),
          data: this.dialog.update.data,
          stopStart: this.stopStart,
          id: this.dialog.update.data.id
        }
      })
    },
    handleCheckStatus(row) {
      if (row.status !== 'STOPPED') {
        this.$router.push({
          name: 'collect-config-operate-detail',
          params: {
            id: row.id,
            title: row.name
          }
        })
      }
    },
    handleStoppedRow({ row }) {
      if (row.taskStatus === 'STOPPED') {
        return {
          background: '#FAFBFD',
          color: '#C4C6CC'
        }
      }
    },
    handleToEdit(id) {
      this.side.show = false
      this.table.data.forEach((item) => {
        if (item.id === id) {
          this.popover.data = item
        }
      })
      this.handleShowAdd('edit')
    },
    handleEditPlugin(data) {
      this.handleSideHidden()
      this.$router.push({
        name: 'plugin-edit',
        params: {
          title: `${this.$t('编辑插件')} ${data.plugin_id}`,
          pluginId: data.plugin_id
        }
      })
    },
    handleToLogCollection() {
      window.open(this.retrievalUrl, '_blank')
    },
    handleSortChange({ order, prop }) {
      this.tableInstance.sortOrder = order
      this.tableInstance.sortProp = prop
      this.table.data = this.tableInstance.getTableData(
        this.tableInstance.tabData[this.panel.active].key
        , this.panel.itemActive
      )
      this.handleTableDataChange(this.table.data)
    }
  }
}
</script>
<style lang="scss" scoped>
.collector-config {
  font-size: 12px;
  &-panel {
    height: 159px;
    height: 170px;
    background: #fff;
    border: 1px solid #dcdee5;
    border-radius: 2px 2px 0 0;
    .panel-tab {
      display: flex;
      align-items: center;
      background: #fafbfd;
      padding: 0;
      margin: 0;
      overflow: auto;
      &-item {
        display: flex;
        flex: 0 0 auto;
        min-width: 140px;
        align-items: center;
        justify-content: center;
        color: #63656e;
        font-size: 14px;
        height: 54px;
        border-bottom: 1px solid #dcdee5;
        border-right: 1px solid #fafbfd;
        cursor: pointer;
        .tab-name {
          font-weight: bold;
          margin-right: 6px;
        }
        &:hover {
          .tab-name {
            color: #3a84ff;
            cursor: pointer;
          }
        }
        .tab-mark {
          color: #fff;
          font-size: 12px;
          min-width: 24px;
          height: 16px;
          line-height: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #c4c6cc;
          padding: 0px 4px;
          border-radius: 12px;
        }
        &.tab-active {
          color: #3a84ff;
          background: #fff;
          border-right-color: #dcdee5;
          border-bottom-color: transparent;
          .tab-mark {
            background: #3a84ff;
            color: #fff;
          }
        }
        &:first-child {
          /* stylelint-disable-next-line declaration-no-important */
          border-left-color: transparent !important;
        }
      }
      &-blank {
        flex: 1;
        height: 54px;
        border-bottom: 1px solid #dcdee5;
      }
    }
    .panel-content {
      height: 115px;
      display: flex;
      align-items: center;
      border: 1px solid transparent;
      border-bottom-color: #dcdee5;
      &-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 115px;
        position: relative;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        &:hover {
          border-bottom-color: #3a84ff;
        }
        &.active-num {
          border-bottom-color: #3a84ff;
        }
        &:not(:last-child):after {
          content: " ";
          position: absolute;
          top: 31px;
          right: 0;
          width: 1px;
          height: 53px;
          background: #dcdee5;
        }
        .content-num {
          color: #313238;
          font-size: 32px;
        }
        .content-desc {
          color: #979ba5;
        }
      }
    }
  }
  &-tool {
    display: flex;
    align-items: center;
    height: 60px;
    .tool-btn {
      margin-right: auto;
    }
    .tool-search {
      width: 360px;
    }
    .tool-icon {
      width: 32px;
      height: 32px;
      line-height: 32px;
      text-align: center;
      font-size: 32px;
      border: 1px solid #c4c6cc;
      color: #979ba5;
      border-radius: 2px;
      cursor: pointer;
    }
  }
  &-table {
    display: flex;
    .config-topology {
      flex: 0 0 240px;
      border: 1px solid #dcdee5;
      border-right: 0;
      border-radius: 0px 0 0 2px;
    }
    .table-wrap {
      flex: 1;
      width: calc(100% - 240px);
      .config-table {
        color: #63656e;
        overflow: visible;
        .col-name {
          color: #3a84ff;
          display: flex;
          cursor: pointer;
          align-items: center;
          line-height: 26px;
          &-update {
            flex: 0 0 32px;
            height: 16px;
            margin-left: 5px;
            background: #ff9c01;
            color: #fff;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            span {
              font-size: 12px;
              *font-size: 10px;
              transform: scale(.83,.83);
            }
          }
          &-desc {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          &-icon {
            font-size: 24px;
          }
        }
        .col-update-log {
          height: 58px;
          display: flex;
          justify-content: center;
          flex-direction: column;
          &-label {
            margin-bottom: 3px;
          }
        }
        .col-status {
          display: flex;
          align-items: center;
          .pointer-active {
            &:hover {
              color: #3a84ff;
              cursor: pointer;
            }
          }
          .status-loading {
            width: 16px;
            height: 16px;
            margin-right: 6px;
            margin-left: -4px;
          }
        }
        .col-status-circle {
          width: 8px;
          height: 8px;
          margin-right: 10px;
          border-radius: 50%;
          border: 1px solid;
        }
        .col-classifiy {
          height: 30px;
          position: relative;
          &-wrap {
            overflow: hidden;
            margin-right: 25px;
            .classifiy-label {
              // &:first-child{
              //     margin-left: 0;
              // }
              background: #f0f1f5;
              font-size: 12px;
              float: left;
              margin: 6px;
              padding: 2px 6px;
              // .label-name {
              //     display: inline-block;
              //     height: 24px;
              //     line-height: 24px;
              //     padding: 0 7px;
              //     text-align: center;
              //     &:first-child {
              //        border-right: 1px solid #DCDEE5;
              //        background: #FFFFFF;
              //     }
              // }
            }
            .classifiy-overflow {
              position: absolute;
              top: 0;
              font-size: 12px;
              height: 20px;
              background: #f0f1f5;
              float: left;
              margin: 6px 0;
              padding: 2px 6px;
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
          &-more {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
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
      }
      .config-pagination {
        display: flex;
        height: 60px;
        align-items: center;
        justify-content: flex-start;
        padding: 0 20px;
        border: 1px solid #dcdee5;
        border-top: 0;
        background: #fff;
        /deep/ .bk-page-count {
          margin-right: auto;
        }
      }
    }
  }
}
.operator-group {
  display: flex;
  flex-direction: column;
  width: 68px;
  height: 98px;
  color: #63656e;
  font-size: 12px;
  border: 1px solid #dcdee5;
  &-btn {
    flex: 1;
    display: flex;
    align-items: center;
    padding-left: 10px;
    background: #fff;
    &:hover {
      background: #f0f1f5;
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
.dialog-del {
  color: #63656e;
  font-size: 12px;
  text-align: center;
  &-title {
    color: #313238;
    font-size: 20px;
    margin-bottom: 16px;
    margin-top: 17px;
    height: 26px;
  }
  &-content {
    margin-bottom: 25px;
    text-align: center;
  }
  &-footer {
    margin-bottom: 14px;
    font-size: 0;
    text-align: center;
    .footer-btn {
      font-size: 12px;
      width: 86px;
      height: 32px;
    }
  }
}
.dialog-delete {
  .bk-dialog-content .bk-dialog-type-sub-header {
    padding-top: 0;
    padding-bottom: 40px;
  }
  &-content {
    color: #3a84ff;
    font-size: 12px;
    cursor: pointer;
    margin-bottom: -3px;
  }
}
.table-edit-disbaled {
  color: #c4c6cc;
  &:hover {
    color: #c4c6cc;
    background-color: #fff;
    cursor: not-allowed;
  }
}
</style>
