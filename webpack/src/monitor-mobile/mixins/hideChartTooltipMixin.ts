import { Component, Vue } from 'vue-property-decorator'
import { Route } from 'vue-router'

Component.registerHooks([
  'beforeRouteLeave'
])

@Component
export default class HideChartTooltipMixin extends Vue {
  public options = {
    tooltip: {
      show: true
    },
    toolbox: {
      show: false
    }
  }

  public activated() {
    this.options.tooltip.show = true
  }

  public beforeRouteLeave(to: Route, from: Route, next: () => void) {
    this.options.tooltip.show = false
    next()
  }
}
