<template>
  <div>
    <div class="performance-tool">
      <!-- 左侧操作按钮 -->
      <div class="performance-tool-left">
        <bk-button
          class="tool-btn"
          :disabled="selectionsCount < 2"
          @click="handleContrastIndex">
          {{ $t('指标对比') }}
        </bk-button>
        <bk-button
          class="tool-btn"
          :disabled="!selectionsCount"
          @click="handleCopyIp">
          {{ $t('复制IP') }}
        </bk-button>
      </div>
      <!-- 右侧筛选条件 -->
      <div class="performance-tool-right">
        <bk-input
          v-model="keyWord"
          class="tool-search"
          :placeholder="$t('输入关键字，模糊搜索')"
          clearable
          right-icon="bk-icon icon-search"
          @change="handleSearch">
        </bk-input>
        <span :class="['tool-icon', { 'is-filter': isFilter }]"
              @click="handleShowPanel">
          <i class="icon-monitor icon-filter"></i>
        </span>
        <bk-popover
          placement="bottom"
          width="515"
          theme="light performance-dialog"
          trigger="click"
          :offset="200">
          <span class="tool-icon">
            <i class="bk-icon icon-cog"></i>
          </span>
          <div slot="content" class="tool-popover">
            <div class="tool-popover-title">
              {{ $t('字段显示设置') }}
            </div>
            <ul class="tool-popover-content">
              <li v-for="item in fieldSettingData"
                  :key="item.id"
                  class="tool-popover-content-item">
                <bk-checkbox
                  :value="item.checked"
                  @change="handleCheckColChange(item)"
                  :disabled="item.disable">
                  {{ item.name }}
                </bk-checkbox>
              </li>
            </ul>
          </div>
        </bk-popover>
        <FilterPanel
          v-model="showFilterPanel"
          :field-data="filterPanelData"
          @filter="handleFilter"
          @reset="handleReset">
        </FilterPanel>
      </div>
    </div>
    <FilterTag @filter-change="handleFilterChange"></FilterTag>
    <MetricContrastDialog v-model="visiable" :select-ips="selections"></MetricContrastDialog>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Inject } from 'vue-property-decorator'
import PerformanceModule from '../../../store/modules/performance'
import MetricContrastDialog from '../metric-contrast-dialog/metric-contrast-dialog.vue'
import FilterPanel from './filter-panel.vue'
import { copyText, typeTools, Debounce } from '../../../../monitor-common/utils/utils.js'
import TableStore from '../table-store'
import MonitorVue from '../../../types/index'
import { IFieldConfig, CheckType, ITableRow } from '../performance-type'
import FilterTag from './filter-tag.vue'

@Component({
  name: 'performance-tool',
  components: {
    MetricContrastDialog,
    FilterPanel,
    FilterTag
  }
})
export default class PerformanceTool extends Vue<MonitorVue> {
  @Prop({ default: 'current', type: String }) private readonly checkType: CheckType
  @Prop({ default: () => [], type: Array }) private readonly selectionData: ITableRow[]
  @Prop({ default: () => [], type: Array }) private readonly excludeDataIds: string[]
  @Prop({ default: 0 }) private readonly selectionsCount: number
  @Inject('tableInstance') private readonly tableInstance: TableStore

  // 采集下发按钮加载状态
  private collectLoading = false
  // 指标对比
  private visiable = false
  private storageKey = `${this.$store.getters.userName}-${this.$store.getters.bizId}`
  private showFilterPanel = false
  // 搜索关键字
  private keyWord = ''
  private selections: Readonly<Array<ITableRow>> = []

  // 可用于筛选的字段信息
  private get filterPanelData() {
    return this.fieldData.filter(item => Object.prototype.hasOwnProperty.call(item, 'filterChecked'))
  }
  // 可用于设置自定义列的信息
  private get fieldSettingData() {
    return this.fieldData.filter(item => Object.prototype.hasOwnProperty.call(item, 'checked'))
  }

  private get isFilter() {
    return this.fieldData.some((item) => {
      if (Array.isArray(item.value)) {
        return item.type === 'condition'
          ? item.value.some(data => !typeTools.isNull(data.value) && data.condition)
          : item.value.some(item => !typeTools.isNull(item))
      }
      return !typeTools.isNull(item.value)
    })
  }

  private get fieldData() {
    return this.tableInstance.fieldData
  }

  // 指标对比
  private handleContrastIndex() {
    this.selections = Object.freeze(JSON.parse(JSON.stringify(this.getSelections())))
    this.visiable = true
  }

  // 复制IP
  private handleCopyIp() {
    const selections = this.getSelections()
    const ipList = selections.map(item => item.bk_host_innerip).join('\n')
    copyText(ipList, (err) => {
      this.$bkMessage('error', err)
    })
    this.$bkMessage({
      theme: 'success',
      message: `${this.$t('成功复制')}${ipList.split('\n').length}${this.$t('个')}IP`
    })
  }

  // 字段显示勾选事件
  @Emit('check-change')
  private handleCheckColChange(item: IFieldConfig) {
    const data = this.getLocalStorage()
    if (item.checked) {
      delete data[item.id]
    } else {
      data[item.id] = 1
    }
    localStorage.setItem(this.storageKey, JSON.stringify(data))
    // 更新store
    const index = this.tableInstance.fieldData.findIndex(field => field.id === item.id)
    if (index > -1) {
      const data = this.tableInstance.fieldData[index]
      data.checked = !data.checked
    }
    return item
  }

  private getLocalStorage() {
    try {
      return JSON.parse(localStorage.getItem(this.storageKey)) || {}
    } catch {
      return {}
    }
  }

  private handleShowPanel() {
    this.showFilterPanel = true
  }

  @Emit('search-change')
  @Emit('filter')
  private handleFilter() {
    if (this.isFilter) {
      const search = this.fieldData.reduce((pre, next) => {
        const isEmpty = Array.isArray(next.value)
          ? next.value.length === 0
          : typeTools.isNull(next.value)
        if (!isEmpty) {
          pre.push({
            id: next.id,
            value: next.value
          })
        }
        return pre
      }, [])
      PerformanceModule.setConditions(JSON.parse(JSON.stringify(search)))
    }
    this.showFilterPanel = false
  }

  @Emit('search-change')
  private handleReset() {
    PerformanceModule.setConditions()
  }

  @Debounce(300)
  @Emit('search-change')
  private handleSearch() {
    this.tableInstance.page = 1
    this.tableInstance.keyWord = this.keyWord
  }

  @Emit('search-change')
  private handleFilterChange() {}

  private getSelections() {
    if (this.checkType === 'current') {
      return this.selectionData
    }
    return this.tableInstance.filterData.filter(item => !this.excludeDataIds.includes(item.rowId))
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.performance-tool {
  padding: 20px 18px 20px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #dcdee5;
  border-top: 0;
  border-bottom: 0;
  font-size: 0;
  &-left {
    display: flex;
    .tool-btn:not(:first-child) {
      margin-left: 8px;
    }
  }
  &-right {
    flex-basis: 515px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    .tool-search {
      flex: 1;
    }
    .tool-icon {
      margin-left: 8px;
      font-size: 16px;
      color: #979ba5;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #c4c6cc;
      border-radius: 2px;
      cursor: pointer;
      &.is-filter {
        border-color: #699df4;
        background: #f1f6ff;
        color: #3a83ff;
      }
      &.disabled {
        cursor: not-allowed;
      }
    }
  }
}
.tool-popover {
  margin: -7px -14px;
  color: #63656e;
  &-title {
    color: #444;
    font-size: 24px;
    line-height: 32px;
    margin: 15px 24px 0;
  }
  &-content {
    padding: 0;
    margin: 15px 20px 22px 24px;
    display: flex;
    flex-flow: row;
    flex-wrap: wrap;
    align-items: center;
    &-item {
      max-width: 200px;
      flex-flow: 0;
      flex-shrink: 0;
      flex-basis: 33.33%;
      margin: 8px 0;

      @include ellipsis;
      /deep/ .bk-form-checkbox {
        margin-bottom: 0;
        .bk-checkbox {
          &::after {
            box-sizing: content-box;
          }
        }
        .bk-checkbox-text {
          width: 130px;

          @include ellipsis;
        }
      }
    }
  }
}
</style>
