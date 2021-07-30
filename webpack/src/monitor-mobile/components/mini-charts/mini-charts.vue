<template>
  <div
    ref="miniChart"
    class="mini-chart"
    @click="handleClick"
  >
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop } from 'vue-property-decorator'
import Highcharts from 'highcharts/highcharts'
// 图表配置项
const defaultChartOption = {
  chart: {
    type: 'area',
    spacing: [0, 0, 0, 0],
    margin: [0, 0, 0, 0],
    width: 85,
    height: 38
  },
  plotOptions: {
    area: {
      fillColor: '#E8EBF3',
      lineColor: '#A0B0CB',
      lineWidth: 1,
      marker: {
        enabled: false,
        states: {
          hover: {
            enabled: false
          }
        }
      },
      states: {
        hover: {
          enabled: false
        }
      }
    }
  },
  yAxis: {
    labels: {
      enabled: false
    },
    title: {
      text: ''
    },
    gridLineWidth: 0
  },
  xAxis: {
    labels: {
      enabled: false
    },
    tickLength: 0
  },
  legend: {
    enabled: false
  },
  tooltip: {
    enabled: false
  },
  title: {
    text: ''
  },
  credits: { enabled: false },
  series: []
}
@Component
export default class MiniCharts extends Vue {
  // 获取图表series数据 function类型
  @Prop() getSeriesData: () => Promise<{series: []}>

  // 图表对象
  public chart: Highcharts
  // 图表是否在视窗内（动态加载）
  public intersectionObserver: IntersectionObserver
  private needObserver = true

  mounted() {
    this.chart = Highcharts.chart(this.$refs.miniChart, defaultChartOption)
    this.registerObserver()
    this.intersectionObserver.unobserve(this.$el)
    this.intersectionObserver.observe(this.$el)
  }

  beforeDestroy() {
    this.chart = null
    this.intersectionObserver && this.intersectionObserver.unobserve(this.$el)
    this.intersectionObserver && this.intersectionObserver.disconnect()
    this.intersectionObserver = null
  }

  @Emit('click')
  handleClick(e: Event) {
    return e
  }

  registerObserver(): void {
    this.intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.intersectionRatio > 0 && this.needObserver) {
          this.handleSeriesData()
        }
      })
    })
  }

  async handleSeriesData() {
    try {
      const data = await this.getSeriesData()
      this.chart && this.chart.update(Object.assign({}, {
        series: data.series || []
      }), true, true)
    } catch (e) {
      // throw e
    } finally {
      this.intersectionObserver && this.intersectionObserver.unobserve(this.$el)
      this.intersectionObserver && this.intersectionObserver.disconnect()
      this.needObserver = false
    }
  }
}
</script>
<style lang="scss" scoped>
    .mini-chart {
      /deep/ .highcharts-plot-background {
        fill: #fafbfd;
      }
    }
</style>
