<template>
  <div class="checkbox-group-wrap">
    <bk-checkbox
      :class="['list-item', { 'active': active === item.key }]"
      v-for="item in list"
      @change="(v, ov) => handleChange(v, ov, item)"
      :true-value="item.key"
      :false-value="''"
      :disabled="disabled && !localValue.includes(item.key)"
      :checked="isChecked(item.key)"
      :key="JSON.stringify(item)">
      {{item.title}}
    </bk-checkbox>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Model, Prop, Emit, Watch } from 'vue-property-decorator'
import { IGraphValueItem } from '../types'
/**
 * 图表多选组件
 */
@Component({
  name: 'checkbox-group'
})
export default class CheckboxGroup extends Vue {
  // value双向绑定
  @Model('valueChange', { type: Array }) private value: IGraphValueItem[]

  // 列表
  @Prop({ default: () => [], type: Array }) private readonly list: any

  // 选中
  @Prop({ default: '', type: String }) private readonly active: string

  @Prop({ default: false, type: Boolean }) private readonly disabled: boolean

  // 本地存储选中值
  private localValue: IGraphValueItem[] = []

  @Emit('valueChange')
  handleValueChange() {
    return this.localValue
  }

  @Watch('value', { immediate: true })
  valueChange(v: IGraphValueItem[]) {
    this.localValue = v
  }

  private handleChange(v, ov, item) {
    if (v) {
      this.localValue.push({
        id: v,
        name: item.title
      })
    } else {
      const index = this.localValue.findIndex(item => item.id === ov)
      this.localValue.splice(index, 1)
    }
    this.handleValueChange()
  }

  private isChecked(key) {
    return !!this.localValue.find(item => item.id === key)
  }
}

</script>

<style lang="scss" scoped>
.checkbox-group-wrap {
  .list-item {
    display: block;
    height: 28px;
    /deep/.bk-checkbox-text {
      margin-left: 15px;
      color: #63656e;
      font-size: 12px;
      &:hover {
        color: #3a84ff;
      }
    }
  }
  .active {
    /deep/.bk-checkbox-text {
      color: #3a84ff;
    }
  }
}
</style>
