<template>
  <div class="alarm-info">
    <van-collapse
      class="alarm-info-header"
      :value="header.active"
      @change="handleCollapseChange">
      <van-collapse-item
        v-for="item in header.list"
        :key="item.id"
        class="header-item"
        :title="item.title"
        :is-link="item.id === 'message'"
        :border="item.id !== 'message'"
        :name="item.id">
        <template
          v-if="item.id !== 'message'"
          #value>
          {{ item.value }}
        </template>
        <template v-else-if="item.value">
          <!-- eslint-disable-next-line vue/singleline-html-element-content-newline -->
          <div class="header-item-pre"> {{ item.value }} </div>
        </template>
      </van-collapse-item>
    </van-collapse>
    <div class="list-title">
      {{ `${$t('事件列表')}(${eventList.length})` }}
    </div>
    <van-list class="card-list">
      <div
        v-for="(item, index) in eventList"
        :key="index"
        class="card-list-item"
        @click="handleGotoDetail(item)">
        <div class="card-title">
          <span class="van-ellipsis">{{ item.title }}</span>
          <!-- 已恢复、已关闭 -->
          <span
            v-if="['closed', 'recovered'].includes(item.status.toLocaleLowerCase())"
            :class="`status-${item.status.toLocaleLowerCase()}`">
            {{ `（${statusMap[item.status]}）` }}
          </span>
          <!-- 已确认 -->
          <span
            v-else-if="item.isAck"
            class="status-recovered">
            {{ `（${$t('已确认')}）` }}
          </span>
          <!-- 未恢复已屏蔽 -->
          <span
            v-else-if="item.isShielded && item.shieldType === 'saas_config'"
            class="status-abnormal">
            {{ `（${$t('已屏蔽')}）` }}
          </span>
          <!-- 未恢复已抑制 -->
          <span
            v-else-if="item.isShielded && item.shieldType !== 'saas_config'"
            class="status-abnormal">
            {{ `（${$t('已抑制')}）` }}
          </span>
          <!-- 未恢复 -->
          <span
            v-else
            class="status-abnormal">
            {{ `（${$t('未恢复')}）` }}
          </span>
        </div>
        <div class="card-date">
          {{ item.firstAnomalyTime }}
        </div>
        <div class="card-content">
          <div class="card-content-left">
            <div class="card-line">
              {{ `${$t('策略')}：${item.strategyName}` }}
            </div>
            <div class="card-line">
              {{ `${$t('时长')}：${item.duration}` }}
            </div>
          </div>
          <div
            v-if="item.dataTypeLabel === 'time_series'"
            class="card-content-right" @click.stop>
            <monitor-mobile-echarts
              height="70"
              :options="chartOption"
              :get-series-data="() => handleGetChartData(item)"
              @click="handleGotoTendency(item)"
              class="card-chart">
            </monitor-mobile-echarts>
          </div>
        </div>
        <van-button
          class="card-button"
          plain
          type="info"
          :disabled="item.isShielded"
          @click.stop="!item.isShielded && handleGotoShield(item.id)">
          {{ $t('快捷屏蔽') }}
        </van-button>
      </div>
    </van-list>
    <footer-button
      :disabled="alarmConfirmDisabled"
      @click="handleAlarmCheck">
      {{ alarmConfirmDisabled ? $t('告警已确认') : $t('告警确认') }}
    </footer-button>
    <div class="mask-bottom"></div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Watch, Prop } from 'vue-property-decorator'
import { Collapse, CollapseItem, PullRefresh, List, Cell, Button, Dialog } from 'vant'
import FooterButton from '../../components/footer-button/footer-button.vue'
import AlarmModule from '../../store/modules/alarm-info'
import { IHeader, IEventItem, IStatusMap } from '../../types/alarm-info'
import moment from 'moment'
import { ackEvent } from '../../../monitor-api/modules/mobile_event'
import MonitorMobileEcharts  from '../../../monitor-ui/monitor-echarts/monitor-mobile-echarts.vue'
@Component({
  name: 'AlarmInfo',
  components: {
    [Collapse.name]: Collapse,
    [CollapseItem.name]: CollapseItem,
    [PullRefresh.name]: PullRefresh,
    [List.name]: List,
    [Cell.name]: Cell,
    [Button.name]: Button,
    FooterButton,
    MonitorMobileEcharts
  }
})
export default class AlarmDetail extends Vue {
  public header: IHeader = { list: [], active: [] }
  public loading = false
  public eventList: IEventItem[] = []
  public statusMap: IStatusMap = null
  public alarmStatus = 1
  @Prop() readonly routeKey: string

  get alarmConfirmDisabled() {
    return this.eventList.every(item => item.isAck)
  }
  get chartOption() {
    return {
      color: ['#a0b0cb'],
      legend: {
        show: false
      },
      grid: {
        show: true,
        left: 0,
        top: 2,
        right: 0,
        bottom: 2,
        backgroundColor: '#fafbfd',
        borderColor: '#fafbfd'
      },
      tooltip: {
        show: false
      },
      toolbox: {
        show: false
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    }
  }
  @Watch('routeKey')
  onRouteKeyChange() {
    this.handleGetAlarmInfo()
  }

  created() {
    this.statusMap = {
      ABNORMAL: this.$t('未恢复'),
      SHIELD_ABNORMAL: this.$t('已屏蔽未恢复'),
      CLOSED: this.$t('已关闭'),
      RECOVERED: this.$t('已恢复')
    }
  }

  activated() {
    this.handleGetAlarmInfo()
  }

  async handleGetAlarmInfo() {
    const data = await AlarmModule.getAlarmInfo()
    this.$store.commit('app/SET_APP_DATA', {
      bkBizName: data.bkBizName
    })
    this.header.list = [
      {
        id: 'bkBizName',
        value: data.bkBizName || '--',
        title: this.$t('业务名称')
      },
      {
        id: 'alarmDate',
        value: data.collectTime ? data.collectTime.slice(0, 19) : '',
        title: this.$t('告警时间')
      },
      {
        id: 'message',
        value: data.message,
        title: this.$t('信息摘要')
      }
    ]
    this.eventList = data.events
  }

  async handleGetChartData(item: IEventItem) {
    const data = await AlarmModule.getChartData({
      event_id: item.id,
      start_time: moment().add(-1, 'h')
        .unix(),
      end_time: moment().unix()
    })
    let series = data.filter(item => item?.metric?.['metric_field'] === 'value')
    series = series.length ? series : data
    return { series: (series || [])
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      .map(({ markPoints, thresholds, markTimeRange, ...item }) => ({ ...item, areaStyle: {
        color: '#e8ebf3'
      } })) }
  }

  // 点击展开更多信息摘要
  handleCollapseChange(v: string[]) {
    this.header.active = v.includes('message') ? ['message'] : []
  }

  // 点击告警确认触发
  handleAlarmCheck() {
    const params = { alert_collect_id: this.$store.state.app.collectId }
    Dialog.confirm({
      title: this.$tc('告警确认'),
      message: String(this.$t('告警确认后，异常事件持续未恢复的情况将不会再发起通知；注意！请及时处理故障，以免影响业务正常运行。')),
      beforeClose: (action, done) => {
        if (action === 'confirm') {
          ackEvent(params).then(() => {
            done()
            this.handleGetAlarmInfo()
          })
            .catch(() => done())
        } else {
          done()
        }
      }
    })
  }

  // 跳转至告警详情
  handleGotoDetail({ title, id }) {
    this.$router.push({
      name: 'alarm-detail',
      params: {
        title,
        id
      }
    })
  }

  // 跳转至告警屏蔽
  handleGotoShield(eventId) {
    this.$store.commit('app/SET_EVENT_ID', eventId)
    this.$router.push({
      name: 'quick-alarm-shield',
      params: {
        eventId
      }
    })
  }

  // 跳转至趋势图
  handleGotoTendency({ id }) {
    this.$router.push({
      name: 'tendency-chart',
      params: {
        id
      }
    })
  }
}
</script>
<style lang="scss" scoped>
    @import "../../static/scss/variate.scss";

    $colorList: $deadlyColor $shieldColor $shieldColor $recoverColor;
    $statusList: "abnormal" "shield_abnormal" "closed" "recovered";

    .alarm-info {
      font-size: 14px;
      position: relative;
      &-header {
        box-shadow: 0 1px 0 0 rgba(99, 101, 110, .05);
        /deep/ &.van-hairline {
          &--top-bottom::after {
            border-width: 0;
          }
        }
        .header-item {
          &-pre {
            padding: 0;
            word-break: break-all;
            margin: 0;
            white-space: pre-line;
            font-size: 12px;
            color: #63656e;
            line-height: 20px;
          }
          /deep/ &.van-hairline {
            &--top::after {
              left: -45%;
              right: -45%;
            }
          }
          /deep/ .van-collapse-item__content {
            padding: 10px 16px;
          }
          .content-list {
            display: flex;
            flex-direction: column;
            color: #63656e;
            &-item {
              display: flex;
              line-height: 20px;
              margin-bottom: 4px;
              font-size: 14px;
              .item-label {
                min-width: 42px;
              }
              .item-content {
                flex: 1;
                display: flex;
                flex-wrap: wrap;
                word-break: break-all;
              }
            }
          }
        }
      }
      .list-title {
        height: 46px;
        display: flex;
        align-items: center;
        margin: 0 20px;
        color: #979ba5;
      }
      .card-list {
        display: flex;
        flex-direction: column;
        padding-bottom: 60px;
        &-item {
          background-color: #fff;
          margin: 0 16px 8px 16px;
          border-radius: 4px;
          box-shadow: 0 1px 0 0 rgba(99, 101, 110, .05);
          padding: 15px 20px;
          position: relative;
          .card-title {
            display: flex;
            align-items: center;
            font-size: 16px;
            color: black;
            font-weight: bold;
            margin-bottom: 2px;

            @for $i from 1 through 4 {
              .status-#{nth($statusList, $i)} {
                color: nth($colorList, $i);
                font-size: 12px;
                font-weight: normal;
              }
            }
            .van-ellipsis {
              display: inline-block;
              max-width: 52%;
            }
          }
          .card-date {
            color: #979ba5;
            margin-bottom: 10px;
          }
          .card-content {
            display: flex;
            justify-content: space-between;
            &-left {
              .card-line {
                margin-bottom: 2px;
                color: $defaultFontColor;
              }
            }
            &-right {
              flex: 0;
              flex-basis: 88px;
              position: absolute;
              right: 20px;
              top: 50px;
            }
          }
          .card-button {
            position: absolute;
            right: 20px;
            top: 20px;
            height: 28px;
            line-height: 27px;
          }
        }
      }
      .mask-bottom {
        position: fixed;
        bottom: 0;
        width: 100%;
        height: 15px;
        background: linear-gradient(rgba(255, 255, 255, 0) 0, #fff 100%);
      }
    }
</style>
