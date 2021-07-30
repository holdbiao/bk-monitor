<template>
  <div class="page-tips-wrap">
    <span class="icon-monitor icon-tips"></span>
    <span class="text">
      {{tipsText}}
      <span class="link" @click="handleOpenLink(linkUrl)">{{linkText}}</span>
      <span class="link" @click="handleGotoLink(docLink)" v-if="docLink">{{$t('相关文档查看')}}</span>
    </span>
  </div>
</template>
<script lang="ts">
import { Component, Prop, Mixins } from 'vue-property-decorator'
import documentLinkMixin from '../../mixins/documentLinkMixin'

@Component({
  name: 'page-tips'
})
export default class PageTips extends Mixins(documentLinkMixin) {
  @Prop({ default: '', type: String }) private readonly tipsText: string
  @Prop({ default: '', type: String }) private readonly linkText: string
  @Prop({ default: '', type: String }) private readonly linkUrl: string
  @Prop({ default: '', type: String }) private readonly docLink: string

  public handleOpenLink(url: string) {
    window.open(url, '_blank')
  }
}
</script>
<style lang="scss" scoped>
.page-tips-wrap {
  display: flex;
  align-items: center;
  min-height: 32px;
  background: #f0f8ff;
  border: 1px solid #c5daff;
  border-radius: 2px;
  font-size: 0;
  padding: 0 10px;
  span {
    font-size: 12px;
  }
  .icon-tips {
    display: flex;
    align-items: center;
    font-size: 16;
    color: #3a84ff;
    margin-right: 8px;
  }
  .text {
    padding: 7px 0;
    line-height: 16px;
    margin-right: 4px;
  }
  .link {
    margin-right: 4px;
    color: #3a84ff;
    cursor: pointer;
    white-space: nowrap;
  }
}
</style>
