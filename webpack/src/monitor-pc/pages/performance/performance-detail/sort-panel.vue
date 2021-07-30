<template>
  <performance-dialog
    :title="$t('视图排序')"
    :value="value"
    :ok-text="$t('保存')"
    :cancel-text="$t('重置')"
    :loading="loading"
    @change="handleDialogValueChange"
    @cancel="handleReset"
    @undo="handleUndo"
    @confirm="handleSave">
    <div v-if="needGroup" :class="['create-group', { 'edit': !showCreateBtn }]">
      <template v-if="showCreateBtn">
        <i class="icon-monitor icon-mc-add"></i>
        <bk-button
          class="ml5 create-btn"
          text
          @click="handleCreateGroup">
          {{ $t('创建分组') }}
        </bk-button>
      </template>
      <template v-else>
        <bk-input ref="groupInput" v-model="newGroupName" @enter="handleSaveNewGroup" :maxlength="30"></bk-input>
        <i class="ml5 bk-icon icon-check-1" @click="handleSaveNewGroup"></i>
        <i class="ml5 icon-monitor icon-mc-close" @click="showCreateBtn = true"></i>
      </template>
    </div>
    <template v-for="(group,index) in groups">
      <bk-collapse v-if="needGroup" v-model="activeName" :key="group.id">
        <transition-group
          :name="transitionName"
          tag="div">
          <bk-collapse-item
            class="group-item"
            :class="{ 'is-dragover': dragover.groupId === group.id }"
            :style="{ 'border-top-color': dragover.groupId === group.id ? '#a3c5fd' : (index === 0 ? '#f0f1f5' : 'transparent') }"
            hide-arrow
            :key="group.id"
            :name="group.id"
            :draggable="group.id !== '__UNGROUP__' && !editId"
            @dragstart.native="handleDragGroupStart(group, $event)"
            @dragend.native="handleDragEnd"
            @dragover.native="handleDragGroupOver(group, $event)"
            @drop.native="(group.id !== '__UNGROUP__') && handleGroupDrop(group, $event)">
            <div class="group-item-title"
                 @mouseenter="handleMouseEnter(group)"
                 @mouseleave="handleMouseLeave">
              <div class="title-left">
                <i :class="[
                     'icon-monitor icon-arrow-right',
                     { 'expand': activeName.includes(group.id) }
                   ]"
                   v-if="group.id !== '__UNGROUP__'">
                </i>
                <!-- 分组名称 -->
                <span class="ml5 text-ellipsis" :title="group.title" v-if="group.id !== editId">{{ group.title }}<span style="color: #979ba5">{{group.id === '__UNGROUP__' ? `（${group.panels.length}）` : ''}}</span></span>
                <!-- 分组编辑态 -->
                <div class="title-edit" v-else @click.stop="() => {}">
                  <bk-input
                    ref="editGroupInput"
                    :value="group.title"
                    @change="handleGroupNameChange"
                    @enter="handleEditSave(group)">
                  </bk-input>
                  <i class="ml5 bk-icon icon-check-1" @click="handleEditSave(group)"></i>
                  <i class="ml5 icon-monitor icon-mc-close" @click="handleEditCancel"></i>
                </div>
              </div>
              <!-- 分组操作项（未分组和编辑态时不显示） -->
              <template v-if="group.id !== '__UNGROUP__' && group.id !== editId">
                <div class="title-right" v-show="hoverGroupId === group.id">
                  <!-- 编辑分组 -->
                  <i class="icon-monitor icon-mc-edit"
                     @click.stop="handleEditGroup(group)">
                  </i>
                  <!-- 删除分组 -->
                  <i class="ml10 icon-monitor icon-mc-delete-line"
                     @click.stop="handleDeleteGroup(group)">
                  </i>
                  <!-- 移动分组 -->
                  <i class="ml10 icon-drag"></i>
                </div>
              </template>
            </div>
            <!-- 分组内容 -->
            <template #content>
              <div v-if="false" class="group-item-content">
                <transition-group
                  :name="transitionName"
                  tag="ul"
                  v-if="group.panels.length">
                  <li v-for="item in group.panels"
                      :key="item.id"
                      draggable
                      class="content-item"
                      :class="{ 'is-dragover': dragover.itemId === item.id }"
                      @dragstart.stop="handleItemDragStart(item, group, $event)"
                      @dragend.stop="handleDragEnd"
                      @dragover.stop="handleItemDragOver(item, group, $event)"
                      @drop="handleItemDrop(item, group, $event)">
                    <span>{{ item.title }}</span>
                    <span class="item-operate">
                      <i :class="[
                           'icon-monitor',
                           item.visible ? 'icon-mc-visual' : 'icon-mc-invisible-fill'
                         ]"
                         @click="handleToggleVisible(group, item)">
                      </i>
                      <i class="ml10 icon-drag"></i>
                    </span>
                  </li>
                </transition-group>
                <div class="content-empty" v-else @drop="handleItemDrop({}, group, $event)">
                  <i class="icon-monitor icon-mind-fill"></i>
                  {{ $t('暂无任何视图') }}
                </div>
              </div>
              <sort-drag-list
                :class="{ 'is-group': needGroup }"
                :group="group"
                :dragover="dragover"
                :transition-name="transitionName"
                @drag-start="handleItemDragStart"
                @drag-end="handleDragEnd"
                @drag-over="handleItemDragOver"
                @drop="handleItemDrop"
                @toggle-visible="handleToggleVisible">
              </sort-drag-list>
            </template>
          </bk-collapse-item>
        </transition-group>
      </bk-collapse>
      <template v-else>
        <sort-drag-list
          :style="{ 'margin-top': index === 0 ? '20px' : '0' }"
          :key="group.id"
          :group="group"
          :dragover="dragover"
          :transition-name="transitionName"
          @drag-start="handleItemDragStart"
          @drag-end="handleDragEnd"
          @drag-over="handleItemDragOver"
          @drop="handleItemDrop"
          @toggle-visible="handleToggleVisible">
        </sort-drag-list>
      </template>
    </template>
  </performance-dialog>
</template>
<script lang="ts">
import { Vue, Component, Model, Emit, Prop, Watch } from 'vue-property-decorator'
import PerformanceDialog from '../components/performance-dialog.vue'
import { IHostGroup, IDragItem, IGroupItem } from '../performance-type'
import { typeTools } from '../../../../monitor-common/utils/utils'
import SortDragList from './sort-drag-list.vue'

@Component({
  name: 'sort-panel',
  components: {
    PerformanceDialog,
    SortDragList
  }
})
export default class SortPanel extends Vue {
  @Model('update-value', { type: Boolean }) readonly value: boolean
  @Prop({ default: () => [], type: Array }) readonly groupsData: IHostGroup[]
  @Prop({ default: true }) readonly needGroup: boolean
  @Prop({ default: false }) readonly loading: boolean

  private groups: IHostGroup[] = []
  // 当前激活项
  private activeName = ['__UNGROUP__']
  // 当前编辑的分组ID
  private editId = ''
  // 当前编辑分组的名称
  private curEditName = ''
  // 当前悬浮组的ID
  private hoverGroupId = ''
  // 创建分组
  private showCreateBtn = true
  // 新分组名
  private newGroupName = ''
  private dragover = {
    groupId: '',
    itemId: ''
  }
  private draging = {
    groupId: '',
    itemId: ''
  }
  private isDraging = false
  private dragoverTimer = null
  // 拖拽动画
  get transitionName() {
    return this.isDraging ? 'flip-list' : ''
  }

  @Watch('groupsData', { immediate: true })
  handleGroupDataChange(v) {
    this.groups = JSON.parse(JSON.stringify(v.map(item => ({
      ...item,
      id: item.id === '' ? '__UNGROUP__'  : item.id
    }))))
  }

  @Emit('reset')
  handleReset() {
    this.handleGroupDataChange(this.groupsData)
  }

  @Emit('save')
  handleSave() {
    return this.groups
  }
  @Emit('undo')
  handleUndo() {
    return this.groups
  }

  @Emit('update-value')
  handleDialogValueChange(v: boolean) {
    return v
  }
  // 分组title悬浮事件
  handleMouseEnter(item: IHostGroup) {
    this.hoverGroupId = item.id
  }

  handleMouseLeave() {
    this.hoverGroupId = ''
  }
  // 编辑分组
  handleEditGroup(group: IHostGroup) {
    this.editId = group.id
    this.$nextTick(() => {
      this.$refs.editGroupInput && (this.$refs.editGroupInput[0] as any).focus()
    })
  }

  // 删除分组
  handleDeleteGroup(group: IHostGroup) {
    const index = this.groups.findIndex(data => data.id === group.id)
    if (!group.panels.length) {
      this.groups.splice(index, 1)
      return
    }

    let unknownGroupIndex = this.groups.findIndex(data => data.id === '__UNGROUP__')
    if (unknownGroupIndex === -1) {
      const len = this.groups.push({
        id: '__UNGROUP__',
        title: this.$tc('未分组的指标'),
        panels: []
      })
      unknownGroupIndex = len - 1
    }
    this.groups[unknownGroupIndex].panels.push(...group.panels)
    this.groups.splice(index, 1)
  }

  // 指标显示和隐藏
  handleToggleVisible(group: IHostGroup, item: IGroupItem) {
    const groupData = this.groups.find(data => data.id === group.id)
    const itemData = groupData.panels.find(data => data.id === item.id)
    itemData.hidden = !itemData.hidden
  }
  // 分组拖拽开始事件
  handleDragGroupStart(group: IHostGroup, e: DragEvent) {
    e.dataTransfer.setData('groupId', group.id)
    this.draging = {
      groupId: group.id,
      itemId: ''
    }
    this.isDraging = true
  }

  handleDrag(e: DragEvent) {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop
    if (e.y < 180) {
      window.scrollTo(e.x, scrollTop - 9)
    }
  }
  // 分组拖拽结束事件
  handleDragEnd(e: DragEvent) {
    e.preventDefault()
    setTimeout(() => {
      this.isDraging = false
      this.handleClearDragData()
    }, 500)
  }

  handleDragGroupOver(group, e: DragEvent) {
    e.preventDefault()
    if (this.dragover.groupId !== group.id) {
      clearTimeout(this.dragoverTimer)
    }
    this.dragover.groupId = group.id
    this.dragoverTimer = setTimeout(() => {
      if (!this.activeName.includes(group.id) && this.dragover.groupId === group.id) {
        this.activeName.push(group.id)
      }
    }, 500)
  }

  // 分组拖拽drop事件
  handleGroupDrop(group: IHostGroup, e: DragEvent) {
    e.preventDefault()
    const dragGroupId = e.dataTransfer.getData('groupId')
    if (dragGroupId === group.id) return

    const dragIndex = this.groups.findIndex(data => data.id === dragGroupId)
    const dropIndex = this.groups.findIndex(data => data.id === group.id)
    if (dragIndex === -1 || dropIndex === -1) return

    const tmp = this.groups.splice(dragIndex, 1)
    this.groups.splice(dropIndex, 0, tmp[0])
    this.handleClearDragData()
  }
  handleClearDragData() {
    this.dragover = {
      groupId: '',
      itemId: ''
    }
    this.draging = {
      groupId: '',
      itemId: ''
    }
  }
  // 指标项拖拽开始事件
  handleItemDragStart(item, group: IHostGroup, e: DragEvent) {
    e.dataTransfer.setData('item', JSON.stringify({
      itemId: item.id,
      groupId: group.id
    }))
    this.draging = {
      itemId: item.id,
      groupId: group.id
    }
    this.isDraging = true
  }
  handleItemDragOver(item, group: IHostGroup, e: DragEvent) {
    e.preventDefault()
    this.dragover.groupId = group.id
    this.dragover.itemId = item.id
  }
  // 指标项拖拽drop事件
  handleItemDrop(item, group: IHostGroup, e: DragEvent) {
    e.preventDefault()
    try {
      const dragItem: IDragItem = JSON.parse(e.dataTransfer.getData('item'))
      if (dragItem.itemId === item.id && dragItem.groupId === group.id) return

      const dragGroup = this.groups.find(data => data.id === dragItem.groupId)
      const dropGroup = this.groups.find(data => data.id === group.id)
      if (!dragGroup || !dropGroup) return

      const dragIndex = dragGroup.panels.findIndex(data => data.id === dragItem.itemId)
      const dropIndex = dropGroup.panels.findIndex(data => data.id === item.id)
      if (dragIndex === -1) return

      const tmp = dragGroup.panels.splice(dragIndex, 1)
      dropGroup.panels.splice(dropIndex, 0, tmp[0])

      // 判断未分组指标数量
      const unknownGroupIndex = this.groups.findIndex(data => data.id === '__UNGROUP__')
      if (unknownGroupIndex > -1 && !this.groups[unknownGroupIndex].panels.length) {
        this.groups.splice(unknownGroupIndex, 1)
      }
      this.dragover.groupId = ''
      this.dragover.itemId = ''
    } catch {
      console.warn('parse drag data error')
    }
  }
  handleGroupNameChange(v) {
    this.curEditName = v
  }
  // 保存分组名称
  handleEditSave(group: IHostGroup) {
    group.title = this.curEditName || group.title
    this.handleEditCancel()
  }
  // 取消编辑分组名称
  handleEditCancel() {
    this.curEditName = ''
    this.editId = ''
  }
  handleCreateGroup() {
    this.showCreateBtn = false
    this.$nextTick(() => {
      this.$refs.groupInput && (this.$refs.groupInput as any).focus()
    })
  }
  handleSaveNewGroup() {
    if (typeTools.isNull(this.newGroupName)) return
    this.groups.unshift({
      id: `custom_${new Date().getTime()}`,
      title: this.newGroupName,
      panels: []
    })
    this.newGroupName = ''
    this.showCreateBtn = true
  }
}
</script>
<style lang="scss" scoped>
.flip-list-move {
  transition: transform .5s;
}
.create-group {
  height: 42px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  &.edit {
    padding: 0 20px;
    i {
      color: #979ba5;
    }
  }
  i {
    font-size: 24px;
    cursor: pointer;
  }
  .icon-mc-add {
    color: #3a84ff;
  }
  .create-btn {
    font-size: 12px;
  }
}
.group-item {
  border: 1px solid transparent;
  border-bottom: 1px solid #f0f1f5;
  /deep/ .bk-collapse-item-hover {
    padding: 0 14px;
    &:hover {
      color: #63656e;
    }
  }
  &.is-dragover {
    border-color: #a3c5fd;
  }
  .icon-drag {
    height: 14px;
    position: relative;
    cursor: move;
    &::after {
      content: " ";
      height: 14px;
      width: 2px;
      position: absolute;
      top: 0;
      border-left: 2px dotted #979ba5;
      border-right: 2px dotted #979ba5;
    }
  }
  &-title {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    .title-left {
      display: flex;
      flex: 1;
      align-items: center;
      color: #313238;
      .icon-arrow-right {
        transition: transform .2s ease-in-out;
        &.expand {
          transform: rotate(90deg);
        }
      }
      i {
        font-size: 24px;
        color: #979ba5;
      }
      .title-edit {
        display: flex;
        align-items: center;
        flex: 1;
      }
    }
    .title-right {
      display: flex;
      align-items: center;
      font-size: 16px;
      color: #979ba5;
      padding-right: 16px;
    }
  }
  .is-group {
    padding: 0 6px 18px 30px
  }
  .text-ellipsis {
    max-width: 220px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}
</style>
