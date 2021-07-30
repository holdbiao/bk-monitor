<template>
  <div class="strategy-algorithm">
    <div class="strategy-algorithm-title" :class="'status-' + level">
      {{levelName}}
    </div>
    <ul class="wrap-list">
      <li v-for="(item, index) in algorithmList" :key="index" class="wrap-list-item" :class="{ 'wrap-list-last': index === algorithmList.length - 1 }">
        <div class="item-title">{{ algorithmsTypeMap[item.algorithmType] }}</div>
        <algorithms-item :type="item.algorithmType" :algorithm-config="handleAlgorithmConfig(item.algorithmConfig, index)" :unit="algorithmList.unit"></algorithms-item>
      </li>
    </ul>
  </div>
</template>

<script>
import AlgorithmsItem from './algorithms-item.vue'
import { strategyThresholdMixin } from '../../../common/mixins.js'
export default {
  name: 'TargetRightPanel',
  components: {
    AlgorithmsItem
  },
  mixins: [strategyThresholdMixin],
  props: {
    // 告警等级 致命 预警 提醒
    levelName: {
      type: String,
      required: true
    },
    level: {
      type: [String, Number],
      required: true
    },
    // 每个告警等级所包含的算法
    algorithmList: {
      type: Array,
      default: () => ([])
    }
  },
  data() {
    return {
      // 检测算法对应字段名
      algorithmsTypeMap: {
        Threshold: this.$t('静态阈值'),
        SimpleRingRatio: this.$t('环比策略（简易）'),
        SimpleYearRound: this.$t('同比策略（简易）'),
        AdvancedRingRatio: this.$t('环比策略（高级）'),
        AdvancedYearRound: this.$t('同比策略（高级）'),
        PartialNodes: this.$t('部分节点数'),
        YearRoundAmplitude: this.$t('同比振幅'),
        RingRatioAmplitude: this.$t('环比振幅'),
        YearRoundRange: this.$t('同比区间'),
        IntelligentDetect: this.$t('智能异常检测')
      }
    }
  },
  methods: {
    handleAlgorithmConfig(data, index) {
      return this.algorithmList[index].algorithmType === 'Threshold' ? this.handleThreshold2Config(data) : data
    }
  }
}
</script>

<style lang="scss" scoped>
  @import "../../../static/css/common";
  $statusColors: $deadlyAlarmColor $warningAlarmColor $remindAlarmColor;

  .strategy-algorithm {
    font-size: 12px;
    color: #63656e;
    padding-left: 20px;
    border: 1px solid #dcdee5;
    border-radius: 2px;
    margin: 0 40px 8px 0;
    &-title {
      margin-top: 7px;
      margin-left: -5px;
      font-weight: bold;
      position: relative;

      @for $i from 1 through length($statusColors) {
        &.status-#{$i} {
          &::before {
            background: nth($statusColors, $i);
          }
        }
      }
      &::before {
        content: "";
        background: #ea3636;
        width: 3px;
        height: 12px;
        position: absolute;
        left: -16px;
        top: 1px;
      }
    }
    .wrap-list {
      display: flex;
      flex-direction: column;
      padding-top: 24px;
      &-item {
        display: flex;
        flex-direction: column;
        position: relative;
        min-height: 48;
        border-left: 2px solid #c4c6cc;
        padding-left: 12px;
        margin-bottom: 10px;
        .item-title {
          position: absolute;
          top: -13px;
          font-weight: bold;
          height: 16px;
          display: flex;
          align-items: center;
          &::before {
            content: " ";
            position: absolute;
            left: -16px;
            width: 6px;
            height: 6px;
            border-radius: 100%;
            background: #c4c6cc;
          }
        }
        .item-content {
          margin: 9px 40px 16px 0;
        }
        .item-line {
          height: 0;
          margin-bottom: 16px;
          border-top: 1px dashed #dcdee5;
        }
      }
      &-last {
        border-left: 0;
        padding-left: 14px;
        height: 42px;
        min-height: 42px;
      }
      &-no-data {
        font-size: 14px;
        height: 50px;
        display: flex;
        justify-content: center;
        margin: -10px 0 0 -30px;
        span {
          display: flex;
          align-items: center;
          height: 20px;
          color: #979ba5;
          i {
            color: #dcdee5;
            margin-right: 8px;
            font-size: 22px;
          }
        }
      }
    }
  }

</style>
