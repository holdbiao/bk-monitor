<template>
  <div class="step-test">
    <!-- 编辑时的提示 -->
    <div class="hint-container" v-if="isShowSkipDebugHint">
      <i class="icon-monitor icon-tips"></i>
      {{ $t('本次对插件的编辑并不影响目标机器的部署内容，所以可以跳过调试阶段直接进行保存，当然再次测试确认是最好的。') }}
    </div>
    <!-- 只有Export有绑定端口和绑定主机     绑定端口可以修改，需要校验      绑定主机是disable状态 -->
    <div class="input-container">
      <div v-if="info.plugin_type === 'Exporter'">
        <div class="step-test-item">
          <div class="item-label item-required">{{ $t('绑定端口') }}</div>
          <div class="item-content">
            <div class="item-param" :class="{ 'input-verify': rules.port.validate }">
              <bk-popover placement="top" :tippy-options="tippyOptions" class="icon-popover">
                <i class="icon-monitor icon-mind-fill" v-show="rules.port.validate"></i>
                <div slot="content">
                  {{ rules.port.message }}
                </div>
              </bk-popover>
              <div class="item-param-name">${port}=</div>
              <verify-input :show-validate.sync="rules.port.validate" :validator="{ content: '' }">
                <bk-input v-model="info.port" class="item-param-input" @blur="validatePort(info.port, 'port')"></bk-input>
              </verify-input>
            </div>
          </div>
        </div>
        <div class="step-test-item">
          <div class="item-label item-label-norequired"> {{ $t('绑定主机') }} </div>
          <div class="item-content">
            <div class="item-param readonly-container">
              <div class="item-param-name">${host}=</div>
              <bk-input v-model="info.url" class="item-param-input" readonly></bk-input>
            </div>
          </div>
        </div>
      </div>
      <!-- 填写参数 -->
      <div class="step-test-item param-item" style="margin-bottom: 10px;">
        <div class="item-label item-label-norequired">{{ $t('填写参数') }}</div>
        <div class="item-content param-container" v-if="isShowParam">
          <template v-for="(item, index) in paramsList">
            <div class="item-param" v-if="!item.hasOwnProperty('visible') && !item.disabled" :key="index" :class="{ 'input-verify': item.isError }">
              <bk-popover placement="top" :tippy-options="tippyOptions" class="icon-popover">
                <i class="icon-monitor icon-mind-fill" v-show="item.isError"></i>
                <div slot="content">
                  {{ item.errorMessage }}
                </div>
              </bk-popover>
              <div class="item-param-name">
                <bk-popover placement="top-start" :tippy-options="tippyOptions">
                  <div :class="{ 'verify-name': item.required }">{{item.name || item.description}}</div>
                  <div slot="content">
                    <div>{{ $t('类型：') }} {{ paramType[item.mode] }}</div>
                    <div>{{ $t('说明：') }} {{ item.description || '--' }}</div>
                  </div>
                </bk-popover>
              </div>
              <!-- 旧代码 -->
              <template v-if="false">
                <!-- 插件类型是JMX 参数是端口时需要校验 -->
                <verify-input v-if="['JMX', 'SNMP'].includes(info.plugin_type) && (item.name === 'port' || item.key === 'port')"
                              :show-validate.sync="rules.snmpPort.validate" :validator="{ content: '' }">
                  <bk-input :placeholder="$t('请输入参数值')" :class="['item-param-input', { 'value-password': item.type === 'password' }]" v-model="item.default"
                            :type="item.type === 'password' ? 'password' : 'text'" @blur="validatePort(item.default, info.plugin_type === 'SNMP' ? 'snmpPort' : 'jmxPort')"></bk-input>
                </verify-input>
                <!-- 其他情况不需要校验 -->
                <bk-input v-else :placeholder="$t('请输入参数值')" :class="['item-param-input', { 'value-password': (item.type === 'password' || item.type === 'encrypt') }]" v-model="item.default" :type="(item.type === 'password' || item.type === 'encrypt') ? 'password' : 'text'"></bk-input>
              </template>
              <!-- 开关 -->
              <div class="switch-wrap" v-else-if="item.type === 'switch'">
                <bk-switcher
                  true-value="true"
                  false-value="false"
                  v-model="item.default">
                </bk-switcher>
              </div>
              <!-- 文件 -->
              <div v-else-if="item.type === 'file'" class="file-wrap">
                <import-file
                  style="border: 0;"
                  :file-name="item.default"
                  :file-content="item.file_base64"
                  @error-message="msg => handleImportError(msg, item)"
                  @change="file => handleFileChange(file, item)">
                </import-file>
              </div>
              <div v-else class="item-param-content">
                <bk-select class="params-select" v-if="item.type === 'list'" v-model="item.default" :clearable="false" @change="handelParamsSelect(item)">
                  <bk-option v-for="(option, i) in item.election" :key="i" :id="option.id" :name="option.name" :disabled="option.disabled"></bk-option>
                </bk-select>
                <bk-input
                  :class="{ 'value-password': (item.type === 'password' || item.type === 'encrypt') }"
                  v-if="item.type === 'text' || item.type === 'password' || item.type === 'encrypt'"
                  :placeholder="$t('请输入参数值')" v-model="item.default"
                  :type="item.type === 'password' || item.type === 'encrypt' ? 'password' : 'text'"
                  @blur="handleValidate(item)">
                </bk-input>
              </div>
            </div>
          </template>
        </div>
        <!-- 未定义参数时的提示 -->
        <div class="item-content no-param" v-else>
          <i class="icon-monitor icon-hint param-icon"></i>
          <span class="param-text">{{ $t('由于插件定义时未定义参数，此处无需填写。') }}</span>
        </div>
      </div>
      <!-- 数据抓取周期 -->
      <div class="step-test-item">
        <div class="item-label item-required">{{ $t('数据抓取周期') }}</div>
        <div class="item-content">
          <bk-select class="cycle-select" v-model="info.cycle" :clearable="false" width="180">
            <bk-option
              v-for="item in cycleList"
              :key="item.code"
              :id="item.code"
              :name="item.name">
            </bk-option>
          </bk-select>
        </div>
      </div>
      <!-- 采集目标 -->
      <div class="step-test-item" v-if="info.plugin_type === 'SNMP'">
        <div class="item-label item-required">{{ $t('采集目标') }}</div>
        <div class="item-content">
          <bk-tag-input
            style="width: 940px;"
            v-model="snmpTargets"
            :placeholder="$t('请输入采集目标主机')"
            :allow-create="true"
            :allow-auto-match="true"
            :has-delete-icon="true"
            :paste-fn="handleTargetsPaste"
            @change="handleSnmpTargetChange">
          </bk-tag-input>
        </div>
      </div>
      <!-- 选择调试目标 -->
      <div class="step-test-item host-item" style="margin-bottom: 10px;">
        <div class="item-label item-required item-label-host"> {{ $t('选择调试目标') }} </div>
        <div class="item-content param-container">
          <div class="host-container" v-for="(item, index) in info.host_info" :key="index" @click="debugStatus !== 'debugging' && selectHost(item, index)">
            <span class="item-icon icon-arm" v-if="item.osType === 'linux_aarch64'">ARM</span>
            <i v-else :class="['item-icon icon-monitor', `icon-${item.osType}`]"></i>
            <div class="item-host-ip">
              <span v-if="item.ip">{{ item.ip }}</span>
              <span v-else class="item-placeholder">{{ $t('点击选择测试目标') }}</span>
            </div>
            <i v-show="item.ip"
               :class="{ 'bk-icon': true, 'icon-close-circle-shape clear-icon': item.ip }"
               @click.stop="!(debugStatus === 'debugging' && !canShowMetricDialog) && handleClearIp(item)">
            </i>
          </div>
        </div>
      </div>
      <!-- 调试进度 -->
      <div class="step-test-item" v-show="isShowDebug" style="height: 342px;">
        <div class="item-label item-label-norequired"> {{ $t('调试进度') }} </div>
        <div class="item-content">
          <div class="debug-container">
            <div class="tabs-container">
              <ul class="debug-tabs">
                <template v-for="(item, index) in debugHostList">
                  <li v-if="item.ip" :class="['debug-tab', { 'debug-active': item.osType === activeTab }]" :key="index" @click="changeTab(index)">
                    <div class="tab-title">
                      <span class="title-icon-logo icon-arm" v-if="item.osType === 'linux_aarch64'">ARM</span>
                      <i v-else :class="['icon-monitor title-icon-logo', `icon-${item.osType}`]"></i>
                      <span class="title-text">{{item.ip}}</span>
                      <img src="../../../../static/images/svg/spinner.svg" v-if="item.status === 3" />
                      <i class="bk-icon icon-exclamation-circle-shape status-exception title-icon-status" v-else-if="item.status === 2"></i>
                      <div class="process-status" v-else-if="item.status === 1">
                        <span class="process-status-bar bar-1"></span>
                        <span class="process-status-bar bar-2"></span>
                        <span class="process-status-bar bar-3"></span>
                      </div>
                    </div>
                    <!-- 调试命令行 -->
                    <div v-show="item.osType === activeTab" :class="['debug-preview', { 'active': item.osType === activeTab }]" :style="{ position: 'absolute', left: `-${index * 180 + 1}px` }">
                      <terminal-instance :consoles="item.data" :animation="false"></terminal-instance>
                    </div>
                  </li>
                </template>
              </ul>
            </div>
            <!-- 指标维度选择器和抓取限时 -->
            <div class="debug-desc">
              <div class="desc-set-montior" :class="{ 'montior-active': canShowMetricDialog }" @click="handleChaneDialogStatus">{{ $t('设置指标&维度') }}</div>
              <div class="desc-text"> {{ $t('数据抓取限时') }} <span class="desc-time">600</span> {{$t('秒')}}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="opeartor-container">
      <bk-button class="reset-btn mc-btn-add" @click="previous"> {{ $t('上一步') }} </bk-button>
      <bk-button class="reset-btn mc-btn-add"
                 :theme="isFirstDebug ? 'success' : 'default'"
                 v-show="debugStatus === 'setting' || debugStatus === 'finish'"
                 :disabled="debugLoading || !canStartDebug" @click="startDebug">
        {{isFirstDebug ? $t('开始调试') : $t('重新调试')}}
      </bk-button>
      <bk-button class="reset-btn btn-debugging mc-btn-add" v-show="debugStatus === 'debugging'"> {{ $t('调试中') }} </bk-button>
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH }"
        class="mc-btn-add"
        theme="primary"
        :disabled="!canSavePlugin"
        @click="authority.MANAGE_AUTH ? savePlugin() : handleShowAuthorityDetail()">
        {{ $t('保存') }}
      </bk-button>
    </div>
    <!-- 选择主机的dialog组件 -->
    <select-host :conf.sync="hostConf" @confirm="handleSelectHostConfirm"></select-host>
    <!-- 指标/维度选择器 -->
    <monitor-dialog
      :class="navToggle ? 'nav-on' : 'nav-off'"
      :value.sync="showMetricDialog"
      :full-screen="true"
      :need-footer="false"
      :need-header="false">
      <metric-dimension
        :data-time="dataTime"
        :os-type-list="osTypeList"
        :metric-json="metricData"
        :plugin-data="pluginData"
        :is-token="isToken"
        :is-from-home="false"
        @close-dialog="handleChaneDialogStatus"
        @refresh-data="handleRefreshData"
        @change-version="handleChangeVersion"
        @back-plugin="previous">
      </metric-dimension>
    </monitor-dialog>
  </div>
</template>
<script>
import SelectHost from './components/select-host'
import TerminalInstance from '../terminal-instance/terminal-instance'
import MonitorDialog from '../../../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import MetricDimension from './metric-dimension/metric-dimension-dialog.vue'
import { startDebugCollectorPlugin,
  stopDebugCollectorPlugin,
  fetchDebugLogCollectorPlugin } from '../../../../../monitor-api/modules/model'
import VerifyInput from './verify-input'
import formLabelMixin from '../../../../mixins/formLabelMixin'
import ImportFile from './components/import-file'
export default {
  name: 'StepSetTest',
  components: {
    SelectHost,
    TerminalInstance,
    VerifyInput,
    MetricDimension,
    MonitorDialog,
    ImportFile
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  mixins: [formLabelMixin],
  props: {
    data: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      left: 180, // tab 宽度
      paramIndex: -1,
      metricData: [{
        table_name: 'Base',
        table_desc: this.$t('默认分组'),
        fields: []
      }],
      pluginData: {},
      showMetricDialog: false,
      isFirstDebug: true,
      debugLoading: false,
      debugStatus: 'setting', // 调试状态：'setting'-设置中，'debugging'-调试中，'finish'-调试完毕
      hostConf: {},
      info: {
        collector_json: {},
        config_json: [], // 填写的参数
        description_md: '',
        logo: '',
        metric_json: [],
        plugin_display_name: '',
        plugin_id: '',
        plugin_type: '', // 插件类型
        tag: '',
        port: '', // 绑定端口
        url: '', // 绑定主机
        cycle: '10', // 数据抓取周期
        config_version: '',
        info_version: '',
        host_info: [] // 调试目标
      },
      dataTime: '', // 数据时间
      rules: {
        port: {
          validate: false,
          message: ''
        },
        jmxPort: {
          validate: false,
          message: ''
        },
        snmpPort: {
          validate: false,
          message: ''
        }
      },
      cycleList: [ // 数据抓取周期
        { code: '10', name: this.$t('10秒') },
        { code: '20', name: this.$t('20秒') },
        { code: '30', name: this.$t('30秒') },
        { code: '60', name: this.$t('1分钟') },
        { code: '120', name: this.$t('2分钟') },
        { code: '300', name: this.$t('5分钟') }
      ],
      activeTab: '',
      paramType: {
        collector: this.$t('采集器参数'),
        opt_cmd: this.$t('命令行参数'),
        pos_cmd: this.$t('位置参数'),
        env: this.$t('环境变量参数'),
        listen_cmd: this.$t('监听参数')
      },
      tippyOptions: {
        distance: 0
      },
      snmpTargets: [],
      paramsList: [],
      ipv4Reg: /^((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]).){3}(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(?::(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$/ // eslint-disable-line
    }
  },
  computed: {
    //  能否开始调试
    canStartDebug() {
      const { info } = this
      const isPortOk = info.plugin_type === 'Exporter'
        ? info.port !== '' && !this.rules.port.validate : true // Exporter 类型需要校验端口
      // const isCycleOk = info.cycle !== ''
      const isHostOk = info.host_info.some(item => item.ip)
      const isTargetOk = info.plugin_type === 'SNMP' ? this.snmpTargets.length : true
      // const rules = !this.rules.port.validate && !this.rules.jmxPort.validate
      // const isOk = isPortOk && isCycleOk && isHostOk && rules
      const isOk = this.paramsList.every(item => (item.required ? !!item.default && !item.isError : true))
      //   const isFileOk = this.info.config_json.every(item => !item.error)
      return isOk && isHostOk && isTargetOk && isPortOk
    },
    //  能否弹出指标窗口
    canShowMetricDialog() {
      return this.info.host_info.some(item => item.isDebug && item.status === 1)
    },
    //  是否显示跳过调试的 hint
    isShowSkipDebugHint() {
      return !this.data.need_debug
    },
    //  能否保存插件
    canSavePlugin() {
      // 1. 已经勾选提示
      // 2. 状态是"FATCH_DATA",并且metric_json有数据
      return this.canShowMetricDialog || this.isShowSkipDebugHint
    },
    //  是否显示参数
    isShowParam() {
      return !!this.info.config_json.find(item => !Object.prototype.hasOwnProperty.call(item, 'visible'))
    },
    //  是否显示调试
    isShowDebug() {
      return ['debugging', 'finish'].includes(this.debugStatus) && this.info.host_info.some(item => item.ip !== '')
    },
    //  操作系统列表
    osTypeList() {
      return this.info.host_info.map(item => item.osType)
    },
    isToken() {
      return !!this.data.token
    },
    debugHostList() {
      return this.info.host_info.filter(item => item.ip)
    },
    // 导航状态
    navToggle() {
      return this.$store.getters.navToggle
    }
  },
  watch: {
    canShowMetricDialog(newV) {
      if (newV) {
        if (this.info.isEdit && this.info.status !== 'draft') {
          this.handleMergeEditData()
        } else {
          this.metricData[0].fields = this.handleMergeData()
        }
        this.showMetricDialog = true
      }
    }
  },
  mounted() {
    this.initFormLabelWidth()
  },
  activated() {
    if (this.data.from === 'plugin') { // 从插件编辑的【下一步】按钮进来，读取上一步的数据
      this.debugStatus = 'setting'
      this.handleData(this.data)
      this.handleParamsList()
    }
  },
  deactivated() {
    this.clearTimer()
  },
  beforeDestroy() {
    this.clearTimer()
  },
  methods: {
    handleParamsList() {
      // if (this.info.plugin_type === 'SNMP') {
      const list = []
      this.info.config_json.reduce((total, cur) => {
        if (cur.auth_json) {
          total.push(...cur.auth_json)
        } else {
          total.push(cur)
        }
        return total
      }, list)
      list.map((item) => {
        item.disabled = false
        item.type === 'list' && (item.election = item.election.map((option) => {
          if (typeof option === 'object') return option
          return {
            id: option,
            name: option,
            disabled: false
          }
        }))
        this.$set(item, 'isError', false)
        this.$set(item, 'errorMessage', '')
        if (item.key === 'port' || item.name === 'port') {
          item.rules = [
            { validate: this.validatePortRules, message: this.$tc('请输入合法的端口') }
          ]
          item.required = true
        }
        return item
      })
      const securityLevel = list.find(item => item.key === 'security_level')
      list.forEach((item) => {
        // snmp v3 必选参数
        if (this.info.plugin_type === 'SNMP' && +this.info.collector_json?.snmp_version === 3) { // eslint-disable-line
          const securityLevelValue = securityLevel.default || null
          let excludes = [] // 非必选选项列表
          let disabledIncludes = [] // 不需要参数
          if (securityLevelValue === 'authPriv') {
            // 安全级别为 authpriv :除 上下文名称 所有都要必填
            excludes = ['context_name']
            if (item.key === 'authentication_protocol') {
              const includes = ['MD5', 'SHA', 'DES', 'AES']
              item.election.forEach(el => el.disabled = !includes.includes(el.id))
            }
          } else if (securityLevelValue === 'authNoPriv') {
            // 安全级别为 authnopriv :除 上下文名称 私钥 和 隐私协议 所有都要必填
            excludes = ['context_name', 'privacy_passphrase', 'privacy_protocol']
            disabledIncludes = ['privacy_passphrase', 'privacy_protocol']
            if (item.key === 'authentication_protocol') {
              const includes = ['MD5', 'SHA']
              item.election.forEach(el => el.disabled = !includes.includes(el.id))
            }
          } else if (securityLevelValue === 'noAuthNoPriv') {
            // 安全级别为 noauthnopriv :除 上下文名称 验证协议 验证口令 隐私协议 私钥 所有都要必填
            excludes = [
              'context_name',
              'authentication_protocol',
              'authentication_passphrase',
              'privacy_protocol',
              'privacy_passphrase'
            ]
            disabledIncludes = [
              'privacy_passphrase',
              'privacy_protocol',
              'authentication_passphrase',
              'authentication_protocol'
            ]
          }
          item.required = !excludes.includes(item.key)
          disabledIncludes.includes(item.key) && (item.disabled = true)
          // 默认值
          if (item.key === 'authentication_protocol' || item.key === 'privacy_protocol') item.default = 'AES'
        } else if ([1, 2].includes(+this.info.collector_json?.snmp_version)) { // eslint-disable-line
          item.required = true
        }
      })
      this.paramsList = list
      // } else {
      //   this.paramsList = this.info.config_json
      // }
    },
    handelParamsSelect(item) {
      // 安全级别
      if (item.key === 'security_level') {
        this.handleParamsList()
      }
    },
    handleValidate(item) {
      if (item.required && `${item.default}`.trim() === '') {
        item.isError = true
        item.errorMessage = this.$t('必填项')
      } else {
        item.isError = false
        item.errorMessage = ''
      }
      if (item.rules) {
        const res = item.rules.find(rulesItem => !rulesItem.validate(item.default))
        item.isError = !!res
        item.errorMessage = res ? res.message : ''
      }
    },
    handleSnmpTargetChange(valueList) {
      for (const item of valueList) {
        // ipv4
        if (!this.ipv4Reg.test(item)) {
          this.$bkMessage({ theme: 'error', message: this.$t('请输入正确的IP地址') })
          this.$nextTick(() => {
            const i = this.snmpTargets.findIndex(item => !this.ipv4Reg.test(item))
            this.snmpTargets.splice(i, 1)
          })
          break
        }
      }
    },
    handleChangeVersion(data) {
      if (data?.token) {
        this.$set(this.data, 'token', data.token)
      }
      if (data) {
        this.$set(this.data, 'config_version', data.config_version)
        this.$set(this.data, 'info_version', data.info_version)
      }
    },
    //  处理数据
    handleData(data) {
      const { info } = this
      info.host_info = []
      const pluginInfo = this.deepCopy(data)
      this.pluginData = {
        plugin_id: pluginInfo.plugin_id,
        plugin_type: pluginInfo.plugin_type,
        config_version: pluginInfo.config_version,
        info_version: pluginInfo.info_version
      }
      Object.keys(pluginInfo).forEach((item) => {
        info[item] = pluginInfo[item]
      })
      // 处理 `pluginInfo.systemList`，并赋值给 `info.host_info`
      pluginInfo.systemList.forEach((item) => {
        info.host_info.push({
          osName: item.os_type,
          osType: item.os_type,
          osTypeId: item.os_id,
          cloudId: '',
          companyId: '',
          ip: '',
          taskId: '',
          timer: null,
          status: 0,
          isDebug: false,
          data: [],
          showInput: false
        })
      })
    },
    //  选择主机
    selectHost(info, index) {
      this.hostConf = {
        isShow: true,
        id: this.$store.getters.bizId,
        param: { ...info, index }
      }
    },
    //  处理主机dialog confirm 事件
    handleSelectHostConfirm(host) {
      this.$set(this.info.host_info, host.index, host)
    },
    //  打开/关闭指标窗口
    handleChaneDialogStatus() {
      if (this.canShowMetricDialog) {
        this.showMetricDialog = !this.showMetricDialog
      }
    },
    //  合并每种操作系统获取到的指标/维度
    handleMergeData() {
      this.dataTime = this.info.lastTime ? this.info.lastTime : this.$t('暂时无数据')
      const hostInfo = this.info.host_info
      //  合并各种操作系统的数据到arr
      const arr = []
      hostInfo.forEach((host) => {
        if (host.metricJson) {
          host.metricJson.forEach((item) => {
            const metric = this.getNewRow('metric', item.metric_name, item.metric_value, host.osType)
            item.dimensions.forEach((el) => {
              arr.push(this.getNewRow('dimension', el.dimension_name, el.dimension_value, host.osType))
              metric.dimensions.push(el.dimension_name)
            })
            arr.push(metric)
          })
        }
      })
      //  把不同操作系统的相同指标/维度的Value合并在一起
      const newArr = []
      arr.forEach((item) => {
        const newItem = newArr.find(el => el.name === item.name)
        if (newItem) {
          newItem.value[item.osType] = item.value[item.osType]
        } else {
          newArr.push(item)
        }
      })
      return newArr
    },
    //  刷新数据
    handleRefreshData(tableData) {
      const newData = this.handleMergeData()
      //  把所有分组里面的指标/维度的名字整合
      let allName = []
      tableData.forEach((group, index) => {
        const res = group.fields.map(item => ({ name: item.name, groupIndex: index }))
        allName = [...allName, ...res]
      })
      //  把新增的指标/维度放进默认分组，并刷新 指标维度关联表(dimensions: [])
      newData.forEach((item) => {
        const newItem = allName.find(el => el.name === item.name)
        if (newItem) {
          tableData[newItem.groupIndex].fields.forEach((el) => {
            if (el.name === item.name) {
              el.dimensions = item.dimensions
            }
          })
        } else {
          tableData[0].fields.push(item)
        }
      })
      this.metricData = JSON.parse(JSON.stringify(tableData))
    },
    //  合并编辑的数据
    handleMergeEditData() {
      const metricJson = this.data.metric_json
      //  如果是没结构的空数组，创建基础结构
      if (metricJson.length === 0) {
        metricJson.push({
          table_name: 'Base',
          table_desc: this.$t('默认分组'),
          fields: []
        })
      } else {
        metricJson.forEach((group) => {
          group.fields.forEach((item) => {
            item.showInput = false
            item.isCheck = false
            item.isDel = true
            item.value = {
              linux: null,
              windows: null,
              aix: null
            }
            if (item.monitor_type === 'metric') {
              item.order = 1
            } else {
              item.order = 3
            }
          })
        })
      }
      //  把之前的指标/维度和这次调试的指标/维度整合
      const newData = this.handleMergeData()
      let allName = []
      metricJson.forEach((group, index) => {
        const res = group.fields.map(item => ({ name: item.name, groupIndex: index, sourceName: item.source_name }))
        allName = [...allName, ...res]
      })
      newData.forEach((item) => {
        const newItem = allName.find(el => el.name === item.name || el.sourceName === item.name)
        if (!newItem) {
          metricJson[0].fields.push(item)
        } else {
          metricJson[newItem.groupIndex].fields.forEach((one) => {
            if (one.name === item.name) {
              one.value = item.value
            }
          })
        }
      })
      this.metricData = JSON.parse(JSON.stringify(metricJson))
    },
    //  生成指标/维度的平铺数据
    getNewRow(type, name, value, osType) {
      const item = {
        monitor_type: type, //  指标
        name, //  英文名
        description: '', //  别名
        source_name: '', //  原指标名
        value: { //  数据预览值
          linux: null,
          windows: null,
          aix: null
        },
        showInput: false,
        is_active: true, //  是否启用
        is_diff_metric: false, //  是否差值指标
        isCheck: false, //  是否勾选
        isDel: false, //  能否删除
        isFirst: true, //  是否默认获取
        errValue: false, //  是否重名
        reValue: false, //  是否关键字冲突
        descReValue: false, //  别名是否重名
        osType //  操作系统类型
      }
      item.value[osType] = value
      if (type === 'metric') {
        item.order = 0
        item.dimensions = []
        item.type = 'double' //  类型
        item.unit = 'none' //  单位
      } else {
        item.order = 2
        item.type = 'string'
        item.unit = '--'
      }
      return item
    },
    //  获取Debug的参数
    getDebugParams() {
      const { info } = this
      const configJson = this.paramsList
      const pluginType = info.plugin_type
      const params = {
        plugin_id: info.plugin_id,
        info_version: info.info_version,
        config_version: info.config_version,
        param: {
          collector: {
            period: info.cycle
          },
          plugin: {}
        }
      }
      const { collector, plugin } = params.param
      if (pluginType === 'Exporter') {
        collector.host = info.host
        collector.port = info.port.trim()
      } else if (pluginType === 'JMX') {
        const portParam = configJson.find(item => item.name === 'port') || {}
        collector.port = portParam.default.trim() || ''
      }
      configJson.forEach((item) => {
        if (pluginType === 'Pushgateway' && item.mode === 'collector') {
          collector[item.name] = this.getItemParam(item)
        } else if (pluginType === 'Pushgateway' && item.mode !== 'collector') {
          plugin[item.name] = this.getItemParam(item)
        } else if (pluginType === 'JMX' && item.name !== 'host' && item.name !== 'port') {
          plugin[item.name] = item.default.trim()
        } else if (pluginType === 'SNMP') {
          const temp = item.mode === 'collector' ? collector : plugin
          temp[item.key] = item.default.trim()
          params.target_nodes = this.snmpTargets.map(item => ({ ip: item, bk_cloud_id: 0, bk_supplier_id: 0 }))
        } else if (pluginType !== 'JMX' && !Object.prototype.hasOwnProperty.call(item, 'visible')) {
          plugin[item.name] = this.getItemParam(item)
        }
      })
      return params
    },
    getItemParam(item) {
      const isFile = item.type === 'file'
      if (isFile) {
        return {
          filename: item.default,
          file_base64: item.file_base64,
          type: item.type
        }
      }
      return item.default.trim()
    },
    //  开始调试
    startDebug() {
      this.debugLoading = true
      const params = this.getDebugParams()
      this.isSelectedTip = this.isSelectedTip || false
      this.info.host_info.forEach(async (item) => {
        // 只对选择了主机的操作系统  status： 1成功  2失败  3调试中
        if (item.ip) {
          if (item.taskId && item.status === 1) { // 如果已经调试，则需先停止
            clearTimeout(item.timer)
            item.timer = null
            await this.stopDebug(item.taskId)
            item.taskId = ''
          }
          this.getTaskId({
            ...params,
            host_info: {
              bk_cloud_id: item.cloudId,
              ip: item.ip,
              bk_biz_id: item.bk_biz_id
            }
          }).then((data) => {
            const taskId = data.task_id
            item.isDebug = true
            item.status = 3 // 调试中
            item.taskId = taskId
            item.timeOut = 2
            this.isFirstDebug = false
            this.handleDebugLog(taskId, 2000)
            !this.activeTab && this.changeTab(0)
            if (this.debugStatus !== 'debugging') {
              this.debugStatus = 'debugging'
            }
          })
            .finally(() => {
              this.debugLoading = false
            })
        }
      })
    },
    //  处理调试日志
    async handleDebugLog(taskId) {
      const host = this.info.host_info.find(item => item.taskId === taskId)
      if (host) {
        // 处理后台返回的结果
        const data = await this.requestDebugLog(taskId).catch(() => {
          this.debugLoading = false
        })
        const { status } = data
        const text = data.log_content
        if (status === 'INSTALL') { // 部署中
          this.changeDebugLog(host, 3, text)
          host.timer = setTimeout(this.handleDebugLog, 2000, taskId)
        } else if (status === 'FETCH_DATA') { // 抓取数据中
          if (data.metric_json.length) {
            this.changeDebugLog(host, 1, text)
            host.metricJson = data.metric_json
            this.info.lastTime = data.last_time
            host.timeOut += 2
            if (host.timeOut > 180) {
              await this.stopDebug(taskId)
            }
            this.setDebugStatus()
          } else {
            this.changeDebugLog(host, 3, text)
            if (host.timeOut > 20) {
              this.setDebugStatus()
            }
          }
          host.timer = setTimeout(this.handleDebugLog, 2000, taskId)
        } else { // 成功或失败
          this.changeDebugLog(host, status === 'SUCCESS' ? 1 : 2, text)
          clearTimeout(host.timer)
          host.timer = null
          await this.stopDebug(taskId)
          host.taskId = ''
          this.setDebugStatus()
          if (status === 'FAILED') {
            this.debugLoading = false
          }
        }
      }
    },
    //  变更调试状态
    changeDebugLog(host, status, text) {
      host.data = [{
        status: status !== 2 ? 1 : status,
        text
      }]
      host.status = status
    },
    //  调试的状态 2种  debugging   finish
    setDebugStatus() {
      const hostInfo = this.info.host_info
      hostInfo.map(item => item.taskId)
      hostInfo.every(item => item.status !== 3) && (this.debugStatus = 'finish')
    },

    //  保存插件
    savePlugin() {
      /* eslint-disable */
      this.data.from = ''
      /* eslint-disable */
      const params = {
        from: 'save',
        status: '',
        message: ''
      }
      this.$set(this.data, 'saveData', params)
      this.$bus.$emit('next')
    },
    // 上一步按钮
    previous() {
      this.clearTimer()
      this.isFirstDebug = true
      /* eslint-disable */
      this.data.back = true
      /* eslint-disable */
      this.$emit('update:data', this.data)
      this.$bus.$emit('forward')
    },
    //  清除调试目标
    handleClearIp(item) {
      item.ip = ''
    },
    //  切换调试的操作系统
    changeTab(index) {
      this.activeTab = this.debugHostList[index].osType
    },
    //  清除定时器
    clearTimer() {
      this.debugHostList.forEach((item) => {
        if (item.timer) {
          clearTimeout(item.timer)
          item.taskId && this.stopDebug(item.taskId)
          this.$set(item, 'timer', null)
        }
      })
    },
    //  深拷贝
    deepCopy(obj) {
      const res = Array.isArray(obj) ? [] : {}
      Object.keys(obj).forEach((key) => {
        if (obj[key] !== null && (typeof obj[key] === 'object' || typeof obj[key] === 'function')) {
          res[key] = this.deepCopy(obj[key])
        } else {
          res[key] = obj[key]
        }
      })
      return res
    },
    //  开始调试接口
    getTaskId(params) {
      return startDebugCollectorPlugin(params.plugin_id, {
        config_version: params.config_version,
        info_version: params.info_version,
        param: params.param,
        host_info: params.host_info,
        target_nodes: params.target_nodes
      })
    },
    //  请求插件调试日志的接口
    requestDebugLog(taskId) {
      return fetchDebugLogCollectorPlugin(this.info.plugin_id, {
        task_id: taskId
      })
    },
    //  停止插件调试的接口
    stopDebug(taskId) {
      return stopDebugCollectorPlugin(this.info.plugin_id, {
        task_id: taskId
      }).catch(() => {})
    },
    //  校验规则
    validatePort(value, type) {
      if (!value) {
        this.rules[type].validate = true
        this.rules[type].message = this.$tc('必填项')
      } else {
        this.rules[type].validate = false
      }
      const res = this.validatePortRules(value)
      if (!res) {
        this.rules[type].validate = !res
        this.rules[type].message = this.$tc('请输入合法的端口')
      } else {
        this.rules[type].validate = false
      }
    },
    validatePortRules(value) {
      const isTrue = /^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$/.test(value.trim())
      return isTrue
    },
    // 支持,;和空格分割格式并且过滤不合法ip 如: 12.1.1.1 13.1.2.1, 123.12.1.1; 2.2.21
    handleTargetsPaste(v) {
      const res = v.replace(/[,;\s]/g, ',').split(',')
        .filter(item => !!item && this.ipv4Reg.test(item))
      this.snmpTargets.push(...res)
      return []
    },
    handleFileChange (file, item) {
      item.file_base64 = file.fileContent
      item.default = file.name
    },
    handleImportError (msg, item) {
      item.isError = !!msg
      item.errorMessage = msg
    }
  }
}
</script>

<style lang="scss" scoped>
    @import "../../../home/common/mixins";

    .step-test {
      padding: 40px 40px 40px 0;
      color: #63656e;
      min-width: 1120px;
      .nav-on {
        /deep/ .monitor-dialog.full-screen {
          /* stylelint-disable-next-line declaration-no-important */
          width: calc(100% - 260px) !important;
          left: 260px;
          min-width: auto;
        }
      }
      .nav-off {
        /deep/ .monitor-dialog.full-screen {
          /* stylelint-disable-next-line declaration-no-important */
          width: calc(100% - 60px) !important;
          left: 60px;
          min-width: auto;
        }
      }
      .bk-button {
        font-size: 12px;
      }
      .hint-container {
        display: flex;
        align-items: center;
        height: 42px;
        width: 1044px;
        background: #f0f8ff;
        border-radius: 2px;
        border: 1px solid #a3c5fd;
        margin: 0 0 22px 36px;
        i {
          font-size: 18px;
          color: #3a84ff;
          margin: 0 9px 0 16px;
        }
      }
      .input-container {
        overflow: hidden;
        .step-test-item {
          display: flex;
          min-height: 32px;
          margin-bottom: 20px;
          .item-label {
            flex: 0 0 116px;
            text-align: right;
            margin-right: 24px;
            height: 32px;
            line-height: 32px;
            align-self: flex-start;
            &.item-required:after {
              content: "*";
              color: red;
              position: relative;
              margin: 2px -7px 0 2px;
              font-size: 12px;
            }
            &-norequired {
              padding-right: 4px;
            }
          }
          .param-container {
            display: flex;
            flex-wrap: wrap;
          }
          .item-content {
            flex: 0 0 950px;
            .readonly-container {
              background: #f0f1f5;
              /deep/ .bk-form-input {
                /* stylelint-disable-next-line declaration-no-important */
                border: 1px solid #f0f1f5 !important;

                /* stylelint-disable-next-line declaration-no-important */
                background: #f0f1f5 !important;
              }
            }
            .input-verify {
              /* stylelint-disable-next-line declaration-no-important */
              border-color: red !important;
            }
            .item-param {
              display: flex;
              flex-direction: column;
              width: 465px;
              height: 58px;
              border: 1px solid #dcdee5;
              border-radius: 2px;
              margin-right: 10px;
              padding-top: 9px;
              margin-bottom: 10px;
              position: relative;
              .icon-popover {
                position: absolute;
                top: 7px;
                right: 7px;
                font-size: 16px;
                color: #ea3636;
              }
              &-name {
                margin-left: 16px;
                .verify-name {
                  white-space: nowrap;
                  &:after {
                    content: "*";
                    color: red;
                    position: relative;
                    margin: 2px -7px 0 2px;
                    font-size: 12px;
                  }
                }
              }
              &-content {
                padding-left: 5px;
              }
              &-input {
                margin: 1px 6px 6px 6px;
                height: 26px;
              }
              &:hover {
                box-shadow: 0 2px 4px 0 rgba(0, 0, 0, .06);
              }
              /deep/ .bk-form-input {
                height: 26px;
                color: #000;
                padding: 0 10px 0 9px;
                border: 1px solid #fff;
                width: 453px;
                &:hover {
                  background: #f5f6fa;
                }
              }
              .param-label {
                max-width: 197px;
                line-height: 30px;
                padding: 0 10px;
                text-align: center;
                display: inline-block;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                &.param-label-required:after {
                  content: "*";
                  color: red;
                  position: relative;
                  margin: 2px -2px 0 2px;
                  font-size: 12px;
                }
              }
              .params-select {
                border: 0;
                box-shadow: none;
              }
              .switch-wrap,
              .file-wrap {
                margin-top: 5px;
                margin-left: 16px;
                .monitor-import {
                  display: flex;
                  align-items: center;
                }
              }
              .file-wrap {
                display: flex;
                height: 26px;
                margin-top: 3px;
                margin-left: 7px;
                margin-right: 4px;
                &:hover {
                  background-color: #f5f6fa;
                }
              }
            }
            .cycle-select {
              width: 180px;
            }
            // 选择调试目标
            .host-container {
              display: flex;
              align-items: center;
              width: 465px;
              height: 32px;
              margin-left: 10px;
              margin-bottom: 10px;
              border: 1px solid #c4c6cc;
              border-radius: 2px;
              &:nth-child(2n-1) {
                margin-left: 0;
              }
              .item-icon {
                height: 30px;
                width: 30px;
                font-size: 16px;
                line-height: 32px;
                text-align: center;
              }
              .icon-arm {
                display: inline-block;
                line-height: 30px;
                height: 30px;
                width: auto;
                font-size: 12px;
                padding: 0 5px;
              }
              .item-host-ip {
                flex-grow: 1;
                .item-placeholder {
                  color: #c4c6cc;
                }
              }
              .clear-icon {
                color: #c4c6cc;
                margin-right: 10px;
                cursor: pointer;
              }
            }
            // 调试进度
            .debug-container {
              width: 940px;
              height: 317px;
              .tabs-container {
                height: 320px;
                max-width: calc(100vw - 477px);
                .debug-tabs {
                  display: flex;
                  align-items: center;
                  position: relative;
                  height: 32px;
                  margin: 0;
                  padding: 0;
                  background: #f5f7fa;
                  border: 1px solid #dcdee5;
                  border-bottom: 0;
                  .debug-active {
                    background: #fff;
                    position: relative;
                    &:after {
                      content: "";
                      height: 2px;
                      width: 181px;
                      position: absolute;
                      background: #3a84ff;
                      left: -1px;
                      top: -1px;
                    }
                  }
                  .debug-tab {
                    display: flex;
                    align-items: center;
                    flex: 0 0 180px;
                    height: 32px;
                    padding: 0 8px;
                    border-right: 1px solid #dcdee5;
                    cursor: pointer;
                    .tab-title {
                      width: 100%;
                      display: flex;
                      align-items: center;
                      height: 16px;
                      line-height: 16px;
                      img {
                        width: 16px;
                      }
                      .title-icon-logo {
                        flex: 0 0 16px;
                        font-size: 16px;
                      }
                      .icon-arm {
                        font-size: 12px;
                      }
                      .title-text {
                        flex: 1;
                        height: 16px;
                        margin-left: 7px;
                      }
                      .title-icon-status {
                        font-size: 16px;
                        padding-bottom: 2px;
                        &.status-exception {
                          color: #ff9c01;
                        }
                      }
                      .process-status {
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        align-items: flex-start;
                        flex: 0 0 16px;
                        height: 10px;
                        font-size: 0px;

                        @keyframes process-bar-1 {
                          0% {
                            width: 12px;
                          }
                          25% {
                            width: 8px;
                          }
                          50% {
                            width: 4px;
                          }
                          75% {
                            width: 8px;
                          }
                          100% {
                            width: 12px;
                          }
                        }
                        @keyframes process-bar-2 {
                          0% {
                            width: 4px;
                          }
                          25% {
                            width: 8px;
                          }
                          50% {
                            width: 12px;
                          }
                          75% {
                            width: 8px;
                          }
                          100% {
                            width: 4px;
                          }
                        }
                        @keyframes process-bar-3 {
                          0% {
                            width: 8px;
                          }
                          25% {
                            width: 12px;
                          }
                          50% {
                            width: 8px;
                          }
                          75% {
                            width: 4px;
                          }
                          100% {
                            width: 8px;
                          }
                        }
                        &-bar {
                          flex: 0 0 2px;
                          background: #3a84ff;
                          &.bar-1 {
                            animation: process-bar-1 .7s linear 0s infinite;
                          }
                          &.bar-2 {
                            animation: process-bar-2 .7s linear 0s infinite;
                          }
                          &.bar-3 {
                            animation: process-bar-3 .7s linear 0s infinite;
                          }
                        }
                      }
                    }
                  }
                }
              }
              .debug-preview {
                max-width: calc(100vw - 477px);
                position: absolute;
                width: 940px;
                height: 288px;
                top: 31px;
                left: -1px;
                text-align: left;
                &.active {
                  z-index: 1;
                }
              }
              .debug-desc {
                display: flex;
                align-items: center;
                justify-content: space-between;
                max-width: calc(100vw - 477px);
                margin-top: 7px;
                .desc-set-montior {
                  color: #c4c6cc;
                  cursor: no-drop;
                }
                .montior-active {
                  color: #3a84ff;
                  cursor: pointer;
                }
                .desc-text {
                  flex-grow: 1;
                  text-align: right;
                  line-height: 16px;
                  margin-left: 6px;
                  color: #979ba5;
                  .desc-time {
                    color: #ff9c01;
                  }
                }
              }
              .debug-tip {
                margin: 10px 0;
                overflow: hidden;
              }
            }
          }
          .no-param {
            display: flex;
            align-items: center;
            .param-icon {
              font-size: 16px;
              margin-right: 5px;
              color: #ffa327;
            }
            .param-text {
              height: 32px;
              line-height: 32px;
            }
          }
        }
      }
      .opeartor-container {
        margin-left: 140px;
        .reset-btn {
          margin-right: 10px;
        }
        .btn-debugging {
          border: 0;
          color: #fff;
          background: #dcdee5;
          cursor: default;
        }
      }
      /deep/.full-screen {
        background: #f5f6fa;
        overflow: scroll;
        padding: 50px 83px 35px
      }
      /deep/ .monitor-dialog-close {
        display: none;
      }
      /deep/ .value-password {
        .control-icon {
          display: none;
        }
      }
    }
</style>
