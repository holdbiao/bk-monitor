<template>
  <div class="config-delivery" v-bkloading="{ isLoading: loading }" :class="{ 'need-loading': loading }">
    <template v-if="taskReady.show">
      <task-ready :task-ready="taskReady.status" :target="config.target"></task-ready>
    </template>
    <template v-else>
      <template v-if="tables && tables.contents && tables.contents.length">
        <config-deploy :all-data="tables" @can-polling="handlePolling" @refresh="handleRefreshData"></config-deploy>
      </template>
      <template v-else>
        <empty-target></empty-target>
      </template>
      <div class="footer">
        <bk-button class="footer-btn" theme="primary" :disabled="hasRunning" @click="!hasRunning && $emit('next')">{{hasRunning ? $t('下发中') : $t('完成')}}</bk-button>
        <bk-button v-if="showRollBack && allowRollBack" :disabled="hasRunning" @click="handleRollback"> {{ $t('回滚') }} </bk-button>
      </div>
    </template>
  </div>
</template>
<script>
import ConfigDeploy from '../../config-deploy/config-deploy'
import EmptyTarget from './empty-target'
import TaskReady from './task-ready'
import { collectTargetStatus,
  rollbackDeploymentConfig,
  isTaskReady } from '../../../../../monitor-api/modules/collecting'
export default {
  name: 'ConfigDelivery',
  components: {
    ConfigDeploy,
    EmptyTarget,
    TaskReady
  },
  props: {
    config: {
      type: Object,
      default: () => {}
    },
    hosts: Object
  },
  data() {
    return {
      loading: false,
      hasRunning: true,
      showRollBack: false,
      tables: [],
      timer: null,
      taskReadyTimer: null,
      t: 10000,
      newDiffData: [],
      ajaxMark: false,
      taskReady: {
        show: true,
        status: {
          msg: this.$t('采集下发准备中')
        }
      }
    }
  },
  computed: {
    allowRollBack() {
      if (this.config.mode === 'edit' && this.config.select && this.config.select.others) {
        return !!this.config.select.others.allowRollback
      }
      return true
    }
  },
  watch: {
    'taskReady.show': {
      handler(is) {
        if (!is) {
          this.init()
        }
      },
      immediate: true
    }
  },
  async created() {
    setTimeout(async () => {
      const show = await isTaskReady({ collect_config_id: this.config.data.id })
      this.taskReady.show = !show
      if (this.taskReady.show) {
        this.taskReadyStatus()
      }
    }, 1000)
  },
  beforeDestroy() {
    clearTimeout(this.timer)
    clearTimeout(this.taskReadyTimer)
  },
  methods: {
    async taskReadyStatus() {
      this.taskReadyTimer = setTimeout(async () => {
        clearTimeout(this.taskReadyTimer)
        if (this.taskReady.show) {
          const show = await isTaskReady({ collect_config_id: this.config.data.id })
          this.taskReady.show = !show
          this.taskReadyStatus()
        }
      }, 2000)
    },
    async init() {
      this.loading = true
      await this.getHosts(this.config.data.id)
      this.showRollBack = this.config.mode === 'edit'
      this.pollingStatus()
    },
    handleRefreshData(id) {
      collectTargetStatus({ id }).then((data) => {
        this.tables = this.handleData(data)
        this.$emit('update:hosts', this.tables)
      })
        .catch((err) => {
          this.bkMsg('error', err.message || this.$t('出错了'))
        })
    },
    getHosts(id) {
      this.ajaxMark = false
      return collectTargetStatus({ id }, { needMessage: false }).then((data) => {
        this.tables = this.handleData(data)
        this.hasRunning = data.contents.some(item => item.child.some(set => (
          set.status === 'RUNNING'
        || set.status === 'PENDING')))
        this.$emit('update:hosts', this.tables)
      })
        .catch((err) => {
          this.bkMsg('error', err.message || this.$t('出错了'))
        })
        .finally(() => {
          this.loading = false
        })
    },
    getHostData(id) {
      return new Promise((resolve, reject) => {
        this.ajaxMark = false
        collectTargetStatus({ id }).then((data) => {
          if (this.ajaxMark) {
            reject(data)
          } else {
            resolve(data)
          }
        })
          .catch((err) => {
            reject(err)
          })
          .finally(() => {
            this.loading = false
          })
      })
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
          } else if (set.status === 'PENDING' || set.status === 'RUNNING') {
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
    },
    bkMsg(theme, message) {
      this.$bkMessage({
        theme,
        message,
        ellipsisLine: 0
      })
    },
    async handleRollback() {
      this.$bkInfo({
        title: this.$t('回滚操作'),
        subTitle: this.$t('将回滚本次的所有配置变更和目标机器的内容。回滚只能回滚上一次的状态，并且只能进行一次。'),
        okText: this.$t('确认回滚'),
        confirmFn: () => {
          // this.$parent.pageLoading = true
          this.loading = true
          this.showRollBack = false
          this.hasRunning = true
          this.$emit('update:type', 'ROLLBACK')
          rollbackDeploymentConfig({ id: this.config.data.id }, { needMessage: false }).then(async () => {
            const isReady = await this.taskReadyStatusPromise(this.config.data.id)
            if (isReady) {
              this.getHosts(this.config.data.id)
              this.pollingStatus()
            }
          })
            .catch((err) => {
              this.showRollBack = true
              this.loading = false
              this.bkMsg('error', err.message || this.$t('出错了'))
            })
        }
      })
    },
    pollingStatus() {
      this.timer = setTimeout(() => {
        clearTimeout(this.timer)
        if (this.hasRunning) {
          this.getHosts(this.config.data.id).finally(() => {
            this.pollingStatus()
          })
        }
      }, this.t)
    },
    async handlePolling(v) {
      this.hasRunning = true
      this.ajaxMark = true
      if (v) {
        clearTimeout(this.timer)
        await this.getHostData(this.config.data.id).then((data) => {
          if (this.ajaxMark) {
            this.tables = this.handleData(data)
            this.hasRunning = data.contents.some(item => item.child.some(set => (
              set.status === 'RUNNING'
            || set.status === 'PENDING')))
            this.$emit('update:hosts', this.tables)
          }
        })
          .finally(() => {
            this.pollingStatus()
          })
      } else {
        clearTimeout(this.timer)
      }
    },
    async taskReadyStatusPromise(id) {
      let timer = null
      clearTimeout(timer)
      return new Promise(async (resolve) => {
        const show = await isTaskReady({ collect_config_id: id })
        if (show) {
          resolve(true)
        } else {
          timer = setTimeout(() => {
            this.taskReadyStatusPromise(id).then((res) => {
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
    .config-delivery {
      display: flex;
      flex-direction: column;
      padding: 41px 60px;
      &.need-loading {
        min-height: calc(100vh - 80px)
      }
      .footer-btn {
        margin-right: 8px;
      }
    }

</style>
