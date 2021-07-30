<template>
  <div class="main-content-box">
    <div class="main-content-box-title"> {{ $t('监控后台服务状态') }} </div>
    <!--后台服务器性能指标-->
    <mo-healthz-backend-metrics-view></mo-healthz-backend-metrics-view>
    <!--数据链路-->
    <mo-healthz-backend-collector-view v-if="isShowCollector"></mo-healthz-backend-collector-view>
    <!--后台服务-->
    <mo-healthz-backend-dataflow-view></mo-healthz-backend-dataflow-view>
    <!--依赖周边组件状态-->
    <mo-healthz-backend-component-view></mo-healthz-backend-component-view>
  </div>
</template>
<script>
import MoHealthzBackendMetricsView from './healthz-backend-metrics'
import MoHealthzBackendCollectorView from './healthz-backend-collector'
import MoHealthzBackendDataflowView from './healthz-backend-dataflow'
import MoHealthzBackendComponentView from './healthz-backend-component'

export default {
  name: 'MoHealthzBackendView',
  components: {
    MoHealthzBackendMetricsView,
    MoHealthzBackendCollectorView,
    MoHealthzBackendDataflowView,
    MoHealthzBackendComponentView
  },
  computed: {
    // 是否显示数据链路健康检查，只在企业版和社区版显示
    isShowCollector() {
      return this.$platform.ee || this.$platform.ce
    }
  }
}
</script>
<style lang="scss" scoped>
    @import "../style/healthz";
</style>
