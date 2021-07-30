<template>
  <div class="empty-target">
    <top-hint class="target-hint" v-if="needTitle">
      <slot> {{ $t('未选择采集目标，但并不影响本次操作') }} </slot>
    </top-hint>
    <div class="empty-container">
      <i class="icon-monitor icon-tishi hint-icon"></i>
      <div class="hint-text">
        <slot name="desc"> {{ $t('未选择采集目标，无需下发') }} </slot>
      </div>
    </div>
  </div>
</template>

<script>
import TopHint from './top-hint'
export default {
  name: 'empty-target',
  components: {
    TopHint
  },
  props: {
    needTitle: {
      type: Boolean,
      default: true
    }
  }
}
</script>

<style lang="scss" scoped>
  .empty-target {
    height: 500px;
    margin-bottom: 20px;
    .target-hint {
      margin-bottom: 10px;
    }
    .empty-container {
      height: 452px;
      background: #fff;
      border-radius: 2px;
      border: 1px dashed #dcdee5;
      position: relative;
      display: flex;
      justify-content: center;
      .hint-icon {
        position: absolute;
        top: 142px;
        left: calc(50% - 16px);
        font-size: 32px;
        color: #dcdee5;
      }
      .hint-text {
        min-width: 144px;
        height: 16px;
        line-height: 16px;
        position: absolute;
        top: 186px;
        font-size: 12px;
        color: #979ba5;
      }
    }
  }
</style>
