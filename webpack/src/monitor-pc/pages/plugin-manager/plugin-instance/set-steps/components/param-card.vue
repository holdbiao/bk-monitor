<template>
  <div :class="{ 'param-card': true, 'disabled': disabled }">
    <div class="title">{{title}}</div>
    <div class="content">
      <bk-input
        :disabled="disabled"
        :value="value"
        @change="handleChange"
        @blur="handleBlur"
        :placeholder="placeholder">
      </bk-input>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop } from 'vue-property-decorator'
@Component({
  name: 'param-card',
  model: {
    prop: 'value',
    event: 'change'
  }
})
export default class ParamCard extends Vue {
  @Prop({ type: String, default: '' })
  title: string

  @Prop({ type: String, default: '' })
  value: string

  @Prop({
    type: String,
    default: () => this.$t('请输入')
  })
  placeholder: string

  @Prop({ type: Boolean, default: false })
  disabled: boolean

  handleChange(val: string) {
    this.$emit('change', val)
  }

  handleBlur() {
    this.$emit('blur')
  }
}
</script>
<style lang="scss" scoped>
.param-card {
  width: 465px;
  height: 58px;
  border: 1px solid #dcdee5;
  background: #fff;
  &:hover {
    box-shadow: 0 2px 4px 0 rgba(0, 0, 0, .06);
  }
  &.disabled {
    background: #fafbfd;
    cursor: not-allowed;
    /deep/ .bk-form-input {
      border: 1px solid rgba(255, 255, 255, .5);

      /* stylelint-disable-next-line declaration-no-important */
      color: #000 !important;

      /* stylelint-disable-next-line declaration-no-important */
      border-color: #fafbfd !important;
    }
  }
  .title {
    color: #63656e;
    font-size: 12px;
    padding: 9px 15px 0 15px;
    margin-bottom: 1px;
  }
  .content {
    padding: 0 6px;
    /deep/ .bk-form-input {
      height: 26px;
      padding-left: 8px;
      border: 1px solid rgba(255, 255, 255, .5);
      color: #000;
      &:hover {
        background: #f5f6fa;
        color: #c4c6cc;
      }
      &:focus {
        color: #63656e;
      }
    }
  }
}
</style>
