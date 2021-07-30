<template>
  <div>
    <span
      class="mneu-wrap"
      v-authority="{ active: !hasAuth }"
      @click="handleClick"
      ref="menuIcon">
      <slot>
        New <i class="icon-monitor icon-mc-add mneu-wrap-icon"></i>
      </slot>
    </span>
    <div v-show="false">
      <ul class="menu-list" ref="menuList">
        <li class="menu-list-item"
            v-for="item in menuList"
            :key="item.id"
            @click="$emit('item-click', item)">
          {{item.name}}
        </li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Ref, Watch } from 'vue-property-decorator'
@Component
export default class SetMenu extends Vue {
  @Ref('menuList') menuListRef: HTMLUListElement
  @Ref('menuIcon') menuIconRef: HTMLUListElement
  @Prop({ required: true }) menuList: {name: string; id: string}[]
  @Prop({ default: true }) hasAuth: boolean
  instance: any = null
  @Watch('hasAuth')
  onHasAuthChange() {
    this.handlePopover()
  }
  mounted() {
    this.handlePopover()
  }
  handlePopover() {
    if (!this.instance && this.hasAuth) {
      this.instance = this.$bkPopover(this.menuIconRef, {
        content: this.menuListRef,
        arrow: false,
        trigger: 'click',
        placement: 'bottom',
        theme: 'light common-monitor',
        maxWidth: 520,
        duration: [275, 0],
        offset: '10, 2'
      })
    } else if (this.instance) {
      this.instance.hide()
      this.instance.destroy()
      this.instance = null
    }
  }
  handleClick() {
    this.$emit('click')
  }
}
</script>
<style lang="scss" scoped>
.mneu-wrap {
  font-size: 12px;
  background: #3a84ff;
  border-color: #3a84ff;
  color: #fff;
  padding: 0 12px;
  border-radius: 2px;
  margin-left: 15px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  &-icon {
    font-size: 16px;
    height: 26px;
    width: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  &:hover {
    cursor: pointer;
    background-color: #699df4;
    opacity: 1;
  }
}
.menu-list {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  background-color: white;
  padding: 6px 0;
  &-item {
    display: flex;
    align-items: center;
    line-height: 32px;
    height: 32px;
    padding: 0 12px;
    color: #63656e;
    &:hover {
      cursor: pointer;
      background-color: #eaf3ff;
      color: #3a84ff;
    }
  }
}
</style>
