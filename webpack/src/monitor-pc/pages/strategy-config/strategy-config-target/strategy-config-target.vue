<template>
  <div class="strategy-config-target" v-bkloading="{ isLoading: loading }">
    <!-- tips -->
    <!-- <div class="select-tips"><i class="icon-monitor icon-tips"></i>{{ $t('动态：只能选择节点，策略目标按节点动态变更。静态：只能选择主机IP，采集目标不会变更。') }}</div> -->
    <!-- IP选择器 -->
    <div class="target-container" ref="targetContainer">
      <!-- <topo-selector
        v-if="isGetDetail"
        :max-width="850"
        ref="topoSelector"
        :mode="selector.mode"
        :type="selector.type"
        :is-instance="selector.isInstance"
        :tab-disabled="selector.tabDisabled"
        :default-active="selector.defaultActive"
        :checked-data="selector.checkedData"
        @type-change="handleTypeChange"
        @checked-change="handleCheckedChange"
        @loading-change="handleLoadingChange"
        @has-checked-data="handleChecked"
        @table-data-change="handleAngChange">
      </topo-selector> -->
      <topo-selector
        :tree-height="targetContainerHeight"
        :height="targetContainerHeight"
        v-if="isGetDetail"
        :target-node-type="selector.targetNodeType"
        :target-object-type="selector.targetObjectType"
        :checked-data="selector.checkedData"
        :preview-width="230"
        :hidden-template="hiddenTemplate"
        ref="topoSelector"
        @check-change="handleChecked">
      </topo-selector>
    </div>
    <div class="target-footer">
      <bk-button class="btn" theme="primary" @click="handleSaveData" :disabled="canSaveEmpty ? false : !checked.length"> {{ $t('保存') }} </bk-button>
      <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </div>
  </div>
</template>

<script>
import TopoSelector from '../../../components/ip-selector/business/topo-selector-new'
import { strategyConfigDetail, bulkEditStrategy } from '../../../../monitor-api/modules/strategies'
import { createNamespacedHelpers } from 'vuex'
const { mapGetters } = createNamespacedHelpers('strategy-config')
export default {
  name: 'StrategyConfigTarget',
  components: {
    TopoSelector
  },
  props: {
    targetList: {
      type: Array,
      default() {
        return []
      }
    },
    setConfig: {
      type: Object,
      default() {
        return {
          bizId: '',
          objectType: '',
          strategyId: 0
        }
      }
    },
    // 是否允许保存空的目标
    canSaveEmpty: {
      type: Boolean,
      default: false
    },
    hiddenTemplate: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      isGetDetail: false,
      //   targetNodeTypeMap: {
      //     'static-ip': 'INSTANCE',
      //     'static-topo': 'INSTANCE',
      //     'dynamic-topo': 'TOPO',
      //     'dynamic-group': 'TOPO'
      //   },
      selector: {
        strategyId: null,
        bizId: 2,
        mode: 'add',
        targetObjectType: 'HOST',
        targetNodeType: 'INSTANCE',
        checkedData: []
      },
      saveData: {
        targetNodes: [],
        targetNodeType: null
      },
      isBack: false,
      checked: [],
      needCheck: true,
      changeNum: 0,
      targetContainerHeight: 0
    }
  },
  computed: {
    ...mapGetters(['strategyParams'])
  },
  created() {
    this.handleConfig(this.setConfig)
    this.$nextTick(() => {
      this.targetContainerHeight = this.$refs.targetContainer.clientHeight
    })
  },
  methods: {
    // handleTypeChange(type) {
    //   this.selectorType = type
    //   this.selector.targetNodeType = this.targetNodeTypeMap[type]
    // },
    handleChecked(checkedData) {
      const { type, data = [] } = checkedData
      this.checked = data
      this.selector.targetNodeType = type
    },
    // 创建/修改策略配置
    async handleSaveData() {
      if (this.setConfig.strategyId) {
        this.handleSaveFromList()
      } else {
        this.handleSaveFormSet()
      }
    },
    // 反馈选中目标的描述
    handleSetTargetDesc(params) {
      let message = ''
      let subMessage = ''
      // eslint-disable-next-line camelcase
      const { target_nodes = [], target_node_type = 'TOPO', target_object_type } = params
      if (!target_nodes.length) return { message, subMessage }

      if (['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(target_node_type)) {
        const count = target_nodes.reduce((pre, item) => {
          const allHost = item.all_host || []
          return Array.from(new Set([...pre, ...allHost]))
        }, []).length
        const textMap = {
          TOPO: `${this.$t('个')}${this.$t('节点')}`,
          SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
          SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
        }
        message = `${target_nodes.length} ${textMap[target_node_type]}`
        // 暂时隐藏模板统计信息
        // eslint-disable-next-line camelcase
        target_node_type === 'TOPO' && (subMessage = `（ ${count} ${target_object_type === 'SERVICE'
          ? this.$t('个') + this.$t('实例')
          : this.$t('台') + this.$t('主机')}）`)
      } else {
        message = `${target_nodes.length} 台主机 `
      }
      return {
        message,
        subMessage
      }
    },
    // 来自编辑新增页面的保持
    handleSaveFormSet() {
      const params = this.getParams()
      this.$emit('message-change', this.handleSetTargetDesc(params))
      this.$emit('target-type-change', this.selector.targetNodeType)
      this.$emit('target-change', params.target_nodes)
    },
    // 来自列表增删目标
    async handleSaveFromList() {
      this.loading = true
      const params = this.getParams()
      let field = ''
      // 判断是主机还是服务，静态还是动态
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
      if (this.selector.targetObjectType === 'HOST') {
        field = hostTargetFieldType[params.target_node_type]
      } else {
        field = serviceTargetFieldType[params.target_node_type]
      }
      const target = [[{
        field,
        method: 'eq',
        value: this.handleCheckedData(params.target_node_type, params.target_nodes)
      }]]
      const success = await bulkEditStrategy({ id_list: [params.id], edit_data: { target } }).catch(() => false)
      success && this.$bkMessage({ theme: 'success', message: this.$t('修改成功') })
      this.handleCancel()
      this.loading = false
    },
    // 获取策略详情数据
    async getStrategyConfig(id) {
      const config = {}
      const data = await strategyConfigDetail({ id }).catch(() => false)
      config.bizId = data.bk_biz_id
      // 动态拓扑可以从bk_target_detail字段获取，该字段含有名称，不用前段拼接
      if (data.bk_target_type !== 'TOPO' && data.item_list[0].target[0].length) {
        config.targetNodes = data.item_list[0].target[0][0].value
      } else {
        config.targetNodes = data.bk_target_detail || []
      }
      config.objectType = data.bk_obj_type
      config.targetNodeType = data.bk_target_type
      this.loading = false
      return config
    },
    // IP选择器派发的loading状态
    handleLoadingChange(status) {
      this.loading = status
    },
    // 初始化
    async handleConfig(params) {
      this.loading = true
      this.isGetDetail = false
      const { selector } = this
      if (+params.strategyId > 0) {
        selector.mode = 'edit'
        selector.strategyId = params.strategyId
        const strategyConfig = await this.getStrategyConfig(params.strategyId)
        if (params.objectType === strategyConfig.objectType) {
          selector.targetNodeType = strategyConfig.targetNodeType
          selector.targetNodes = strategyConfig.targetNodes
          this.checked = strategyConfig.targetNodes
        }
        this.isGetDetail = true
      } else {
        this.isGetDetail = true
        selector.mode = this.targetList.length ? 'edit' : 'add'
        selector.targetNodeType = params.targetType || (params.objectType === 'SERVICE'
          ? 'TOPO' : 'INSTANCE')
        selector.targetNodes = this.targetList
        this.checked = this.targetList
      }
      selector.targetObjectType = params.objectType
      selector.checkedData = selector.targetNodes || []
      this.loading = false
    },
    // 获取要保存的数据
    getParams() {
      const { selector } = this
      const { saveData } = this
      // 转换成后台需要的类型
      // getCheckedData 获取IP选择器右边的数据
      const { type, data } = this.$refs.topoSelector.getCheckedData()
      saveData.targetNodes = data

      // 编辑态下如果目标节点为空，则取默认type
      saveData.targetNodeType = this.selector.mode === 'edit' && !saveData.targetNodes.length
        ? this.selector.targetNodeType
        : type

      const params = {
        id: selector.strategyId,
        bk_biz_id: selector.bizId,
        target_object_type: selector.targetObjectType,
        target_node_type: saveData.targetNodeType,
        target_nodes: saveData.targetNodes
      }
      return params
    },
    // // 选择框状态改变触发的事件
    // handleCheckedChange(checkedData) {
    //   const { selector } = this
    //   // const type = selector.type
    //   if (['static-ip', 'static-topo'].includes(this.selectorType) && checkedData.length) {
    //     // 如果是 'static-ip'，'static-topo' 类型，且有选中则禁用动态 tab
    //     selector.tabDisabled = 1
    //   } else if (this.selectorType === 'dynamic-topo' && checkedData.length) {
    //     // 如果是 'dynamic-topo' 类型，且有选中则禁用静态 tab
    //     selector.tabDisabled = 0
    //   } else if (!selector.isInstance && !checkedData.length) {
    //     // 如果采集对象不是服务，且没有选中则不禁用 tab
    //     selector.tabDisabled = -1
    //   }
    // },
    // 分静态和动态拓扑
    handleCheckedData(type, data) {
      const checkedData = []
      if (type === 'INSTANCE') {
        data.forEach((item) => {
          checkedData.push({
            ip: item.ip,
            bk_cloud_id: item.bk_cloud_id,
            bk_supplier_id: item.bk_supplier_id
          })
        })
      } else {
        data.forEach((item) => {
          checkedData.push({
            bk_inst_id: item.bk_inst_id,
            bk_obj_id: item.bk_obj_id
          })
        })
      }
      return checkedData
    },
    handleAngChange() {
      this.changeNum += 1
    },
    handleCancel() {
      this.$emit('cancel', false)
    }
  }
}
</script>

<style lang="scss" scoped>
    .strategy-config-target {
      color: #63656e;
      .select-tips {
        display: flex;
        margin: 15px 0;
        i {
          color: #979ba5;
          font-size: 16PX;
          margin-right: 6px;
        }
      }
      .target-container {
        display: flex;
        height: 560px;
        margin-top: 15px;
        &-lable {
          font-size: 14px;
          margin-right: 40px;
        }
      }
      .target-footer {
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        .btn {
          margin-right: 8px;
        }
      }
      /deep/ .ip-select-left .left-content-wrap {
        height: calc(var(--height) - 135px)
      }
      /deep/ .bk-big-tree {
        height: 310px;
        overflow: auto;
      }
    }
</style>
