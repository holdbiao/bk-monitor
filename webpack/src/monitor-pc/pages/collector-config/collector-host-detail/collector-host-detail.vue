<template>
  <div class="host-detail" v-bkloading="{ 'isLoading': loading }" :class="{ 'detail-loading': loading }">
    <template v-if="!loading">
      <div class="host-detail-desc" v-if="tables.length">
        <i class="icon-monitor icon-tips"></i> {{ $t('该内容是对') }} {{tables.config_info.name}} {{ $t('进行') }}“ <span class="desc-operate">{{operatorMap[tables.config_info.last_operation]}}</span> ”{{ $t('操作的执行详情') }} </div>
      <collector-host-status v-if="tables && tables.contents && tables.contents.length" :all-data="tables" @can-polling="handlePolling" @refresh="handleRefreshData"></collector-host-status>
      <!-- <config-deploy v-if="tables && tables.contents && tables.contents.length" :all-data="tables" @can-polling="handlePolling"></config-deploy> -->
      <empty-detail v-else :need-title="false">
        <template #desc> {{ $t('本次操作未选择目标，无下发操作记录') }} </template>
      </empty-detail>
    </template>
  </div>
</template>
<script>
// import ConfigDeploy from '../config-deploy/config-deploy'
import CollectorHostStatus from './collector-host-status'
import EmptyDetail from '../collector-add/config-delivery/empty-target'
import { collectInstanceStatus } from '../../../../monitor-api/modules/collecting'
import * as collectAuth from '../authority-map'
import authorityMixinCreate from '../../../mixins/authorityMixin'
export default {
  name: 'HostDetail',
  components: {
    CollectorHostStatus,
    // ConfigDeploy,
    EmptyDetail
  },
  mixins: [authorityMixinCreate(collectAuth)],
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail
    }
  },
  data() {
    return {
      loading: true,
      needPolling: true,
      pollingCount: 1,
      tables: [],
      operatorMap: {
        ROLLBACK: this.$t('回滚'),
        UPGRADE: this.$t('升级'),
        CREATE: this.$t('新增'),
        EDIT: this.$t('编辑'),
        ADD_DEL: this.$t('增删目标'),
        START: this.$t('启用'),
        STOP: this.$t('停用'),
        AUTO_DEPLOYING: this.$t('自动执行')
      },
      statusList: ['PENDING', 'RUNNING', 'DEPLOYING', 'STARTING', 'STOPPING']
    }
  },
  async created() {
    this.loading = true
    this.id = this.$route.params.id
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
    await this.getHosts(this.pollingCount).finally(() => {
      this.loading = false
      this.$store.commit(
        'app/SET_NAV_TITLE',
        `${this.$t('route-' + '执行详情').replace('route-', '')}`
        + '-'
        + `#${this.$route.params.id} ${this.tables.config_info.name}`
      )
    })
  },
  beforeDestroy() {
    window.clearTimeout(this.timer)
  },
  methods: {
    getHosts(count) {
      return collectInstanceStatus({ id: this.id }).then((data) => {
        if (count !== this.pollingCount) return
        this.tables = this.handleData(data)
        this.needPolling = data.contents.some(item => item.child.some(set => (this.statusList.includes(set.status))))
        if (!this.needPolling) {
          window.clearTimeout(this.timer)
        } else if (count === 1) {
          this.handlePolling()
        }
      })
        .catch(() => {})
    },
    handlePolling(v = true) {
      if (v) {
        this.timer = setTimeout(() => {
          clearTimeout(this.timer)
          this.pollingCount += 1
          this.getHosts(this.pollingCount).finally(() => {
            if (!this.needPolling) return
            this.handlePolling()
          })
        }, 10000)
      } else {
        window.clearTimeout(this.timer)
      }
    },
    handleRefreshData() {
      return collectInstanceStatus({ id: this.id }).then((data) => {
        this.tables = this.handleData(data)
      })
        .catch(() => {})
    },
    handleData(data) {
      const oldContent = this.tables.contents
      const content = data.contents
      const sumData = {
        success: {},
        failed: {},
        pending: {}
      }
      content.forEach((item, index) => {
        item.successNum = 0
        item.failedNum = 0
        item.pendingNum = 0
        item.table = []
        item.expand = oldContent?.length && oldContent[index] ? oldContent[index].expand : item.child.length > 0
        item.child.forEach((set) => {
          if (set.status === 'SUCCESS') {
            sumData.success[set.instance_id] = set.instance_id
            item.successNum += 1
          } else if (this.statusList.includes(set.status)) {
            item.pendingNum += 1
            sumData.pending[set.instance_id] = set.instance_id
          } else {
            item.failedNum += 1
            sumData.failed[set.instance_id] = set.instance_id
          }
        })
      })
      const headerData = {}
      headerData.successNum = Object.keys(sumData.success).length
      headerData.failedNum = Object.keys(sumData.failed).length
      headerData.pendingNum = Object.keys(sumData.pending).length
      headerData.total = headerData.successNum + headerData.failedNum + headerData.pendingNum
      data.headerData = headerData
      return data
    }
    // async handleSetPolling (v) {
    //     this.ajaxMark = true
    //     if (v) {
    //         clearTimeout(this.timer)
    //         await this.getHostData().then(data => {
    //             if (this.ajaxMark) {
    //                 this.tables = this.handleData(data)
    //                 const needPolling = data.contents.some(item => item.child.some(set => (set.status === 'PENDING' || set.status === 'RUNNING')))
    //                 if (!needPolling) {
    //                     window.clearTimeout(this.timer)
    //                 }
    //             }
    //         }).catch(data => {
    //             console.error(data)
    //         }).finally(_ => {
    //             this.handlePolling()
    //         })
    //     } else {
    //         clearTimeout(this.timer)
    //     }
    // }
  }
}
</script>
<style lang="scss" scoped>
.host-detail {
  color: #63656e;
  min-height: calc(100vh - 120px);
  &-desc {
    display: flex;
    align-items: center;
    margin: -2px 0 18px;
    .icon-tips {
      color: #979ba5;
      font-size: 14px;
      margin-right: 7px;
      height: 14px;
    }
    .desc-operate {
      font-weight: bold;
    }
  }
}
</style>
