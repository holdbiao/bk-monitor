<template>
  <section class="mainframe-serious">
    <div class="mainframe-serious-title"> {{ $t('共产生') }} <span class="serious-title">{{alarm.warning_count}} {{ $t('个高危告警') }} </span>
      <a v-if="alarm.has_more" href="javascript:void(0)" class="check-more" @click="gotoEventCenter"> {{ $t('查看更多') }} </a>
    </div>
    <ul class="mainframe-serious-list">
      <li class="item" v-for="item in alarm.abnormal_events" :key="item.event_id">
        <svg-icon :icon-name="`${item.type === 'serious' ? 'warning' : 'hint'}`" :class="`item-icon item-icon-${item.type}`"></svg-icon>
        <span @click="gotoDetailHandle(item.event_id)">{{item.content}}</span>
      </li>
    </ul>
  </section>
</template>

<script>
import moment from 'moment'
import SvgIcon from '../../../components/svg-icon/svg-icon'
import { gotoPageMixin } from '../../../common/mixins'
export default {
  name: 'ProcessSerious',
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
  methods: {
    gotoDetailHandle(id) {
      this.$router.push({
        name: 'event-center-detail',
        params: {
          id
        }
      })
    },
    gotoEventCenter() {
      this.$router.push({
        name: 'event-center',
        params: {
          beginTime: moment().add(-7, 'days')
            .format('YYYY-MM-DD HH:mm:ss'),
          endTime: moment().format('YYYY-MM-DD HH:mm:ss')
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
