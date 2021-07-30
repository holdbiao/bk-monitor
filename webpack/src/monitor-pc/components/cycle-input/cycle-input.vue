<template>
  <div class="cycle-input">
    <div
      :style="`width: ${getWidth}; min-width: ${minWidth}px;`"
      class="set-input-wrapper">
      <div
        class="set-input"
        ref="inputRef"
        type="number"
        :data-placeholder="placeholder"
        v-text="displayName"
        :contenteditable="true"
        :placeholder="placeholder"
        @click.stop="inputFocus"
        @input="handleInput"></div>
      <span class="input-unit">min</span>
    </div>
    <div v-show="false">
      <ul class="cycle-list" ref="listRef" :style="`width: ${width}px;`">
        <li
          v-for="(item, index) in list"
          :key="index"
          :class="['cycle-item', { 'cycle-item-active': value === item.id }]"
          @click="handleSelect(item)">
          {{item.name + 'min'}}
        </li>
      </ul>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref, Watch } from 'vue-property-decorator'
import MonitorVue from '../../types/index'

@Component({
  name: 'cycle-input'
})
export default class CycleInput extends Vue<MonitorVue> {
  @Prop({ default: 60, type: Number }) readonly maxVal: number
  @Prop({ default: 60, type: Number }) readonly value: number
  @Prop({ default: 180, type: [Number, String] }) readonly width: number | string
  @Prop({ default: 80, type: Number }) readonly minWidth: number
  @Prop({ default: '', type: String }) readonly placeholder: String
  @Prop({ default: () => [], type: Array }) readonly list: { name: string, id: number }[]

  displayName = ''
  popoverInstance: any = null

  get getWidth(): string {
    if (this.width === 'auto') return this.width
    if (typeof this.width === 'number') return `${this.width}px`
    return `${this.width}`
  }

  @Ref('listRef') readonly listRefEl: HTMLBaseElement
  @Ref('inputRef') readonly inputRefEl: HTMLBaseElement

  @Watch('value', { immediate: true })
  valueChange(val) {
    const res = this.list.find(item => item.id === val)
    this.displayName = res ? res.name : (val ? String(val / 60) : '')
  }

  inputFocus() {
    this.initPopover()
    this.setCaretPosition(this.inputRefEl)
  }

  handleSelect(item) {
    this.displayName = item.name
    this.hidePop()
    if (item.id === this.value) return
    this.$emit('input', item.id)
  }

  hidePop() {
    this.popoverInstance?.hide(0)
    this.popoverInstance?.destroy()
    this.popoverInstance = null
  }

  async handleInput(e) {
    let val = e.target.innerText
    val = val.replace(/\D/g, '')
    if (val && +val > 60) {
      this.displayName = '60'
    } else {
      this.displayName = val
    }
    this.inputRefEl.innerHTML = this.displayName
    await this.$nextTick()
    const newVal = +this.displayName * 60
    this.setCaretPosition(this.inputRefEl)
    if (this.value === newVal) return
    this.$emit('input', +this.displayName * 60)
  }

  async initPopover() {
    if (this.popoverInstance) return
    const width = this.inputRefEl.offsetWidth
    this.popoverInstance = this.$bkPopover(this.inputRefEl, {
      content: this.listRefEl,
      trigger: 'manual',
      theme: 'light cycle-list-wrapper',
      interactive: true,
      arrow: false,
      placement: 'bottom-start',
      maxWidth: 300,
      width,
      distance: 12,
      followCursor: false,
      flip: false,
      animation: 'slide-toggle',
      onHidden: () => {
        this.popoverInstance?.destroy()
        this.popoverInstance = null
      }
    })
    this.popoverInstance?.show(100)
  }

  setCaretPosition(textDom) {
    let range
    try {
      if (window.getSelection) {
        range = window.getSelection() // 创建range
        range.selectAllChildren(textDom) // range 选择obj下所有子内容
        range.collapseToEnd() // 光标移至最后
      }
    } catch (e) {
      console.log(e)
    }
  }
}
</script>
<style lang="scss" scoped>
.cycle-input {
  .set-input-wrapper {
    position: relative;
    // min-width: 80px;
    .set-input {
      box-sizing: border-box;
      display: flex;
      align-items: center;
      min-height: 32px;
      line-height: 30px;
      border: 1px solid #c4c6cc;
      border-radius: 2px;
      padding: 0 12px;
      text-align: left;
      &:empty:before {
        content: attr(placeholder);
        color: #c4c6cc;
      }
      &:focus {
        content: none;
      }
      &:hover {
        cursor: pointer;
      }
      &:focus {
        border-color: #3a84ff;
        box-shadow: 0 0 4px rgba(58,132,255,.4);
      }
    }
    .input-unit {
      display: flex;
      align-items: center;
      justify-content: center;
      position: absolute;
      top: 0;
      right: 12px;
      height: 100%;
      color: #c4c6cc;
    }
  }

}
</style>

<style lang="scss">
.cycle-list-wrapper-theme {
  padding: 0;
  width: 100%;
  box-shadow: 0 0 6px rgba(204, 204, 204, .3);
  border-radius: 0;
  .cycle-list {
    display: flex;
    flex-direction: column;
    padding: 6px 0;
    min-width: 98px;
    width: 100%;
    box-sizing: border-box;
    max-height: 210px;
    overflow: auto;
    border: 1px solid #dcdee5;
    border-radius: 2px;
    background-color: #fff;
    .cycle-item {
      flex: 0 0 32px;
      display: flex;
      align-items: center;
      padding: 0 15px;
      &:hover {
        background-color: #e1ecff;
        color: #3a84ff;
        cursor: pointer;
      }
    }
    .cycle-item-active {
      background-color: #e1ecff;
      color: #3a84ff;
    }
  }
}
</style>
