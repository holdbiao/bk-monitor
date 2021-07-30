<template>
  <bk-dropdown-menu ext-cls="dropdown-menu" trigger="click" @show="dropdownShow" @hide="dropdownHide">
    <template slot="dropdown-trigger">
      <div class="dropdown-trigger">
        <div class="trigger-name">
          <i
            v-if="icon"
            :class="['icon-monitor', 'mr5', icon]"
            @click.stop="$emit('on-icon-click')">
          </i>
          <span
            :class="['trigger-text', { 'text-active': textActive }]"
            v-if="showName">
            {{ currentActive.name }}
          </span>
        </div>
        <i :class="['bk-icon icon-angle-down',{ 'icon-flip': isDropdownShow }]"></i>
      </div>
    </template>
    <template slot="dropdown-content">
      <ul class="dropdown-list">
        <li v-for="item in list"
            :key="item.id"
            :class="['dropdown-list-item', { 'active': active === item.id }]"
            @click="handleChangeActive(item.id)">
          <!-- 刷新文案改为关闭，但是选择后还是展示刷新 -->
          {{ item.name === $t('刷新') ? $t('关闭') : item.name }}
        </li>
      </ul>
    </template>
  </bk-dropdown-menu>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Model, Watch } from 'vue-property-decorator'
import { IOption } from '../performance-type'

@Component({ name: 'dropdown-menu' })
export default class DropDownMenu extends Vue {
  @Model('change', { default: '' }) readonly value: string | number
  @Prop({ default: () => [], type: Array }) readonly list: IOption[]
  @Prop({ default: '' }) readonly icon: string
  @Prop({ default: true }) readonly showName: boolean
  @Prop({ default: false }) readonly textActive: boolean

  private isDropdownShow = false
  private active: string | number = ''

  get currentActive() {
    if (this.list.length && this.active) {
      return this.list.find(item => item.id === this.active) || this.list[0]
    }
    return { id: 'unknown', name: this.$t('请选择') }
  }

  @Watch('value', { immediate: true })
  handleValueChange(v) {
    // this.handleChangeActive(v)
    this.active = v
  }

  dropdownShow() {
    this.isDropdownShow = true
  }

  dropdownHide() {
    this.isDropdownShow = false
  }

  @Emit('change')
  handleChangeActive(id: string | number) {
    this.active = id
    return this.active
  }
}
</script>
<style lang="scss" scoped>
.dropdown-menu {
  /* stylelint-disable-next-line declaration-no-important */
  width: inherit !important;
}
.dropdown-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 42px;
  padding: 0 10px 0 15px;
  &:hover {
    cursor: pointer;
    color: #3a84ff
  }
  .trigger-name {
    display: flex;
    align-items: center;
    height: 20px;
    i {
      font-size: 14px;
      height: 14px;
    }
    .text-active {
      color: #3a84ff;
    }
  }
  .icon-angle-down {
    font-size: 20px;
  }
}
.dropdown-list-item {
  padding: 0 15px;
  line-height: 32px;
  cursor: pointer;
  &.active {
    color: #3a84ff;
    background: #f5f6fa;
  }
  &:hover {
    cursor: pointer;
    background-color: #eaf3ff;
    color: #3a84ff;
  }
}
</style>
