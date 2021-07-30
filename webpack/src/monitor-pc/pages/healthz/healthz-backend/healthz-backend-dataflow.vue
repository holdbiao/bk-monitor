<template>
  <div class="main-component-content">
    <p> {{ $t('后台服务') }} </p>
    <div v-for="(item,index) in backendDataFlowComponent" style="display: inline-block;" :key="index">
      <!--只有数据流的组件才显示连接线，最后一个组件不显示连接线-->
      <mo-healthz-component-tooltip-view :component-name="item"
                                         :index="index"
                                         :show-line="'yes'"
                                         :is-last="index === backendDataFlowComponent.length - 1">
      </mo-healthz-component-tooltip-view>
    </div>
  </div>
</template>
<script>
// import { mapState } from 'vuex'
import store from '../store/healthz/store'
import MoHealthzComponentTooltipView from '../common/healthz-component-tooltip'
export default {
  name: 'MoHealthzBackendDataflowView',
  components: {
    MoHealthzComponentTooltipView
  },
  computed: {
    backendDataFlowComponent() {
      return store.state.backendDataFlowComponent
    }
    // ...mapState([
    //     'backendDataFlowComponent'
    // ])
  }
}
</script>
<style lang="scss" scoped>
    @import "../style/healthz";
</style>
