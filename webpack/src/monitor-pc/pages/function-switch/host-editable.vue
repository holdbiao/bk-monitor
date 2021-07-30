<template>
  <div class="host-editable-wrapper">
    <div @dblclick="dblclickHost" class="text" ref="text">{{value || '--'}}</div>
    <div
      class="input"
      v-show="editable"
      ref="input"
      :contenteditable="editable"
      @blur="handleBlur"
      @keydown.enter="handleEnter">
      {{value}}
    </div>
  </div>

</template>

<script lang='ts'>
import { Vue, Component, Prop, Ref } from 'vue-property-decorator'

@Component({
  name: 'host-editable'
})
export default class HostEditable extends Vue {
  @Ref('input') readonly inputRef
  @Ref('text') readonly textRef
  // host
  @Prop({ default: false, required: true }) readonly value: string
  // 编辑状态
  editable = false

  // 失去焦点后往外更新值
  handleBlur(evt) {
    this.editable = false
    const text = evt.target.innerText
    this.value !== text && this.$emit('input', text)
  }

  // 双击后可编辑状态
  dblclickHost() {
    this.editable = true
    this.$nextTick(() => {
      this.inputRef.focus()
      this.inputRef.innerText = ''
      this.inputRef.innerText = this.value
      const el = this.inputRef
      // 设置光标位置至末尾
      if (typeof window.getSelection !== 'undefined' && typeof document.createRange !== 'undefined') {
        const range = document.createRange()
        range.selectNodeContents(el)
        range.collapse(false)
        const sel = window.getSelection()
        sel.removeAllRanges()
        sel.addRange(range)
      }
    })
  }

  // 回车
  handleEnter() {
    this.inputRef.blur()
  }
}
</script>

<style lang="scss" scoped>
  @import "../../static/css/common.scss";

  .host-editable-wrapper {
    position: relative;
    height: 26px;
    cursor: pointer;
    .text {
      position: relative;
      padding: 0 20px 0 0;
      line-height: 26px;

      @include ellipsis;
    }
    &:hover {
      background-color: #f0f1f5;
    }
    .input {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 60px;
      border: 1px solid $slightFontColor;
      border-radius: 2px;
      overflow-y: scroll;
      background-color: #fff;
      z-index: 1;
    }
  }
</style>
