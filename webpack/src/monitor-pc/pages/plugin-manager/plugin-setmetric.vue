<template>
  <metric-dimension
    v-monitor-loading="{ isLoading: loading }"
    :metric-json="metricData"
    :plugin-data="pluginData"
    :is-from-home="true">
  </metric-dimension>
</template>

<script>
import MetricDimension from './plugin-instance/set-steps/metric-dimension/metric-dimension-dialog.vue'
import { retrieveCollectorPlugin } from '../../../monitor-api/modules/model'
import authorityMixinCreate from '../../mixins/authorityMixin'
import * as pluginManageAuth from './authority-map'

export default {
  name: 'PluginSetmetric',
  components: {
    MetricDimension
  },
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail
    }
  },
  mixins: [authorityMixinCreate(pluginManageAuth)],
  data() {
    return {
      loading: false,
      metricData: [],
      pluginData: {}
    }
  },
  created() {
    this.getDeteilData()
  },
  methods: {
    async getDeteilData() {
      this.loading = true
      let detailData = {}
      this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      await retrieveCollectorPlugin(this.$route.params.pluginId).then((data) => {
        detailData = data
        this.$store.commit(
          'app/SET_NAV_TITLE',
          `${this.$t('route-' + '设置指标&维度').replace('route-', '')} - ${this.$route.params.pluginId}`
        )
      })
        .finally(() => {
          this.loading = false
        })
      this.metricData = detailData.metric_json
      this.metricData.forEach((group) => {
        group.fields.forEach((item) => {
          item.isCheck = false
          item.isDel = true
          item.errValue = false
          item.reValue = false
          item.descReValue = false
          item.showInput = false
          item.isFirst = false
          if (item.monitor_type === 'metric') {
            item.order = 0
          } else {
            item.order = 1
          }
        })
      })
      this.pluginData = {
        plugin_id: detailData.plugin_id,
        plugin_type: detailData.plugin_type,
        config_version: detailData.config_version,
        info_version: detailData.info_version
      }
    }
  }
}
</script>
