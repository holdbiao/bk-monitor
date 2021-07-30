<template>
  <div>
    <!--服务状态-->
    <mo-healthz-header-view :msg.sync="msg"></mo-healthz-header-view>
    <div class="dash-board-center-div" v-show="msg === 0" v-bkloading="{ isLoading: dashLoading }">
      <!--监控后台服务状态-->
      <mo-healthz-backend-view></mo-healthz-backend-view>
      <!--监控saas依赖周边组件状态-->
      <mo-healthz-saas-view></mo-healthz-saas-view>
    </div>
    <!--异常告警-->
    <mo-healthz-alarm-config :msg.sync="msg"></mo-healthz-alarm-config>
    <!--数据流弹窗，依赖周边组件信息，及rabbitmq弹窗-->
    <mo-healthz-common-popup-window-view></mo-healthz-common-popup-window-view>
  </div>
</template>
<script>
import store from './store/healthz/store'
import MoHealthzHeaderView from './healthz-header'
import MoHealthzBackendView from './healthz-backend/healthz-backend'
import MoHealthzSaasView from './healthz-saas/healthz-saas'
import MoHealthzAlarmConfig from './healthz-error'
import MoHealthzCommonPopupWindowView from './common/healthz-common-popup-window'
// const configData = require('./config')
export default {
  store,
  name: 'MoHealthzView',
  components: {
    MoHealthzHeaderView,
    MoHealthzBackendView,
    MoHealthzSaasView,
    MoHealthzAlarmConfig,
    MoHealthzCommonPopupWindowView
  },
  data() {
    return {
      msg: 0,
      dashLoading: true, // 控制页面是否载入中,
      configData: {
        saasComponentNeedToTest: ['cmdb', 'bk_data', 'job', 'metadata', 'nodeman', 'gse'],
        displayedMetrics: [
          'system.cpu.percent',
          'system.disk.ioutil',
          'system.disk.usage',
          'system.mem.process.usage'
        ],
        displayedMetricsDescription: {
          'system.cpu.percent': this.$t('CPU使用率'),
          'system.disk.ioutil': this.$t('磁盘IO使用率'),
          'system.disk.usage': this.$t('磁盘使用率'),
          'system.mem.process.usage': this.$t('应用内存使用率')
        },
        backendCollectorComponent: [
          'gse_data',
          'pre_kafka',
          'transfer',
          'influxdb_proxy',
          'influxdb'
        ],
        backendDataFlowComponent: [
          'access_data',
          'access_real_time_data',
          'access_event',
          'detect',
          'trigger',
          'event_generator',
          'event_manager',
          'action',
          'kernel_api'
        ],
        backendDependenciesComponent: [
          'kafka',
          'mysql',
          'elasticsearch',
          'supervisor',
          'redis',
          'celery',
          'graph_exporter'
        ],
        saasDependenciesComponent: [
          'cmdb',
          'job',
          'bk_data',
          'metadata',
          'nodeman',
          'gse',
          'rabbitmq',
          'saas_celery'
        ]
      }
    }
  },
  mounted() {
    this.getGlobalData()
  },
  methods: {
    // 请求网络获取到全局数据
    getGlobalData() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      const self = this
      this.$api.healthz.getGlobalStatus({}, { needRes: true }).then((res) => {
        if (res.result && res.data.length) {
          // 将获取到的全局数据放入store中
          store.commit('loadGlobalData', res.data)
          // 数据加载完成后，需要将数据中的所有 ip 聚合放在列表里面
          const tmpIPlist = []
          res.data.forEach((tmpData) => {
            if (tmpData.node_name === 'system'
                && Object.prototype.hasOwnProperty.call(tmpData, 'server_ip')
                && tmpData.server_ip !== ''
                && tmpIPlist.indexOf(tmpData.server_ip) === -1) {
              tmpIPlist.push(tmpData.server_ip)
            }
          })
          // 首次加载选中的和全部的ip列表相同
          store.commit('changeSelectedIPs', tmpIPlist)
          store.commit('changeAllIPs', tmpIPlist)
        }
        // 取消 loading 状态
        self.dashLoading = false
      })
      // 填充配置信息
      this.loadConfigData()
    },
    // 读取配置信息，并且填充相关的参数
    loadConfigData() {
      // 填充对应的配置
      // 社区版剔除tsdb-proxy
      if (this.$platform.ce) {
        const index = this.configData.backendCollectorComponent.indexOf('tsdb_proxy')
        this.configData.backendCollectorComponent.splice(index, 1)
      }
      store.commit('loadConfigSaasComponentNeedToTest', this.configData.saasComponentNeedToTest)
      store.commit('loadConfigBackendDataFlowComponent', this.configData.backendDataFlowComponent)
      store.commit('loadConfigBackendDependenciesComponent', this.configData.backendDependenciesComponent)
      store.commit('loadConfigSaasDependenciesComponent', this.configData.saasDependenciesComponent)
      store.commit('loadDisplayedMetrics', this.configData.displayedMetrics)
      store.commit('loadDisplayedMetricsDescription', this.configData.displayedMetricsDescription)
      store.commit('loadBackendCollectorComponent', this.configData.backendCollectorComponent)
    }
  }
}
</script>
<style lang="scss" scoped>


    @media screen and (min-width: 1000px) {
      /deep/ .el-dialog {
        /* stylelint-disable-next-line declaration-no-important */
        width: 522px !important;
      }
    }

    /* 全局dialog样式 */
    /deep/ .el-dialog {
      /* stylelint-disable-next-line declaration-no-important */
      width: 40% !important;
      height: 335px;
      overflow-x: hidden;
      overflow-y: auto;
    }
    /deep/ .el-dialog .el-dialog__title {
      font-size: 16px;
      font-weight: normal;
      font-stretch: normal;
      line-height: 24px;
      letter-spacing: 0px;
      color: #333;
    }
    /deep/ .el-dialog__body {
      max-height: 345px;

      /* stylelint-disable-next-line declaration-no-important */
      padding: 10px 20px !important;
      color: #606266;
      font-size: 14px;
    }
</style>
