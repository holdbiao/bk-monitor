<!--
 * @Author:
 * @Date: 2021-05-25 19:15:01
 * @LastEditTime: 2021-06-18 10:52:49
 * @LastEditors:
 * @Description:
-->
<template>
  <bk-dialog
    :value="value"
    :title="$t('添加更多条件')"
    render-directive="if"
    header-position="left"
    width="460"
    @value-change="handleValueChange"
    @confirm="handleConfirm">
    <div class="condition-panel"
         v-for="item in groupList"
         :key="item.id">
      <h2 class="condition-panel-title">{{ item.name }}</h2>
      <bk-checkbox-group class="condition-panel-content" v-model="selectedValues[item.id]">
        <bk-checkbox
          class="content-item"
          v-for="data in item.data"
          :key="data.id"
          :value="data.id"
          :disabled="data.filterDisable || (loading && loadingFieldIds.includes(data.id))">
          {{ data.name }}
        </bk-checkbox>
      </bk-checkbox-group>
    </div>
  </bk-dialog>
</template>
<script lang="ts">
import { Vue, Prop, Model, Emit, Watch, Component } from 'vue-property-decorator'
import { IFieldConfig, ISelectedValues } from '../performance-type'

@Component({ name: 'condition-panel' })
export default class ConditionPanel extends Vue {
  @Model('value-change') private readonly value: boolean

  @Prop({ default: () => [] }) private readonly fieldData!: IFieldConfig[]
  @Prop({ default: false, type: Boolean }) private readonly loading!: boolean

  private data = []
  private selectedValues: ISelectedValues = {
    selectedGroup: [],
    unSelectedGroup: []
  }
  private loadingFieldIds = ['status', 'cpu_load', 'cpu_usage',
    'disk_in_use', 'io_util', 'mem_usage', 'psc_mem_usage', 'display_name']

  private get groupList() {
    return [
      {
        id: 'selectedGroup',
        name: window.i18n.t('已选条件'),
        data: this.checkedData
      },
      {
        id: 'unSelectedGroup',
        name: window.i18n.t('可选条件'),
        data: this.unCheckedData
      }
    ]
  }

  // 获取当前勾选过的字段
  private get checkedData() {
    return this.data.filter(item => !!item.filterChecked)
  }

  private get unCheckedData() {
    return this.data.filter(item => !item.filterChecked)
  }

  created() {
    this.data = JSON.parse(JSON.stringify(this.fieldData))
  }

  @Watch('fieldData', { deep: true })
  private handleFieldDataChange(v) {
    this.data = JSON.parse(JSON.stringify(v))
  }

  @Watch('value')
  private handleChange() {
    this.selectedValues.selectedGroup = this.checkedData.map(item => item.id)
    this.selectedValues.unSelectedGroup = []
  }

  @Emit('value-change')
  private handleValueChange(v) {
    return v
  }

  @Emit('confirm')
  private handleConfirm() {
    return this.selectedValues
  }
}
</script>
<style lang="scss" scoped>
.condition-panel {
  &-title {
    font-size: 12px;
    font-weight: 700;
  }
  &-content {
    display: flex;
    flex-wrap: wrap;
    .content-item {
      flex-basis: 33%;
      margin-bottom: 10px;
      /deep/ .bk-checkbox-text {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        width: 110px;
      }
    }
  }
}
</style>
