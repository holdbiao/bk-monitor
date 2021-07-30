<template>
  <!-- 异常告警 -->
  <div class="dash-board-center" v-show="msg === 1">
    <mo-panel shadow="never">
      <div slot="header">
        <i class="icon icon-volume"></i>
        <span> {{ $t('通知设置') }} </span>
      </div>
      <el-form ref="alarmConfigForm" label-width="160px" label-position="right" size="small" :model="this" :rules="rules" v-bkloading="{ isLoading: loadingAlarmConfig }">
        <el-form-item required :label="$t('通知方式')" prop="alarmType">
          <!-- <el-checkbox-group v-model="alarmType" v-validate="{ required: true }" data-vv-name="alarmType"> -->
          <el-checkbox-group v-model="alarmType">
            <el-checkbox label="mail"><img src="../../static/assets/images/mail.png" alt="mail" style="height: 20px"></el-checkbox>
            <el-checkbox label="wechat"><img src="../../static/assets/images/wechat.png" alt="wechat" style="height: 20px"></el-checkbox>
            <el-checkbox label="sms"><img src="../../static/assets/images/sms.png" alt="sms" style="height: 20px"></el-checkbox>
            <el-checkbox v-if="$platform.te" label="im"><img src="../../static/assets/images/rtx.png" alt="rtx" style="height: 20px"></el-checkbox>
            <el-checkbox label="phone"><img src="../../static/assets/images/phone.png" alt="phone" style="height: 20px"></el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item required :label="$t('通知人员')" prop="alarmRole">
          <el-select
            style="width: 300px"
            multiple
            remote :placeholder="$t('请输入人员名称进行搜索')"
            :remote-method="filterMethod"
            :default-first-option="true"
            v-model="alarmRole"
            :loading="loadingAlarmRoleOptions"
            filterable>
            <el-option :key="option.english_name" :label="`${option.chinese_name}(${option.english_name})`" :value="option.english_name" v-for="option in filteredRoleOptions"></el-option>
          </el-select>
          <el-tooltip placement="right" effect="dark" style="margin-left: 10px" :content="$t('当蓝鲸监控的进程状态异常或告警队列拥塞时会通知相关人员')">
            <span><i class="fa fa-question-circle"></i></span>
          </el-tooltip>
        </el-form-item>
        <el-row style="text-align: center">
          <el-button type="success" @click="setAlarmConfig" :loading="loadingSaveAlarmConfig"> {{ $t('保存') }} </el-button>
        </el-row>
      </el-form>
    </mo-panel>
  </div>
</template>
<script>
import MoPanel from './panel'
import { Form, FormItem, CheckboxGroup, Checkbox, Select, Option, Tooltip, Row, Button } from 'element-ui'
import { messageMixin } from './message-mixin'
export default {
  name: 'MoHealthzAlarmConfig',
  components: {
    MoPanel,
    ElForm: Form,
    ElFormItem: FormItem,
    ElCheckboxGroup: CheckboxGroup,
    ElCheckbox: Checkbox,
    ElSelect: Select,
    ElOption: Option,
    ElTooltip: Tooltip,
    ElRow: Row,
    ElButton: Button
  },
  mixins: [messageMixin],
  props: {
    msg: {
      type: Number
    }
  },
  data() {
    return {
      alarmType: [],
      alarmRole: [],
      alarmRoleOptions: [],
      filteredRoleOptions: [],
      loadingAlarmRoleOptions: false,
      loadingAlarmConfig: false,
      loadingSaveAlarmConfig: false,
      rules: {
        alarmType: [{ required: true, message: this.$t('通知方式不能为空'), trigger: 'change' }],
        alarmRole: [{ required: true, message: this.$t('通知人员不能为空'), trigger: 'change' }]
      }
    }
  },
  watch: {
    msg() {
      if (this.msg === 1) {
        if (this.alarmRoleOptions.length === 0) {
          this.getAllUser()
        }
        this.getAlarmConfig()
      }
    }
  },
  methods: {
    getAllUser() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      const self = this
      self.loadingAlarmRoleOptions = true
      self.$api.healthz.allUser().then((data) => {
        self.alarmRoleOptions = data
        self.loadingAlarmRoleOptions = false
      })
        .catch(() => {
          self.message.error(this.$t('获取人员名单失败'))
          self.loadingAlarmRoleOptions = false
        })
    },
    getAlarmConfig() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      const self = this
      self.loadingAlarmConfig = true
      self.$api.healthz.getAlarmConfig().then((data) => {
        if (data.alarm_type.length > 0 || data.alarm_role.length > 0) {
          self.alarmRole = data.alarm_role
          self.alarmType = data.alarm_type
        } else {
          self.$refs.alarmConfigForm.resetFields()
        }
        self.loadingAlarmConfig = false
      })
        .catch(() => {
          self.message.error(this.$t('获取通知设置失败'))
          self.loadingAlarmConfig = false
        })
    },
    setAlarmConfig() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      const self = this
      self.loadingSaveAlarmConfig = true
      let params = {
        alarm_type: self.alarmType,
        alarm_role: self.alarmRole
      }

      params = { alarm_config: params }

      self.$refs.alarmConfigForm.validate((valid) => {
        if (valid) {
          self.$api.healthz.updateAlarmConfig(params, { needRes: true }).then((res) => {
            if (res.result) {
              self.message.success(this.$t('保存成功'))
            } else {
              self.message.error(this.$t('获取通知设置失败'))
            }
            self.loadingSaveAlarmConfig = false
          })
        } else {
          self.message.error(this.$t('校验失败，请检查参数'))
          self.loadingSaveAlarmConfig = false
        }
      }).catch(() => {
        self.message.error(this.$t('校验失败，请检查参数'))
        self.loadingSaveAlarmConfig = false
      })
    },
    filterMethod(query) {
      if (query !== '') {
        this.loadingAlarmRoleOptions = true
        setTimeout(() => {
          this.filteredRoleOptions = this.alarmRoleOptions.filter((item) => {
            const str = `${item.english_name}|${item.chinese_name}`
            return str.indexOf(query) > -1
          })

          this.filteredRoleOptions = this.filteredRoleOptions.slice(0, 500)
          this.loadingAlarmRoleOptions = false
        })
      }
    }
  }
}
</script>
<style scoped lang="scss">
    .icon-volume {
      background: url("../../static/assets/images/icon-volume.png");
    }
    /deep/ .el-card__header {
      padding: 15px;
      .icon,
      > span {
        float: left;
      }
      .icon {
        height: 20px;
        width: 20px;
        margin-right: 10px;

        /* stylelint-disable-next-line declaration-no-important */
        background-size: 20px 20px !important;
      }
    }
</style>
