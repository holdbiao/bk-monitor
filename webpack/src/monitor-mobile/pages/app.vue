<template>
    <van-pull-refresh :value="refresh" @change="handleRefreshChange" @refresh="handleRefresh">
        <div style="min-height: 100vh">
            <keep-alive>
                <router-view :route-key="routeKey" />
            </keep-alive>
            <router-view
                key="noCache"
                name="noCache" />
            <drag-label
                v-if="['alarm-info', 'alarm-detail', 'quick-alarm-shield'].includes($route.name)"
                :alarm-num="alarmNum"
                @click="handleGoToEventCenter" />
            <van-overlay
                :show="loading"
                z-index="9999">
                <div class="loading-wrap">
                    <van-loading></van-loading>
                </div>
            </van-overlay>
        </div>
    </van-pull-refresh>
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import { Loading, Overlay, PullRefresh } from 'vant'
import DragLabel from '../components/drag-label/drag-label.vue'
import { random } from '../../monitor-common/utils/utils'
@Component({
  name: 'App',
  components: {
    [Loading.name]: Loading,
    [Overlay.name]: Overlay,
    DragLabel,
    [PullRefresh.name]: PullRefresh
  }
})
export default class App extends Vue {
  routeKey: string = random(10)
  get loading() {
    return this.$store.state.app.loading
  }

  get alarmNum() {
    return this.$store.getters['app/alarmCount']
  }

  get refresh() {
    return this.$store.state.app.refresh
  }

  created() {
    this.$store.commit('app/setPageLoading', true)
  }

  // 跳转至事件中心
  handleGoToEventCenter() {
    this.$router.push({
      name: 'event-center',
      params: {
        title: this.$store.state.app.bkBizName + this.$tc('事件中心')
      }
    })
  }

  handleRefreshChange(v) {
    this.$store.commit('app/setRefresh', v)
  }

  handleRefresh() {
    this.handleRefreshChange(true)
    this.routeKey = random(100)
    // setTimeout(() => {
    //     this.$router.push({
    //         path: this.$route.path + '/' + random(10)
    //     })
    //     this.handleRefreshChange(false)
    // }, 1000)
  }
}
</script>
<style lang="scss" scoped>
  .loading-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
</style>
