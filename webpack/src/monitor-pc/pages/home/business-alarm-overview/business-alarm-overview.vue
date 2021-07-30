<template>
  <section class="business-alarm" v-if="selectAlarm">
    <PanelCard class="left" :title="$t('业务监控状态总览')">
      <business-alarm-aquare :squares="businessAlarm"
                             :selected-index.sync="selectedIndex"
                             :is-all-normal.sync="isAllNormal"
                             class="content" :status="selectAlarm.status"></business-alarm-aquare>
    </PanelCard>
    <div class="right">
      <!-- <all-overview v-if="isAllNormal" :selected-index.sync="selectedIndex" :business-alarm="businessAlarm" :alarm="selectAlarm"></all-overview> -->
      <business-alarm-panel :title="selectTitle" :icon="selectAlarm.status" v-show="!isAllNormal">
        <keep-alive>
          <uptimecheck :alarm="selectAlarm" v-if="selectAlarm.name === alarmMap.uptimecheck"></uptimecheck>
          <service :alarm="selectAlarm" v-if="selectAlarm.name === alarmMap.service"></service>
          <process :alarm="selectAlarm" v-if="selectAlarm.name === alarmMap.process"></process>
          <os :alarm="selectAlarm" v-if="selectAlarm.name === alarmMap.os"></os>
        </keep-alive>
      </business-alarm-panel>
    </div>
  </section>
</template>

<script>
import PanelCard from '../components/panel-card/panel-card'
import BusinessAlarmAquare from '../components/business-alarm-square/business-alarm-square'
import BusinessAlarmPanel from '../components/business-alarm-panel/business-alarm-panel'
import Uptimecheck from './uptimecheck'
import Service from './service'
import Os from './os'
import Process from './process'
// import AllOverview from './all-overview'
import { alarmDetailChartData } from '../../../../monitor-api/modules/event_center'
export default {
  name: 'business-alarm-overview',
  components: {
    BusinessAlarmAquare,
    PanelCard,
    BusinessAlarmPanel,
    Uptimecheck,
    Service,
    Os,
    Process
    // AllOverview
  },
  props: {
    businessAlarm: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  data() {
    return {
      selectedIndex: 0,
      isAllNormal: false,
      alarmMap: {
        uptimecheck: 'uptimecheck',
        service: 'service',
        process: 'process',
        os: 'os'
      },
      titleMap: {
        uptimecheck: {
          serious: this.$t('拨测监控异常报告'),
          slight: this.$t('拨测监控异常报告'),
          normal: this.$t('拨测监控很健康'),
          unset: this.$t('暂未接入【服务拨测】')
        },
        service: {
          serious: this.$t('服务监控异常报告'),
          slight: this.$t('服务监控异常报告'),
          normal: this.$t('服务监控很健康'),
          unset: this.$t('暂未接入【服务监控】')
        },

        process: {
          serious: this.$t('进程监控异常报告'),
          slight: this.$t('进程监控异常报告'),
          normal: this.$t('进程监控很健康'),
          unset: this.$t('暂未接入【进程监控】')
        },
        os: {
          serious: this.$t('主机监控异常报告'),
          slight: this.$t('主机监控异常报告'),
          normal: this.$t('主机监控很健康'),
          unset: this.$t('暂未接入【主机监控】')
        }
      }
    }
  },
  computed: {
    selectAlarm() {
      return this.businessAlarm[this.selectedIndex]
    },
    selectTitle() {
      return this.titleMap[this.selectAlarm.name][this.selectAlarm.status]
    },
    selectLogs() {
      return this.selectAlarm.operate_records ? this.selectAlarm.operate_records[0].operate_desc : ''
    }
  },
  watch: {
    businessAlarm: {
      handler() {
        this.handleSetIndex()
      },
      deep: true
    }
  },
  created() {
    if (this.businessAlarm.length) {
      this.handleSetIndex()
    }
  },
  methods: {
    getCustomAlarmChartData() {
      alarmDetailChartData({
        alarm_id: 5838598, // 告警实例ID
        monitor_id: 364, // 监控项ID
        chart_type: 'main' // 固定值
      })
    },
    findIndexByStatus(status) {
      return this.businessAlarm.findIndex(item => item.status === status)
    },
    handleSetIndex() {
      // if (this.businessAlarm.every(item => item.status === 'normal')) {
      //     this.isAllNormal = true
      // }
      let selectIndex = this.findIndexByStatus('serious')
      if (selectIndex === -1) {
        selectIndex = this.findIndexByStatus('slight')
        if (selectIndex === -1) {
          selectIndex = this.findIndexByStatus('unset')
        }
      }
      this.selectedIndex = selectIndex === -1 ? 0 : selectIndex
    }
  }
}
</script>

<style scoped lang="scss">
    .business-alarm {
      display: flex;
      .left {
        width: 357px;
        height: 403px;
        background: #fff;
        .content {
          position: relative;
          left: 80px;
          top: 108px;
        }
      }
      .right {
        flex: 1;
        background: #fafbfd;
        border-radius: 0px 2px 2px 0px;
      }
    }
</style>
