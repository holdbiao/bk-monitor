<template>
  <bk-dialog :title="title"
             v-model="conf.isShow"
             header-position="left"
             width="480"
             :show-footer="false">
    <div class="param-body">
      <div class="item" v-for="(item, index) in conf.list" :key="index">
        <div class="label">{{item.label}} ：</div>
        <div class="value">{{item.value || '--'}}</div>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
export default {
  name: 'view-param',
  props: {
    title: String,
    conf: {
      type: Object,
      default: () => ({
        isShow: false,
        list: []
      })
    }
  }
}
</script>

<style lang="scss" scoped>
  .param-body {
    .item {
      display: flex;
      margin-bottom: 20px;
      .label {
        flex: 0 0 170px;
        text-align: right;
        font-size: 14px;
        color: #979ba5;
        margin-right: 24px;
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
</style>
