<!--
 * @Author:
 * @Date: 2021-05-25 19:15:01
 * @LastEditTime: 2021-06-18 10:50:19
 * @LastEditors:
 * @Description:
-->
<template>
  <!-- 分类面板 -->
  <div class="performance-overview">
    <div class="performance-overview-panel"
         v-for="item in panel.list"
         :class="{ 'panel-active': panel.active === item.key, disabled: loading }"
         :key="item.key"
         v-bk-tooltips="{
           content: $t('数据正在加载'),
           disabled: !loading,
           delay: 500
         }"
         @click="!loading && handlePanelClick(item.key)">
      <span class="panel-icon icon-monitor" :class="item.icon"></span>
      <div class="panel-desc">
        <div class="panel-desc-num">{{ item.num || 0 }}</div>
        <div class="panel-desc-name">{{ item.name }}</div>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit, Prop, Watch } from 'vue-property-decorator'
import { IPanelStatistics, IPanel } from '../performance-type'

@Component({ name: 'overview-panel' })
export default class OverviewPanel extends Vue {
  @Prop({ default: '' }) private readonly active!: string
  @Prop({ default: () => ({}) }) private readonly panelStatistics!: IPanelStatistics
  @Prop({ default: false, type: Boolean }) private readonly loading!: boolean

  private panel: IPanel = {
    list: [
      {
        icon: 'icon-gaojing',
        name: window.i18n.t('告警未恢复'),
        key: 'unresolveData',
        num: 0
      },
      {
        icon: 'icon-CPU',
        name: `${window.i18n.t('CPU使用率超')}80%`,
        key: 'cpuData',
        num: 0
      },
      {
        icon: 'icon-neicun',
        name: `${window.i18n.t('应用内存使用率超')}80%`,
        key: 'menmoryData',
        num: 0
      },
      {
        icon: 'icon-cipan',
        name: `${window.i18n.t('磁盘空间使用率')}80%`,
        key: 'diskData',
        num: 0
      }
    ],
    active: this.active
  }
  created() {
    this.panel.list.forEach(item => item.num = this.panelStatistics[item.key])
  }

  @Watch('active')
  private handleActiveChange(v) {
    this.panel.active = v
  }

  @Watch('panelStatistics')
  private handlePanelStatisticsChange(statistics: IPanelStatistics) {
    this.panel.list.forEach((item) => {
      item.num = statistics[item.key]
    })
  }

  @Emit('click')
  private handlePanelClick(key: string) {
    this.panel.active = this.panel.active === key ? '' : key
    return this.panel.active
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.performance-overview {
  display: flex;
  flex-direction: row;
  height: 76px;
  &-panel {
    flex: 1 1 315px;
    min-width: 200px;
    padding-left: 45px;
    height: 100%;
    border: 1px solid #dcdee5;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    position: relative;

    @include hover();
    &.disabled {
      cursor: not-allowed
    }
    &:not(:nth-child(1)) {
      border-left: 0;
    }
    .panel-icon {
      font-size: 32px;
      color: #c4c6cc;
    }
    .panel-desc {
      margin: 0 15px;
      &-num {
        font-size: 16px;
        font-weight: 600;
        color: #000;
        line-height: 22px;
      }
      &-name {
        font-size: 12px;
        color: #979ba5;
        line-height: 16px;
      }
    }
    &.panel-active {
      .panel-icon {
        color: $primaryFontColor;
      }
      &::after {
        content: "";
        left: 0;
        right: 0;
        bottom: -1px;
        position: absolute;
        height: 2px;
        background: $primaryFontColor;
      }
    }
  }
}
</style>
