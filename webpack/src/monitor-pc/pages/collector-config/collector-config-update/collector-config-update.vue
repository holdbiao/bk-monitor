<template>
  <div class="dialog-update" v-bkloading="{ isLoading: loading }">
    <div class="dialog-update-left">
      <div class="left-title"> {{ $t('升级插件') }} </div>
      <div class="left-message" :class="{ 'status-err': !updateStatus }">
        <span class="icon-monitor icon-tips message-icon"></span>
        <span v-if="!updateMessage" class="left-message-content"> {{ $t('插件') }}“ {{pluginName}} ”{{ $t('最新版本') }}({{lastVersion}}){{ $t('可能存在运行参数变动，请检查并确认运行参数！') }} </span>
        <span v-else class="left-message-content">
          {{updateMessage}}
        </span>
      </div>
      <div class="left-form">
        <bk-form form-type="vertical">
          <div class="left-form-wrap">
            <template v-if="configJson.length">
              <bk-form-item :label="$t('运行参数')">
                <template v-for="(item, index) in configJson">
                  <!-- snmp多用户 -->
                  <auto-multi
                    v-if="item.auth_json !== undefined"
                    :key="index"
                    :template-data="[]"
                    :souce-data="item.auth_json"
                    :tips-data="[]"
                    :param-type="paramType"
                    :allow-add="false"
                    @canSave="bool => handleSnmpAuthCanSave(bool, item)"
                    @triggerData="triggerAuthData">
                  </auto-multi>
                  <verify-input
                    v-else
                    class="params-item"
                    :key="index"
                    :show-validate.sync="item.validate.isValidate"
                    :validator="item.validate"
                    position="right">
                    <auto-complete-input
                      class="mb10"
                      :key="index"
                      :tips-data="[]"
                      :type="item.type"
                      :config="item"
                      @input="handleInput(item)"
                      @error-message="msg => handleErrorMessage(msg, item)"
                      @file-change="file => configJsonFileChange(file, item)"
                      v-model.trim="item.default">
                      <template slot="prepend">
                        <bk-popover placement="top" :tippy-options="tippyOptions">
                          <div class="prepend-text">{{ item.description ? item.description : item.name }}</div>
                          <div slot="content">
                            <div> {{ $t('参数名称：') }} {{ item.name }}</div>
                            <div> {{ $t('参数类型：') }} {{ paramType[item.mode] }}</div>
                            <div> {{ $t('参数说明：') }} {{ item.description || '--' }}</div>
                          </div>
                        </bk-popover>
                      </template>
                    </auto-complete-input>
                  </verify-input>
                </template>
              </bk-form-item>
            </template>
            <div v-else class="wrap-empty"> {{ $t('该插件未定义参数，如需升级请继续！') }} </div>
          </div>
          <bk-form-item class="update-footer">
            <bk-button
              class="update-footer-btn"
              theme="primary"
              :title="$t('提交')"
              @click="handleSubmit"
              :loading="updateLoading"> {{ $t('提交') }} </bk-button>
            <bk-button theme="default" :title="$t('取消')" @click="handleCancel(false)"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </div>
    <div class="dialog-update-right">
      <div class="right-title"> {{ $t('更新记录') }} </div>
      <div class="right-content">
        <ul class="record-list">
          <li class="record-list-item" v-for="(item, index) in versionLog" :key="index">
            <div class="item-title" :class="{ 'current-item': item.version === version }">{{item.version}}</div>
            <div class="item-wrap">
              <div class="item-wrap-content">
                {{item.version_log}}
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script>
import { pluginUpgradeInfo } from '../../../../monitor-api/modules/plugin'
import AutoCompleteInput from '../collector-add/config-set/auto-complete-input'
import AutoMulti from '../collector-add/config-set/auto-multi'
import VerifyInput from '../../plugin-manager/plugin-instance/set-steps/verify-input'

export default {
  name: 'CollectorConfigUpdate',
  components: {
    AutoCompleteInput,
    AutoMulti,
    VerifyInput
  },
  props: {
    updateParams: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      tippyOptions: {
        distance: 0
      },
      show: false,
      loading: false,
      updateLoading: false,
      updateStatus: true,
      updateMessage: '',
      pluginId: '',
      pluginName: '',
      version: '',
      configJson: [],
      versionLog: [],
      //   formData: {},
      rules: {
        port: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        user: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        password: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ]
      },
      paramType: {
        collector: this.$t('采集器参数'),
        opt_cmd: this.$t('命令行参数'),
        pos_cmd: this.$t('位置参数'),
        env: this.$t('环境变量参数'),
        listen_cmd: this.$t('监听参数')
      }
    }
  },
  computed: {
    lastVersion() {
      if (this.versionLog.length) {
        return this.versionLog[0].version
      }
      return ''
    }
  },
  watch: {
    updateParams: {
      handler: 'handleConfigUpdate',
      immediate: true
    }
  },
  methods: {
    handleConfigUpdate() {
      this.updateStatus = true
      this.updateMessage = ''
      const { pluginId, configVersion, infoVersion, id } = this.updateParams
      this.show = true
      this.loading = true
      pluginUpgradeInfo({ plugin_id: pluginId,
        config_version: configVersion,
        info_version: infoVersion,
        config_id: id }).then((data) => {
        this.pluginId = data.plugin_id
        this.pluginName = data.plugin_display_name
        this.version = data.plugin_version
        this.configJson = this.handleConfigJson(data.runtime_params)
        this.versionLog = data.version_log
      })
        .finally(() => {
          this.loading = false
        })
    },
    handleSnmpAuthCanSave(v, item) {
      item.validate.isValidate = !v
    },
    handleInput(item) {
      item.validate = this.validateItem(item)
    },
    validateItem(item) {
      const validate = {
        content: '',
        isValidate: false
      }
      const fnMap = {
        port: (v) => {
          const isPass = /^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$/.test(v)
          validate.content = isPass ? '' : this.$t('请输入正确的端口号')
          validate.isValidate = !isPass
        },
        host: (v) => {
          validate.content = v ? '' : this.$t('必填项')
          validate.isValidate = !v
        }
      }
      const fn = fnMap[item.key || item.name]
      fn?.(item.default)

      return validate
    },
    triggerAuthData(v) {
      if (this.configJson) {
        this.configJson.forEach((item) => {
          if (item.auth_json) {
            return item.auth_json = v
          }
          return { ...item }
        })
      }
    },
    handleConfigJson(runtimeParams) {
      const handleDefaultValue = (list) => {
        list.forEach((item) => {
          if (item.auth_json) {
            handleDefaultValue(item.auth_json)
          }
          item.default = item.value || ''
          if (item.type === 'file') {
            item.default = item?.value?.filename
            item.file_base64 = item?.value?.file_base64 // eslint-disable-line
          }
        })
      }
      handleDefaultValue(runtimeParams)
      const configJson = runtimeParams.map((item) => {
        if ((item.key || item.name) === 'auth_json') {
          const temp = [item.auth_json.map((set) => {
            set.validate = {
              content: '',
              isValidate: false
            }
            return set
          })]
          this.$set(item, 'auth_json', temp)
          item.validate = {
            content: '',
            isValidate: false
          }
          return item
        }
        item.validate = {
          content: '',
          isValidate: false
        }
        return item
      })
      return configJson
    },
    handleCancel(v = false) {
      this.$emit('close-update', v)
    },
    handleConfigJsonParams() {
      const formData = {}
      const fn = (list) => {
        list.forEach((set) => {
          if (set.auth_json) {
            fn(set.auth_json[0])
          } else {
            const value = set.type === 'file'
              ? { filename: set.default, file_base64: set.file_base64 }
              : set.default
            formData[set.key || set.name] = {
              value,
              mode: set.mode
            }
          }
        })
      }
      fn(this.configJson)
      return formData
    },
    handleSubmit() {
      // this.updateLoading = true
      // this.updateStatus = true
      if (!this.validateParams()) return
      this.updateMessage = ''
      const collector = {}
      const plugin = {}
      const formData = this.handleConfigJsonParams()
      Object.keys(formData).forEach((key) => {
        const item = formData[key]
        if (item.mode === 'collector') {
          collector[key] = item.value
        } else {
          plugin[key] = item.value
        }
      })
      const params = {
        params: {
          collector,
          plugin
        },
        id: this.updateParams.id
      }
      this.$emit('on-submit', params)
    },
    handleFileChange(file, item) {
      const obj = this.formData[item.name].value
      obj.file_base64 = file.fileBase64
      obj.filename = file.name
    },
    handleErrorMessage(msg, item) {
      item.validate.content = msg
      item.validate.isValidate = !!msg
    },
    validateParams() {
      console.log(this.configJson)
      return this.configJson.every(item => !item.validate.isValidate)
    },
    configJsonFileChange(file, item) {
      item.default = file.name
      item.file_base64 = file.fileContent
    }
  }
}
</script>
<style lang="scss" scoped>
.dialog-update {
  display: flex;
  width: 850px;
  //   height: 480px;
  margin: -33px -24px -26px -24px;
  font-size: 12px;
  background: #fafbfd;
  &-left {
    flex: 0 0 490px;
    padding: 0 24px;
    padding-top: 19px;
    background: #fff;
    padding-bottom: 20px;
    .left-title {
      color: #313238;
      font-size: 20px;
    }
    .left-message {
      height: 56px;
      border: 1px solid #a3c5fd;
      border-radius: 2px;
      background: #f0f8ff;
      margin-top: 12px;
      display: flex;
      padding-top: 10px;
      padding-right: 24px;
      .message-icon {
        flex: 0 0 36px;
        color: #3a84ff;
        width: 36px;
        text-align: center;
        font-size: 14px;
      }
      &.status-err {
        border-color: #fd9c9c;
        background: #ffeded;
        .message-icon {
          color: #ff5656;
        }
      }
      &-content {
        flex: 1;
        color: #63656e;
      }
    }
    .left-form {
      margin-top: 10px;
      /deep/ .bk-label {
        font-size: 12px;

        /* stylelint-disable-next-line declaration-no-important */
        width: 100% !important;
      }
      &-wrap {
        min-height: 272px;
        // overflow: auto;
        .mb10 {
          margin-bottom: 10px;
        }
        .wrap-empty {
          display: flex;
          height: 100%;
          align-items: center;
          justify-content: center;
          color: #979ba5;
          font-size: 14px;
        }
        /deep/.auto-complete-input {
          .group-prepend {
            flex-shrink: 0;
            padding: 0 20px;
          }
        }
        /deep/.step-verify-input {
          height: 32px;
          margin-bottom: 10px;
          &:last-child {
            margin-bottom: 0;
          }
          .tooltips-icon {
            /* stylelint-disable-next-line declaration-no-important */
            top: 8px!important;
          }
          .auto-complete-input {
            width: 100%;

            /* stylelint-disable-next-line declaration-no-important */
            margin-bottom: 0!important;
          }
          .auto-complete-input-select {
            height: 100%;
          }
        }
        /deep/.auto-complete-input-select {
          .bk-tooltip {
            // display: flex;
            height: 32px;
            .prepend-text {
              top: 0;
            }
          }
          .bk-select {
            height: 32px;
          }
        }
      }
      .update-footer {
        margin-top: 20px;
        &-btn {
          margin-right: 10px;
        }
      }
    }
  }
  &-right {
    flex: 1;
    background: #fafbfd;
    padding-left: 20px;
    max-height: 480px;
    overflow: auto;
    .right-title {
      margin: 22px 0 18px 0px;
      color: #63656e;
      font-size: 14px;
      font-weight: bold;
    }
    .right-content {
      height: 390px;
      overflow-x: visible;
      .record-list {
        padding: 0;
        margin: 0;
        color: #63656e;
        font-size: 12px;
        &-item {
          position: relative;
          .item-title {
            font-weight: bold;
            margin-left: 14px;
            &.current-item {
              color: #000;
              &::before {
                border: 2px solid #3a84ff;
                background: #fff;
                width: 6px;
                height: 6px;
                top: 4px;
                left: 0;
              }
            }
            &::before {
              content: " ";
              width: 6px;
              height: 6px;
              border-radius: 50%;
              position: absolute;
              top: 6px;
              left: 2px;
              background: #3a84ff;
            }

          }
          .item-wrap {
            margin: -2px 0 -2px 4px;
            min-height: 32px;
            border-left: 2px solid #dcdee5;
            padding: 10px 30px 10px 8px;
          }
        }
      }
    }
  }
}
</style>
