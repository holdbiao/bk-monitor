<template>
  <bk-dialog
    :value="show"
    theme="primary"
    :mask-close="false"
    header-position="left"
    @after-leave="handleCancel"
    :show-footer="!disabledEditConfig"
    :width="480"
    :title="$t(disabledEditConfig ? $t('参数详情') : $t('定义参数'))">
    <div class="readonly-param" v-if="disabledEditConfig">
      <div class="item" v-for="(item, index) in readonlyParam" :key="index">
        <div class="label">{{item.label}} ：</div>
        <div class="value">{{item.value || '--'}}</div>
      </div>
    </div>
    <div class="param-html" v-else>
      <div class="item-param param-type">
        <span class="item-required"> {{ $t('参数类型') }} </span>
        <bk-select v-model="config.types.type" :clearable="false" @change="handleTypeChange">
          <bk-option
            v-show="type.id !== 'collector'"
            v-for="(type, index) in config.types.list" :id="type.id" :name="type.name" :key="index">
          </bk-option>
        </bk-select>
      </div>
      <span class="type-des">{{typeDes[config.types.type] }}</span>
      <div class="item-param">
        <span class="item-required"> {{ $t('参数名称') }} </span>
        <verify-input :show-validate.sync="rules.name.error" :validator="{ content: rules.name.message }">
          <bk-input v-model="config.paramName" :clearable="true"></bk-input>
        </verify-input>
      </div>
      <div class="item-param">
        <span> {{ $t('默认值') }} </span>
        <div class="default-value">
          <div :class="['value-type', { 'is-input': ['text', 'password', 'file'].includes(config.default.type) }]">
            <bk-select :clearable="false" v-model="config.default.type" @selected="handleDefaultTypeChange">
              <bk-option v-for="(item) in defaultTypeList" :key="item.id" :id="item.id" :name="item.name"></bk-option>
            </bk-select>
          </div>
          <div class="value">
            <bk-input v-model="config.default.value" v-if="config.default.type === 'text'"></bk-input>
            <bk-input v-model="config.default.value" v-else-if="['password', 'encrypt'].includes(config.default.type)" type="password" ext-cls="value-password"></bk-input>
            <bk-switcher
              v-else-if="config.default.type === 'switch'"
              class="value-switch"
              true-value="true"
              false-value="false"
              v-model="config.default.value">
            </bk-switcher>
            <div class="file-input-wrap" v-else-if="config.default.type = 'file'">
              <import-file
                :file-name="config.default.value"
                :file-content="config.default.fileBase64"
                @change="handleFileChange"
                @error-message="handleImportError">
              </import-file>
              <div v-if="fileErrorMsg" class="error-msg">{{ fileErrorMsg }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="item-param">
        <span> {{ $t('参数说明') }} </span>
        <bk-input v-model="config.description"></bk-input>
      </div>
    </div>
    <div slot="footer">
      <bk-button class="mr-5" theme="primary" :title="$t('提交')" :disabled="disabledEditConfig" @click="handleConfirm" @keyup.enter="handleConfirm"> {{ $t('提交') }} </bk-button>
      <bk-button theme="default" :title="$t('取消')" @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </div>
  </bk-dialog>
</template>
<script>
import VerifyInput from '../../../../../components/verify-input/verify-input'
import importFile from './import-file'
export default {
  name: 'ConfigParam',
  components: {
    VerifyInput,
    importFile
  },
  props: {
    show: Boolean,
    param: {
      type: Object,
      default: () => ({})
    },
    paramList: {
      type: Array,
      default: () => ({})
    },
    pluginType: {
      type: String,
      default: 'Script'
    }
  },
  data() {
    return {
      labels: {
        mode: this.$t('参数类型1'),
        name: this.$t('参数名称1'),
        default: this.$t('默认值'),
        description: this.$t('参数说明1')
      },
      types: {
        text: this.$t('文本'),
        file: this.$t('文件'),
        password: this.$t('密码'),
        switch: this.$t('开关')
      },
      typeDes: {
        opt_cmd: `${this.$t('最常用的参数使用方式。如')}--port 3306`,
        env: `${this.$t('在程序中直接获取环境变量中的变量如')}os.getenv('PYTHONPATH')`,
        pos_cmd: `${this.$t('基于参数传递的顺序进行变量的获取,由添加参数的顺序决定,如Shell中常见的echo')} $1`
      },
      config: {
        types: {
          list: [
            {
              id: 'opt_cmd',
              name: this.$t('命令行参数')
            },
            {
              id: 'env',
              name: this.$t('环境变量')
            },
            {
              id: 'pos_cmd',
              name: this.$t('位置参数')
            },
            {
              id: 'collector',
              name: this.$t('采集器参数')
            }
          ],
          type: 'opt_cmd'
        },
        default: {
          list: [
            {
              name: this.$t('文本'),
              id: 'text'
            },
            {
              name: this.$t('强密码'),
              id: 'encrypt'
            },
            {
              name: this.$t('密码'),
              id: 'password'
            },
            {
              name: this.$t('文件'),
              id: 'file'
            },
            {
              name: this.$t('开关'),
              id: 'switch'
            }
          ],
          type: 'text',
          value: ''
        },
        paramName: '',
        description: ''
      },
      rules: {
        name: {
          error: false,
          message: this.$t('请输入参数名')
        }
      },
      fileErrorMsg: ''
    }
  },
  computed: {
    // 禁止编辑
    disabledEditConfig() {
      return this.param.disabled
    },
    // 只读参数
    readonlyParam() {
      const param = this.param || {}
      const result = []
      Object.keys(this.labels).forEach((key) => {
        result.push({
          label: this.labels[key],
          value: key === 'default'
            ? (`${param[key]}`.length
              ? `${this.types[param.type]}=${param[key]}`
              : this.types[param.type])
            : param[key]
        })
      })
      return result
    },
    defaultTypeList() {
      let defaultList = []
      if (this.pluginType !== 'Exporter') {
        defaultList = this.config.default.list.filter(item => item.id !== 'encrypt')
      } else {
        defaultList = this.config.default.list
      }
      if (this.config.types.type === 'opt_cmd') {
        return defaultList
      }
      return defaultList.filter(item => item.id !== 'switch')
    }
  },
  watch: {
    show(val) {
      if (val) {
        this.initProps()
        /**
                     * @description 如果有值，则回填
                     */
        if (Object.keys(this.param).length) {
          const { param } = this
          this.config.paramName = param.name
          this.config.types.type = param.mode
          this.config.default.type = param.type
          this.config.default.value = param.default
          this.config.description = param.description
          param.type === 'file' && (this.config.default.fileBase64 = param.file_base64)
        }
      } else if (this.rules.name.error) {
        this.rules.name.error = false
      }
    }
  },
  methods: {
    handleConfirm() {
      const name = this.config.paramName.trim()
      this.rules.name.error = !name
      if (this.rules.name.error) {
        this.rules.name.message = this.$t('请输入参数名')
        return
      }
      if (this.config.default.type === 'file' && this.fileErrorMsg) return
      const param = {
        name,
        mode: this.config.types.type,
        type: this.config.default.type,
        default: ['text', 'password'].includes(this.config.default.type)
          ? this.config.default.value.trim()
          : this.config.default.value,
        description: this.config.description.trim()
      }
      this.config.default.type === 'file' && (param.file_base64 = this.config.default.fileBase64)
      this.$emit('confirm', param)
      this.$emit('update:show', false)
    },
    handleCancel() {
      this.$emit('update:show', false)
    },
    /**
             * @description 初始化表单属性
             */
    initProps() {
      this.config.paramName = ''
      this.config.description = ''
      this.config.default.value = ''
      this.config.default.type = 'text'
      this.config.types.type = 'opt_cmd'
    },
    handleDefaultTypeChange(type) {
      const typeMap = {
        text: () => this.config.default.value = '',
        password: () => this.config.default.value = '',
        file: () => {
          this.config.default.value = ''
          this.$set(this.config.default, 'fileBase64', '')
        },
        switch: () => this.config.default.value = this.config.default.value || 'false',
        encrypt: () => this.config.default.value = ''
      }
      this.fileErrorMsg = ''
      typeMap[type]?.()
    },
    handleTypeChange(nv, ov) {
      if (ov === 'opt_cmd' && this.config.default.type === 'switch') {
        this.config.default.type = 'text'
        this.config.default.value = ''
      }
    },
    handleFileChange(fileInfo) {
      this.config.default.value = fileInfo.name
      this.config.default.fileBase64 = fileInfo.fileContent
    },
    handleImportError(msg) {
      this.fileErrorMsg = msg
    }
  }
}
</script>
<style lang="scss" scoped>
.param-html {
  .item-param {
    margin-bottom: 17px;
    .item-required::after {
      position: relative;
      top: -1px;
      left: 3px;
      content: "*";
      color: red;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }
  .param-type {
    margin-bottom: 0;
  }
  .type-des {
    font-size: 12px;
  }
  .default-value {
    display: flex;
    .value-type {
      flex: 0 0 94px;
    }
    .is-input {
      /deep/ .bk-select {
        border-right: 0;
        box-shadow: none;
        border-radius: 2px 0 0 2px;
      }
    }
    .value {
      display: flex;
      align-items: center;
      flex: 1;
      /deep/ .bk-form-input {
        border-radius: 0 2px 2px 0;
      }
      /deep/ .value-password {
        .control-icon {
          display: none;
        }
      }
      .value-switch {
        margin-left: 20px;
      }
    }
    .file-input-wrap {
      flex: 1;
      height: 32px;
      .monitor-import {
        display: flex;
        align-items: center;
        vertical-align: middle;
        margin: 0;
      }
      .error-msg {
        padding-top: 6px;
        color: #f56c6c;
        font-size: 12px;
      }
    }
  }
}
.readonly-param {
  .item {
    display: flex;
    margin-bottom: 20px;
    .label {
      flex: 0 0 170px;
      text-align: right;
      font-size: 14px;
      color: #979ba5;
      margin-right: 10px;
    }
    .value {
      flex: 1;
      word-break: break-all;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }
}
.mr-5 {
  margin-right: 5px;
}
</style>
