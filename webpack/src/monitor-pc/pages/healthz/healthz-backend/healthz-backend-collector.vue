<template>
  <div class="main-component-content">
    <p> {{ $t('数据链路') }} </p>
    <div v-for="(item, index) in backendCollectorComponent" style="display: inline-block;" :key="index">
      <mo-healthz-component-tooltip-view :component-name="item"
                                         :index="index"
                                         :show-line="'yes'"
                                         :is-last="index === backendCollectorComponent.length - 1">
      </mo-healthz-component-tooltip-view>
    </div>
  </div>
</template>
<script>
// import { mapState } from 'vuex'
import store from '../store/healthz/store'
import MoHealthzComponentTooltipView from '../common/healthz-component-tooltip'
export default {
  name: 'MoHealthzBackendCollectorView',
  components: {
    MoHealthzComponentTooltipView
  },
  computed: {
    backendCollectorComponent() {
      return store.state.backendCollectorComponent
    }
    // ...mapState([
    //     'backendCollectorComponent'
    // ])
  }
}
</script>
<style lang="scss" scoped>
    @import "../style/healthz";
</style>
