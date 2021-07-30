<template>
  <div class="main-component-content">
    <p> {{ $t('依赖周边组件状态') }} </p>
    <div v-for="(item,index) in backendDependenciesComponent" style="display: inline-block;" :key="index">
      <mo-healthz-component-tooltip-view
        :component-name="item"
        :index="index"
        :is-last="index === backendDependenciesComponent.length - 1"></mo-healthz-component-tooltip-view>
    </div>
  </div>
</template>
<script>
// import { mapState } from 'vuex'
import store from '../store/healthz/store'
import MoHealthzComponentTooltipView from '../common/healthz-component-tooltip'
export default {
  name: 'MoHealthzBackendComponentView',
  components: {
    MoHealthzComponentTooltipView
  },
  data() {
    return {}
  },
  computed: {
    backendDependenciesComponent() {
      return store.state.backendDependenciesComponent
    }
    // ...mapState([
    //     'backendDependenciesComponent'
    // ])
  }
}
</script>
<style scoped lang="scss">
    @import "../style/healthz";
</style>
