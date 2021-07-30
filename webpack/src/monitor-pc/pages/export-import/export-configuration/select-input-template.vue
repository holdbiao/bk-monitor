<template>
  <div :tabindex="1" @blur="handleSelectBlur">
    <div class="select-node"
         :class="{ 'hight-lignt': listShow }"
         @click="handleSelectChange"
         @mouseenter="handleClearIconShow"
         @mouseleave="handleClearIconClose">
      <span v-if="!value" class="default-text">{{ placeholder }}</span>
      <span v-else>{{ value }}</span>
      <div class="focus" :class="{ 'transform': listShow }">
        <i class="bk-select-angle bk-icon icon-angle-down"></i>
      </div>
      <i class="bk-icon icon-close-circle-shape clear" v-if="iconShow" @click.stop="handleClearValue"></i>
    </div>
    <div class="select-node-content" v-show="listShow">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'select-input-template',
  props: {
    placeholder: {
      type: String,
      default() {
        return this.$t('请选择')
      }
    },
    value: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      listShow: false,
      iconShow: false
    }
  },
  methods: {
    handleSelectChange() {
      this.listShow = !this.listShow
    },
    handleSelectBlur() {
      this.listShow = false
    },
    // clear-icon显示
    handleClearIconShow() {
      this.iconShow = !!this.value
    },
    // clear-icon关闭
    handleClearIconClose() {
      this.iconShow = false
    },
    // clear-icon事件
    handleClearValue() {
      this.$emit('clear', this.value)
      this.iconShow = false
    }
  }
}
</script>

<style lang="scss" scoped>
  .select-node {
    width: 380px;
    height: 32px;
    background: #fff;
    border: 1px solid #c4c6cc;
    border-radius: 2px;
    padding: 0 8px 0 10px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    .default-text {
      color: #c4c6cc;
    }
  }
  .select-node-content {
    position: absolute;
    top: 34px;
    left: 126px;
    background: #fff;
    border: 1px solid #dcdee5;
    border-radius: 2px;
    box-shadow: 0 3px 6px 0 rgba(49, 50, 56, .15);
    width: 380px;
    max-height: 760px;
    z-index: 2;
  }
  .focus {
    display: flex;
    align-items: center;
    position: relative;
    transition: transform .3s cubic-bezier(.4,0,.2,1);
  }
  .clear {
    position: absolute;
    top: 9px;
    right: 8px;
    color: #c4c6cc;
    background: #fff;
    &:hover {
      color: #979ba5;
    }
  }
  .transform {
    transform: rotate(-180deg)
  }
  .hight-lignt {
    border: 1px solid #3a84ff;
    box-shadow: 0 0 4px rgba(58,132,255,.4);
  }
</style>
