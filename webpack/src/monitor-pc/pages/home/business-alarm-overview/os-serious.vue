<template>
  <section class="mainframe-serious">
    <div class="mainframe-serious-title"> {{ $t('共产生') }} <span class="serious-title">{{alarm.high_risk.length}} {{ $t('个高危告警') }} </span> {{ this.$t('和') }} <span class="slight-title">{{alarm.other.length}} {{ $t('个其他告警') }} </span>
      <a v-if="alarm.has_more" href="javascript:void(0)" class="check-more" @click="gotoEventCenter"> {{ $t('查看更多') }} </a>
    </div>
    <ul class="mainframe-serious-list">
      <li class="item" v-for="item in list" :key="item.id">
        <svg-icon :icon-name="`${item.type === 'serious' ? 'warning' : 'hint'}`" :class="`item-icon item-icon-${item.type}`"></svg-icon>
        <span @click="gotoDetailHandle(item.title.event_id)">{{item.title.content}}</span>
      </li>
    </ul>
  </section>
</template>

<script>
import SvgIcon from '../../../components/svg-icon/svg-icon'
import { gotoPageMixin } from '../../../common/mixins'
import moment from 'moment'
export default {
  name: 'os-serious',
  components: {
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
  computed: {
    list() {
      return this.alarm.high_risk.map(item => ({
        title: item,
        type: 'serious'
      })).concat(this.alarm.other.map(item => ({
        title: item,
        type: 'default'
      })))
    }
  },
  methods: {
    gotoEventCenter() {
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

  .mainframe-serious {
    &-title {
      min-width: 450px;
      font-size: $fontSmSize;
      color: $defaultFontColor;
      padding-bottom: 8px;
      border-bottom: 1px solid $defaultBorderColor;
      margin-right: 40px;
    }
    .check-more {
      float: right;
      font-size: 14px;
      color: #3a84ff;
    }
    .serious-title {
      font-weight: bold;
    }
    .slight-title {
      font-weight: bold;
    }
    &-list {
      padding: 0 20px 0 0;
      max-height: 280px;
      overflow: auto;
      .item {
        margin: 15px 0;
        font-size: 12px;
        color: $defaultFontColor;
        &:hover {
          cursor: pointer;
          color: #3a84ff;
        }
        &-icon {
          margin-right: 6px;
          margin-bottom: 1px;
          width: 16px;
          height: 16px;
        }
        &-icon-serious {
          color: $deadlyAlarmColor;
        }
        &-icon-normal {
          color: $warningAlarmColor;
        }
        &-icon-unset,
        &-icon-default {
          color: $remindAlarmColor;
        }
      }
    }
  }
</style>
