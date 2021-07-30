<template>
  <section class="custom-serious">
    <div class="custom-serious-title"> {{ $t('告警事件') }} </div>
    <div class="custom-serious-content">
      <div class="chart-item" v-for="(item,index) in alarm.abnormal_events" :key="index">
        <business-alarm-card :title="item.strategy_name" :id="item.event_id" :level="item.level" :alarm="item"></business-alarm-card>
      </div>
    </div>
  </section>
</template>

<script>
import BusinessAlarmCard from '../components/business-alarm-card/business-alarm-card'

export default {
  name: 'service-serious',
  components: {
    BusinessAlarmCard
  },
  props: {
    alarm: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../common/mixins";

  .custom-serious {
    &-title {
      font-size: $fontSmSize;
      font-weight: bold;
      color: $defaultFontColor;
      line-height: 19px;
      padding-bottom: 8px;
      margin-right: 40px;
      border-bottom: 1px solid $defaultBorderColor;
    }
    &-content {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      flex-wrap: wrap;
      min-width: 460px;
      max-height: 260px;
      overflow: auto;
      margin-top: 14px;

      @media only screen and (min-width: 1414px) {
        .chart-item:nth-child(2n+1) {
          margin-right: 30px;
        }
      }
      @media only screen and (max-width: 1434px) {
        .chart-item {
          margin-right: 30px;
        }
      }
    }
  }
</style>
