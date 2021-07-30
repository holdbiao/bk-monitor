<template>
  <div class="hosts" v-if="initConfig">
    <div style="margin-bottom: 10px">{{$t('设备IP列表')}}</div>
    <bk-tag-input
      style="margin-bottom: 20px"
      v-if="data.collectType === 'SNMP'"
      v-model="snmpTargets"
      :placeholder="$t('请输入采集目标主机')"
      :allow-create="true"
      :allow-auto-match="true"
      :has-delete-icon="true">
    </bk-tag-input>
    <div class="topo-selector-wrapper" ref="topoSelectorWrapper" v-else>
      <topo-selector
        :tree-height="topoSelectorHeight"
        :height="topoSelectorHeight"
        preview-width="25%"
        :preview-range="[150, 800]"
        left-panel-width="30%"
        :target-node-type="selector.targetNodeType"
        :target-object-type="selector.targetObjectType"
        :checked-data="selector.checkedData"
        ref="topoSelector">
      </topo-selector>
    </div>
    <div style="margin-bottom: 10px" v-if="config.supportRemote">{{$t('采集器主机')}}</div>
    <div class="select-private-host" v-if="config.supportRemote">
      <div class="left" @click="handleShow">
        <span class="ip" v-if="remoteHost.ip">{{remoteHost.ip}}</span>
        <span v-else> {{ $t('添加采集插件运行主机') }} </span>
        <!-- <span style="color: #3A84FF; cursor: pointer;" @click="handleShow">使用选择器</span> -->
      </div>
      <div class="right">
        <bk-checkbox :disabled="!remoteHost.ip" v-model="remoteHost.isCollectingOnly"> {{ $t('采集专有主机') }} <span v-bk-tooltips.top="$t('专有采集主机 使用整个服务器的50%的资源,其他情况都只是使用10%的资源并且不超过单CPU资源.')" class="icon-monitor icon-tips"></span>
        </bk-checkbox>
      </div>
    </div>
    <div class="footer">
      <bk-button theme="primary" @click.stop="handleStart"> {{ $t('开始下发') }} </bk-button>
      <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </div>
    <select-host :conf="conf" :filter="searchFn" :get-host="getHost" @confirm="handleSelect"></select-host>
  </div>
</template>
<script>
import SelectHost from '../../../plugin-manager/plugin-instance/set-steps/components/select-host'
import TopoSelector from '../../../../components/ip-selector/business/topo-selector-new'
import { saveCollectConfig } from '../../../../../monitor-api/modules/collecting'
import { hostAgentStatus, getNodesByTemplate } from '../../../../../monitor-api/modules/commons'
export default {
  name: 'BkHost',
  components: {
    SelectHost,
    TopoSelector
  },
  props: {
    data: {
      type: Object,
      default: () => ({})
    },
    pageLoading: Boolean,
    step: {
      type: Number,
      default: 0
    },
    diffData: {
      type: Object,
      default: () => ({})
    },
    config: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      initConfig: false,
      host: [],
      conf: {
        isShow: false
      },
      remoteHost: {
        ip: '',
        bkSupplierId: 0,
        isCollectingOnly: false
      },
      id: null,
      nodeType: 'INSTANCE',
      configDetail: {},
      selector: {
        mode: 'edit',
        targetNodeType: 'INSTANCE',
        targetObjectType: 'HOST',
        checkedData: []
      },
      agentStatusMap: {
        normal: 'Agent 正常',
        abnormal: 'Agent 异常',
        not_exist: 'Agent 未安装'
      },
      isNoHost: false,
      nodesMap: new Map(),
      loading: false,
      snmpTargets: [],
      topoSelectorHeight: 0
    }
  },
  computed: {
    dynamicTopoCountLabel() {
      return this.config.set.data.objectType === 'HOST' ? this.$t('当前主机数') : this.$t('当前实例数')
    },
    isSnmp() {
      return this.config.params.collect_type === 'SNMP'
    }
  },
  watch: {
    config: {
      handler(v) {
        if (v.params.remote_collecting_host) {
          this.remoteHost.ip = v.params.remote_collecting_host.ip
          this.remoteHost.bkCloudId = v.params.remote_collecting_host.bk_cloud_id
          this.remoteHost.bkSupplierId = v.params.remote_collecting_host.bk_supplier_id
          this.remoteHost.isCollectingOnly = v.params.remote_collecting_host.is_collecting_only
        } else {
          this.remoteHost.isCollectingOnly = true
        }
        this.handleConfig(v)
        this.initConfig = true
      },
      deep: true
    }
  },
  created() {
    // static-ip、static-top 对应的nodeType参数都为 instance
    this.id = this.data.id
    // const hostType = {
    //   INSTANCE: 'static-ip',
    //   TOPO: 'dynamic-topo'
    // }
    // this.selector.type = this.data.objectTypeEn === 'SERVICE' ? 'dynamic-topo' : hostType[this.data.nodeType]
    this.nodeType = this.data.nodeType
  },
  methods: {
    // handleLoadingChange(status) {
    //   this.$emit('update:pageLoading', status)
    // },
    handleShow() {
      this.conf.isShow = true
    },
    // handleIpChangeType(v) {
    //   this.selectorType = v
    //   // this.selector.type = v
    // },
    handleSelect(v) {
      this.remoteHost.ip = v.ip
      this.remoteHost.bkCloudId = v.cloudId
      this.remoteHost.bkSupplierId = v.supplierId
    },
    // handleCheckedChange(checkedData) {
    //   const { selector } = this
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
    handleConfig(v) {
      const { selector } = this
      const { set } = v
      const setOthers = set.others
      const { objectType } = set.data
      const { targetNodes } = setOthers
      const { targetNodeType } = setOthers
      selector.mode = v.mode

      selector.targetNodeType = targetNodeType
      selector.targetObjectType = objectType

      this.$emit('update:pageLoading', false)
      this.isNoHost = !!targetNodes.length
      selector.checkedData = targetNodes
      if (this.isSnmp) this.snmpTargets = targetNodes.map(item => item.ip)
      this.$nextTick(() => {
        this.topoSelectorHeight = this.$refs.topoSelectorWrapper.clientHeight
      })
    },
    async handleStart() {
      let data = null
      let type = null
      if (!this.isSnmp) {
        const res = this.$refs.topoSelector.getCheckedData()
        data = res.data
        type = res.type
        if (!data.length && !this.isNoHost) {
          this.$emit('update:diffData', { added: [], removed: [], updated: [], unchanged: [] })
          this.$emit('update:step', 1)
          this.$emit('update:needRollback', false)
          return
        }
      }
      this.$emit('update:pageLoading', true)
      const params = { ...this.config.params }
      if (this.remoteHost.ip) {
        params.remote_collecting_host = { ip: this.remoteHost.ip,
          bk_cloud_id: this.remoteHost.bkCloudId,
          bk_supplier_id: this.remoteHost.bkSupplierId,
          is_collecting_only: this.remoteHost.isCollectingOnly }
      }
      if (this.isSnmp) {
        params.target_nodes = this.snmpTargets.map(ip => ({
          ip,
          bk_cloud_id: 0,
          bk_supplier_id: 0
        }))
      } else {
        params.target_nodes = data
      }
      if (this.isSnmp) {
        params.target_node_type = 'INSTANCE'
      } else {
        // 没有选中数据，则使用初始类型
        params.target_node_type = !params.target_nodes.length ? this.selector.targetNodeType : type
      }

      if (this.$refs.topoSelector) {
        const target = this.$refs.topoSelector.getCheckedData()
        // 临时处理
        if (['SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(target.type)) {
          const data = await getNodesByTemplate({
            bk_inst_type: this.selector.targetObjectType,
            bk_obj_id: target.type,
            bk_inst_ids: target.data.map(item => item.bk_inst_id)
          }).catch(() => [])
          target.data = data
        }

        this.$emit('target', {
          bkObjType: this.selector.targetObjectType,
          target: target.data,
          bkTargetType: target.type
        })
      } else if (this.isSnmp) {
        this.$emit('target', {
          bkObjType: this.selector.targetObjectType,
          target: this.snmpTargets,
          bkTargetType: this.selector.targetNodeType
        })
      }

      saveCollectConfig({ id: this.id, ...params, operation: 'ADD_DEL' }, { needMessage: false }).then((data) => {
        this.$emit('update:diffData', data.diff_node)
        this.$emit('update:step', 1)
        this.$emit('step-change', true, 0)
        this.$emit('update:pageLoading', false)
      })
        .catch((res) => {
          this.$bkMessage({
            theme: 'error',
            message: res.message || this.$t('系统出错了'),
            ellipsisLine: 0
          })
          this.$emit('update:pageLoading', false)
        })
    },
    handleCancel() {
      this.$router.back()
    },
    getHost() {
      return hostAgentStatus()
    },
    searchFn(keyWord, data) {
      return keyWord ? data.filter(item => item.ip.indexOf(keyWord) > -1) : data
    }
  }
}
</script>
<style lang="scss" scoped>
.hosts {
  height: 100%;
  padding: 40px 56px 40px 60px;
  display: flex;
  flex-direction: column;
  .topo-selector-wrapper {
    flex: 1;
    margin-bottom: 10px;
    height: 0;
    /deep/ .ip-select-left .left-content-wrap {
      height: calc(var(--height) - 135px)
    }
    /deep/ .bk-big-tree {
      height: 310px;
      overflow: auto;
    }
  }
  .select-private-host {
    display: flex;
    height: 42px;
    .left {
      display: flex;
      flex-grow: 1;
      padding: 0 20px;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: #c4c6cc;
      border: 1px solid #dcdee5;
      .ip {
        color: #63656e;
      }
      &:hover {
        border: 1px solid #3a84ff;
      }
    }
    .icon-tips {
      color: #979ba5;
    }
    .right {
      width: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #dcdee5;
      border-left: 0;
    }
  }
  .footer {
    margin-top: 20px;
    font-size: 0;
    /deep/ .bk-button {
      margin-right: 10px;
    }
  }
  /deep/ .bk-checkbox-text {
    /* stylelint-disable-next-line declaration-no-important */
    color: #63656e !important;
  }
  /deep/ .group-append {
    padding-left: 26px;
    min-width: 170px;
    line-height: 30px;
    .bk-checkbox-text {
      font-size: 12px;
    }
  }
}
</style>
