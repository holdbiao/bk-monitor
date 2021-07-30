<template>
  <div class="config-select" v-bkloading="{ isLoading: loading }">
    <template v-if="config.set.data.collectType === 'SNMP'">
      <div style="margin-bottom: 10px">{{$t('设备IP列表')}}</div>
      <bk-tag-input
        v-model="snmpTargets"
        :placeholder="$t('请输入采集目标主机')"
        :allow-create="true"
        :allow-auto-match="true"
        :has-delete-icon="true"
        :paste-fn="handleTargetsPaste"
        @change="handleSnmpTargetChange">
      </bk-tag-input>
    </template>
    <div class="select-container" ref="selectContainer" v-else>
      <!-- <div class="select-tips"><i class="icon-monitor icon-tips"></i> {{ $t('动态：只能选择节点，采集目标按节点动态变更。静态：只能选择主机IP，采集目标不会变更。') }}</div> -->
      <!-- <topo-selector
        ref="topoSelector"
        :mode="selector.mode"
        :type="selectorType"
        :is-instance="selector.isInstance"
        :tab-disabled="selector.tabDisabled"
        :default-active="selector.defaultActive"
        :checked-data="selector.checkedData"
        @type-change="(type) => selectorType = type"
        @checked-change="handleCheckedChange"
        @loading-change="(status) => loading = status">
      </topo-selector> -->
      <topo-selector
        :tree-height="selectContainerHeight"
        :height="selectContainerHeight"
        preview-width="25%"
        :preview-range="[150, 800]"
        left-panel-width="30%"
        :target-node-type="selector.targetNodeType"
        :target-object-type="selector.targetObjectType"
        :checked-data="selector.checkedData"
        ref="topoSelector">
      </topo-selector>
    </div>
    <div :class="['remote-container', { 'is-snmp': config.set.data.collectType === 'SNMP' }]">
      <div class="remote-hint" v-if="config.set.supportRemote">
        <bk-switcher v-model="info.isUseRemoteHost" size="small"></bk-switcher>
        <span class="hint-text"> {{ $t('使用远程运行主机') }} </span>
        <i class="icon-monitor icon-tips hint-icon" v-bk-tooltips="remoteHostTooltips"></i>
      </div>
      <div style="margin-top: 10px" v-if="config.set.data.collectType === 'SNMP' && info.isUseRemoteHost">{{$t('采集器主机')}}</div>
      <div class="remote-host" v-show="info.isUseRemoteHost">
        <div class="host-input">
          <div style="flex-grow: 1" @click="handleShowSelector">
            <span class="host-placeholder" v-if="!info.remoteCollectingHost.ip"> {{ $t('添加采集插件运行主机') }} </span>
            <span v-else>{{info.remoteCollectingHost.ip}}</span>
          </div>
          <i class="bk-icon icon-close-circle-shape clear-icon" @click="handleClearIp" v-if="info.remoteCollectingHost.ip"></i>
        </div>
        <div class="host-pro">
          <bk-checkbox class="pro-checkbox"
                       v-model="info.remoteCollectingHost.isCollectingOnly"
                       :disabled="!canSelectProHost"> {{ $t('采集专有主机') }} </bk-checkbox>
          <i class="icon-monitor icon-tips host-hint-icon" v-bk-tooltips="proHostTooltips"></i>
        </div>
      </div>
    </div>
    <div class="btn-container">
      <bk-button class="btn-previous" @click="handlePrevious"> {{ $t('上一步') }} </bk-button>
      <bk-button class="btn-delivery" theme="primary" :disabled="!canDelivery" @click="handleDelivery"> {{ $t('开始下发') }} </bk-button>
      <!-- <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button> -->
    </div>
    <select-host :conf="selectHostConf" :filter="searchFn" :get-host="getHost" @confirm="handleHostConfirm"></select-host>
  </div>
</template>

<script>
import SelectHost from '../../../plugin-manager/plugin-instance/set-steps/components/select-host'
import { saveCollectConfig } from '../../../../../monitor-api/modules/collecting'
import { hostAgentStatus, getNodesByTemplate } from '../../../../../monitor-api/modules/commons'
import TopoSelector from '../../../../components/ip-selector/business/topo-selector-new'

export default {
  name: 'ConfigSelect',
  components: {
    SelectHost,
    TopoSelector
  },
  props: {
    config: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      loading: false,
      info: {
        isUseRemoteHost: false,
        targetNodeType: 'TOPO', // TOPO, INSTANCE
        remoteCollectingHost: {
          ip: '',
          bkCloudId: '',
          bkSupplierId: '',
          isCollectingOnly: true
        },
        targetNodes: []
      },
      remoteHostTooltips: {
        content: this.$t('默认就是采集目标与采集程序运行在一起，在有单独的采集主机或者权限限制需要远程采集的方式。'),
        placement: 'top'
      },
      proHostTooltips: {
        content: this.$t('使用整个服务器的50%的资源，其他情况都只是使用10%的资源并且不超过单CPU资源。'),
        placement: 'top'
      },
      selector: {
        mode: 'add',
        targetNodeType: 'TOPO',
        targetObjectType: 'HOST',
        checkedData: []
      },
      selectHostConf: {
        isShow: false
      },
      agentStatusMap: {
        normal: `Agent ${this.$t('正常')}`,
        abnormal: `Agent ${this.$t('异常')}`,
        not_exist: `Agent ${this.$t('未安装')}`
      },
      snmpTargets: [],
      ipv4Reg: /^((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]).){3}(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(?::(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$/, // eslint-disable-line
      selectContainerHeight: 0
    }
  },
  computed: {
    canSelectProHost() {
      // 以下情况可以选择【采集专有主机】：
      // 1. 已经选择远程主机。
      return this.info.remoteCollectingHost.ip !== ''
    },
    canDelivery() {
      // 以下情况可以下发：
      // 1. 没有启用【使用远程主机】；
      // 2. 已启用【使用远程主机】，且已经选择远程主机。
      const { info } = this
      const { isUseRemoteHost } = info
      const snmpTargetsIsOk = this.config.set.data.collectType === 'SNMP'
        ? !!this.snmpTargets.length && (isUseRemoteHost && info.remoteCollectingHost.ip !== '') : true
      return (!isUseRemoteHost || (isUseRemoteHost && info.remoteCollectingHost.ip !== '')) && snmpTargetsIsOk
    }
  },
  created() {
    this.handleConfig(this.config)
    this.$nextTick(() => {
      this.selectContainerHeight = this.$refs.selectContainer.clientHeight
    })
  },
  methods: {
    handlePrevious() {
      this.$emit('previous')
    },
    // 开始下发
    async handleDelivery() {
      const { info } = this
      const { remoteCollectingHost } = info
      if (!info.isUseRemoteHost && remoteCollectingHost) {
        remoteCollectingHost.ip = ''
        remoteCollectingHost.bkCloudId = ''
        remoteCollectingHost.bkSupplierId = ''
      }
      const params = this.config.set.data.collectType === 'SNMP' ? this.getSnmpParams() : this.getParams()

      if (this.config.set.data.collectType === 'SNMP') {
        this.$emit('target', {
          bkObjType: this.selector.targetObjectType,
          target: this.snmpTargets,
          bkTargetType: this.selector.targetNodeType
        })
      } else {
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
      }

      // 保存配置
      await this.saveConfig(params).then((data) => {
        this.selector.type = this.selectorType
        this.saveData(this.config, this.info, data)
        this.$emit('next')
        this.loading = false
      })
        .catch(() => {
          this.loading = false
        })
    },
    handleCancel() {
      this.$router.back()
    },
    handleConfig(v) {
      const { selector } = this
      const { set } = v
      const setOthers = set.others
      const { objectType } = set.data
      const { targetNodes } = setOthers
      const { targetNodeType } = setOthers
      const { select } = v
      selector.mode = v.mode
      if (set.data.collectType === 'SNMP') {
        this.info.isUseRemoteHost = true
        v.mode === 'edit' && (this.snmpTargets = setOthers.targetNodes.map(item => item.ip))
      }
      if (select.mode === 'edit') {
        this.info = select.data
      } else if (v.mode === 'edit') {
        this.info = this.handleData(setOthers)
      }
      // 如果是非编辑态则初始化targetNodeType
      selector.targetNodeType = targetNodeType || 'TOPO'
      selector.targetObjectType = objectType // 采集对象为服务时，只能选择动态
      selector.checkedData = targetNodes || []
    },
    // 保存配置
    saveData(config, info, data) {
      const { mode } = config
      const { selector } = this
      const others = {
        selector
      }
      config.data.id = data.id
      if (mode === 'edit') {
        const diffNode = data.diff_node
        others.added = diffNode.added
        others.updated = diffNode.updated
        others.removed = diffNode.removed
        others.unchanged = diffNode.unchanged
        others.allowRollback = data.can_rollback
      }
      this.$emit(
        'update:config',
        {
          ...config,
          select: {
            data: info,
            others,
            mode: 'edit'
          }
        }
      )
    },
    // 获取要保存的数据
    getParams() {
      const setData = this.config.set.data
      const pluginData = setData.plugin
      const selectData = this.info
      const { remoteCollectingHost } = selectData

      // 获取选择的数据
      const { type, data } = this.$refs.topoSelector.getCheckedData()

      selectData.targetNodes = data

      // 编辑态下如果目标节点为空，则取默认
      selectData.targetNodeType = this.selector.mode === 'edit' && !selectData.targetNodes.length
        ? this.selector.targetNodeType
        : type

      const param = {
        collector: {
          period: setData.period
        },
        plugin: {}
      }
      const { collector, plugin } = param
      if (setData.collectType === 'SNMP_Trap') {
        Reflect.set(param, 'snmp_trap', {})
        if (setData.plugin.snmpv) {
          this.$set(param.snmp_trap, 'version', setData.plugin.snmpv.split('_')[1])
        }
      }
      pluginData.configJson.forEach((item) => {
        if (setData.collectType === 'SNMP_Trap') {
          // SNMP_Trap 用 item.key 作为键名
          if (setData.plugin.snmpv === 'snmp_v3') {
            if (item.auth_json) {
              param.snmp_trap.auth_info = []
              item.auth_json.forEach((items, index) => {
                param.snmp_trap.auth_info.push({})
                items.forEach((item) => {
                  param.snmp_trap.auth_info[index][item.key] = item.default
                })
              })
            } else {
              param.snmp_trap[item.key] = item.default
            }
          } else {
            param.snmp_trap[item.key] = item.default
          }
        } else {
          if (item.mode === 'collector') {
            // mode='collector' 时，将用户填写的运行参数存在 `param.collector` 对象中
            collector[item.name] = item.default
          } else {
            // 否则，存在 `param.plugin` 对象中
            plugin[item.name] = item.default
            if (item.type === 'file') {
              plugin[item.name] = {
                filename: item.default,
                file_base64: item.file_base64
              }
            }
          }
        }
      })
      if (setData.collectType === 'Log') {
        param.log = setData.log
      } else if (setData.collectType === 'Process') {
        param.process = setData.process
      }
      if (setData.isShowHost) { // 绑定主机
        collector[setData.host.name] = setData.host.default
      }
      if (setData.isShowPort) { // 绑定端口
        collector[setData.port.name] = setData.port.default
      }

      const params = {
        name: setData.name,
        bk_biz_id: setData.bizId,
        collect_type: setData.collectType,
        target_object_type: setData.objectType,
        plugin_id: pluginData.id,
        params: param,
        label: setData.objectId,
        target_node_type: selectData.targetNodeType,
        target_nodes: selectData.targetNodes,
        remote_collecting_host: remoteCollectingHost?.ip ? {
          ip: remoteCollectingHost.ip,
          is_collecting_only: remoteCollectingHost.isCollectingOnly,
          bk_cloud_id: remoteCollectingHost.bkCloudId,
          bk_supplier_id: remoteCollectingHost.bkSupplierId
        } : null
      }
      if (this.config.mode === 'edit' && setData.id) { // 编辑时，增加 `id` 字段
        params.id = setData.id
      }
      return params
    },
    getSnmpParams() {
      const setData = this.config.set.data
      const pluginData = setData.plugin
      const selectData = this.info
      const { remoteCollectingHost } = selectData
      const { configJson } = pluginData

      const param = {
        collector: {
          period: setData.period
        },
        plugin: {}
      }
      const configJsonList = configJson.reduce((total, cur) => {
        if (cur.auth_json) {
          total.push(...cur.auth_json[0])
        } else {
          total.push(cur)
        }
        return total
      }, [])
      configJsonList.forEach((item) => {
        if (item.mode === 'collector') {
          param.collector[item.key] = item.default
        } else {
          param.plugin[item.key] = item.default
        }
      })
      const params = {
        name: setData.name,
        bk_biz_id: setData.bizId,
        collect_type: setData.collectType,
        target_object_type: setData.objectType,
        plugin_id: pluginData.id,
        params: param,
        label: setData.objectId,
        target_node_type: 'INSTANCE',
        remote_collecting_host: remoteCollectingHost?.ip ? {
          ip: remoteCollectingHost.ip,
          is_collecting_only: remoteCollectingHost.isCollectingOnly,
          bk_cloud_id: remoteCollectingHost.bkCloudId,
          bk_supplier_id: remoteCollectingHost.bkSupplierId
        } : null,
        target_nodes: this.snmpTargets.map(item => ({
          ip: item,
          bk_cloud_id: 0,
          bk_supplier_id: 0
        }))
      }
      if (this.config.mode === 'edit' && setData.id) { // 编辑时，增加 `id` 字段
        params.id = setData.id
      }
      return params
    },
    //  保存配置接口
    saveConfig(params) {
      this.loading = true
      return saveCollectConfig(params)
    },
    handleShowSelector() {
      this.selectHostConf.isShow = true
    },
    handleHostConfirm(v) {
      const { remoteCollectingHost } = this.info
      remoteCollectingHost.ip = v.ip
      remoteCollectingHost.bkCloudId = v.cloudId
      remoteCollectingHost.bkSupplierId = 0
    },
    handleData(data) {
      const { remoteCollectingHost } = data
      return {
        isUseRemoteHost: remoteCollectingHost !== null,
        targetNodeType: data.targetNodeType,
        remoteCollectingHost: remoteCollectingHost
          ? {
            ip: remoteCollectingHost.ip,
            bkCloudId: remoteCollectingHost.bk_cloud_id,
            bkSupplierId: remoteCollectingHost.bk_supplier_id,
            isCollectingOnly: remoteCollectingHost.is_collecting_only
          }
          : {
            ip: '',
            bkCloudId: '',
            bkSupplierId: '',
            isCollectingOnly: true
          },
        targetNodes: data.targetNodes
      }
    },
    // 获取主机
    getHost() {
      return hostAgentStatus()
    },
    // 分静态和动态拓扑
    handleCheckedData(type, data) {
      const checkedData = []
      if (['static-ip', 'static-topo'].includes(type)) {
        data.forEach((item) => {
          checkedData.push({
            ip: item.ip,
            bk_cloud_id: item.bkCloudId,
            bk_supplier_id: item.bkSupplierId
          })
        })
      } else {
        data.forEach((item) => {
          checkedData.push({
            bk_inst_id: item.bkInstId,
            bk_obj_id: item.bkObjId
          })
        })
      }
      return checkedData
    },
    handleClearIp() {
      this.info.remoteCollectingHost.ip = ''
    },
    // 远程主机搜索筛选
    searchFn(keyWord, data) {
      return keyWord ? data.filter(item => item.ip.indexOf(keyWord) > -1) : data
    },
    handleSnmpTargetChange(valueList) {
      // eslint-disable-next-line no-restricted-syntax
      for (const item of valueList) {
        // ipv4
        const reg = /^((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]).){3}(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(?::(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$/ // eslint-disable-line
        if (!reg.test(item)) {
          this.$bkMessage({ theme: 'error', message: this.$t('请输入正确的IP地址') })
          this.$nextTick(() => {
            const i = this.snmpTargets.findIndex(item => !reg.test(item))
            this.snmpTargets.splice(i, 1)
          })
          break
        }
      }
    },
    handleTargetsPaste(v) {
      const res = v.replace(/[,;\s]/g, ',').split(',')
        .filter(item => !!item && this.ipv4Reg.test(item))
      this.snmpTargets.push(...res)
      return []
    }
  }
}
</script>

<style lang="scss" scoped>
    .config-select {
      display: flex;
      flex-direction: column;
      padding: 41px 60px;
      height: 100%;
      .select-container {
        flex: 1;
        .select-tips {
          display: flex;
          color: #63656e;
          margin-bottom: 15px;
          i {
            color: #979ba5;
            font-size: 16PX;
            margin-right: 6px;
          }
        }
        .static-ip-table {
          .col-status {
            &.success {
              color: #2dcb56;
            }
            &.error {
              color: #ea3636;
            }
            &.not-exist {
              color: #c4c6cc;
            }
          }
        }
        .dynamic-topo-table {
          .col-label {
            .col-label-container {
              display: inline-flex;
              align-items: center;
              background: #fff;
              border-radius: 2px;
              border: 1px solid #dcdee5;
              font-size: 12px;
              .col-label-key {
                height: 24px;
                line-height: 24px;
                background: #fafbfd;
                padding: 0 10px;
              }
              .col-label-value {
                height: 24px;
                line-height: 24px;
                border-left: 1px solid #dcdee5;
                padding: 0 10px;
              }
            }
          }
        }
      }
      .remote-container {
        margin-top: 51px;
        .remote-hint {
          height: 24px;
          display: inline-flex;
          align-items: center;
          /deep/ .bk-switcher.is-checked {
            background: #3a84ff;
          }
          .hint-text {
            color: #63656e;
            margin-left: 10px;
          }
          .hint-icon {
            margin-left: 4px;
            font-size: 16px;
            color: #979ba5;
            cursor: pointer;
          }
        }
        .remote-host {
          margin-top: 10px;
          display: flex;
          .host-input {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 9px 0 20px;
            height: 42px;
            width: 100%;
            border: 1px solid #dcdee5;
            cursor: pointer;
            .host-placeholder {
              color: #c4c6cc;
            }
            span {
              height: 42px;
              line-height: 42px;
            }
            i {
              color: #c4c6cc;
            }
            &:hover {
              border: 1px solid #3a84ff;
            }
          }
          .host-pro {
            display: flex;
            align-items: center;
            min-width: 171px;
            height: 42px;
            line-height: 42px;
            text-align: center;
            border: 1px solid #dcdee5;
            border-left: 0;
            background: #fafbfd;
            border-radius: 0px 1px 1px 0px;
            .pro-checkbox {
              margin-left: 26px;
            }
            /deep/ .bk-checkbox-text {
              margin-left: 9px;
              font-size: 12px;
              color: #63656e;
            }
            .host-hint-icon {
              margin-left: 4px;
              font-size: 16px;
              color: #979ba5;
              cursor: pointer;
            }
          }
        }
      }
      .is-snmp {
        margin-top: 20px;
      }
      .btn-container {
        margin-top: 20px;
        font-size: 0;
        .btn-previous,
        .btn-delivery {
          margin-right: 10px;
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
