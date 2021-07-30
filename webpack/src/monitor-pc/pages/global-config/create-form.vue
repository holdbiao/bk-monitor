<template>
  <div class="create-form">
    <bk-form ref="createForm" :model="model" :rules="rules" v-bind="formProps">
      <bk-form-item class="create-form-item" v-for="(item,index) in formList" :key="index" v-bind="item.formItemProps" :icon-offset="item.type === 'input' && item.formChildProps.type === 'number' ? 358 : 8">
        <component :is="'bk-' + item.type" v-bind="item.formChildProps" :style="{ width: item.type === 'input' && item.formChildProps.type === 'number' ? '120px' : '' }" v-model="model[item.formItemProps.property]">
          <template v-if="item.type === 'select'">
            <bk-option v-for="option in item.formChildProps.options"
                       :key="option.id"
                       :id="option.id"
                       :name="option.name">
            </bk-option>
          </template>
          <template v-else-if="item.type === 'checkbox-group'">
            <bk-checkbox v-for="option in item.formChildProps.options" :key="option.id" :value="option.id">
              {{option.name}}
            </bk-checkbox>
          </template>
          <template v-else-if="item.type === 'radio-group'">
            <bk-radio v-for="option in item.formChildProps.options" :key="option.id" :value="option.id">
              {{option.name}}
            </bk-radio>
          </template>
        </component>
        <template v-if="item.formItemProps.help_text">
          <div class="form-desc">{{item.formItemProps.help_text}}</div>
        </template>
      </bk-form-item>
      <bk-form-item>
        <bk-button
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="footer-btn"
          theme="primary"
          @click="authority.MANAGE_AUTH ? handleConfirm() : handleShowAuthorityDetail()"
          :loading="isChecking">
          {{ $t('提交') }}
        </bk-button>
        <bk-button theme="default" @click="handleReset"> {{ $t('重置') }} </bk-button>
      </bk-form-item>
    </bk-form>
  </div>
</template>
<script>
export default {
  name: 'create-form',
  props: {
    // 验证信息
    rules: {
      type: Object,
      default() {
        return {}
      }
    },
    // form model数据集
    model: {
      type: Object,
      required: true
    },
    // form配置列表
    formList: {
      type: Array,
      required: true
    },
    validate: Function,
    // form属性
    formProps: {
      type: Object,
      default() {
        return {
          'label-width': 200
        }
      }
    }
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  data() {
    return {
      isChecking: false
    }
  },
  methods: {
    // 点击提交触发
    handleConfirm() {
      this.$emit('save', this.$refs.createForm.validate)
    },
    // 点击重置
    handleReset() {
      this.$emit('reset', this.model)
    }
  }
}
</script>
<style lang="scss" scoped>
  .create-form {
    max-width: 656px;
    &-item {
      /deep/ .bk-select {
        background-color: #fff;
      }
      /deep/ .bk-form-radio {
        margin-right: 30px;
        .bk-checkbox {
          background-color: #fff;
        }
      }
      /deep/ .bk-form-checkbox {
        margin-right: 30px;
      }
      /deep/ .bk-label {
        min-width: 120px;
        span {
          line-height: 20px;
          display: inline-block;
        }
      }
      /deep/ .bk-tag-selector {
        .bk-select-dropdown {
          min-height: 27px;
        }
      }
      .form-desc {
        color: #979ba5;
        font-size: 12px;
        line-height: 16px;
        margin-top: 4px;
      }
    }
    .footer-btn {
      margin-right: 10px;
    }
  }
</style>
