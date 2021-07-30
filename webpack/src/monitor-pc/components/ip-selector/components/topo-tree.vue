<template>
  <bk-big-tree
    ref="tree"
    :data="nodes"
    :options="nodeOptions"
    :height="height"
    selectable
    :expand-on-click="expandOnClick"
    :default-checked-nodes="defaultCheckedNodes"
    show-checkbox
    :check-strictly="false"
    :default-expanded-nodes="defaultExpandedNodes"
    :lazy-method="lazyMethod"
    :lazy-disabled="lazyDisabled"
    :padding="20"
    @select-change="handleSelectChange">
    <template #default="{ data }">
      <div class="node-label">
        <span class="label">{{ data.name }}</span>
        <span :class="['num mr10', { 'selected': getSelectedStatus(data) }]" v-show="showCount">
          {{ data.children ? data.children.length : 0 }}
        </span>
      </div>
    </template>
  </bk-big-tree>
</template>
<script lang="ts">
/* eslint-disable @typescript-eslint/member-ordering */
import { Vue, Component, Prop, Emit, Ref } from 'vue-property-decorator'
import { ITreeNode } from '../types/selector-type'

@Component({ name: 'topo-tree' })
export default class StaticTopo extends Vue {
  @Prop({ default: () => [], type: Array }) private readonly defaultCheckedNodes!: (string | number)[]
  @Prop({ default: () => ({}), type: Object }) private readonly options!: any
  @Prop({ default: () => [], type: Array }) private readonly nodes!: ITreeNode[]
  @Prop({ default: true, type: Boolean }) private readonly checkedable!: boolean
  @Prop({ default: 300, type: Number }) private readonly height!: number
  @Prop({ default: false, type: Boolean }) private readonly expandOnClick!: boolean
  @Prop({ default: true, type: Boolean }) private readonly showCount!: boolean
  @Prop({ type: Function }) private readonly lazyMethod!: Function
  @Prop({ type: [Function, Boolean] }) private readonly lazyDisabled!: Function
  @Prop({ default: 2, type: Number }) private readonly defaultExpandLevel!: number

  @Ref('tree') private readonly treeRef!: any

  private defaultExpandedNodes: ITreeNode[] = []

  private get nodeOptions() {
    const nodeOptions = {
      idKey: 'id',
      nameKey: 'name',
      childrenKey: 'children'
    }
    return Object.assign(nodeOptions, this.options)
  }

  private created() {
    const defaultExpandedNodes = this.handleGetExpandNodeByDeep(this.defaultExpandLevel, this.nodes)
    if (this.defaultCheckedNodes?.length) {
      defaultExpandedNodes.push(...this.defaultCheckedNodes)
    }
    this.defaultExpandedNodes = defaultExpandedNodes
  }

  public getSelectedStatus(data: any) {
    const { idKey = 'id' } = this.nodeOptions
    const id = data[idKey]
    return this.defaultCheckedNodes.includes(id)
  }

  @Emit('select-change')
  public handleSelectChange(treeNode: ITreeNode) {
    return treeNode
  }

  public handleSetChecked(id: string | string[]) {
    if (this.treeRef) {
      this.treeRef.removeChecked()
      this.treeRef.setChecked(id, { emitEvent: false, beforeCheck: false, checked: true })
    }
  }

  public addNode(data: ITreeNode[], parentId: string | number) {
    this.treeRef?.addNode(data, parentId)
  }

  private handleGetExpandNodeByDeep(deep = 1, treeData: ITreeNode[] = []) {
    return treeData.reduce((pre: any[], node) => {
      ((deep) => {
        if (deep > 1 && Array.isArray(node.children) && node.children.length > 0) {
          pre = pre.concat(this.handleGetExpandNodeByDeep(deep = deep - 1, node.children))
        } else {
          pre = pre.concat(node.id)
        }
      })(deep)
      return pre
    }, [])
  }
}
</script>
<style lang="scss" scoped>
::v-deep .bk-big-tree-node {
  &.is-checked {
    background: #f5f6fa;
  }
  &.is-selected {
    /* stylelint-disable-next-line declaration-no-important */
    background: #e1ecff !important;
    .node-content {
      color: #63656e;
    }
  }
  &:hover {
    background: #f5f6fa;
  }
  .node-checkbox {
    /* stylelint-disable-next-line declaration-no-important */
    display: none !important;
  }
  .node-content {
    overflow: inherit;
    text-overflow: inherit;
    white-space: nowrap;
  }
}
.node-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  .num {
    background: #f0f1f5;
    border-radius: 2px;
    height: 18px;
    line-height: 18px;
    padding: 0 5px;
    color: #63656e;
    &.selected {
      background: #fff;
    }
  }
}
</style>
