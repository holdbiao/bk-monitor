<template>
  <span key="preAdd"
        v-if="addType === 'common'"
        class="input-add"
        @click.stop.prevent="handleAddClick">
    <i class="bk-icon icon-plus"></i>
  </span>
  <span v-else class="input-title" @click.stop.prevent="handleAddClick">
    {{addTitle}}
    <span class="input-title-desc">{{addDesc}}</span>
  </span>
</template>
<script>
export default {
  name: 'set-add',
  props: {
    // character 为文字按钮
    addType: {
      type: String,
      default: 'common',
      validator(v) {
        return ['common', 'character'].includes(v)
      }
    },
    // 文字按钮按钮时显示的名称
    addTitle: {
      type: String,
      default() {
        return this.$t('点击添加')
      }
    },
    addDesc: {
      type: String,
      default: ''
    }
  },
  methods: {
    handleAddClick(e) {
      this.$emit('set-add', e)
    }
  }
}
</script>
<style lang="scss" scoped>
  .input-add {
    box-sizing: border-box;
    width: 32px;
    height: 32px;
    border-radius: 2px;
    background-color: #f0f1f5;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3a84ff;
    cursor: pointer;
    margin-right: 2px;
    margin-top: 2px;
    .icon-plus {
      // font-weight: bold;
      font-size: 24px;
    }
    &:hover {
      cursor: pointer;
    }
  }
  .input-title {
    color: #3a84ff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    &:hover {
      cursor: pointer;
    }
    &-desc {
      color: #c4c6cc;
    }
  }
</style>
