<template>
  <bk-dialog
    :value="isShow"
    theme="primary"
    :header-position="'left'"
    @after-leave="handleAfterLeave"
    :confirm-fn="handleSubmit" :title="$t('快捷屏蔽告警事件')"
    width="800px">
    <div class="quick-alarm-shield-event" v-bkloading="{ 'isLoading': loading }">
      <div class="stratrgy-item" v-if="!loading">
        <div class="item-label item-before"> {{ $t('屏蔽时间') }} </div>
        <verify-input :show-validate.sync="rule.customTime" :validator="{ content: $t('请至少选择一种时间') }">
          <div class="item-time">
            <bk-button v-for="(item, index) in timeList" :key="index"
                       class="width-item"
                       :class="{ 'is-selected': timeValue === item.id }"
                       @click.stop="handleScopeChange(item.id)">
              {{item.name}}
            </bk-button>
            <bk-button v-if="timeValue !== 0" class="custom-width" :class="{ 'is-selected': timeValue === 0 }" @click.stop="handleScopeChange(0)"> {{ $t('自定义') }} </bk-button>
            <bk-date-picker v-else v-model="customTime" :options="options" :placeholder="$t('选择日期时间范围')" :type="'datetimerange'" ref="time"></bk-date-picker>
          </div>
        </verify-input>
      </div>
      <div class="stratrgy-item">
        <div class="item-label"> {{ $t('告警内容') }} </div>
        <div class="item-tips"><i class="icon-monitor icon-hint"></i> {{ $t('屏蔽的是告警内容的这类事件，不仅仅当前的事件还包括后续屏蔽时间内产生的事件。') }} </div>
        <div class="item-content">
          <div class="column-item">
            <div class="column-label"> {{ $t('告警级别：') }} </div><div class="column-content">{{levelMap[config.level]}}</div>
          </div>
          <div class="column-item">
            <div class="column-label"> {{ $t('维度信息：') }} </div><div class="column-content">
              <template v-if="detail.dimensions.length">
                <span v-for="(item, index) in detail.dimensions" :key="index">
                  <template v-if="!(item.name === 'bk_target_cloud_id' && item.value === '0')">
                    <span v-if="index !== 0"> - </span>
                    <span>{{ item.displayName }}</span>
                    (<span :class="{ 'info-check': item.name === 'bk_target_ip' }" style="margin-left: 0;">{{ item.displayValue }}</span>)
                  </template>
                </span>
              </template>
              <span v-else>--</span>
            </div>
          </div>
          <div class="column-item" style="margin-bottom: 18px">
            <div class="column-label"> {{ $t('触发条件：') }} </div><div class="column-content">{{config.eventMessage}}</div>
          </div>
        </div>
      </div>
      <div class="stratrgy-item">
        <div class="item-label"> {{ $t('屏蔽原因') }} </div>
        <div class="item-desc">
          <bk-input
            :type="'textarea'"
            v-model="desc"
            width="625"
            :rows="3"
            :maxlength="100">
          </bk-input>
        </div>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
import VerifyInput from '../../../components/verify-input/verify-input'
import { addShield } from '../../../../monitor-api/modules/shield'
import { quickAlarmShieldMixin } from '../../../common/mixins'
export default {
  name: 'quick-alarm-shield-event',
  components: {
    VerifyInput
  },
  mixins: [quickAlarmShieldMixin],
  props: {
    isShow: {
      type: Boolean,
      default: false
    },
    eventId: [Number, String],
    detail: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      levelMap: ['', this.$t('致命'), this.$t('提醒'), this.$t('预警')],
      timeValue: 18,
      customTime: ['', ''],
      desc: '',
      config: {},
      rule: {
        customTime: false
      },
      loading: false
    }
  },
  watch: {
    eventId: {
      handler(newId, oldId) {
        if (`${newId}` !== `${oldId}`) {
          this.handleDialogShow()
        }
      },
      immediate: true
    }
    // detail: {
    //     handler (v) {
    //         this.handleDialogShow()
    //     }
    // }
  },
  methods: {
    handleDialogShow() {
      // this.loading = true
      this.timeValue = 18
      this.desc = ''
      this.customTime = ''
      this.config = this.detail
    },
    handleSubmit(event) {
      const time = this.getTime()
      if (time) {
        this.loading = true
        const params = {
          category: 'event',
          begin_time: time.begin,
          end_time: time.end,
          dimension_config: {
            id: this.eventId
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
          this.$emit('change-is-shielded', true)
          event.close()
          this.$bkMessage({ theme: 'success', message: this.$t('恭喜，创建告警屏蔽成功') })
        })
          .finally(() => {
            this.loading = false
          })
      }
    },
    handleAfterLeave() {
      this.$emit('update:isShow', false)
    }
  }
}
</script>

<style lang="scss" scoped>
    .quick-alarm-shield-event {
      font-size: 14px;
      color: #63656e;
      .stratrgy-item {
        display: flex;
        flex-direction: column;
        margin-bottom: 17px;
        .item-label {
          width: 68px;
          margin-bottom: 8px;

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
            width: 327px;
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
        .item-content {
          display: flex;
          flex-direction: column;
          padding: 17px 21px 0 21px;
          min-width: 625px;
          background: #fafbfd;
          border: 1px solid #dcdee5;
          border-radius: 2px;
          .column-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 20px;
          }
          .column-label {
            min-width: 70px;
            text-align: right;
            margin-right: 7px;
          }
          .column-content {
            word-wrap: break-word;
            word-break: break-all;
          }
        }
        .item-tips {
          display: flex;
          align-items: center;
          font-size: 12px;
          height: 32px;
          width: 100%;
          background: #f0f8ff;
          border: 1px solid #e1ecff;
          margin-bottom: 10px;
          i {
            font-size: 14px;
            color: #3a84ff;
            margin: 0 9px 0 11px;
          }
        }
        /deep/ .bk-date-picker.long {
          width: 327px;
        }
        /deep/ .bk-date-picker-rel .bk-date-picker-editor {
          border-radius: 0;
          margin-left: -1px;
          border: 1px #3a84ff solid;
        }
      }
    }
    /deep/ .bk-date-picker-dropdown {
      /* stylelint-disable-next-line declaration-no-important */
      left: 191px !important
    }
    /deep/ .bk-dialog-wrapper .bk-dialog-body {
      padding: 1px 24px 4px;
    }
</style>
