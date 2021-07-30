<template>
  <div class="uptime-check">
    <div class="uptime-check-tab">
      <div
        v-for="item in tabList"
        class="tab-item"
        :class="{ 'tab-active': active === item.id }"
        :key="item.id"
        @click="handleTabChange(item.id)">
        {{ item.name }}
      </div>
      <div class="uptime-check-content">
        <page-tips
          style="margin-bottom: 16px"
          :tips-text="$t('服务拨测通过拨测节点向远程目标发送探测信息，来发现目标服务的状态情况。支持TCP HTTP(s) UDP ICMP。该功能依赖服务器安装bkmonitorbeat采集器。')"
          :link-text="$t('采集器安装前往节点管理')"
          :link-url="`${this.$store.getters.bkNodemanHost}#/plugin-manager/list`"
          doc-link="quickStartDial">
        </page-tips>
        <keep-alive v-if="active">
          <component
            :is="active"
            :from-route-name="fromRoueName"
            :node-name="nodeName"
            @node-name-change="nodeName = ''"
            @set-task="handleSetNodeName">
          </component>
        </keep-alive>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Prop, Mixins, Provide } from 'vue-property-decorator'
import UptimeCheckTask from './uptime-check-task/uptime-check-task.vue'
import UptimeCheckNode from './uptime-check-nodes/uptime-check-nodes.vue'
import { TranslateResult } from 'vue-i18n'
import authorityMixinCreate from '../../mixins/authorityMixin'
import pageTips from '../../components/pageTips/pageTips.vue'
import * as uptimeAuth from './authority-map'
enum UptimeCheckType {
  task = 'uptime-check-task',
  node = 'uptime-check-node'
}
interface ITabItem {
  id: UptimeCheckType;
  name: TranslateResult;
}
Component.registerHooks([
  'beforeRouteEnter',
  'beforeRouteLeave'
])
@Component({
  name: 'uptime-check',
  components: {
    UptimeCheckTask,
    UptimeCheckNode,
    pageTips
  }
})
export default class UptimeCheck extends Mixins(authorityMixinCreate(uptimeAuth)) {
  @Prop() id
  @Provide('authority') authority
  @Provide('handleShowAuthorityDetail') handleShowAuthorityDetail
  @Provide('uptimeAuth') uptimeAuth
  private active = ''
  private tabList: ITabItem[] = []
  private fromRoueName = ''
  private nodeName = ''
  private uptimeAuth = uptimeAuth
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.active = vm.id && UptimeCheckType.node === vm.id ?  UptimeCheckType.node : UptimeCheckType.task
      vm.fromRoueName = from.name || ''
    })
  }
  beforeRouteLeave(to, from, next) {
    this.nodeName = ''
    next()
  }
  created() {
    this.tabList = [
      {
        name: this.$t('任务'),
        id: UptimeCheckType.task
      },
      {
        name: this.$t('节点'),
        id: UptimeCheckType.node
      }
    ]
  }
  handleSetNodeName(name) {
    this.active = UptimeCheckType.task
    this.nodeName = name || ''
  }
  handleTabChange(id) {
    this.active = id
  }
}
</script>
<style lang="scss" scoped>
.uptime-check {
  margin: -20px -24px 0 -24px;
  height: calc(100vh - 52px);
  overflow: hidden;
  &-tab {
    height: 32px;
    padding-left: 24px;
    padding-top: 3px;
    background: #fff;
    border-bottom: 1px solid #dcdee5;
    box-shadow: 0 3px 4px 0 rgba(64, 112, 203, .06);
    .tab-item {
      display: inline-block;
      height: 100%;
      font-size: 14px;
      margin-right: 30px;
      cursor: pointer;
    }
    .tab-active {
      color: #3a84ff;
      border-bottom: 2px solid #3a84ff;
    }
  }
  &-content {
    overflow: auto;
    padding: 20px 20px 0 0;
    height: calc( 100vh - 88px);
  }
}
</style>
