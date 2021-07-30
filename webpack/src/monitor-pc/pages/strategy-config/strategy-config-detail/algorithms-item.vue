<template>
  <div>
    <!-- 静态阈值 -->
    <div v-if="type === 'Threshold'" class="algorithms-content">
      {{ $t('当前值') }}&nbsp;<span class="bold-span" v-for="(item, index) in threshold" :key="index">{{ item }}&nbsp;</span> {{ $t('时触发告警') }} </div>
    <!-- 环比策略（高级）同比策略（高级） -->
    <div v-else-if="['AdvancedYearRound', 'AdvancedRingRatio'].includes(type)" class="algorithms-content"> {{ $t('较前') }} <span v-if="ceil || all">
      <span class="bold-span">{{ algorithm.ceilInterval }}</span>
      <span v-if="type === 'AdvancedYearRound'"> {{ $t('天同一时刻绝对值的均值上升') }} </span>
      <span v-else-if="type === 'AdvancedRingRatio'"> {{ $t('个时间点的均值上升') }} </span>
      <span class="bold-span">{{ algorithm.ceil }}%</span>
    </span>
      <span v-if="all">，{{ $t('或较前') }} </span>
      <span v-if="floor || all">
        <span class="bold-span">{{ algorithm.floorInterval }}</span>
        <span v-if="type === 'AdvancedYearRound'"> {{ $t('天同一时刻绝对值的均值下降') }} </span>
        <span v-else-if="type === 'AdvancedRingRatio'"> {{ $t('个时间的均值下降') }} </span>
        <span class="bold-span">{{ algorithm.floor }}%</span>
      </span> {{ $t('时触发告警') }} </div>
    <!-- 环比策略（简易）同比策略（简易） -->
    <div v-else-if="['SimpleYearRound', 'SimpleRingRatio'].includes(type)" class="algorithms-content">
      <span v-if="ceil || all">
        <span v-if="type === 'SimpleYearRound' "> {{ $t('当前值较上周同一时刻上升') }} </span>
        <span v-else-if="type === 'SimpleRingRatio'"> {{ $t('当前值较上一个时刻上升') }} </span>
        <span class="bold-span">{{ algorithm.ceil }}%</span>
      </span>
      <span v-if="all">&nbsp;{{ $t('或') }}&nbsp;</span>
      <span v-if="floor || all">
        <span v-if="type === 'SimpleYearRound' "> {{ $t('当前值较上周同一时刻下降') }} </span>
        <span v-else-if="type === 'SimpleRingRatio'"> {{ $t('当前值较上一个时刻下降') }} </span>
        <span class="bold-span">{{ algorithm.floor }}%</span>
      </span> {{ $t('时触发告警') }} </div>
    <!-- 部分节点数 -->
    <div v-else-if="type === 'PartialNodes'" class="algorithms-content">
      {{ $t('满足以上条件的拨测节点数') }}>= <span class="bold-span">{{ algorithm.count }}</span> {{ $t('时触发告警') }}
    </div>
    <!-- 同比振幅 环比振幅 同比区间 -->
    <div v-else-if="['YearRoundAmplitude', 'YearRoundRange', 'RingRatioAmplitude'].includes(type)" class="algorithms-content">
      <span>
        <span v-if="type === 'YearRoundAmplitude'">{{ $t('当前值') }}&nbsp;<span class="bold-span">−</span>&nbsp;{{ $t('前一时刻值') }}&nbsp;<span class="bold-span">{{ methodMap[algorithm.method] }}</span>&nbsp;{{ $t('过去') }}&nbsp;<span class="bold-span">{{ algorithm.days }}</span></span>
        <span v-else-if="type === 'YearRoundRange'">{{ $t('当前值') }}&nbsp;<span class="bold-span">{{ methodMap[algorithm.method] }}</span>&nbsp;{{ $t('过去') }}&nbsp;<span class="bold-span">{{ algorithm.days }}</span></span>
        <span v-else-if="type === 'RingRatioAmplitude'">{{ $t('当前值与前一时刻值') }}&nbsp;<span class="bold-span">>={{ algorithm.threshold }}</span></span>
      </span>
      <span>
        <span v-if="type === 'YearRoundAmplitude'"> {{ $t('天内任意一天同时刻差值') }} </span>
        <span v-else-if="type === 'YearRoundRange'"> {{ $t('天内同时刻绝对值') }} </span>
        <span v-else-if="type === 'RingRatioAmplitude'">{{ $t('且，之间差值') }}&nbsp;<span class="bold-span">>=</span>&nbsp;{{ $t('前一时刻') }}&nbsp;<span class="bold-span"></span></span>
      </span>
      <span class="bold-span">×&nbsp;{{ algorithm.ratio }}&nbsp;+&nbsp;{{ algorithm.shock }}</span>
    </div>
    <div v-else-if="type === 'IntelligentDetect'" class="algorithms-content">
      {{$t('突增率')}} <span class="bold-span" style="margin-left: 5px">{{ anomalyMap[algorithmConfig.anomaly_detect_direct || algorithmConfig.anomalyDetectDirect] }}</span>  {{$t('敏感度设置为')}}<span class="bold-span" style="margin-left: 5px">{{ algorithmConfig.sensitivity_value || algorithmConfig.sensitivityValue }}</span>
      <!-- <div class="ai-tips">
        <i class="icon-monitor icon-tishi"></i>{{$t('智能异常学习时长7天后数据生效，已学习2天')}}
      </div> -->
    </div>
  </div>
</template>

<script>
import { transformDataKey } from '../../../../monitor-common/utils/utils.js'
export default {
  name: 'AlgorithmsItem',
  props: {
    type: String, // 检测算法类型
    algorithmConfig: [Object, Array], // 检测算法配置
    unit: [String, Number] // 单位
  },
  data() {
    return {
      methodMap: {
        gte: '>=',
        gt: '>',
        lte: '<=',
        lt: '<',
        eq: '=',
        neq: '!='
      },
      algorithm: null,
      threshold: [],
      ceil: false,
      floor: false,
      all: false,
      anomalyMap: {
        ceil: this.$t('向上'),
        floor: this.$t('向下'),
        all: this.$t('向上或向下')
      }
    }
  },
  watch: {
    // 转化成驼峰
    algorithmConfig: {
      handler(newV) {
        this.algorithm = transformDataKey(newV)
        if (this.type === 'Threshold') {
          this.handleThreshold()
        } else {
          this.handleAdvancedLength()
        }
      },
      immediate: true
    }
  },
  methods: {
    handleAdvancedLength() {
      this.ceil = !!this.algorithmConfig.ceil
      this.floor = !!this.algorithmConfig.floor
      this.all = this.floor && this.ceil
    },
    handleThreshold() {
      this.threshold = []
      this.algorithm.forEach((item) => {
        if (item.condition) {
          this.threshold.push(item.condition)
        }
        this.threshold.push(this.methodMap[item.method])
        this.threshold.push(item.threshold)
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.bold-span {
  font-weight: bold;
  color: #3a84ff;
}
.algorithms-title {
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
.algorithms-content {
  margin: 9px 40px 16px 0;
}
.algorithms-line {
  height: 0;
  margin-bottom: 16px;
  border-top: 1px dashed #dcdee5;
}
.ai-tips {
  display: flex;
  align-items: center;
  height: 16px;
  color: #ffb848;
  margin-top: 4px;
  font-size: 12px;
  .icon-monitor {
    font-size: 16px;
    margin-right: 8px;
  }
}
</style>
