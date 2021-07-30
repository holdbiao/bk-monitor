<template>
  <div class="content-process">
    <ul class="process-list">
      <li
        class="process-list-item"
        v-for="(item, index) in processList"
        :class="{ 'is-active': item.displayName === process }"
        :key="index"
        @click="handleProcessChange(item)">
        <span :class="`item-status-${item.status}`"></span>
        <abnormal-tips
          :tips-text="handleComponentStatusData(item.status).tipsText"
          :link-text="handleComponentStatusData(item.status).linkText"
          :link-url="handleComponentStatusData(item.status).linkUrl"
          :doc-link="handleComponentStatusData(item.status).docLink"
          placement="top"
          :delay="200"
          ext-cls="abnormal-tips-wrap"
          :disabled="![2, 1].includes(transformStatus(item.status))">
          {{item.displayName}}
        </abnormal-tips>
      </li>
    </ul>
    <ul class="chart-list" v-if="false">
      <li class="chart-list-item special-item">
        <monitor-echarts
          :key="process + '-text'"
          chart-type="text"
          class="chart-item"
          :title="`${process}${$t('运行时长')}`"
          style="marginRight: 10px"
          height="100"
          :get-series-data="handleGetTextSeries">
        </monitor-echarts>
        <monitor-echarts
          :key="process + '-status'"
          class="chart-item"
          chart-type="status"
          :title="$t('端口运行状态')"
          height="100"
          :get-series-data="handleGetPortSeries">
        </monitor-echarts>
      </li>
    </ul>
    <dashboard-panels
      :keyword="keyword"
      :chart-option="chartOption"
      :groups-data="groupsData"
      :variable-data="variableData"
      :compare-value="compareValue"
      :chart-type="chartType">
    </dashboard-panels>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop } from 'vue-property-decorator'
import PerformanceModule from '../../../store/modules/performance'
import MonitorEcharts from '../../../../monitor-ui/monitor-echarts/monitor-echarts-new.vue'
import DashboardPanels from './dashboard-panels.vue'
import AbnormalTips from '../../../components/abnormal-tips/abnormal-tips.vue'
@Component({
  name: 'view-content-process',
  components: {
    MonitorEcharts,
    DashboardPanels,
    AbnormalTips
  }
})
export default class ViewContentProcess extends Vue {
  @Prop({ default: () => [], type: Array }) readonly groupsData: IHostGroup[]
  @Prop({ default: 1 }) readonly chartType: ChartType
  @Prop() readonly variableData: {}
  @Prop({ required: true }) readonly compareValue: IQueryOption
  @Prop({ default: '' }) readonly keyword: string

  // 图表配置设置
  @Prop() readonly chartOption: object
  private portList: {port: string; status: string}[] =  []

  private componentStatusMap: any = {
    1: { // 异常
      tipsText: window.i18n.t('原因：查看进程本身问题或者检查进程配置是否正常'),
      docLink: 'processMonitor'
    },
    2: { // 无数据
      tipsText: window.i18n.t('原因：processbeat进程采集器未安装或者状态异常'),
      linkText: window.i18n.t('前往节点管理处理'),
      linkUrl: `${this.$store.getters.bkNodemanHost}#/plugin-manager/list`
    },
    3: {}
  }
  get processList() {
    return PerformanceModule.curProcessList
  }
  get process() {
    return PerformanceModule.curProcess
  }
  @Emit('process-change')
  handleProcessChange(item) {
    PerformanceModule.setProcessId(item.displayName)
  }

  handleComponentStatusData(status: number) {
    const resStatus = this.transformStatus(status)
    return this.componentStatusMap[resStatus]
  }
  transformStatus(status: number) {
    let resStatus = 1
    switch (status) {
      case -1:
        resStatus = 2
        break
      case 0:
        resStatus = 3
        break
      default:
        resStatus = 1
        break
    }
    return resStatus
  }
  handleGetTextSeries() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          value: 56.78,
          unit: this.$t('小时')
        })
      }, 1000)
    })
  }
  async handleGetPortSeries() {
    const data = await PerformanceModule.getHostProcessPortDetail()
    return data
  }
}
</script>
<style lang="scss" scoped>
$statusColors: #dcdee5 #10c178 #fd9c9c #ffeb00;
$statusBgColors: #f0f1f5 #85dcb8 #ea3636 #ffeb00;

.content-process {
  color: #63656e;
  font-size: 12px;
  .process-list {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 10px;
    &-item {
      display: flex;
      align-items: center;
      border: 1px solid #dcdee5;
      border-radius: 2px;
      height: 24px;
      background-color: #fafbfd;
      padding: 3px 10px 3px 6px;
      line-height: 16px;
      margin: 0 6px 6px 0;

      @for $i from -1 through 1 {
        .item-status-#{$i} {
          background-color: nth($statusBgColors, $i + 2);
          border: 1px solid nth($statusColors, $i + 2);
          width: 6px;
          height: 6px;
          border-radius: 6px;
          margin-right: 5px;
        }
      }
      &:hover {
        cursor: pointer;
      }
      &.is-active {
        border-color: #3a84ff;
        color: #3a84ff;
      }
    }
  }
  .chart-list {
    display: flex;
    flex-wrap: wrap;
    margin-top: 10px;
    margin-right: -10px;
    &-item {
      display: flex;
      margin: 0 10px 10px 0;
      &.special-item {
        width: 100%;
        .chart-item {
          box-shadow: 0px 1px 2px 0px rgba(0,0,0,.1);
          border-radius: 2px;
          height: 100px;
        }
      }
    }
  }
}
</style>
