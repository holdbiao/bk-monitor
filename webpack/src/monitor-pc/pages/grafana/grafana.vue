<template>
  <div class="grafana-wrap">
    <iframe ref="iframe" class="grafana-wrap-frame" allow="fullscreen" :src="grafanaUrl"></iframe>
  </div>
</template>
<script lang="ts">
import { Component, Watch, Ref, Mixins } from 'vue-property-decorator'
import  authorityMixinCreate from '../../mixins/authorityMixin'
import * as authMap from '../grafana/authority-map'
import { getDashboardList } from '../../../monitor-api/modules/grafana'
import { DASHBOARD_ID_KEY } from '../../constant/constant'

@Component({
  name: 'grafana'
})
export default class Grafana extends Mixins(authorityMixinCreate(authMap)) {
  private grafanaUrl = ''
  private unWatch = null
  get orignUrl() {
    return  process.env.NODE_ENV === 'development'
      ? `${process.env.proxyUrl}/`
      : `${location.origin}${window.site_url}`
  }
  get dashboardCheck() {
    return this.$store.getters['grafana/dashboardCheck']
  }
  @Ref('iframe') private iframeRef: HTMLIFrameElement
  @Watch('dashboardCheck')
  onIsCreateChange(v) {
    this.iframeRef && this.iframeRef.contentWindow.postMessage(v.split('-')[0], '*')
  }
  async created() {
    const list = await getDashboardList().catch(() => [])
    const dashboardCache = localStorage.getItem(DASHBOARD_ID_KEY)
    const { bizId } = this.$store.getters
    if (list.length) {
      let dashboardId = ''
      if (dashboardCache && dashboardCache.indexOf('{') > -1) {
        const data = JSON.parse(dashboardCache)
        dashboardId = data[bizId]
        if (!(dashboardId && list.some(item => item.uid === dashboardId))) {
          dashboardId = list[0].uid
          data[bizId] = dashboardId
          localStorage.setItem(DASHBOARD_ID_KEY, JSON.stringify(data))
        }
      } else if (list.some(item => item.uid === dashboardCache)) {
        dashboardId = dashboardCache
        localStorage.setItem(DASHBOARD_ID_KEY, JSON.stringify({ [bizId]: dashboardId }))
      } else {
        dashboardId = list[0].uid
        localStorage.setItem(DASHBOARD_ID_KEY, JSON.stringify({ [bizId]: dashboardId }))
      }
      this.grafanaUrl = `${this.orignUrl}grafana/d/${dashboardId}?orgName=${bizId}`
    } else {
      this.grafanaUrl = `${this.orignUrl}grafana/?orgName=${this.$store.getters.bizId}`
    }
    await this.$nextTick()
    this.unWatch = this.$watch('authority', () => {
      this.$store.commit('grafana/setHasManageAuth', this.authority.MANAGE_AUTH)
    }, { deep: true, immediate: true })
  }

  mounted() {
    window.addEventListener('message', this.handleMessage, false)
  }

  beforeDestroy() {
    window.removeEventListener('message', this.handleMessage, false)
    this.unWatch && this.unWatch()
  }

  handleMessage(e) {
    if (e?.data?.pathname) {
      const pathname = `${e.data.pathname}`
      const matches = pathname.match(/\/d\/([^/]+)\//)
      const isInDashboard = !!matches && matches.length > 0
      const dashboardId = isInDashboard ? matches[1] : ''
      localStorage.setItem(DASHBOARD_ID_KEY, dashboardId)
    } else if (e?.data?.redirected) {
      if (e.data.href) {
        location.href = `${e.data.href}?c_url=${location.href}`
      } else {
        location.reload()
      }
    }
  }
}
</script>
<style lang="scss" scoped>
    .grafana-wrap {
      margin: -20px -24px 0;
      &-frame {
        width: 100%;
        min-width: 100%;
        min-height: calc(100vh - 55px);
        border: 0;
      }
    }
</style>
