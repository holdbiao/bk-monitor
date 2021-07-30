<template>
  <section class="panel-card">
    <div class="panel-card-title clearfix">
      <span class="title-left">{{title || 'Title'}}</span>
      <slot name="title"></slot>
    </div>
    <div class="panel-card-content">
      <slot></slot>
    </div>
  </section>
</template>

<script>
export default {
  name: 'panel-card',
  props: {
    title: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../../common/mixins";

  .panel-card {
    padding: 18px 20px;
    &-title {
      margin-bottom: 14px;
      .title-left {
        height: 19px;
        font-size: $fontSmSize;
        font-weight: bold;
        line-height: 19px;
        float: left;
        color: $defaultFontColor;
      }
    }
  }
</style>
