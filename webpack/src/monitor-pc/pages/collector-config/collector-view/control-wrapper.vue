<template>
  <div class="control-wrapper" ref="listWrap">
    <!-- 主机列表 -->
    <div class="list-wrapper">
      <!-- 左侧头部 -->
      <div class="left-title">
        <i class="icon-monitor icon-zhankai" @click="showTaskList = true"></i>
        <span class="title-text">{{detailInfo.name || customEscalInfo.name}}</span>
      </div>
      <!-- 主机拓扑 -->
      <div class="left-main" v-monitor-loading="{ isLoading: topoLoading }">
        <bk-input
          clearable
          @change="searchTopo"
          v-model="searchTopText"
          :placeholder="$t('搜索IP/主机名')"
          :right-icon="'bk-icon icon-search'">
        </bk-input>
        <div
          class="tab-list"
          v-if="routeType === 'collect'">
          <div
            v-for="(item, index) in tabList"
            :key="index"
            v-bk-tooltips="{ content: item.tips ? item.tips : '' }"
            :class="['tab-item', { 'tab-active': item.type === host.status }]"
            @click="handleClickTab(item)">
            <span
              v-if="item.type !== 'all'"
              :class="['dots', item.type]">
            </span>{{item.type === 'all' ? item.name : statusData[item.type].count}}
          </div>
        </div>
        <div class="big-tree-wrapper">
          <template v-if="!hiddenTopHostList">
            <div
              :class="['all-data', {
                'all-data-active': host.active === null,
                'mt10': routeType === 'custom'
              }]"
              @click="handleSelectNode(null)">{{$t('数据总览')}}</div>
            <!-- 拓扑展示 -->
            <div class="big-tree-main" v-if="hostTopoStatus.topo">
              <bk-big-tree
                :class="['big-tree', { 'clear-selected': host.active === null }]"
                ref="bkBigTree"
                :filter-method="filterMethod"
                :default-expanded-nodes="defaultExpandedNodes"
                :data="treeData"
                :selectable="enableCmdbLevel"
                :expand-on-click="false">
                <template #default="node">
                  <div
                    v-if="node.data && node.data.status"
                    :class="[
                      'bk-tree-node',
                      { 'active': !enableCmdbLevel && (node.data.service_instance_id === host.active || node.data.instance_id === host.active) }
                    ]"
                    @click="handleSelectNode(node.data)">
                    <span style="padding-right: 5px;">
                      <span :class="['dots', node.data.status.toLocaleLowerCase()]"></span>
                      {{node.data.instance_name}}
                      <span class="host-name" v-if="node.data.bk_host_name">({{node.data.bk_host_name}})</span>
                    </span>
                  </div>
                  <span v-else-if="node.data" class="topo-node" @click="handleSelectNode(node.data)">{{node.data.name}}</span>
                </template>
              </bk-big-tree>
            </div>
            <!-- 主机列表 -->
            <bk-virtual-scroll
              v-if="hostTopoStatus.host || routeType === 'custom'"
              ref="hostVirtualScroll"
              class="host-list-wrapper"
              style="height: calc(100% - 32px)"
              :item-height="32">
              <template slot-scope="item">
                <div
                  v-if="routeType === 'collect'"
                  :class="['host-item', { 'host-item-active': item.data.service_instance_id === host.active || item.data.instance_id === host.active }]"
                  @click="handleSelectNode(item.data)">
                  <span :class="['dots', item.data.status.toLocaleLowerCase()]"></span>
                  {{`${item.data.ip}`}}<span class="host-name" v-if="item.data.bk_host_name">({{item.data.bk_host_name}})</span>
                </div>
                <div v-else :class="['host-item', { 'host-item-active': item.data === host.active }]" @click="handleSelectNode(item.data)">
                  {{item.data}}
                </div>
              </template>
            </bk-virtual-scroll>
          </template>
          <bk-exception v-else type="empty" scene="part" class="empty-wrapper">
            <span>{{$t('暂无数据')}}</span>
          </bk-exception>
        </div>
      </div>
    </div>
    <transition name="task-list">
      <!-- 任务列表 -->
      <div class="task-list-wrapper" v-show="showTaskList">
        <!-- 左侧头部 -->
        <div class="task-title">
          <span class="title-text">{{routeType === 'collect' ? $t('任务列表') : $t('指标列表')}}</span>
          <i class="icon-monitor icon-shouqi" @click="showTaskList = false"></i>
        </div>
        <div class="task-main" v-monitor-loading="{ 'isLoading': taskLoading }">
          <bk-input
            clearable
            v-model="searchTaskText"
            :placeholder="routeType === 'collect' ? $t('输入任务名称') : $t('请输入指标名/ID')"
            :right-icon="'bk-icon icon-search'"
            @change="searchTask">
          </bk-input>
          <!-- <ul class="task-list" v-if="taskList.length">
            <li
              v-for="(item, index) in taskList"
              :key="index"
              :class="['task-item', { 'task-item-active': item.id === +$route.params.id }]"
              @click="handleChangeTask(item)">
              {{item.name}}
            </li>
          </ul> -->
          <div style="padding: 9px 0; height: 100%;" v-show="taskList.length || customData.list.length">
            <bk-virtual-scroll
              class="task-list"
              v-if="routeType === 'collect'"
              ref="taskListVirtualScroll"
              :list="taskList"
              :item-height="32">
              <template slot-scope="item">
                <div
                  :class="['task-item', { 'task-item-active': item.data.id === +$route.params.id }]"
                  @click="handleChangeTask(item.data)">
                  {{item.data.name}}
                </div>
              </template>
            </bk-virtual-scroll>
            <ul v-else class="task-list custom-list" ref="customList">
              <li
                v-for="(item, index) in customData.list"
                :key="index"
                :class="['task-item', { 'task-item-active': item['time_series_group_id'] === +$route.params.id }]"
                @click="handleChangeTask(item)">
                {{item.name}}
              </li>
            </ul>
          </div>
          <bk-exception v-show="!(taskList.length || customData.list.length)" type="empty" scene="part" class="empty-wrapper">
            <span>{{$t('暂无数据')}}</span>
          </bk-exception>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Watch, Prop, Ref, Emit } from 'vue-property-decorator'
import { frontendTargetStatusTopo, collectConfigList } from '../../../../monitor-api/modules/collecting'
import { customTimeSeriesDetail, customTimeSeriesList } from '../../../../monitor-api/modules/custom_report'
import { deepClone } from '../../../../monitor-common/utils/utils'
import { IStatusData, ITabList, IDetailInfo, IHostTopoStatus, ICustomData } from '../collector-config-type'
import { debounce, throttle } from 'throttle-debounce'

import viewWrapper from './view-wrapper.vue'

@Component({
  name: 'control-wrapper',
  components: {
    viewWrapper
  }
})
export default class ControlWrapper extends Vue {
  // 路由参数 id、 name
  @Prop({ default: '', required: true, type: [String, Number] }) readonly id: string | number
  @Prop({ default: '', required: true, type: [String, Number] }) readonly name: string | number
  @Prop({ default: () => ({}), required: true, type: Object }) readonly detailInfo: IDetailInfo
  @Prop({ type: Object }) readonly hostTopoStatus: IHostTopoStatus
  @Prop({ type: String }) readonly routeType: 'collect' | 'custom'

  @Ref('bkBigTree') readonly bkBigTreeRef: any
  @Ref('hostVirtualScroll') readonly hostVirtualScrollRef: any
  @Ref('taskListVirtualScroll') readonly taskListVirtualScrollRef: any
  @Ref('listWrap') readonly listWrapRef: HTMLElement
  @Ref('customList') readonly customListRef: HTMLElement

  private host: any = {
    cacheData: [],
    cacheTreeData: [],
    data: [],
    param: [],
    active: null,
    status: 'all',
    node: null
  }

  private tabList: ITabList[] = [
    {
      name: window.i18n.tc('全部'),
      type: 'all'
    },
    {
      type: 'success',
      tips: `${window.i18n.t('正常')}  (${window.i18n.t('近3个周期数据')})`
    },
    {
      type: 'failed',
      tips: `${window.i18n.t('异常')}  (${window.i18n.t('下发采集失败')})`
    },
    {
      type: 'nodata',
      tips: `${window.i18n.t('无数据')}  (${window.i18n.t('近3个周期数据')})`
    }
  ]

  private defaultExpandedNodes: any = []
  private showTaskList = false
  private topoLoading = false
  private taskLoading = false

  private treeData: any = []

  // 各状态数据
  private statusData: IStatusData = {
    success: {
      count: 0,
      data: []
    },
    failed: {
      count: 0,
      data: []
    },
    nodata: {
      count: 0,
      data: []
    },
    all: {
      count: 0,
      data: []
    }
  }

  // 拓扑搜索参数
  private searchTopo: Function
  private searchTopText = ''
  // 主机搜索参数
  private searchHostText = ''
  // 采集任务列表数据
  private taskList: any = []
  private taskListCache: any = []
  // 采集任务搜索数据
  private searchTask: Function
  private searchTaskText = ''
  // 自定义指标目标列表
  private customEscalTargetList: string[] = []
  // 自定义指标信息
  private customEscalInfo: any = {}
  // 监听大小变化的对像
  private resizeObserver: any = null
  private resizeFn: Function
  // 自定指标数据
  private customData: ICustomData = {
    list: [],
    page: 1,
    total: 1,
    limit: Math.ceil(document.body.clientHeight / 32),
    searchKey: ''
  }
  private throttledScroll: Function = () => {}

  get enableCmdbLevel() {
    return this.$store.getters.enable_cmdb_level
  }

  @Emit('on-target-list-change')
  private emitTargetListChange(list: any) {
    return list
  }

  @Emit('on-select-node')
  private handleSelectNodeChange(v) {
    return v
  }

  private get targetList() {
    if (this.routeType === 'collect') {
      return this.statusData.all.data
    } if (this.routeType === 'custom') {
      return this.customEscalTargetList
    }
  }

  private get hostList() {
    let list = []
    if (this.routeType === 'collect') {
      if (this.hostTopoStatus.host) {
        list = this.statusData[this.host.status].data
        const text = this.searchHostText.toLocaleLowerCase()
        list = list.filter((item) => {
          const name = (item.ip + item.bk_host_name).toLocaleLowerCase()
          return name.indexOf(text) > -1
        })
      }
    } else if (this.routeType === 'custom') {
      const text = this.searchHostText.toLocaleLowerCase()
      list = this.customEscalTargetList.filter((item) => {
        const name = item.toLocaleLowerCase()
        return name.indexOf(text) > -1
      })
    }

    return list
  }

  private get hiddenTopHostList() {
    const noTopo = this.hostTopoStatus.topo && !this.treeData.length
    const noHost = this.hostTopoStatus.host && !this.hostList.length
    const noTargetList = this.routeType === 'custom' && !this.hostList.length
    return noHost || noTopo || noTargetList
  }

  @Watch('targetList')
  private handleTatgetListChange(list: any) {
    this.emitTargetListChange(list)
  }

  @Watch('hostList', { immediate: true })
  private async handleHostListChange(list) {
    await this.$nextTick()
    // 更新主机虚拟滚动数据
    if (this.hostVirtualScrollRef && (this.hostTopoStatus.host || this.routeType === 'custom')) {
      this.hostVirtualScrollRef.setListData(list)
    }
  }

  @Watch('id')
  private idChange(v, ov) {
    if (+v !== +ov) {
      this.getTaskList()
    }
  }

  @Watch('showTaskList')
  private async showTaskListChange(v) {
    await this.$nextTick()
    v && this.taskListVirtualScrollRef && this.taskListVirtualScrollRef.resize()
  }

  private created() {
    // 搜索函数防抖
    this.searchTopo = debounce(300, false, v => this.handleSearchTopo(v))
    this.searchTask = debounce(500, false, v => this.handleSearchTask(v))
    this.getTaskList()
  }

  private mounted() {
    this.resizeFn = debounce(300, false, () => {
      this.hostVirtualScrollRef?.resize()
      this.taskListVirtualScrollRef?.resize()
      this.bkBigTreeRef?.resize()
    })
    try {
      this.resizeObserver = new ResizeObserver(this.resizeFn)
      this.resizeObserver.observe(this.listWrapRef)
    } catch (error) {
      console.log(error)
    }
    if (this.routeType === 'custom') {
      this.bindCustomListScroll()
    }
  }

  private beforeDestroy() {
    this.resizeObserver.unobserve(this.listWrapRef)
    this.customListRef.removeEventListener('scroll', this.throttledScroll)
  }

  private getTaskList() {
    if (this.routeType === 'custom') {
      this.customData.page = 1
      this.customData.list = []
      // 自定义指标列表
      this.getCustomDataList()
    } else if (this.routeType === 'collect') {
      // 采集任务列表
      this.getCollectTaskList()
    }
  }

  private async initData() {
    this.initHost()
    if (this.routeType === 'collect') {
      // 采集任务列表
      this.clearHostData()
      const data = await this.getTargetHost()
      this.treeData = data
      this.host.cacheTreeData = data
      this.host.status = 'all'
      this.host.active = null
      // 统计个状态数据
      this.traverseTree(data)
    } else if (this.routeType === 'custom') {
      this.topoLoading = true
      // 自定义指标列表
      customTimeSeriesDetail({ time_series_group_id: this.$route.params.id }).then((res) => {
        this.customEscalInfo = res
        this.customEscalTargetList = res.target
      })
        .finally(() => {
          this.topoLoading = false
        })
    }
  }

  private initHost() {
    this.host = {
      cacheData: [],
      cacheTreeData: [],
      data: [],
      param: [],
      active: null,
      status: 'all',
      node: null
    }
  }

  private bindCustomListScroll() {
    this.throttledScroll = throttle(300, false, this.handleScroll)
    this.customListRef.addEventListener('scroll', this.throttledScroll)
  }

  private handleScroll(e) {
    const { scrollHeight, scrollTop, clientHeight } = e.target
    const isEnd = scrollHeight - scrollTop === clientHeight
    if (isEnd && this.customData.list.length < this.customData.total) {
      if (this.taskLoading) return
      // 分页加载
      this.getCustomDataList(this.customData.page + 1).then(() => {
        this.customData.page += 1
      })
    }
  }

  // 获取自定义指标数据
  private getCustomDataList(nextPage?: number) {
    const { searchKey, page, limit } = this.customData
    const params = {
      search_key: searchKey,
      page,
      page_size: limit
    }
    nextPage && (params.page = nextPage)
    this.taskLoading = true
    return customTimeSeriesList(params).then((res) => {
      this.customData.list = this.customData.list.concat(res.list)
      this.customData.total = res.total
    })
      .catch(() => [])
      .finally(() => this.taskLoading = false)
  }

  // tab切换
  private handleClickTab(tab: ITabList) {
    if (tab.type !== 'all' && !this.statusData[tab.type].count) return
    this.host.status = tab.type
    // this.host.active = null
    this.searchTopText = ''
    this.searchHostText = ''
    this.hostVirtualScrollRef && this.hostVirtualScrollRef.scrollPageByIndex(0)
    if (this.hostTopoStatus.topo) {
      this.treeData = tab.type === 'all' ? this.host.cacheTreeData : this.trimTree()
      this.handleExpandeds(this.treeData)
    }
  }

  private clearHostData() {
    for (const key in this.statusData) {
      this.statusData[key].count = 0
      this.statusData[key].data = []
    }
  }

  // 获取主机数据
  private getTargetHost(): Promise<any> {
    return new Promise((resolve, reject) => {
      this.topoLoading = true
      frontendTargetStatusTopo({ id: this.$route.params.id }).then((data) => {
        resolve(data)
      })
        .catch((err) => {
          reject(err)
        })
        .finally(() => {
          this.topoLoading = false
        })
    })
  }

  // 选中节点
  private handleSelectNode(node: any) {
    if (this.routeType === 'collect') {
      let curActive = null
      // 判断视图类型
      if (node === null) {  // 1. 数据预览
        curActive = null
      } else if (node.status) { // 2. 主机视图
        const { targetObjectType } = this.detailInfo
        if (targetObjectType === 'HOST') {
          curActive = node.instance_id
        } else if (targetObjectType === 'SERVICE') {
          curActive = node.service_instance_id
        }
      } else { // 3. 拓扑节点
        curActive = `${node.bk_inst_id}-${node.bk_obj_id}`
      }
      // 判断视图类型是否变更 和 是否开启功能开关
      if (curActive === this.host.active || (!this.enableCmdbLevel && node && !node.status)) return

      this.host.active = curActive
      this.host.node = node
      this.handleSelectNodeChange(this.host)
    } else if (this.routeType === 'custom') {
      if (this.host.active === node) return
      this.host.active = node
      this.host.node = node
      this.handleSelectNodeChange(node)
    }
  }

  // 统计状态信息
  private traverseTree(treeData: any) {
    const hosts = new Set()
    const key = this.detailInfo.targetObjectType === 'HOST' ? 'name' : 'service_instance_id'
    const recursiveTraverse = (node) => {
      if (node.children) {
        node.children.forEach((item) => {
          recursiveTraverse(item)
        })
      } else if ((node.ip || node.instance_name) && !hosts.has(node[key])) {
        hosts.add(node[key])
        const status = node.status.toLocaleLowerCase()
        this.statusData[status].count += 1
        this.statusData[status].data.push(node)
        this.statusData.all.count += 1
        this.statusData.all.data.push(node)
      }
    }
    if (this.hostTopoStatus.host) {
      treeData.forEach((node) => {
        hosts.add(node[key])
        const status = node.status.toLocaleLowerCase()
        this.statusData[status].count += 1
        this.statusData[status].data.push(node)
        this.statusData.all.count += 1
        this.statusData.all.data.push(node)
      })
    } else {
      treeData.forEach((node) => {
        recursiveTraverse(node)
      })
    }
    this.handleExpandeds(this.treeData)
  }

  // 处理默认展开
  private handleExpandeds(curTreeData) {
    if (!curTreeData.length) return
    const expandeds = new Set()
    const LEVEL = 3 // 默认展开到第几层
    let count = 1
    const fn = (node) => {
      count < LEVEL && expandeds.add(node.id)
      count += 1
      if (node.children && count < LEVEL) {
        fn(node.children[0])
      }
    }
    fn(curTreeData[0])
    this.defaultExpandedNodes = Array.from(expandeds)
  }

  // 根据目标状态过滤tree数据
  private trimTree() {
    let stack = []
    const result = []
    const treeData = JSON.parse(JSON.stringify(this.host.cacheTreeData))
    const traverse = (node) => {
      stack.unshift(node)
      if (node.children) {
        node.children.forEach((item) => {
          traverse(item)
        })
      } else {
        node.isDelete = node.status.toLocaleLowerCase() !== this.host.status
      }
    }
    treeData.forEach((node) => {
      stack = []
      traverse(node)
      stack.forEach((item) => {
        if (item.children) {
          item.children = item.children.filter(node => !node.isDelete)
          item.isDelete = !item.children.length
        }
      })
      const rootNode = stack[stack.length - 1]
      if (!rootNode.isDelete) {
        result.push(rootNode)
      }
    })
    return result
  }

  // 获取采集任务列表数据
  private async getCollectTaskList() {
    this.taskLoading = true
    const data = await collectConfigList({ refresh_status: false })
      .catch(() => ({}))
      .finally(() => this.taskLoading = false)
    this.taskList = data.config_list?.filter?.(item => item.status === 'STARTED') || []
    this.taskListCache = deepClone(this.taskList)
  }

  // 切换采集任务
  private handleChangeTask(item) {
    this.initHost()
    if (this.routeType === 'collect') {
      if (item.id === this.id) return
      this.$emit('on-task-change')
      this.$router.replace({
        name: 'collect-config-view',
        params: {
          id: item.id,
          title: item.name
        }
      })
    } else {
      if (item.time_series_group_id === +this.id) return
      this.$emit('on-task-change')
      this.$router.replace({
        name: 'custom-escalation-view',
        params: {
          id: item.time_series_group_id
        }
      })
    }
  }
  // 主机topo搜索
  private handleSearchTopo(v: string) {
    if (this.bkBigTreeRef && this.hostTopoStatus.topo) {
      this.bkBigTreeRef.filter(v)
    } else if (this.hostTopoStatus.host || this.routeType === 'custom') {
      this.searchHostText = v
    }
  }

  // 采集任务搜索
  private handleSearchTask(v: string) {
    if (this.routeType === 'collect') {
      if (v) {
        this.taskList = this.taskListCache.filter(item => item.name.includes(v))
      } else {
        this.taskList = this.taskListCache
      }
    } else {
      this.customData.searchKey = v.trim()
      this.customData.page = 1
      this.customData.list = []
      this.getCustomDataList()
    }
  }

  private filterMethod(keyword: string, node: any): boolean {
    if (this.host.status === 'all') {
      return node.data.name.indexOf(keyword) > -1
    }
    return node.data.name.indexOf(keyword) > -1 && node.data.status?.toLocaleLowerCase() === this.host.status
  }
}

</script>

<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.control-wrapper {
  height: 100%;
  .list-wrapper {
    height: 100%;
    .left-title {
      display: flex;
      align-items: center;
      height: 42px;
      background: #fff;
      //   box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
      border-bottom: 1px solid #f0f1f5;
      .icon-zhankai {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 16px;
        width: 48px;
        height: 100%;
        border-right: 1px solid #f0f1f5;
        cursor: pointer;
      }
      .title-text {
        font-size: 12px;
        text-align: left;
        color: #313238;
        line-height: 20px;
        padding: 0 10px;

        @include ellipsis
        }
    }
    .left-main {
      height: calc(100% - 42px);
      padding: 16px 10px 16px 20px;
      padding-bottom: 0;
      .tab-list {
        display: flex;
        margin: 8px 0 10px 0;
        .tab-item {
          flex: 1;
          text-align: center;
          height: 26px;
          line-height: 24px;
          color: #63656e;
          font-size: 12px;
          border: 1px solid #dcdee5;
          border-radius: 2px;
          cursor: pointer;
          &:not(:last-child) {
            margin-right: 2px;
          }
          &:hover {
            border: 1px solid #699df4;
          }
        }
        .tab-active {
          color: #699df4;
          background: #e7effb;
          border: 1px solid #699df4;
        }
      }
      .big-tree-wrapper {
        height: calc(100% - 76px);
        .big-tree-main {
          height: calc(100% - 32px);
          overflow: auto;
        }
        .all-data {
          height: 32px;
          line-height: 32px;
          padding-left: 14px;
          font-size: 14px;
          cursor: pointer;
        }
        .mt10 {
          margin-top: 10px;
        }
        .all-data-active {
          color: #3a84ff;
          background-color: #e1ecff;
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
            cursor: pointer;
            padding-left: calc(var(--level) * 40px);
            &:hover {
              background-color: #e1ecff;
            }
          }
          .topo-node {
            cursor: pointer;
            display: inline-block;
            width: 100%;
          }
          .bk-big-tree-node.is-leaf {
            padding-left: 0;
            cursor: default;
            .bk-tree-node {
              width: max-content;
              padding-left: calc(var(--level) * 40px);
              &:hover {
                background-color: #e1ecff;
                color: #3a84ff;
              }
              &.active {
                color: #3a84ff;
                background-color: #e1ecff;
                width: 100%;
              }
              span {
                cursor: pointer;
              }
            }
          }
        }
        /deep/ .clear-selected {
          .bk-big-tree-node.is-selected {
            background-color: unset;
            .node-content {
              color: unset;
            }
          }
        }
        .host-list-wrapper {
          /deep/.bk-scroll-item {
            white-space: nowrap;
          }
          .host-item {
            height: 32px;
            padding: 0 12px;
            font-size: 12px;
            color: #63656e;
            line-height: 32px;
            white-space: nowrap;
            cursor: pointer;
            &:hover {
              color: #3a84ff;
              background-color: #e1ecff;
            }
          }
          .host-item-active {
            color: #3a84ff;
            background-color: #e1ecff;
          }
        }
      }
      .host-name {
        color: #c4c6cc;
      }
      .dots {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin-right: 6px;
        // background: #f0f1f5;
        // border: 1px solid #dcdee5;
        border-radius: 50%;
      }
      .success {
        background: #a0f5e3;
        border: 1px solid #18c0a1;
      }
      .failed {
        background: #fd9c9c;
        border: 1px solid #ea3636;
      }
      .nodata {
        background: #f0f1f5;
        border: 1px solid #dcdee5;
      }
    }
  }
  .task-list-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: #fff;
    z-index: 100;
    .task-title {
      display: flex;
      align-items: center;
      height: 42px;
      background: #fff;
      border-bottom: 1px solid #f0f1f5;
      .icon-shouqi {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 16px;
        width: 48px;
        height: 100%;
        cursor: pointer;
      }
      .title-text {
        flex: 1;
        font-size: 12px;
        text-align: left;
        color: #313238;
        line-height: 20px;
        padding-left: 20px;
      }
    }
    .task-main {
      height: calc(100% - 42px);
      padding: 16px 20px;
      .task-list {
        height: calc(100% - 16px);
        .task-item {
          height: 32px;
          padding: 0 12px;
          font-size: 12px;
          color: #63656e;
          line-height: 32px;
          cursor: pointer;
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
          &:hover {
            color: #3a84ff;
            background-color: #e1ecff;
          }
        }
        .task-item-active {
          color: #3a84ff;
          background-color: #e1ecff;
        }
      }
      .custom-list {
        overflow-y: auto;
      }
    }
  }
  .empty-wrapper {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    /deep/.part-img {
      margin-top: -100px;
    }
  }
}
// 左侧栏动画
.task-list-enter-active,
.task-list-leave-active {
  transition: all .3s ease-in-out;
}
.task-list-enter,
.task-list-leave-to {
  transform: translateX(-100%);
  //   opacity: .5;
}
</style>
