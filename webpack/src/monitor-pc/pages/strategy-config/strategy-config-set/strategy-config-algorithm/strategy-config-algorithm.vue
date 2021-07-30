<template>
  <bk-dialog
    :value="dialogShow"
    :theme="'primary'"
    :width="dialogWidth"
    :esc-close="false"
    :mask-close="false"
    header-position="left" :title="$t('添加检测算法')"
    :ok-text="$t('添加')"
    :auto-close="false"
    @cancel="handleCancel"
    @confirm="handleConfirm">
    <div v-bkloading="{ isLoading: loading }">
      <div class="dialog-header">
        <!-- <span class="dialog-header-title"> {{ $t('检测算法') }} </span> -->
        <bk-select
          v-model="active"
          :searchable="false"
          :clearable="false"
          style="width: 180px"
          :disabled="mode !== 'add'"
          @change="handleValueChange">
          <bk-option
            v-for="(option, index) in options"
            :key="index"
            :disabled="!!option.disabled"
            :id="option.id"
            v-show="option.show"
            :name="option.name">
          </bk-option>
        </bk-select>
        <span class="title-unit" v-if="unitSuffixList && unitSuffixList.length">
          {{ $t('单位：') }}
          <bk-select
            v-model="algorithmUnit"
            :searchable="false"
            :clearable="false"
            class="unit-select">
            <bk-option
              v-for="option in unitSuffixList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </span>
      </div>
      <div v-if="active === 'Threshold'">
        <div class="dialog-defualt">
          <div class="dialog-defualt-title"> {{ $t('当前值') }}{{ $t('满足以下条件时触发') }} </div>
          <strategy-algorithm-input :value="curItem.value" @change="handleThresholdChange"></strategy-algorithm-input>
        </div>
      </div>
      <template v-if="active === 'AdvancedYearRound'">
        <div class="dialog-other">
          <div class="dialog-other-row"> {{ $t('较前') }} <bk-input :clearable="true" v-model="AdvancedYearRound.ceil_interval" class="input-top" type="number" :placeholder="$t('输入整数')" :min="1" :precision="0"></bk-input> {{ $t('天同一时刻绝对值的均值') }} <div>
            <bk-input v-model="AdvancedYearRound.ceil" style="width: 151px" type="number" :placeholder="$t('输入数字')" :min="0">
              <template slot="prepend">
                <div class="input-text" style="color: #2dcb56"> {{ $t('上升') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-other-row" style="margin-top: 20px"> {{ $t('较前') }} <bk-input :clearable="true" v-model="AdvancedYearRound.floor_interval" class="input-top" type="number" :placeholder="$t('输入整数')" :min="1" :precision="0"></bk-input> {{ $t('天同一时刻绝对值的均值') }} <div>
            <bk-input v-model="AdvancedYearRound.floor" style="width: 151px" :min="0" type="number" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #ea3636"> {{ $t('下降') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-icon">{{ $t('或') }}</div>
        </div>
      </template>
      <template v-else-if="active === 'AdvancedRingRatio'">
        <div class="dialog-other">
          <div class="dialog-other-row"> {{ $t('较前') }} <bk-input :clearable="true" v-model="AdvancedRingRatio.ceil_interval" class="input-top" type="number" :placeholder="$t('输入整数')" :min="1" :precision="0"></bk-input> {{ $t('个时间点的均值') }} <div>
            <bk-input v-model="AdvancedRingRatio.ceil" style="width: 151px" :min="0" type="number" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #2dcb56"> {{ $t('上升') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-other-row" style="margin-top: 20px"> {{ $t('较前') }} <bk-input :clearable="true" v-model="AdvancedRingRatio.floor_interval" class="input-top" type="number" :placeholder="$t('输入整数')" :min="1" :precision="0"></bk-input> {{ $t('个时间点的均值') }} <div>
            <bk-input v-model="AdvancedRingRatio.floor" style="width: 151px" :min="0" type="number" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #ea3636"> {{ $t('下降') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-icon">{{ $t('或') }}</div>
        </div>
      </template>
      <template v-else-if="active === 'SimpleRingRatio'">
        <div class="dialog-other">
          <div class="dialog-other-row"> {{ $t('当前值较前一时刻') }} <div>
            <bk-input v-model="SimpleRingRatio.ceil" style="width: 151px" type="number" :min="0" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #2dcb56"> {{ $t('上升') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-other-row" style="margin-top: 20px"> {{ $t('当前值较前一时刻') }} <div>
            <bk-input v-model="SimpleRingRatio.floor" style="width: 151px" type="number" :min="0" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #ea3636"> {{ $t('下降') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-icon">{{ $t('或') }}</div>
        </div>
      </template>
      <template v-else-if="active === 'SimpleYearRound'">
        <div class="dialog-other">
          <div class="dialog-other-row"> {{ $t('当前值较上周同一时刻') }} <div>
            <bk-input v-model="SimpleYearRound.ceil" style="width: 151px" :min="0" type="number" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #2dcb56"> {{ $t('上升') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-other-row" style="margin-top: 20px"> {{ $t('当前值较上周同一时刻') }} <div>
            <bk-input v-model="SimpleYearRound.floor" style="width: 151px" :min="0" type="number" :placeholder="$t('输入数字')">
              <template slot="prepend">
                <div class="input-text" style="color: #ea3636"> {{ $t('下降') }} </div>
              </template>
              <template slot="append">
                <div class="input-symbol symbol-append">%</div>
              </template>
            </bk-input>
          </div> {{ $t('时触发告警') }} </div>
          <div class="dialog-icon">{{ $t('或') }}</div>
        </div>
      </template>
      <template v-else-if="active === 'PartialNodes'">
        <div class="dialog-uptime">
          {{ $t('满足以上条件的拨测节点数') }}>=
          <bk-input class="dialog-uptime-input" v-model="PartialNodes.count" :min="1" type="number" :placeholder="$t('输入整数')" @input="hanldeInputNumber" :precision="0">
          </bk-input> {{ $t('时触发告警') }} </div>
      </template>
      <template v-else-if="active === 'YearRoundAmplitude'">
        <div class="dialog-uptime"> {{ $t('当前值') }} <span class="method-span need-margin">-</span> {{ $t('前一时刻值') }} <bk-select class="dialog-uptime-input" v-model="YearRoundAmplitude.method" :clearable="false">
          <bk-option v-for="item in methods"
                     :key="item.id"
                     :id="item.id"
                     :name="item.name">
          </bk-option>
        </bk-select> {{ $t('过去') }} <bk-input v-model="YearRoundAmplitude.days" :clearable="false" :min="1" :precision="0" class="dialog-uptime-input" type="number"></bk-input> {{ $t('天内任意一天同时刻差值') }} <span class="method-span" style="margin-left: 5px">×</span>
          <bk-input class="dialog-uptime-input" type="number" v-model="YearRoundAmplitude.ratio" :clearable="false"></bk-input>
          <span class="method-span">+</span>
          <bk-input class="dialog-uptime-input" type="number" v-model="YearRoundAmplitude.shock" :clearable="false"></bk-input>
        </div>
      </template>
      <template v-else-if="active === 'RingRatioAmplitude'">
        <div class="dialog-uptime" key="RingRatioAmplitude"> {{ $t('当前值与前一时刻值') }} <span class="method-span" style="margin-left: 5px">>=</span>
          <bk-input v-model="RingRatioAmplitude.threshold" :clearable="false" class="dialog-uptime-input" type="number"></bk-input> {{ $t('且，之间差值') }} <span class="method-span need-margin">>=</span> {{ $t('前一时刻') }} <span class="method-span" style="margin-left: 5px">×</span>
          <bk-input v-model="RingRatioAmplitude.ratio" :clearable="false" class="dialog-uptime-input" type="number" :show-controls="true">
            <!-- <template slot="append">
                            <div class="input-symbol symbol-append">%</div>
                        </template> -->
          </bk-input>
          <span class="method-span">+</span>
          <bk-input v-model="RingRatioAmplitude.shock" :clearable="false" class="dialog-uptime-input" type="number"></bk-input>
        </div>
      </template>
      <template v-else-if="active === 'YearRoundRange'">
        <div class="dialog-uptime" key="YearRoundRange"> {{ $t('当前值') }} <bk-select v-model="YearRoundRange.method" :clearable="false" class="dialog-uptime-input">
          <bk-option v-for="item in methods"
                     :key="item.id"
                     :id="item.id"
                     :name="item.name">
          </bk-option>
        </bk-select> {{ $t('过去') }} <bk-input v-model="YearRoundRange.days" :min="1" :precision="0" :clearable="false" class="dialog-uptime-input" type="number"></bk-input> {{ $t('天内同时刻绝对值') }} <span class="method-span" style="margin-left: 5px">×</span>
          <bk-input v-model="YearRoundRange.ratio" :clearable="false" class="dialog-uptime-input" type="number" :show-controls="true">
            <!-- <template slot="append">
                            <div class="input-symbol symbol-append">%</div>
                        </template> -->
          </bk-input>
          <span class="method-span">+</span>
          <bk-input v-model="YearRoundRange.shock" :clearable="false" class="dialog-uptime-input" type="number"></bk-input>
        </div>
      </template>
      <template v-else-if="active === 'IntelligentDetect'">
        <div class="ai-check">
          <div class="ai-check-item">
            <span class="check-title">{{$t('突增率：')}}</span>
            <bk-select behavior="simplicity" size="small" class="check-select" v-model="IntelligentDetect.anomaly_detect_direct" :clearable="false">
              <bk-option
                v-for="item in anomalyList"
                :key="item.id"
                :id="item.id"
                :name="item.name">
              </bk-option>
            </bk-select>
            <!-- <span>{{$t('超过')}}</span>
            <bk-input behavior="simplicity" class="check-input" v size="small" /> % -->
          </div>
          <div class="ai-check-item">
            <span class="check-title">{{$t('敏感度：')}}</span>
            <!-- <check-bar v-model="IntelligentDetect.sensitivity_value" /> -->
            <bk-slider class="check-slider" v-model="IntelligentDetect.sensitivity_value" :min-value="0" :max-value="100" /><span class="check-value">{{IntelligentDetect.sensitivity_value}}</span>
          </div>
        </div>
        <!-- <div class="ai-tips">
          <i class="icon-monitor icon-tishi"></i>{{$t('智能异常学习时长需7天后数据生效')}}
        </div> -->
      </template>
      <div class="validate-message" :style="{ visibility: validate ? 'hidden' : 'visible' }"> {{ $t('检测算法填写不完整，请完善后添加') }} </div>
    </div>
  </bk-dialog>
</template>

<script>
import StrategyAlgorithmInput from '../strategy-set-input/strategy-algorithm-input'
import { createNamespacedHelpers } from 'vuex'
import { isPostiveInt } from '../../../../../monitor-common/utils/utils'
const { mapGetters, mapActions } = createNamespacedHelpers('strategy-config')
export default {
  name: 'StrategyConfigAlgorithm',
  components: {
    StrategyAlgorithmInput
  },
  props: {
    dialogShow: Boolean,
    mode: {
      type: String,
      required: true,
      validator(v) {
        return ['add', 'edit', 'delete'].includes(v)
      }
    },
    selectedAlgorithms: {
      type: Array,
      default() {
        return []
      }
    },
    value: {
      type: Object,
      default() {
        return {
          type: 'Threshold',
          config: []
        }
      }
    },
    defaultUnit: {
      type: String,
      default: ''
    },
    unitSuffixId: {
      type: [String, Number],
      default: 'NONE'
    },
    unitSuffixList: {
      type: Array,
      default: () => []
    },
    uptimeCheckType: [String, Number],
    dataTypeLabel: String,
    dataSourceLabel: String,
    // 计算公式
    aggMethod: String,
    isIcmp: Boolean, // 拨测服务的协议类型
    allAlgorithm: Object // 已经选中的其他算法
  },
  data() {
    const defaultData = this.getDefaultData()
    return {
      active: '',
      options: [
        {
          id: 'Threshold',
          name: this.$t('静态阈值'),
          show: true
        },
        {
          id: 'AdvancedYearRound',
          name: this.$t('同比策略（高级）'),
          show: true
        },
        {
          id: 'AdvancedRingRatio',
          name: this.$t('环比策略（高级）'),
          show: true
        },
        {
          id: 'SimpleYearRound',
          name: this.$t('同比策略（简易）'),
          show: true
        },
        {
          id: 'SimpleRingRatio',
          name: this.$t('环比策略（简易）'),
          show: true
        },
        {
          id: 'PartialNodes',
          name: this.$t('部分节点数'),
          show: true,
          disabled: true
        },
        {
          id: 'YearRoundAmplitude',
          name: this.$t('同比振幅'),
          show: true
        },

        {
          id: 'RingRatioAmplitude',
          name: this.$t('环比振幅'),
          show: true
        },
        {
          id: 'YearRoundRange',
          name: this.$t('同比区间'),
          show: true
        },
        {
          id: 'IntelligentDetect',
          name: this.$t('智能异常检测'),
          show: !!window.enable_aiops
        }
      ],
      methods: [
        {
          id: 'gt',
          name: '>'
        },
        {
          id: 'gte',
          name: '>='
        },
        {
          id: 'lt',
          name: '<'
        },
        {
          id: 'lte',
          name: '<='
        },
        {
          id: 'eq',
          name: '='
        }
      ],
      loading: false,
      ...defaultData,
      unitMap: {},
      unitList: [],
      algorithmUnit: '',
      anomalyList: [
        {
          id: 'ceil',
          name: this.$t('向上')
        },
        {
          id: 'floor',
          name: this.$t('向下')
        },
        {
          id: 'all',
          name: this.$t('向上或向下')
        }
      ]
    }
  },
  computed: {
    ...mapGetters(['uptimeCheckMap']),
    curItem() {
      return this[this.active]
    },
    curOption() {
      return this.options.find(item => item.id === this.active)
    },
    dialogWidth() {
      if (this.active === 'YearRoundAmplitude' || this.active === 'RingRatioAmplitude') {
        return 856
      } if (this.active === 'YearRoundRange') {
        return 770
      }
      return 700
    }
  },
  watch: {
    dialogShow: {
      async handler(v) {
        if (v) {
          this.options.forEach((ite) => {
            const item = ite
            const uptimeItem = this.uptimeCheckMap[this.uptimeCheckType]
            // this.dataTypeLabel === 'log' ||
            if (this.aggMethod === 'REAL_TIME') { // 监控项时日志关键字 只能选择静态阈值
              item.show = item.id === 'Threshold' && !this.selectedAlgorithms.includes(item.id)
            } else if (uptimeItem) {
              // ICMP协议的拨测服务开放所有的检测算法选项、HTTP、TCP、UDP协议仅有静态阈值检测算法
              if (!this.isIcmp) {
                item.show = item.id === uptimeItem && !this.selectedAlgorithms.includes(item.id)
              } else {
                item.show = item.id !== 'PartialNodes' && !this.selectedAlgorithms.includes(item.id)
              }
            } else if (item.id === 'IntelligentDetect') {
              item.show = window.enable_aiops && ['bk_data', 'bk_monitor'].includes(this.dataSourceLabel)
              && this.dataTypeLabel === 'time_series' && !this.selectedAlgorithms.includes(item.id)
              // 3种级别算法中 智能检测算法只能选择一次
              if (item.show && this.allAlgorithm) {
                item.show = !Object.keys(this.allAlgorithm)
                  .some(key => this.allAlgorithm[key]
                    .some(set => set.type === 'IntelligentDetect'))
              }
            } else {
              item.show = item.id !== 'PartialNodes' && !this.selectedAlgorithms.includes(item.id)
            }
          })
          if (!this.active || this.selectedAlgorithms.length === 0 || this.selectedAlgorithms.includes(this.active)) {
            const activeItem = this.options.find(item => item.show)
            if (activeItem) {
              this.active = this.options.find(item => item.show).id
            }
          }
        } else {
          const data = this.getDefaultData()
          Object.keys(data).forEach((key) => {
            this[key] = data[key]
          })
          this.active = ''
        }
        this.algorithmUnit =  this.value ? this.value.algorithmUnit : this.unitSuffixId
      },
      immediate: true
    },
    value: {
      async handler(v) {
        if (v && this.mode === 'edit') {
          this.active = v.type
          if (v.type === 'Threshold') {
            this.Threshold.value = v.config.map(({ method, threshold, condition }) => {
              const set = { method, value: threshold }
              condition && (set.condition = condition)
              return set
            })
          } else {
            Object.keys(v.config).forEach((key) => {
              this.curItem[key] = v.config[key]
            })
          }
        }
      },
      immediate: true
    }
  },
  beforeDestroy() {
    this.handleCancel()
  },
  methods: {
    ...mapActions(['getUnitData']),
    getDefaultData() {
      return {
        Threshold: {
          value: []
        },
        AdvancedYearRound: {
          ceil_interval: '',
          ceil: '',
          floor_interval: '',
          floor: ''
        },
        AdvancedRingRatio: {
          ceil_interval: '',
          ceil: '',
          floor_interval: '',
          floor: ''
        },
        SimpleRingRatio: {
          ceil: '',
          floor: ''
        },
        SimpleYearRound: {
          ceil: '',
          floor: ''
        },
        PartialNodes: {
          count: 1
        },
        YearRoundAmplitude: {
          method: 'gte',
          days: '',
          ratio: '',
          shock: ''
        },
        RingRatioAmplitude: {
          threshold: '',
          ratio: '',
          shock: ''
        },
        YearRoundRange: {
          method: 'gte',
          days: '',
          ratio: '',
          shock: ''
        },
        IntelligentDetect: {
          sensitivity_value: 50,
          anomaly_detect_direct: 'all'
        },
        validate: true
      }
    },
    handleCancel() {
      this.$emit('hide-dialog', false)
    },
    handleConfirm() {
      this.validate = false
      if (this.active === 'Threshold') {
        this.validate = !!this.curItem.value.length
        && this.curItem.value.every(set => (`${set.value}`).trim().length > 0)
      } else if (this.active === 'AdvancedYearRound' || this.active === 'AdvancedRingRatio') {
        const ceilInterval = this.curItem.ceil_interval
        const { ceil } = this.curItem
        const floorInterval = this.curItem.floor_interval
        const { floor } = this.curItem
        this.validate = (ceilInterval === '' && ceil === ''
                && isPostiveInt(floorInterval) && floor !== '' && floor >= 0)
            || (floorInterval === '' && floor === '' && isPostiveInt(ceilInterval) && ceil !== '' && ceil >= 0)
            || (isPostiveInt(floorInterval) && floor !== '' && floor >= 0
                && isPostiveInt(ceilInterval) && ceil !== '' && ceil >= 0)
      } else if (this.active === 'SimpleRingRatio' || this.active === 'SimpleYearRound') {
        const { ceil } = this.curItem
        const { floor } = this.curItem
        this.validate = (ceil !== '' && ceil >= 0 && floor === '')
            || (floor !== '' && floor >= 0 && ceil === '')
            || (floor !== '' && ceil !== '' && ceil >= 0 && floor >= 0)
      } else if (this.active === 'PartialNodes') {
        this.validate = this.curItem.count >= 1
      } else if (this.active === 'YearRoundAmplitude' || this.active === 'YearRoundRange') {
        const { days, ratio, shock } = this.curItem
        this.validate = days >= 1 && ratio !== '' && shock !== ''
      } else if (this.active === 'RingRatioAmplitude') {
        const { threshold, ratio, shock } = this.curItem
        this.validate = threshold !== '' && ratio !== '' && shock !== ''
      } else if (this.active === 'IntelligentDetect') {
        this.validate = true
      }
      if (this.validate) {
        const data = this.handleTransformValue()
        this.$emit('confirm-dialog', false, data)
      }
    },
    handleThresholdChange(val) {
      this.curItem.value = val
    },
    handleValueChange() {
      this.validate = true
    },
    handleTransformValue() {
      const data = {
        type: this.active,
        title: this.curOption.name,
        algorithmUnit: this.algorithmUnit
      }
      if (this.active === 'Threshold') {
        data.config = this.curItem.value.map(({ method, value, condition }) => {
          const set = { method, threshold: value }
          condition && (set.condition = condition)
          return set
        })
        return data
      }
      data.config = this.curItem
      return data
    },
    hanldeInputNumber(v) {
      this.$nextTick().then(() => {
        this.PartialNodes.count = +(`${v}`).replace(/\.[0-9e]*/, '')
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.dialog-header {
  display: flex;
  align-items: center;
  margin-top: -10px;
  &-title {
    width: 67px;
    margin-right: 5px;
    position: relative;
    &::after {
      content: "*";
      color: #ea3636;
      position: absolute;
      right: 0px;
    }
  }
  .title-unit {
    font-weight: normal;
    padding-left: 16px;
    border-left: 1px solid #d8d8d8;
    margin-left: 16px;
    display: flex;
    align-items: center;
    .unit-select {
      width: 180px;
      display: inline-block;
    }
  }
}
.validate-message {
  display: flex;
  min-width: 100%;
  align-items: center;
  font-size: 12px;
  color: #ea3636;
  margin-top: 2px;
  height: 18px;
  visibility: hidden;
  margin-bottom: -10px;
}
.dialog-defualt {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 72px;
  width: 652px;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  margin-top: 10px;
  padding: 16px 20px 20px 20px;
  flex-wrap: wrap;
  &-title {
    margin-bottom: 10px;
    font-weight: bold;
    font-size: 12px;
    display: flex;
    align-items: center
  }
}
.dialog-other {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  height: 124px;
  width: 652px;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  margin-top: 10px;
  padding-left: 20px;
  position: relative;
  &-row {
    display: flex;
    align-items: center;
    /deep/ .bk-input-number {
      position: relative;
      .input-number-option {
        display: none;
      }
    }
  }
  .input-top {
    width: 72px;
    margin: 0 10px;
  }
  .input-text {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 32px;
  }
  .input-symbol {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 32px;
    &.symbol-append {
      width: 32px;
    }
  }
  /deep/ .control-append-group {
    margin: 0 10px;
  }
  /deep/ .control-prepend-group {
    background-color: #fafbfd;
    width: 32px;
  }
  /deep/ .bk-form-input {
    padding: 0 10px;
  }
}
.dialog-uptime {
  display: flex;
  align-items: center;
  height: 72px;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  margin-top: 10px;
  padding: 0 20px;
  &-input {
    margin: 0 10px 0 8px;
    width: 72px;
  }
  .method-span {
    color: #3a84ff;
  }
  .need-margin {
    margin: 0 5px;
  }
  .percent-input {
    width: 86px;
    margin: 0 5px;
    /deep/ .group-append {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 32px;
      background: #fafbfd;
      font-size: 12px;
    }
  }
}
.dialog-icon {
  width: 24px;
  height: 24px;
  border: 1px solid #dcdee5;
  border-radius: 6px;
  text-align: center;
  position: absolute;
  right: -12px;
  background-color: #fff;
}
.ai-check {
  width: 652px;
  height: 126px;
  background: #fff;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  display: flex;
  flex-direction: column;
  padding: 14px 0 0 10px;
  color: #63656e;
  font-size: 12px;
  margin-top: 10px;
  &-item {
    display: flex;
    align-items: center;
    margin-top: 18px;
    .check-title {
      font-weight: bold;
      line-height: 20px;
      height: 20px;
    }
    .check-slider {
      flex: 1;
      margin-right: 10px;
    }
    .check-value {
      margin-right: 40px;
    }
    .check-select {
      width: 120px;
      margin-right: 10px;
    }
    .check-input {
      width: 80px;
      margin-left: 10px;
    }
  }
}
.ai-tips {
  display: flex;
  align-items: center;
  height: 16px;
  color: #ffb848;
  margin-top: 6px;
  font-size: 12px;
  .icon-monitor {
    font-size: 16px;
    margin-right: 8px;
  }
}
</style>
