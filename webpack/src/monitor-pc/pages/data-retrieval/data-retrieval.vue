<template>
  <div>
    <template v-if="!logShow">
      <div class="data-retrieval">
        <div class="data-retrieval-left"
             data-tag="resizeTarget"
             :style="{ 'flex-basis': drag.width + 'px', width: drag.width + 'px' }">
          <!-- 左边操作区域 -->
          <data-retrieval-operations style="overflow: hidden" @log-click="handleLogClick"></data-retrieval-operations>
          <!-- <div
            class="click-open"
            v-bk-tooltips="openTips"
            v-if="showClickOpen"
            @click="handleClickOpen">
            <i class="icon-monitor icon-arrow-right"></i>
          </div> -->
          <div class="left-drag"
               v-show="!showClickOpen"
               @mousedown="handleMouseDown"
               @mousemove="handleMouseMove">
          </div>
        </div>
        <!-- 视图展示区域 -->
        <div class="data-retrieval-right" :style="{ 'flex-basis': `calc(100% - ${drag.width}px)`, width: `calc(100% - ${drag.width}px)` }">
          <data-retrieval-view :left-show="!showClickOpen" @show-left="drag.width = 450"></data-retrieval-view>
        </div>
      </div>
    </template>
    <log-retrieval v-else></log-retrieval>
  </div>
</template>
<script lang="ts">
import { Component, Mixins, Provide } from 'vue-property-decorator'
import DataRetrievalOperations from './data-retrieval-operations/data-retrieval-operations.vue'
import DataRetrievalView from './data-retrieval-view/data-retrieval-view.vue'
import DataRetrievalStore from '../../store/modules/data-retrieval'
import LogRetrieval from '../log-retrieval/log-retrieval.vue'
import  authorityMixinCreate from '../../mixins/authorityMixin'
import * as dataRetrievalAuthMap from './authority-map'
import { VIEW_AUTH as GRAFANA_VIEW_AUTH, MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../grafana/authority-map'
const authMap = {
  ...dataRetrievalAuthMap,
  GRAFANA_VIEW_AUTH,
  GRAFANA_MANAGE_AUTH
}
Component.registerHooks([
  'beforeRouteEnter'
])

@Component({
  name: 'data-retrieval',
  components: {
    DataRetrievalOperations,
    DataRetrievalView,
    LogRetrieval
  }
})
export default class DataRetrieval extends Mixins(authorityMixinCreate(authMap)) {
  @Provide('authority') authority
  @Provide('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Provide('authorityMap') authorityMap
  drag: { width: number; minWidth: number; maxWidth: number } = { width: 450, minWidth: 300, maxWidth: 800 }
  chartsData: any[] = []

  openTips: any = {
    content: window.i18n.t('点击重新展开'),
    showOnInit: true,
    placements: ['right'],
    delay: 500
  }
  logShow = false
  leftShow = true
  authorityMap = authMap
  get showClickOpen() {
    return this.drag.width < this.drag.minWidth
  }

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (from.name !== 'view-detail' && from.name !== null) {
        DataRetrievalStore.initStoreData()
        DataRetrievalStore.handleAddCondition()
      }
      // 主机详情跳转
      if (from.name === 'performance-detail' || vm.$route.query.targets) {
        let { targets } = vm.$route.query.targets ? vm.$route.query :  vm.$route.params
        if (!targets) return
        if (typeof targets === 'string') targets = JSON.parse(targets)
        targets = vm.handleTargets(targets)
        const initMap = [
          { expr: 'nameNum', value: 0 },
          { expr: 'queryData.target', value: [] },
          { expr: 'queryData.queryConfigs', value: [] },
          { expr: 'queryData.compareConfig', value: { type: 'none', split: true } },
          { expr: 'queryData.tools', value: { timeRange: 1 * 60 * 60 * 1000, refleshInterval: -1 } }
        ]
        // 设置默认参数
        DataRetrievalStore.setDataList(initMap)
        targets.forEach((item) => {
          // 一条查询数据所需数据
          const queryItem = {
            metricField: item.data.metric_field,
            method: item.data.method,
            interval: item.data.interval,
            resultTableId: item.data.result_table_id,
            dataSourceLabel: item.data.data_source_label,
            dataTypeLabel: item.data.data_type_label,
            groupBy: item.data.group_by,
            where: item.data.where
          }
          DataRetrievalStore.handleAddCondition(queryItem)
          // eslint-disable-next-line camelcase
          if (item.data.function?.time_compare) {
            // eslint-disable-next-line camelcase
            DataRetrievalStore.setCompareConfig({ type: 'time', timeOffset: item.data.function.time_compare })
          }
        })

        vm.$nextTick(() => {
          DataRetrievalStore.handleQuery()
        })
      }
    })
  }

  created() {
    DataRetrievalStore.handleAddCondition()
  }

  mounted() {
    window.addEventListener('message', this.handleMessage, false)
  }

  beforeDestroy() {
    window.removeEventListener('message', this.handleMessage, false)
  }

  // drag触发
  handleMouseDown(e: MouseEvent) {
    let { target } = e

    while (target && target.dataset.tag !== 'resizeTarget') {
      target = target.parentNode
    }
    const rect = target.getBoundingClientRect()
    document.onselectstart = function () {
      return false
    }
    document.ondragstart = function () {
      return false
    }
    const handleMouseMove = (event) => {
      if (event.clientX - rect.left < 200) {
        this.drag.width = 0
      } else {
        this.drag.width = Math.min(Math.max(this.drag.minWidth, event.clientX - rect.left), this.drag.maxWidth)
      }
    }
    const handleMouseUp = () => {
      document.body.style.cursor = ''
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.onselectstart = null
      document.ondragstart = null
    }
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // drag触发
  handleMouseMove(e) {
    let { target } = e
    while (target && target.dataset.tag !== 'resizeTarget') {
      target = target.parentNode
    }
  }
  handleClickOpen() {
    if (!this.showClickOpen) return
    this.drag.width = 300
  }
  // 点击日志检索触发
  handleLogClick() {
    this.logShow = true
  }
  // 日志检索点击指标检索派发message
  handleMessage(e) {
    if (e.data && e.data === 'datarieval-click') {
      this.logShow = false
    }
  }

  handleTargets(targets) {
    targets.forEach((item) => {
      const { data } = item
      if (data.where.length) {
        data.where.forEach((where) => {
          // 条件eq转and
          const con = where.condition
          if (con && con.toLowerCase() === 'eq') where.condition = 'and'
        })
      }
    })
    return targets
  }
}
</script>
<style lang="scss" scoped>
.data-retrieval {
  width: 100%;
  display: flex;
  // margin: -20px -24px 0px;
  // height: calc(100vh - 52px);
  overflow: hidden;
  &-left {
    flex: 0 0 450px;
    background: white;
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .1);
    position: relative;
    .left-drag {
      position: absolute;
      right: -3px;
      top: calc(50% - 50px);
      width: 6px;
      height: 100px;
      display: flex;
      align-items: center;
      justify-items: center;
      background-color: #dcdee5;
      border-radius: 3px;
      z-index: 101;
      &::after {
        content: " ";
        height: 80px;
        width: 0;
        border-left: 2px dotted white;
        position: absolute;
        left: 2px;
      }
      &:hover {
        cursor: col-resize;
      }
    }
    .click-open {
      display: flex;
      justify-content: center;
      align-items: center;
      position: absolute;
      right: -10px;
      top: calc(50% - 50px);
      width: 10px;
      height: 100px;
      cursor: pointer;
      border-radius: 0px 8px 8px 0px;
      background-color: #dcdee5;
      z-index: 10;
      .icon-arrow-right {
        display: inline-block;
        width: 16px;
        height: 16px;
        font-size: 16px;
      }
    }
  }
  &-right {
    flex: 1;
  }
}
</style>
