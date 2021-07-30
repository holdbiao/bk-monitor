<template>
  <div class="alarm-shield-detail" v-bkloading="{ isLoading: loading }">
    <div v-if="detailData.category === 'scope'" class="title"> {{ $t('基于范围进行屏蔽') }} </div>
    <div v-else-if="detailData.category === 'strategy'" class="title"> {{ $t('基于策略进行屏蔽') }} </div>
    <div v-else-if="detailData.category === 'event'" class="title"> {{ $t('基于告警事件进行屏蔽') }} </div>
    <div class="scope-item">
      <div class="item-label">{{$t('所属')}}</div>
      <div class="item-content">{{ bizName }}</div>
    </div>
    <div class="scope-item">
      <div class="item-label">{{$t('屏蔽状态')}}</div>
      <div class="item-content"><span :style="{ color: statusColorMap[detailData.status] }">{{ statusMap[detailData.status] }}</span></div>
    </div>
    <!-- 屏蔽对象的详情展示 -->
    <component v-if="!loading" :is="componentId" :dimension="detailData.dimensionConfig"></component>
    <!-- 时间范围 -->
    <div class="scope-item">
      <div class="item-label">{{$t('屏蔽周期')}}</div>
      <div class="item-content">{{ cycleMap[cycleConfig.type] }}</div>
    </div>
    <div class="scope-item">
      <div class="item-label">{{$t('时间范围')}}</div>
      <div v-if="cycleConfig.type === 1" class="item-data">{{ detailData.beginTime }} ~ {{ detailData.endTime }}</div>
      <div v-else-if="cycleConfig.type === 2" class="item-data">{{$t('每天的')}}&nbsp;<span class="item-highlight">{{ cycleConfig.startTime }} ~ {{ cycleConfig.endTime }}</span>&nbsp;{{$t('进行告警屏蔽')}}</div>
      <div v-else-if="cycleConfig.type === 3" class="item-data">{{$t('每周')}}&nbsp;<span class="item-highlight">{{ cycleConfig.weekList }}</span>&nbsp;{{$t('的')}}&nbsp;<span class="item-highlight">{{ cycleConfig.startTime }} ~ {{ cycleConfig.endTime }}</span>&nbsp;{{$t('进行告警屏蔽')}}</div>
      <div v-else-if="cycleConfig.type === 4" class="item-data">{{$t('每月')}}&nbsp;<span class="item-highlight">{{ cycleConfig.dayList }}</span>&nbsp;{{$t('日的')}}&nbsp;<span class="item-highlight">{{ cycleConfig.startTime }} ~ {{ cycleConfig.endTime }}</span>&nbsp;{{$t('进行告警屏蔽')}}</div>
    </div>
    <div v-if="cycleConfig.type !== 1" class="scope-item">
      <div class="item-label">{{$t('日期范围')}}</div>
      <div class="item-content">{{ detailData.beginTime }} ~ {{ detailData.endTime }}</div>
    </div>
    <!-- 屏蔽原因 -->
    <div class="scope-item">
      <div class="item-label">{{$t('屏蔽原因')}}</div>
      <div class="item-content"><pre style="margin: 0; white-space: pre-wrap;">{{ detailData.description || '--' }}</pre></div>
    </div>
    <!-- 通知方式 -->
    <div v-if="detailData.shieldNotice">
      <div class="scope-item" style="margin-bottom: 10px">
        <div class="item-label item-img">{{$t('通知对象')}}</div>
        <div class="item-content">
          <div class="personnel-choice" v-for="(item, index) in noticeConfig.receiver" :key="index">
            <img v-if="item.logo" :src="item.logo">
            <i v-else-if="!item.logo && item.type === 'group'" class="icon-monitor icon-mc-user-group no-img"></i>
            <i v-else-if="!item.logo && item.type === 'user'" class="icon-monitor icon-mc-user-one no-img"></i>
            <span>{{ item.displayName }}</span>
          </div>
        </div>
      </div>
      <div class="scope-item">
        <div class="item-label">{{$t('通知方式')}}</div>
        <div class="item-content">{{ noticeConfig.way }}；</div>
      </div>
      <div class="scope-item">
        <div class="item-label">{{$t('通知时间')}}</div>
        <div class="item-data">{{$t('屏蔽开始/结束前')}}<span class="item-highlight">&nbsp;{{ noticeConfig.time }}&nbsp;</span>{{$t('分钟发送通知')}}</div>
      </div>
    </div>
  </div>
</template>

<script>
import AlarmShieldDetailScope from './alarm-shield-detail-scope.vue'
import AlarmShieldDetailEvent from './alarm-shield-detail-event.vue'
import AlarmShieldDetailStrategy from './alarm-shield-detail-strategy.vue'
import { getNoticeWay } from '../../../../monitor-api/modules/notice_group'
import { mapMutations, mapActions } from 'vuex'

export default {
  name: 'alarm-shield-detail',
  components: {
    AlarmShieldDetailScope,
    AlarmShieldDetailEvent,
    AlarmShieldDetailStrategy
  },
  props: {
    id: [Number, String]
  },
  data() {
    return {
      loading: false,
      bizName: '',
      detailData: {}, // 屏蔽详情数据
      title: '',
      typeMap: [
        {
          type: 'scope',
          title: this.$t('基于范围进行屏蔽'),
          componentId: 'AlarmShieldDetailScope'
        },
        {
          type: 'strategy',
          title: this.$t('基于策略进行屏蔽'),
          componentId: 'AlarmShieldDetailStrategy'
        },
        {
          type: 'event',
          title: this.$t('基于告警事件进行屏蔽'),
          componentId: 'AlarmShieldDetailEvent'
        }
      ],
      componentId: 'AlarmShieldDetailScope',
      statusMap: ['', this.$t('屏蔽中'), this.$t('已过期'), this.$t('被解除')],
      statusColorMap: {
        [this.$t('屏蔽中')]: '#63656E',
        [this.$t('被解除')]: '#FF9C01',
        [this.$t('已过期')]: '#C4C6CC'
      },
      // 时间，日期数据
      cycleConfig: {},
      cycleMap: ['', this.$t('单次'), this.$t('每天'), this.$t('每周'), this.$t('每月')],
      weekListMap: ['', this.$t('星期一'), this.$t('星期二'), this.$t('星期三'),
        this.$t('星期四'), this.$t('星期五'), this.$t('星期六'), this.$t('星期日')],
      // 事件中心跳转过来
      fromEvent: false,
      strategyStatusMap: {
        UPDATED: this.$t('（配置已被修改）'),
        DELETED: this.$t('（配置已被删除）'),
        UNCHANGED: ''
      },
      // 通知方式数据
      noticeConfig: {}
    }
  },
  watch: {
    id(newId, oldId) {
      if (`${newId}` !== `${oldId}`) {
        this.getDetailData(newId)
      }
    }
  },
  beforeRouteEnter(to, from, next) {
    const { name } = from
    next((vm) => {
      vm.fromEvent = name === 'event-center-detail'
    })
  },
  mounted() {
    const { params } = this.$route
    this.$nextTick(() => {
      this.getDetailData(params.id, params.eventId)
    })
  },
  methods: {
    ...mapMutations('app', ['SET_NAV_TITLE']),
    ...mapActions('shield', ['frontendShieldDetail']),
    ...mapActions('alert-events', ['shieldSnapshot']),
    async getNoticeWay() {
      let noticeWay = []
      await getNoticeWay({ bk_biz_id: this.bizId }).then((data) => {
        noticeWay = data
      })
      return noticeWay
    },
    // 获取屏蔽详情数据
    async getDetailData(id, eventId) {
      this.loading = true
      let data = {}
      this.SET_NAV_TITLE('加载中...')
      if (this.fromEvent) {
        this.SET_NAV_TITLE(this.$t('加载中...'))
        data = await this.shieldSnapshot({
          shield_snapshot_id: id,
          id: eventId
        })
        const statusText = this.strategyStatusMap[data.shield_status]
        this.SET_NAV_TITLE(statusText ? `#${data.id}${statusText}` : `#${data.id}`)
      } else {
        data = await this.frontendShieldDetail({ id }).catch(() => {
          this.$bkMessage({ theme: 'error', message: this.$t('屏蔽详情获取失败') })
          this.loading = false
        })
        this.SET_NAV_TITLE(`#${id}`)
      }
      this.detailData = data
      this.handleDetailData(data)
    },
    // 处理屏蔽详情数据
    async handleDetailData(data) {
      // 筛选出所属业务
      const bizItem = this.$store.getters.bizList.filter(item => data.bkBizId === item.id)
      this.bizName = bizItem[0].text
      // type处理
      const { title, componentId } = this.typeMap.find(item => item.type === data.category)
      this.title = title
      this.componentId = componentId
      // 时间，日期处理
      const weekList = data.cycleConfig.weekList.map(item => this.weekListMap[item])
      this.cycleConfig = {
        type: data.cycleConfig.type,
        startTime: data.cycleConfig.beginTime,
        endTime: data.cycleConfig.endTime,
        dayList: data.cycleConfig.dayList.join('、'),
        weekList: weekList.join('、')
      }
      // 通知方式处理 shieldNotice: 是否开启通知方式
      if (data.shieldNotice) {
        const { noticeConfig } = data
        const noticeWay = await this.getNoticeWay()
        const way = noticeConfig.noticeWay.map((item) => {
          const res = noticeWay.find(el => el.type === item)
          return res.label
        })
        this.noticeConfig = {
          receiver: noticeConfig.noticeReceiver,
          way: way.join('；'),
          time: noticeConfig.noticeTime
        }
      }
      this.loading = false
    }
  }
}
</script>

<style lang="scss" scoped>
    .alarm-shield-detail {
      width: 100%;
      min-height: calc(100vh - 80px);
      border: 1px solid #dcdee5;
      border-radius: 2px;
      padding: 18px 94px 18px 30px;
      background: #fff;
      font-size: 14px;
      color: #63656e;
      .title {
        font-size: 14px;
        font-weight: bold;
        color: #313238;
        margin-bottom: 23px;
      }
      .scope-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        .item-label {
          min-width: 90px;
          color: #979ba5;
          text-align: right;
          margin-right: 24px;
        }
        .item-img {
          margin-top: 4px;
        }
        .item-data {
          min-height: 19px;
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          .item-highlight {
            color: #3a84ff;
            font-weight: bold;
          }
        }
        .item-content {
          min-height: 19px;
          display: flex;
          align-items: flex-end;
          flex-wrap: wrap;
          word-break: break-all;
          .personnel-choice {
            display: flex;
            align-items: center;
            margin: 0 21px 10px 0;
            img {
              width: 24px;
              height: 24px;
              border-radius: 16px;
              margin-right: 5px;
            }
            .no-img {
              color: #c4c6cc;
              font-size: 24px;
              background: #fafbfd;
              border-radius: 16px;
              margin-right: 5px;
            }
          }
        }
      }
    }
</style>
