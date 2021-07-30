<template>
  <div class="compare-panel">
    <slot name="pre"></slot>
    <div class="panel-wrap" ref="panelWrap">
      <div class="panel-wrap-left">
        <drop-down-menu v-model="compare.type" :list="compareList" @change="handleChangeType"></drop-down-menu>
      </div>
      <div class="panel-wrap-center">
        <div class="center-maintag" v-if="compare.type === 'target' && curHost && curHost.ip">
          <span class="tag" :title="curHost.ip">{{curHost.ip}}</span>
        </div>
        <slot name="content" v-bind="{ compare }">
          <!-- 目标对比 -->
          <div class="target-select" v-if="compare.type === 'target'">
            <bk-select
              v-if="needTarget"
              ref="targetSelect"
              @toggle="handleSelectToggle"
              :clearable="false"
              :placeholder="$t('请选择目标')"
              searchable
              multiple
              display-tag
              v-model="compare.value"
              @change="handleValueChange('compare')"
              :popover-width="200">
              <bk-option
                v-for="option in targetList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
              <div class="target-select-clear" v-if="refTargetSelect && showClearBtn">
                <span class="clear-btn" @click="deleteSelected">{{$t('清空')}}</span>
              </div>
            </bk-select>
          </div>
          <!-- 时间对比 -->
          <bk-select
            v-model="compare.value"
            class="time-select"
            :clearable="false"
            multiple
            ref="timeSelect"
            @toggle="handleSelectToggle"
            v-else-if="compare.type === 'time'"
            @change="handleValueChange('compare')">
            <bk-option
              v-for="item in timeshiftList"
              :key="item.id + item.name"
              :id="item.id"
              :name="item.name">
            </bk-option>
            <div>
              <div class="time-select-custom" @click.prevent.stop="handleCustomClick">
                <span v-if="!custom.show" class="custom-text">{{$t('自定义')}}</span>
                <bk-input
                  v-else v-model.trim="custom.value"
                  size="small"
                  @keydown.enter.native="handleAddCustomTime">
                </bk-input>
                <!-- <bk-popover :content="$t('自定义输入格式: 如 1w 代表一周 m 分钟 h 小时 d 天 w 周 M 月 y 年')" offset="-100, 0" zIndex="9999">
                  <span v-if="custom.show"  class="help-icon icon-monitor icon-mc-help-fill"></span>
                </bk-popover> -->
                <span v-if="custom.show" v-bk-tooltips.top="$t('自定义输入格式: 如 1w 代表一周 m 分钟 h 小时 d 天 w 周 M 月 y 年')" class="help-icon icon-monitor icon-mc-help-fill"></span>
              </div>
            </div>
          </bk-select>
          <!-- 不对比: 视图拆分 -->
          <div class="split-btn-wrapper" v-else-if="needSplit && compare.type === 'none'">
            <i
              @click="handleSplit"
              :class="[
                'icon-monitor',
                compare.value ? 'icon-hebing' : 'icon-chaifen icon-active'
              ]">
            </i>
          </div>
          <span class="margin-left-auto"></span>
          <div
            :class="['search-selector-wrapper', { 'search-select-active': searchSelectActive }]"
            v-if="needSearchSelect">
            <slot name="search">
              <bk-search-select
                ext-cls="search-select"
                v-model="tools.searchValue"
                :placeholder="$t('搜索')"
                :data="searchSelectList"
                :show-condition="false"
                :filter="true"
                :filter-menu-method="() => {}"
                :show-popover-tag-change="false"
                :clearable="true"
                @clear="handleSearchSelectChange(tools.searchValue)"
                @input-focus="searchSelectActive = true"
                @change="handleSearchSelectChange">
                <i slot="prefix" class="bk-icon icon-search"></i>
              </bk-search-select>
            </slot>
          </div>
          <div class="time-shift" :style="{ minWidth: !showText ? '0' : '100px' }">
            <monitor-date-range
              :key="dateRangeKey"
              icon="icon-mc-time-shift"
              class="time-shift-select"
              @add-option="handleAddOption"
              dropdown-width="96"
              v-model="tools.timeRange"
              @change="handleTimeRangeChange"
              :options="timerangeList"
              :style="{ minWidth: showText ? '100px' : '40px' }"
              :show-name="showText"
              :z-index="2500">
            </monitor-date-range>
          </div>
          <drop-down-menu
            :show-name="showText"
            :icon="tools.refleshInterval === -1 ? 'icon-mc-alarm-recovered' : 'icon-zidongshuaxin'"
            class="time-interval"
            v-model="tools.refleshInterval"
            :text-active="tools.refleshInterval !== -1"
            @on-icon-click="$emit('on-immediate-reflesh')"
            @change="handleValueChange('interval')"
            :list="refleshList">
          </drop-down-menu>
        </slot>
      </div>
      <div class="panel-wrap-right" v-if="hasViewChangeIcon">
        <span class="tool-icon" @click="handleViewChange">
          <i class="icon-monitor" :class="iconList[chartType]"></i>
        </span>
      </div>
    </div>
    <slot name="append"></slot>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Ref, Watch } from 'vue-property-decorator'
import {
  IOption,
  ICompareOption,
  IToolsOption,
  ChartType,
  ISearchSelectList,
  ICompareChangeType } from '../performance-type'
import DropDownMenu from './dropdown-menu.vue'
import MonitorDateRange from '../../../components/monitor-date-range/monitor-date-range.vue'
import { addListener, removeListener } from 'resize-detector'
import { getRandomId } from '../../../utils'
import { PERFORMANCE_CHART_TYPE } from '../../../constant/constant'
@Component({
  name: 'compare-panel',
  components: {
    DropDownMenu,
    MonitorDateRange
  }
})
export default class ComparePanel extends Vue {
  @Ref('panelWrap') refPanelWrap: HTMLDivElement
  @Ref('timeSelect') refTimeSelect: Vue
  @Ref('targetSelect') refTargetSelect: Vue
  @Prop({ default: 1 }) readonly chartType: ChartType
  @Prop({ default: true }) readonly hasViewChangeIcon: boolean
  // 维度列表
  @Prop({
    default: () => [
      {
        id: 'none',
        name: window.i18n.t('不对比')
      },
      {
        id: 'target',
        name: window.i18n.t('目标对比')
      },
      {
        id: 'time',
        name: window.i18n.t('时间对比')
      }
    ],
    type: Array
  }) readonly compareList: IOption[]
  // 对比时间list
  @Prop({
    default: () => [
      {
        id: '1h',
        name: window.i18n.t('1小时前')
      },
      {
        id: '1d',
        name: window.i18n.t('昨天')
      },
      {
        id: '1w',
        name: window.i18n.t('上周')
      },
      {
        id: '1M',
        name: window.i18n.t('一月前')
      }
    ],
    type: Array
  }) readonly timeshiftList: IOption[]
  // 目标对比 ip列表
  @Prop({ default() {
    return []
  } }) readonly targetList:  IOption[]
  // 工具栏时间间隔列表
  @Prop({ default() {
    return [
      {
        name: this.$t('1小时'),
        value: 1 * 60 * 60 * 1000
      },
      {
        name: this.$t('1天'),
        value: 24 * 60 * 60 * 1000
      },
      {
        name: this.$t('7天'),
        value: 168 * 60 * 60 * 1000
      },
      {
        name: this.$t('1个月'),
        value: 720 * 60 * 60 * 1000
      }
    ]
  } }) readonly timerangeList:  IOption[]

  // 工具栏刷新时间间隔列表
  @Prop({ default() {
    return [ // 刷新间隔列表
      {
        name: window.i18n.t('刷新'),
        id: -1
      },
      {
        name: '1m',
        id: 60 * 1000
      },
      {
        name: '5m',
        id: 5 * 60 * 1000
      },
      {
        name: '15m',
        id: 15 * 60 * 1000
      },
      {
        name: '30m',
        id: 30 * 60 * 1000
      },
      {
        name: '1h',
        id: 60 * 60 * 1000
      },
      {
        name: '2h',
        id: 60 * 2 * 60 * 1000
      },
      {
        name: '1d',
        id: 60 * 24 * 60 * 1000
      }
    ]
  } }) readonly refleshList:  IOption[]
  // 是否需要拆分视图
  @Prop({ default: true })
  needSplit: boolean

  @Prop({ required: true }) value: {compare: ICompareOption; tools: IToolsOption}

  // 是否需要目标选择输入
  @Prop({ default: true }) needTarget
  @Prop({ default: false, type: Boolean }) needSearchSelect: boolean
  @Prop({ default: () => [], type: Array })
  searchSelectList: ISearchSelectList
  @Prop({ type: Object }) readonly curHost
  searchSelectActive = false
  // 对比数据
  compare: ICompareOption = { type: 'none', value: '' }
  // 工具数据
  tools: IToolsOption = { timeRange: 1 * 60 * 60 * 1000, refleshInterval: -1, searchValue: [] }
  resizeHandler: Function = null
  showText = false
  iconList = ['icon-mc-one-column', 'icon-mc-two-column', 'icon-mc-three-column']
  custom = {
    show: false,
    value: ''
  }

  get dateRangeKey() {
    let key = 'dateRangeKey'
    if (this.tools.timeRange && this.timeshiftList) {
      key = getRandomId()
    }
    return key
  }

  get handleSelectorActive() {
    let flag = false
    if (this.tools.searchValue.length) {
      flag = true
    }
    return flag
  }

  get showClearBtn() {
    return this.refTargetSelect.unmatchedCount !== this.targetList.length
  }

  @Watch('curHost', { deep: true })
  handleCurHost(v) {
    if (v !== null) {
      // 默认为主机
      let id = `${v.cloudId}-${v.ip}`
      if (v.type && v.type === 'SERVICE') {
        // 实例
        id = v.value
      } else if (v.type && v.type === 'custom') {
        // 自定义指标
        id = v.ip
      }
      const index = this.compare.value.indexOf(id)
      if (Array.isArray(this.compare.value) && index !== -1) {
        this.compare.value.splice(index, 1)
      }
    }
  }

  @Watch('value', { immediate: true, deep: true })
  onValueChange(v) {
    this.compare = { ...v.compare }
    this.tools = { ...v.tools }
  }

  mounted() {
    this.resizeHandler = () => {
      const rect = this.refPanelWrap.getBoundingClientRect()
      this.showText = rect.width > 750
    }
    this.resizeHandler()
    addListener(this.refPanelWrap, this.resizeHandler)
  }
  beforeDestroy() {
    removeListener(this.refPanelWrap, this.resizeHandler)
  }
  @Emit('change')
  handleValueChange(type: ICompareChangeType) {
    return {
      compare: { ...this.compare },
      tools: { ...this.tools },
      type
    }
  }
  @Emit('chart-change')
  handleViewChange() {
    localStorage.setItem(PERFORMANCE_CHART_TYPE, String((this.chartType + 1) % 3))
    return (this.chartType + 1) % 3
  }

  handleAddCustomTime() {
    const regular = /^([1-9][0-9]*)+(m|h|d|w|M|y)$/
    if (regular.test(this.custom.value.trim())) {
      (this.compare.value as string[]).push(this.custom.value)
      this.handleValueChange('compare')
      this.custom.show = false
      this.handleAddCustomTimeEmit()
    } else {
      this.$bkMessage({
        theme: 'warning',
        message: this.$t('请按照提示输入'),
        offsetY: 40
      })
    }
  }

  @Emit('add-timeshift-option')
  handleAddCustomTimeEmit() {
    return this.custom.value
  }
  // 选择时间间隔触发
  handleTimeRangeChange() {
    this.handleValueChange('timeRange')
  }
  handleSelectToggle(v: boolean) {
    if (v) {
      this?.refTimeSelect?.$refs?.selectDropdown?.instance?.set({ zIndex: 9999 })
      this?.refTargetSelect?.$refs?.selectDropdown?.instance?.set({ zIndex: 9999 })
    }
  }
  // 设置自定义时间间隔触发
  handleAddOption(params) {
    this.$emit('add-timerange-option', params)
    this.tools.timeRange = params.value
    this.handleValueChange('timeRange')
  }
  async handleChangeType(type) {
    if (type === 'none') this.compare.value = this.needSplit
    else if (type === 'time') {
      this.compare.value = ['1h']
    } else if (type === 'target') this.compare.value = ''
    this.handleValueChange('compare')
  }
  handleSplit() {
    this.compare.value = !this.compare.value
    this.handleValueChange('compare')
  }
  handleCustomClick() {
    this.custom.show = true
    this.custom.value = ''
  }

  handleSearchSelectChange(val) {
    this.tools.searchValue = val
    this.handleValueChange('search')
  }

  deleteSelected() {
    this.$set(this.compare, 'value', [])
  }
}
</script>
<style lang="scss" scoped>
/deep/ .bk-dropdown-menu {
  width: 100%;
}
.compare-panel {
  display: flex;
  height: 42px;
  border-bottom: 1px solid #f0f1f5;
  // box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
  background: #fff;
  .panel-wrap {
    flex: 1;
    height: 100%;
    display: flex;
    .tool-icon {
      width: 48px;
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      color: #979ba5;
      cursor: pointer;
      border-left: 1px solid #f0f1f5;
    }
    &-left {
      flex-basis: 124px;
      width: 124px;
    }
    &-center {
      display: flex;
      flex: 1;
      border-left: 1px solid #f0f1f5;
      padding-left: 6px;
      position: relative;
      .split-btn-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-left: -6px;
        width: 48px;
        height: 100%;
        border-right: 1px solid #f0f1f5;
        .icon-monitor {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 24px;
          height: 24px;
          border-radius: 2px;
          font-size: 17px;
          cursor: pointer;
        }
        .icon-active {
          color: #3a84ff;
          background-color: #e1ecff;
        }
      }
      .time-select {
        height: 32px;
        margin: 4px 5px 0 0;
        flex: 1;
        max-width: 200px;
        &-custom {
          display: flex;
          align-items: center;
          height: 32px;
        }
      }
      .target-select {
        background: white;
        z-index: 99;
        margin: 4px 5px 0 0;
        min-width: 110px;
        /deep/ .bk-select {
          border: 0;
          &.is-focus {
            box-shadow: none;
          }
        }
        /deep/ .bk-select-tag-container .bk-select-tag {
          max-width: none;
        }
      }
      .margin-left-auto {
        margin-left: auto;
      }
      .search-selector-wrapper {
        display: flex;
        align-items: center;
        min-width: 78px;
        padding-right: 11px;
        border-left: 1px solid #f0f1f5;
        /deep/.search-select {
          flex: 1;
          .bk-search-select {
            border: 0px;
            .icon-search {
              color: #c4c6cc;
              font-size: 16px;
              padding-left: 18px;
              margin-bottom: 2px;
            }
            .search-input-input {
              padding: 0 3px;
              padding-left: 1px;
              min-width: 0;
            }
            .search-nextfix-icon {
              display: none;
            }
          }
        }
      }
      .search-select-active {
        min-width: 240px;
      }
      .time-shift {
        flex-shrink: 0;
        min-width: 100px;
        // margin-left: auto;
        border-left: 1px solid #f0f1f5;
        display: flex;
        align-items: center;
        height: 42px;
        &-select {
          width: 100%;
        }
        /deep/ .date {
          border: 0;
          &.is-focus {
            box-shadow: none;
          }
        }
      }
      .time-interval {
        // width: 100px;
        border-left: 1px solid #f0f1f5;
      }
      .center-maintag {
        margin-top: 8px;
        padding: 0 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 74px;
        height: 22px;
        background: #f0f1f5;
        border-radius: 2px;
        font-weight: 700;
        color: #63656e;
        .tag {
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }
      }
    }
  }
}
.target-select {
  &-clear {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    padding: 0 16px;
    &:before {
      content: "";
      margin-top: 4px;
      height: 1px;
      padding: 0 8px;
      width: 100%;
      background: #f0f1f5;
    }
    .clear-btn {
      color: #3a84ff;
      cursor: pointer;
    }
  }
}
.time-select {
  &-custom {
    display: flex;
    align-items: center;
    height: 32px;
    padding: 0 16px;
    position: relative;
    margin-bottom: 6px;
    /deep/ .bk-input-small {
      display: flex;
      align-items: center;
    }
    /deep/ .bk-tooltip-ref {
      margin-left: -20px;
    }
    &:hover {
      cursor: pointer;
    }
    & .custom-text:hover,
    /deep/ & .bk-tooltip-ref:hover {
      color: #3a84ff;
    }
    .help-icon {
      position: absolute;
      right: 20px;
      height: 14px;
      width: 14px;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    /deep/ .tippy-active {
      color: #3a84ff;
    }
  }
}
</style>
