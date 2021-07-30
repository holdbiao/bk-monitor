<template>
  <div class="config-deploy">
    <!-- <div class="config-deploy-description" v-if="$route.name === 'collect-config-operate-detail'">
            <i class="icon-monitor icon-tips item-icon"></i><span>该内容是对{{config.name}}进行 "<span class="operation-step-name">{{operationStepName}}</span>" 操作的执行详情</span>
        </div> -->
    <div class="config-deploy-header" v-if="isRunning">
      <div class="bk-button-group">
        <bk-button @click="header.status = 'ALL'" :class="{ 'is-selected': header.status === 'ALL' }" size="normal"> {{ $t('全部') }}({{header.data.total}})</bk-button>
        <bk-button @click="header.status = 'SUCCESS'" :class="{ 'is-selected': header.status === 'SUCCESS' }" size="normal"> {{ $t('正常') }}({{header.data.successNum}})</bk-button>
        <bk-button @click="header.status = 'FAILED'" :class="{ 'is-selected': header.status === 'FAILED' }" size="normal"> {{ $t('异常') }}({{header.data.failedNum}})</bk-button>
        <bk-button @click="header.status = 'RUNNING'" :class="{ 'is-selected': header.status === 'RUNNING' }" size="normal"> {{ $t('执行中') }}({{header.data.pendingNum}})</bk-button>
      </div>
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH }"
        :icon="header.batchRetry ? 'loading' : ''"
        :disabled="header.batchRetry || !(header.data.failedNum > 0 && header.data.pendingNum === 0)"
        class="header-retry"
        hover-theme="primary"
        @click="authority.MANAGE_AUTH ? handleBatchRetry() : handleShowAuthorityDetail()">
        <i v-if="!header.batchRetry" class="icon-monitor icon-mc-retry"></i>
        {{ $t('失败批量重试') }}
      </bk-button>
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH }"
        :icon="disBatch ? 'loading' : ''"
        :disabled="!haveDeploying || disBatch"
        class="header-retry"
        hover-theme="primary"
        @click="authority.MANAGE_AUTH ? handleBatchStop() : handleShowAuthorityDetail()">
        {{ $t('批量终止') }}
      </bk-button>
    </div>
    <div class="config-deploy-content" v-if="content.length">
      <right-panel class="content-panel"
                   v-for="(item, index) in content"
                   :key="index"
                   need-border
                   :collapse="item.expand"
                   @change="handleCollapseChange(item, $event)"
                   title-bg-color="#F0F1F5"
                   :collapse-color="item.child.length ? '#313238' : '#C4C6CC'"
                   :class="{ 'no-data': !item.child.length }"
                   :style="{ borderBottomWidth: item.expand ? '0' : '1px' }">
        <bk-table class="content-panel-table" :data="item.table" :empty-text="$t('查询无数据')" max-height="450">
          <bk-table-column min-width="120" :label="$t('目标')" prop="instance_name"></bk-table-column>
          <bk-table-column width="120" :label="$t('状态')">
            <template slot-scope="props">
              <div class="col-status">
                <img class="col-status-img" v-if="isRunning && statusList.includes(props.row.status)" src="../../../static/images/svg/spinner.svg" />
                <div class="col-status-radius" v-if="isRunning && ['FAILED','WARNING','SUCCESS','STOPPED'].includes(props.row.status)"
                     :style="{ 'border-color': statusMap[props.row.status].border, background: statusMap[props.row.status].color }"></div>
                <span v-if="isRunning">{{statusMap[props.row.status].name}}</span>
                <span v-else>--</span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column width="90" :label="$t('版本')" prop="plugin_version">
          </bk-table-column>
          <bk-table-column :label="$t('详情')" min-width="200">
            <template slot-scope="props">
              <div class="col-detail">
                <span class="col-detail-data">{{props.row.log || '--'}}</span>
                <span class="col-detail-more" v-if="isRunning && props.row.status === 'FAILED'" @click="handleGetMoreDetail(props.row)"> {{ $t('详情') }} </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column width="80" label="">
            <template slot-scope="props">
              <div
                v-authority="{ active: !authority.MANAGE_AUTH }"
                class="col-retry"
                v-if="isRunning && props.row.status === 'FAILED'"
                @click="authority.MANAGE_AUTH ? handleRetry(props.row, item) : handleShowAuthorityDetail()">
                {{ $t('重试') }}
              </div>
              <div
                v-authority="{ active: !authority.MANAGE_AUTH }"
                class="col-retry"
                v-if="isRunning && ['DEPLOYING','RUNNING','PENDING'].includes(props.row.status)"
                @click="authority.MANAGE_AUTH ? handleRevoke(props.row, item) : handleShowAuthorityDetail()">
                {{ $t('终止') }}
              </div>
            </template>
          </bk-table-column>
        </bk-table>
        <template slot="pre-panel">
          <div class="pre-panel" v-if="item.is_label">
            <span class="pre-panel-name" :style="{ backgroundColor: labelMap[item.label_name].color }">{{labelMap[item.label_name].name}}</span>
            <span class="pre-panel-mark" :style="{ borderColor: labelMap[item.label_name].color }"></span>
          </div>
        </template>
        <div slot="title" class="panel-title">
          <span class="title-name">{{item.node_path}}</span>
          <div class="total">
            <template v-if="isRunning">
              <span class="num" v-if="item.successNum"><span style="color: #2dcb56;">{{item.successNum}}</span> {{ $t('个成功') }} <span v-if="item.failedNum || item.pendingNum">,</span></span>
              <span class="num" v-if="item.failedNum"><span style="color: #ea3636;">{{item.failedNum}}</span> {{ $t('个失败') }} <span v-if="item.pendingNum">,</span></span>
              <span class="num" v-if="item.pendingNum"><span style="color: #3a84ff;">{{item.pendingNum}}</span> {{ $t('个执行中') }} </span>
              <span class="num" v-else-if="!item.child.length">共 <span style="color: #63656e;">0</span> {{config.target_object_type === 'HOST' ? $t('台主机') : $t('个实例')}}</span>
            </template>
            <span class="num" v-else>共 {{item.successNum + item.failedNum + item.pendingNum}} {{config.target_object_type === 'HOST' ? $t('台主机') : $t('个实例')}}</span>
          </div>
        </div>
      </right-panel>
    </div>
    <bk-sideslider :is-show.sync="side.show" :quick-close="true" :width="900" :title="side.title">
      <div class="side-detail" slot="content" v-bkloading="{ isLoading: side.loading }">
        <pre class="side-detail-code">{{side.detail}}</pre>
      </div>
    </bk-sideslider>
  </div>
</template>
<script>
import RightPanel from '../../../components/ip-select/right-panel'
import { retryTargetNodes,
  getCollectLogDetail,
  batchRetry,
  batchRevokeTargetNodes,
  revokeTargetNodes,
  isTaskReady } from '../../../../monitor-api/modules/collecting'
export default {
  name: 'CollectorHostStatus',
  components: {
    RightPanel
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  props: {
    allData: {
      type: Object,
      required: true
    },
    isRunning: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      disBatch: false,
      header: {
        status: 'ALL',
        batchRetry: false,
        data: {
          successNum: 0,
          failedNum: 0,
          pendingNum: 0,
          total: 0
        }
      },
      content: null,
      config: null,
      refresh: true,
      operationStepName: '',
      statusList: ['PENDING', 'RUNNING', 'DEPLOYING', 'STARTING', 'STOPPING'],
      labelMap: {
        ADD: {
          color: '#3A84FF',
          name: this.$t('新增')
        },
        REMOVE: {
          color: '#6C3AFF',
          name: this.$t('删除')
        },
        UPDATE: {
          color: '#FF9C01',
          name: this.$t('变更')
        },
        RETRY: {
          color: '#414871',
          name: this.$t('重试')
        }
      },
      statusMap: {
        SUCCESS: {
          color: '#94F5A4',
          border: '#2DCB56',
          name: this.$t('正常')
        },
        FAILED: {
          color: '#FD9C9C',
          border: '#EA3636',
          name: this.$t('异常')
        },
        PENDING: {
          color: '#3A84FF',
          name: this.$t('等待中')
        },
        RUNNING: {
          color: '#3A84FF',
          name: this.$t('执行中')
        },
        DEPLOYING: {
          color: '#3A84FF',
          name: this.$t('部署中')
        },
        STARTING: {
          color: '#3A84FF',
          name: this.$t('启用中')
        },
        STOPPING: {
          color: '#F0F1F5',
          border: '#C4C6CC',
          name: this.$t('停用中')
        }
      },
      side: {
        show: false,
        title: '',
        detail: '',
        loading: false
      }
    }
  },
  computed: {
    haveDeploying() {
      const resArr = []
      this.content.forEach((item) => {
        const res = item.child.some(one => ['DEPLOYING', 'RUNNING', 'PENDING'].includes(one.status))
        resArr.push(res)
      })
      return resArr.some(item => item)
    }
  },
  watch: {
    allData: {
      handler(v) {
        if (this.refresh) {
          this.handleData(v)
        }
      },
      immediate: true
    },
    'header.status': {
      handler: 'handleStatusChange'
    }
  },
  methods: {
    handleData(data) {
      this.config = data.config_info
      const { status } = this.header
      this.header.data = data.headerData
      this.content = data.contents
      this.content.forEach((item) => {
        item.child.forEach((set) => {
          if (this.statusList.includes(set.status) || set.status === status || status === 'ALL') {
            item.table.push(set)
          }
        })
      })
      const operationStepMap = {
        ADD_DEL: this.$t('增删目标'),
        UPGRADE: this.$t('升级'),
        CREATE: this.$t('创建'),
        EDIT: this.$t('编辑'),
        START: this.$t('启用'),
        STOP: this.$t('停用'),
        ROLLBACK: this.$t('回滚')
      }
      this.operationStepName = operationStepMap[this.config.last_operation]
    },
    async handleRetry(data, table) {
      this.refresh = false
      if (this.side.title === data.instance_name) {
        this.side.title = ''
      }
      const node = this.config.target_object_type === 'HOST'
        ? {
          ip: data.ip,
          bk_cloud_id: data.bk_cloud_id,
          bk_supplier_id: data.bk_supplier_id
        } : {
          service_instance_id: data.service_instance_id
        }
      this.content.forEach((item) => {
        if (item.child && item.child.length) {
          const setData = item.child.find(set => set.instance_id === data.instance_id && set.status === 'FAILED')
          if (setData) {
            setData.status = 'PENDING'
            item.pendingNum += 1
            item.failedNum -= 1
          }
        }
      })
      this.header.data.pendingNum += 1
      this.header.data.failedNum -= 1
      this.handlePolling(false)
      retryTargetNodes({
        id: this.config.id,
        target_nodes: [node],
        steps: data.steps
      }).then(async () => {
        const isReady = await this.taskReadyStatus(this.config.id)
        if (isReady) {
          this.refresh = true
          this.handlePolling()
        }
      })
        .catch(() => {
          data.status = 'FAILED'
          table.pendingNum -= 1
          table.failedNum += 1
          this.header.data.pendingNum -= 1
          this.header.data.failedNum += 1
          this.refresh = true
          this.handlePolling()
        })
    },
    handleRevoke(data, table) {
      revokeTargetNodes({
        id: this.config.id,
        instance_ids: [data.instance_id]
      }).finally(() => {
        data.status = 'FAILED'
        table.pendingNum -= 1
        table.failedNum += 1
        this.header.data.pendingNum -= 1
        this.header.data.failedNum += 1
        this.refresh = true
        this.handleRefreshData()
      })
    },
    async handleBatchRetry() {
      const failed = []
      this.refresh = false
      this.header.batchRetry = true
      this.side.title = ''
      this.content.forEach((item) => {
        item.child.forEach((set) => {
          if (set.status === 'FAILED') {
            set.status = 'PENDING'
            failed.push(set)
          }
        })
        item.pendingNum += item.failedNum
        item.failedNum = 0
      })
      this.header.data.pendingNum += this.header.data.failedNum
      this.header.data.failedNum = 0
      this.handlePolling(false)
      batchRetry({
        id: this.config.id
      }).then(async () => {
        const isReady = await this.taskReadyStatus(this.config.id)
        if (isReady) {
          this.header.batchRetry = false
          this.refresh = true
          this.handlePolling()
        }
      })
        .catch(() => {
          failed.forEach((item) => {
            item.status = 'FAILED'
          })
          this.header.data.pendingNum = 0
          this.header.data.failedNum = failed.length
          this.header.batchRetry = false
          this.refresh = true
          this.handlePolling()
        })
    },
    handleBatchStop() {
      this.refresh = false
      this.disBatch = true
      batchRevokeTargetNodes({
        id: this.config.id
      }).finally(() => {
        this.disBatch = false
        this.header.batchRetry = false
        this.refresh = true
        this.handleRefreshData()
      })
    },
    bkMsg(theme, message) {
      this.$bkMessage({
        theme,
        message,
        ellipsisLine: 0
      })
    },
    handlePolling(v = true) {
      this.$emit('can-polling', v)
    },
    handleRefreshData() {
      this.$emit('refresh')
    },
    handleStatusChange(status) {
      this.content.forEach((item) => {
        item.table = []
        item.child.forEach((set) => {
          if ((status === 'RUNNING' && this.statusList.includes(set.status))
          || set.status === status || status === 'ALL') {
            item.table.push(set)
          }
        })
      })
    },
    handleCollapseChange(item, v) {
      if (item.child.length) {
        item.expand = v
      }
    },
    handleGetMoreDetail(data) {
      this.side.show = true
      if (this.side.title !== data.instance_name) {
        this.side.title = data.instance_name
        this.side.loading = true
        getCollectLogDetail({
          id: this.config.id,
          instance_id: data.instance_id,
          task_id: data.task_id
        }, { needMessage: false }).then((data) => {
          this.side.detail = data.log_detail
          this.side.loading = false
        })
          .catch((err) => {
            this.bkMsg('error', err.message || this.$t('获取更多数据失败'))
            this.side.show = false
            this.side.loading = false
          })
      }
    },
    async taskReadyStatus(id) {
      let timer = null
      clearTimeout(timer)
      return new Promise(async (resolve) => {
        const show = await isTaskReady({ collect_config_id: id })
        if (show) {
          resolve(true)
        } else {
          timer = setTimeout(() => {
            this.taskReadyStatus(id).then((res) => {
              resolve(res)
            })
          }, 2000)
        }
      })
    }
  }
}
</script>
<style lang="scss" scoped>
    .config-deploy {
      &-description {
        margin-bottom: 20px;
        height: 16px;
        line-height: 16px;
        font-size: 12px;
        color: #63656e;
        .icon-tips {
          color: #979ba5;
          margin-right: 7px;
        }
        .operation-step-name {
          font-weight: bold;
        }
      }
      &-header {
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        .header-retry {
          margin-left: 10px;
          .icon-monitor {
            margin-right: 6px;
            display: inline-block;
          }
        }
        /deep/ .icon-loading {
          margin-right: 4px;
          &::before {
            display: none;
          }
        }
      }
      &-content {
        .no-data {
          /deep/ .right-panel-title {
            cursor: not-allowed;
          }
        }
        .pre-panel {
          height: 24px;
          display: flex;
          color: #fff;
          font-size: 12px;
          align-items: center;
          margin-left: -17px;
          margin-right: 10px;
          &-name {
            height: 24px;
            background: #3a84ff;
            display: flex;
            align-items: center;
            z-index: 2;
            padding-left: 6px;
          }
          &-mark {
            flex: 0 0 0px;
            border-width: 6px;
            transform: scaleY(2);
            border-style: solid;
            border-color: #3a84ff transparent #3a84ff #3a84ff;

            /* stylelint-disable-next-line declaration-no-important */
            border-right-color: transparent !important;
          }
        }
        .panel-title {
          display: flex;
          align-items: center;
          .title-name {
            margin-right: 24px;
            color: #63656e;
            font-weight: bold;
          }
        }
        .content-panel {
          margin-bottom: 20px;
          &-table {
            background-color: #fff;
          }
          .col-status {
            display: flex;
            align-items: center;
            &-img {
              width: 16px;
              margin-right: 5px;
            }
            &-radius {
              width: 8px;
              height: 8px;
              margin: 4px 10px 4px 4px;
              border-radius: 50%;
              border: 1px solid;
            }
          }
          .col-retry {
            color: #3a84ff;
            cursor: pointer;
          }
          .col-detail {
            display: flex;
            align-items: center;
            flex-wrap: nowrap;
            &-data {
              overflow: hidden;
              white-space: nowrap;
              text-overflow: ellipsis;
            }
            &-more {
              flex: 0 0 28px;
              color: #3a84ff;
              cursor: pointer;
              margin-left: 2px;
            }
          }
        }
      }
      /deep/ .bk-sideslider-wrapper {
        padding-bottom: 0;
        .bk-sideslider-content {
          background: #fafbfd;
        }
      }
      .side-detail {
        margin: 4px 0 4px 60px;
        background: #fff;
        padding: 10px 30px 10px 16px;
        min-height: calc(100vh - 70px);
        &-code {
          word-break: break-all;
          white-space: pre-wrap;
        }
      }
    }
</style>
