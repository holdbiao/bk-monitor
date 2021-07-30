<template>
  <span class="group-select-wrap" @click="handleClick">
    <span class="btn-content">
      <slot></slot>
    </span>
    <bk-select
      ext-popover-cls="dropdown-content"
      class="select-dropdown"
      ref="selectDropdown"
      v-model="localValue"
      :popover-min-width="270"
      @toggle="boo => !boo && (showInput = false)"
      @change="handleSelectChange">
      <bk-option
        v-for="(option, index) in localList"
        :key="index"
        :id="option.id"
        :name="option.name">
      </bk-option>
      <div slot="extension" style="cursor: pointer;">
        <div v-show="showInput" class="add-input-wrap">
          <bk-input class="input" size="small" v-model="localInputValue" @keydown="handleKeyupEnter"></bk-input>
          <bk-button class="btn" :text="true" size="small" @click="handleAddOption">{{$t('确定')}}</bk-button>
          <bk-button class="btn" :text="true" size="small" @click="showInput = false">{{$t('取消')}}</bk-button>
        </div>
        <div v-show="!showInput" @click="handleShowInput">
          <i class="bk-icon icon-plus-circle"></i><span style="margin-left: 4px">{{$t('新增分组')}}</span>
        </div>
      </div>
    </bk-select>
  </span>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref, Emit, Model, Watch } from 'vue-property-decorator'
import { deepClone } from '../../../monitor-common/utils/utils'

@Component({ name: 'group-select' })
export default class GroupSelect extends Vue {
  @Prop({ default: () => [], type: Array }) readonly list: any
  @Prop({ default: false, type: Boolean }) readonly disabled: boolean
  @Model('valueChange') readonly value: string | number

  @Ref('selectDropdown') readonly selectDropdownRef: any

  private showInput = false
  private localValue: string | number = ''
  private localList: any = []
  private localInputValue = ''

  @Watch('value', { immediate: true })
  handleValueChange(v) {
    this.localValue = v
  }

  @Watch('list', { immediate: true, deep: true })
  handleListChange(list) {
    this.localList = list
  }

  @Emit('change')
  @Emit('valueChange')
  emitValueChange() {
    return this.localValue
  }

  @Emit('listChange')
  emitListChange() {
    return deepClone(this.localList)
  }

  private handleClick() {
    if (this.disabled) return
    this.selectDropdownRef && this.selectDropdownRef.show()
  }

  private handleSelectChange() {
    this.emitValueChange()
  }

  private handleShowInput() {
    this.showInput = true
  }

  private handleAddOption() {
    if (!this.localInputValue) {
      this.showInput = false
      return
    }
    this.localList.push({
      id: this.localInputValue,
      name: this.localInputValue
    })
    this.emitListChange()
    this.localInputValue = ''
    this.showInput = false
  }

  private handleKeyupEnter(...args) {
    const e = args[1]
    const { keyCode } = e
    if (keyCode === 13) this.handleAddOption()
  }
}
</script>

<style lang="scss" scoped>
.group-select-wrap {
  position: relative;
  .btn-content {
    z-index: 1;
  }
  .select-dropdown {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    top: 0;
    opacity: 0;
    overflow: hidden;
    z-index: -1;
  }
}
</style>

<style lang="scss">
.dropdown-content {
  .bk-option-content,
  .bk-select-extension {
    padding: 0 10px;
  }
  .add-input-wrap {
    display: flex;
    align-items: center;
    .input {
      flex: 1;
    }
    .btn {
      flex-shrink: 0;
      padding: 0;
      margin: 0 8px;
      &:last-child {
        margin: 0;
      }
    }
  }
}
</style>
