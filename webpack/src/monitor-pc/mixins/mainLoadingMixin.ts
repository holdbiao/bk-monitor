/* eslint-disable new-cap */
import { Component, Vue, Watch } from 'vue-property-decorator'

@Component
// 设置全局通用的Loading
export default class mainLoadingMixin extends Vue {
  @Watch('mainLoading')
  public onMainLoadingChange(newVal: boolean) {
    this.handleSetMainLoading(newVal)
  }
  public handleSetMainLoading(v: boolean) {
    this.$store.commit('app/SET_MAIN_LOADING', v)
  }
}
