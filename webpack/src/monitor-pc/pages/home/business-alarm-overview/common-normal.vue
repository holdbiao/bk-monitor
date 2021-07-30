<template>
  <section class="common-normal">
    <div class="title">
      {{normal.title}}
    </div>
    <div class="content">
      <div v-if="alarm.name === 'uptimecheck'">
        <div class="content-item" v-for="item in alarm.notice_task" :key="item.task_id">
          <a class="guide" @click="gotoUpcheckTimePage('task', item.task_id)"> {{ $t('立即查看') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content">
            {{item.task_name}} {{ $t('当前服务可用率') }} <span
              class="item-warning">{{item.available}}</span>，{{ $t('建议您关注') }} </div>
        </div>
        <div class="content-item" v-for="item in alarm.warning_task" :key="item.task_id">
          <a class="guide" @click="gotoUpcheckTimePage('task', item.task_id)"> {{ $t('立即查看') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content">
            {{item.task_name}} {{ $t('当前可用率仅') }} <span
              class="item-warning">{{item.available}}</span>，{{ $t('服务质量较差，请及时处理') }} </div>
        </div>
        <div class="content-item" v-if="alarm.single_supplier">
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('检测到当前仅配置了1个运营商节点，为了更全面的反应不同网络环境用户的访问质量，建议您接入更多其他类型的网络运营商节点，覆盖更全面。') }} <a class="into" @click="gotoUpcheckTimePage('node')"> {{ $t('立即接入') }} </a> {{ $t('（点击跳转到拨测节点页面）') }} </div>
        </div>
      </div>
      <div v-else-if="alarm.name === 'service'">
        <div class="content-item" v-if="alarm.should_config_strategy">
          <a class="guide" @click="gotoStrategy"> {{ $t('前往添加') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('检测到告警策略 未配置监控目标，创建好策略后别忘了添加目标才可生效喔。自研的中间件也能接入蓝鲸监控吗？') }} </div>
        </div>
        <div class="content-item">
          <a class="guide" @click="handleGotoLink('scriptCollect')"> {{ $t('马上了解') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('如何使用脚本进行服务监控？') }} </div>
        </div>
        <div class="content-item">
          <a class="guide" @click="handleGotoLink('multiInstanceMonitor')"> {{ $t('马上了解') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('如何实现多实例采集？') }} </div>
        </div>
        <div class="content-item">
          <a class="guide" @click="handleGotoLink('componentMonitor')"> {{ $t('马上了解') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('如何对开源组件进行监控？') }} </div>
        </div>
      </div>
      <div v-else-if="alarm.name === 'process'">
        <div class="content-item">
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('未发现有异常运行的进程。') }} </div>
        </div>
        <div class="content-item" v-if="!alarm.has_monitor">
          <a class="guide" @click="gotoStrategy"> {{ $t('立即配置') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('检测到未配置进程/端口监控策略，请尽快配置方能及时的发现风险/故障。') }} </div>
        </div>
      </div>
      <div v-else-if="alarm.name === 'host'">
        <div class="content-item">
          <a class="guide"> {{ $t('快速设置') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('检测到你对“CPU使用率、应用内容使用量、磁盘利用率”未做全局告警策略配置') }} </div>
        </div>
        <div class="content-item">
          <a class="guide"> {{ $t('快速设置') }} </a>
          <svg-icon class="item-icon" icon-name="hint"></svg-icon>
          <div class="item-content"> {{ $t('检测到你的多个主机监控指标未配置告警策略') }} </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import SvgIcon from '../../../components/svg-icon/svg-icon'
import { gotoPageMixin } from '../../../common/mixins'
import documentLinkMixin from '../../../mixins/documentLinkMixin'

export default {
  name: 'common-normal',
  components: {
    SvgIcon
  },
  mixins: [gotoPageMixin, documentLinkMixin],
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
      commonMap: {
        uptimecheck: {
          title: this.$t('当前拨测任务状态良好，无告警事件产生')
        },
        service: {
          title: this.$t('当前被监控的服务运行正常，无告警产生')
        },
        process: {
          title: this.$t('当前进程状态正常，无告警产生')
        },
        os: {
          title: this.$t('当前主机状态正常，无告警事件产生')
        }
      }
    }
  },
  computed: {
    normal() {
      return this.commonMap[this.alarm.name]
    }
  },
  methods: {
    gotoUpcheckTimePage(type, taskId) {
      if (type === 'node') {
        this.$router.push({ name: 'uptime-check',
          params: {
            id: 'uptime-check-node'
          } })
      } else {
        this.$router.push({ name: 'uptime-check-task-detail', params: { taskId }, replace: true })
      }
    },
    gotoStrategy() {
      this.$router.push({ name: 'strategy-config-add' })
    },
    gotoCustomPage() {
      localStorage.setItem('configListIndex', 1)
      this.commonGotoPage('config')
    },
    gotoComponentPage(name) {
      if (name) {
        this.commonGotoPage(`component/?type=${name}`)
      } else {
        this.commonGotoPage('config')
      }
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../common/mixins";

  @mixin content-dec {
    color: #3a84ff;
    &:hover {
      cursor: pointer;
    }
  }

  .common-normal {
    padding-right: 40px;
    .title {
      min-width: 450px;
      font-size: 12px;
      color: $defaultFontColor;
      line-height: 19px;
      padding-bottom: 17px;
      border-bottom: 1px solid $defaultBorderColor;
      &-guide {
        @include content-dec();
      }
    }
    .content {
      padding: 13px 0;
      > div {
        max-height: 260px;
        overflow: auto;
      }
      &-item {
        font-size: 12px;
        color: $defaultFontColor;
        overflow: hidden;
        margin: 10px 0;
        .item-icon {
          color: #979ba5;
          float: left;
          margin-top: 1px;
          font-size: $fontNormalSize;
        }
        .item-content {
          margin-left: 25px;
          min-width: 340px;
          margin-right: 60px;
          .into {
            color: #3a84ff;
            cursor: pointer;
          }
        }
        .guide {
          float: right;

          @include content-dec();
        }
        .item-warning {
          color: #ff9c01;
        }
      }
    }
  }
</style>
