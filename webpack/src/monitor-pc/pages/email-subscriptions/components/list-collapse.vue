<template>
  <div class="list-collapse-wrap">
    <bk-collapse
      :custom-trigger-area="true"
      :value="activeName"
      @item-click="handleItemClick">
      <bk-collapse-item
        class="list-item"
        name="1"
        :hide-arrow="true">
        <div class="list-header">
          <span :class="['icon-monitor', 'icon-Triangle-down', { 'icon-Triangle-down-hidden': activeName.indexOf('1') === -1 }]"></span>
          <span class="title">{{title}}</span>
          <slot name="header-btn"></slot>
        </div>
        <div slot="content" class="list-content">
          <slot name="content"></slot>
        </div>
      </bk-collapse-item>
    </bk-collapse>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'
/**
 * 邮件订阅列表页
 */
@Component({
  name: 'email-subscriptions'
})
export default class EmailSubscriptions extends Vue {
  @Prop({ default: '', type: String }) private readonly title: string
  @Prop({ default: [], type: Array }) private readonly activeName: string[]

  @Emit('item-click')
  handleItemClick(arr: string[]) {
    return arr
  }
}
</script>

<style lang="scss" scoped>
.list-collapse-wrap {
  .list-item {
    /deep/.bk-collapse-item-header,
    /deep/.bk-collapse-item-content {
      padding: 0;
    }
    .list-header {
      display: flex;
      align-items: center;
      height: 42px;
      padding: 0 16px;
      border: 1px solid #dcdee5;
      // border-bottom: 0;
      border-radius: 2px 2px 0px 0px;
      background: #f0f1f5;
      .icon-Triangle-down {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 24px;
        height: 24px;
        font-size: 24px;
        margin-right: 2px;
        &::before {
          margin-top: -2px;
        }
      }
      .icon-Triangle-down-hidden {
        transform: rotate(-90deg);
      }
    }
    .list-content {
      /deep/.bk-table {
        /* stylelint-disable-next-line declaration-no-important */
        margin-top: 0!important;
        border-top: 0;
      }
    }
  }
}
</style>
