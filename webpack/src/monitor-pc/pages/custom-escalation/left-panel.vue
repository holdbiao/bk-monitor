<template>
  <article class="download-panel">
    <!--标题-->
    <section class="download-panel-title">{{ title }}</section>
    <!--列表-->
    <section class="download-panel-content">
      <ul>
        <li v-for="(item, index) in list" :key="index" @mouseenter="handleMouseEnter(index)" @mouseleave="handleMouseLeave">
          <!--左侧图标-->
          <span class="content-item-left">
            <svg v-if="item.id === 'api'" class="icon" style="width: 32px; height: 32px;vertical-align: middle;fill: currentColor;overflow: hidden;" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="653"><path d="M192 0h640c105.6 0 192 86.4 192 192v640c0 105.6-86.4 192-192 192H192c-105.6 0-192-86.4-192-192V192c0-105.6 86.4-192 192-192z" fill="#E1ECFF" p-id="654" data-spm-anchor-id="a313x.7781069.1998910419.i2"></path><path d="M710.4 361.6H704c-12.8-96-92.8-169.6-188.8-169.6-80 0-150.4 51.2-176 124.8h-3.2c-112 0-204.8 96-204.8 211.2 0 67.2 32 131.2 86.4 172.8l25.6-73.6c-25.6-25.6-38.4-60.8-38.4-96 0-76.8 57.6-137.6 131.2-137.6h3.2c28.8 0 57.6-19.2 67.2-44.8 16-44.8 60.8-76.8 108.8-76.8 57.6 0 108.8 44.8 118.4 105.6 6.4 35.2 35.2 64 73.6 64h6.4c60.8 0 108.8 51.2 108.8 115.2 0 32-12.8 64-35.2 86.4v86.4c67.2-32 108.8-99.2 108.8-172.8-3.2-112-83.2-195.2-185.6-195.2z" fill="#3A84FF" p-id="655"></path><path d="M288 848H236.8l86.4-243.2H384l86.4 243.2h-51.2l-19.2-51.2h-96L288 848z m32-92.8h70.4l-32-102.4-38.4 102.4z m230.4 92.8h-51.2v-243.2h73.6c64 0 99.2 25.6 99.2 73.6-3.2 48-28.8 73.6-83.2 73.6h-38.4v96z m0-201.6v67.2h16c35.2 3.2 51.2-9.6 51.2-35.2 0-22.4-16-35.2-51.2-35.2-6.4 3.2-12.8 3.2-16 3.2z m204.8-41.6v243.2H704v-243.2h51.2z" fill="#3A84FF" p-id="656"></path></svg>
            <svg v-if="item.id === 'python'" class="icon" style="width: 32px; height: 32px;vertical-align: middle;fill: currentColor;overflow: hidden;" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="807"><path d="M192 0h640c105.6 0 192 86.4 192 192v640c0 105.6-86.4 192-192 192H192c-105.6 0-192-86.4-192-192V192c0-105.6 86.4-192 192-192z" fill="#DCE9F0" p-id="808"></path><path d="M582.4 134.4l28.8 6.4 22.4 9.6 19.2 9.6 16 9.6 9.6 9.6 9.6 9.6 6.4 9.6 3.2 9.6V416l-3.2 16-6.4 16-9.6 12.8-9.6 9.6-12.8 9.6-9.6 6.4-9.6 3.2-9.6 3.2-9.6 3.2H390.4l-19.2 3.2-19.2 12.8-12.8 9.6-9.6 9.6-9.6 9.6-6.4 12.8-3.2 12.8-3.2 9.6-3.2 9.6v112H224l-9.6-3.2-9.6-3.2-9.6-6.4-12.8-9.6-12.8-12.8-9.6-9.6-9.6-19.2-9.6-22.4-6.4-28.8-3.2-35.2v-38.4l3.2-38.4 6.4-32 6.4-28.8 9.6-22.4 12.8-19.2 12.8-12.8 12.8-9.6 12.8-6.4 12.8-6.4 12.8-3.2H512v-28.8h-185.6V192l3.2-9.6 6.4-9.6 9.6-9.6 6.4-6.4 12.8-6.4 12.8-6.4 16-3.2 19.2-3.2 19.2-3.2 22.4-3.2H547.2l35.2 3.2z m-198.4 64l-6.4 9.6-3.2 12.8 3.2 12.8 6.4 9.6 9.6 6.4 12.8 3.2 12.8-3.2 9.6-6.4 6.4-9.6 3.2-12.8-3.2-12.8-6.4-9.6-9.6-6.4-12.8-3.2-12.8 3.2-9.6 6.4z" fill="#0075AA" p-id="809"></path><path d="M800 323.2l9.6 3.2 9.6 3.2 9.6 6.4 12.8 9.6 12.8 9.6 9.6 16 9.6 19.2 9.6 22.4 6.4 28.8 3.2 32V512l-3.2 38.4-6.4 32-6.4 28.8-9.6 22.4-12.8 19.2-12.8 16-9.6 6.4-12.8 6.4-12.8 6.4-12.8 3.2H512v25.6h185.6v108.8l-3.2 9.6-6.4 9.6-9.6 9.6-9.6 9.6-12.8 6.4-12.8 6.4-16 3.2-19.2 3.2-19.2 3.2-22.4 3.2H473.6l-35.2-3.2-28.8-6.4-22.4-9.6-19.2-9.6-16-9.6-9.6-9.6-9.6-9.6-6.4-9.6-3.2-9.6V604.8l3.2-16 6.4-16 9.6-12.8 9.6-9.6 9.6-6.4 9.6-6.4 9.6-3.2 9.6-3.2 9.6-3.2h227.2l19.2-3.2 16-6.4 12.8-9.6 9.6-9.6 9.6-9.6 6.4-12.8 3.2-12.8 3.2-9.6 3.2-9.6v-112h70.4l19.2-9.6z m-208 451.2l-6.4 9.6-3.2 16 3.2 12.8 6.4 9.6 9.6 6.4 12.8 3.2 12.8-3.2 9.6-6.4 6.4-9.6 3.2-12.8-3.2-12.8-3.2-12.8-9.6-6.4-12.8-3.2-12.8 3.2-12.8 6.4z" fill="#FFBD01" p-id="810"></path></svg>
            <span class="item-name">{{ item.name }}</span>
          </span>
          <!--右侧悬浮操作-->
          <span class="content-item-right" v-show="hoverIndex === index">
            <i class="icon-monitor icon-mc-download item-hover-download" v-if="item.href">
              <a :href="item.href" :download="item.name"></a>
            </i>
            <i class="icon-monitor icon-mc-link item-hover-link ml10" @click="handleGotoLink(item.id)"></i>
          </span>
        </li>
      </ul>
    </section>
  </article>
</template>

<script lang="ts">
import { Component, Prop, Mixins } from 'vue-property-decorator'
import documentLinkMixin from '../../mixins/documentLinkMixin'

@Component
export default class leftPanel extends Mixins(documentLinkMixin) {
  // content item 列表
  @Prop({
    default: () => []
  }) readonly list: []

  // 标题
  @Prop({
    default() {
      return this.$t('使用说明及SDK下载')
    }
  }) readonly title: string

  // 当前悬浮 Item 的 index
  private hoverIndex = -1

  // 处理悬浮Icon
  handleMouseEnter(index: number) {
    this.hoverIndex = index
  }

  // 移除悬浮Icon
  handleMouseLeave() {
    this.hoverIndex = -1
  }
}
</script>

<style lang="scss" scoped>
  @import "../../static/css/common";

  $panelItemBorderColor: #a3c5fd;

  @mixin layout-flex($flexDirection, $alignItems, $justifyContent) {
    display: flex;
    flex-direction: $flexDirection;
    align-items: $alignItems;
    justify-content: $justifyContent;
  }

  .download-panel {
    padding: 26px 20px 20px 20px;
    &-title {
      font-weight: bold;
      color: $unsetIconColor;
    }
    &-content {
      .item-icon {
        font-size: 32px;
      }
      .item-hover-download {
        font-size: 18px;
        color: $primaryFontColor;
      }
      .item-hover-link {
        font-size: 16px;
        color: $primaryFontColor;
      }
      .item-name {
        margin-left: 12px;
        font-size: 14px;
        font-weight: bold;
        color: $defaultFontColor;
      }
      li {
        margin-top: 10px;
        padding: 0 12px 0 16px;
        width: 206px;
        height: 56px;
        border: 1px solid $defaultBorderColor;
        border-radius: 4px;
        cursor: pointer;

        @include layout-flex(row, center, space-between);
        &:hover {
          border-color: $panelItemBorderColor;
          box-shadow: 0px 2px 4px 0px rgba(58, 132, 255, .1);
        }
        .content-item-left {
          @include layout-flex(row, center, flex-start);
        }
        .content-item-right {
          @include layout-flex(row, center, flex-start);
        }
      }
    }
  }
</style>
