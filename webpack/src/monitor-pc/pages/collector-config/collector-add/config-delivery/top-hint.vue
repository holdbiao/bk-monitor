<template fuctional>
  <div class="top-hint">
    <i class="icon-monitor icon-tips hint-icon"></i>
    <div class="hint-text">
      <slot></slot>
    </div>
  </div>
</template>
<style lang="scss" scoped>
  .top-hint {
    display: flex;
    align-items: center;
    height: 36px;
    background: #f0f8ff;
    border-radius: 2px;
    border: 1px solid #a3c5fd;
    .hint-icon {
      flex: 0 0 16px;
      margin-left: 11px;
      font-size: 16px;
      color: #3a84ff;
    }
    .hint-text {
      flex: 1;
      margin-left: 9px;
      width: 223px;
      height: 16px;
      font-size: 12px;
      color: #63656e;
    }
  }
</style>
