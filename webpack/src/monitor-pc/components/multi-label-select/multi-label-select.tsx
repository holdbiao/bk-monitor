/*
 * @Date: 2021-06-21 14:53:51
 * @LastEditTime: 2021-06-23 16:29:12
 * @Description:
 */
import { Component, Prop, Watch, Emit, Ref } from 'vue-property-decorator'
import { Component as tsc } from 'vue-tsx-support'
// import { Tree } from 'bk-magic-vue'
import { VNode } from 'vue'
import './multi-label-select.scss'
import LabelTree from './label-tree/label-tree'
import { ITreeItem, TMode, IAddWrapSize } from './types'
import { deepClone } from '../../../monitor-common/utils/utils'
import { debounce } from 'throttle-debounce'

interface IContainerProps {
  mode: TMode,
  treeData?: ITreeItem[],
  checkedNode?: string[],
  allowAutoMatch?: boolean
}

@Component({
  name: 'MultiLabelSelect',
  components: {
    LabelTree
  }
})
export default class MultiLabelSelect extends tsc<IContainerProps> {
  @Prop({ default: 'create', type: String }) private mode: TMode
  @Prop({ default: () => [] }) private treeData: ITreeItem[]
  @Prop({ default: () => [], type: Array }) private checkedNode: string[]
  @Prop({ default: true, type: Boolean }) private allowAutoMatch: boolean // 自定义失焦自动生成tag

  @Ref('createLabelTree') private readonly createLabelTreeRef
  @Ref('wrapper') private readonly wrapperRef
  @Ref('input') private readonly inputRef
  @Ref('selectDropdown') private readonly selectDropdownRef
  @Ref('tagList') private readonly tagListRef

  private treeLoading = false
  private isEdit = false
  private defaultPlaceholder: string = i18n.t('请选择或输入')
  private addWrapSize: IAddWrapSize = {
    width: 470,
    height: 357,
    startClientX: 0,
    startClientY: 0
  }

  private dropDownInstance: any = null
  private resizeObserver: any = null
  private popoverContentWidth = 465
  private localCheckNode: string[] = []
  private localTreeList: ITreeItem[] = []
  private localSearchData: any[] = []
  private inputValue = ''
  private handleOverflowDebounce: Function = null

  private tippyOptions: any = {
    onHidden: null
  }

  get filterSearchData() {
    const value = this.removeSpacesInputValue
    if (value) {
      const res = this.localSearchData.map((item) => {
        const obj = {
          groupName: item.groupName,
          children: item.children.filter((key) => {
            const isSame = key?.toUpperCase().indexOf(value.toUpperCase()) > -1
            return isSame && !this.localCheckNode.includes(`/${key}/`)
          })
        }
        return obj
      }).filter(item => item.children.length)
      return res
    }
    return this.localSearchData
  }

  // 可以自定义标签
  get isCanCustom() {
    const value = this.removeSpacesInputValue
    const res = this.localSearchData.some(item => item.children.some(set => set === value))
    return !res
  }

  /**
   * 去除空格的搜索值
   */
  get removeSpacesInputValue() {
    return this.inputValue.replace(/\s/g, '')
  }

  get menuListDisplay() {
    const noSearch = !this.filterSearchData.find(item => item.children.length)
    const noList = !this.localSearchData.find(item => item.children.length)
    const display = noSearch || noList ? 'none' : 'block'
    return display
  }

  @Watch('checkedNode', { immediate: true, deep: true })
  checkedNodeChange() {
    this.localCheckNode = deepClone(this.checkedNode)
    this.handleOverflowDebounce?.()
  }

  @Watch('treeData', { immediate: true, deep: true })
  treeDataChange() {
    this.localTreeList = deepClone(this.treeData)
    this.mode === 'select' && this.createSearchData(this.treeData)
  }

  // @Watch('filterSearchData')
  // async filterSearchDataChange (nv) {
  //   if (this.isEdit) {
  //     const leng = nv.length
  //     const fn = leng ? this.showDropdown :  this.hideDropdown
  //     await this.$nextTick()
  //     fn()
  //   }
  // }

  @Emit('listChange')
  localTreeListChange() {
    return deepClone(this.localTreeList)
  }

  @Emit('checkedChange')
  localCheckNodeChange() {
    return deepClone(this.localCheckNode)
  }

  created() {
    this.tippyOptions.onHidden = this.hideDropdownCb
  }

  mounted() {
    if (this.mode === 'select') {
      this.resizeObsever()
      this.dropDownInstance = this.selectDropdownRef?.instance
      this.handleOverflow()
      this.handleOverflowDebounce = debounce(300, false, this.handleOverflow)
    }
  }
  beforeDestroy() {
    this.mode === 'select' && this.resizeObserver.unobserve(this.wrapperRef)
  }

  /**
   * 新增模式下监听容器的大小变化
   */
  resizeObsever() {
    this.resizeObserver = new ResizeObserver((entries) => {
      const rect = entries[0].contentRect
      this.popoverContentWidth = rect.width
      this.handleOverflowDebounce()
    })
    this.resizeObserver.observe(this.wrapperRef)
  }

  /**
   * 统计标签数目
   * @param group 标签分组名
   */
  //   getLabelCount(groupName: string) {
  //     const res = this.localSearchData.find(item => item.groupName === groupName)
  //     return res ? res.children?.length : 0
  //   }

  /**
   * 创建搜索所需的数据
   * @param list
   */
  createSearchData(list: ITreeItem[]) {
    const res = list.map(item => ({
      group: item.group,
      groupName: item.groupName,
      children: this.getSearchData(item.children)
    }))
    this.localSearchData = res
  }

  /**
   * 获取各分组下的数据id
   * @param list
   */
  getSearchData(list: ITreeItem[]) {
    const res = []
    const fn = (data) => {
      data.forEach((item) => {
        if (item.children) {
          fn(item.children)
        } else {
          res.push(item.key)
        }
      })
    }
    fn(list)
    return res
  }

  /**
   * 展示下拉
   */
  showDropdown() {
    this.dropDownInstance.show()
    this.removeOverflow()
  }

  hideDropdown() {
    this.dropDownInstance.hide()
  }

  /**
   * 下拉隐藏回调
   */
  hideDropdownCb() {
    this.inputValue = ''
    this.isEdit = false
    this.handleOverflow()
  }

  /**
   * 树形数据更新
   * @param list
   */
  handleLocalTreeListChange(list) {
    this.localTreeList = list
    this.localTreeListChange()
  }

  /**
   * 新增一级标签
   */
  handleAddFirstLevelLabel() {
    const isCreate = this.localTreeList.some(item => item.isCreate)
    if (isCreate) return
    this.localTreeList.push({
      id: null,
      key: '',
      name: '',
      parent: null,
      isCreate: true
    })
    this.$nextTick(() => {
      this.createLabelTreeRef.inputFocus()
    })
  }

  /**
   * 选中标签
   * @param checked
   */
  handleNodeChecked(checked) {
    const change = checked.valueChange
    if (change.type === 'add') {
      this.localCheckNode.push(change.value)
    } else {
      const index = this.localCheckNode.findIndex(item => item === change.value)
      this.localCheckNode.splice(index, 1)
    }
    this.localCheckNodeChange()
  }

  /**
   * 输入框聚焦
   */
  async focusInputer() {
    this.isEdit = true
    await this.$nextTick()
    this.inputRef.focus()
    this.showDropdown()
  }

  /**
   * 控制超出省略提示
   */
  async handleOverflow() {
    this.removeOverflow()
    const list = this.tagListRef
    const childs = list.children
    const overflowTagWidth = 32
    const listWidth = this.popoverContentWidth || list.offsetWidth
    let totalWidth = 0
    for (const i in childs) {
      const item = childs[i]
      if (!item.className || item.className.indexOf('key-node') === -1) continue
      totalWidth += (item.offsetWidth + 5)
      // 超出省略
      await this.$nextTick()
      if (totalWidth + overflowTagWidth + 3 > listWidth) {
        const hideNum = this.checkedNode.length - +i
        this.insertOverflow(item, hideNum > 99 ? 99 : hideNum)
        break
      }
    }
  }

  /**
   * 插入超出提示
   * @param target
   * @param num
   */
  insertOverflow(target, num) {
    if (this.isEdit) return
    const li = document.createElement('li')
    const div = document.createElement('div')
    li.className = 'tag-overflow'
    div.className = 'tag'
    div.innerText = `+${num}`
    li.appendChild(div)
    this.tagListRef.insertBefore(li, target)
  }

  /**
   * 移除超出提示
   */
  removeOverflow() {
    const overflowList = this.tagListRef.querySelectorAll('.tag-overflow')
    overflowList.forEach((item) => {
      this.tagListRef.removeChild(item)
    })
  }

  /**
   * 输入框失去焦点
   */
  inputBlur() {
    if (this.allowAutoMatch && this.removeSpacesInputValue && !this.filterSearchData.length) {
      this.createCustomLabel()
      this.isEdit = false
    }
  }

  /**
   * 鼠标变盘事件
   * @param e
   */
  inputKeydown(e: KeyboardEvent) {
    // Backspace Enter
    const key = e.code
    const keyFn = {
      Enter: this.handleCustomLabel,
      Backspace: () => {
        if (!this.inputValue.length) {
          const index = this.localCheckNode.length - 1
          index >= 0 && this.handleRemoveTag(index)
        }
      }
    }
    keyFn[key]?.()
  }

  /**
   * 输入框input
   * @param e
   */
  inputChange(e: any) {
    this.inputValue = e.target.value
    if (this.filterSearchData.length) {
      this.showDropdown()
    } else {
      // this.hideDropdown()
    }
  }

  // 创建自定义标签
  handleCustomLabel() {
    this.createCustomLabel()
    this.inputValue = ''
  }

  /**
   * 创建标签
   */
  createCustomLabel() {
    const isCreateCustom = this.isCanCustom && this.removeSpacesInputValue
    if (isCreateCustom) {
      const labelArr = this.removeSpacesInputValue.split('/').filter(item => !!item)
      const id = `/${labelArr.join('/')}/`
      if (!this.localCheckNode.includes(id)) {
        this.localCheckNode.push(id)
        this.localCheckNodeChange()
      } else {
        this.$bkMessage({
          message: this.$t('标签重名'),
          theme: 'error'
        })
      }
    } else {
      const id = `/${this.removeSpacesInputValue}/`
      !this.localCheckNode.includes(id) && this.localCheckNode.push(id)
    }
  }

  /**
   * 删除标签
   * @param e
   * @param index
   */
  handleRemoveTag(index: number) {
    // e?.stopPropagation()
    this.localCheckNode.splice(index, 1)
    this.localCheckNodeChange()
    // this.localTreeListChange()
  }

  /**
   * 处理搜索高亮
   * @param str
   */
  searchHighlight(str: string) {
    const value = this.removeSpacesInputValue
    const reg = new RegExp(`${value}`, 'g')
    let res = str.replace(reg, `<span class="hl">${value}</span>`)
    try {
      res = res.replace(/([^<])(\/)([^>])/g, '$1&nbsp;/&nbsp;$3')
    } catch (error) {
      console.log(error)
    }
    return res
  }

  /**
   * 选中搜索结果
   * @param id
   */
  selectSearchRes(id) {
    this.localCheckNode.push(id)
    this.localCheckNodeChange()
    this.inputValue = ''
    this.isEdit = false
    this.hideDropdown()
  }

  handleTreeLoading(v) {
    this.treeLoading = v
  }

  /**
   * 容器大小控制
   * @param e
   */
  handleMouseDown(e: MouseEvent) {
    this.addWrapSize.startClientX = e.clientX
    this.addWrapSize.startClientY = e.clientY
    document.addEventListener('mousemove', this.handleMousemove, false)
    document.addEventListener('mouseup', this.handleMouseup, false)
  }
  handleMouseup() {
    this.addWrapSize.startClientX = 0
    this.addWrapSize.startClientY = 0
    document.removeEventListener('mousemove', this.handleMousemove, false)
    document.removeEventListener('mouseup', this.handleMousemove, false)
  }
  handleMousemove(e: MouseEvent) {
    if (this.addWrapSize.startClientX === 0) return
    const offsetX = e.clientX - this.addWrapSize.startClientX
    const offsetY = e.clientY - this.addWrapSize.startClientY
    this.addWrapSize.startClientX = e.clientX
    this.addWrapSize.startClientY = e.clientY
    this.addWrapSize.width = this.addWrapSize.width + offsetX
    this.addWrapSize.height = this.addWrapSize.height + offsetY
  }

  protected render(): VNode {
    return (
      <div class="multi-label-select" ref="wrapper">
        {/* 新增模式 */}
        { this.mode === 'create'
          ? (<div class="multi-label-add">
            <bk-button onClick={ this.handleAddFirstLevelLabel }>
              <div class="add-btn-wrap">
                <i class="icon-monitor icon-mc-add"></i>
                <span class="text">{ this.$t('添加一级标签') }</span>
              </div>
            </bk-button>
            { this.localTreeList.length
              ? <div
                class="label-tree-contain-wrap"
                v-bkloading={ { isLoading: this.treeLoading } }
                style={ `width: ${this.addWrapSize.width}px; height: ${this.addWrapSize.height}px;`}>
                <div class="label-tree-scroll-wrap">
                  <label-tree
                    ref="createLabelTree"
                    mode="create"
                    onLoading={ this.handleTreeLoading }
                    onListChange={ this.handleLocalTreeListChange }
                    checkedNode={ this.localCheckNode }
                    treeData={ this.localTreeList } />
                </div>
                <i class="resize-icon-inner"></i>
                <i
                  class="resize-icon-wrap"
                  onMousedown={ this.handleMouseDown }
                  onMousemove={ this.handleMousemove }
                  onMouseup={ this.handleMouseup }>
                </i>
              </div> : '' }
          </div>)
        // 选择模式
          : (<div>
            <bk-popover
              class="multi-label-select-dropdown"
              ref="selectDropdown"
              trigger="manual"
              placement="bottom-start"
              theme="light multi-label-list-wrapper"
              animation="slide-toggle"
              transfer={ false }
              arrow={ false }
              distance={ 12 }
              tippyOptions={ this.tippyOptions }>
              <div
                class={ ['multi-label-input', { 'is-focus': this.isEdit }] }
                onClick={ this.focusInputer }>
                {
                  !this.localCheckNode.length && !this.isEdit
                    ? <p class="placeholder">{ this.defaultPlaceholder }</p> : ''
                }
                <ul class="tag-list" ref="tagList">
                  {
                    this.localCheckNode.map((item, index) => <li
                      class="key-node"
                      key={ index }>
                      <div class="tag">
                        <span class="text">{ item.split('/').filter(item => item)
                          .join(' / ') }</span>
                      </div>
                      <i
                        class="icon-monitor icon-mc-close remove-key"
                        onClick={ e => this.handleRemoveTag(index, e) }></i>
                    </li>)
                  }
                  {
                    this.isEdit ? <li ref="staffInput" class="staff-input">
                      <span class="input-value">{this.inputValue}</span>
                      <input
                        type="text"
                        class="input"
                        ref="input"
                        value={ this.inputValue }
                        onInput={ this.inputChange }
                        onBlur={ this.inputBlur }
                        onClick={ e => e.stopPropagation() }
                        onKeydown={ this.inputKeydown } />
                    </li> : ''
                  }
                </ul>
              </div>
              <div
                slot="content"
                class="menu-list-wrap"
                ref="menuList"
                style={ `display: ${this.menuListDisplay}; width: ${this.popoverContentWidth}px` }>
                {
                  // 搜索结果
                  this.removeSpacesInputValue ? <div class="search-result-wrap">
                    {
                      this.filterSearchData.map(item => (
                        <div class="group-item">
                          <div class="group-title">
                            <div class="title">{ `${item.groupName}( ${item.children.length} )` }</div>
                          </div>
                          <ul class="res-list">
                            {
                              item.children.map(id => (
                                <li
                                  class="res-item"
                                  domPropsInnerHTML={ this.searchHighlight(id) }
                                  onClick={ () => this.selectSearchRes(id) }>{ id }</li>
                              ))
                            }
                          </ul>
                        </div>
                      ))
                    }
                  </div>
                  // 标签树
                    : <div class="tree-wrap">
                      {
                        this.treeData.map(item => (
                          item.children.length
                            ? <div class="group-item">
                              <div class="group-title">
                                <div class="title">{ `${item.groupName}( ${item.children.length} )` }</div>
                              </div>
                              <label-tree
                                mode="select"
                                checkedNode={ this.localCheckNode }
                                treeData={ item.children }
                                onCheckedChange={ this.handleNodeChecked } />
                            </div> : undefined
                        ))
                      }
                    </div>
                }
              </div>
            </ bk-popover>
          </div>)}
      </div>)
  }
}
