<template>
  <div class="strategy-detail-table detail-content" v-bkloading="{ isLoading: strategyTarget.loading }">
    <div v-if="tableData.length">
      <!-- 表格 -->

      <bk-table
        v-if="targetType === 'INSTANCE'"
        :empty-text="$t('查询无数据')"
        :outer-border="false"
        :header-border="false"
        :data="tableData">
        <bk-table-column label="IP" prop="ip" min-width="120"></bk-table-column>
        <bk-table-column :label="$t('Agent状态')" min-width="100">
          <template slot-scope="scope">
            <span v-if="scope.row.agentStatus" :style="{ 'color': statusColorMap[scope.row.agentStatus] }">{{ statusMap[scope.row.agentStatus] }}</span>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('云区域')" prop="bkCloudName" min-width="250">
          <template slot-scope="scope">
            <span>{{scope.row.bkCloudName || '--'}}</span>
          </template>
        </bk-table-column>
      </bk-table>
      <bk-table
        :empty-text="$t('查询无数据')"
        :data="tableData"
        v-else-if="['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(targetType) || objType === 'SERVICE'">
        <bk-table-column :label="$t('节点名称')" prop="nodePath" min-width="120"></bk-table-column>
        <bk-table-column v-if="objType === 'SERVICE'" :label="$t('当前实例数')" min-width="100">
          <template slot-scope="scope">
            <div class="target-count">{{ scope.row.count }}</div>
          </template>
        </bk-table-column>
        <bk-table-column v-else-if="targetType === 'TOPO'" :label="$t('当前主机数')" min-width="100">
          <template slot-scope="scope">
            <div class="target-count">{{ scope.row.count }}</div>
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('分类')" min-width="250">
          <template slot-scope="scope">
            <div class="monitoring-target">
              <div v-for="(item, index) in scope.row.labels" :key="index" class="target-labels">
                <div class="label-first">{{ item.first }}</div>
                <div class="label-second">{{ item.second }}</div>
              </div>
            </div>
          </template>
        </bk-table-column>
      </bk-table>
      <div class="table-mask"></div>
      <!-- 分页 -->
      <!-- <bk-pagination
                key="sdfsdfsdf"
                class="table-pagination"
                align="right"
                size="small"
                pagination-able
                show-total-count
                :current="tableInstance.page"
                :limit="tableInstance.pageSize"
                :count="tableInstance.total"
                :limit-list="tableInstance.pageList"
                @change="handlePageChange"
                @limit-change="handleLimitChange">
            </bk-pagination> -->
    </div>
    <!-- 无数据 -->
    <div v-else class="table-no-data">
      <i class="icon-monitor icon-tishi"></i>
      <span class="table-no-data-explain"> {{ $t('暂无任何监控目标') }} </span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StrategyConfigDetailTable',
  props: {
    // 表格数据
    tableData: {
      type: Array,
      default: () => ([])
    },
    targetType: String,
    objType: String
  },
  data() {
    return {
      statusColorMap: {
        normal: '#2DCB56',
        abnormal: '#EA3636',
        not_exist: '#C4C6CC'
      },
      statusMap: {
        normal: `Agent ${this.$t('正常')}`,
        abnormal: `Agent ${this.$t('异常')}`,
        not_exist: `Agent ${this.$t('未安装')}`
      },
      strategyTarget: {
        type: '',
        data: [],
        tableData: [],
        loading: false
      },
      tableInstance: {
        page: 1,
        pageSize: 10,
        pageList: [10, 20, 50, 100],
        total: 0
      }
    }
  },
  watch: {
    tableData: {
      handler() {
        this.tableData && this.handleTableData(false)
      },
      immediate: true
    }
  },
  methods: {
    // table数据变更事件
    handleTableData(needLoading = true, time) {
      this.strategyTarget.loading = needLoading
      const { tableInstance } = this
      const ret = this.tableData
      this.tableInstance.total = ret.length
      this.strategyTarget.tableData = ret.slice(
        tableInstance.pageSize * (tableInstance.page - 1),
        tableInstance.pageSize * tableInstance.page
      )
      if (needLoading) {
        setTimeout(() => {
          this.strategyTarget.loading = false
        }, time)
      }
    },
    // 分页切换事件
    handlePageChange(page) {
      this.tableInstance.page = page
      this.handleTableData(false, 50)
    },
    // 每页条数切换事件
    handleLimitChange(limit) {
      this.tableInstance.page = 1
      this.tableInstance.pageSize = limit
      this.handleTableData(false, 50)
    }
  }
}
</script>

<style lang="scss" scoped>
    .strategy-detail-table {
      margin-top: 18px;
      height: 478px;
      position: relative;
      /deep/ .bk-table-body-wrapper {
        overflow-y: auto;
        overflow-x: hidden;
        max-height: 433px;
      }
      .table-mask {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 5px;
        z-index: 9;
        background-color: #fff;
      }
      .target-count {
        text-align: right;
        width: 59px;
      }
      .monitoring-target {
        display: flex;
        flex-wrap: wrap;
        padding: 6px 0 4px 0;
      }
      .target-labels {
        display: flex;
        margin: 0 6px 2px 0;
      }
      .label-first {
        padding: 3px 10px 5px;
        border: 1px solid #dcdee5;
        border-radius: 2px 0 0 2px;
        background: #fafbfd;
      }
      .label-second {
        padding: 3px 10px 5px;
        border: 1px solid #dcdee5;
        border-radius: 0 2px 2px 0;
        border-left: 0;
        background: #fff;
      }
      .table-pagination {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 60px;
        padding: 0 20px;
        border: 1px solid #dcdee5;
        border-top: 0;
        background: #fff;
        /deep/ .bk-page-count {
          margin-right: auto;
        }
      }
      .table-no-data {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        i {
          color: #dcdee5;
          font-size: 28px;
          margin: 208px 0 13px 0;
        }
        &-explain {
          font-size: 14px;
          margin-bottom: 3px;
        }
      }
    }
</style>
