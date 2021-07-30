<template>
  <div @click="handleFocus" class="step-verify-input" :class="{ 'is-empty': showValidate && validator.content }">
    <slot></slot>
    <span class="bk-icon icon-exclamation-circle-shape tooltips-icon"
          v-show="showValidate && validator.content && position === 'right'"
          v-bk-tooltips.top-end="validator"></span>
    <span class="bottom-text" v-show="showValidate && position === 'bottom'">{{validator.content}}</span>
  </div>
</template>

<script>
export default {
  name: 'StepVerifyInput',
  props: {
    position: {
      type: String,
      default: 'bottom'
    },
    validator: {
      type: Object,
      default() {
        return {
          content: this.$t('必填项')
        }
      }
    },
    showValidate: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    handleFocus() {
      // this.$emit('update:showValidate', false)
    }
  }
}
</script>

<style scoped lang="scss">
  .step-verify-input {
    position: relative;
    display: flex;
    align-items: center;
    .tooltips-icon {
      display: inline-block;
      position: absolute;
      right: 20px;
      top: 10px;
      font-size: 16px;
    }
    .bottom-text {
      position: absolute;
      top: 100%;
      left: 0;
      width: 600px;
      padding-top: 6px;
      color: #f56c6c;
      font-size: 12px;
      line-height: 1;
    }
    /deep/ .bk-select {
      width: 100%;
    }
  }
  .is-empty {
    /deep/ input {
      border-color: #ff5656;
    }
    .tooltips-icon {
      color: #ea3636;
      cursor: pointer;
    }
  }
</style>
