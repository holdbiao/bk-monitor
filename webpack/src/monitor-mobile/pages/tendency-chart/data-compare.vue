<template>
  <div class="table">
    <!-- 对比类型和维度 -->
    <div class="table-filter">
      <div
        class="table-filter-type"
        @click="handleShowPopup('compareType')">
        {{ compareText }}
        <i class="icon-down"></i>
      </div>
      <div
        v-show="compareType.value > 0"
        class="table-filter-dimension"
        @click="handleShowPopup('compareData')">
        {{ compareValue }}
        <i class="icon-down"></i>
      </div>
    </div>
    <!-- 表头 -->
    <van-row class="table-header">
      <van-col
        v-for="(config, index) in dataConfig"
        :key="index"
        :span="config.span">
        {{ config.label }}
      </van-col>
    </van-row>
    <!-- 表格内容 -->
    <van-row
      v-for="(row, index) in data"
      :key="index"
      class="table-body">
      <van-col
        v-for="(config, i) in dataConfig"
        :key="i"
        :span="config.span">
        <span
          v-if="config.prop === 'name'"
          class="compare-icon"
          :style="{
            background: colors[index]
          }">
        </span>
        <span>{{ row[config.prop] | filterBigNum }}</span>
      </van-col>
    </van-row>
    <!-- select -->
    <bk-select
      v-model="currentCompare.value"
      :show.sync="showPopup"
      :columns="columns"
      @confirm="handleConfirm"
      @cancel="handleCancel">
    </bk-select>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop } from 'vue-property-decorator'
import { Row, Col, DropdownMenu, DropdownItem, Popup, Picker } from 'vant'
import BkSelect from '../../components/select/select.vue'
import { IContent, IDropdownMenu, IConfig, IOptions, ICompare } from '../../types/tendency-chart'
import { transfromNum } from '../../../monitor-common/utils/utils'

@Component({
  name: 'data-compare',
  components: {
    [Row.name]: Row,
    [Col.name]: Col,
    [DropdownMenu.name]: DropdownMenu,
    [DropdownItem.name]: DropdownItem,
    [Popup.name]: Popup,
    [Picker.name]: Picker,
    BkSelect
  },
  filters: {
    filterBigNum(v) {
      if (!v) return '--'
      return isNaN(v) ? v : transfromNum(v)
    }
  }
})
export default class Table extends Vue {
  // 对比数据
  @Prop({ default: () => [] }) private readonly data: IContent[]
  // 对比曲线颜色
  @Prop({ default: () => [] }) private readonly colors: string[]

  // 表格配置
  private dataConfig: IConfig[] = []

  // 对比类型（时间对比、维度对比）
  private compareType: IDropdownMenu = {
    value: 1,
    options: []
  }

  // 对比时间
  private compareData: IDropdownMenu = {
    value: 24,
    options: []
  }

  // select组件是否显示
  private showPopup = false

  // 当前select组件的数据类型
  private currentPopup = 'compareType'

  private currentCompare: ICompare = {
    type: '',
    value: 0
  }

  created() {
    this.dataConfig = [
      {
        label: this.$tc('时间'),
        span: 7,
        prop: 'name'
      },
      {
        label: 'min',
        span: 3,
        prop: 'min'
      },
      {
        label: 'max',
        span: 3,
        prop: 'max'
      },
      {
        label: 'avg',
        span: 3,
        prop: 'avg'
      },
      {
        label: 'current',
        span: 4,
        prop: 'current'
      },
      {
        label: 'total',
        span: 4,
        prop: 'total'
      }
    ]
    this.compareType.options = [
      {
        text: this.$t('时间对比'),
        value: 1
      },
      {
        text: this.$t('不对比'),
        value: 0
      }
    ]
    this.compareData.options = [
      {
        text: this.$t('天前', { num: 1 }),
        value: 24
      },
      {
        text: this.$t('天前', { num: 2 }),
        value: 24 * 2
      },
      {
        text: this.$t('天前', { num: 3 }),
        value: 24 * 3
      },
      {
        text: this.$t('天前', { num: 4 }),
        value: 24 * 4
      },
      {
        text: this.$t('天前', { num: 5 }),
        value: 24 * 5
      },
      {
        text: this.$t('天前', { num: 6 }),
        value: 24 * 6
      },
      {
        text: this.$t('周前', { num: 1 }),
        value: 24 * 7
      },
      {
        text: this.$t('周前', { num: 2 }),
        value: 24 * 7 * 2
      },
      {
        text: this.$t('月前', { num: 1 }),
        value: 24 * 30
      }
    ]
  }

  // 当前select组件的options数据
  get columns(): IOptions[] {
    return this.currentPopup === 'compareType' ? this.compareType.options : this.compareData.options
  }

  // 对比方式文案
  get compareText() {
    const options = this.compareType.options.find(item => item.value === this.compareType.value)
    return options ? options.text : ''
  }

  // 对比值
  get compareValue() {
    const options = this.compareData.options.find(item => item.value === this.compareData.value)
    return options ? options.text : ''
  }

  handleShowPopup(v) {
    this.currentPopup = v
    this.showPopup = true
  }

  @Emit('change')
  handleConfirm(value: number) {
    if (this.currentPopup === 'compare') {
      this.compareType.value = value
    } else if (this.currentPopup === 'compareType')  {
      this.compareType.value = value
    } else {
      this.compareData.value = value
    }
    this.handleCancel()
    this.currentCompare = {
      type: this.currentPopup,
      value
    }
    return this.currentCompare
  }

  handleCancel() {
    this.showPopup = false
  }
}
</script>
<style lang="scss" scoped>
    /deep/ .van-row {
      line-height: 3.125rem;
      border-bottom: 1px solid rgba(220,222,229,.6);
      .van-col:not(:first-child) {
        text-align: right;
      }
    }

    @mixin select-btn {
      background: #f0f1f5;
      border-radius: 4px;
      padding: 0 .75rem;
      color: #63656e;
    }

    .table {
      background: #fff;
      padding: 0 1.5rem 0 1.5rem;
      font-size: .8rem;
      padding-top: 1rem;
      &-filter {
        line-height: 2rem;
        display: flex;
        &-type {
          flex: 0 7.5rem;
          margin-right: .625rem;
          display: flex;
          justify-content: space-between;
          align-items: center;

          @include select-btn;
        }
        &-dimension {
          flex: 1;
          display: flex;
          justify-content: space-between;
          align-items: center;

          @include select-btn;
        }
        .icon-down {
          display: inline-block;
          width: 0;
          height: 0;
          border-width: 5px;
          border-style: solid;
          border-color: #979ba5 transparent transparent transparent;
          transform: translateY(2px);
        }
      }
      &-header {
        /deep/ &.van-row {
          font-weight: 500;
          color: #313238;
        }
      }
      &-body {
        /deep/ &.van-row {
          font-weight: 400;
          color: #63656e;
          .van-col:first-child {
            display: flex;
            align-items: center;
          }
        }
        .compare-icon {
          width: 1rem;
          height: .8rem;
          display: inline-block;
          margin-right: .5rem;
        }
      }
    }
</style>
