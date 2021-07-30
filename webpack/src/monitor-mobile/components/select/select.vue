<template>
  <transition name="fade">
    <div
      v-if="show"
      v-transfer-dom="'.bk-mobile-landscape'"
      class="bk-select">
      <!-- select内容 -->
      <div class="main">
        <!-- select 标题 -->
        <div
          v-if="title"
          class="title">
          {{ title }}
        </div>
        <!-- options picker -->
        <slot>
          <van-picker
            :columns="columns"
            :default-index="defaultIndex"
            @change="handlePickerChange" />
        </slot>
        <!-- 确定/取消 操作 -->
        <div class="contral-btn">
          <span
            class="cancel"
            @click="handleSelectCancel">
            {{ $t('取消') }}
          </span>
          <span class="line" />
          <span
            class="confirm"
            @click="handleSelectConfirm">
            {{ $t('确定') }}
          </span>
        </div>
      </div>
    </div>
  </transition>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Model } from 'vue-property-decorator'
import { Picker } from 'vant'
import transferDom from '../../directives/transform-dom'

type ValueType = string | number

interface IOptions {
  text: string;
  value: ValueType;
}
interface ISelected {
  index: number;
  selected: IOptions;
}

@Component({
  name: 'bk-select',
  components: {
    [Picker.name]: Picker
  },
  directives: {
    transferDom
  }
})
export default class BkSelect extends Vue {
  // 自定义model
  @Model('update', { type: [String, Number, Array] }) readonly value!: ValueType

  // select 标题
  @Prop({ default: '' }) private title: string

  // select options数据项
  @Prop({
    default: () => [
      {
        text: 'no data',
        value: 0
      }
    ]
  })
  private columns: IOptions[]

  // 是否显示select组件
  @Prop({ default: false }) private show: boolean

  // select默认选中的索引
  get defaultIndex() {
    return this.columns.findIndex(item => item.value === this.value)
  }

  // 当前选中的值
  private selectedValues: ValueType = this.value

  // 取消事件
  @Emit('cancel')
  handleSelectCancel() {
    this.handleHideSelect()
    return this.value
  }

  // 确定事件
  @Emit('confirm')
  @Emit('update')
  handleSelectConfirm() {
    this.handleHideSelect()
    return this.selectedValues
  }

  handlePickerChange(picker: Picker, selected: IOptions, index: number) {
    this.selectedValues = selected.value
    this.$emit('change', picker, selected, index)
  }

  @Emit('change')
  @Emit('update:show')
  handleHideSelect() {
    return false
  }
}
</script>
<style lang="scss" scoped>
    @import '../../static/scss/variate.scss';
    @import '../../static/scss/mixin.scss';

    .bk-select {
        @include overlay;
        z-index: 9999;
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
