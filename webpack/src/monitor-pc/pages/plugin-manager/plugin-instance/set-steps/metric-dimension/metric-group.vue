<!--
 * @Date: 2021-06-10 11:55:13
 * @LastEditTime: 2021-06-25 19:40:20
 * @Description:
-->
<template>
  <div class="metric-group" :class="{ 'active': show }">
    <div class="group-header">
      <div class="left-box" @click="show = !show">
        <i class="bk-icon group-icon" :class="show ? 'icon-right-shape' : 'icon-down-shape'"></i>
        <div class="group-name">{{ groupName }}</div>
        <div class="group-num">
          {{ $t('共') }}
          <span class="num-blod">{{ getMetricNum }}</span> {{ $t('个指标，') }}
          <span class="num-blod">{{ getDimensionNum }}</span> {{ $t('个维度') }}
        </div>
        <template v-if="groupIndex !== 0">
          <i class="ml20 icon-monitor icon-bianji edit-icon" @click.stop="handleEditGroup"></i>
          <i class="icon-monitor icon-mc-delete edit-icon" @click.stop="handleDelGroup"></i>
        </template>
      </div>
      <div>
        <bk-button text size="small" class="pl5 pr5" @click.stop="addRow('metric')">{{ $t('新增指标') }}</bk-button>
        <bk-button text size="small" class="mr15 pl5 pr5" @click.stop="addRow('dimension')">{{ $t('新增维度') }}</bk-button>
      </div>
    </div>
    <transition :css="false"
                @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
                @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave">
      <div class="table-box" v-show="!show">
        <div class="left-table" :class="{ 'left-active': isShowData }">
          <bk-table :data="paginationData"
                    :outer-border="false"
                    :pagination="pagination"
                    :max-height="427"
                    :show-pagination-info="false"
                    :row-class-name="handleRowClassName"
                    @page-change="handlePageChange"
                    @page-limit-change="handleLimitChange">
            <bk-table-column width="80" align="center" :render-header="renderSelection" :resizable="false">
              <template slot-scope="scope">
                <bk-checkbox v-model="scope.row.isCheck" :disabled="scope.row.monitor_type === 'dimension'"
                             @change="handleCheckMetric(scope)">
                </bk-checkbox>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('指标/维度')" width="150">
              <template slot-scope="scope">
                {{ scope.row.monitor_type === 'metric' ? $t('指标') : $t('维度') }}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('英文名')" min-width="100">
              <template slot-scope="scope">
                <div class="cell-margin name">
                  <div @mouseenter="handleInputMouseEnter(...arguments, scope.$index, scope.row.source_name)" @mouseleave="handleInputMouseLeave" :ref="'inputmetric' + scope.$index">
                    <div v-if="!scope.row.showInput || scope.row.isFirst" class="overflow-tips" v-bk-overflow-tips @click="handleClickInput(scope)">
                      <span v-if="scope.row.name">{{ scope.row.name }}</span>
                      <span v-else style="color: #c4c6cc">{{ $t('输入指标id') }}</span>
                    </div>
                    <bk-input v-else v-model="scope.row.name" :placeholder="scope.row.monitor_type === 'metric' ? $t('输入指标id') : $t('输入维度id')" size="small"
                              :disabled="scope.row.isFirst || !!scope.row.source_name" @blur="handleCheckName(scope.row)"
                              :class="{ 'input-err': scope.row.errValue || scope.row.reValue }" :ref="`input${scope.$index}`">
                    </bk-input>
                  </div>
                  <bk-popover class="change-name" placemnet="top-start" trigger="mouseenter" :tippy-options="{ a11y: false }">
                    <i v-if="scope.row.errValue" class="icon-monitor icon-remind"></i>
                    <i v-else-if="scope.row.reValue" class="icon-monitor icon-change" @click.stop="handleRename(scope.row)"></i>
                    <div slot="content">
                      <template v-if="scope.row.errValue">{{ $t('名字有冲突') }}</template>
                      <template v-else-if="scope.row.reValue">
                        <div>{{ $t('名字有冲突,可点击该图') }}</div>
                        {{ $t('标转换成非冲突名称') }}
                      </template>
                    </div>
                  </bk-popover>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('别名')" min-width="100">
              <template slot-scope="scope">
                <div class="cell-margin name">
                  <bk-input v-model="scope.row.description" size="small"
                            :placeholder="scope.row.monitor_type === 'metric' ? $t('输入指标别名') : $t('输入维度别名')"
                            @blur="handleCheckDescName(scope.row)" :class="{ 'input-err': scope.row.descReValue }">
                  </bk-input>
                  <bk-popover class="change-name" placemnet="top-start" trigger="mouseenter" :tippy-options="{ a11y: false }">
                    <i v-if="scope.row.descReValue" class="icon-monitor icon-remind"></i>
                    <div slot="content">
                      <template v-if="scope.row.descReValue">{{ $t('别名有冲突') }}</template>
                    </div>
                  </bk-popover>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('类型')" width="120">
              <template slot-scope="scope">
                <template v-if="scope.row.monitor_type === 'metric'">
                  <div v-if="numType.value && numType.index === scope.$index" class="cell-margin" @mouseleave="handleMouseLeave('numType')">
                    <bk-select
                      v-model="scope.row.type"
                      :popover-options="selectPopoverOption"
                      @change="handleTypeChange(scope.row)"
                      :clearable="false"
                      @toggle="handleToggleChange(...arguments, 'numType')">
                      <bk-option
                        v-for="option in typeList"
                        :key="option.id"
                        :id="option.id"
                        :name="option.name">
                      </bk-option>
                    </bk-select>
                  </div>
                  <div v-else class="cell-span" @mouseenter="handleMouseenter(scope.$index, 'numType')">{{ scope.row.type }}</div>
                </template>
                <template v-else>
                  <div class="cell-span">{{ scope.row.type }}</div>
                </template>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('单位')" width="170">
              <template slot-scope="scope">
                <div class="cell-margin" v-if="unit.value && unit.index === scope.$index && scope.row.monitor_type === 'metric'" @mouseleave="handleMouseLeave('unit')">
                  <!-- <bk-cascade
                                        v-model="scope.row.unit"
                                        :list="unitList"
                                        clearable
                                        style="width: 130px;"
                                        @toggle="handleToggleChange(...arguments, 'unit')">
                                    </bk-cascade> -->
                  <bk-select
                    v-model="scope.row.unit"
                    :clearable="false"
                    :popover-width="120"
                    @toggle="handleToggleChange(...arguments, 'unit')"
                    :popover-options="selectPopoverOption">
                    <bk-option-group
                      v-for="(group, index) in unitList"
                      :name="group.name"
                      :key="index">
                      <bk-option
                        v-for="option in group.formats"
                        :key="option.id"
                        :id="option.id"
                        :name="option.name">
                      </bk-option>
                    </bk-option-group>
                  </bk-select>
                </div>
                <div v-else class="cell-span" @mouseenter="handleMouseenter(scope.$index, 'unit')">{{ handleFindUnitName(scope.row.unit) }}</div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('启/停')" width="90">
              <template slot-scope="scope">
                <bk-switcher v-model="scope.row.is_active" size="small" @change="handleSwitchChange(arguments, scope)" theme="primary"></bk-switcher>
              </template>
            </bk-table-column>
            <bk-table-column label="" width="90" prop="create_time">
              <template slot-scope="scope">
                <i class="bk-icon icon-plus-circle icon-btn" @click="handleAddRow(scope)"></i>
                <i class="bk-icon icon-minus-circle icon-btn" :class="{ 'not-del': !scope.row.isDel }" @click="handleDelRow(scope)"></i>
              </template>
            </bk-table-column>
            <div slot="empty" class="empty">
              <i class="icon-monitor icon-remind empty-i"></i>
              <div>{{ $t('暂无指标/维度') }} <span class="blue" @click="handleAddFirstRow">{{ $t('点击添加') }}</span></div>
            </div>
          </bk-table>
        </div>
        <template v-if="!isFromHome">
          <div class="right-data" v-show="isShowData">
            <ul class="ul-head">
              <li class="host-type" :class="{ 'active': osIndex === dataPreview.index }"
                  v-for="(osType, osIndex) in osTypeList" :key="osIndex"
                  @click="handleDataChange(osIndex, osType)">{{ osType }}</li>
            </ul>
            <template v-if="metricData.length">
              <div class="data-preview" v-for="(item, index) in metricData" :key="index">
                {{ typeof item.value[dataPreview.type] === null ? '--' : item.value[dataPreview.type] + '' }}
              </div>
            </template>
            <div v-else class="no-data-preview"></div>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<script>
/* eslint-disable vue/no-mutating-props */
import { mapActions, mapGetters } from 'vuex'
import { collapseMixin } from '../../../../../common/mixins'
import ColumnCheck from '../../../../performance/column-check/column-check.vue'

export default {
  name: 'MetricGroup',
  mixins: [collapseMixin],
  props: {
    metricData: { //  指标/维度数据
      type: Array,
      default: () => ([])
    },
    stopData: {
      type: Array,
      default: () => ([])
    },
    hideStop: Boolean,
    groupName: String, //  分组名字
    groupIndex: Number, //  分组索引
    isShowData: Boolean, //  数据预览开关
    osTypeList: { //  调试类型
      type: Array,
      default: () => ([])
    },
    nameList: { // 英文名列表
      type: Array,
      default: () => ([])
    },
    descNameList: { //  别名列表
      type: Array,
      default: () => ([])
    },
    isFromHome: {
      type: Boolean,
      default: false
    },
    unitList: { //  动态单位表
      type: Array,
      default: () => ([])
    },
    typeList: {
      type: Array,
      default() {
        return [ //  类别表
          { id: 'double', name: 'double' },
          { id: 'int', name: 'int' }
        ]
      }
    }
  },
  data() {
    return {
      show: false, //  是否展开
      dataPreview: { //  数据预览参数
        index: 0,
        type: this.osTypeList[0]
      },
      numType: {
        value: true,
        index: -1,
        toggle: false
      },
      unit: {
        value: true,
        index: -1,
        toggle: false
      },
      instance: null,
      selectPopoverOption: {
        boundary: 'body',
        flipBehavior: ['bottom']
      },
      pagination: {
        current: 1,
        count: this.metricData.length,
        limit: 20,
        limitList: [20, 50, 100]
      },
      selectList: [
        {
          id: 'current',
          name: this.$t('本页全选')
        },
        {
          id: 'all',
          name: this.$t('跨页全选')
        }
      ],
      checkType: 'current'
    }
  },
  computed: {
    ...mapGetters('plugin-manager', ['reservedWords']), //    关键字列表
    // 表格前端分页
    paginationData() {
      const { limit, current } = this.pagination
      return this.metricData.slice(limit * (current - 1), limit * current)
    },
    // 指标数量
    getMetricNum() {
      const res = this.metricData.filter(item => item.monitor_type === 'metric' && item.name !== '')
      const stopMetrics = this.stopData.filter(item => item.data.monitor_type === 'metric'
      && item.data.name !== ''
      && !item.data.is_active)
      return this.hideStop ? res.length + stopMetrics.length : res.length
    },
    // 维度数量
    getDimensionNum() {
      const res = this.metricData.filter(item => item.monitor_type === 'dimension' && item.name !== '')
      const stopDimensions = this.stopData.filter(item => item.data.monitor_type === 'dimension'
      && item.data.name !== '' && !item.data.is_active)
      return this.hideStop ? res.length + stopDimensions.length : res.length
    },
    //  是否半选
    indeterminateValue() {
      if (this.checkType === 'current') {
        return this.paginationData.some(item => item.isCheck)
      }
      return this.metricData.some(item => item.isCheck)
    },
    // 是否全选
    allCheckValue() {
      if (this.checkType === 'current' && this.paginationData.length) {
        return this.paginationData.every(item => item.isCheck || item.monitor_type === 'dimension')
      }

      if (this.checkType === 'all' && this.metricData.length) {
        return this.metricData.every(item => item.isCheck || item.monitor_type === 'dimension')
      }

      return false
    },
    // 是否全部为维度
    isAllDimension() {
      const data = this.checkType === 'current' ? this.paginationData : this.metricData
      return data.every(item => item.monitor_type === 'dimension')
    },
    checkValue() {
      if (this.isAllDimension) {
        return 0
      }

      if (this.allCheckValue) {
        return 2
      }
      if (this.indeterminateValue) {
        return 1
      }
      return 0
    }
  },
  watch: {
    metricData(data) {
      this.pagination.count = data.length
      this.$nextTick(() => {
        // 当前页全部删除时，跳转到上一页
        if (!this.paginationData.length && this.pagination.current > 1) {
          this.pagination.current -= 1
        }
      })
    }
  },
  async created() {
    !this.reservedWords.length && await this.getReservedWords()
  },
  methods: {
    ...mapActions('plugin-manager', ['getReservedWords']),
    //  编辑分组
    handleEditGroup() {
      this.$emit('edit-group', this.groupIndex)
    },
    //  删除分组
    handleDelGroup() {
      this.$emit('del-group', this.groupIndex)
    },
    // 在当前行下面新增一行指标/维度
    handleAddRow(scope) {
      this.$emit('add-row', scope.row, scope.$index, this.groupIndex)
    },
    // 删除行
    handleDelRow(scope) {
      if (scope.row.isDel) {
        this.$emit('del-row', scope.row, scope.$index, this.groupIndex)
      }
    },
    //  增加初始行
    handleAddFirstRow() {
      this.$emit('add-first', this.groupIndex)
    },
    //  勾选指标联动勾选维度
    handleCheckMetric(scope) {
      if (scope.row.dimensions) {
        scope.row.dimensions.forEach((name) => {
          this.metricData.forEach((item) => {
            if (name === item.name) {
              item.isCheck = scope.row.isCheck
            }
          })
        })
      }
    },
    // 勾选全部
    handleCheckAll({ value, type }) {
      this.resetCheckStatus() // 从跨页全选切换到本页或者取消全选都要清空勾选操作

      // 全选操作
      if (value === 2) {
        // 有关联指标的维度集合
        const relatedDimensions = new Set()
        const data = type === 'current' ? this.paginationData : this.metricData
        data.forEach((item) => {
          // 维度不能被勾选
          item.isCheck = value === 2 && item.monitor_type !== 'dimension'
          item.monitor_type === 'metric' && (item.dimensions || []).forEach(item => relatedDimensions.add(item))
        })
        // 自动勾选关联的维度
        this.metricData.forEach((item) => {
          item.monitor_type === 'dimension' && (item.isCheck = relatedDimensions.has(item.name))
        })
      }
      this.checkType = type
    },
    // 数据预览切换
    handleDataChange(osIndex, osType) {
      this.dataPreview.index = osIndex
      this.dataPreview.type = osType
    },
    // 英文名失焦校验
    handleCheckName(row) {
      // 校验名字是否与关键字冲突
      const index = this.metricData.findIndex(item => item.id === row.id)
      const data = this.metricData[index]
      if (row.name !== '') {
        if (row.monitor_type === 'metric' && this.nameList.filter(item => item === row.name).length > 1) {
          data.errValue = true
          data.reValue = false
        } else if (row.monitor_type === 'dimension'
        && this.metricData.filter(item => item.name === row.name).length > 1) {
          data.errValue = true
          data.reValue = false
        } else if (this.reservedWords.find(item => item === row.name.toLocaleUpperCase())) {
          data.errValue = false
          data.reValue = true
        } else {
          data.reValue = false
          data.errValue = false
        }
        row.showInput = false
      } else {
        data.errValue = false
        data.reValue = false
      }
    },
    // 别名失焦校验
    handleCheckDescName(row) {
      // 校验名字是否与关键字冲突
      this.$set(row, 'descReValue', row.descReValue)
      if (row.description !== '') {
        if (this.descNameList.filter(item => item === row.description).length > 1) {
          row.descReValue = true
        } else {
          row.descReValue = false
        }
      } else {
        row.descReValue = false
      }
    },
    //  转化有冲突的关键字指标/维度名
    handleRename(row) {
      const index = this.metricData.findIndex(item => item.id === row.id)
      this.metricData[index].source_name = row.name
      this.metricData[index].name = `_${row.name}`
      this.metricData[index].reValue = false
      this.handleCheckName(row)
    },
    handleInputMouseEnter(e, index, sourceName) {
      if (!sourceName) return
      const inputRef = this.$refs[`inputmetric${index}`]
      this.instance = this.$bkPopover(inputRef, {
        content: this.$t('名字冲突，已转化成非冲突名字'),
        arrow: true,
        showOnInit: true,
        distance: 0,
        placement: 'top-start'
      })
      this?.instance?.show(100)
    },
    handleInputMouseLeave() {
      if (this.instance) {
        this.instance.hide(0)
        this.instance.destroy()
        this.instance = null
      }
    },
    handleMouseenter(index, type) {
      if (type === 'numType') {
        this.numType.value = true
        this.numType.index = index
      } else {
        this.unit.value = true
        this.unit.index = index
      }
    },
    handleMouseLeave(type) {
      if (type === 'numType' && !this.numType.toggle) {
        this.numType.value = false
        this.numType.index = -1
      } else if (type === 'unit' && !this.unit.toggle) {
        this.unit.value = false
        this.unit.index = -1
      }
    },
    handleToggleChange(value, type) {
      if (type === 'numType') {
        this.numType.toggle = value
      } else {
        this.unit.toggle = value
      }
    },
    handleTypeChange(row) {
      row.is_diff_metric = row.type === 'diff'
    },
    //  找到单位值对应的name
    handleFindUnitName(id) {
      let name = id
      this.unitList.forEach((group) => {
        const res = group.formats.find(item => item.id === id)
        if (res) {
          name = res.name
        }
      })
      return name
    },
    handleSwitchChange(arg, scope) {
      this.$emit('switch', this.groupIndex, scope.row)
    },
    // select表头渲染
    renderSelection(h) {
      return h(ColumnCheck, {
        props: {
          list: this.selectList,
          value: this.checkValue,
          defaultType: this.checkType,
          disabled: this.isAllDimension
        },
        on: {
          change: this.handleCheckAll
        }
      })
    //   return <bk-checkbox value={this.allCheckValue} indeterminate={this.indeterminateValue}
    //     disabled={!this.metricData.length} onChange={this.handleCheckAll}></bk-checkbox>
    },
    handleClickInput(scope) {
      scope.row.showInput = true
      this.$nextTick(() => {
        const refname = `input${scope.$index}`
        this.$refs?.[refname]?.focus()
      })
    },
    handlePageChange(page) {
      this.pagination.current = page
    },
    handleLimitChange(limit) {
      this.pagination.limit = limit
    },
    resetCheckStatus() {
      this.metricData.forEach((item) => {
        // 维度不能被勾选
        item.isCheck = false
      })
    },
    addRow(type) {
      this.handleAddRow({
        row: {
          monitor_type: type
        },
        $index: -1,
        groupIndex: this.groupIndex
      })
    },
    /**
     * @description: 当出现数据冲突情况给当前表格行添加类名
     * @param {*} row 当前行数据
     * @param {*} rowIndex 当前行索引
     * @return {*}
     */
    handleRowClassName({ row }) {
      return (row.errValue || row.reValue || row.descReValue) ? 'table-error-row' : ''
    }
  }
}
</script>

<style lang="scss" scoped>
    /deep/ .bk-table-header {
      .is-first {
        .bk-table-header-label {
          overflow: visible;
        }
      }
    }
    .pl5 {
      padding-left: 5px;
    }
    .pr5 {
      padding-right: 5px;
    }
    .metric-group {
      background: #fff;
      margin-bottom: 8px;
      color: #63656e;
      padding: 0 13px 30px 22px;
      box-shadow: 0 1px 2px 0 rgba(0,0,0,.10);
      transition: height .5s;
      /deep/ .bk-form-input,
      .bk-select {
        border: 1px solid #fff;
        &:hover {
          background: #f5f6fa;
          border: 1px solid #f5f6fa;
        }
      }
      .num-blod {
        font-weight: bold;
      }
      .group-header {
        display: flex;
        align-items: center;
        height: 64px;
        .left-box {
          flex-grow: 1;
          display: flex;
          align-items: center;
          height: 64px;
          cursor: pointer;
          .group-icon {
            font-size: 15px;
            margin-right: 6px;
          }
          .group-name {
            font-size: 14px;
            font-weight: bold;
            margin-right: 40px;
          }
          .group-num {
            color: #979ba5;
          }
          // /deep/ .bk-table-fit {
          //     max-height: 421px;
          //     overflow: scroll;
          // }
          // /deep/ .bk-table-header-wrapper {
          //     position: sticky;
          //     top: 0px;
          //     z-index: 1;
          // }
        }
        .edit-icon {
          font-size: 24px;
          color: #979ba5;
          cursor: pointer;
          &:hover {
            color: #3a84ff;
          }
        }
      }
      .table-box {
        display: flex;
        padding: 0 17px;
        overflow-x: hidden;

        /* stylelint-disable-next-line declaration-no-important */
        overflow-y: scroll !important;
        max-height: 427px;
        .left-table {
          margin-right: 4px;
          width: 100%;
          transition: width .5s;
          .name {
            position: relative;
            .change-name {
              position: absolute;
              right: 10px;
              top: 0;
              font-size: 20px;
              color: #ea3636;
              i {
                display: inline-block;
                font-size: 16px;
                margin-top: 5px;
              }
              .icon-remind {
                cursor: pointer;
              }
              .icon-change {
                margin-top: 2px;
                font-size: 20px;
              }
            }
          }
          .cell-margin {
            margin-left: -10px;
            .overflow-tips {
              height: 26px;
              line-height: 26px;
              padding-left: 11px;
              text-overflow: ellipsis;
              overflow: hidden;
              white-space: nowrap;
              &:hover {
                background: #f5f6fa;
              }
            }
            .icon-change {
              font-size: 20px;
              color: #ea3636;
            }
          }
          .cell-span {
            height: 26px;
            line-height: 26px;
            padding-left: 1px;
          }
          .icon-btn {
            color: #979ba5;
            font-size: 20px;
            margin-right: 4px;
            cursor: pointer;
          }
          .not-del {
            color: #dcdee5;
            cursor: no-drop;
          }
          .input-err {
            /deep/ .bk-form-input {
              padding: 0 30px 0 10px;
            }
          }
          /deep/ .bk-table-row td {
            /* stylelint-disable-next-line declaration-no-important */
            background: #fff;
          }
          /deep/.table-error-row {
            td {
              background: #f0f1f5;
            }
          }
          /deep/ .bk-form-input[disabled] {
            color: #63656e;

            /* stylelint-disable-next-line declaration-no-important */
            background: #fff !important;

            /* stylelint-disable-next-line declaration-no-important */
            border-color: #fff !important;
            cursor: no-drop;
          }
          /deep/ .is-focus {
            border-color: #3a84ff;
            box-shadow: none;
            &:hover {
              background: #fff;
              border-color: #3a84ff;
            }
          }
          .empty {
            height: 93px;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 32px;
            &-i {
              font-size: 24px;
              color: #c4c6cc;
              margin-bottom: 4px;
              cursor: pointer;
            }
            .blue {
              color: #3a84ff;
              cursor: pointer;
            }
          }
          /deep/ .bk-table-empty-text {
            padding: 0;
          }
        }
        .left-active {
          width: calc(100% - 420px);
        }
        .right-data {
          width: 420px;
          display: flex;
          flex-direction: column;
          .ul-head {
            display: flex;
            background: #000;
            .host-type {
              display: flex;
              align-items: center;
              justify-content: center;
              color: #fff;
              height: 42px;
              width: 71px;
            }
            .active {
              height: 42px;
              overflow: hidden;
              background: #313238;
              position: relative;
              &:after {
                content: "";
                width: 71px;
                height: 2px;
                position: absolute;
                background: #3a84ff;
                top: 0;
              }
            }
          }
          .data-preview {
            height: 42px;
            line-height: 42px;
            color: #979ba5;
            background: #313238;
            padding: 0 20px;
            border-bottom: 1px solid #3b3c42;
          }
          .no-data-preview {
            height: 93px;
            width: 420px;
            background: #313238;
          }
        }
      }
    }
    /deep/ .bk-group-options {
      .bk-option-content {
        padding: 0 0 0 16px;
      }
    }
</style>
