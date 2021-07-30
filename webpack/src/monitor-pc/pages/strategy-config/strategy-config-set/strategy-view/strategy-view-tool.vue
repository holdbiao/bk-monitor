<template>
  <div class="tool-panel">
    <div class="panel-wrap" ref="panelWrap">
      <div class="panel-wrap-left">
        {{ $t('图表预览') }}
      </div>
      <div class="panel-wrap-center">
        <slot name="content">
          <span class="margin-left-auto"></span>
          <div class="time-shift" :style="{ minWidth: !showText ? '0' : '100px' }">
            <monitor-date-range
              icon="icon-mc-time-shift"
              class="time-shift-select"
              @add-option="handleAddOption"
              dropdown-width="96"
              v-model="timeRange"
              :options="timerangeList"
              :style="{ minWidth: showText ? '100px' : '40px' }"
              :show-name="showText"
              @change="handleValueChange('timeRange')">
            </monitor-date-range>
          </div>
          <drop-down-menu
            :show-name="showText"
            :icon="refleshInterval === -1 ? 'icon-mc-alarm-recovered' : 'icon-zidongshuaxin'"
            class="time-interval"
            v-model="refleshInterval"
            :text-active="refleshInterval !== -1"
            @on-icon-click="$emit('on-immediate-reflesh')"
            @change="handleValueChange('interval')"
            :list="refleshList">
          </drop-down-menu>
        </slot>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref, Emit, Watch } from 'vue-property-decorator'
import { IOption, ICompareChangeType } from '../../../performance/performance-type'
import DropDownMenu from '../../../performance/performance-detail/dropdown-menu.vue'
import MonitorDateRange from '../../../../components/monitor-date-range/monitor-date-range.vue'
import { addListener, removeListener } from 'resize-detector'

@Component({
  name: 'tool-panel',
  components: {
    DropDownMenu,
    MonitorDateRange
  }
})
export default class ToolPanel extends Vue {
  @Ref('panelWrap') refPanelWrap: HTMLDivElement
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

  private showText = false
  private timeRange: number | number[] = 1 * 60 * 60 * 1000
  private refleshInterval = 5 * 60 * 1000
  private resizeHandler: Function = null

  @Watch('timeRange')
  handleTimeRangeChange(range) {
    // 自定义时间默认不开启刷新，语义时间默认刷新时间为 1 分钟
    if (Array.isArray(range)) {
      this.refleshInterval = -1
      this.handleValueChange('interval')
    } else if (this.refleshInterval === -1) {
      this.refleshInterval = 5 * 60 * 1000
      this.handleValueChange('interval')
    }
  }

  @Emit('change')
  handleValueChange(type: ICompareChangeType) {
    return {
      type,
      tools: {
        timeRange: this.timeRange,
        refleshInterval: this.refleshInterval
      }
    }
  }

  mounted() {
    this.resizeHandler = () => {
      const rect = this.refPanelWrap.getBoundingClientRect()
      this.showText = rect.width > 500
    }
    this.resizeHandler()
    addListener(this.refPanelWrap, this.resizeHandler)
  }

  beforeDestroy() {
    removeListener(this.refPanelWrap, this.resizeHandler)
  }

  // 设置自定义时间间隔触发
  handleAddOption(params) {
    this.$emit('add-timerange-option', params)
    this.timeRange = params.value
    this.handleValueChange('timeRange')
  }

  handleSetTimeRange(range: number | number[]) {
    this.timeRange = range
  }
}
</script>
<style lang="scss" scoped>
/deep/ .bk-dropdown-menu {
  width: 100%;
}
.tool-panel {
  display: flex;
  height: 42px;
  border-bottom: 1px solid #f0f1f5;
  // box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
  background: #fff;
  .panel-wrap {
    flex: 1;
    height: 100%;
    display: flex;
    &-left {
      flex-basis: 124px;
      width: 124px;
      line-height: 42px;
      color: #4e4e4e;
      padding-left: 15px;
    }
    &-center {
      display: flex;
      flex: 1;
      padding-left: 6px;
      position: relative;
      .margin-left-auto {
        margin-left: auto;
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
    }
  }
}
</style>
