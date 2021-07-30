<template>
  <span class="" @click="handleShowFilterList($event)">
    <i :class="[
      'ml5 icon-monitor icon-filter-fill',
      { 'active': active }
    ]"></i>
  </span>
</template>
<script lang="ts">
import { Component, Vue, Prop, Emit, Watch } from 'vue-property-decorator'
import MonitorVue from '../../types/index'
import LabelMenu from './label-menu.vue'
import i18n from '../../i18n/i18n'

interface IOption {
  id: string
  name: string
  checked: boolean
}

@Component({ name: 'filter-funnel' })
export default class FilterFunnel extends Vue<MonitorVue> {
  @Prop({ default: () => [] }) readonly data: IOption[]

  private labelMenuInstance: LabelMenu = null
  private instance: any = null
  private list: IOption[] = []

  get active() {
    return this.list.some(item => item.checked)
  }

  @Watch('data', { deep: true, immediate: true })
  handleDataChange() {
    this.handleResetList()
  }

  public handleShowFilterList(e: Event) {
    if (!this.labelMenuInstance) {
      this.labelMenuInstance = new LabelMenu({
        i18n
      }).$mount()
      this.labelMenuInstance.list = this.list
      this.labelMenuInstance.$on('confirm', () => {
        this.handleConfirm()
      })
      this.labelMenuInstance.$on('clear', () => {
        this.handleClear()
      })
    }
    if (!this.instance) {
      this.instance = this.$bkPopover(e.target, {
        content: this.labelMenuInstance.$el,
        trigger: 'manual',
        arrow: false,
        theme: 'light common-monitor table-filter',
        maxWidth: 280,
        offset: '0, 5',
        sticky: true,
        duration: [275, 0],
        interactive: true,
        onHidden: () => {
          this.handleResetList()
        }
      })
    }
    this.instance && this.instance.show(100)
  }

  @Emit('clear')
  public handleClear(): IOption[] {
    this.instance && this.instance.hide()
    return JSON.parse(JSON.stringify(this.list))
  }

  @Emit('confirm')
  public handleConfirm(): IOption[] {
    this.instance && this.instance.hide()
    return JSON.parse(JSON.stringify(this.list))
  }

  public handleResetList() {
    this.list = JSON.parse(JSON.stringify(this.data))
    this.labelMenuInstance && (this.labelMenuInstance.list = this.list)
  }
}
</script>
<style lang="scss" scoped>
.icon-filter-fill {
  color: #c0c4cc;
  cursor: pointer;
  &.active {
    color: #3a84ff;
  }
}
</style>

