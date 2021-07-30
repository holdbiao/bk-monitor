<!--
 * @Author:
 * @Date: 2021-06-18 10:36:27
 * @LastEditTime: 2021-06-21 11:25:51
 * @LastEditors:
 * @Description:
-->
<template>
  <div :class="['item', { 'is-hover': isHoverStatus }]"
       @mouseenter="handleMouseEnter"
       @mouseleave="handleMouseLeave">
    <div class="item-title">
      <span>{{ title }}</span>
      <i class="icon-monitor icon-mc-close"
         @click="handleClose"
         v-if="isHoverStatus">
      </i>
    </div>
    <div class="item-content">
      <slot>
        <bk-input
          v-if="['textarea', 'text'].includes(type)"
          :type="type"
          :value="value"
          :rows="rows"
          @input="handleUpdateValue">
        </bk-input>
        <bk-checkbox-group
          class="item-content-checkbox"
          v-else-if="type === 'checkbox'"
          :value="value"
          @change="handleUpdateValue">
          <bk-checkbox
            v-for="item in options"
            :key="item.id"
            :value="item.id">
            {{ item.name }}
          </bk-checkbox>
        </bk-checkbox-group>
        <bk-select
          v-else-if="type === 'select'"
          ref="select"
          :value="value"
          :popover-options="{ 'boundary': 'window' }"
          :multiple="multiple"
          searchable
          :remote-method="handleSelectSearch"
          @change="handleSelectChange">
          <bk-option
            v-for="item in sortOptions"
            :key="item.id"
            :id="item.id"
            :name="item.name">
            {{ item.name }}
          </bk-option>
        </bk-select>
        <bk-cascade
          v-else-if="type === 'cascade'"
          :value="value"
          :list="cascadeOptions"
          clearable
          :popover-options="{ 'boundary': 'window' }"
          check-any-level
          ref="cascade"
          :multiple="multiple"
          filterable
          @toggle="handleCascadeToggle"
          @search="handleCascadeSearch"
          @change="handleCascadeChange">
        </bk-cascade>
        <div v-else-if="type === 'condition'">
          <div v-for="(data, index) in conditionsData"
               :key="index"
               :class="['item-content-condition', { mb10: index < (conditionsData.length - 1) }]">
            <div class="condition-left">
              <!-- 条件 -->
              <bk-select
                class="condition-select"
                :popover-options="{ 'boundary': 'window' }"
                v-model="data.condition"
                @change="handleConditionChange">
                <bk-option
                  v-for="item in conditions"
                  :key="item.id"
                  :id="item.id"
                  :name="item.name">
                  {{ item.name }}
                </bk-option>
              </bk-select>
              <!-- 值 -->
              <bk-input
                class="condition-input"
                v-model="data.value"
                type="number"
                @change="handleConditionChange">
              </bk-input>
            </div>
            <!-- 增/减 -->
            <div class="condition-right">
              <i class="icon-monitor icon-jia ml5"
                 @click="handleAddCondition(index)">
              </i>
              <i :class="['icon-monitor icon-jian ml5', { 'disabled': iconDisabled }]"
                 @click="handleDeleteCondition(index)">
              </i>
            </div>
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Prop, Emit, Model, Component, Watch, Ref } from 'vue-property-decorator'
import { InputType, IOption, FieldValue, IConditionValue } from '../performance-type'
import { sort } from '../../../../monitor-common/utils/utils.js'

@Component({ name: 'filter-panel-item' })
export default class PanelItem extends Vue {
  @Ref('cascade') readonly cascadeRef: any
  @Ref('select') readonly selectRef: any
  @Model('update-value', { type: [String, Number, Array] }) private readonly value: FieldValue
  @Prop({ default: 'title' }) private readonly title: string
  @Prop({ default: 'select', type: String }) private readonly type: InputType
  @Prop({ default: false }) private readonly disabled: boolean
  @Prop({ default: false }) private readonly multiple: boolean
  @Prop({ default: false }) private readonly allowEmpt: boolean
  @Prop({ default: () => [], type: Array }) private readonly options: IOption[]
  @Prop({
    default: () => ({
      list: [],
      active: ''
    })
  }) private readonly conditions: IOption[]

  private hover = false
  // 同一字段支持多个条件（eg：CPU使用率 > 80 且 CPU使用率 < 90）
  private conditionsData: IConditionValue[] = [
    {
      condition: undefined,
      value: undefined
    }
  ]

  // textarea最小高度
  private minRows = 3
  // textarea最大高度
  private maxRows = 6

  private cascadeKeyWord = ''

  private get cascadeOptions() {
    const temp = [...this.options]
    if (this.cascadeKeyWord && this.cascadeRef?.searchList?.length) {
      temp.unshift({ id: '__all__', name: this.$t('- 全部 -'), children: [] })
    }
    return temp
  }

  // 排序options
  private get sortOptions() {
    if (Array.isArray(this.options)) {
      this.options.forEach((item) => {
        if (Array.isArray(item.children)) {
          item.children = sort(item.children, 'name')
        }
      })
      let temp = sort(this.options, 'name')
      // 处理空选项
      if (this.allowEmpt) {
        temp = [temp.find(set => set.id === '__empt__'), ...temp.filter(set => set.id !== '__empt__')]
          .filter(item => !!item)
      }
      // 添加搜索全选选项
      this.multiple && temp.length && temp.unshift({ id: '__all__', name: this.$t('- 全部 -') })
      return temp
    }
    return this.options
  }

  // 当前textarea高度
  private get rows() {
    if (this.type === 'textarea') {
      const valueLength = (`${this.value}`).split('\n').length
      return valueLength > this.minRows
        ? Math.min(valueLength, this.maxRows)
        : this.minRows
    }
    return 1
  }

  private get isHoverStatus() {
    return this.hover && !this.disabled
  }

  private get iconDisabled() {
    return this.conditionsData.length === 1
  }

  @Watch('value', { immediate: true })
  private handleValueChange(v) {
    if (this.type === 'condition') {
      v.length === 0
        ? this.conditionsData = [
          {
            condition: undefined,
            value: undefined
          }
        ]
        : this.conditionsData = v
    } else if (this.type === 'cascade') {
      this.$nextTick(() => {
        this?.cascadeRef?.updateSelected()
      })
    }
  }

  // @Watch('options', { deep: true, immediate: true })
  // private optionsChange() {
  //   this.localOptions = deepClone(this.options)
  // }

  @Emit('close')
  @Emit('update-value')
  private handleClose() {
    return Array.isArray(this.value) ? [] : ''
  }

  private handleMouseEnter() {
    this.hover = true
  }

  private handleMouseLeave() {
    this.hover = false
  }

  @Emit('update-value')
  private handleUpdateValue(v) {
    return v
  }

  // 添加条件
  private handleAddCondition(index: number) {
    this.conditionsData.splice(index + 1, 0, {
      condition: undefined,
      value: undefined
    })
  }

  // 删除条件
  private handleDeleteCondition(index: number) {
    if (this.iconDisabled) return
    this.conditionsData.splice(index, 1)
  }

  // 条件值变更事件
  @Emit('update-value')
  private handleConditionChange() {
    return this.conditionsData
  }

  // select搜索筛选
  private handleSelectSearch(keyWord) {
    (this?.selectRef?.options || []).forEach((option) => {
      option.unmatched = !option.name.includes(keyWord)
      if (option.id === '__all__') option.unmatched = false
    })
  }
  /**
   * @description: 下拉选中全部操作
   * @param {*} list
   * @return {*}
   */
  private handleSelectChange(list) {
    if (list.includes('__all__')) {
      list = (this?.selectRef?.options || []).filter(item => item.id !== '__all__' && !item.unmatched)
        .map(item => item.id)
      this.$nextTick(() => {
        this.selectRef.setSelectedOptions()
        this.selectRef.close()
      })
    }
    this.handleUpdateValue(list)
  }
  /**
   * @description: 级联选择器搜索
   * @param {*} keyWord 搜索关键词
   * @return {*}
   */
  private async handleCascadeSearch(keyWord: string) {
    this.cascadeKeyWord = keyWord
    await this.$nextTick()
    if (keyWord) this.cascadeRef.filterableStatus = true
    const { searchList } = this.cascadeRef
    if (searchList.length) {
      searchList.unshift({ id: ['__all__'], disabled: false, isSelected: false, name: this.$t('- 全部 -') })
    }
    this.cascadeRef.searchList = searchList
  }
  /**
   * @description: 级联值更新
   * @param {*} val 更新值
   * @return {*}
   */
  private handleCascadeChange(val: any[]) {
    const allIndex = val.findIndex(item => item.includes('__all__'))
    if (allIndex >= 0) {
      val = []
      for (const item of this.cascadeRef.searchList) {
        if (!item.id.includes('__all__')) {
          val.push(item.id)
        }
      }
      this.cascadeRef.searchContent = ''
      this.cascadeRef.filterableStatus = false
      this.cascadeKeyWord = ''
    }
    this.handleUpdateValue(val)
  }
  private handleCascadeToggle(val: boolean) {
    if (!val) this.cascadeKeyWord = ''
  }
}
</script>
<style lang="scss" scoped>
.item {
  padding: 0 8px 8px 12px;
  &.is-hover {
    background: #f5f6fa;
    border-radius: 2px;
  }
  &-title {
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    span {
      line-height: 20px;
    }
    i {
      font-size: 16px;
      cursor: pointer;
      color: #ff5656;
      margin-right: -4px;
      font-weight: bold;
    }
  }
  &-content {
    margin-top: 6px;
    /deep/ .bk-select {
      background: #fff;
    }
    /deep/ .bk-cascade {
      background: #fff;
    }
    &-checkbox {
      display: flex;
      justify-content: space-between;
    }
    &-condition {
      display: flex;
      justify-content: space-between;
      .condition-left {
        display: flex;
        justify-content: space-between;
        flex: 1;
        .condition-select {
          flex: 1;
          margin-right: 8px;
        }
        .condition-input {
          flex: 1;
        }
      }
      .condition-right {
        display: flex;
        flex-basis: 50px;
        align-items: center;
        font-size: 20px;
        color: #979ba5;
        i {
          cursor: pointer;
          &.disabled {
            cursor: not-allowed;
            color: #c4c6cc;
          }
        }
      }
    }
  }
}
</style>
