<template>
  <article>
    <!--空数据-->
    <section class="content-empty">
      <span class="empty-icon"><i class="icon-monitor" :class="icon"></i></span>
      <span class="empty-drop">{{ title }}</span>
      <span class="empty-tip" v-if="subTitle">{{ subTitle }}</span>
    </section>
  </article>
</template>
<script>
export default {
  name: 'content-empty',
  props: {
    // icon
    icon: {
      type: String,
      default: 'icon-hint'
    },
    // title
    title: {
      type: String,
      default() {
        return this.$t('无数据')
      }
    },
    // subtitle
    subTitle: {
      type: String,
      default: ''
    }
  }
}
</script>
<style lang="scss" scoped>
  @import "../../../static/css/common";

  $emptyTipColor: #979ba5;

  @mixin layout-flex($flexDirection: row, $alignItems: stretch, $justifyContent: flex-start) {
    display: flex;
    flex-direction: $flexDirection;
    align-items: $alignItems;
    justify-content: $justifyContent;
  }

  .content-empty {
    @include layout-flex(column, center);
    .empty-icon {
      height: 42px;
      width: 42px;
      font-size: 42px;
      color: $slightFontColor;
    }
    .empty-drop {
      margin-top: 6px;
      line-height: 19px;
      font-size: 14px;
      font-weight: bold;
      color: $defaultFontColor;
    }
    .empty-tip {
      margin-top: 6px;
      line-height: 16px;
      color: $emptyTipColor;
    }
  }
</style>
