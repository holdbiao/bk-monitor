<!--
 * @Date: 2021-06-10 17:24:16
 * @LastEditTime: 2021-06-21 10:49:09
 * @Description:
-->
<template>
  <div>
    <PerformanceDialog
      :title="$t('主机筛选')"
      :value="value"
      :ok-text="$t('筛选')"
      :cancel-text="$t('清空')"
      :show-undo="false"
      @change="handleDialogValueChange"
      @cancel="handleReset"
      @confirm="handleFilterData">
      <div class="filter-panel" v-if="value">
        <div v-for="item in data" :key="item.id">
          <FilterPanelItem
            v-if="item.show"
            :class="{ 'mb10': lastItemId !== item.id }"
            v-model="item.value"
            :title="item.name"
            :type="item.type"
            :disabled="item.filterDisable"
            :options="item.options || []"
            :conditions="item.conditions || {}"
            :multiple="!!item.multiple"
            :allow-empt="!!item.allowEmpt"
            @close="handlePanelItemClose(item.id)">
          </FilterPanelItem>
        </div>
        <bk-button class="add-panel" text @click="handleMoreClick">
          {{ $t('添加其他条件') }}
        </bk-button>
      </div>
    </PerformanceDialog>
    <ConditionPanel
      v-model="showMoreCondition"
      :field-data="data"
      :loading="tableInstance.loading"
      @confirm="handleConditionConfirm">
    </ConditionPanel>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Model, Emit, Prop, Watch, Inject } from 'vue-property-decorator'
import PerformanceDialog from './performance-dialog.vue'
import FilterPanelItem from './filter-panel-item.vue'
import ConditionPanel from './condition-panel.vue'
import TableStore from '../table-store'
import { IFieldConfig, ISelectedValues } from '../performance-type'

@Component({
  name: 'filter-panel',
  components: {
    PerformanceDialog,
    FilterPanelItem,
    ConditionPanel
  }
})
export default class FilterPanel extends Vue {
  @Model('update-value', { type: Boolean }) private readonly value: boolean
  @Prop({ default: () => [] }) private readonly fieldData!: IFieldConfig[]
  @Inject('tableInstance') private readonly tableInstance: TableStore

  private data: IFieldConfig[] = []
  private showMoreCondition = false

  private get lastItemId() {
    const list = this.data.filter(item => item.show)
    return list?.[list.length - 1].id
  }
  created() {
    this.data = JSON.parse(JSON.stringify(this.fieldData))
    this.handleCheckedData()
  }

  @Watch('fieldData', { deep: true })
  private handleFieldDataChange(v) {
    this.data = JSON.parse(JSON.stringify(v))
    this.handleCheckedData()
  }

  @Emit('update-value')
  private handleDialogValueChange(v: boolean) {
    // 还原筛选条件
    if (!v) {
      this.data = JSON.parse(JSON.stringify(this.fieldData))
      this.handleCheckedData()
    }
    return v
  }

  @Emit('reset')
  private handleReset() {
    this.tableInstance.page = 1
    this.tableInstance.fieldData.forEach((item) => {
      item.value = Array.isArray(item.value) ? [] : ''
    })
  }

  /**
   * @description: 更新条件的显隐状态
   * @param {*}
   * @return {*}
   */
  private handleCheckedData() {
    const loadingFieldIds = ['status', 'cpu_load', 'cpu_usage',
      'disk_in_use', 'io_util', 'mem_usage', 'psc_mem_usage', 'display_name']
    this.data.forEach((item) => {
      if (this.tableInstance.loading) {
        item.show = !!item.filterChecked && !loadingFieldIds.includes(item.id)
      } else {
        // 增加show属性控制显隐，避免data引用发生改变而导致组件刷新
        item.show = !!item.filterChecked
      }
    })
  }

  private handleMoreClick() {
    this.showMoreCondition = true
  }

  private handleConditionConfirm(v: ISelectedValues) {
    const selected = v.selectedGroup.concat(v.unSelectedGroup)
    this.data.forEach((item) => {
      item.filterChecked = selected.includes(item.id)
    })
    this.handleCheckedData()
  }

  @Emit('close')
  private handlePanelItemClose(id: string) {
    const item = this.tableInstance.fieldData.find(item => item.id === id)
    if (item) {
      item.filterChecked = false
      Array.isArray(item.value) ? item.value = [] : item.value = ''
    }
    return item
  }

  @Emit('filter')
  private handleFilterData() {
    this.tableInstance.page = 1
    this.tableInstance.fieldData.forEach((item) => {
      const data = this.data.find(data => data.id === item.id)
      if (data) {
        item.value = data.value
        item.filterChecked = data.filterChecked
        // 非空值情况下默认展示数据列，空值就保持原有展示情况
        const notEmptyValue = Array.isArray(data.value) ? data.value.length > 0 : !!data.value
        // 集群模块字段对应的是 集群列 和 模块列
        if (item.id === 'cluster_module' && notEmptyValue) {
          this.tableInstance.fieldData
            .filter(item => ['bk_cluster', 'bk_inst_name'].includes(item.id))
            .forEach((item) => {
              item.checked = true
            })
        } else if (notEmptyValue) {
          item.checked = true
        }
      }
    })
    return this.data
  }
}
</script>
<style lang="scss" scoped>
.filter-panel {
  padding: 0 10px;
  .add-panel {
    font-size: 12px;
    margin-left: 12px;
  }
}
</style>
