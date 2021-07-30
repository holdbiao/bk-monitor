<template>
  <div
    class="label-wrapper"
    :class="orientation"
    @click="handleClick">
    <i
      class="icon-monitor"
      :class="`icon-${orientation}`" />
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Model } from 'vue-property-decorator'

export enum Screen {
  LANDSCAPE = 'landscape', // 横屏
  PORTRAIT = 'portrait' // 竖屏
}

@Component
export default class ScreenOrientation extends Vue {
  // 自定义v-model
  @Model('orientation-change', { type: String }) private readonly value!: string

  // 当前方向
  private orientation = ''

  created() {
    this.orientation = this.getRealOrientation()
    window.addEventListener('orientationchange', this.handleOrientationchange, false)
    this.$once('hook:beforeDestroy', () => {
      window.removeListener(this.handleOrientationchange)
    })
  }

  @Emit('click')
  @Emit('orientation-change')
  handleClick() {
    this.orientation = this.orientation === Screen.PORTRAIT ? Screen.LANDSCAPE : Screen.PORTRAIT
    let className = ''
    let rotate = 0
    const realOrientation = this.getRealOrientation()
    if (realOrientation !== this.orientation) {
      className = this.orientation === Screen.LANDSCAPE ? 'bk-mobile-landscape' : 'bk-mobile-portrait'
      rotate = this.orientation === Screen.LANDSCAPE ? 90 : -90
    } else {
      className = ''
      rotate = 0
    }

    this.setRootElementClass(className, rotate)
    return this.orientation
  }

  @Emit('change')
  @Emit('orientation-change')
  handleOrientationchange() {
    this.orientation = this.getRealOrientation()
    this.setRootElementClass('', 0)
    return this.orientation
  }

  setRootElementClass(className: string, rotate: number) {
    const htmlEle = this.$root.$el as HTMLElement
    htmlEle.className = className
    htmlEle.style.transform = rotate === 0 ? 'unset' : `rotate(${rotate}deg)`
  }

  getRealOrientation() {
    return Math.abs(window.orientation as number) === 90 ? Screen.LANDSCAPE : Screen.PORTRAIT
  }
}
</script>
<style lang="scss" scoped>
    .label-wrapper {
      z-index: 999;
      position: fixed;
      right: 1.5rem;
      bottom: 1.5rem;
      width: 3.5rem;
      height: 3.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0px 3px 6px 0px rgba(79,85,96,.3);
      i {
        font-size: 1.6rem;
        color: #3a84ff;
      }
    }
</style>
