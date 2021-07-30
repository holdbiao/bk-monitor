<template>
  <section class="overview-content">
    <div
      class="item-pie-char"
      v-bkloading="{ isLoading: todayAlarmLoading }">
      <today-alarm-pie
        v-if="!todayAlarmLoading"
        :series-data="todayAlarm.data"
        :unrecovered-count="todayAlarm.unrecoveredCount">
      </today-alarm-pie>
    </div>
    <div
      class="item-business-chart"
      v-bkloading="{ isLoading: businessAlarmLoading }">
      <business-alarm-overview
        v-if="!businessAlarmLoading"
        :business-alarm="businessAlarm">
      </business-alarm-overview>
    </div>
    <div class="item-real-time"
         v-bkloading="{ isLoading: realTimeAlarmLoading }">
      <real-time-alarm-list
        v-if="!realTimeAlarmLoading"
        :list="realTimeAlarm">
      </real-time-alarm-list>
      <div v-if="!realTimeAlarm.length"
           class="fake-wrap">
        <div class="fake-wrap-message">
          <svg-icon class="example-icon"
                    icon-name="warning"></svg-icon>
          <div class="example-message"> {{ $t('暂无告警事件产生...') }} </div>
        </div>
      </div>
    </div>
    <div class="item-types-list"
         v-bkloading="{ isLoading: typeAlarmLoading }"
         :style="{ 'overflow': !typeAlarmListExample ? 'visible' : 'hidden' }">
      <types-alarm-list
        :items="typeAlarmList"
        :days="typeAlarmDays"
        :show-example="typeAlarmListExample"
        @select="getTypeAlarmListData">
      </types-alarm-list>
      <div v-if="typeAlarmListExample"
           class="fake-wrap">
        <div class="fake-wrap-example"> {{ $t('数据示例') }} </div>
      </div>
    </div>
    <div class="item-use-radio"
         v-bkloading="{ isLoading: useAlarmLoading }">
      <use-radio-charts v-if="!useAlarmLoading"
                        :series="useRatioSeries"
                        :show-example="useRetioAlarmExample"></use-radio-charts>
      <div v-if="useRetioAlarmExample"
           class="fake-wrap">
        <div class="fake-wrap-example"> {{ $t('数据示例') }} </div>
      </div>
    </div>
    <div class="item-available-rate"
         ref="itemRate"
         v-bkloading="{ isLoading: availableAlarmLoading }"
         :style="{ 'overflow': availableRate.setList.length ? 'visible' : 'hidden' }">
      <available-rate-chart v-if="!availableAlarmLoading"
                            :set-list="availableRate.setList"
                            :series="availableRate.series"
                            :utcoffset="availableRate.utcoffset"
                            @update="updateSpecialFocusTaskList"
                            :checked-list="availableRate.checkedList">
      </available-rate-chart>
      <div v-if="!availableRate.series.length || errorMsg.length"
           :class="{ 'fake-no-data': availableRate.setList.length }"
           class="fake-wrap">
        <div class="fake-wrap-message">
          <svg-icon class="example-icon"
                    icon-name="warning"></svg-icon>
          <div class="example-message">{{errorMsg || $t('查询无数据...') }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import TodayAlarmPie from './today-alarm-pie/today-alarm-pie'
import BusinessAlarmOverview from './business-alarm-overview/business-alarm-overview'
import RealTimeAlarmList from './realtime-alarm-list/realtime-alarm-list'
import TypesAlarmList from './types-alarm-list/types-alarm-list'
import UseRadioCharts from './use-radio-charts/use-radio-charts'
import AvailableRateChart from './available-rate-chart/available-rate-chart'
import moment from 'moment'
import {
  alarmCountInfo,
  alarmRank,
  monitorInfo,
  hostPerformanceDistribution
} from '../../../monitor-api/modules/overview'
import { frontPageData } from '../../../monitor-api/modules/uptime_check'
import {
  listUptimeCheckTask,
  listApplicationConfig,
  partialUpdateApplicationConfig,
  createApplicationConfig
} from '../../../monitor-api/modules/model'
import { listEvent } from '../../../monitor-api/modules/alert_events'
const seriousColorMap = [
  '#bf2727',
  '#ea3636',
  '#ea5a36',
  '#ff7701',
  '#ff9c01',
  '#ffae48',
  '#FF9C01',
  '#FFAE48',
  '#FFC348',
  '#FFDD48'
]
const normalColorMap = [
  '#2eb050',
  '#2dcb56',
  '#55e533',
  '#8de533',
  '#b6e533',
  '#d1e533',
  '#B6E533',
  '#D1E533',
  '#E5D733',
  '#FFE348'
]
export default {
  name: 'Home',
  components: {
    TodayAlarmPie,
    BusinessAlarmOverview,
    RealTimeAlarmList,
    TypesAlarmList,
    UseRadioCharts,
    AvailableRateChart
  },
  data() {
    return {
      todayAlarm: {
        data: [],
        unrecoveredCount: 0
      },
      realTimeAlarm: [],
      typeAlarmList: [],
      typeAlarmDays: null,
      overviewList: [],
      typeAlarmLoading: true,
      realTimeAlarmLoading: true,
      todayAlarmLoading: true,
      useAlarmLoading: true,
      titleAlarmLoading: true,
      businessAlarmLoading: true,
      homeLoading: true,
      availableAlarmLoading: true,
      availableRate: {
        setList: [],
        checkedList: [],
        series: [],
        specialTaskId: -1,
        utcoffset: 0
      },
      useRatioSeries: [],
      businessAlarm: [],
      typeAlarmListExample: false,
      useRetioAlarmExample: false,
      errorMsg: '',
      interval: null,
      handleResize: null
    }
  },
  created() {
    // this.getOverviewTitleData()
    this.getTodayAlarmPieData()
    this.getRealTimeAlarmListData()
    this.getTypeAlarmListData()
    this.getUptimeCheckTaskList()
    this.getSpecialFocusTaskList()
    this.getUseRatioChartData()
    this.getBusinessAlarmOverviewData()
  },
  mounted() {
    this.interval = window.setInterval(this.getRealTimeAlarmListData, 6000 * 1000)
    this.handleHomeLoadingChange()
  },
  beforeDestroy() {
    window.clearInterval(this.interval)
    window.removeEventListener('resize', this.handleResize)
  },
  methods: {
    handleHomeLoadingChange() {
      this.homeLoading = false
    },
    // getOverviewTitleData() {
    //   overviewInfo().then((data) => {
    //     const ret = []
    //     data.forEach((items, indexs) => {
    //       Array.isArray(items.data) && items.data.length && items.data.forEach((item, index) => {
    //         ret.push({
    //           abnormal: item.data.error,
    //           normal: item.data.total,
    //           type: item.type.trim().toLowerCase(),
    //           last: index === items.data.length - 1 && indexs !== data.length - 1,
    //           extra: item.extra,
    //           pageType: items.type.trim().toLowerCase()
    //         })
    //       })
    //     })
    //     this.overviewList = ret
    //   })
    //     .finally(() => {
    //       this.titleAlarmLoading = false
    //     })
    // },
    getTodayAlarmPieData() {
      this.todayAlarmLoading = true
      alarmCountInfo().then(({ levels: data, unrecovered_count: unrecoveredCount }) => {
        this.todayAlarm = {
          data: data.sort((a, b) => a.count - b.count),
          unrecoveredCount
        }
        this.todayAlarmLoading = false
      })
        .catch(() => {
          this.todayAlarmLoading = false
        })
    },
    getRealTimeAlarmListData() {
      this.realTimeAlarmLoading = true
      listEvent({
        bk_biz_ids: [this.$store.getters.bizId],
        time_range: `${moment().add(-7, 'days')
          .format()} -- ${moment().format()}`,
        page: 1, // 当前页数。固定
        page_size: 6, // 每页的数量，视情况设置
        order: '-id'
      }).then((data) => {
        this.realTimeAlarm = data.event_list.map(item => ({
          id: item.id,
          level: item.level,
          title: item.strategy_name,
          targetKey: item.target_key,
          sourceTime: item.begin_time,
          beginTime: item.display_begin_time,
          isRecovered: item.event_status === 'recovered'
        }))
      })
        .finally(() => {
          this.realTimeAlarmLoading = false
        })
    },
    getTypeAlarmListData(days = 1) {
      this.typeAlarmLoading = true
      alarmRank({ days }).then((data) => {
        this.typeAlarmDays = data.days
        this.typeAlarmListExample = data.using_example_data
        this.typeAlarmList = data.data
      })
        .catch(() => {
          this.typeAlarmListExample = true
        })
        .finally(() => {
          this.typeAlarmLoading = false
        // this.typeAlarmListExample = true
        })
    },
    getUptimeCheckTaskList() {
      listUptimeCheckTask({ status: 'running' }).then((data) => {
        this.availableRate.setList = data.map(item => ({
          id: item.id,
          name: item.name
        }))
      })
    },
    getSpecialFocusTaskList() {
      listApplicationConfig({
        cc_biz_id: this.$store.getters.bizId,
        key: 'specialFocusTaskList'
      }).then((data) => {
        if (Array.isArray(data) && data.length === 0) {
          createApplicationConfig({
            cc_biz_id: this.$store.getters.bizId,
            key: 'specialFocusTaskList',
            value: JSON.stringify([])
          }).then((data) => {
            this.availableRate.specialTaskId = data.id
            this.availableRate.checkedList = []
          })
        } else {
          const value = JSON.parse(data[0].value)
          this.availableRate.checkedList = Array.isArray(value) ? value : [value]
          this.availableRate.specialTaskId = data[0].id
        }
        this.getAvailableRateChartData()
      })
    },
    updateSpecialFocusTaskList(list = []) {
      this.availableAlarmLoading = true
      partialUpdateApplicationConfig(
        this.availableRate.specialTaskId,
        {
          value: Array.isArray(list) ? JSON.stringify(list) : [list]
        }
      ).then((data) => {
        this.availableRate.checkedList = JSON.parse(data.value) || []
        this.getAvailableRateChartData()
      })
    },
    getAvailableRateChartData() {
      frontPageData({
        task_id_list: this.availableRate.checkedList || []
      }, {
        needMessage: false
      }).then((data) => {
        if (data.series) {
          let i = 0
          let j = 0
          this.availableRate.utcoffset = data.utcoffset
          this.errorMsg = ''
          this.availableRate.series = data.series.sort((a, b) => {
            if (a.data && a.data.length && b.data && b.data.length) {
              return a.data[a.data.length - 1][1] - b.data[b.data.length - 1][1]
            }
            return false
          }).map((item) => {
            const data = {
              ...item,
              color: item.is_ok ? normalColorMap[i] : seriousColorMap[j]
            }
            i += 1
            j += 1
            return data
          })
        }
      })
        .catch((e) => {
          this.errorMsg = e.message
          this.availableRate.series = []
        })
        .finally(() => {
          this.availableAlarmLoading = false
        })
    },
    getUseRatioChartData() {
      hostPerformanceDistribution().then((data) => {
        this.useRetioAlarmExample = data.using_example_data
        this.useRatioSeries = data.data || []
      })
        .catch(() => {
          this.useRetioAlarmExample = true
        })
        .finally(() => {
          this.useAlarmLoading = false
        })
    },
    getBusinessAlarmOverviewData() {
      monitorInfo().then((data) => {
        this.businessAlarm = [data.uptimecheck, data.service, data.process, data.os]
      })
        .finally(() => {
          this.businessAlarmLoading = false
        })
    }
  }
}
</script>

<style scoped lang="scss">
@import "common/mixins";

.overview-title {
  height: 60px;
  width: 100%;
}
.overview-content {
  display: flex;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin: -20px -20px 0 0;
  .item,
  %item {
    min-height: 405px;
    background: #fff;
    border-radius: 2px;
    margin: 20px 0 0 0px;
    flex: 1 1 444px;
    position: relative;
    overflow: hidden;
    margin-right: 20px;

    @include border-1px();
    .fake-wrap {
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0);
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      top: 0;
      z-index: 12;
      display: flex;
      justify-content: center;
      align-items: center;

      @include hover(default);
      &-example {
        position: absolute;
        left: -30px;
        bottom: 30px;
        width: 145px;
        height: 24px;
        transform: rotateZ(45deg);
        text-align: center;
        line-height: 24px;
        background: #c4c6cc;
        color: #fff;
        font-size: 16px;
        font-weight: bold;
      }
      &-message {
        text-align: center;
        .example-icon {
          text-align: center;
          margin-bottom: 5px;
          width: 100%;
          color: #979ba5;
          font-size: 28px;
        }
        .example-message {
          height: 19px;
          font-size: 14px;
          color: #63656e;
          line-height: 19px;
        }
      }
    }
    .fake-no-data {
      top: 35px;
      height: calc(100% - 35px);

      @include hover(default);
    }
  }
  .item-pie-char {
    flex: 1 1 355px;

    @extend %item;
  }
  .item-real-time {
    flex: 1 1 355px;

    @extend %item;
  }
  .item-add-view {
    @extend %item;

    @include border-dashed-1px();
  }
  .item-business-chart {
    flex: 1 1 888px;

    @extend %item;
  }
  .item-types-list {
    flex: 1 1 700px;

    @extend %item;
  }
  .item-use-radio {
    flex: 1 1 980px;

    @extend %item;
  }
  .item-available-rate {
    min-height: 365px;
    width: 100%;
    min-width: 990px;

    @extend %item;
  }
}
.home-loading {
  /* stylelint-disable-next-line declaration-no-important */
  position: fixed !important;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}
</style>
