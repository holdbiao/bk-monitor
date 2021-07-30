<template>
  <div
    class="host-list"
    data-tag="resizeTarget"
    :style="{ width: drag.width + 'px', 'flex-basis': drag.width + 'px' }"
    v-bkloading="{ isLoading: reload }">
    <div
      class="resize-line"
      @mousedown="handleMouseDown">
    </div>
    <div class="host-list-title">
      <span>{{ $t('主机列表') }}</span>
      <i class="icon-monitor icon-double-up"
         @click="handleTogglePanel">
      </i>
    </div>
    <div class="host-list-content">
      <div class="content-top">
        <bk-input v-model="keyword" @change="handleSearch"></bk-input>
        <span :class="['content-top-refresh', { 'loading': reload }]"
              @click="handleReloadList">
          <i class="icon-monitor icon-mc-alarm-recovered"></i>
        </span>
      </div>
      <div class="content-bottom">
        <!-- <bk-virtual-scroll
          :list="hostList"
          :item-height="itemHeight"
          ref="hostList">
          <template #default="{ data }">
            <div
              :class="[
                'content-bottom-item',
                {
                  'active': active === `${data.bk_host_innerip}-${data.bk_cloud_id}`
                }
              ]"
              @click="handleItemClick(data)">
              <span :class="['item-status', `status-${statusMap[data.status].status}`]"></span>
              <span class="ml10">{{ data.bk_host_innerip }}</span>
              <span class="item-name" v-if="data.bk_host_name">
                {{ `(${data.bk_host_name})` }}
              </span>
            </div>
          </template>
        </bk-virtual-scroll> -->
        <bk-big-tree
          :class="['big-tree', { 'selectable-tree': !enableCmdbLevel }]"
          ref="bkBigTree"
          :default-expanded-nodes="defaultExpandedID"
          :default-selected-node="defaultExpandedID[0]"
          :filter-method="filterMethod"
          :data="hostTopoTreeList"
          :height="treeHeight"
          :selectable="enableCmdbLevel"
          :expand-on-click="false"
          v-if="hostTopoTreeList && !!hostTopoTreeList.length">
          <template #empty>
            <div>empty</div>
          </template>
          <template #default="{ data }">
            <div :class="[
                   'bk-tree-node',
                   { 'active': (`${data.ip}-${data.bk_cloud_id}` === curNode.id)
                     || (enableCmdbLevel && (`${data.bk_inst_id}-${data.bk_obj_id}` === curNode.id)) }
                 ]"
                 @click="handleItemClick(data)">
              <span class="node-content" style="padding-right: 5px;">
                <span v-if="data.status !== undefined" :class="['item-status', `status-${statusMap[data.status].status}`]"></span>
                <span>{{data.ip || data.bk_inst_name}}</span>
                <span v-if="data.bkHostName" class="host-name">({{data.bkHostName}})</span>
              </span>
            </div>
          </template>
        </bk-big-tree>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Model, Watch, Ref } from 'vue-property-decorator'
import PerformanceModule, { ICurNode } from '../../../store/modules/performance'
import { debounce } from 'throttle-debounce'
import { deepClone } from '../../../../monitor-common/utils/utils'

@Component({ name: 'host-list' })
export default class HostList extends Vue {
  @Ref('hostList') refHostList: any
  @Ref('bkBigTree') readonly bkBigTreeRef: any

  @Prop({ default: '', type: Object }) readonly curNode: ICurNode
  // 是否显示面板
  @Model('visible-change', { default: true }) readonly visible: boolean

  private treeHeight = 700
  // 重新加载
  private reload = false
  private itemHeight = 32
  private statusMap = {
    '-1': {
      name: window.i18n.t('未知'),
      status: '3'
    },
    0: {
      name: window.i18n.t('正常'),
      status: '1'
    },
    1: {
      name: window.i18n.t('离线'),
      status: '1'
    },
    2: {
      name: window.i18n.t('Agent未安装'),
      status: '2'
    },
    3: {
      name: window.i18n.t('无数据上报'),
      status: '3'
    }
  }
  private searchData = [
    {
      name: '集群',
      id: 'cluster',
      children: [{
        name: '蓝鲸',
        id: 'bkmonitor'
      }]
    },
    {
      name: '模块',
      id: 'module',
      children: [{
        name: 'paas平台',
        id: 'pass'
      }]
    },
    {
      name: '操作系统',
      id: 'system',
      children: [{
        name: '蓝鲸',
        id: 'bkmonitor'
      }]
    }
  ]
  private keyword = ''
  private drag = {
    width: 280,
    minWidth: 100,
    maxWidth: 500,
    defaultWidth: 280,
    dragDown: false
  }
  private handleSearch = null
  private handleResizeTreeDebounce = null
  @Watch('curNode', { immediate: true, deep: true })
  onActiveChange() {
    this.keyword = ''
  }
  @Watch('visible', { immediate: true })
  visibleChange(v) {
    if (v) {
      !this.drag.dragDown && (this.drag.width = this.drag.defaultWidth)
    }
  }

  get enableCmdbLevel() {
    return this.$store.getters.enable_cmdb_level
  }
  //   get keyword() {
  //     return PerformanceModule.keyword
  //   }
  get hostList() {
    return PerformanceModule.filterHostList
  }
  get hostTopoTreeList() {
    if (!this.hostList.length) return []
    const resList = deepClone(PerformanceModule.filterHostTopoTreeList)
    const hostMap = new Map()
    // eslint-disable-next-line no-restricted-syntax
    for (const item of this.hostList) {
      hostMap.set(`${item.bk_host_innerip}-${item.bk_cloud_id}`, item)
    }
    const fn = (list): any => {
      if (list?.length) {
        // eslint-disable-next-line no-restricted-syntax
        for (const item of list) {
          if (item.ip) {
            // const target = this.hostList.find((tar) => {
            //   const a = `${item.ip}-${item.bk_cloud_id}`
            //   const b = `${tar.bk_host_innerip}-${tar.bk_cloud_id}`
            //   return  a === b
            // })
            const target = hostMap.get(`${item.ip}-${item.bk_cloud_id}`)
            item.status = target.status
            item.bkHostName = target.bk_host_name
          } else if (item.children && item.children.length) {
            fn(item.children)
          }
        }
      }
    }
    fn(resList)
    return resList
  }
  get defaultExpandedID() {
    const fn = (list, targetName): any => {
      if (list?.length) {
        // eslint-disable-next-line no-restricted-syntax
        for (const item of list) {
          const sourceId = this.curNode.type === 'host'
            ? `${item.ip}-${item.bk_cloud_id}`
            : `${item.bk_inst_id}-${item.bk_obj_id}`
          if (sourceId === targetName) {
            return item
          } if (item.children && item.children.length) {
            const res = fn(item.children, targetName)
            if (res) return res
          }
        }
      }
    }
    const res = fn(this.hostTopoTreeList, this.curNode.id)
    const data = res ? [res.id] : []
    if (this.bkBigTreeRef) {
      this.bkBigTreeRef.setSelected(data[0])
      this.bkBigTreeRef.setExpanded(data)
    }
    return data
  }
  created() {
    PerformanceModule.getTopoTree({
      instance_type: 'host',
      remove_empty_nodes: false
    })
    this.handleSearch = debounce(300, false, (v) => {
    //   PerformanceModule.setKeyWord(v)
      this.bkBigTreeRef && this.bkBigTreeRef.filter(v)
    })
  }
  mounted() {
    this.handleResizeTreeDebounce = debounce(300, false, this.handleResizeTree)
  }
  activated() {
    this.refHostList && this.refHostList.resize()
  }

  handleItemClick(data) {
    // const osTypeList = { linux: 1, windows: 2, aix: 3 }
    // const curOsType =  osTypeList[data.os_type]
    // return {
    //   ip: data.ip,
    //   cloudId: data.bk_cloud_id,
    //   osType: curOsType
    // }
    const curNode: ICurNode = {
      type: 'host',
      id: ''
    }
    if (!data.ip) {
      curNode.type = 'node'
      curNode.id = `${data.bk_inst_id}-${data.bk_obj_id}`
      curNode.bkInstId = data.bk_inst_id
      curNode.bkObjId = data.bk_obj_id
    } else {
      curNode.type = 'host'
      curNode.id = `${data.ip}-${data.bk_cloud_id}`
      curNode.ip = data.ip
      curNode.cloudId = data.bk_cloud_id
    }
    // 功能开关
    if (!this.enableCmdbLevel && curNode.type === 'node') return

    this.handleNodeChange(curNode)
  }
  @Emit('node-change')
  handleNodeChange(data: ICurNode) {
    return data
  }

  // 显示和隐藏面板
  @Emit('visible-change')
  handleTogglePanel() {
    return !this.visible
  }

  @Emit('reload')
  async handleReloadList() {
    this.reload = true
    this.keyword = ''
    await PerformanceModule.getHostPerformance()
    this.reload = false
  }

  filterMethod(keyword: string, node: any): boolean {
    const { data } = node
    return data.ip && ((data.ip + data.bkHostName).indexOf(keyword) > -1)
  }

  // 更新树形组件宽度
  handleResizeTree() {
    this.bkBigTreeRef?.resize()
  }

  // drag触发
  handleMouseDown(e) {
    let { target } = e
    while (target && target.dataset.tag !== 'resizeTarget') {
      target = target.parentNode
    }
    this.drag.dragDown = true
    const rect = target.getBoundingClientRect()
    document.onselectstart = function () {
      return false
    }
    document.ondragstart = function () {
      return false
    }
    const handleMouseMove = (event) => {
      if (event.clientX - rect.left < this.drag.minWidth) {
        this.drag.width = 0
        if (this.visible) this.handleTogglePanel()
      } else {
        this.drag.width = Math.min(Math.max(this.drag.minWidth, event.clientX - rect.left), this.drag.maxWidth)
        if (!this.visible) this.handleTogglePanel()
      }
      this.handleResizeTreeDebounce()
    }
    const handleMouseUp = () => {
      this.drag.dragDown = false
      document.body.style.cursor = ''
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.onselectstart = null
      document.ondragstart = null
    }
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }
}
</script>
<style lang="scss" scoped>
$statusBorderColors: #2dcb56 #c4c6cc #ea3636;
$statusColors: #94f5a4 #f0f1f5 #fd9c9c;

@keyframes rotate {
  0% { transform: rotate(0deg);}
  50% { transform: rotate(180deg);}
  100% { transform: rotate(360deg);}
}

.host-list {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid #f0f1f5;
  height: 100%;
  .resize-line {
    right: 0;
    background: none;
    cursor: col-resize;
  }
  &-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex: 0 0 42px;
    padding: 0 8px 0 20px;
    border-bottom: 1px solid #f0f1f5;
    i {
      transform: rotate(-90deg);
      font-size: 24px;
      color: #979ba5;
      cursor: pointer;
    }
  }
  &-content {
    height: calc(100% - 42px);
    padding: 16px 20px 0 20px;
    .content-top {
      display: flex;
      &-search {
        flex: 1;
      }
      &-refresh {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-left: 2px;
        height: 32px;
        width: 32px;
        font-size: 16px;
        border: 1px solid #c4c6cc;
        cursor: pointer;
        i {
          width: 16px;
          height: 16px;
        }
        &.loading i {
          animation: rotate 2s linear infinite;
        }
      }
    }
    .content-bottom {
      margin-top: 16px;
      height: calc(100% - 64px);
      /deep/.big-tree {
        /* stylelint-disable-next-line declaration-no-important */
        height: 100%!important;
      }
      .item-status {
        display: inline-block;
        width: 6px;
        min-width: 6px;
        height: 6px;
        border: 1px solid;
        border-radius: 50%;
      }
      &-item {
        display: flex;
        align-items: center;
        height: 32px;
        cursor: pointer;
        padding-left: 10px;
        &:hover {
          background: #f5f6fa;
        }
        .item-name {
          margin-left: 2px;
          color: #c4c6cc;
        }
        &.active {
          background: #e1ecff;
          color: #3a84ff;
          .item-name {
            color: #3a84ff;
          }
        }
      }
      /deep/ .big-tree {
        width: max-content;
        min-width: 100%;
        .is-root {
          .node-options {
            margin-left: 26px;
          }
        }
        .bk-big-tree-node {
          padding-left: calc(var(--level) * 40px);
          &:hover {
            background-color: #e1ecff;
          }
        }
        .bk-big-tree-node.is-leaf {
          cursor: default;
          padding-left: 20px;
          .bk-tree-node {
            width: max-content;
            padding-left: calc(var(--level) * 40px);

            @for $i from 1 through length($statusColors) {
              .status-#{$i} {
                background: nth($statusColors, $i);
                border: 1px solid nth($statusBorderColors, $i);
              }
            }
            &:hover {
              background-color: #e1ecff;
              color: #3a84ff;
            }
            .node-content {
              display: flex;
              align-items: center;
              cursor: pointer;
              .item-status {
                margin-right: 10px;
              }
              .host-name {
                color: #c4c6cc;
              }
            }
          }
        }
      }
      /deep/ .selectable-tree .bk-big-tree-node.is-leaf {
        padding-left: 0;
        .active {
          color: #3a84ff;
          background-color: #e1ecff;
          width: 100%;
        }
      }
      /deep/ .bk-scroll-home .bk-min-nav-slide {
        width: 5px;
        border-radius: 5px;
      }
    }
  }
}
</style>
