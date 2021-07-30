<template>
  <PanelCard class="real-time-alarm" :title="$t('实时告警事件')">
    <a slot="title" class="title-setting" :class="{ 'title-disable': !list.length }" href="javascript:void(0)" @click="gotoPageHandle"> {{ $t('查看更多') }} </a>
    <div class="list">
      <ul>
        <li class="item" v-for="item in list" :key="item.id" @click="item.id && gotoDetailHandle(item.id)">
          <span
            :class="`icon-${item.level}`">{{item.level === 1 ? 'C' : (item.level === 2 ? 'N' : 'S')}}</span>
          <div class="content" :title="item.title">
            <div class="content-content">{{item.targetKey}} {{item.title}}</div>
            <svg-icon icon-name="check" class="checked-icon" v-if="item.isRecovered"></svg-icon>
          </div>
          <span class="end">{{item.beginTime || '--'}}</span>
        </li>
      </ul>
    </div>
  </PanelCard>
</template>

<script>
import PanelCard from '../components/panel-card/panel-card'
import SvgIcon from '../../../components/svg-icon/svg-icon'
import moment from 'moment'
import { gotoPageMixin } from '../../../common/mixins'

moment.locale('zh-cn')

export default {
  name: 'realTime-alarm-list',
  components: {
    PanelCard,
    SvgIcon
  },
  mixins: [gotoPageMixin],
  props: {
    list: {
      type: Array,
      required: true
    }
  },
  methods: {
    getTimeFromNow(t) {
      return moment(t).fromNow()
    },
    gotoPageHandle() {
      this.$router.push({
        name: 'event-center',
        params: {
          beginTime: moment().add(-7, 'days')
            .format('YYYY-MM-DD HH:mm:ss'),
          endTime: moment().format('YYYY-MM-DD HH:mm:ss')
        }
      })
    },
    gotoDetailHandle(id) {
      this.$router.push({
        name: 'event-center-detail',
        params: {
          id
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../common/mixins";

  .real-time-alarm {
    .title-setting {
      float: right;
      height: 19px;
      font-size: $fontSmSize;
      color: #3a84ff;
      line-height: 19px;
    }
    .title-disable {
      color: #979ba5;
      cursor: not-allowed;
    }
    .list {
      ul {
        padding: 0;
        .item {
          padding: 15px 0;
          border-bottom: 1px solid #f0f1f5;
          list-style: none;
          display: flex;
          justify-content: flex-start;
          align-items: center;
          &:hover {
            background: #fafbfd;
            cursor: pointer;
          }
          .icon,
          %icon {
            width: 24px;
            height: 24px;
            border-radius: 100%;
            text-align: center;
            line-height: 24px;
            font-weight: 900;
            flex: 0 0 24px;
          }
          .icon-1 {
            background: #fdd;
            color: $deadlyAlarmColor;

            @extend %icon;
          }
          .icon-3 {
            background: #ffe8c3;
            color: $warningAlarmColor;

            @extend %icon;
          }
          .icon-2 {
            background: #fff9de;
            color: $remindAlarmColor;

            @extend %icon;
          }
          .content {
            flex: 1;
            height: 19px;
            font-size: $fontSmSize;
            color: $defaultFontColor;
            line-height: 19px;
            margin: 0 10px;
            overflow: hidden;
            &-content {
              max-width: 100%;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              &:hover {
                color: $normalFontColor;
              }
            }
            .checked-icon {
              color: #85cfb7;
              font-size: 18px;
            }
          }
          .end {
            height: 19px;
            font-size: $fontSmSize;
            color: #979ba5;
            line-height: 19px;
            min-width: 50px;
          }
          &:last-child {
            border-bottom: 0;
            padding-bottom: 10px;
          }
        }
      }
    }
  }
</style>
