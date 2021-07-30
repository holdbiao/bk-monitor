<template>
  <transition
    name="monitor-dialog"
    @after-enter="afterEnter"
    @after-leave="afterLeave">
    <div v-show="value"
         class="monitor-dialog-mask"
         :style="{ zIndex }"
         @click="handleMaskClick">
      <div ref="monitor-dialog"
           class="monitor-dialog"
           :class="{ 'full-screen': fullScreen }"
           :style="{ width: width + 'px' }">
        <i class="bk-icon icon-close monitor-dialog-close" @click="handleClose"></i>
        <div class="monitor-dialog-header" v-if="needHeader">
          <slot name="header">
            {{title}}
          </slot>
        </div>
        <div class="monitor-dialog-body">
          <slot></slot>
        </div>
        <div class="monitor-dialog-footer" v-if="needFooter">
          <slot name="footer">
            <bk-button v-show="showConfirmBtn" class="footer-btn" theme="primary" @click="handleClickConfirm"> {{ $t('确定') }} </bk-button>
            <bk-button theme="default" @click="handleClickCancel"> {{ $t('取消') }} </bk-button>
          </slot>
        </div>
      </div>
    </div>
  </transition>
</template>
<script lang="ts">
import { Component, Prop, Vue, Watch } from 'vue-property-decorator'

@Component
export default class MonitorDialog extends Vue {
  closed = false
  // 是否显示
  @Prop({
    type: Boolean,
    default: false
  })
  value: boolean

  // 标题
  @Prop({
    type: String,
    default() {
      return this.$t('监控平台')
    }
  })
  title: string

  // 宽度
  @Prop({
    type: [String, Number],
    default: 400
  })
  width: string | number

  // 是否插入到body下
  @Prop({
    type: Boolean,
    default: false
  })
  appendToBody: boolean

  // 是否点击mask关闭
  @Prop({
    type: Boolean,
    default: false
  })
  maskClose: boolean

  // 层级
  @Prop({
    type: [String, Number],
    default: 1000
  })
  zIndex: number

  // 是否需要footer
  @Prop({
    type: Boolean,
    default: true
  })
  needFooter: boolean

  // 关闭之前触发
  @Prop([Function])
  beforeClose: (args: any) => void

  // 是否全屏
  @Prop([Boolean])
  fullScreen: boolean

  // 是否需要展示header
  @Prop({
    type: Boolean,
    default: true
  })
  needHeader: boolean

  // 是否需要展示确定按钮
  @Prop({
    type: Boolean,
    default: true
  })
  showConfirmBtn: boolean

  @Watch('value')
  onValueChange(val: boolean): void {
    if (val) {
      this.closed = false
      this.appendToBody && document.body.appendChild(this.$el)
      this.$emit('on-open')
    } else {
      if (!this.closed) this.$emit('on-close')
    }
  }

  mounted() {
    this.value && this.appendToBody && document.body.appendChild(this.$el)
  }

  destroyed() {
    if (this.appendToBody && this.$el && this.$el.parentNode) {
      this.$el.parentNode.removeChild(this.$el)
    }
  }

  // 点击背景mask
  handleMaskClick(): void {
    if (!this.maskClose) return
    this.handleClose()
  }

  // 点击关闭按钮
  handleClose(): void {
    if (typeof this.beforeClose === 'function') {
      this.beforeClose(this.hideDialog)
    } else {
      this.hideDialog()
    }
  }

  // 点击确定
  handleClickConfirm(): void {
    this.$emit('on-confirm')
  }

  // 点击取消
  handleClickCancel(): void {
    this.handleClose()
    this.$emit('on-cancel')
  }

  // 关闭弹窗
  hideDialog(cancel?: Boolean): void {
    if (cancel !== false) {
      this.$emit('update:value', false)
      this.$emit('change', false)
      this.$emit('on-close')
      this.closed = true
    }
  }

  // 打开动画执行完毕
  afterEnter(): void {
    this.$emit('on-opened')
  }

  // 关闭动画执行完毕
  afterLeave(): void {
    this.$emit('on-closed')
  }
}
</script>
<style lang="scss" scoped>
    .monitor-dialog-mask {
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      top: 0;
      background-color: rgba(0,0,0,.6);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity .3s;
      .monitor-dialog {
        min-height: 200px;
        box-sizing: border-box;
        background-color: rgb(255, 255, 255);
        background-clip: padding-box;
        box-shadow: rgba(0, 0, 0, .15) 0px 4px 12px;
        border-width: 0px;
        border-radius: 2px;
        color: #63656e;
        padding: 20px 24px 0 24px;
        position: relative;
        display: flex;
        flex-direction: column;
        transition: opacity .3s;
        &.full-screen {
          position: fixed;
          left: 0;
          top: 0;
          bottom: 0;
          right: 0;

          /* stylelint-disable-next-line declaration-no-important */
          width: 0 !important;
          min-width: 100%;
          min-height: 100%;

          /* stylelint-disable-next-line declaration-no-important */
          height: 0 !important;
          z-index: 2001;
        }
        &-header {
          font-size: 20px;
        }
        &-body {
          flex: 1;
        }
        &-footer {
          height: 50px;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          border-top: 1px solid #dcdee5;
          margin: 0 -24px;
          padding-right: 24px;
          background-color: #fafbfd;
          .footer-btn {
            margin-left: auto;
            margin-right: 10px;
          }
        }
        &-close {
          position: absolute;
          right: 10px;
          top: 10px;
          height: 24px;
          width: 24px;
          font-size: 16px;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2000;
          &:hover {
            border-radius: 50%;
            background-color: #f0f1f5;
            cursor: pointer;
          }
        }
      }
    }
    .monitor-dialog-enter-active {
      animation: monitor-dialog-in .3s;
    }
    .monitor-dialog-leave-active {
      animation: monitor-dialog-out .3s;
    }

    @keyframes monitor-dialog-in {
      0% {
        transform: translate3d(0, -20px, 0);
        opacity: 0;
      }
      100% {
        transform: translate3d(0, 0, 0);
        opacity: 1;
      }
    }
    @keyframes monitor-dialog-out {
      0% {
        transform: translate3d(0, 0, 0);
        opacity: 1;
      }
      100% {
        transform: translate3d(0, -20px, 0);
        opacity: 0;
      }
    }
</style>
