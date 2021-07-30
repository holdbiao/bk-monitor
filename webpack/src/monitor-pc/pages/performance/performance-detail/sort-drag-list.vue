<template>
  <div class="drag-list">
    <transition-group
      :name="transitionName"
      tag="ul"
      v-if="group.panels.length">
      <li v-for="item in group.panels"
          :key="item.id"
          draggable
          class="content-item"
          :class="{ 'is-dragover': dragover.itemId === item.id }"
          @dragstart.stop="handleDragStart(item, group, $event)"
          @dragend.stop="handleDragEnd"
          @dragover.stop="handleDragOver(item, group, $event)"
          @drop="handleDrop(item, group, $event)">
        <span class="item-title">{{ item.title }}</span>
        <span class="item-operate">
          <i :class="[
               'icon-monitor',
               !item.hidden ? 'icon-mc-visual' : 'icon-mc-invisible-fill'
             ]"
             @click="handleToggleVisible(group, item)">
          </i>
          <i class="ml10 icon-drag"></i>
        </span>
      </li>
    </transition-group>
    <div class="content-empty" v-else @drop="handleDrop({}, group, $event)">
      <i class="icon-monitor icon-mind-fill"></i>
      {{ $t('暂无任何视图') }}
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop } from 'vue-property-decorator'
import { IHostGroup, IGroupItem } from '../performance-type'
@Component({ name: 'SortDragList' })
export default class SortDragList extends Vue {
  @Prop({ required: true }) group: IHostGroup
  @Prop({ required: true }) dragover: {}
  @Prop({ required: true }) transitionName: ''

  @Emit('drag-end')
  handleDragEnd(e: DragEvent) {
    return e
  }
  handleDragStart(item: IGroupItem, group: IHostGroup, $event: DragEvent) {
    this.$emit('drag-start', item, group, $event)
  }
  handleDragOver(item: IGroupItem, group: IHostGroup, e: DragEvent) {
    e.preventDefault()
    this.$emit('drag-over', item, group, e)
  }
  handleDrop(item: IGroupItem, group: IHostGroup, e: DragEvent) {
    e.preventDefault()
    this.$emit('drop', item, group, e)
  }
  handleToggleVisible(group: IHostGroup, item: IGroupItem) {
    this.$emit('toggle-visible',  group, item)
  }
}
</script>
<style lang="scss" scoped>
.flip-list-move {
  transition: transform .5s;
}
.drag-list {
  padding: 0 20px;
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
  .content-empty {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 64px;
    color: #979ba5;
    background: #fafbfd;
    border: 1px solid #f0f1f5;
    border-radius: 2px;
    i {
      font-size: 14px;
      position: relative;
      top: 1px;
      margin-right: 6px;
    }
  }
  .content-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 24px 0 12px;
    height: 32px;
    background: #f5f6fa;
    border-radius: 2px;
    border: 1px solid transparent;
    margin-bottom: 2px;
    .item-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .item-operate {
      display: flex;
      align-items: center;
    }
    i {
      font-size: 16px;
    }
    &:hover {
      background: #e1ecff;
      border-color: #a3c5fd;
      cursor: pointer;
    }
    &.is-dragover {
      background: #e1ecff;
    }
  }
}
</style>
