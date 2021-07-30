<template>
  <div class="date-notice-component">
    <div class="set-shield-config-item">
      <div class="item-label item-required"> {{ $t('屏蔽周期') }} </div>
      <div class="item-container">
        <bk-radio-group v-model="shieldCycle.value">
          <bk-radio v-for="(item, index) in shieldCycle.list" :key="index" :value="item.value">{{ item.label }}</bk-radio>
        </bk-radio-group>
      </div>
    </div>
    <div class="set-shield-config-item" :class="{ 'verify-show': dataVerify }">
      <div class="item-label item-required"> {{ $t('时间范围') }} </div>
      <div class="item-container">
        <!-- 单次 -->
        <template v-if="shieldCycle.value === 'single'">
          <div class="date-wrapper">
            <bk-date-picker
              :editable="true"
              :options="datePicker.options"
              v-model="noticeDate.single.range"
              type="datetimerange"
              format="yyyy-MM-dd HH:mm:ss"
              @change="validateDateRange"
              :placeholder="$t('请选择时间范围')">
            </bk-date-picker>
            <span v-if="shieldCycle.value === 'single' && !hasDateRange" class="error-message">{{ $t('请选择时间范围') }}</span>
            <span v-else class="date-scope-desc">{{ $t('屏蔽时间范围最大上限半年') }}</span>
          </div>
        </template>
        <!-- 每天 -->
        <template v-else-if="shieldCycle.value === 'day'">
          <div class="date-wrapper">
            <bk-time-picker v-model="noticeDate.day.range" type="timerange" @change="validateScope" :placeholder="$t('请选择时间范围')" allow-cross-day></bk-time-picker>
            <span v-show="shieldCycle.value !== 'single' && !hasTimeRange" class="error-message"> {{ $t('请选择时间范围') }} </span>
          </div>
        </template>
        <!-- 每周 -->
        <template v-else-if="shieldCycle.value === 'week'">
          <div class="date-wrapper">
            <bk-select :multiple="true" :value="noticeDate.week.list" @change="handleSelectWeek" :placeholder="$t('请选择星期范围')">
              <bk-option v-for="(item, index) in week.list" :key="index" :name="item.name" :id="item.id"></bk-option>
            </bk-select>
            <span v-show="!hasWeekList" class="error-message"> {{ $t('请选择每星期范围') }} </span>
          </div>
          <div class="date-wrapper">
            <bk-time-picker v-model="noticeDate.week.range" type="timerange" @change="validateScope" :placeholder="$t('请选择时间范围')" allow-cross-day></bk-time-picker>
            <span v-show="!hasTimeRange" class="error-message"> {{ $t('请选择时间范围') }} </span>
          </div>
        </template>
        <!-- 每月 -->
        <template v-else-if="shieldCycle.value === 'month'">
          <div class="date-wrapper">
            <div class="day-picker" ref="dayList" @click="handlePopover($event)">
              <span class="list" v-if="noticeDate.month.list.length">{{noticeDate.month.list.join('、')}}</span>
              <span class="list placeholder" v-else> {{ $t('请选择每月时间范围') }} </span>
              <i class="bk-icon icon-angle-down" :class="{ 'up-arrow': !!popoverInstances }"></i>
              <i v-if="noticeDate.month.list.length" @click="handleClearMonthList" class="bk-select-clear bk-icon icon-close"></i>
            </div>
            <span class="error-message" v-show="!hasMonthList"> {{ $t('请选择每月时间范围') }} </span>
          </div>
          <div class="date-wrapper">
            <bk-time-picker v-model="noticeDate.month.range" type="timerange" @change="validateScope" :placeholder="$t('请选择时间范围')" allow-cross-day></bk-time-picker>
            <span v-show="!hasTimeRange" class="error-message"> {{ $t('请选择时间范围') }} </span>
          </div>
        </template>
      </div>
    </div>
    <div class="set-shield-config-item date-range verify-show" v-if="shieldCycle.value !== 'single'">
      <div class="item-label item-required"> {{ $t('日期范围') }} </div>
      <div class="item-container">
        <bk-date-picker :key="shieldCycle.value" v-model="dateRange" :options="datePicker.options" type="daterange" format="yyyy-MM-dd" @change="validateDateRange" :placeholder="$t('请选择日期范围')"></bk-date-picker>
        <span v-if="!hasDateRange" class="error-message"> {{ $t('请选择日期范围') }} </span>
        <span v-else class="date-scope-desc"> {{ $t('屏蔽时间范围最大上限半年') }} </span>
      </div>
    </div>
    <!-- popover -->
    <div v-show="false">
      <ul ref="dayPicker" class="date-list-wrapper">
        <li
          class="item"
          :class="{ 'active': item.active }"
          @click.stop="handleSelectDate(item)"
          v-for="(item, index) in datePicker.list" :key="index">
          <span>{{ item.value }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
<script>
import moment from 'moment'
export default {
  name: 'alarm-shield-date',
  data() {
    const defaultData = this.generationDefaultData()
    return {
      ...defaultData,
      hasTimeRange: true,
      hasDateRange: true,
      hasWeekList: true,
      hasMonthList: true,
      popoverInstances: null,
      week: {
        list: [
          { name: this.$t('星期一'), id: 1 },
          { name: this.$t('星期二'), id: 2 },
          { name: this.$t('星期三'), id: 3 },
          { name: this.$t('星期四'), id: 4 },
          { name: this.$t('星期五'), id: 5 },
          { name: this.$t('星期六'), id: 6 },
          { name: this.$t('星期日'), id: 7 }
        ]
      }
    }
  },
  computed: {
    dataVerify() {
      return !this.hasTimeRange || !this.hasDateRange || !this.hasWeekList || !this.hasMonthList
    }
  },
  watch: {
    'shieldCycle.value'() {
      this.hasTimeRange = true
      this.hasDateRange = true
      this.hasWeekList = true
      this.hasMonthList = true
    }
  },
  activated() {
    this.handleSetDefaultData()
    for (let i = 1; i < 32; i++) {
      this.datePicker.list.push({ value: i, active: false })
    }
  },
  methods: {
    generationDefaultData() {
      return {
        datePicker: {
          list: [],
          values: new Set(),
          options: {
            disabledDate(date) {
              return date && (date.valueOf() < Date.now() - 8.64e7 || date.valueOf() > Date.now() + (8.64e7 * 181))
            }
          }
        },
        shieldCycle: {
          list: [
            { label: this.$t('单次'), value: 'single' },
            { label: this.$t('每天'), value: 'day' },
            { label: this.$t('每周'), value: 'week' },
            { label: this.$t('每月'), value: 'month' }
          ],
          value: 'single'
        },
        dateRange: [],
        noticeDate: {
          single: {
            list: [],
            range: []
          },
          day: {
            list: [],
            range: []
          },
          week: {
            list: [],
            range: []
          },
          month: {
            list: [],
            range: []
          }
        }
      }
    },
    handlePopover() {
      this.$nextTick(() => {
        this.popoverInstances = this.$bkPopover(this.$refs.dayList, {
          content: this.$refs.dayPicker,
          trigger: 'manual',
          arrow: false,
          placement: 'bottom-start',
          theme: 'light common-monitor',
          maxWidth: 280,
          distance: 5,
          duration: [275, 0],
          interactive: true,
          followCursor: false,
          flip: true,
          flipBehavior: ['bottom', 'top'],
          flipOnUpdate: true,
          onHidden: () => {
            this.popoverInstances.hide(0)
            this.popoverInstances.destroy()
            this.popoverInstances = null
          }
        })
        this.popoverInstances.show()
      })
    },
    handleClearMonthList() {
      this.noticeDate.month.list = []
      this.datePicker.values = new Set()
      this.datePicker.list.forEach((item) => {
        item.active = false
      })
    },
    // 选择每周的时候触发，勾选的值会按升序排列
    handleSelectWeek(v) {
      this.noticeDate.week.list = JSON.parse(JSON.stringify(v)).sort((a, b) => a - b)
      this.validateList('week')
    },
    // 选择每月的时候触发，勾选的值会按升序排列
    handleSelectDate(item) {
      item.active = !item.active
      if (this.datePicker.values.has(item.value)) {
        this.datePicker.values.delete(item.value)
      } else {
        this.datePicker.values.add(item.value)
      }
      this.noticeDate.month.list = Array.from(this.datePicker.values).sort((a, b) => a - b)
      this.validateList('month')
    },
    // 初始化数据
    handleSetDefaultData() {
      const defaultData = this.generationDefaultData()
      Object.keys(defaultData).forEach((key) => {
        this[key] = defaultData[key]
      })
    },
    validateDateRange(val) {
      this.hasDateRange = !!val.join('')
      const startTime = moment(this.noticeDate.single.range[0]).format('YYYY-MM-DD HH:mm:ss')
      const endTime = moment(this.noticeDate.single.range[1]).format('YYYY-MM-DD HH:mm:ss')
      if (startTime.includes('00:00:00') && endTime.includes('00:00:00')) {
        this.noticeDate.single.range[1].setHours(23, 59, 59)
        this.noticeDate.single.range = [this.noticeDate.single.range[0], this.noticeDate.single.range[1]]
      }
    },
    // 时间范围的校验
    validateScope() {
      const type = this.shieldCycle.value
      this.hasTimeRange = this.noticeDate[type].range.join('')
    },
    // 每周和每月的校验 type: week month
    validateList(type) {
      if (type === 'week') {
        this.hasWeekList = this.noticeDate.week.list.join('')
      } else {
        this.hasMonthList = this.noticeDate.month.list.join('')
      }
    },
    validateValue() {
      const type = this.shieldCycle.value
      const result = this.noticeDate[type]
      if (type === 'single') {
        this.hasTimeRange = true
        this.hasDateRange = !!result.range.join('')
      } else {
        this.hasDateRange = !!this.dateRange.join('')
        this.validateScope()
      }
      if (type === 'week') {
        this.validateList('week')
        return this.hasDateRange && this.hasTimeRange && this.hasWeekList
      } if (type === 'month') {
        this.validateList('month')
        return this.hasDateRange && this.hasTimeRange && this.hasMonthList
      }
      return this.hasDateRange && this.hasTimeRange
    },
    /**
             * @description 获取组件的值
             */
    getDateData() {
      if (!this.validateValue()) return false
      const cycleMap = { single: 1, day: 2, week: 3, month: 4 }
      const params = {
        dateRange: [],
        type: cycleMap[this.shieldCycle.value],
        typeEn: this.shieldCycle.value,
        ...this.noticeDate
      }
      if (this.shieldCycle.value !== 'single') {
        params.dateRange[0] = `${moment(this.dateRange[0]).format('YYYY-MM-DD')} 00:00:00`
        params.dateRange[1] = `${moment(this.dateRange[1]).format('YYYY-MM-DD')} 23:59:59`
      }
      Object.keys(this.noticeDate).forEach((key) => {
        if (key === 'single') {
          this.noticeDate[key].range = this.noticeDate[key]
            .range
            .map(item => moment(item).format('YYYY-MM-DD HH:mm:ss'))
        }
      })
      return params
    },
    /**
             * @description 设置组件的值
             */
    setDate(v) {
      const type = v.typeEn
      this.shieldCycle.value = type
      this.noticeDate[type] = v[type]
      if (type !== 'single') {
        this.dateRange = v.dateRange
      }
      if (type === 'month') {
        const { list } = v[type]
        this.datePicker.list.forEach((item) => {
          if (list.includes(item.value)) {
            item.active = true
            this.datePicker.values.add(item.value)
          }
        })
      }
    }
  }

}
</script>
<style lang="scss" scoped>
.date-notice-component {
  .verify-show {
    /* stylelint-disable-next-line declaration-no-important */
    margin-bottom: 32px !important;
  }
  .set-shield-config-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-bottom: 20px;
    font-size: 14px;
    color: #63656e;
    &.date-range {
      margin-bottom: 20px;
    }
    .item-label {
      min-width: 110px;
      text-align: right;
      margin-right: 24px;
      position: relative;
      flex: 0 0;
    }
    .item-required::after {
      content: "*";
      color: red;
      position: absolute;
      top: 2px;
      right: -9px;
    }
    .item-container {
      display: flex;
      position: relative;
      .scope-item {
        width: 168px;
      }
      .date-wrapper {
        position: relative;
      }
      .bk-form-radio {
        margin-right: 32px;
        /deep/ input[type=radio] {
          margin-right: 8px;
        }
      }
      .bk-date-picker {
        margin-right: 10px;
        width: 413px;
        // /deep/ .bk-date-picker-editor {
        //     padding-left: 12px;
        // }
      }
      .day-picker {
        position: relative;
        display: flex;
        padding: 0 16px 0 12px;
        margin-right: 10px;
        width: 413px;
        height: 32px;
        border: 1px solid #c4c6cc;
        border-radius: 2px;
        line-height: 30px;
        font-size: 12px;
        color: #63656e;
        cursor: pointer;
        .bk-icon {
          position: absolute;
          right: 12px;
          top: 8px;
          transition: transform .3s cubic-bezier(.4,0,.2,1),-webkit-transform .3s cubic-bezier(.4,0,.2,1);
        }
        .bk-select-clear {
          display: none;
          position: absolute;
          right: 11px;
          top: 8px;
          width: 14px;
          height: 14px;
          line-height: 14px;
          background-color: #c4c6cc;
          border-radius: 50%;
          text-align: center;
          font-size: 12px;
          color: #fff;
          z-index: 100;
          &::before {
            display: block;
            transform: scale(.7)
          }
          &:hover {
            background-color: #979ba5;
          }
        }
        .up-arrow {
          transform: rotate(-180deg);
        }
        .placeholder {
          color: #c4c6cc;
          font-size: 12px;
        }
        .list {
          overflow: hidden;
        }
        &:hover {
          .bk-select-clear {
            display: inline-block;
          }
        }
      }
      .date-scope-desc {
        position: absolute;
        left: 0;
        top: 36px;
        color: #c4c6cc;
        font-size: 12px;
      }
      .error-message {
        position: absolute;
        left: 0;
        top: 36px;
        color: #ea3636;
        font-size: 12px;
      }
    }
    .bk-select {
      margin-right: 10px;
      width: 413px;
    }
  }
}
.date-list-wrapper {
  display: flex;
  flex-wrap: wrap;
  margin: 0;
  width: 254px;
  box-sizing: border-box;
  padding: 10px 16px 15px 12px;
  border-radius: 2px;
  border: 1px solid #c4c6cc;
  .item {
    display: inline-block;
    list-style: none;
    height: 32px;
    width: 32px;
    line-height: 32px;
    text-align: center;
    cursor: pointer;
    color: #63656e;
    font-size: 12px;
    &:hover {
      background: #f0f1f5;
    }
  }
  .active {
    span {
      display: inline-block;
      width: 100%;
      height: 100%;
      background-color: #3a84ff;
      color: #fff;
    }

  }
}
</style>
