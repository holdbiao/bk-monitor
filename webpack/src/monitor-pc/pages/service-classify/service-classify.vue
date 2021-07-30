<template>
  <div class="service-classify" v-monitor-loading="{ isLoading: loading }">
    <div class="service-classify-tool">
      <bk-button class="tool-btn mc-btn-add" theme="primary" @click="handleShowAddView"> {{ $t('新建') }} </bk-button>
      <div class="tool-explanation"><i class="icon-monitor icon-tips"></i><span> {{ $t('修改或删除分类请') }} <span class="tool-span" @click="handleToCMDB"> {{ $t('前往CMDB') }} </span></span></div>
      <bk-input class="tool-search" :placeholder="$t('一级分类/二级分类')" right-icon="bk-icon icon-search" @change="handleSearch"></bk-input>
    </div>
    <div class="service-classify-panel">
      <ul class="panel-tab">
        <li class="panel-tab-item" v-for="(item,index) in panel.data" :key="index" :class="{ 'tab-active': index === panel.active }" @click="index !== panel.active && handleTabItemClick(index)">
          <span class="tab-name">{{item.name}}</span>
          <span class="tab-mark">{{item.total}}</span>
        </li>
        <li class="panel-tab-blank"></li>
      </ul>
    </div>
    <div class="service-classify-table">
      <bk-table :empty-text="$t('查询无数据')"
                @row-mouse-enter="i => table.hoverIndex = i"
                @row-mouse-leave="i => table.hoverIndex = -1"
                :data="table.data">
        <bk-table-column
          v-if="false" :label="$t('所属')"
          prop="bizName"
          min-width="120">
        </bk-table-column>
        <bk-table-column :label="$t('一级分类')"
                         prop="first"
                         min-width="100">
        </bk-table-column>
        <bk-table-column :label="$t('二级分类')"
                         min-width="100">
          <template slot-scope="scope">
            <div class="table-row">
              <span class="col-edit" v-if="scope.$index !== table.editIndex">{{scope.row.second}}</span>
              <!-- <bk-input v-if="scope.$index === table.editIndex" :ref="'label-' + scope.$index"
                                        :maxlength="50"
                                        v-model="table.editName"
                                        @keydown="handleLabelKey(scope, ...arguments)"
                                        v-bk-clickoutside="handleTagClickout"></bk-input>
                                    <i @click.stop.prevent="handleEditLabel(scope, $event)" v-show="scope.$index !== table.editIndex && table.hoverIndex === scope.$index" class="icon-monitor icon-bianji col-btn" style="font-size: 24px "></i> -->
            </div>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('指标数')"
                         min-width="100">
          <template slot-scope="scope">
            <div class="col-target">
              <span class="col-btn" :class="{ 'zero': !scope.row.metricCount }" @click="handleToTarget(scope.row)">{{scope.row.metricCount}}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('采集配置')"
                         min-width="100">
          <template slot-scope="scope">
            <div class="col-config">
              <span
                v-authority="{ active: !authority.COLLECTION_VIEW_AUTH }"
                class="col-btn"
                :class="{ 'zero': !scope.row.configCount }"
                @click="authority.COLLECTION_VIEW_AUTH
                  ? handleToCollectionConfig(scope.row)
                  : handleShowAuthorityDetail(serviceClassifyAuth.COLLECTION_VIEW_AUTH)">
                {{scope.row.configCount}}
              </span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('策略配置')"
                         min-width="100">
          <template slot-scope="scope">
            <div class="col-config">
              <span
                v-authority="{ active: !authority.RULE_VIEW_AUTH }"
                class="col-btn"
                :class="{ 'zero': !scope.row.strategyCount }"
                @click="authority.RULE_VIEW_AUTH
                  ? handleToStrategyConfig(scope.row)
                  : handleShowAuthorityDetail(serviceClassifyAuth.RULE_VIEW_AUTH)">
                {{scope.row.strategyCount}}
              </span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('操作')"
                         width="150">
          <template slot-scope="scope">
            <span
              v-authority="{ active: !authority.EXPORT_MANAGE_AUTH }"
              class="col-btn"
              @click="authority.EXPORT_MANAGE_AUTH
                ? handleConfigurationExport(scope.row)
                : handleShowAuthorityDetail(serviceClassifyAuth.EXPORT_MANAGE_AUTH)">
              {{ $t('配置导出') }}
            </span>
          </template>
        </bk-table-column>
      </bk-table>
      <div class="alarm-group-pagination">
        <template v-if="tableInstance">
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
</template>

<script>
import TableStore from './store'
import { serviceCategoryList } from '../../../monitor-api/modules/service_classify'
import { debounce } from 'throttle-debounce'
import { commonPageSizeMixin } from '../../common/mixins'
import * as serviceClassifyAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'

export default {
  name: 'ServiceClassify',
  mixins: [commonPageSizeMixin, authorityMixinCreate(serviceClassifyAuth)],
  data() {
    return {
      serviceClassifyAuth,
      header: {
        keyword: '',
        handelSearch() {

        }
      },
      loading: true,
      panel: {
        isLoading: false,
        active: 0,
        data: [
          {
            name: this.$t('服务分类'),
            total: 0
          }
          // {
          //     name: '主机分类',
          //     total: '29'
          // }
        ]
      },
      table: {
        data: [],
        tableData: [],
        loading: false,
        hoverIndex: -1,
        editIndex: -1,
        editName: ''
      },
      tableInstance: null,
      bizList: []
    }
  },
  created() {
    this.bizList = this.$store.getters.bizList
    this.handleGetListData()
    this.handleSearch = debounce(300, this.handleKeywordChange)
  },
  methods: {
    handleGetListData(needLoading = true) {
      this.loading = needLoading
      serviceCategoryList().then((data) => {
        const biz = this.bizList.find(item => item.id === this.$store.getters.bizId)
        this.tableInstance = new TableStore(data, biz.text)
        this.panel.data[0].total = this.tableInstance.total || 0
        this.table.data = this.tableInstance.getTableData()
      })
        .finally(() => {
          this.loading = false
        })
    },
    handleTabItemClick(index) {
      this.panel.active = index
      const { tableInstance } = this
      tableInstance.page = 1
      this.table.data = this.getTableData()
    },
    handleKeywordChange(v) {
      this.tableInstance.keyword = v
      this.tableInstance.keyword = v
      this.tableInstance.page = 1
      this.table.data = this.tableInstance.getTableData()
    },
    handleToCMDB() {
      window.open(`${this.$store.getters.cmdbUrl}/#/business/${this.$store.getters.bizId}/service/cagetory`, '_blank')
    },
    handleToTarget() {
      // alert('跳转到指标数')
    },
    handleToCollectionConfig(data) {
      if (!data.configCount) return
      this.$router.push({
        name: 'collect-config',
        params: {
          serviceCategory: `${data.first}-${data.second}`
        }
      })
    },
    handleToStrategyConfig(data) {
      if (!data.strategyCount) return
      this.$router.push({
        name: 'strategy-config',
        params: {
          serviceCategory: `${data.first}-${data.second}`
        }
      })
    },
    handleConfigurationExport(row) {
      const params = {
        first: row.first,
        second: row.second
      }
      this.$router.push({
        name: 'export-configuration',
        params
      })
    },
    handlePageChange(page) {
      this.tableInstance.page = page
      this.table.data = this.tableInstance.getTableData()
    },
    handleLimitChange(limit) {
      this.tableInstance.page = 1
      this.tableInstance.pageSize = limit
      this.handleSetCommonPageSize(limit)
      this.table.data = this.tableInstance.getTableData()
    },
    handleShowAddView() {
      window.open(`${this.$store.getters.cmdbUrl}/#/business/${this.$store.getters.bizId}/service/cagetory`, '_blank')
    }
  }
}
</script>

<style lang="scss" scoped>
    .service-classify {
      min-height: calc(100vh - 80px);
      font-size: 12px;
      color: #63656e;
      &-tool {
        display: flex;
        align-items: center;
        .tool-explanation {
          margin-left: 21px;
          margin-right: auto;
          display: flex;
          align-items: center;
          .tool-span {
            color: #3a84ff;
            cursor: pointer;
          }
          i {
            margin-top: 3px;
            font-size: 14px;
            color: #979ba5;
            margin-right: 7px;
          }
        }
        .tool-search {
          width: 360px;
        }
      }
      &-panel {
        height: 52px;
        background: #fff;
        margin-top: 16px;
        border: 1px solid #dcdee5;
        border-bottom: 0;
        border-radius: 2px 2px 0 0;
        .panel-tab {
          display: flex;
          background: #fafbfd;
          padding: 0;
          margin: 0;
          overflow: auto;
          &-item {
            display: flex;
            flex: 0 0 auto;
            min-width: 120px;
            align-items: center;
            justify-content: center;
            color: #63656e;
            font-size: 14px;
            height: 42px;
            border-bottom: 1px solid #dcdee5;
            border-right: 1px solid #dcdee5;
            padding: 0 20px;
            cursor: pointer;
            .tab-name {
              font-weight: bold;
              margin-right: 6px;
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
            &:hover {
              cursor: pointer;
              color: #3a84ff;
            }
          }
          &-blank {
            flex: 1;
            height: 42px;
            border-bottom: 1px solid #dcdee5;
          }
        }
      }
      &-table {
        background: #fff;
        .table-row {
          display: flex;
          align-items: center;
          height: 32px;
        }
        .col {
          &-target {
            width: 48px;
            text-align: right;
          }
          &-config {
            width: 58px;
            text-align: right;
          }
          &-btn {
            color: #3a84ff;
            cursor: pointer;
            margin-right: 12px;
          }
          &-edit {
            margin-right: 3px;
          }
        }
        .zero {
          color: #c4c6cc;
          cursor: not-allowed;
        }
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
        .alarm-group-pagination {
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
</style>
