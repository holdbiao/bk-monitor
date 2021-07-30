<template>
  <ul class="preview-template">
    <li v-for="(item,index) in renderList" :key="index" class="preview-template-item">
      <h5 class="item-title">{{item.name}}</h5>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="item-template" :class="{ 'no-br': item.tabActive === 1 }" v-html="item.message">
      </div>
    </li>
  </ul>
</template>
<script>
export default {
  name: 'preview-template',
  props: {
    // 需要渲览预览通知模板
    renderList: {
      type: Array,
      required: true
    }
  }
}
</script>
<style lang="scss" scoped>
  .preview-template {
    display: flex;
    flex-direction: column;
    color: #63656e;
    font-size: 14px;
    height: 390px;
    overflow: auto;
    margin-bottom: 2px;
    margin-right: -22px;
    &-item {
      margin-top: 17px;
      padding-right: 22px;
      .item-title {
        font-weight: 500;
        margin-bottom: 7px;
        margin-top: 0;
      }
      .item-template {
        &.no-br {
          /deep/ br {
            display: none;
          }
        }
        /deep/ div {
          /* stylelint-disable-next-line declaration-no-important */
          background-color: white !important;
        }
      }
    }
  }
</style>
