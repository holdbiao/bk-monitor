<template>
  <div class="process-params">
    <div class="form-item">
      <label class="item-label required">{{ $t('选择插件') }}</label>
      <div class="item-content">
        <bk-input :value="pluginDisplayName" readonly></bk-input>
      </div>
    </div>
    <div class="form-item">
      <label class="item-label required">{{ $t('进程匹配') }}</label>
      <div class="item-content">
        <bk-radio-group v-model="params.match_type" class="process-match">
          <bk-radio value="command">
            {{ $t('命令行匹配') }}
          </bk-radio>
          <bk-radio value="pid" class="ml20">
            {{ $t('pid文件') }}
          </bk-radio>
        </bk-radio-group>
        <div v-if="params.match_type === 'command'">
          <verify-input
            class="small-input validate-icon"
            position="right"
            :show-validate.sync="rules.match_pattern"
            :validator="{ content: $t('必填项') }">
            <bk-input class="mt10 small-input" v-model="params.match_pattern">
              <template slot="prepend">
                <div class="group-text" :placeholder="$t('进程关键字')">{{ $t('包含') }}</div>
              </template>
            </bk-input>
          </verify-input>


          <bk-input class="mt10 small-input" v-model="params.exclude_pattern">
            <template slot="prepend">
              <div class="group-text" :placeholder="$t('进程排除正则')">{{ $t('排除') }}</div>
            </template>
          </bk-input>
        </div>
        <template v-else-if="params.match_type === 'pid'">
          <verify-input
            class="small-input validate-icon"
            position="right"
            :show-validate.sync="rules.pid_path"
            :validator="{ content: $t('必填项') }">
            <bk-input class="mt10 small-input" :placeholder="$t('进程的pid绝对路径')" v-model="params.pid_path"></bk-input>
          </verify-input>
        </template>
      </div>
    </div>
    <div class="form-item">
      <label class="item-label">{{ $t('进程名') }}</label>
      <div class="item-content">
        <bk-input :placeholder="$t('留空默认以二进制名称，可以手动指定或者取值')" v-model="params.process_name"></bk-input>
      </div>
    </div>
    <div class="form-item">
      <label class="item-label">{{ $t('端口探测') }}</label>
      <div class="item-content">
        <bk-switcher
          v-model="params.port_detect"
          show-text
          :on-text="$t('开')"
          :off-text="$t('关')"
          size="small"
          theme="primary">
        </bk-switcher>
      </div>
    </div>
  </div>
</template>
<script>
import VerifyInput from '../../../plugin-manager/plugin-instance/set-steps/verify-input'
export default {
  name: 'ProcessParams',
  components: {
    VerifyInput
  },
  props: {
    processParams: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      params: Object.assign({
        match_type: 'pid',
        pid_path: '',
        process_name: '',
        match_pattern: '',
        exclude_pattern: '',
        port_detect: true,
        labels: {}
      }, this.processParams),
      rules: {
        pid_path: false,
        match_pattern: false
      },
      pluginDisplayName: this.$t('进程采集插件')
    }
  },
  watch: {
    params: {
      deep: true,
      handler(newValue, oldValue) {
        this.$emit('change', newValue, oldValue)
      }
    }
  },
  methods: {
    // 校验
    validate() {
      if (this.params.match_type === 'pid') {
        this.rules.pid_path = !this.params.pid_path
        return !!this.params.pid_path
      }
      this.rules.match_pattern = !this.params.match_pattern
      return  !!this.params.match_pattern
    }
  }
}
</script>
<style lang="scss" scoped>
.small-input {
  width: 320px;
  &.validate-icon {
    /deep/ .tooltips-icon {
      right: 5px;
      top: 18px;
    }
  }
}
.form-item {
  display: flex;
  margin-bottom: 20px;
  .item-label {
    min-width: 75px;
    height: 32px;
    line-height: 32px;
    text-align: right;
    margin-right: 34px;
    position: relative;
    &.required {
      &::after {
        content: "*";
        position: absolute;
        color: #f00;
        right: -9px;
        font-size: 12px;
      }
    }
  }
  .item-content {
    width: 500px;
    /deep/ .bk-radio-text {
      font-size: 12px;
    }
  }
}
</style>
