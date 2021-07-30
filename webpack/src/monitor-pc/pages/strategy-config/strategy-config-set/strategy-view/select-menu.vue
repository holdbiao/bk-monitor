<template>
  <div class="select-menu">
    <ul class="menu">
      <li v-for="(item, index) in list"
          :key="index"
          class="menu-item"
          :style="{ 'text-align': align }"
          :disabled="item.disabled"
          :title="item.name"
          v-show="!item.hidden"
          @click="!item.disabled && handleMenuClick(item)">
        {{ item.name }}
      </li>
    </ul>
    <div class="extension"
         v-show="showExtension"
         @click="handleExtensionClick">
      {{ extensionText }}
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'

export interface IMenu {
  id: string | number
  name: string
  readonly?: boolean
  disabled?: boolean
  hidden?: boolean
}

@Component({ name: 'select-menu' })
export default class Menu extends Vue {
  @Prop({ default: () => [], type: Array }) private readonly list!: IMenu[]
  @Prop({ default: 'left', type: String }) private readonly align!: string
  @Prop({ default: false, type: Boolean }) private readonly showExtension!: boolean

  private extensionText = window.i18n.t('全部选项')

  @Emit('click')
  private handleMenuClick(item: IMenu) {
    return item
  }

  @Emit('extension-click')
  private handleExtensionClick() {}
}
</script>
<style lang="scss" scoped>
.menu {
  font-size: 12px;
  padding: 6px 0;
  min-width: 84px;
  background: #fff;
  border: 1px solid #dcdee5;
  max-height: 260px;
  overflow: auto;
  &-item {
    height: 32px;
    line-height: 32px;
    padding: 0 10px;
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    word-break: break-all;
    &:hover {
      background: #f5f6fa;
      color: #3a84ff;
    }
  }
  &-item[disabled] {
    color: #c4c6cc;
    cursor: not-allowed;
  }
}
.extension {
  height: 32px;
  border: 1px solid #dcdee5;
  border-top: 0;
  display: flex;
  align-items: center;
  background-color: #fafbfd;
  padding: 0 15px;
  cursor: pointer;
}
</style>
