<template>
  <div class="conditions-item" v-bkloading="{ isLoading: comLoading }">
    <!-- 头部 -->
    <div class="item-header" @click="handleShowContent">
      <div class="header-left">
        <i :class="['icon-monitor', 'icon-arrow-down', { 'arrow-right': !isShowContent }]"></i>
        <span class="title">{{ handleName() }}</span>
      </div>
      <div class="header-right">
        <span :class="['icon', !data.hidden ? 'visual' : 'invisible']" @click.stop="handleVisibility">
          <i :class="['icon-monitor', !data.hidden ? 'icon-mc-visual-fill' : 'icon-mc-invisible-fill']"></i>
          <i :class="['icon-monitor', !data.hidden ? 'icon-mc-visual' : 'icon-mc-invisible']"></i>
        </span>
        <span class="icon copy" @click.stop="handleClone">
          <i class="icon-monitor icon-mc-copy-fill"></i>
          <i class="icon-monitor icon-mc-copy"></i>
        </span>
        <span class="icon delete" @click.stop="handleDelete">
          <i class="icon-monitor icon-mc-delete-line"></i>
          <i class="icon-monitor icon-delete-fill"></i>
        </span>
      </div>
    </div>
    <!-- 条件详细内容 -->
    <div class="item-content" ref="content">
      <div style="padding-bottom: 20px">
        <div class="form-item">
          <div class="label">{{ $t('监控对象') }}</div>
          <bk-select
            :value="data.label"
            :disabled="!!data.metricField"
            :clearable="false"
            @change="handleLabelChange">
            <bk-option-group
              v-for="(group, index) in labelList"
              :name="group.name"
              :key="index">
              <bk-option
                v-for="option in group.children"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-option-group>
          </bk-select>
        </div>
        <div class="form-item">
          <div class="label">{{ $t('指标选择') }}</div>
          <bk-input
            ref="metricInput"
            :placeholder="$t('请选择')"
            @clear="handleClearMerticVal"
            :clearable="true"
            @focus="handleShowMetricSelector"
            :value="metricValStr">
          </bk-input>
        </div>
        <div v-if="metric.value">
          <div class="form-item group">
            <div class="group-item">
              <div class="label">{{ $t('汇聚方法') }}</div>
              <bk-select :value="data.method" @change="changeMethod" :clearable="false">
                <bk-option
                  v-for="(method, index) in aggMethodList"
                  :key="index"
                  :id="method.id"
                  :name="method.name">
                </bk-option>
              </bk-select>
            </div>
            <div class="group-item">
              <div class="label">{{ $t('汇聚周期') }}</div>
              <cycle-input
                :value="data.interval"
                :placeholder="$t('请输入汇聚周期')"
                width="auto"
                :list="aggIntervalList"
                @input="changeInterval">
              </cycle-input>
            </div>
          </div>
          <div class="form-item">
            <div class="label">{{ $t('维度') }}</div>
            <strategy-dimension-input
              :key="dimensionKey"
              :metric-field="data.metricField"
              :type-id="data.label"
              :dimensions="data.groupBy"
              :data-source-label="data.dataSourceLabel"
              :data-type-label="data.dataTypeLabel"
              :dimension-list="dimensionsListFilterList"
              @dimension-select="handleDimensionSelect"
              @dimension-delete="handleDimensionDelete">
            </strategy-dimension-input>
          </div>
          <div class="form-item">
            <div class="label">{{ $t('条件') }}</div>
            <strategy-condition-input
              :key="conditionKey"
              ref="conditionsRef"
              :conditions="data.where"
              :dimension-list="dimensionsList"
              :result-table-id="data.resultTableId"
              :metric-field="data.metricField"
              :data-type-label="data.dataTypeLabel"
              :data-source-label="data.dataSourceLabel"
              :type-id="data.label"
              :biz-id="bizId"
              @on-set-value="handleConditionsValue"
              @on-remove-item="handleConditionsValue">
            </strategy-condition-input>
          </div>
        </div>
      </div>
    </div>
    <!-- 指标选择器 -->
    <strategy-config-metric-new
      ref="StrategyConfigMetricNew"
      :id="metric.id"
      :is-show="metric.show"
      :is-edit="metricIsEdit"
      :metric="metric.metricObj"
      :monitor-type.sync="metric.label"
      :scenario-list="scenarioList"
      @on-add="handleAddMetric"
      @show-change="handleHideMetricDialog"
      @hide-dialog="handleHideMetricDialog">
    </strategy-config-metric-new>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Ref, Prop, Watch } from 'vue-property-decorator'
import { deepClone, transformDataKey, Debounce } from '../../../../monitor-common/utils/utils'
import MonitorVue from '../../../types/index'
import strategyDimensionInput
  from '../../strategy-config/strategy-config-set/strategy-set-input/strategy-dimension-input.vue'
import strategyConditionInput
  from '../../strategy-config/strategy-config-set/strategy-set-input/strategy-condition-input.vue'
import StrategyConfigMetricNew
  from '../../strategy-config/strategy-config-set/strategy-config-metric/strategy-config-metric-new.vue'
import { IQueryConfigsItem, IAggMethodList, IMethodListItem, IDimensionsListItem, IAggIntervalListItem } from '../index'
import DataRetrieval from '../../../store/modules/data-retrieval'
import { getRandomId } from '../../../utils'
import CycleInput from '../../../components/cycle-input/cycle-input.vue'


@Component({
  name: 'data-query-conditions-item',
  components: {
    strategyDimensionInput,
    strategyConditionInput,
    StrategyConfigMetricNew,
    CycleInput
  }
})
export default class DataQueryConditionsItem extends Vue<MonitorVue> {
  // 查询条件数据
  @Prop({ required: true, default: () => {}, type: Object }) data: IQueryConfigsItem

  // 循环索引
  @Prop({ required: true, type: Number }) readonly index: number

  // 当前组件loading
  comLoading = false
  // 查询条件展开状态
  isShowContent = true

  nameChar = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  // 计算公式列表
  aggMethodList: IAggMethodList[] = []
  // 周期列表
  aggIntervalList: IAggIntervalListItem[] = [
    {
      id: 60,
      name: '1'
    },
    {
      id: 120,
      name: '2'
    },
    {
      id: 300,
      name: '5'
    }
  ]
  // 监控条件方法
  conditionMethods: IMethodListItem[] = []
  // 维度
  dimensionsList: IDimensionsListItem[] = []

  // 指标选择器数据
  metric: any = {
    id: 0,
    show: false,
    isEdit: false,
    metricObj: null,
    label: null,
    value: null
  }

  get bizId() {
    return this.$store.getters.bizId
  }

  get defaultAggMethodList() {
    return DataRetrieval.defaultMethodListGetter
  }

  get metricIsEdit() {
    return !!(this.metric.id && this.metric.metricObj) && this.metric.show
  }
  // 指标数据
  get timeSeriesMetricList() {
    return DataRetrieval.timeSeriesMetric[this.data.label]
  }

  // 监控对象
  get labelList() {
    return DataRetrieval.labelListGetter
  }

  get queryData() {
    return DataRetrieval.queryDataGetter
  }

  get dimensionsListFilterList() {
    return this.dimensionsList.filter((item) => {
      if ('isDimension' in item) return item.isDimension
      return true
    })
  }

  get dimensionKey() {
    let key = 'refreshDimensionKey'
    if (this.dimensionsList) {
      key = getRandomId()
    }
    return key
  }

  get conditionKey() {
    let key = 'refreshConditionKey'
    if (this.dimensionsList || this.conditionMethods) {
      key = getRandomId()
    }
    return key
  }

  get scenarioList() {
    return this.$store.getters['strategy-config/scenarioList']
  }

  // 指标显示字符串
  get metricValStr() {
    let value = ''
    if (this.metric.value) {
      const {
        resultTableLabelName,
        relatedName, resultTableName,
        metricFieldName
      } = transformDataKey(this.metric.value)
      value = `${resultTableLabelName}/${relatedName}/${resultTableName}/${metricFieldName}`
    }
    return value
  }

  // 查询条件 ref
  @Ref('content') readonly contentEl: HTMLElement
  // conditions ref
  @Ref('conditionsRef') readonly conditionsEl: any

  @Ref('StrategyConfigMetricNew') readonly StrategyConfigMetricEl: StrategyConfigMetricNew

  @Ref('metricInput') readonly metricInputEl: any

  @Watch('isShowContent', { immediate: true })
  watchShowContent(v: boolean) {
    if (v) {
      this.$nextTick(() => {
        this.contentEl.addEventListener('transitionend', this.handleContentHeightAuto, false)
      })
    } else {
      this.contentEl.removeEventListener('transitionend', this.handleContentHeightAuto, false)
    }
  }

  @Watch('data', { immediate: true })
  watchQueryData() {
    this.metric.label = this.data.label
    this.getMetricData()
  }

  mounted() {
    // 获取conditions值
    // this.$bus.$on('handle-conditions-validator', this.handleConditionsValidator)
    this.isShowContent && this.showContent()
    this.getMetricData()
  }

  beforeDestroy() {
    // 取消监听
    this.$bus.$off('get-conditions-value')
    this.$bus.$off('handle-conditions-validator')
  }

  handleShowMetricSelector() {
    this.metricInputEl.blur()
    this.metric.show = true
  }

  // 获取指标数据
  async getMetricData() {
    const needGetMetric = this.data.metricField
    if (needGetMetric && this.StrategyConfigMetricEl) {
      const params = {
        resultTableLabel: this.data.label,
        dataSourceLabel: this.data.dataSourceLabel,
        dataTypeLabel: this.data.dataTypeLabel,
        id: this.data.merticId,
        metricName: this.data.metricField,
        resultTableId: this.data.resultTableId,
        relatedId: this.data.relatedId,
        relatedName: this.data.relatedName
      }
      this.comLoading = true
      const metric = await this.StrategyConfigMetricEl.getMetric(params)
      this.comLoading = false
      this.metric.value = metric
      this.handleMerticData(metric)
    }
  }
  async handleLabelChange(value) {
    this.metric.label = value
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'label', value })
  }
  // 指标更新
  handleMerticData(value) {
    const metricObj = transformDataKey(value)
    this.handleMetricBackToDisplay(metricObj)
    const {
      id,
      relatedId,
      relatedName,
      conditionMethods,
      dimensions,
      metricField,
      resultTableId,
      dataSourceLabel,
      //   defaultDimensions,
      //   defaultCondition,
      methodList,
      dataTypeLabel
    } = metricObj
    this.metric.id = id
    // 监控条件方法
    this.conditionMethods = !Array.isArray(conditionMethods) ? [] : conditionMethods.map(item => ({
      id: item.value,
      name: item.label,
      show: true
    }))
    // 计算公式
    this.aggMethodList = !methodList ? this.defaultAggMethodList : methodList.map(id => ({
      id,
      name: id
    }))
    // 监控维度
    this.dimensionsList = dimensions
    // 监控条件默认值
    // const newWhere = !defaultCondition ? [] : defaultCondition.map((item) => {
    //   const { key, method, value } = item
    //   return {
    //     key,
    //     method,
    //     value: [value]
    //   }
    // })
    // 前端搜索数据依赖merticId、relatedId、relatedName
    const valueMap = [
      { expr: 'merticId', value: id },
      { expr: 'relatedId', value: relatedId },
      { expr: 'relatedName', value: relatedName },
      { expr: 'method', value: this.data.method || (methodList ? methodList[0] : this.defaultAggMethodList[0].id) },
      { expr: 'interval', value: this.data.interval || this.aggIntervalList[0] },
      { expr: 'metricField', value: metricField },
      { expr: 'resultTableId', value: resultTableId },
      { expr: 'dataSourceLabel', value: dataSourceLabel },
      { expr: 'dataTypeLabel', value: dataTypeLabel || 'time_series' },
      { expr: 'groupBy', value: this.data.groupBy || [] },
      { expr: 'where', value: this.data.where || [] }
    ]
    // 更新vuex的qeuryconfigs
    valueMap.forEach((item) => {
      DataRetrieval.setQueryConfigItem({ index: this.index, expr: item.expr, value: item.value })
    })
  }
  // 处理指标选择器回显数据
  handleMetricBackToDisplay(metric) {
    const metricObj = {
      dataSourceLabel: metric.dataSourceLabel,
      dataTypeLabel: metric.dataTypeLabel,
      metricName: metric.metricField,
      relatedId: metric.relatedId,
      relatedName: metric.relatedName,
      resultTableId: metric.resultTableId,
      id: metric.id
    }
    this.metric.metricObj = metricObj
  }

  // 展开查询条件
  handleShowContent() {
    this.isShowContent = !this.isShowContent
    this.showContent()
  }

  // 展开
  showContent() {
    const el = this.contentEl
    if (!el) return
    const h = el.scrollHeight
    if (el.style.height) {
      el.style.height === 'auto' && (el.style.height = `${h}px`)
      setTimeout(() => {
        el.style.height = null
      }, 0)
    } else {
      el.style.height = `${h}px`
    }
  }

  // 处理展开高度自适应
  handleContentHeightAuto() {
    const h = this.contentEl.style.height
    h && (this.contentEl.style.height = 'auto')
  }

  // 克隆查询条件
  handleClone() {
    const tempItem = deepClone(this.data)
    DataRetrieval.handleCloneQueryConfig(tempItem)
  }

  // 删除查询条件
  handleDelete() {
    let flag = false
    const item = this.queryData.queryConfigs[this.index]
    if (item.metricField && !item.hidden) flag = true
    DataRetrieval.handleDeleteQueryConfig(this.index)
    if (this.queryData.queryConfigs.length <= 1 && this.queryData.compareConfig.type === 'metric') {
      DataRetrieval.setData({ expr: 'queryData.compareConfig.type', value: 'none' })
      DataRetrieval.setData({ expr: 'queryData.compareConfig.split', value: true })
    }
    if (flag) {
      DataRetrieval.handleQuery()
      return
    }
  }

  // 控制查询条件可见性
  handleVisibility() {
    DataRetrieval.handleHiddenQueryConfig(this.index)
    DataRetrieval.handleQuery()
  }

  // 更新计算公式
  changeMethod(value) {
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'method', value })
    DataRetrieval.handleQuery()
  }
  // 更新监控周期
  @Debounce(300)
  changeInterval(value) {
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'interval', value })
    DataRetrieval.handleQuery()
  }

  // 添加维度
  handleDimensionSelect(data, emitType: 'created' | undefined) {
    const value = data.map(item => item.id).filter(id => String(id).length)
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'groupBy', value })
    if (!emitType && emitType !== 'created') {
      DataRetrieval.handleQuery()
    }
  }

  // 删除维度
  handleDimensionDelete(data) {
    const groupBy = this.data.groupBy.filter(item => item !== data.id)
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'groupBy', value: groupBy })
    DataRetrieval.handleQuery()
  }

  // 条件值变更
  handleConditionsValue(data) {
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'where', value: data })
    if (data.some(item => !item.value || !item.value.length)) return
    DataRetrieval.handleQuery()
  }

  // 获取conditions值
  handleGetConditionsValue() {
    const condition = this.conditionsEl
    if (condition) {
      const where = condition.getValue()
      where && DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'where', value: where })
    }
  }

  //   // 处理每条条件的校验
  //   handleConditionsValidator() {
  //     if (this.data.hidden) return
  //     DataRetrieval.addPromiseListValidator(new Promise((resolve) => {
  //       if (this.data.metricField) {
  //         resolve(true)
  //       } else {
  //         resolve(true)
  //         // reject(`${this.$t('指标不能为空')}-${this.nameChar[this.index]}`)
  //       }
  //     }))
  //   }

  //   // 清除指标设置数据
  //   clearMetricConfig() {
  //     const clearMap = [
  //       { expr: 'groupBy', value: null },
  //       { expr: 'where', value: null },
  //       { expr: 'method', value: '' },
  //       { expr: 'interval', value: 60 },
  //       { expr: 'metricField', value: '' }
  //     ]
  //     clearMap.forEach((item) => {
  //       const { expr, value } = item
  //       DataRetrieval.setQueryConfigItem({ index: this.index, expr, value })
  //     })
  //   }

  async handleAddMetric(metric) {
    this.metric.id = metric.id
    this.metric.value = transformDataKey(metric)
    // this.clearMetricConfig()
    this.handleMerticData(this.metric.value)
    DataRetrieval.handleQuery()
    await this.$nextTick()
    DataRetrieval.setData({ expr: 'labelCache', value: this.metric.label })
  }

  handleHideMetricDialog(show) {
    this.metric.show = show
    DataRetrieval.setQueryConfigItem({ index: this.index, expr: 'label', value: this.metric.label })
  }

  handleClearMerticVal() {
    this.metric.metricObj = null
    this.metric.isEdit = true
    this.metric.value = null
    if (this.queryData.queryConfigs.length <= 1) {
      DataRetrieval.setData({ expr: 'queryConfigsResult', value: {} })
    }
    DataRetrieval.clearQueryItem(this.index)
  }

  handleName(): string {
    const len = this.nameChar.length
    const { index } = this
    if (index < len) {
      return this.nameChar[index]
    }
    const n = Math.floor(index / len)
    const i = index % len
    return this.nameChar.slice(0, n) + this.nameChar[i]
  }
}

</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.conditions-item {
  font-size: 12px;
  border-bottom: 1px solid #f0f1f5;
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 20px 8px 14px;
    cursor: pointer;
    .header-left {
      display: flex;
      align-items: center;
      .title {
        margin-left: 6px;
        color: #313238;
      }
    }
    .header-right {
      font-size: 0;
      .icon {
        font-size: 16px;
        &:not(:last-child) {
          margin-right: 11px;
        }
      }
      .copy {
        display: inline-block;
        .icon-mc-copy-fill {
          display: none;
        }
        &:hover {
          .icon-mc-copy {
            display: none;
          }
          .icon-mc-copy-fill {
            display: inline-block;
            color: $primaryFontColor;
          }
        }
      }
      .delete {
        display: inline-block;
        .icon-delete-fill {
          display: none;
        }
        &:hover {
          .icon-mc-delete-line {
            display: none;
          }
          .icon-delete-fill {
            display: inline-block;
            color: $primaryFontColor;
          }
        }
      }
      .visual {
        display: inline-block;
        .icon-mc-visual-fill {
          display: none;
        }
        &:hover {
          .icon-mc-visual {
            display: none;
          }
          .icon-mc-visual-fill {
            display: inline-block;
            color: $primaryFontColor;
          }
        }
      }
      .invisible {
        display: inline-block;
        .icon-mc-invisible-fill {
          display: none;
        }
        &:hover {
          .icon-mc-invisible {
            display: none;
          }
          .icon-mc-invisible-fill {
            display: inline-block;
            color: $primaryFontColor;
          }
        }
      }
    }
  }
  .item-content {
    padding: 0 20px 0 44px;
    overflow: hidden;
    height: 0;
    will-change: height;
    transition: height .3s ease-in-out;
    .form-item {
      padding-bottom: 15px;
    }
    .group {
      display: flex;
      .group-item {
        width: 50%;
        &:not(:last-child) {
          margin-right: 8px;
        }
      }
    }
    .label {
      line-height: 20px;
      color: $defaultFontColor;
      margin-bottom: 6px;
    }
  }
}
</style>
