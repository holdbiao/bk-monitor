<template>
  <div class="content-retrieval">
    <div class="retrieval-title"
         @click="handleChangeStatus">
      <i class="icon-monitor icon-arrow-down" :class="{ 'retrieval-active': !queryConfig.show }"></i>{{ queryConfig.name }}
    </div>
    <transition
      @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
      @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave">
      <div v-show="queryConfig.show">
        <div class="retrieval-content">
          <div class="retrieval-content-row">
            <span class="row-label">监控对象：</span>
            <span class="row-content">{{ metric && metric['result_table_label_name'] }}</span>
          </div>
          <div class="retrieval-content-row">
            <span class="row-label">监控指标：</span>
            <span class="row-content">{{ queryConfig.data.metric_field }}</span>
          </div>
          <div class="retrieval-content-row">
            <span class="row-label" style="padding-top: 3px;">监控条件：</span>
            <span class="row-content">
              <div class="item-agg-condition">
                <div class="item-agg-dimension mb-2" v-for="(item, index) in aggCondition" :key="index" :style="{ 'color': aggConditionColorMap[item], 'font-weight': aggConditionFontMap[item] }">
                  {{Array.isArray(item) ? item.join(' , ') : item }}
                </div>
              </div>
            </span>
          </div>
        </div>
        <div class="retrieval-content-convergence">
          <div class="convergence-label">{{ $t('汇聚方法') }}</div>
          <bk-select v-model="queryConfig.data.method" :clearable="false" @change="handleMethodChange">
            <bk-option
              v-for="option in methodList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </div>
        <div class="retrieval-content-convergence">
          <div class="convergence-label">{{ $t('汇聚周期') }}</div>
          <bk-select
            v-model="queryConfig.data.interval"
            :clearable="false"
            @change="handleIntervalChange">
            <bk-option
              v-for="option in intervalList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </div>
        <div
          v-for="item in groupList"
          :key="JSON.stringify(item.name)">
          <convergence-options-item
            class="retrieval-convergence"
            v-show="item.checked"
            :title="item.name"
            :id="item.id"
            :is-default="item.disabled"
            :has-close-icon="!item.disabled"
            :groupby-list="getGroupByList(item.id)"
            @checked-change="handleCheckedChange"
            @delete-dimension="handleDeleteDimension(item.id)">
          </convergence-options-item>
        </div>
        <div class="add-convergence" @click="handleOpenDialog">
          <i class="icon-monitor icon-mc-add"></i>
          {{ $t('添加其他条件') }}
        </div>
      </div>
    </transition>
    <monitor-dialog
      :value="isdialogShow"
      :title="$t('添加条件')"
      :before-close="handleBackStep"
      @on-confirm="handleAddDimension">
      <bk-checkbox-group v-model="groupChecked">
        <bk-checkbox
          class="dialog-checkbox"
          v-for="item in groupList"
          :key="item.id"
          :value="item.id"
          :disabled="item.disabled">
          {{ item.name }}
        </bk-checkbox>
      </bk-checkbox-group>
    </monitor-dialog>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Mixins, Emit } from 'vue-property-decorator'
import collapseMixin from '../../mixins/collapseMixin'
import ConvergenceOptionsItem from './convergence-options-item.vue'
import MonitorDialog from '../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import { getMetricList } from '../../../monitor-api/modules/strategies'
import { getVariableValue } from '../../../monitor-api/modules/grafana'
import { strategyMapMixin } from '../../common/mixins'
import { CONDITION_METHOD_LIST } from '../../constant/constant'
@Component({
  name: 'query-criteria-item',
  components: {
    ConvergenceOptionsItem,
    MonitorDialog
  }
})
export default class QueryCriteriaItem extends Mixins(collapseMixin, strategyMapMixin) {
  @Prop({ required: true, type: Object }) readonly queryConfig: any
  @Prop(Number) readonly groupIndex: number

  isdialogShow = false
  beforeChangeCheckedDimensions = []
  checkedDimensions = []
  metric: any = {}
  groupBySelectList = []
  aggCondition = []
  methodList = [
    {
      id: 'SUM',
      name: 'SUM'
    },
    {
      id: 'AVG',
      name: 'AVG'
    },
    {
      id: 'MAX',
      name: 'MAX'
    },
    {
      id: 'MIN',
      name: 'MIN'
    },
    {
      id: 'COUNT',
      name: 'COUNT'
    }
  ]
  intervalList = [
    { id: 60, name: '1min' },
    { id: 120, name: '2min' },
    { id: 300, name: '5min' }
  ]
  groupList = []
  groupChecked = []

  get dimensionsList() {
    if (this.metric?.dimensions) {
      return this.metric.dimensions.map((item) => {
        const res = this.checkedDimensions.indexOf(item.id) > -1
        return {
          ...item,
          disabled: res,
          order: res ? 0 : 1
        }
      }).sort((a, b) => a.order - b.order)
    } return []
  }

  get dimensionsFilterList() {
    return this.metric.dimensions.filter((item) => {
      if ('is_dimension' in item) return item.is_dimension
      return true
    })
  }

  async created() {
    this.checkedDimensions = this.queryConfig.data.group_by
    this.groupChecked = this.queryConfig.data.group_by
    this.beforeChangeCheckedDimensions = this.queryConfig.data.group_by
    await this.handleFilterMetric(this.queryConfig.data)
    this.handleAggCondition(this.queryConfig.data)
  }

  handleMethodChange(v) {
    this.$emit('query-change', v, 'method', this.groupIndex)
  }

  handleIntervalChange(v) {
    this.$emit('query-change', v, 'Interval', this.groupIndex)
  }

  async handleFilterMetric(queryConfig) {
    this.$emit('change-loading', true)
    const params = {
      bk_biz_id: queryConfig.bk_biz_id,
      data_source_label: queryConfig.data_source_label,
      data_type_label: queryConfig.data_type_label,
      search_fields: {
        metric_field: queryConfig.metric_field,
        result_table_id: queryConfig.result_table_id
      },
      page: 1,
      page_size: 24
    }
    const data = await getMetricList(params).catch(() => {})
    // eslint-disable-next-line prefer-destructuring
    this.metric = data.metric_list[0]
    if (this.metric?.dimensions) {
      this.groupList = this.dimensionsFilterList.map((item) => {
        const isDefault = this.groupChecked.some(set => item.id === set)
        return {
          ...item,
          disabled: isDefault,
          order: isDefault ? 0 : 1,
          checked: isDefault || false
        }
      }).sort((a, b) => a.order - b.order)
    } else {
      this.groupList = []
    }
    this.$emit('change-loading', false)
  }

  handleAggCondition(data) {
    const { aggCondition } = this
    data.where.forEach((item) => {
      if (item.condition) {
        aggCondition.push(item.condition.toLocaleUpperCase())
      }
      const method = CONDITION_METHOD_LIST.find(set => set.id === item.method)
      aggCondition.push(item.key)
      aggCondition.push(method.name)
      aggCondition.push(item.value)
    })
  }

  handleAddDimension() {
    this.groupList.forEach((item) => {
      item.checked = item.disable || this.groupChecked.some(id => id === item.id)
    })
    this.handleBackStep()
  }

  handleDeleteDimension(key) {
    this.groupChecked = this.groupChecked.filter(id => id !== key)
    this.groupList.forEach((item) => {
      item.checked = item.disabled || this.groupChecked.some(id => id === item.id)
    })
    const res = {}
    res[key] = 'all'
    this.$emit('checked-change', this.groupIndex, res)
  }

  getGroupByList(field) {
    const { data } = this.queryConfig
    const params = {
      bk_biz_id: data.bk_biz_id,
      type: 'dimension',
      params: {
        data_source_label: data.data_source_label,
        data_type_label: data.data_type_label,
        field,
        metric_field: data.metric_field,
        result_table_id: data.result_table_id,
        where: data.where
      }
    }
    return () => new Promise((resolve, reject) => {
      getVariableValue(params).then((data) => {
        const result = Array.isArray(data) ? data.map(item => (
          { name: item.label, id: item.value }
        )) : []
        resolve(result)
      })
        .catch((err) => {
          reject(err)
        })
    })
  }

  handleOpenDialog() {
    this.isdialogShow = true
  }

  handleBackStep() {
    this.isdialogShow = false
  }

  handleCheckedChange(value) {
    this.$emit('checked-change', this.groupIndex, value)
  }

  @Emit('change-status')
  handleChangeStatus() {
    return this.queryConfig.name
  }
}
</script>

<style lang="scss" scoped>
.content-retrieval {
  border-bottom: 1px solid #f0f1f5;
  .retrieval-title {
    display: flex;
    align-items: center;
    height: 40px;
    color: #313238;
    padding: 0 14px;
    cursor: pointer;
    .icon-arrow-down {
      color: #63656e;
      margin-right: 6px;
      font-size: 24px;
      transition: .3s;
    }
    .retrieval-active {
      transform: rotate(-90deg);
      transition: .3s;
    }
  }
  .retrieval-content {
    padding: 0 30px 8px 30px;
    &-row {
      display: flex;
      line-height: 20px;
      min-height: 20px;
      margin-bottom: 10px;
      .row-label {
        min-width: 60px;
        color: #979ba5;
        margin-right: 12px;
      }
      .row-content {
        word-break: break-all;
        line-height: 20px;
        .item-agg-dimension {
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: left;
          min-height: 24px;
          line-height: 16px;
          border-radius: 2px;
          margin: 0 4px 2px 0;
        }
        .item-agg-condition {
          background: #fff;
          display: flex;
          flex-wrap: wrap;
          text-align: left;
        }
      }
    }
  }
  .retrieval-content-convergence {
    width: 320px;
    height: 73px;
    padding: 5px 10px 10px 10px;
    margin: 0 auto;
    .convergence-label {
      margin-bottom: 6px;
    }
  }
  .retrieval-convergence {
    margin: 0 auto;
  }
  .add-convergence {
    padding: 0 20px;
    margin-bottom: 9px;
    color: #3a84ff;
    display: flex;
    align-items: center;
    cursor: pointer;
    .icon-mc-add {
      font-size: 24px;
    }
  }
  .dialog-checkbox {
    margin-top: 8px;
    padding-right: 16px;
  }
}
</style>
