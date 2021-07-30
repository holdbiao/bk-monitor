<template>
  <transition name="ease">
    <div class="dialog" v-show="value">
      <div class="dialog-header">
        <slot name="header">
          <span class="dialog-header-title">
            {{ title }}
          </span>
          <span class="dialog-header-close">
            <i class="icon-monitor icon-mc-close" @click="handleClose"></i>
          </span>
        </slot>
      </div>
      <div class="dialog-content">
        <slot></slot>
      </div>
      <div class="dialog-footer">
        <slot name="footer">
          <bk-button
            :disabled="loading"
            theme="primary"
            class="confirm-btn mr8"
            @click="handleConfirm">
            {{ okText }}
          </bk-button>
          <bk-button :disabled="loading" class="mr8" @click="handleCancel">{{ cancelText }}</bk-button>
          <bk-button :disabled="loading" v-show="showUndo" @click="handleUndo">{{ $t('还原默认') }}</bk-button>
        </slot>
      </div>
    </div>
  </transition>
</template>
<script lang="ts">
import { Vue, Prop, Component, Emit, Model } from 'vue-property-decorator'

@Component({ name: 'peformance-dialog' })
export default class Dialog extends Vue {
  @Model('change', { type: Boolean }) readonly value: boolean
  @Prop({ default: '', type: String }) readonly title: string
  @Prop({ default: '', type: String }) readonly okText: string
  @Prop({ default: '', type: String }) readonly cancelText: string
  @Prop({ default: false, type: Boolean }) readonly loading: boolean
  @Prop({ default: true, type: Boolean }) private readonly showUndo: boolean

  @Emit('close')
  @Emit('change')
  handleClose() {
    return !this.value
  }

  @Emit('confirm')
  handleConfirm() {}

  @Emit('cancel')
  handleCancel() {}

  @Emit('undo')
  handleUndo() {}
}
</script>
<style lang="scss" scoped>
.dialog {
  position: absolute;
  top: 0;
  bottom: 0;
  right: 24px;
  width: 360px;
  border-radius: 2px;
  box-shadow: 0px 3px 6px 0px rgba(0,0,0,.1);
  background: #fff;
  z-index: 200;
  &-header {
    height: 56px;
    padding: 10px 6px 0 24px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #f0f1f5;
    &-title {
      font-size: 20px;
      line-height: 28px;
    }
    &-close {
      margin-top: -4px;
      i {
        font-size: 32px;
        cursor: pointer;
      }
    }
  }
  &-content {
    max-height: calc(100% - 115px);
    overflow: auto;
  }
  &-footer {
    padding: 16px 0 0 20px;
    .mr8 {
      margin-right: 8px;
    }
    .confirm-btn {
      min-width: 86px;
      margin-right: 8px;
    }
  }
}
</style>
