<template>
  <div class="card">
    <h4 class="card__title" @click="clickHandle" :title="title" :style="{ borderLeftColor: seriesDataMap[level].color }">{{title ||
      'Title'}}</h4>
    <div class="card__content" v-if="options" v-bkloading="{ isLoading: isLoading }">
      <monitor-eacharts
        v-if="seriesData.length"
        height="36"
        :options="options"
        @click="clickHandle"
        :unit="valueSuffix"
        :series="seriesData">
      </monitor-eacharts>
      <span class="error-content" v-else @click="clickHandle" :title="message">{{message}}</span>
    </div>
  </div>
</template>

<script>
import { gotoPageMixin } from '../../../../common/mixins'
import { graphPoint } from '../../../../../monitor-api/modules/alert_events'
import MonitorEacharts from '../../../../../monitor-ui/monitor-echarts/monitor-echarts'
export default {
  name: 'business-alarm-card',
  components: {
    MonitorEacharts
  },
  mixins: [gotoPageMixin],
  props: {
    alarm: {
      type: Object,
      default() {
        return {}
      }
    },
    id: null,
    title: {
      type: String,
      default: ''
    },
    level: {
      type: [String, Number],
      default: '1'
    }
  },
  data() {
    return {
      observer: null,
      needObserver: true,
      styles: {
        width: 210,
        height: 37
      },
      utcoffset: 0,
      valueSuffix: '',
      seriesData: [],
      alarmYAxis: [],
      isLoading: false,
      message: this.$t('查询无数据'),
      seriesDataMap: {
        1: {
          name: this.$t('致命告警'),
          color: '#EA3636'
        },
        2: {
          name: this.$t('预警告警'),
          color: '#FF9C01'
        },
        3: {
          name: this.$t('提醒告警'),
          color: '#FFD000'
        }
      }
    }
  },
  computed: {
    options() {
      return {
        color: [this.seriesDataMap[this.level].color],
        legend: {
          show: false
        },
        xAxis: {
          splitLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            show: false
          },
          boundaryGap: false
        },
        grid: {
          containLabel: true,
          left: 5,
          right: 5,
          top: 5,
          bottom: 5,
          backgroundColor: 'transparent'
        },
        yAxis: {
          scale: false,
          min: 0,
          splitLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            show: false
          }
        },
        tooltip: {
          appendToBody: true
        }
      }
    }
  },
  mounted() {
    this.registerObserver()
    this.observer.unobserve(this.$el)
    this.observer.observe(this.$el)
  },
  beforeDestroy() {
    this.observer.unobserve(this.$el)
    this.observer.disconnect()
  },
  methods: {
    registerObserver() {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.intersectionRatio > 0 && this.needObserver) {
            this.getAlarmChatData()
          }
        })
      })
    },
    getAlarmChatData() {
      this.observer.unobserve(this.$el)
      this.observer.disconnect()
      this.needObserver = false
      this.isLoading = true
      graphPoint({
        id: this.id,
        chart_type: 'main'
      }).then((data) => {
        this.utcoffset = data.utcoffset
        this.valueSuffix = data.unit
        this.seriesData = data.series.map((item) => {
          if (item.data && item.data.length) {
            item.data.forEach((i, j) => {
              if (i[0] === data.begin_source_timestamp) {
                item.data[j] = {
                  symbolSize: 6,
                  symbol: 'circle',
                  value: [i[0], i[1]],
                  itemStyle: {
                    borderWidth: 2,
                    enabled: true,
                    shadowBlur: 0,
                    opacity: 1,
                    borderColor: '#DDDDDD'
                  },
                  label: {
                    show: false
                  }
                }
              }
            })
          }
          return {
            ...item,
            lineStyle: {
              width: 1
            },
            areaStyle: {
              opacity: 0.25
            }
          }
        })
      })
        .catch((e) => {
          this.seriesData = []
          this.message = e.message || this.$t('数据拉取异常')
        })
        .finally(() => {
          this.isLoading = false
        })
    },
    clickHandle() {
      this.$router.push({
        name: 'event-center-detail',
        params: {
          id: this.alarm.event_id
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
    @import "../../common/mixins";

    .card {
      padding: 4px 0 20px 0;
      &__title {
        font-size: 12px;
        color: $defaultFontColor;
        padding-left: 6px;
        border-left: 2px solid #a3c5fd;
        text-align: left;
        margin: 0 0 10px 0;
        max-width: 208px;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;

        @include hover();

      }
      &__content {
        min-width: 210px;
        min-height: 37px;
        overflow: auto;
        background: #fafbfd;
        text-align: center;
        line-height: 37px;
        font-weight: bold;
        .error-content {
          display: block;
          width: 100%;
          max-width: 208px;
          height: 100%;
          text-overflow: ellipsis;
          overflow: hidden;
          white-space: nowrap;

          @include hover();
        }
      }
    }
</style>
