<template>
    <transition name="fade">
        <div
            v-if="show"
            class="bk-datetime-picker">
            <div class="main">
                <div class="title">
                    {{ title ? title : $t('选择截止时间') }}
                </div>
                <van-datetime-picker
                    ref="datetimePicker"
                    :value="value"
                    type="datetime"
                    :min-date="minDate"
                    :max-date="maxDate" />
                <div class="contral-btn">
                    <span
                        class="cancel"
                        @click="handleCancel"
                    >{{ $t('取消') }}</span>
                    <span class="line" />
                    <span
                        class="confirm"
                        @click="handleConfirm"
                    >{{ $t('确定') }}</span>
                </div>
            </div>
        </div>
    </transition>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref, Emit } from 'vue-property-decorator'
import { DatetimePicker } from 'vant'

export interface ITimeObj {
  timestamp: number;
  datetime: string;
  dateObj: Date;
}

@Component({
  name: 'bk-datetime-picker',
  components: {
    [DatetimePicker.name]: DatetimePicker
  }
})
export default class TendencyChart extends Vue {
  @Ref() readonly datetimePicker!: DatetimePicker
  // 显示状态
  @Prop({ default: false }) private show: boolean

  // 日期范围
  @Prop(Date) private minDate: Date

  @Prop(Date) private maxDate: Date

  // 当前时间
  @Prop({ default: () => new Date() }) private value: Date

  @Prop({ default: '' }) private readonly title: string

  // 处理点击确定
  @Emit('confirm')
  handleConfirm(): ITimeObj {
    const DP = this.datetimePicker.getPicker()
    // 当前选中的值
    const val = DP.getValues().map(item => parseInt(item, 10))
    const datetime = val.join('/')
    val[1] -= 1 // 注意月份从0开始
    const timeTuple = [...val] as [number, number, number, number, number]
    const timestamp = +new Date(...timeTuple)
    const timeObj = {
      timestamp,
      datetime,
      dateObj: new Date(...timeTuple)
    }
    this.handleCancel()
    return timeObj
  }

  // 点击取消
  @Emit('cancel')
  handleCancel() {
    this.$emit('update:show', false)
  }
}
</script>
<style lang="scss" scoped>
    @import '../../static/scss/variate.scss';
    .bk-datetime-picker {
        /deep/.van-datetime-picker {
            .van-picker__toolbar {
                display: none;
            }
        }
        z-index: 9999;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 1rem;
        background-color: rgba(0, 0, 0, .1);
        .main {
            position: absolute;
            left: 1rem;
            right: 1rem;
            bottom: 1rem;
            border-radius: 1rem;
            padding: 1.25rem;
            background-color: #fff;
            .title {
                line-height: 1.75rem;
                font-size: 1.25rem;
                color: #313238;
            }
            .contral-btn {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1rem;
                color: $primaryColor;
                font-size: 1.25rem;
                .line {
                    display: inline-block;
                    width: 1px;
                    height: 18px;
                    margin: 0 46px;
                    background-color: #eaebef;
                }
            }
        }

    }
    .fade-enter-active, .fade-leave-active {
        transition: opacity .3s ease-in-out;
        .main {
            transition: bottom .3s ease-in-out;
        }
    }
    .fade-enter, .fade-leave-to {
        opacity: 0;
        .main {
            bottom: -300px;
        }
    }
</style>
