<template>
  <bk-dialog
    width="850"
    :value="conf.isShow"
    :show-footer="false"
    @input="close"
    @after-leave="handleAfterLeaveChange">
    <div class="host-header">
      <div class="host-header-title"> {{ title }} </div>
    </div>
    <div class="host-body">
      <bk-input
        class="body-search" :placeholder="$t('请输入')"
        clearable
        right-icon="bk-icon icon-search"
        v-model.trim="keyword"
        @input="handleKeywordChange"
        ref="selectInput">
      </bk-input>
      <div class="body-table" v-bkloading="{ isLoading: isLoading }">
        <bk-table
          class="select-host-table-wrap"
          ref="hostTableRef"
          height="313" :empty-text="$t('查询无数据')"
          highlight-current-row
          :data="tableData"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick">
          <bk-table-column label="IP" prop="ip"></bk-table-column>
          <bk-table-column :label="$t('系统')" prop="osName"></bk-table-column>
          <bk-table-column :label="$t('Agent状态')">
            <template slot-scope="scope">
              <span :class="scope.row.agentStatus === 0 ? 'success' : 'error'"
                    v-bk-tooltips="{ content: `${scope.row.agentStatusName}${$t('不能进行调试')}`,
                                     boundary: 'window', disabled: scope.row.agentStatus === 0 }"
              >{{scope.row.agentStatusName}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('云区域')" prop="cloudName"></bk-table-column>
        </bk-table>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
import { hostAgentStatus } from '../../../../../../monitor-api/modules/commons'
import { deepClone } from '../../../../../../monitor-common/utils/utils'
export default {
  name: 'SelectHost',
  props: {
    conf: {
      type: Object,
      default: () => ({
        isShow: false,
        id: '',
        param: {}
      })
    },
    getHost: Function,
    filter: Function
  },
  data() {
    return {
      isLoading: false,
      keyword: '', // 搜索关键字
      host: {
        index: -1
      }, // 主机信息
      index: -1,
      tableData: [],
      allHost: [],
      handleKeywordChange: this.debounce(this.filterHost, 200) // 处理搜索关键字改变事件
    }
  },
  computed: {
    title() {
      return this.conf.param?.osType === 'windows' ? this.$t('选择{0}调试主机', ['Windows']) : this.$t('选择{0}调试主机', ['Linux'])
    }
  },
  watch: {
    'conf.param': {
      handler(val) {
        this.host = val
        this.requestHost(this.conf.id)
      },
      deep: true
    },
    'conf.isShow': {
      handler(val) {
        if (val) {
          setTimeout(() => {
            this.$refs.selectInput.focus()
          }, 300)
        }
      }
    }
  },
  mounted() {
    if (this.getHost) {
      this.isLoading = true
      this.getHost().then((data) => {
        this.allHost = data.map(item => ({
          ip: item.bk_host_innerip, // IP
          osType: item.bk_os_type, // 系统类型
          osName: item.bk_os_name, // 系统名称
          agentStatus: item.agent_status, // Agent 状态代码
          agentStatusName: item.agent_status_display, // Agent 状态名称
          cloudName: item.bk_cloud_name, // 云区域
          cloudId: item.bk_cloud_id, // cloudId
          companyId: '', // 服务商 ID
          bk_biz_id: item.bk_biz_id,
          supplierId: item.bk_supplier_account
        }))
        this.tableData = this.allHost
      })
        .finally(() => {
          this.isLoading = false
        })
    }
  },
  methods: {
    /**
    * @desc 关闭弹框
    */
    close(isShow = false) {
      const conf = deepClone(this.conf)
      conf.isShow = isShow
      this.$emit('update:conf', conf)
    },
    /**
    * @desc 弹框关闭回调函数
    */
    handleAfterLeaveChange() {
      this.keyword = ''
      this.host = {}
      this.$refs.hostTableRef.setCurrentRow()
    },
    /**
    * @desc 搜索主机
    */
    requestHost(id) {
      if (this.getHost) return
      this.isLoading = true
      hostAgentStatus({
        bk_biz_id: id
      }).then((data) => {
        this.allHost = this.handleHostData(data)
        this.filterHost()
      })
        .finally(() => {
          this.isLoading = false
        })
    },
    /**
    * @desc 处理主机数据
    * @param {Arrya} data - 源数据
    * @return {Array}
    */
    handleHostData(data) {
      if (Array.isArray(data) && data.length > 0) {
        return data.map(item => ({
          ip: item.bk_host_innerip, // IP
          osType: item.bk_os_type, // 系统类型
          osName: item.bk_os_name, // 系统名称
          agentStatus: item.agent_status, // Agent 状态代码
          agentStatusName: item.agent_status_display, // Agent 状态名称
          cloudName: item.bk_cloud_name, // 云区域
          cloudId: item.bk_cloud_id, // cloudId
          companyId: '', // 服务商 ID
          bk_biz_id: item.bk_biz_id
        }))
      }
      return []
    },
    /**
    * @desc 获取表格行样式
    */
    getRowClassName({ row }) {
      return row.agentStatus === 0 ? 'table-row-selected' : 'table-row-disabled'
    },
    /**
    * @desc 处理表格行点击事件
    */
    handleRowClick(row) {
      if (row.agentStatus !== 0) {
        this.$bkMessage({
          theme: 'warning',
          message: this.$t('无法选择Agent状态异常的服务器')
        })
        this.$refs.hostTableRef.setCurrentRow()
        return
      }
      this.$emit('confirm', { ...this.host, ...row, osType: this.host.osType, osName: this.host.osType })
      this.close()
    },
    /**
    * @desc 去抖函数
    */
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
    /**
    * @desc 过滤主机
    */
    filterHost(val) {
      if (val) {
        this.tableData = this.filter
          ? this.filter(val, this.allHost)
          : this.allHost.filter(item => this.matchOsType(item.osType) && item.ip.includes(val))
            .sort((itemPre, itemNext) => itemPre.ip.length - itemNext.ip.length)
      } else {
        this.tableData = this.filter
          ? this.filter(val, this.allHost)
          : this.allHost.filter(item => this.matchOsType(item.osType))
      }
    },
    // 目标主机匹配条件
    matchOsType(osType, osTypeId = this.host.osTypeId) {
      if (osTypeId === '4') { // Liunx_arrch64平台
        return osType === '1'
      }
      return osType === osTypeId
    }
  }
}
</script>

<style lang="scss" scoped>
    .host-header {
      margin-top: -15px;
      width: 120px;
      height: 26px;
      line-height: 26px;
      font-size: 20px;
      color: #444;
      margin-bottom: 18px;
      &-title {
        width: 400px;
      }
    }
    .host-body {
      width: 802px;
      .body-search {
        margin-bottom: 10px;
      }
      .body-table {
        .success {
          color: #2dcb56;
        }
        .error {
          color: #ea3636;
        }
        /deep/ .bk-table-row.table-row-selected {
          cursor: pointer;
        }
        /deep/ .bk-table-row.table-row-disabled {
          cursor: not-allowed;
        }
      }
    }
</style>
<style lang="scss">
.select-host-table-wrap {
  .bk-table-body-wrapper {
    overflow-y: auto;
    height: 271px;
  }
}
</style>
