<template>
  <div class="upgrade-wrapper">
    <div class="header">
      <div>
        <bk-button class="start-upgrade" :theme="'primary'" @click="upgradeAll"> {{ $t('开始升级')}} </bk-button>
      </div>
    </div>
    <div class="upgrade-list-wrapper">
      <h1> {{ $t('配置升级向导') }} </h1>
      <p> {{ $t('蓝鲸监控 V3 使用了全新的数据链路，为了确保数据能够正常上报，需要更新以下主机的采集器与采集配置。点击右上角') }} <strong> {{ $t('开始升级') }} </strong> {{ $t('按钮即可开始。') }} </p>
      <p> {{ $t('升级可能需要较长的时间，请耐心等待。') }} <strong> {{ $t('升级过程中，请勿关闭页面。') }} </strong></p>
      <div class="script-collecotr" v-bkloading="{ isLoading: script.loading }">
        <h3 class="title"> {{ $t('脚本采集') }} </h3>
        <bk-table
          :data="script.data"
          :empty-text="$t('无数据')"
        >
          <bk-table-column :label="$t('需要升级的主机IP')" prop="ip" width="180"></bk-table-column>
          <bk-table-column :label="$t('云区域ID')" prop="bk_cloud_id" width="180"></bk-table-column>
          <bk-table-column :label="$t('所属业务')" width="180">
            <template slot-scope="props">
              {{bizMapping[props.row.bk_biz_id]}}
            </template>
          </bk-table-column>
          <bk-table-column class-name="dimension-row" :label="$t('绑定任务')" prop="tasks">
            <template slot-scope="props">
              <ul>
                <li v-for="(task, index) in props.row.tasks" :key="index">{{`${task.title}(${task.desc})`}}</li>
              </ul>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('状态')" width="180" prop="status">
            <template slot-scope="props">
              <span :class="props.row.status">{{statusColor[props.row.status]}}</span>
              <span
                style="vertical-align: middle;"
                v-if="props.row.status === 'failed'"
                class="bk-icon icon-exclamation-circle failed"
                v-bk-tooltips=" {
                  content: props.row.errorMsg,
                  showOnInit: false,
                  placements: ['top']
                }">
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作')" width="240">
            <template slot-scope="props">
              <bk-button :disabled="disableProps[props.row.status]" text @click="start(props.row)"> {{ $t('升级') }} </bk-button>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <div class="log-collector" v-bkloading="{ isLoading: log.loading }">
        <h3> {{ $t('日志采集') }} </h3>
        <bk-table
          :data="log.data"
          :empty-text="$t('无数据')"
        >
          <bk-table-column :label="$t('需要升级的主机IP')" prop="ip" width="180"></bk-table-column>
          <bk-table-column :label="$t('云区域ID')" prop="bk_cloud_id" width="180"></bk-table-column>
          <bk-table-column :label="$t('所属业务')" width="180">
            <template slot-scope="props">
              {{bizMapping[props.row.bk_biz_id]}}
            </template>
          </bk-table-column>
          <bk-table-column class-name="dimension-row" :label="$t('绑定任务')" prop="tasks">
            <template slot-scope="props">
              <ul>
                <li v-for="(task, index) in props.row.tasks" :key="index">{{`${task.title}(${task.desc})`}}</li>
              </ul>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('状态')" prop="status" width="180">
            <template slot-scope="props">
              <span :class="props.row.status">{{statusColor[props.row.status]}}</span>
              <span
                style="vertical-align: middle;"
                v-if="props.row.status === 'failed'"
                class="bk-icon icon-exclamation-circle failed"
                v-bk-tooltips=" {
                  content: props.row.errorMsg,
                  showOnInit: false,
                  placements: ['top']
                }">
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作')" width="240">
            <template slot-scope="props">
              <bk-button title="primary" :disabled="disableProps[props.row.status]" text @click="start(props.row)"> {{ $t('升级') }} </bk-button>

            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'CollectorUpgrade',
  data() {
    return {
      bizList: {
        value: 0,
        data: []
      },
      script: {
        data: [],
        loading: true
      },
      log: {
        data: [],
        loading: true
      },
      waitUpgradeTasks: [],
      upgradingTasks: [],
      statusColor: {
        ready: this.$t('准备升级'),
        pending: this.$t('正在升级...'),
        success: this.$t('升级成功'),
        failed: this.$t('升级失败')
      },
      disableProps: {
        ready: false,
        pending: true,
        success: true,
        failed: false
      },
      bizMapping: {}
    }
  },
  computed: {

  },
  created() {
    this.getUpgradeList()
  },
  mounted() {
    this.bizList.data = this.$store.getters.bizList.slice()
    this.bizList.data.unshift({ id: 0, text: this.$t('全部') })
    for (const index in this.bizList.data) {
      const biz = this.bizList.data[index]
      this.bizMapping[biz.id] = biz.text
    }
  },
  methods: {
    upgradeAll() {
      this.$bkInfo({
        title: this.$t('确定开始升级'),
        maskClose: true,
        confirmFn: () => {
          this.waitUpgradeTasks = [...this.script.data, ...this.log.data]
          this.waitUpgradeTasks.forEach((task, index) => {
            task.status = 'pending'
            if (index < 5) {
              this.enterQueue(task)
            }
          })
        }
      })
    },
    start(row) {
      this.waitUpgradeTasks.push(row)
      this.enterQueue(row)
    },
    enterQueue(task) {
      task.status = 'pending'
      if (this.upgradingTasks.length < 5) {
        this.upgradingTasks.push(task)
        const index = this.waitUpgradeTasks.findIndex(item => item.ip === task.ip)
        if (index > -1) {
          this.waitUpgradeTasks.splice(index, 1)
          this.upgrade(task)
        }
      }
    },
    getUpgradeList() {
      const addStatusProp = (array, type) => {
        array.forEach((data) => {
          data.status = 'ready'
          data.errorMsg = ''
          data.type = type
        })
      }
      this.script.loading = true
      this.log.loading = true

      this.$api.model.listUpgradeHostScriptCollectorConfig({ bk_biz_id: this.$store.getters.bizId }).then((data) => {
        addStatusProp(data, 'script')
        this.script.data = data.filter(task => task.upgrade_status !== 'success')
        data.errorMsg = ''
        this.script.loading = false
      })
      this.$api.model.listUpgradeHostLogCollector({ bk_biz_id: this.$store.getters.bizId }).then((data) => {
        addStatusProp(data, 'log')
        this.log.data = data.filter(task => task.upgrade_status !== 'success')
        this.log.loading = false
      })
    },
    upgrade(row) {
      const param = {
        ip: row.ip,
        bk_cloud_id: row.bk_cloud_id
      }
      const ajaxFun = row.type === 'script' ? this.$api.model.upgradeHostScriptCollectorConfig
        : this.$api.model.upgradeHostLogCollector
      ajaxFun(param).then((res) => {
        if (res.result) {
          row.status = 'success'
        } else {
          row.status = 'failed'
          row.errorMsg = res.message
        }
        const upgradeTaskIndex = this.upgradingTasks.findIndex(task => task.ip === row.ip)
        this.upgradingTasks.splice(upgradeTaskIndex, 1)
        if (this.waitUpgradeTasks.length) {
          this.enterQueue(this.waitUpgradeTasks[0])
        }
      })
    }
  }
}
</script>
<style lang="scss" scoped>
.upgrade-wrapper {
  .header {
    // position: fixed;
    // top: 0;
    // left: 50px;
    // z-index: 2000;
    // width: calc(100% - 50px);
    display: flex;
    justify-content: space-between;
    height: 50px;
    line-height: 50px;
    padding: 0 16px;
    background: #fff;
    /deep/ .bk-select {
      display: inline-block;
      vertical-align: middle;
    }
  }
  .success {
    color: #2dcb56;
  }
  .failed {
    color: #ea3636;
  }
  .pending {
    color: #3a84ff;
  }
  /deep/ .bk-button-text.bk-primary {
    padding-left: 0;
  }
  /deep/ .dimension-row {
    .cell {
      -webkit-line-clamp: 100;
      ul {
        margin-bottom: 0;
        padding-left: 0;
      }
    }
  }
  /deep/ .bk-table-empty-block {
    background: #fff;
  }
  .upgrade-list-wrapper {
    .log-collector {
      margin-top: 20px;
    }
  }
}
</style>
