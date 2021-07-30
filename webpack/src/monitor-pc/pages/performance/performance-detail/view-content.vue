<template>
  <div class="view-content" v-bkloading="{ isLoading: loading }">
    <keep-alive>
      <dashboard-panels
        v-if="type === 'host'"
        :groups-data="groupsData"
        :variable-data="variableData"
        :compare-value="compareValue"
        :chart-type="chartType"
        :chart-option="chartOption"
        :keyword="keyword">
      </dashboard-panels>
      <process-content
        v-else
        :groups-data="groupsData"
        :variable-data="variableData"
        :compare-value="compareValue"
        :chart-type="chartType"
        @process-change="handleProcessChange"
        :chart-option="chartOption"
        :keyword="keyword">
      </process-content>
    </keep-alive>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'
import { ViewType, IHostGroup, ChartType, IQueryOption } from '../performance-type'
import MonitorEcharts from '../../../../monitor-ui/monitor-echarts/monitor-echarts.vue'
import ProcessContent from './view-content-process.vue'
import DashboardPanels from './dashboard-panels.vue'
import { ICurNode } from '../../../store/modules/performance'

@Component({
  name: 'view-content',
  components: {
    MonitorEcharts,
    ProcessContent,
    DashboardPanels
  }
})
export default class ViewContent extends Vue {
  // 视图类型
  @Prop({ default: 'host' }) readonly type: ViewType
  // 视图样式
  @Prop({ default: 0 }) readonly chartType: ChartType
  @Prop({ required: true }) readonly curNode: ICurNode
  // 分组数据
  @Prop({ default: () => [], type: Array }) readonly groupsData: IHostGroup[]
  @Prop({ default: false }) readonly loading: boolean
  @Prop({ default: '' }) readonly keyword: string
  @Prop({ required: true }) readonly compareValue: IQueryOption
  // 汇聚方法（节点类型会使用）
  @Prop({ default: '', type: String }) method!: string

  private chartOption: any = {
    annotation: {
      show: true,
      list: ['strategy']
    }
  }
  get variableData() {
    if (this.curNode.type === 'host') {
      return {
        $bk_target_ip: this.curNode.ip,
        $bk_target_cloud_id: this.curNode.cloudId,
        $process_name: this.curNode.processId
      }
    }
    return {
      $bk_obj_id: this.curNode.bkObjId,
      $bk_inst_id: this.curNode.bkInstId,
      $method: this.method,
      $process_name: this.curNode.processId
    }
  }
  @Emit('process-change')
  handleProcessChange(v) {
    return v
  }
}
</script>
<style lang="scss" scoped>
.view-content {
  background: #fafbfd;
  padding: 16px;
  height: 100%;
  width: 100%;
  overflow: auto;
}
</style>
