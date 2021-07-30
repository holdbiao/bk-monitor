<template>
  <div :class="['monitor-date-range-container',offset === 'left' ? 'offset-left' : 'offset-right']">
    <div class="monitor-date-range">
      <div :class="['date', { 'is-focus': isFoucs }]"
           tabindex="0"
           ref="monitorDateRange"
           @click="handleFocus"
           @blur="handleBlur">
        <span v-if="icon" :class="[icon, 'icon-monitor', 'left-icon', { 'mr5': showName }]"></span>
        <span class="text" v-show="showName">{{date}}</span>
        <span class="bk-select-angle bk-icon icon-angle-down"></span>
      </div>
      <transition name="fade">
        <div class="date-panel" v-show="showDropdown" :style="{ minWidth: hasCustomDate ? '290px' : dropdownWidth + 'px', zIndex }">
          <ul class="option-list">
            <li v-for="(option, index) in options" :key="index" @click="handleSelect(option)" class="item">{{option.name}}</li>
          </ul>
          <div @mousedown.stop.prevent="handleCustom" class="option-footer">{{ $t('自定义') }}</div>
        </div>
      </transition>
    </div>
    <bk-date-picker
      :style="{ zIndex }"
      class="monitor-date"
      :split-panels="false"
      ref="bkDateRange"
      :value="initDateTimeRange"
      :placeholder="$t('选择日期时间范围')"
      :type="'datetimerange'"
      @change="handleDateChange"
      @pick-success="handleConfirm">
    </bk-date-picker>
  </div>
</template>
<script>
import moment from 'moment'
export default {
  name: 'MonitorDateRange',
  model: {
    prop: 'value',
    event: 'change'
  },
  props: {
    offset: {
      type: String,
      default: 'left'
    },
    options: {
      type: Array,
      default: () => []
    },
    icon: {
      type: String,
      default: ''
    },
    showName: {
      type: Boolean,
      default: true
    },
    dropdownWidth: {
      type: [Number, String],
      default: '84'
    },
    value: [Number, String, Array],
    zIndex: {
      type: Number,
      default: 10
    }
  },
  data() {
    return {
      date: '',
      isFoucs: false,
      showDropdown: false,
      initDateTimeRange: [moment().subtract(1, 'hours')
        .format(), moment().format()]
    }
  },
  computed: {
    hasCustomDate() {
      return this.options.some(set => set.name === set.value)
    }
  },
  watch: {
    value() {
      this.handleSetDate()
    }
  },
  mounted() {
    if (this.value) {
      this.handleSetDate()
    }
  },
  methods: {
    handleSetDate() {
      const value = Array.isArray(this.value) ? `${this.value[0]} -- ${this.value[1]}` : this.value
      this.date = value
      this.options.forEach((item) => {
        if (item.value === value) {
          this.date = item.name
        }
      })
    },
    handleFocus() {
      this.isFoucs = !this.isFoucs
      this.showDropdown = !this.showDropdown
    },
    handleBlur() {
      this.showDropdown = false
      this.isFoucs = false
      this.$refs.bkDateRange.visible = false
    },
    // 点击自定义
    handleCustom() {
      setTimeout(() => {
        this.$refs.bkDateRange.visible = true
      })
    },
    handleSelect(v) {
      this.date = v.name
      this.$emit('change', v.value)
    },
    handleDateChange(v) {
      this.initDateTimeRange = v
    },
    handleConfirm() {
      // eslint-disable-next-line vue/max-len
      this.date = `${moment(this.initDateTimeRange[0]).format('YYYY-MM-DD HH:mm:ss')} -- ${moment(this.initDateTimeRange[1]).format('YYYY-MM-DD HH:mm:ss')}`
      if (!this.options.some(set => set.value === this.date)) { // 重复的不新增
        this.$emit('add-option', { name: this.date, value: this.date })
      }
      this.$refs.bkDateRange.visible = false
      this.$refs.monitorDateRange.blur()
      this.$emit('change', this.initDateTimeRange)
    }
  }
}
</script>
<style lang="scss" scoped>
.monitor-date-range-container {
  position: relative;
  .monitor-date-range {
    position: relative;
    .date-icon {
      font-size: 14px;
    }
    .date {
      position: relative;
      height: 32px;
      line-height: 32px;
      border-radius: 2px;
      padding: 0 36px 0 10px;
      border: 1px solid #c4c6cc;
      background: #fff;
      color: #63656e;
      cursor: pointer;
      display: flex;
      align-items: center;
      .date-icon {
        margin-right: 5px;
      }
      .left-icon {
        font-size: 14px;
      }
      .mr5 {
        margin-right: 5px;
      }
      &.is-focus {
        border-color: #3a84ff;
        box-shadow: 0 0 4px rgba(58,132,255,.4);
      }
      .icon-angle-down {
        position: absolute;
        right: 12px;
        top: 5px;
        font-size: 20px;
      }
    }
    .date-panel {
      position: absolute;
      top: 40px;
      right: 0;
      border: 1px solid #dcdee5;
      border-radius: 2px;
      line-height: 32px;
      background: #fff;
      color: #63656e;
      overflow: hidden;
      z-index: 10;
      .option-list {
        display: flex;
        flex-direction: column;
        padding: 6px 0;
        max-height: 230px;
        overflow: auto;
        .item {
          padding: 0 16px;
          &:hover {
            cursor: pointer;
            background-color: #f4f6fa;
            color: #3a84ff;
          }
          &.item-active {
            background-color: #f4f6fa;
            color: #3a84ff;
          }
        }
      }
      .option-footer {
        height: 32px;
        padding: 0 16px;
        display: flex;
        align-items: center;
        cursor: pointer;
        background-color: #fafbfd;
        border-top: 1px solid #dcdee5;
      }
    }
  }
  .fade-enter-active,
  .fade-leave-active {
    transition: height .6s;
  }
  .date-enter,
  .date-leave {
    transition: .6s cubic-bezier(.4, 0, .2, 1);
    opacity: 0;
  }
}
.offset-left {
  /deep/ .bk-date-picker.monitor-date {
    position: absolute;
    right: 0;
    width: 0;
    .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      right: 0px !important;

      /* stylelint-disable-next-line declaration-no-important */
      left: inherit !important;

      /* stylelint-disable-next-line declaration-no-important */
      top: 20px !important;
      padding-bottom: 0;
    }
    .bk-date-picker-rel {
      display: none;
    }
    .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      right: 0px !important;

      /* stylelint-disable-next-line declaration-no-important */
      left: inherit !important;

      /* stylelint-disable-next-line declaration-no-important */
      top: 20px !important;
    }
  }
}
.offset-right {
  /deep/ .bk-date-picker.monitor-date {
    position: absolute;
    left: 0;
    width: 0;
    .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      left: 0px !important;

      /* stylelint-disable-next-line declaration-no-important */
      left: inherit !important;

      /* stylelint-disable-next-line declaration-no-important */
      top: 20px !important;
      padding-bottom: 0;
    }
    .bk-date-picker-rel {
      display: none;
    }
    .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      left: 0px !important;

      /* stylelint-disable-next-line declaration-no-important */
      left: inherit !important;

      /* stylelint-disable-next-line declaration-no-important */
      top: 20px !important;
    }
  }
}
</style>

