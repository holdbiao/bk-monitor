<template>
  <ul class="chart-menu">
    <template v-for="item in menuList">
      <li
        class="chart-menu-item"
        :key="item.id"
        v-if="list.includes(item.id)"
        @mousedown="handleMenuClick(item)">
        <i class="menu-icon icon-monitor" :class="'icon-' + (!item.checked ? item.icon : item.nextIcon || item.icon)"></i>
        {{!item.checked ? item.name : item.nextName || item.name}}
        <i v-if="item.hasLink" class="icon-monitor icon-mc-link link-icon"></i>
      </li>
    </template>
  </ul>
</template>
<script lang="ts">
import { Component, Vue, Emit, Prop } from 'vue-property-decorator'
interface menuItem {
  id: string;
  name: string;
  nextName?: string;
  checked: boolean;
  icon: string;
  hasLink?: boolean;
  nextIcon?: string
}
@Component({
  name: 'chart-menu'
})
export default class ChartMenu extends Vue {
  @Prop({ default: () => [] }) list: string[]
  menuList: menuItem[] = []
  created() {
    this.menuList = [
      {
        name: this.$t('保存到仪表盘'),
        checked: false,
        id: 'save',
        icon: 'mc-mark'
      },
      {
        name: this.$t('截图到本地'),
        checked: false,
        id: 'screenshot',
        icon: 'mc-camera'
      },
      {
        name: this.$t('查看大图'),
        checked: false,
        id: 'fullscreen',
        icon: 'fullscreen'
      },
      {
        name: this.$t('检索'),
        checked: false,
        id: 'explore',
        icon: 'mc-retrieval',
        hasLink: true
      },
      {
        name: this.$t('添加策略'),
        checked: false,
        id: 'strategy',
        icon: 'menu-strategy',
        hasLink: true
      },
      {
        name: this.$t('Y轴固定最小值为0'),
        checked: false,
        id: 'set',
        nextName: this.$t('Y轴自适应'),
        icon: 'mc-yaxis',
        nextIcon: 'mc-yaxis-scale'
      },
      {
        name: this.$t('面积图'),
        checked: false,
        id: 'area',
        nextName: this.$t('线性图'),
        icon: 'mc-area',
        nextIcon: 'mc-line'
      }
    ]
  }
  @Emit('menu-click')
  handleMenuClick(item: menuItem) {
    item.checked = !item.checked
    return item
  }
}
</script>
<style lang="scss" scoped>
.chart-menu {
  width: 182px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  box-shadow: 0px 3px 6px 0px rgba(0,0,0,.15);
  padding: 6px 0;
  font-size: 12px;
  position: absolute;
  z-index: 999;
  &-item {
    display: flex;
    width: 100%;
    align-items: center;
    flex: 0 0 32px;
    padding-left: 12px;
    color: #63656e;
    font-weight: normal;
    &:hover {
      background: #f5f6fa;
      color: #3a84ff;
      cursor: pointer;
      .menu-icon {
        color: #3a84ff;
      }
    }
    .menu-icon,
    %menu-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      width: 12px;
      height: 12px;
      margin-right: 12px;
      color: #979ba5;
    }
    .link-icon {
      color: #979ba5;
      margin-left: auto;

      @extend %menu-icon;
      &:hover {
        color: #3a84ff;
      }
    }
  }
}
</style>
