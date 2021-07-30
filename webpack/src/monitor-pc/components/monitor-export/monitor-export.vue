<template>
  <span class="monitor-export" @click="handleExport">
    <slot>{{$t('导出')}}</slot>
  </span>
</template>
<script lang="ts">
import { CreateElement } from 'vue'
import { Vue, Component, Emit } from 'vue-property-decorator'

@Component({ name: 'MonitorExport' })
export default class MonitorExport extends Vue {
  render(h: CreateElement) {
    return h('span', {
      class: {
        'monitor-export': true
      },
      on: {
        click: this.handleExport
      }
    }, String(this.$t('导出')))
  }
  @Emit('click')
  handleExport(): Function {
    return (data: any, fileName: string) => {
      if (!data) return
      const downlondEl = document.createElement('a')
      const blob = new Blob([JSON.stringify(data, null, 4)])
      const fileUrl = URL.createObjectURL(blob)
      downlondEl.href = fileUrl
      downlondEl.download = fileName || 'metric.json'
      downlondEl.style.display = 'none'
      document.body.appendChild(downlondEl)
      downlondEl.click()
      document.body.removeChild(downlondEl)
    }
  }
}
</script>

<style lang="scss" scoped>
.monitor-export {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  color: #3a84ff;
  margin: 0 10px;
  &:hover {
    cursor: pointer;
  }
}
</style>
