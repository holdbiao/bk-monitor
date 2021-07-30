<template>
  <bk-dialog
    width="850"
    :value="isShow"
    :show-footer="false"
    @after-leave="handleback">
    <div class="host-header">
      <div> {{ $t('选择机器') }} </div>
    </div>
    <div class="host-body">
      <bk-input
        class="body-search" :placeholder="$t('请输入')"
        clearable
        right-icon="bk-icon icon-search"
        v-model.trim="keyword"
        @change="handleKeywordChange">
      </bk-input>
      <div class="body-table">
        <bk-table
          height="313"
          ref="hostTableRef" :empty-text="$t('查询无数据')"
          highlight-current-row
          :data="tableData"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick">
          <bk-table-column label="IP" prop="ip"></bk-table-column>
          <bk-table-column :label="$t('Agent状态')">
            <template slot-scope="scope">
              <span :style="{ color: agentColorMap[scope.row.agentStatus] }">{{agentStatusMap[scope.row.agentStatus]}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('云区域')" prop="cloudName"></bk-table-column>
        </bk-table>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
export default {
  name: 'uptime-check-node-edit-table',
  props: {
    isShow: Boolean,
    ipList: Array
  },
  data() {
    return {
      keyword: '', // 搜索关键字
      index: -1,
      tableData: [],
      handleKeywordChange: this.debounce(this.filterIP, 200), // 处理搜索关键字改变事件
      agentStatusMap: {
        '-1': this.$t('Agent异常'),
        0: this.$t('Agent正常'),
        2: this.$t('Agent未安装')
      },
      agentColorMap: {
        '-1': '#EA3636',
        0: '#2DCB56',
        2: '#C4C6CC'
      }
    }
  },
  mounted() {
    this.tableData = this.ipList
  },
  methods: {
    handleback() {
      this.$emit('show-change', false)
    },
    getRowClassName({ row }) {
      return row.isBuilt ? 'table-row-disabled' : ''
    },
    /**
             * @desc 处理表格行点击事件
             */
    handleRowClick(row) {
      if (row.isBuilt) {
        this.$refs.hostTableRef.setCurrentRow()
        return false
      }
      this.tableData = this.ipList
      this.keyword = ''
      this.$refs.hostTableRef.setCurrentRow()
      this.$emit('configIp', row.ip)
      this.$emit('show-change', false)
    },
    debounce(fn, delay) {
      let timer = null
      return (...args) => {
        if (timer) {
          clearTimeout(timer)
        }
        timer = setTimeout(() => {
          fn.apply(this, args)
        }, delay)
      }
    },
    filterIP() {
      if (this.keyword.length) {
        const tableData = this.ipList.filter(item => item.ip.includes(this.keyword))
        this.tableData = tableData
      } else {
        this.tableData = this.ipList
      }
    }
  }
}
</script>

<style lang="scss" scoped>
    .host-header {
      margin-top: -20px;
      width: 120px;
      height: 31px;
      line-height: 31px;
      font-size: 24px;
      color: #444;
      margin-bottom: 7px;
    }
    .host-body {
      width: 802px;
      .body-search {
        margin-bottom: 10px;
      }
      .body-table {
        /deep/ .bk-table-row.table-row-disabled {
          background: #fafbfd;
          color: #c4c6cc;
          cursor: not-allowed;
        }
      }
    }
</style>
