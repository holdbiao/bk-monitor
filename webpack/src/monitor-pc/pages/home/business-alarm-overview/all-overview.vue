<template>
  <div class="all-overview">
    <bk-tab :active.sync="active" type="unborder-card"
            @tab-change="handleTabChange"
    >
      <bk-tab-panel
        v-for="(panel, index) in panels"
        v-bind="panel"
        :key="index">
      </bk-tab-panel>
      <div>
        <uptimecheck :alarm="alarm" v-if="active === 'uptimecheck'"></uptimecheck>
        <service :alarm="alarm" v-if="active === 'service'"></service>
        <os :alarm="alarm" v-if="active === 'os'"></os>
        <process :alarm="alarm" v-if="active === 'process'"></process>
      </div>
    </bk-tab>
  </div>
</template>
<script>
import Uptimecheck from './uptimecheck'
import Service from './service'
import Os from './os'
import Process from './process'
export default {
  name: 'all-overview',
  components: {
    Uptimecheck,
    Service,
    Os,
    Process
  },
  props: {
    selectedIndex: Number,
    alarm: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      panels: [
        { label: this.$t('拨测监控'), name: 'uptimecheck' },
        { label: this.$t('服务监控'), name: 'service' },
        { label: this.$t('进程监控'), name: 'process' },
        { label: this.$t('主机监控'), name: 'os' }
      ],
      active: 'uptimecheck'
    }
  },
  methods: {
    handleTabChange(v) {
      const indexMap = {
        uptimecheck: 0,
        service: 1,
        process: 2,
        os: 3
      }
      this.$emit('update:selectedIndex', indexMap[v])
    }
  }
}
</script>
