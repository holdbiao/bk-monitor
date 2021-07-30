<template>
  <article class="strategy-config-target" v-bkloading="{ isLoading: loading }">
    <section class="target-container" ref="targetContainer">
      <div class="target-container-lable"> {{ $t('监控目标') }} </div>
      <topo-selector
        ref="topoSelector"
        class="topo-selector"
        :tree-height="targetContainerHeight"
        :height="targetContainerHeight"
        :target-object-type="targetType"
        @check-change="handleCheckedChange">
      </topo-selector>
    </section>
    <section class="target-footer">
      <bk-button class="btn" theme="primary" @click="handleSave" :disabled="!checkedData.length || !historyId"> {{ $t('保存') }} </bk-button>
      <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </section>
  </article>
</template>

<script>
import TopoSelector from '../../../components/ip-selector/business/topo-selector-new.vue'
import { mapActions } from 'vuex'

export default {
  name: 'ImportConfigurationTarget',
  components: {
    TopoSelector
  },
  props: {
    // 历史任务ID
    historyId: {
      type: [Number, String],
      default: 0,
      required: true
    },
    // 实例类型
    targetType: {
      type: String,
      default: 'INSTANCE',
      required: true
    }
  },
  data() {
    return {
      loading: false,
      checkedData: [],
      targetNodeType: 'TOPO',
      targetContainerHeight: 0
    }
  },
  mounted() {
    this.targetContainerHeight = this.$refs.targetContainer.clientHeight
  },
  methods: {
    ...mapActions('import', ['addMonitorTarget']),
    /**
     * 选择器勾选节点事件
     * @param {Array} checkedData 选中节点数据
     */
    handleCheckedChange(checkedData) {
      this.checkedData = checkedData.data
      this.targetNodeType = checkedData.type
    },
    /**
     * 获取统一添加监控目标请求参数
     */
    getParams() {
      // 字段名
      let field = ''
      const hostTargetFieldType = {
        TOPO: 'host_topo_node',
        INSTANCE: 'ip',
        SERVICE_TEMPLATE: 'host_service_template',
        SET_TEMPLATE: 'host_set_template'
      }
      const serviceTargetFieldType = {
        TOPO: 'service_topo_node',
        SERVICE_TEMPLATE: 'service_service_template',
        SET_TEMPLATE: 'service_set_template'
      }
      if (this.targetType === 'HOST') {
        field = hostTargetFieldType[this.targetNodeType]
      } else {
        field = serviceTargetFieldType[this.targetNodeType]
      }

      return {
        import_history_id: Number(this.historyId),
        target: [[{
          field,
          method: 'eq',
          value: this.checkedData
        }]]
      }
    },
    // 批量修改采集目标
    async handleSave() {
      const params = this.getParams()
      this.loading = true
      const success = await this.addMonitorTarget(params).catch(() => false)
      this.loading = false
      if (success) {
        this.$bkMessage({
          theme: 'success',
          message: this.$t('添加成功')
        })
        this.$router.push({ name: 'export-import' })
      }
    },
    handleCancel() {
      this.$router.back()
    }
  }
}
</script>

<style lang="scss" scoped>
    @import "../../../static/css/common";

    .strategy-config-target {
      padding: 10px 0 0 10px;
      color: $defaultFontColor;
      height: calc(100vh - 100px);
      .select-tips {
        display: flex;
        margin: 0 0 15px 96px;
        i {
          color: $unsetIconColor;
          font-size: 16px;
          margin-right: 6px;
        }
      }
      .target-container {
        display: flex;
        height: 80%;
        margin-bottom: 20px;
        &-lable {
          font-size: 14px;
          margin-right: 40px;
        }
        /deep/ .topo-selector {
          width: calc(100% - 126px);
        }
        .topo-selector {
          flex: 1;
          margin-right: 20px;
        }
      }
      .target-footer {
        margin-left: 96px;
        .btn {
          margin-right: 8px;
        }
      }
    }
</style>
