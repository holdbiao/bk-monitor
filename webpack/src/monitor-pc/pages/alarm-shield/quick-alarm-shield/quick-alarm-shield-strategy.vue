<template>
  <bk-dialog
    :value="isShowStrategy"
    theme="primary"
    :header-position="'left'"
    @after-leave="handleAfterLeave"
    :confirm-fn="handleSubmit" :title="$t('快捷屏蔽策略告警')"
    width="773px">
    <div class="quick-alarm-shield-stratrgy" v-bkloading="{ 'isLoading': loading }">
      <div class="stratrgy-item" v-if="!loading">
        <div class="item-label item-before" style="width: 66px;"> {{ $t('屏蔽时间') }} </div>
        <verify-input :show-validate.sync="rule.customTime" :validator="{ content: $t('请至少选择一种时间') }">
          <div class="item-time">
            <bk-button v-for="(item, index) in timeList" :key="index"
                       class="width-item"
                       :class="{ 'is-selected': timeValue === item.id }"
                       @click.stop="handleScopeChange(item.id)">
              {{ item.name }}
            </bk-button>
            <bk-button v-if="timeValue !== 0" class="custom-width" :class="{ 'is-selected': timeValue === 0 }" @click.stop="handleScopeChange(0)"> {{ $t('自定义') }} </bk-button>
            <bk-date-picker v-else v-model="customTime" :options="options" :placeholder="$t('选择时间范围')" :type="'datetimerange'" ref="time"></bk-date-picker>
          </div>
        </verify-input>
      </div>
      <div class="stratrgy-item">
        <div class="item-label"> {{ $t('策略内容') }} </div>
        <strategy-detail :strategy-data="strategyData"></strategy-detail>
      </div>
      <div class="stratrgy-item" style="margin-bottom: 11px">
        <div class="item-label"> {{ $t('屏蔽原因') }} </div>
        <div>
          <bk-input
            :type="'textarea'"
            v-model="desc"
            width="625"
            :rows="3"
            :maxlength="100">
          </bk-input>
        </div>
      </div>
      <!-- <div class="to-strategy" @click="handleToStrategy">更多高级设置<i class="icon-monitor icon-mc-wailian"></i></div> -->
    </div>
  </bk-dialog>
</template>

<script>
import { transformDataKey } from '../../../../monitor-common/utils/utils.js'
import VerifyInput from '../../../components/verify-input/verify-input'
import { strategyInfo } from '../../../../monitor-api/modules/strategies'
import { addShield } from '../../../../monitor-api/modules/shield'
import { quickAlarmShieldMixin, strategyMapMixin } from '../../../common/mixins'
import StrategyDetail from '../alarm-shield-components/strategy-detail'
export default {
  name: 'quick-alarm-shield-stratrgy',
  components: {
    VerifyInput,
    StrategyDetail
  },
  mixins: [quickAlarmShieldMixin, strategyMapMixin],
  props: {
    isShowStrategy: {
      type: Boolean,
      default: false
    },
    strategyId: Number
  },
  data() {
    return {
      timeValue: 18,
      customTime: ['', ''],
      desc: '',
      typeLabel: '',
      rule: {
        customTime: false
      },
      loading: false,
      strategyData: {}
    }
  },
  watch: {
    strategyId: {
      handler(newId, oldId) {
        if (`${newId}` !== `${oldId}`) {
          this.handleDialogShow()
        }
      },
      immediate: true
    }
  },
  methods: {
    handleSubmit(v) {
      const time = this.getTime()
      if (time) {
        this.loading = true
        const params = {
          category: 'strategy',
          begin_time: time.begin,
          end_time: time.end,
          dimension_config: {
            id: [this.strategyId],
            level: this.strategyData.level
          },
          cycle_config: {
            begin_time: '',
            type: 1,
            day_list: [],
            week_list: [],
            end_time: ''
          },
          shield_notice: false,
          description: this.desc,
          is_quick: true
        }
        addShield(params).then(() => {
          v.close()
          this.$bkMessage({ theme: 'success', message: this.$t('恭喜，创建告警屏蔽成功') })
          this.$parent.handleGetListData()
        })
          .finally(() => {
            this.loading = false
          })
      }
    },
    handleDialogShow() {
      this.loading = true
      this.timeValue = 18
      this.desc = ''
      this.customTime = ''
      this.getDetailStrategy()
    },
    getDetailStrategy() {
      if (this.strategyId) {
        strategyInfo({ id: this.strategyId }).then((res) => {
          const data = transformDataKey(res)
          const [strategyData] = data.itemList
          this.strategyData = strategyData
        })
          .finally(() => {
            this.loading = false
          })
      }
    },
    handleAfterLeave() {
      this.$emit('update:isShowStrategy', false)
    },
    handleToStrategy() {
      const params = {
        strategyId: this.strategyId
      }
      this.$emit('update:isShowStrategy', false)
      this.$router.push({ name: 'alarm-shield-add', params })
    }
  }
}
</script>

<style lang="scss" scoped>
    .quick-alarm-shield-stratrgy {
      font-size: 14px;
      color: #63656e;
      .stratrgy-item {
        display: flex;
        flex-direction: column;
        margin-bottom: 17px;
        .item-label {
          width: 86px;
          margin-bottom: 8px;
        }
        .item-time {
          display: flex;
          .width-item {
            min-width: 86px;
            &:hover {
              color: #3a84ff;
              background: #e1ecff;
              border: 1px #3a84ff solid;
              z-index: 2;
            }
          }
          .custom-width {
            width: 300px;
          }
          .is-selected {
            color: #3a84ff;
            background: #e1ecff;
            border: 1px #3a84ff solid;
            z-index: 2;
          }
          /deep/ .bk-button {
            border-radius: 0;
            margin-left: -1px;
          }
        }
        .item-before {
          position: relative;
          &::before {
            content: "*";
            color: #ea3636;
            position: absolute;
            top: 0;
            right: -9px;
          }
        }
        /deep/ .bk-date-picker.long {
          width: 300px;
        }
        /deep/ .bk-date-picker-rel .bk-date-picker-editor {
          border-radius: 0;
          margin-left: -1px;
          border: 1px #3a84ff solid;
        }
      }
      .to-strategy {
        color: #3a84ff;
        display: flex;
        align-items: center;
        cursor: pointer;
        i {
          font-size: 21px;
        }
      }
    }
    /deep/ .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      left: 191px !important
    }
    /deep/ .bk-dialog-wrapper .bk-dialog-body {
      padding: 1px 24px 14px;
    }
    /deep/ .item-content {
      max-height: 270px;
      overflow: scroll;
    }
</style>
