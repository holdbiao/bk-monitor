<template>
    <div
        ref="dragRef"
        class="drag-label"
        @click="e => $emit('click', e)"
        @mousedown="handleMouseDown"
        @touchstart="handleMouseDown"
        @mousemove="handleMouseMove"
        @touchmove.prevent="handleMouseMove"
        @mouseup="handleMouseUp"
        @touchend="handleMouseUp">
        <slot>
            <i class="icon-monitor icon-menu-event" />
        </slot>
        <span
            v-if="alarmNum > 0"
            class="alarm-num">
            {{ alarmNum > 99 ? 99 : alarmNum }}
        </span>
    </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref } from 'vue-property-decorator'
@Component
export default class DragLabel extends Vue {
  // 告警数量
  @Prop({ default: 0 }) readonly alarmNum!: number

  @Ref() readonly dragRef: HTMLElement

  isMoving = false
  position: { x: number; y: number } = { x: 0, y: 0 }
  nx = 0
  ny = 0
  dx = 0
  dy = 0
  xPum = 0
  yPum = 0

  beforeDestroy() {
    this.isMoving = false
  }

  // 拖拽开始触发
  handleMouseDown(event) {
    this.isMoving = true
    let touch
    if (event.touches) {
      const [touchs] = event.touches
      touch = touchs
    } else {
      touch = event
    }
    this.position.x = touch.clientX
    this.position.y = touch.clientY
    this.dx = this.dragRef.offsetLeft
    this.dy = this.dragRef.offsetTop
  }

  // 移动时触发
  handleMouseMove(event) {
    if (this.isMoving) {
      let touch
      if (event.touches) {
        const [touchs] = event.touches
        touch = touchs
      } else {
        touch = event
      }
      this.nx = touch.clientX - this.position.x
      this.ny = touch.clientY - this.position.y
      this.xPum = this.dx + this.nx
      this.yPum = this.dy + this.ny
      // 添加限制：只允许在屏幕内拖动
      const maxWidth = window.innerWidth - 48
      const maxHeight = window.innerHeight - 48
      if (this.xPum < 0) { // 屏幕x限制
        this.xPum = 0
      } else if (this.xPum > maxWidth) {
        this.xPum = maxWidth
      }
      if (this.yPum < 0) { // 屏幕y限制
        this.yPum = 0
      } else if (this.yPum > maxHeight) {
        this.yPum = maxHeight
      }
      this.dragRef.style.left = `${this.xPum}px`
      this.dragRef.style.top = `${this.yPum}px`
      // 阻止页面的滑动默认事件
      document.addEventListener('touchmove', () => {
        event.stopPropagation()// jq 阻止冒泡事件
      }, false)
    }
  }

  // 拖拽释放时触发
  handleMouseUp() {
    this.isMoving = false
  }
}
</script>
<style lang="scss" scoped>
    .drag-label {
        z-index: 9999;
        position: fixed;
        bottom: 92px;
        right: 24px;
        display: flex;
        width: 48px;
        height: 48px;
        opacity: 0.8;
        background: #313238;
        border-radius: 24px;
        box-shadow: 0px 3px 6px 0px rgba(79,85,96,0.3);
        align-items: center;
        justify-content: center;
        color: #C4C6CC;
        font-size: 22px;
        .alarm-num {
            position: absolute;
            right: 0px;
            top: 0px;
            width: 16px;
            height: 16px;
            padding: 2px;
            background-color: #EA3636;
            color: white;
            border-radius: 50%;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    }
</style>
