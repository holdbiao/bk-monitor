<template>
  <monitor-dialog
    :value.sync="show"
    :title="title || $t('监控目标')"
    width="1100"
    :need-footer="false"
    :z-index="zIndex"
    @on-confirm="handleConfirm"
    @change="handleValueChange">
    <strategy-config-target
      :can-save-empty="canSaveEmpty"
      :tab-disabled="tabDisabled"
      :target-list="targetList"
      :set-config="strategySetConfig"
      :hidden-template="hiddenTemplate"
      @target-change="handleTargetChange"
      @message-change="handleTargetDesChange"
      @target-type-change="handleTargetTypeChange"
      @cancel="handleValueChange">
    </strategy-config-target>
  </monitor-dialog>
</template>
<script lang="ts">
import { Vue, Component, Prop, Watch } from 'vue-property-decorator'
import MonitorDialog from '../../../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import StrategyConfigTarget from '../../strategy-config-target/strategy-config-target.vue'
@Component({
  components: {
    MonitorDialog,
    StrategyConfigTarget
  }
})
export default class StrategySetTarget extends Vue {
  show = false
  // 是否展示
  @Prop({
    type: Boolean,
    default: false
  })
  dialogShow: boolean

  // 业务id
  @Prop()
  bizId: number | string

  // 监控对象类型
  @Prop()
  objectType: string

  // 默认选择的目标
  @Prop()
  targetList: Array<any>

  // 目标类型
  @Prop()
  targetType: string

  // 策略id
  @Prop()
  strategyId: string | number

  // tab的disabled状态控制, 0: 静态disabled; 1: 动态disabled; -1: 都不disabled
  @Prop({ default: null, type: [Number, null] })
  tabDisabled: 0 | 1 | -1 | null

  // 是否允许保存空的目标
  @Prop({ default: false, type: Boolean })
  canSaveEmpty: {
    type: Boolean,
    default: false
  }

  @Prop({ default: false, type: Boolean }) hiddenTemplate: boolean
  @Prop({ default: '', type: String }) title: string

  @Watch('dialogShow', {
    immediate: true
  })
  onDialogShowChange(v) {
    this.show = v
  }

  get zIndex() {
    // eslint-disable-next-line no-underscore-dangle
    if (window.__bk_zIndex_manager && window.__bk_zIndex_manager.nextZIndex) {
      // eslint-disable-next-line no-underscore-dangle
      return window.__bk_zIndex_manager.nextZIndex()
    }
    return 2000
  }

  get strategySetConfig() {
    return {
      targetType: this.targetType,
      objectType: this.objectType,
      bizId: this.bizId,
      strategyId: this.strategyId || 0
    }
  }

  // 是否显示触发
  handleValueChange(v) {
    this.$emit('update:dialogShow', v)
    this.$emit('show-change', v)
  }

  // 点击保存触发
  handleConfirm() {
    this.show = false
    this.$emit('update:dialogShow', false)
  }

  // 选中目标改变触发
  handleTargetChange(targets: Array<any>) {
    this.$emit('targets-change', targets)
    this.handleConfirm()
  }

  // 目标类型改变触发
  handleTargetTypeChange(v) {
    this.$emit('target-type-change', v)
  }

  // 目标描述改变触发
  handleTargetDesChange(message) {
    this.$emit('message-change', message)
  }
}
</script>
