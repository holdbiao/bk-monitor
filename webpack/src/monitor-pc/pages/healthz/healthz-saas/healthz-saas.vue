<template>
  <div class="main-content-box">
    <div class="main-content-box-title"> {{ $t('监控Saas依赖周边组件状态') }} </div>
    <!--依赖周边组件状态-->
    <mo-healthz-saas-component-view style="white-space: break-spaces;"></mo-healthz-saas-component-view>
  </div>
</template>
<script>
import MoHealthzSaasComponentView from './healthz-saas-component'
export default {
  name: 'MoHealthzSaasView',
  components: {
    MoHealthzSaasComponentView
  },
  data() {
    return {}
  },
  methods: {}
}
</script>
<style lang="scss" scoped>
    @import "../style/healthz";
</style>
