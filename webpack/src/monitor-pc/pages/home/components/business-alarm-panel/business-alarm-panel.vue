<template>
  <section class="business-panel">
    <div class="wall-border" :class="`wall-border-${icon}`"></div>
    <div class="title">
      <span class="title-name">{{title || 'Title'}}</span>
      <span class="title-icon" :class="`title-icon-${icon}`">
        <svg-icon class="svg-icon" :icon-name="iconClass"></svg-icon>
      </span>
    </div>
    <slot></slot>
    <div class="footer" v-if="log">
      <h4 class="footer-title"> {{ $t('操作日志') }} </h4>
      <div class="footer-message">{{log}}</div>
    </div>
  </section>
</template>

<script>
import SvgIcon from '../../../../components/svg-icon/svg-icon'

export default {
  name: 'business-alarm-panel',
  components: {
    SvgIcon
  },
  props: {
    title: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      default: 'normal'
    },
    log: {
      type: String,
      default: ''
    }
  },
  computed: {
    iconClass() {
      if (this.icon === 'serious' || this.icon === 'slight') {
        return 'warning'
      } if (this.icon === 'unset') {
        return 'remind'
      }
      return 'check'
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../../common/mixins";

  .business-panel {
    margin: 35px 0 0 40px;
    background: #fafbfd;
    position: relative;
    .title {
      font-size: 0;
      overflow: hidden;
      padding-bottom: 13px;
      &-name {
        display: inline-block;
        height: 26px;
        font-size: 20px;
        color: #313238;
        line-height: 26px;
      }
      &-icon {
        margin-left: 6px;
        font-size: 20px;
        position: relative;
        top: -1.5px;
      }
      .svg-icon {
        width: 24px;
        height: 24px;
      }
      &-icon-serious {
        color: $seriousIconColor;
      }
      &-icon-slight {
        color: $slightIconColor;
      }
      &-icon-unset {
        color: $unsetIconColor;
      }
      &-icon-normal {
        color: $normalIconColor;
      }

    }
    .footer {
      margin-right: 40px;
      padding-top: 15px;
      border-top: 1px solid #ddd;
      color: $defaultFontColor;
      &-title {
        height: 23px;
        font-size: 14px;
        font-weight: bold;
        line-height: 23px;
        margin: 0 0 5px 0;
      }
      &-message {
        height: 23px;
        font-size: 12px;
        line-height: 23px;
      }
    }
    .wall-border {
      width: 2px;
      height: 51px;
      position: absolute;
      left: -41px;
      top: 5px;
    }
    .wall-border-serious {
      background: $seriousColor;
    }
    .wall-border-slight {
      background: $slightColor;
    }
    .wall-border-unset {
      background: $unsetColor;
    }
    .wall-border-normal {
      background: $normalColor;
    }
  }
</style>
