<template>
  <bk-dialog
    :title="curItem.title"
    :width="curItem.width"
    :esc-close="false"
    :value="dialogShow"
    :mask-close="false"
    header-position="left"
    @after-leave="handleAfterLeave"
    @confirm="handleConfirm">
    <div class="strategy-dialog-wrap" v-bkloading="{ isLoading: loading }">
      <template v-if="setType === 0">
        <div class="alarm-group-label"> {{ $t('告警组') }} <span class="asterisk">*</span>
        </div>
        <bk-select class="alarm-notice-list" multiple v-model="data.alarmGroup" :clearable="false" searchable v-if="dialogShow">
          <bk-option v-for="(option, index) in groupList"
                     :key="index"
                     :id="option.id"
                     :name="option.name">
          </bk-option>
        </bk-select>
        <span v-if="data.noticeGroupError" class="notice-error-msg error-msg-font"> {{ $t('请选择告警组') }} </span>
      </template>
      <template v-else-if="setType === 1">
        <div class="modify-trigger-condition">
          {{ $t('在') }}
          <bk-input @change="handleFormatNumber(arguments, 'triggerCondition', 'cycleOne')" class="number-input" type="number" :min="1" :max="60" v-model="data.triggerCondition.cycleOne"></bk-input> {{ $t('个周期内满足') }} <bk-input @change="handleFormatNumber(arguments, 'triggerCondition', 'count')" class="number-input" type="number" :min="1" :max="numbersScope.countMax" v-model="data.triggerCondition.count"></bk-input> {{ $t('次检测算法触发告警通知') }} <span v-if="data.triggerError" class="trigger-condition-tips">
            <i class="icon-monitor icon-mind-fill item-icon"></i> {{ $t('要求: 满足次数&lt;=周期数') }} </span>
        </div>
      </template>
      <template v-else-if="setType === 5">
        <div class="modify-trigger-condition"> {{ $t('连续') }} <bk-input @change="handleFormatNumber(arguments, 'recover', 'val')" class="number-input" type="number" :min="1" v-model="data.recover.val"></bk-input> {{ $t('个周期内不满足触发条件') }} </div>
        <span v-if="data.recoverCycleError" class="recover-cycle-error-msg error-msg-font"> {{ $t('恢复条件周期为正整数') }} </span>
      </template>
      <template v-else-if="setType === 2">
        <div class="alarm-interval"> {{ $t('若告警未恢复并且未确认，则每隔') }} <bk-input @change="handleFormatNumber(arguments, 'notice', 'val')" class="number-input" type="number" :min="1" :max="1440" v-model="data.notice.val"></bk-input> {{ $t('分钟进行告警') }} </div>
        <span v-if="data.recoverAlarmError" class="recover-error-msg error-msg-font"> {{ $t('通知间隔为正整数') }} </span>
      </template>
      <template v-else-if="setType === 3">
        <div class="no-data-alarm" :class="{ 'close-no-data-alarm': !data.openAlarmNoData }">
          <bk-switcher v-model="data.openAlarmNoData" size="small" theme="primary"></bk-switcher>
          <span class="alarm-enable"> {{ $t('启用无数据告警') }} </span>
        </div>
        <div class="no-data-alarm-cycle" v-show="data.openAlarmNoData"> {{ $t('当数据连续丢失') }} <bk-input @change="handleFormatNumber(arguments, 'noDataAlarm', 'cycle')" class="number-input" type="number" :min="1" v-model="data.noDataAlarm.cycle"></bk-input> {{ $t('个周期后触发告警') }} </div>
        <span v-if="data.noDataCycleError" class="no-data-error-msg error-msg-font"> {{ $t('周期为正整数') }} </span>
      </template>
      <template v-else-if="setType === 4">
        <bk-checkbox class="alarm-recover" v-model="data.alarmNotice"> {{ $t('告警恢复通知') }} </bk-checkbox>
      </template>
      <template v-else-if="setType === 6">
        <div class="alarm-recover">
          <bk-switcher v-model="data.enAbled" size="small" theme="primary"></bk-switcher>
          {{ $t('请确认是否批量启用/停用已选择的') + checkedList.length + $t("个策略") }}
        </div>
      </template>
      <template v-else-if="setType === 7">
        <div class="alarm-recover">
          {{ $t('请确认是否批量删除已选择的') + checkedList.length + $t("个策略") }}
        </div>
      </template>
      <template v-else-if="setType === 9">
        <div v-bkloading="{ isLoading: alertNotificationTemplateLoading }" class="alarm-recover message-template">
          <span class="default-template" @click="alertNotificationTemplate.messageTemplate = messageTemplate">{{$t('填充默认模板')}}</span>
          <template-input ref="templateInput" :default-value="alertNotificationTemplate.messageTemplate" :trigger-list="alertNotificationTemplate.triggerList" @change="handleTemplateChange"></template-input>
          <div class="message-template-tip">
            <div>{{$t('注意：批量设置会覆盖原有的已选择的告警策略模版配置。')}}</div>
          </div>
        </div>
      </template>
    </div>
    <template #footer>
      <bk-button v-if="setType === 6 || setType === 7" theme="primary" @click="handleConfirm"> {{ $t('确认') }} </bk-button>
      <bk-button v-else theme="primary" @click="handleConfirm" :disabled="loading"> {{ $t('保存') }} </bk-button>
      <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </template>
  </bk-dialog>
</template>
<script>
import TemplateInput from '../strategy-config-set/strategy-template-input/strategy-template-input'
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('strategy-config')
export default {
  name: 'StrategyConfigDialog',
  components: {
    TemplateInput
  },
  props: {
    setType: {
      type: Number,
      required: true
    },
    groupList: {
      type: Array,
      default: () => ([])
    },
    dialogShow: Boolean,
    selectList: {
      type: Array,
      default() {
        return []
      }
    },
    checkedList: {
      type: Array,
      default: () => ([])
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      typeMap: [
        {
          title: this.$t('批量修改告警组'),
          width: 400
        },
        {
          title: this.$t('批量修改触发条件'),
          width: 480
        },
        {
          title: this.$t('批量修改通知间隔'),
          width: 480
        },
        {
          title: this.$t('批量修改无数据告警'),
          width: 400
        },
        {
          title: this.$t('批量修改告警恢复通知'),
          width: 400
        },
        {
          title: this.$t('批量修改恢复条件'),
          width: 480
        },
        {
          title: this.$t('批量启用/停用策略'),
          width: 480
        },
        {
          title: this.$t('批量删除策略'),
          width: 480
        },
        {
          title: this.$t('增删目标'),
          width: 480
        },
        {
          title: this.$t('批量修改告警模板'),
          width: 480
        }
      ],
      numbersScope: {
        countMax: 5
      },
      data: {
        alarmGroup: '',
        triggerCondition: {
          cycleOne: 5,
          count: 4,
          cycleTwo: 5
        },
        recover: {
          val: 5
        },
        notice: {
          val: 120
        },
        noDataAlarm: {
          cycle: 5
        },
        openAlarmNoData: true,
        alarmNotice: true,
        triggerError: false,
        noticeGroupError: false,
        recoverAlarmError: false,
        recoverCycleError: false,
        noDataCycleError: false,
        enAbled: false
      },
      cachInitData: null,
      alertNotificationTemplate: {
        messageTemplate: '',
        triggerList: []
      },
      messageTemplate: `{{content.level}}
{{content.begin_time}}
{{content.time}}
{{content.duration}}
{{content.target_type}}
{{content.data_source}}
{{content.content}}
{{content.current_value}}
{{content.biz}}
{{content.target}}
{{content.dimension}}
{{content.detail}}
{{content.related_info}}`,
      alertNotificationTemplateLoading: true
    }
  },
  computed: {
    curItem() {
      return this.typeMap[this.setType] || {}
    }
  },
  watch: {
    dialogShow(v) {
      if (v) {
        this.setType === 0 && this.$emit('get-group-list')
        this.data = JSON.parse(JSON.stringify(this.cachInitData))
      }
    },
    'data.triggerCondition.cycleOne'(v) {
      this.numbersScope.countMax = v
    },
    setType(v) {
      // 批量告警模板数据
      if (v === 9) {
        if (this.alertNotificationTemplate.triggerList.length === 0) {
          this.handleGetVariateList()
        } else {
          this.alertNotificationTemplateLoading = false
        }
      }
    }
  },
  created() {
    this.cachInitData = JSON.parse(JSON.stringify(this.data))
  },
  methods: {
    ...mapActions(['getNoticeVariableList']),
    // 获取策略模板变量列表
    async handleGetVariateList() {
      const data = await this.getNoticeVariableList()
      this.alertNotificationTemplate.triggerList = data.reduce((pre, cur) => {
        pre.push(...cur.items)
        return pre
      }, [])
      this.alertNotificationTemplateLoading = false
    },
    // 通知模板编辑变化触发
    handleTemplateChange(v) {
      this.alertNotificationTemplate.messageTemplate = v || ''
    },
    handleCancel() {
      this.$emit('hide-dialog', false)
    },
    handleConfirm() {
      const params = this.generationParam()
      if (params) {
        this.$emit('confirm', params)
        this.$emit('hide-dialog', false)
      }
    },
    handleAfterLeave() {
      this.$emit('hide-dialog', false)
    },
    handleFormatNumber(arg, type, prop) {
      let inputVal = arg[0].toString()
      const index = inputVal.indexOf('.')
      if (index > -1) {
        inputVal = inputVal.replace(/\./gi, '')
      }
      this.data[type][prop] = parseInt(inputVal, 10)
    },
    validateGroupList() {
      this.data.noticeGroupError = !this.data.alarmGroup.length
      return this.data.noticeGroupError
    },
    validateTriggerCondition() {
      for (const key in this.data.triggerCondition) {
        if (!this.data.triggerCondition[key]) {
          this.data.triggerError = true
          return true
        }
      }
      const cycleOne = parseInt(this.data.triggerCondition.cycleOne, 10)
      const count = parseInt(this.data.triggerCondition.count, 10)
      if (cycleOne < count) {
        this.data.triggerError = true
      } else {
        this.data.triggerError = false
      }
      return this.data.triggerError
    },
    validateRecoveAlarmCondition() {
      this.data.recoverAlarmError = !this.data.notice.val
      return this.data.recoverAlarmError
    },
    validateRecoveCycle() {
      this.data.recoverCycleError = !this.data.recover.val
      return this.data.recoverCycleError
    },
    validateNoDataAlarmCycle() {
      this.data.noDataCycleError = !this.data.noDataAlarm.cycle
      return this.data.noDataCycleError
    },
    generationParam() {
      if (this.setType === 0) {
        return this.validateGroupList() ? false : { notice_group_list: this.data.alarmGroup }
      } if (this.setType === 1) {
        return this.validateTriggerCondition() ? false : {
          trigger_config: {
            count: parseInt(this.data.triggerCondition.count, 10),
            check_window: parseInt(this.data.triggerCondition.cycleOne, 10)
          }
        }
      } if (this.setType === 2) {
        return this.validateRecoveAlarmCondition() ? false : { alarm_interval: parseInt(this.data.notice.val, 10) }
      } if (this.setType === 3) {
        if (this.data.openAlarmNoData && this.validateNoDataAlarmCycle()) {
          return false
        }
        return this.data.openAlarmNoData
          ? {
            no_data_config: {
              continuous: parseInt(this.data.noDataAlarm.cycle, 10),
              is_enabled: this.data.openAlarmNoData
            }
          }
          : { no_data_config: { is_enabled: this.data.openAlarmNoData } }
      } if (this.setType === 4) {
        return { send_recovery_alarm: this.data.alarmNotice }
      } if (this.setType === 5) {
        return this.validateRecoveCycle() ? false : { recovery_config: { check_window: this.data.recover.val } }
      } if (this.setType === 6) {
        return { is_enabled: this.data.enAbled }
      } if (this.setType === 7) {
        return { isDel: true }
      } if (this.setType === 9) {
        return { message_template: this.alertNotificationTemplate.messageTemplate }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.strategy-dialog-wrap {
  position: relative;
  .alarm-notice-list {
    margin-bottom: 40px;
  }
  .modify-trigger-condition {
    display: flex;
    align-items: center;
    margin-top: 13px;
    margin-bottom: 40px;
    .trigger-condition-tips {
      position: absolute;
      top: 38px;
      left: 22px;
      font-size: 12px;
      color: #63656e;
      color: #ea3636;
    }
  }
  .alarm-group-label {
    margin-bottom: 5px;
    .asterisk {
      color: #ea3636;
      margin-left: 3px;
    }
  }
  .alarm-recover {
    margin-bottom: 60px;
  }
  .alarm-interval {
    margin-top: 13px;
    margin-bottom: 40px;
  }
  .no-data-alarm {
    margin-bottom: 19px;
    &.close-no-data-alarm {
      margin-bottom: 61px;
    }
    .alarm-enable {
      margin-left: 5px;
    }
  }
  .no-data-alarm-cycle {
    margin-bottom: 40px;
  }
  .number-input {
    display: inline-block;
    width: 64px;
    margin: 0 8px;
  }
  .notice-error-msg {
    position: absolute;
    top: 59px;
  }
  .trigger-error {
    color: #ea3636;
  }
  .error-msg-font {
    color: #ea3636;
    font-size: 12px;
  }
  .recover-error-msg {
    position: absolute;
    top: 23px;
  }
  .recover-cycle-error-msg {
    position: absolute;
    top: 32px;
  }
  .no-data-error-msg {
    position: absolute;
    top: 62px;
  }
  .default-template {
    color: #3a84ff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    height: 20px;
  }
  .message-template {
    /deep/ .template-input {
      min-height: 150px;
    }
    &-tip {
      border: 1px solid #a3c5fd;
      background-color: #f0f8ff;
      padding: 10px 35px 10px 10px;
      line-height: 24px;
      margin: 10px 0 20px 0;
      position: relative;
      transition: height ease-in-out .3s;
      overflow: hidden;
      border-radius: 2px;
      div {
        color: #63656e;
      }
    }
  }
}
</style>
<style lang="scss" scoped>
/deep/ .bk-dialog-body {
  padding-top: 0;
  padding-bottom: 0;
}
/deep/ .bk-dialog-footer {
  font-size: 0;
  .bk-button {
    margin-right: 10px;
    &:last-child {
      margin-right: 0;
    }
  }
}
/deep/ .strategy-dialog-wrap .alarm-recover {
  margin-bottom: 24px;
}
</style>
<style lang="scss">
.tippy-popper {
  body & {
    pointer-events: auto;
  }
}
</style>
