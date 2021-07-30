<template>
  <section class="today-alarm">
    <div class="today-alarm__chart" ref="todayAlarm">
      <span v-if="!seriesData.length || !seriesData.some(item => item.count > 0)" class="alarm-title">{{$t('未恢复告警分布')}}</span>
      <monitor-pie-echart
        v-if="seriesData.length && seriesData.some(item => item.count > 0)"
        :series="series"
        :title="$t('未恢复告警分布')"
        chart-type="pie"
        :options="{ legend: { show: false }, tool: {
          show: true,
          moreShow: false
        } }"
        @chart-click="handlePieItemClick"
        height="320">
        <div class="slot-center" slot="chartCenter" @click="unrecoveredClickHandle">
          <bk-popover :content="$t('点击查看告警列表')">
            <div class="alarm-num">{{unrecoveredCount}}</div>
          </bk-popover>
        </div>
      </monitor-pie-echart>
      <div v-else class="no-data">
        <div class="no-data-desc"> {{ $t('告警空空，一身轻松') }} </div>
      </div>
    </div>
    <div class="today-alarm__footer">
      <div class="item" @click="itemClickHandle(1)">
        <h3 class="serious">{{ seriesData.length ? seriesData.find(item => item.level === 1).count : 0}}</h3>
        <div> {{ $t('致命') }} </div>
      </div>
      <div class="item" @click="itemClickHandle(2)">
        <h3 class="normal">{{ seriesData.length ? seriesData.find(item => item.level === 2).count : 0}}</h3>
        <div> {{ $t('预警') }} </div>
      </div>
      <div class="item" @click="itemClickHandle(3)">
        <h3 class="slight">{{ seriesData.length ? seriesData.find(item => item.level === 3).count : 0}}</h3>
        <div> {{ $t('提醒') }} </div>
      </div>
    </div>
  </section>
</template>

<script>
import MonitorPieEchart from '../../../../monitor-ui/monitor-echarts/monitor-echarts'
import { gotoPageMixin } from '../../../common/mixins'

export default {
  name: 'TodayAlarmPie',
  components: {
    MonitorPieEchart
  },
  mixins: [gotoPageMixin],
  props: {
    seriesData: {
      type: Array,
      required: true
    },
    unrecoveredCount: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      seriesDataMap: {
        1: {
          name: this.$t('致命'),
          color: '#EA3636'
        },
        2: {
          name: this.$t('预警'),
          color: '#FF9C01'
        },
        3: {
          name: this.$t('提醒'),
          color: '#FFD000'
        }
      }
    }
  },
  computed: {
    series() {
      return [{
        label: { show: false },
        cursor: 'pointer',
        data: this.seriesData.map((item) => {
          const seriesMapData = this.seriesDataMap[item.level]
          return {
            value: item.count,
            name: seriesMapData.name,
            level: item.level,
            itemStyle: {
              color: seriesMapData.color
            },
            tooltip: {
              formatter: () => `<span style="color:${seriesMapData.color}">\u25CF</span> <b> ${seriesMapData.name}</b>
              <br/>${this.$t('告警数量')}: <b>${item.count}</b><br/>`,
              textStyle: {
                fontSize: 12
              }
            }
          }
        })
      }]
    }
  },
  methods: {
    handlePieItemClick(params) {
      params?.data && this.itemClickHandle(params.data.level)
    },
    itemClickHandle(level) {
      this.$router.push({
        name: 'event-center',
        params: {
          status: 'ABNORMAL',
          level
        }
      })
    },
    unrecoveredClickHandle() {
      this.$router.push({
        name: 'event-center',
        params: {
          status: 'ABNORMAL'
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
    @import "../common/mixins";

    .today-alarm {
      &__chart {
        position: relative;
        min-width: 348px;
        min-height: 330px;
        .alarm-title {
          height: 19px;
          font-size: 14px;
          font-weight: bold;
          line-height: 19px;
          float: left;
          color: #63656e;
          margin: 20px 0px 0px 18px;
        }
        .slot-center {
          @include hover();
          .alarm-num {
            height: 30px;
            font-size: 24px;
            font-weight: 600;
            color: #313238;
            line-height: 30px;
            text-align: center;
          }
          .alarm-name {
            height: 19px;
            font-size: $fontSmSize;
            color: #3a84ff;
            line-height: 19px;
          }
        }
        .no-data {
          position: absolute;
          left: 50%;
          top: 50%;
          width: 220px;
          height: 220px;
          background: #fff;
          transform: translate3d(-110px, -120px, 0);
          text-align: center;
          background-image: url("../../../static/images/svg/no-alarm.svg");
          background-repeat: no-repeat;
          background-size: contain;
          &-desc {
            position: absolute;
            bottom: -40px;
            text-align: center;
            width: 100%;
            font-size: 20px;
            color: $defaultFontColor;
            font-weight: 300;
          }
          .alarm-num {
            height: 45px;
            font-size: 32px;
            font-weight: 600;
            color: #313238;
            line-height: 45px;
            text-align: center;
          }
          .alarm-name {
            height: 19px;
            font-size: $fontSmSize;
            color: #3a84ff;
            line-height: 19px;
          }
        }
      }
      &__footer {
        border-top: 1px solid $defaultBorderColor;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        bottom: 0;
        .item {
          flex: 1;
          height: 72px;
          display: inline-block;
          border-right: 1px solid $defaultBorderColor;
          &:hover {
            background: #fafbfd;
            cursor: pointer;
          }
          h3 {
            height: 33px;
            font-size: 24px;
            font-weight: 600;
            line-height: 33px;
            text-align: center;
            margin: 7px 0 0 0;
          }
          div {
            text-align: center;
            font-size: $fontSmSize;
            color: #63656e;
          }
          .serious {
            color: $deadlyAlarmColor;
          }
          .normal {
            color: $warningAlarmColor;
          }
          .slight {
            color: $remindAlarmColor;
          }
        }
        :nth-child(3) {
          border-right: 0;
        }
      }
    }
</style>
