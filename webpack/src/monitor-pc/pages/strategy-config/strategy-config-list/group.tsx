import { Component, Emit, Prop } from 'vue-property-decorator'
import { Component as tsc } from 'vue-tsx-support'
import { Collapse, CollapseItem } from 'bk-magic-vue'
import { TranslateResult } from 'vue-i18n'
import { VNode } from 'vue'
import './group.scss'

export interface IGroupData {
  id: string | number
  name: TranslateResult
  data: any[] // data为自定义分组数据
}
type themeType = 'filter' | 'bold'
type titleSlotType = (item: IGroupData) => VNode

interface IGroupProps {
  data?: IGroupData[] // 数据源
  theme?: themeType // 主题
  defaultActiveName?: string[] // 默认展开项
  customTitleSlot?: titleSlotType // 自定义title
}

interface IGroupEvents {
  onClear: (item: IGroupData) => void
}

interface IGroupSlots {
  default: { item: IGroupData }
}

type TActiveName = (string | number)[]

/**
 * 插件分组信息
 */
@Component({
  name: 'Group'
})
export default class Group extends tsc<IGroupProps, IGroupEvents, IGroupSlots> {
  @Prop({ type: Array, default: () => ([]) }) readonly data: IGroupData[]
  @Prop({ type: String, default: '' }) readonly theme: themeType
  @Prop({ type: Array, default: () => ([]) }) readonly defaultActiveName!: TActiveName
  @Prop({ type: Function, default: undefined }) readonly customTitleSlot: titleSlotType

  activeName: TActiveName = []

  created () {
    this.activeName = this.defaultActiveName
  }

  /**
   * 自定义title（内置两种样式）
   * @param item
   * @returns
   */
  titleSlot(item: IGroupData): VNode {
    if (this.customTitleSlot) return this.customTitleSlot(item)

    return this.theme === 'bold' ? this.boldTitleSlot(item) : this.filterTitleTheme(item)
  }

  /**
   * 插件分组样式
   * @param item
   * @returns
   */
  boldTitleSlot(item: IGroupData): VNode {
    return (
      <div class="group-title bold">
        <i class={['bk-icon icon-angle-right', { expand: this.activeName.includes(item.id) }]}></i>
        <span class="name">{item.name}</span>
      </div>
    )
  }

  /**
   * 筛选分组样式
   * @param item
   * @returns
   */
  filterTitleTheme(item: IGroupData): VNode {
    return (
      <div class="group-title filter">
        <div class="title-left">
          <i class={['bk-icon icon-angle-right', { expand: this.activeName.includes(item.id) }]}></i>
          <span class="name">{item.name}</span>
        </div>
        <i class="icon-monitor icon-mc-clear" onClick={event => this.handleClearChecked(event, item)}></i>
      </div>
    )
  }

  render() {
    return (
      <Collapse vModel={this.activeName}>
        {
          this.data && this.data.map(item => (
            item.data.length > 0
              ? <CollapseItem
                ext-cls={`collapse-item collapse-item-${this.theme}`}
                hide-arrow
                key={item.id}
                name={item.id}
                scopedSlots={{
                  default: () => (
                    this.titleSlot(item)
                  ),
                  content: () => (
                    this.$scopedSlots.default && this.$scopedSlots.default({ item })
                  )
                }}>
              </CollapseItem> : undefined
          ))
        }
      </Collapse>
    )
  }

  @Emit('clear')
  handleClearChecked(event: Event, item: IGroupData) {
    event.stopPropagation()
    return item
  }
}
