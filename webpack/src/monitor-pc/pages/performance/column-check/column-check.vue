<template>
  <div class="column-check-wrapper">
    <bk-checkbox
      :indeterminate="value === 1"
      :value="value === 2"
      :class="{
        'all-checked': currentType === 'all',
        'indeterminate': value === 1 && currentType === 'all'
      }"
      :disabled="disabled"
      @change="handleChangeAll">
    </bk-checkbox>
    <bk-popover
      placement="bottom-start"
      theme="column-check"
      :arrow="false"
      trigger="click"
      ref="popover"
      offset="-10, 0"
      :distance="0"
      :on-hide="() => showList = false"
      :on-show="() => showList = true">
      <i :class="['icon-monitor', showList ? 'icon-arrow-up' : 'icon-arrow-down']"></i>
      <template #content>
        <ul class="dropdown-list">
          <li
            :class="['list-item', { 'list-item-active': currentType === item.id }]"
            v-for="(item, index) in list"
            :key="index"
            @click="handleSelect(item.id)">
            {{item.name}}
          </li>
        </ul>
      </template>
    </bk-popover>
  </div>
</template>

<script lang='ts'>
import { Vue, Component, Prop, Ref, Emit, Watch } from 'vue-property-decorator'
import { bkPopover } from 'bk-magic-vue'

@Component({
  name: 'column-check'
})

export default class StrategySetTarget extends Vue {
  @Ref('popover') readonly popover!: bkPopover

  @Prop({
    default: []
  })
  list: {id: string, name: string }[]

  @Prop({
    default: 0,
    validator: val => [0, 1, 2].includes(val)
  })
  value: number

  @Prop({ default: 'current' }) readonly defaultType: 'current' | 'all'
  @Prop({ default: false, type: Boolean }) disabled: boolean

  checkValue = false
  currentType = 'current'
  showList = false

  created() {
    this.currentType = this.defaultType
  }

  @Watch('defaultType')
  handleTypeChange() {
    this.currentType = this.defaultType
  }

  @Emit('change')
  emitChange(value: number, type: string): {value: number, type: string} {
    return {
	  value,
	  type
    }
  }

  // 选择全选方式
  handleSelect(type: string): void {
    this.currentType = type
    this.checkValue = true
    this.popover.instance.hide()
    this.emitChange(this.checkValue ? 2 : 0, this.currentType)
  }

  // 全选操作
  handleChangeAll(value: boolean): void {
    this.checkValue = value
    this.emitChange(this.checkValue ? 2 : 0, value ? this.currentType : 'current')
  }
}
</script>

<style lang="scss">
.column-check-theme {
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: all;
  .tippy-backdrop {
    background: none;
  }
  .dropdown-list {
    padding: 5px 0;
    border-radius: 4px;
    font-size: 14px;
    background-color: #fff;
    box-shadow: 0px 3px 6px 1px rgba(0, 0, 0, .1);
    overflow: hidden;
    .list-item {
      height: 32px;
      line-height: 32px;
      padding: 0 16px;
      color: #63656e;
      cursor: pointer;
      pointer-events: all;
    }
    .list-item-active {
      color: #3a84ff;
      background-color: #eaf3ff;
    }
  }
}
</style>
<style lang="scss" scoped>
.column-check-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  .all-checked {
    /deep/ .bk-checkbox {
      background-color: #fff;
      &::after {
        border-color: #3a84ff;
      }
    }
  }
  .indeterminate {
    /deep/ .bk-checkbox {
      &::after {
        background: #3a84ff;
      }
    }
  }
  /deep/ .bk-tooltip {
    position: absolute;
    top: 1px;
    right: -20px;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 16px;
    height: 16px;
    .bk-tooltip-ref {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      height: 100%;
      .icon-monitor {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 16px;
        height: 16px;
        font-size: 20px;
        cursor: pointer;
      }
    }
  }
}
</style>
