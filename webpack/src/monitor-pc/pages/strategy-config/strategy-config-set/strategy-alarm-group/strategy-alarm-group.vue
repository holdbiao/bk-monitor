<template>
  <div class="strategy-alarm-group">
    <bk-tag-input
      :placeholder="$t('请选择告警组')"
      :list="alarmGroupList"
      save-key="id"
      trigger="focus"
      display-key="name"
      search-key="name"
      :tpl="renderAlarmGroupList"
      :tag-tpl="renderAlarmGroupTag">
    </bk-tag-input>
  </div>
</template>
<script lang="tsx">
import { Vue, Prop, Component } from 'vue-property-decorator'
// eslint-disable-next-line no-unused-vars
import MonitorVue from '../../../../types'
@Component({
  name: 'StrategyAlarmGroup'
})
export default class StrategyAlarmGroup extends Vue<MonitorVue> {
  @Prop(Array)
  // 告警组列表
  alarmGroupList: Array<any>

  // tag渲览函数
  renderAlarmGroupTag(node: any): Vue.VNode {
    return this.$createElement('div', {
      class: {
        tag: true
      }
    }, node.name)
  }

  renderAlarmGroupList(node, ctx, highlightKeyword) {
    return this.$createElement('div', {
      class: {
        'bk-selector-node': true,
        'bk-selector-member': true
      }
    }, [
      this.$createElement('span', {
        class: {
          text: true
        },
        domProps: {
          domPropsInnerHTML: `${highlightKeyword(node.name)}`
        }
      }, `${highlightKeyword(node.name)}`)
    ])
  }
}
</script>
<style lang="scss" scoped>
    .tag-list {
      > li {
        height: 22px;
      }
    }
    .strategy-alarm-group {
      width: 100%;
      /deep/ .key-node {
        /* stylelint-disable-next-line declaration-no-important */
        border: 0 !important;

        /* stylelint-disable-next-line declaration-no-important */
        background: none !important;
      }
      .tag {
        background: #f0f1f5;
        border-radius: 2px;
        height: 22px;
        line-height: 16px;
        text-align: center;
        padding: 4px 10px;
      }
    }
    .bk-selector-list {
      .bk-selector-member {
        padding: 0 10px;
        display: flex;
        align-items: center;
      }
    }
</style>
