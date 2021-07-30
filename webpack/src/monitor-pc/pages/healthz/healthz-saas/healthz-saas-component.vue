<template>
  <div class="main-component-content">
    <p> {{ $t('依赖周边组件状态') }} </p>
    <div v-for="(item, index) in saasDependenciesComponent" style="display: inline-block;" :key="index">
      <!--cmdb,job,bk_data的组件-->
      <mo-healthz-saas-component-tooltip-view :component-name="item" :index="index"
                                              v-if="saasComponentNeedToTest.indexOf(item) > -1"></mo-healthz-saas-component-tooltip-view>
      <!--其他的组件-->
      <mo-healthz-component-tooltip-view :component-name="item"
                                         :index="index"
                                         :is-last="index === saasDependenciesComponent.length - 1"
                                         v-else></mo-healthz-component-tooltip-view>
    </div>
  </div>
</template>
<script>
// import { mapState } from 'vuex'
import store from '../store/healthz/store'
import MoHealthzSaasComponentTooltipView from '../common/healthz-saas-component-tooltip'
import MoHealthzComponentTooltipView from '../common/healthz-component-tooltip'
export default {
  name: 'MoHealthzSaasComponentView',
  components: {
    MoHealthzSaasComponentTooltipView,
    MoHealthzComponentTooltipView
  },
  data() {
    return {}
  },
  computed: {
    saasDependenciesComponent() {
      return store.state.saasDependenciesComponent
    },
    saasComponentNeedToTest() {
      return store.state.saasComponentNeedToTest
    }
    // ...mapState([
    //     'saasDependenciesComponent',
    //     'saasComponentNeedToTest'
    // ])
  }
}
</script>
<style scoped lang="scss">
    @import "../style/healthz";
</style>
