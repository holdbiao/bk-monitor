<template>
  <div class="time-period-wrap">
    <bk-radio-group
      class="radio-group"
      v-model="typeValue"
      @change="getValue">
      <bk-radio
        class="radio-item"
        v-for="(item, index) in radioMap"
        :key="index"
        :value="item.id">
        {{item.name}}
      </bk-radio>
    </bk-radio-group>
    <div class="time-select">
      <!-- 每周几 -->
      <bk-select
        v-if="typeValue === 3"
        class="week"
        v-model="week"
        :clearable="false"
        multiple
        key="week-selector"
        style="width: 200px;"
        @change="getValue">
        <bk-option
          v-for="item in weekList"
          :key="'week' + item.id"
          v-bind="item">
        </bk-option>
      </bk-select>
      <!-- 每月几号 -->
      <bk-select
        v-if="typeValue === 4"
        class="month"
        v-model="month"
        multiple
        key="month-selector"
        :clearable="false"
        style="width: 200px;"
        @change="getValue">
        <bk-option
          v-for="item in 31"
          :key="item"
          :id="item"
          :name="item + '号'">
        </bk-option>
      </bk-select>
      <!-- 时间选择 -->
      <bk-time-picker
        v-if="[2, 3, 4].includes(typeValue)"
        style="width: 168px;"
        v-model="dayTime"
        :clearable="false"
        :placeholder="'选择时间'"
        @change="v => getValue(v, 'time')">
      </bk-time-picker>
      <!-- 是否包含周末 -->
      <!-- <bk-checkbox-group
        style="width: 168px;"
        v-if="typeValue === 2"
        v-model="includeWeekend"
        @change="getValue"> -->
      <bk-checkbox
        v-model="includeWeekend"
        @change="getValue"
        v-if="typeValue === 2">{{$t('包含周末')}}</bk-checkbox>
      <!-- </bk-checkbox-group> -->
      <!-- 仅一次 -->
      <bk-date-picker
        v-if="typeValue === 1"
        style="width: 168px;"
        v-model="onceTime"
        :clearable="false"
        :type="'datetime'"
        :options="datePickerOptions"
        @change="v => getValue(v, 'datetime')">
      </bk-date-picker>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Watch, Model, Emit } from 'vue-property-decorator'
import { IRadioMap, ITimePeriodValue, EType } from '../types'
import moment from 'moment'
/**
 * 时间周期组件
 */
@Component({
  name: 'time-period'
})
export default class TimePeriod extends Vue {
  @Model('updateValue', { default: () => ({
    type: 2,
    runTime: '09:30:20',
    dayList: [1],
    weekList: [1]
  }), type: Object }) value: ITimePeriodValue

  // 时间数据
  private typeValue: EType = 2
  private weekList: IRadioMap[] = [
    { name: window.i18n.t('星期一'), id: 1 },
    { name: window.i18n.t('星期二'), id: 2 },
    { name: window.i18n.t('星期三'), id: 3 },
    { name: window.i18n.t('星期四'), id: 4 },
    { name: window.i18n.t('星期五'), id: 5 },
    { name: window.i18n.t('星期六'), id: 6 },
    { name: window.i18n.t('星期日'), id: 7 }
  ]
  private week: number[] = [1]
  private month: number[] = [1]
  //   private dayTime: Date | string = new Date()
  private dayTime: Date | string = moment(new Date()).format('HH:mm:ss')

  private includeWeekend = true
  private onceTime: Date = new Date()

  // datePicker配置
  private datePickerOptions: any = {
    disabledDate: (v: string) => {
      const item: number = +new Date(v)
      const cur: Date = new Date()
      const start: number = +new Date(cur.getFullYear(), 0, 1, 0, 0, 0, 0)
      const end: number = +new Date(cur.getFullYear(), 11, 31, 23, 59, 59, 0)
      return !(item >= start && item <= end)
    }
  }

  // 时间类型选择
  private radioMap: IRadioMap[] = [
    { id: 2, name: window.i18n.t('按天') },
    { id: 3, name: window.i18n.t('按周') },
    { id: 4, name: window.i18n.t('按月') },
    { id: 1, name: window.i18n.t('仅一次') }
  ]

  // 值更新
  @Watch('value', { immediate: true })
  valueChage(val: ITimePeriodValue, oldVal: ITimePeriodValue): void {
    if (JSON.stringify(val) !== JSON.stringify(oldVal)) {
      // 回显
      this.displayBack(val)
      this.getValue()
    }
  }

  /**
     * 数据回显展示
     * @params val 外部传入数据
     */
  private displayBack(val: ITimePeriodValue) {
    if (!val) return
    const { type, runTime, weekList, dayList } = val
    this.typeValue = type
    if ([2, 3, 4].includes(type)) {
      this.dayTime = runTime
    }
    switch (type) {
      case 2: // 按天
        this.includeWeekend = [6, 7].every(item => weekList.includes(item))
        break
      case 3: // 按周
        this.week = weekList
        break
      case 4: // 按月
        this.month = dayList
        break
      case 1: // 仅一次
        this.onceTime = new Date(runTime)
        break
    }
  }

  /**
     * 双向绑定的值更新
     */
  @Emit('updateValue')
  private getValue(v?, type?: 'time' | 'datetime'): ITimePeriodValue {
    const value: ITimePeriodValue = {
      type: this.typeValue,
      runTime: '',
      dayList: [],
      weekList: []
    }
    if ([2, 3, 4].includes(this.typeValue)) (value.runTime = `${type === 'time' ? v : this.dayTime}`)
    switch (this.typeValue) {
      case 1: // 仅一次
        value.runTime = moment(type === 'datetime' ? v : this.onceTime).format('YYYY-MM-DD HH:mm:ss')
        break
      case 2: // 按天
        // value.runTime = this.dayTime
        value.weekList = this.includeWeekend ? [6, 7] : []
        break
      case 3: // 按周
        value.weekList = this.week
        break
      case 4: // 按月
        value.dayList = this.month
        break
    }
    return value
  }
}
</script>

<style lang="scss" scoped>
.time-period-wrap {
  .radio-group {
    .radio-item {
      &:not(:last-child) {
        margin-right: 54px;
      }
    }
  }
  .time-select {
    display: flex;
    align-items: center;
    margin-top: 5px;
    .week,
    .month {
      display: inline-block;
    }
    &>:not(:last-child) {
      margin-right: 8px;
    }
  }
}
</style>
