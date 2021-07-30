<template>
  <div class="select-chart-wrap" v-bkloading="{ isLoading }">
    <transition-group
      name="flip-list"
      tag="ul"
      class="selected-list-wrap"
      v-if="selectedList.length">
      <li
        v-for="(item, index) in selectedList"
        :key="item.id"
        :class="['selected-item', {
          'active': DragData.toActive === index || selectedActive === item.id
        }]"
        draggable="true"
        @click="handleSelectItem(item)"
        @dragstart="handleDragStart($event, index)"
        @dragend="handleDragEnd($event, index)"
        @drop="handleDrop($event, index)"
        @dragenter="handleDragEnter($event, index)"
        @dragover="handleDragOver($event, index)">
        <span class="icon-drag"></span>
        <span class="item-title">
          <span class="title">{{item.name}}</span>
          <span class="des" v-bk-tooltips="{ content: handleBelonging(item), delay: 300 }">&nbsp;{{`- ${$t('所属:')}${handleBelonging(item)}`}}</span>
        </span>
        <span @click.stop="handleDelSelected(index)" class="icon-monitor icon-mc-close"></span>
      </li>
    </transition-group>
    <div class="add-btn-wrap" v-show="!tool.show && !isDisabled">
      <span class="add-btn" @click="handleAddChart"><span class="icon-monitor icon-mc-add" />{{$t('添加图表')}}</span>
    </div>
    <div class="select-tool-wrap" v-if="tool.show">
      <div class="tool-left-wrap">
        <bk-tab
          class="tab-wrap"
          :active.sync="tool.active"
          type="unborder-card"
          @tab-change="handleTabChange">
          <bk-tab-panel
            v-for="(tab, index) in tool.tabList"
            v-bind="tab"
            :key="index">
          </bk-tab-panel>
        </bk-tab>
        <bk-select
          v-show="tool.active === 'default'"
          class="biz-list-wrap"
          v-model="DefaultCurBizIdList"
          multiple
          searchable
          :clearable="false"
          @change="handleChangeBizIdList">
          <bk-option
            v-for="(option, index) in handleBizIdList"
            :key="index"
            :id="option.id"
            :name="option.text">
          </bk-option>
        </bk-select>
        <bk-select
          v-if="tool.active === 'grafana'"
          searchable
          class="biz-list-wrap"
          v-model="curBizId"
          :clearable="false"
          @change="handleGraphBizid">
          <bk-option
            v-for="(option, index) in bizIdList"
            :key="index"
            :id="option.id"
            :name="option.text">
          </bk-option>
        </bk-select>
        <div class="left-list-wrap">
          <div
            v-for="(item, index) in leftList"
            :key="index"
            :class="['left-list-item', { 'active': leftActive === item.uid }]"
            @click="handleSelectLeftItem(item)">
            {{item.name}}
          </div>
        </div>
      </div>
      <div class="tool-right-wrap">
        <div class="right-title">{{$t('可选图表({num})', { num: rightList.length })}}</div>
        <div class="right-list-wrap">
          <checkbox-group
            v-model="rightSelect"
            :list="rightList"
            :active="selectedActive"
            :disabled="isDisabled">
          </checkbox-group>
        </div>
        <div class="right-btn-wrap">
          <bk-button size="small" theme="primary" :disabled="false" @click="handleComfirm">{{$t('确认')}}</bk-button>
          <bk-button size="small" @click="handleCancel">{{$t('取消')}}</bk-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Model, Emit, Watch } from 'vue-property-decorator'
import { IAddChartToolData, IChartListAllItem, IChartDataItem, IGraphValueItem, IDefaultRadioList } from '../types'
import { graphsListByBiz, buildInMetric } from '../../../../monitor-api/modules/report'
import { deepClone } from '../../../../monitor-common/utils/utils'
import checkboxGroup from './checkboxGroup.vue'

/**
 * 添加内容-图表选择组件
 */
@Component({
  name: 'select-chart',
  components: {
    checkboxGroup
  }
})
export default class SelectChart extends Vue {
  // value双向绑定
  @Model('valueChange', { type: Array }) private value: string[]

  private isLoading = false
  // 选择图表工具的数据
  private tool: IAddChartToolData = {
    show: false,
    active: 'grafana',
    tabList: [
      { name: 'default', label: window.i18n.t('内置') },
      { name: 'grafana', label: window.i18n.t('仪表盘') }
    ]
  }

  // active状态与列表数据
  private selectedActive: string = null
  private selectedList: IGraphValueItem[] = []
  // private leftList: IChartListAllItem[] = []
  private curBizId = `${window.cc_biz_id}`
  private DefaultCurBizIdList: string[] = [`${window.cc_biz_id}`]
  private bizIdList: any = []
  private leftActive: string = null
  private rightSelect: IGraphValueItem[] = []
  private allGrafanaListMap: any = []
  private allDefaultList: any = []
  private defaultRadioList: IDefaultRadioList[] = [
    { id: 'all', text: window.i18n.tc('有权限的业务(最大20个)'), title: window.i18n.tc('有权限的业务') },
    { id: 'settings', text: window.i18n.tc('配置管理业务'), title: window.i18n.tc('配置管理业务') },
    { id: 'notify', text: window.i18n.tc('告警接收业务'), title: window.i18n.tc('告警接收业务') }
  ]
  private radioMap: string[] = ['all', 'settings', 'notify']

  // 拖拽数据状态记录
  private DragData: any = {
    from: null,
    to: null,
    toActive: null
  }

  private get leftList(): IChartListAllItem[] {
    const isDefault = this.tool.active === 'default'
    const list = isDefault ? this.allDefaultList : this.allGrafanaListMap[this.curBizId]
    return list || []
  }

  private get rightList(): IChartDataItem[] {
    if (this.tool.active === 'default' && !this.DefaultCurBizIdList.length) return []
    const allList = this.leftList.reduce((total, cur) => {
      cur.panels.forEach((item) => {
        const bizId = this.tool.active === 'default'
          ? this.DefaultCurBizIdList.sort().join(',')
          : this.curBizId
        item.fatherId = cur.uid
        item.key = `${bizId}-${this.leftActive}-${item.id}`
      })
      total = total.concat(cur.panels)
      return total
    }, [])
    return allList.filter(item => (this.leftActive === item.fatherId) && !/^-1/.test(item.key))
  }

  private get handleBizIdList() {
    return [...this.defaultRadioList, ...this.bizIdList.map(item => ({
      id: String(item.id),
      text: item.text
    }))]
  }

  // 限制最多选择图表数
  private get isDisabled(): boolean {
    const MAX = 20
    return this.rightSelect.length >= MAX
  }

  @Emit('valueChange')
  handleValueChange(v?: string) {
    return v || this.selectedList
  }
  // 值更新
  @Watch('value', { immediate: true, deep: true })
  watchValueChange(v: IGraphValueItem[]) {
    this.selectedList = v
    this.rightSelect = deepClone(v)
  }

  async created() {
    this.isLoading = true
    await Promise.all([this.getChartList(), this.getBuildInMetric()]).finally(() => this.isLoading = false)
    this.bizIdList = this.$store.getters.bizList.map(item => ({
      id: String(item.id),
      text: item.text
    }))
  }

  /**
   * 获取内置图表数据
   */
  private getBuildInMetric() {
    return buildInMetric().then((list) => {
      this.allDefaultList = list
    })
  }

  /**
     * 获取图表列表数据
     */
  private getChartList(needLoading = false)  {
    // const noPermission = !this.bizIdList.some(item => `${item.id}` === `${this.curBizId}`)
    if (+this.curBizId === -1) return
    needLoading && (this.isLoading = true)
    return graphsListByBiz({ bk_biz_id: this.curBizId }).then((list) => {
      this.allGrafanaListMap = list
    })
      .finally(() => this.isLoading = false)
  }

  /**
     * 删除已选择
     * @params index 数据索引
     */
  private handleDelSelected(index: number) {
    this.selectedList.splice(index, 1)
    const isEixstActive = this.selectedList.find(checked => checked.id === this.selectedActive)
    !isEixstActive && (this.selectedActive = null)
    this.handleValueChange()
  }

  /**
     * 选择
     * @params index 数据索引
     */
  private handleSelectItem(item: IGraphValueItem) {
    if (this.selectedActive === item.id) return
    this.selectedActive = item.id
    const ids = item.id.split('-')
    const isDefault = !(typeof +ids[0] === 'number' && this.bizIdList.find(item => item.id === ids[0]))
    if (!isDefault && !this.bizIdList.find(item => item.id === ids[0])) return
    // eslint-disable-next-line prefer-destructuring
    this.leftActive = ids[1]
    this.tool.show = true
    this.tool.active = isDefault ? 'default' : 'grafana'
    // eslint-disable-next-line prefer-destructuring
    this.tool.active === 'default' ? this.DefaultCurBizIdList = ids[0].split(',') : this.curBizId = ids[0]
    this.rightSelect = deepClone(this.selectedList)
  }

  /**
   * 新建图表
   */
  private handleAddChart() {
    this.rightSelect = deepClone(this.selectedList)
    this.tool.show = true
  }

  /**
   * 左侧选中操作
   */
  private handleSelectLeftItem(item: IChartListAllItem) {
    item.bk_biz_id && (this.curBizId = `${item.bk_biz_id}`)
    this.leftActive = item.uid
  }

  /**
   * 确认操作
   */
  private handleComfirm() {
    this.$parent && this.$parent.handlerFocus()
    // this.selectedList = [...new Set(deepClone(this.rightSelect))].map(item => `${item}`)
    this.selectedList = deepClone(this.rightSelect)
    this.rightSelect = []
    this.handleValueChange()
    this.tool.show = false
    this.selectedActive = null
  }


  /**
   * 取消操作
   */
  private handleCancel() {
    this.tool.show = false
    this.selectedActive = null
    this.rightSelect = []
  }

  private handleTabChange() {
    this.tool.active === 'default'
      ? this.DefaultCurBizIdList = [`${+window.cc_biz_id > -1 ? window.cc_biz_id : 'all'}`]
      : this.curBizId = `${window.cc_biz_id}`
    this.selectedActive = ''
    this.leftActive = null
  }

  private handleChangeBizIdList(list) {
    const leng = list.length
    const lastChild = list[leng - 1]
    const firstChild = list[0]
    const { radioMap } = this
    const isAllRadio = list.every(item => radioMap.includes(item))
    if (radioMap.includes(lastChild)) {
      this.DefaultCurBizIdList = [lastChild]
    }
    if (radioMap.includes(firstChild) && !isAllRadio && leng > 1) {
      this.DefaultCurBizIdList = this.DefaultCurBizIdList.filter(item => !radioMap.includes(item))
    }
  }

  private handleGraphBizid() {
    if (this.tool.active === 'default') return
    this.getChartList(true)
  }

  private handleBelonging(item) {
    const res = item.id.split('-')
    const str = this.radioMap.includes(res[0])
      ? this.defaultRadioList.find(item => item.id === res[0])?.title
      : res[0]
    return str
  }

  /**
     * 以下为拖拽操作
     */
  private handleDragStart(e: DragEvent, index: number) {
    this.DragData.from = index
  }
  private handleDragOver(e: DragEvent) {
    e.preventDefault()
    e.dataTransfer.effectAllowed = 'move'
  }
  private handleDragEnd() {
    this.DragData = {
      from: null,
      to: null,
      toActive: null
    }
  }
  private handleDrop() {
    const { from, to } = this.DragData
    if (from === to) return
    const list = deepClone(this.selectedList)
    const temp = list[from]
    list.splice(from, 1)
    list.splice(to, 0, temp)
    this.handleValueChange(list)
  }
  private handleDragEnter(e: DragEvent, index: number) {
    this.DragData.to = index
    this.DragData.toActive = index
  }
}
</script>

<style lang="scss" scoped>
.select-chart-wrap {
  .flip-list-move {
    transition: transform .5s;
  }
  .selected-list-wrap {
    width: 465px;
    border: 1px solid #dcdee5;
    margin-bottom: 6px;
    .selected-item {
      display: flex;
      align-items: center;
      height: 38px;
      background: #fff;
      cursor: pointer;
      &:hover {
        background-color: #eef5ff;
      }
      &:not(:last-child) {
        border-bottom: 1px solid #dcdee5;
      }
      .icon-drag {
        display: inline-block;
        flex-shrink: 0;
        width: 6px;
        height: 14px;
        margin: 0 8px;
        position: relative;
        cursor: move;
        &::after {
          content: " ";
          height: 14px;
          width: 2px;
          position: absolute;
          top: 0;
          border-left: 2px dotted #63656e;
          border-right: 2px dotted #63656e;
        }
      }
      .item-title {
        flex: 1;
        display: flex;
        align-items: center;
        .des {
          max-width: 300px;
          white-space: nowrap;
          overflow: hidden;
          display: inline-block;
          text-overflow: ellipsis;
          color: #979ba5;
        }
      }
      .icon-mc-close {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-shrink: 0;
        font-size: 24px;
        width: 24px;
        height: 24px;
        margin-right: 3px;
        cursor: pointer;
      }
    }
    .active {
      background-color: #eef5ff;
    }
  }
  .add-btn-wrap {
    .add-btn {
      display: flex;
      align-items: center;
      font-size: 14px;
      width: 100px;
      color: #63656e;
      cursor: pointer;
      .icon-mc-add {
        font-size: 32px;
        color: #3a84ff;
      }
    }

  }
  .select-tool-wrap {
    display: flex;
    width: 664px;
    height: 327px;
    background: #fff;
    border: 1px solid #dcdee5;
    border-radius: 2px 2px 0px 0px;
    margin-top: 7px;
    .tool-left-wrap {
      flex: 278px 0;
      width: 278px;
      border-right: 1px solid #dcdee5;
      .tab-wrap {
        height: 32px;
        background-color: #fafbfd;
        border-bottom: 1px solid #dcdee5;
        /deep/.bk-tab-header {
          height: 100%;
          .bk-tab-label-wrapper {
            height: 100%;
            .bk-tab-label-list {
              height: 100%;
              .bk-tab-label-item {
                display: flex;
                align-items: center;
                justify-content: center;
              }
              .bk-tab-label {
                // height: 100%;
                font-size: 12px;
                line-height: 1;
              }
            }
          }
        }
        /deep/.bk-tab-label-list {
          display: flex;
          width: 100%;
          padding: 0 20px;
          .bk-tab-label-item {
            flex: 1;
            padding-left: 10px;
            padding-right: 10px;
            min-width: 0;
            &.active {
              &::after {
                left: 0;
                width: 100%;
              }
            }
          }
        }
        /deep/.bk-tab-section {
          padding: 0;
        }
      }
      .left-list-wrap {
        height: calc(100% - 78px);
        overflow-y: auto;
        .left-list-item {
          height: 32px;
          padding: 0 12px;
          font-size: 12px;
          line-height: 32px;
          color: #63656e;
          cursor: pointer;
          &:hover {
            background-color: #eef5ff;
          }
        }
        .active {
          background-color: #eef5ff;
        }
      }
      // .no-bk-biz-select {
      //   height: calc(100% - 40px);
      // }
      .biz-list-wrap {
        margin: 10px 12px 5px 12px;
      }
    }
    .tool-right-wrap {
      flex: 1;
      padding: 10px 0 0 14px;
      .right-title {
        height: 16px;
        font-size: 12px;
        text-align: left;
        color: #c4c6cc;
        line-height: 16px;
        margin-bottom: 9px;
      }
      .right-list-wrap {
        height: calc(100% - 68px);
        overflow-y: auto;
      }
      .right-btn-wrap {
        text-align: right;
        margin-top: 4px;
        padding-right: 12px;
        font-size: 0;
        & > :not(:last-child) {
          margin-right: 12px;
        }
      }
    }
  }
}
</style>
