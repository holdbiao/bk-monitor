<template>
  <div class="dimensions-panel">
    <div v-for="item in dimensionData.filter(item => !!item.name)"
         :key="item.id"
         class="dimensions-panel-item">
      <div class="item-title">{{ item.name }}</div>
      <div class="item-content">
        <bk-input
          class="item-content-select"
          size="small"
          v-model.trim="dimensionValues[item.id]"
          @click.native="handleShowMenu($event, item)"
          @change="handleSelectChange">
        </bk-input>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'
import SelectMenu, { IMenu } from './select-menu.vue'
import { Debounce } from '../../../../../monitor-common/utils/utils'

interface IDimensionOption {
  id: string
  name: string
  show: boolean
  list: IMenu[]
}

@Component({ name: 'strategy-view-dimensions' })
export default class DimensionsPanel extends Vue {
  // 维度列表
  @Prop({ default: () => [], type: Array }) private readonly dimensionData!: IDimensionOption[]
  // 当前可选项值
  @Prop({ default: () => ({}), type: Object }) private readonly currentDimensionMap: object

  private currentItem: IDimensionOption = null
  private dimensionValues = {}
  private menuInstance: SelectMenu = new SelectMenu().$mount()
  private popoverInstance = null

  created() {
    this.menuInstance.$on('click', this.handleMenuClick)
    this.menuInstance.$on('extension-click', this.handleExtensionClick)
  }

  beforeDestroy() {
    this.menuInstance.$off('click', this.handleMenuClick)
    this.menuInstance.$off('extension-click', this.handleExtensionClick)
  }

  @Debounce(300)
  @Emit('change')
  private handleSelectChange() {
    return JSON.parse(JSON.stringify(this.dimensionValues))
  }

  private handleMenuClick(menu: IMenu) {
    if (!this.currentItem) return

    this.$set(this.dimensionValues, this.currentItem.id, menu.id)
    this.popoverInstance && this.popoverInstance.hide()
    this.handleSelectChange()
  }

  private handleExtensionClick() {
    if (!this.currentItem) return

    this.menuInstance.$props.list = this.currentItem.list
    this.menuInstance.$props.showExtension = false
  }

  private handleShowMenu(event: Event, item: IDimensionOption) {
    if (!item.list || item.list.length === 0) return

    this.currentItem = item

    const currentDimensionList = this.currentDimensionMap[item.id]
    const showExtension = currentDimensionList && !!currentDimensionList.length
    this.menuInstance.$props.list = showExtension ? currentDimensionList : item.list
    this.menuInstance.$props.showExtension = showExtension

    this.popoverInstance = this.$bkPopover(event.target, {
      content: this.menuInstance.$el,
      trigger: 'manual',
      arrow: false,
      theme: 'light common-monitor',
      maxWidth: 280,
      sticky: true,
      duration: [275, 0],
      offset: '0, -8',
      interactive: true,
      onHidden: () => {
        this.popoverInstance && this.popoverInstance.destroy()
        this.popoverInstance = null
        this.currentItem = null
      }
    })
    this.popoverInstance.show()
  }
}
</script>
<style lang="scss" scoped>
.dimensions-panel {
  padding: 0 14px;
  display: flex;
  flex-wrap: wrap;
  &-item {
    display: flex;
    align-items: center;
    height: 24px;
    line-height: 24px;
    margin-right: 5px;
    margin-bottom: 10px;
    .item-title {
      background: #f0f1f5;
      border: 1px solid #c4c6cc;
      border-radius: 2px 0px 0px 2px;
      padding: 0 10px;
    }
    .item-content-select {
      margin-left: -1px;
      min-width: 100px;
    }
  }
}
</style>
