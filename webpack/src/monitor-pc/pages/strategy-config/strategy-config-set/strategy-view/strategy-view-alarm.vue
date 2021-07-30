<template>
  <div class="strategy-view-alarm">
    <div class="alarm-title">图表标题</div>
    <div class="alarm-content-wrap">
      <div class="alarm-bar"></div>
      <div class="alarm-label mt10">
        <span class="alarm-label-item"
              v-for="(item, index) in labels"
              :key="index">
          {{item}}
        </span>
      </div>
      <div class="alarm-legend mt20">
        <div class="alarm-legend-item"
             v-for="item in data.alarmAggregation"
             :key="item.level">
          <span class="legend-icon" :style="{ background: levelMap[item.level] }"></span>
          <span class="legend-name">{{item.name}}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import { handleTimeRange } from '../../../../utils/index'
import moment from 'moment'

@Component({ name: 'strategy-view-alarm' })
export default class StrategyViewAlarm extends Vue {
  private data = {
    range: 1 * 60 * 60 * 1000,
    alarmAggregation: []
  }
  private levelMap = {
    1: '#ea3636',
    2: '#ff9c01',
    3: '#ffde3a',
    4: '#7dccac',
    5: '#d8d8d8',
    6: '#979ba5'
  }
  private labelNums = 6

  private get labels() {
    const { startTime, endTime } = handleTimeRange(this.data.range)
    const step = (endTime - startTime) / this.labelNums

    const labels = []
    let curTime = startTime
    while (curTime <= endTime) {
      curTime = curTime + step
      labels.push(moment(curTime * 1000).format('hh:mm'))
    }
    return labels
  }

  private created() {
    this.data.alarmAggregation = [
      {
        level: 1,
        name: this.$t('致命')
      },
      {
        level: 2,
        name: this.$t('预警')
      },
      {
        level: 3,
        name: this.$t('提醒')
      },
      {
        level: 4,
        name: this.$t('正常')
      },
      {
        level: 5,
        name: this.$t('无数据')
      },
      {
        level: 6,
        name: this.$t('信号屏蔽')
      }
    ]
  }
}
</script>
<style lang="scss" scoped>
.strategy-view-alarm {
  .alarm-title {
    font-weight: 700;
  }
  .alarm-content-wrap {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0 22px;
    .alarm-bar {
      height: 16px;
      background: red;
    }
    .alarm-label {
      display: flex;
      justify-content: space-between;
    }
    .alarm-legend {
      display: flex;
      justify-content: center;
      &-item {
        display: flex;
        align-items: center;
        margin-right: 8px;
        .legend-icon {
          width: 12px;
          height: 12px;
          display: inline-block;
          margin-right: 3px;
        }
      }
    }
  }
}
</style>
