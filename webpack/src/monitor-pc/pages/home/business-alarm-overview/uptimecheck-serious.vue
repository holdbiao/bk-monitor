<template>
  <section class="serious-content">
    <div class="serious-content-tab">
      <div class="tab-wrap">
        <span class="tab" :class="{ active: tabIndex === 0 }"
              @click="tabIndex = 0"><span class="tab-name"> {{ $t('拨测任务') }} </span><span
                class="tab-num">{{taskNum}}</span></span>
        <span class="tab" :class="{ active: tabIndex === 1 }"
              @click="tabIndex = 1"><span class="tab-name"> {{ $t('拨测节点') }} </span><span
                class="tab-num">{{nodeNum}}</span></span>
      </div>
    </div>
    <div class="serious-content-wrap" v-show="tabIndex === 0">
      <div class="serious-content-wrap-container" v-if="alarm.task && alarm.task.abnormal_events.length">
        <div class="chart-item" v-for="item in alarm.task.abnormal_events"
             :key="item.task_id">
          <business-alarm-card :title="item.title" :id="item.event_id" :level="1" :alarm="item">
          </business-alarm-card>
        </div>
      </div>
      <div class="no-alarm" v-else> {{ $t('拨测任务很健康，无告警事件产生!') }} </div>
    </div>
    <div class="serious-content-wrap" v-show="tabIndex === 1">
      <div class="serious-content-wrap-container" v-if="alarm.node && alarm.node.abnormal_nodes.length">
        <ul class="list">
          <li class="item" v-for="item in alarm.node.abnormal_nodes" :key="item.id" @click="nodeAlarmClickHandle">
            <svg-icon icon-name="warning" class="item-icon item-icon-serious"></svg-icon>
            <span>{{item.isp ? `${item.isp}-` : ''}}{{item.name}} {{ $t('节点出现异常，请及时排查！') }} </span>
          </li>
        </ul>
      </div>
      <div class="no-alarm" v-else> {{ $t('拨测节点很健康，无告警事件产生!') }} </div>
    </div>
  </section>
</template>

<script>
import BusinessAlarmCard from '../components/business-alarm-card/business-alarm-card'
import SvgIcon from '../../../components/svg-icon/svg-icon'
import { gotoPageMixin } from '../../../common/mixins'
export default {
  name: 'uptimecheck-serious',
  components: {
    BusinessAlarmCard,
    SvgIcon
  },
  mixins: [gotoPageMixin],
  props: {
    alarm: {
      type: Object,
      default() {
        return {}
      }
    }
  },
  data() {
    return {
      tabIndex: 0
    }
  },
  computed: {
    taskNum() {
      const { alarm } = this
      if (alarm.task && alarm.task.abnormal_events) {
        return (alarm.task.abnormal_events.length > 99 ? '99+' : alarm.task.abnormal_events.length)
      }
      return 0
    },
    nodeNum() {
      const { alarm } = this
      if (alarm.node && alarm.node.abnormal_nodes.length) {
        return (alarm.node.abnormal_nodes.length > 99 ? '99+' : alarm.node.abnormal_nodes.length)
      }
      return 0
    }
  },
  methods: {
    nodeAlarmClickHandle() {
      this.$router.push({ name: 'uptime-check',
        params: {
          id: 'uptime-check-node'
        } })
      // this.commonGotoPage('uptime_check/nodes/')
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../common/mixins";

  .serious-content {
    &-tab {
      font-size: 0;
      margin-bottom: 10px;
      .tab-wrap {
        margin-right: 40px;
        border-bottom: 1px solid $defaultBorderColor;
        .tab {
          display: inline-block;
          font-size: $fontSmSize;
          color: $defaultFontColor;
          padding-bottom: 7px;
          margin-bottom: -1px;
          &:nth-child(1) {
            margin-right: 20px;
          }
          &:hover {
            cursor: pointer;
          }
          &-name {
            vertical-align: middle;
          }
          &-num {
            display: inline-block;
            min-width: 16px;
            padding: 0 5px;
            height: 16px;
            background: #c4c6cc;
            color: #fff;
            opacity: 1;
            border-radius: 8px;
            text-align: center;
            line-height: 16px;
            margin-left: 6px;
            font-size: 12px;
          }

        }
        .active {
          color: #3a84ff;
          border-bottom: 2px solid #3a84ff;
          .tab-num {
            background: #3a84ff;
          }
        }
      }
    }
    &-wrap {
      text-align: center;
      &-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        flex-wrap: wrap;
        min-width: 460px;
        max-height: 260px;
        overflow: auto;

        @media only screen and (min-width: 1414px) {
          .chart-item:nth-child(2n+1) {
            margin-right: 30px;
          }
        }
        @media only screen and (max-width: 1434px) {
          .chart-item {
            margin-right: 30px;
          }
        }
        .list {
          padding: 0;
          max-height: 280px;
          overflow: auto;
          .item {
            display: flex;
            text-align: center;
            margin: 5px 0;
            font-size: 12px;
            color: $defaultFontColor;
            &:hover {
              cursor: pointer;
              color: #3a84ff;
            }
            &-icon {
              margin-right: 6px;
              width: 16px;
              height: 16px;
            }
            &-icon-serious {
              color: $deadlyAlarmColor;
            }
            &-icon-slight {
              color: $warningAlarmColor;
            }
            &-icon-unset,
            &-icon-default {
              color: $remindAlarmColor;
            }
          }
        }
      }
      .no-alarm {
        margin: 5px 0;
        font-size: 12px;
        color: $defaultFontColor;
        text-align: left;
      }
    }
  }
</style>
