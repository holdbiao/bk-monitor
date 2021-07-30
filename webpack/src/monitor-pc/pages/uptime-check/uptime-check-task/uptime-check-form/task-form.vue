<template>
  <div class="task-form" v-bkloading="{ isLoading: isLoading }">
    <section v-show="!formDone.show">
      <div class="uptime-form-item">
        <div class="item-label item-required"> {{ $t('所属业务') }} </div>
        <div class="item-container">
          <bk-select class="reset-width" :disabled="ccBizId !== 0" :clearable="false" v-model="task.business" @change="handleChangeBiz">
            <bk-option v-for="item in businessList"
                       :key="item.id"
                       :id="item.id"
                       :name="item.text">
            </bk-option>
          </bk-select>
          <span class="validate-hint" v-show="requiredOptions.business"> {{ $t('请选择所属业务') }} </span>
        </div>
      </div>
      <div class="uptime-form-item">
        <div class="item-label item-required"> {{ $t('任务名称') }} </div>
        <div class="item-container">
          <verify-input class="reset-width" :show-validate.sync="requiredOptions.name" :validator="{ content: nameErrorMsg }">
            <!-- <bk-input v-model="task.name" @blur="requiredOptions.name = !Boolean(task.name)"></bk-input> -->
            <bk-input v-model="task.name" @blur="validateName"></bk-input>
          </verify-input>
        </div>
      </div>
      <div class="uptime-form-item">
        <div class="item-label item-required"> {{ $t('协议') }} </div>
        <div class="item-container">
          <bk-radio-group v-model="protocol.value" @change="handleChangeProtocol">
            <bk-radio class="protocol-radio" v-for="(item, index) in protocol.data" :key="index" :value="item">
              <span v-if="item !== 'ICMP'">{{item === 'HTTP' ? `${item}(S)` : item}}</span>
              <span v-else
                    class="radio-icmp-tips"
                    v-bk-tooltips.bottom="'功能依赖1.10.x及以上版本的bkmonitorbeat'">
                {{ item }}
              </span>
            </bk-radio>
          </bk-radio-group>
        </div>
      </div>
      <div class="uptime-form-item ip-selector" v-show="protocol.value !== 'HTTP'">
        <div class="item-label item-required"> {{ $t('目标') }} </div>
        <div class="item-container target">
          <topo-selector
            :preview-width="230"
            :checked-data="task.target"
            :with-external-ips="true"
            :show-table-tab="true"
            :target-node-type="targetNodeType"
            class="topo-selector"
            ref="topoSelector"
            v-if="topoSelector.isShow"
            @check-change="handleTopoCheckedChange">
          </topo-selector>
          <div class="item-container-tips"
               v-show="requiredOptions.target"
               :style="{ color: targetTipsError ? '#f56c6c' : '#63656E' }">
            {{ topoSelector.validateText }}
          </div>
        </div>
      </div>
      <div class="uptime-form-item" v-show="protocol.value === 'HTTP'">
        <div class="item-label item-required"> {{ $t('请求方法') }} </div>
        <div class="item-container">
          <bk-radio-group v-model="task.method">
            <bk-radio class="method-radio" value="GET">GET</bk-radio>
            <bk-radio class="method-radio" value="POST">POST</bk-radio>
          </bk-radio-group>
        </div>
      </div>
      <div class="uptime-form-item" v-show="protocol.value === 'HTTP'">
        <div class="item-label item-required"> {{ $t('目标地址') }} </div>
        <div class="item-container">
          <verify-input class="reset-width" :show-validate.sync="requiredOptions.urls" :validator="{ content: urlsErrorMsg }">
            <bk-input v-model="task.urls" @blur="requiredOptions.urls = !valiDateUrl(task.urls)"></bk-input>
          </verify-input>
        </div>
      </div>
      <div class="uptime-form-item submit-content" v-show="protocol.value === 'HTTP' && task.method === 'POST'">
        <div class="item-label item-required"> {{ $t('提交内容') }} </div>
        <div class="item-container">
          <bk-input class="reset-width" placeholder="发送的内容格式：k1=v1;k2=v2，或者一段JSONObject，如: {&quot;key&quot;:&quot;value&quot;}" type="textarea" v-model="task.submitContent"
                    @focus="requiredOptions.submitContent = false"
                    @blur="requiredOptions.submitContent = !Boolean(task.submitContent)">
          </bk-input>
          <span class="validate-hint" v-show="requiredOptions.submitContent"> {{ $t('请填写提交内容') }} </span>
        </div>
      </div>
      <div class="uptime-form-item" v-show="protocol.value !== 'HTTP' && protocol.value !== 'ICMP'">
        <div class="item-label item-required"> {{ $t('端口') }} </div>
        <div class="item-container">
          <verify-input class="reset-width" :show-validate.sync="requiredOptions.port" :validator="{ content: $t('请输入合法的端口') }">
            <bk-input v-model="task.port" :show-controls="true" type="number" :min="1" :max="65535" @blur="validatePort"></bk-input>
          </verify-input>
        </div>
      </div>
      <div class="uptime-form-item" v-show="protocol.value === 'UDP'">
        <div class="item-label item-required"> {{ $t('请求内容') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="requiredOptions.requestContent" :validator="{ content: $t('请输入合法的十六进制请求内容') }">
            <bk-input class="reset-width" :placeholder="$t('十六进制的请求内容，如3a47534b422d644c')"
                      v-model="task.requestContent" @blur="requiredOptions.requestContent = Boolean(task.requestContent.length % 2) || !/^[a-fA-F0-9]+$/.test(task.requestContent.trim())">
            </bk-input>
          </verify-input>
        </div>
      </div>
      <div class="uptime-form-item">
        <div class="item-label item-required"> {{ $t('拨测节点') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="requiredOptions.nodes" :validator="{ content: $t('请选择拨测节点') }">
            <bk-select class="reset-width" ref="taskNodeSelect" :clearable="false" :multiple="true" v-model="task.nodes">
              <bk-option v-for="item in node[task.business]"
                         :disabled="Boolean(item.status === '-1')"
                         :key="item.id"
                         :name="item.name + ' ' + item.ip"
                         :id="item.id">
              </bk-option>
              <div slot="extension" class="item-input-create" @click="handleCreateTaskNode">
                <i class="bk-icon icon-plus-circle"></i>{{ $t('新增拨测节点') }}
              </div>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <div class="uptime-form-item">
        <div class="item-label item-required"> {{ $t('超时设置') }} </div>
        <div class="item-container timeout">
          <verify-input :show-validate.sync="requiredOptions.timeout" :validator="timeoutValidate">
            <bk-input style="width: 120px;" v-model.number="task.timeout" type="number" @blur="handleValidateTimeout">
              <div class="unit" slot="append">ms</div>
            </bk-input>
          </verify-input>
          <div class="hint-icon" v-bk-tooltips.top="$t('超过该时长未正常采集数据时，系统判定该任务为不可用状态！')">
            <span class="icon-monitor icon-tips icon"></span>
          </div>
        </div>
      </div>
      <div class="uptime-form-item last-item">
        <div class="item-label group"> {{ $t('任务组') }} </div>
        <div class="item-container">
          <bk-select :placeholder="$t('请选择想要加入的任务组')" :multiple="true" class="reset-width" v-model="task.groups">
            <bk-option v-for="item in groupList"
                       class="reset-width"
                       :key="item.id"
                       :name="item.name"
                       :id="item.id">
            </bk-option>
          </bk-select>
        </div>
      </div>
      <div class="uptime-form-item text-item">
        <div class="item-label"></div>
        <div class="item-container item-advance"><bk-button text @click="isShowAdvanced = !isShowAdvanced">{{isShowAdvanced ? $t('隐藏高级选项') : $t('显示高级选项')}}</bk-button></div>
      </div>
      <!-- 高级选项 -->
      <transition name="advanced-option-fade">
        <div v-show="isShowAdvanced" class="uptime-form-item advanced-option">
          <advanced-option ref="advancedRef" :protocol="protocol.value" :options="advancedOptions"></advanced-option>
        </div>
      </transition>
      <div class="uptime-form-item">
        <div class="item-label"></div>
        <div class="item-container">
          <bk-button
            v-authority="{ active: !authority.MANAGE_AUTH }"
            class="btn-submit"
            theme="primary"
            :icon="isSubmit ? 'loading' : ''"
            :disabled="isSubmit"
            @click="authority.MANAGE_AUTH ? submit() : handleShowAuthorityDetail()">
            {{ submitBtnText }}
          </bk-button>
          <bk-button @click="cancel"> {{ $t('取消') }} </bk-button>
        </div>
      </div>
    </section>
    <polling-loading :status="pollingObj.status" :show.sync="pollingObj.show"></polling-loading>
    <section v-show="formDone.show">
      <task-form-done
        :edit-id="toEditId"
        :status="formDone.status"
        :error-msg="formDone.errorMsg"
        :table-data="formDone.data"
        :type="operatorType"
        @back-add="handleBackToAdd"
        @clear-task-data="handleClearTaskData">
      </task-form-done>
    </section>
  </div>
</template>
<script>
import AdvancedOption from './advanced-option'
import VerifyInput from '../../../../components/verify-input/verify-input'
import TopoSelector from '../../../../components/ip-selector/business/topo-selector-new'
import TaskFormDone from './task-form-done'
import PollingLoading from '../../../../components/polling-loading/polling-loading'
import { hostAgentStatus } from '../../../../../monitor-api/modules/commons'
import {
  listUptimeCheckNode,
  listUptimeCheckGroup,
  retrieveUptimeCheckTask,
  testUptimeCheckTask,
  createUptimeCheckTask,
  updateUptimeCheckTask,
  deployUptimeCheckTask,
  runningStatusUptimeCheckTask
} from '../../../../../monitor-api/modules/model'
import authorityMixinCreate from '../../../../mixins/authorityMixin'
import * as uptimeAuth from '../../authority-map'

export default {
  name: 'TaskForm',
  components: {
    AdvancedOption,
    VerifyInput,
    TopoSelector,
    TaskFormDone,
    PollingLoading
  },
  mixins: [authorityMixinCreate(uptimeAuth)],
  props: {
    id: [Number, String]
  },
  data() {
    return {
      isFromNode: false,
      task: {},
      backup: {},
      taskInfo: {},
      protocol: {
        data: ['HTTP', 'TCP', 'UDP', 'ICMP'],
        value: 'HTTP'
      },
      requiredOptions: {
        business: false,
        name: false,
        timeout: false,
        nodes: false,
        urls: false,
        port: false,
        requestContent: false,
        submitContent: false,
        target: false
      },
      urlsErrorMsg: '缺少URL协议字符，如http://',
      nameErrorMsg: '',
      oldOriginData: {},
      headTitle: null,
      isShowAdvanced: false,
      advancedOptions: {},
      businessList: this.$store.getters.bizList,
      ccBizId: parseInt(this.$store.getters.bizId, 10),
      // 拨测节点信息
      node: {},
      hosts: [],
      groupList: [],
      isSubmit: false,
      isLoading: false,
      formDone: {
        show: false,
        status: 'success',
        errorMsg: '',
        data: []
      },
      topoSelector: {
        isShow: false,
        validateText: this.$t('请选择目标机器')
      },
      uptimeCheckMetricMap: {
        task_duration: this.$t('响应时间'),
        response_code: this.$t('期望响应码'),
        message: this.$t('期望响应内容'),
        available: this.$t('单点可用率')
      },
      createprocess: {
        isCreate: false,
        id: ''
      },
      pollingObj: {
        status: {
          failMsg: '',
          msg: ''
        },
        show: false
      },
      toEditId: '',
      targetNodeType: 'INSTANCE'
    }
  },
  computed: {
    submitBtnText() {
      if (!this.isSubmit) {
        return this.$t('提交')
      }
      return this.id ? this.$t('编辑中...') : this.$t('创建中...')
    },
    operatorType() {
      return this.id ? 'edit' : 'add'
    },
    hasTarget() {
      const data = this.task ? this.task.target : []
      return data && data.length > 0
    },
    maxAvailableDurationLimit() {
      return this.$store.getters.maxAvailableDurationLimit
    },
    timeoutValidate() {
      return {
        content: `${this.$t('请设置超时时间')}，${this.$t('最小值：')}0ms (${this.$t('不包含')})`
        + `，${this.$t(`最大值：${this.maxAvailableDurationLimit}ms`)}`
      }
    },
    targetTipsError() {
      const { target = [] } = this.task
      return target.length === 0
    }
  },
  watch: {
    id: {
      handler() {
        this.handleInitTaskForm()
      },
      immediate: true
    },
    'protocol.value'(v) {
      // topo树首次显示时需要重置虚拟滚动的状态
      if (v !== 'HTTP') {
        this.$nextTick(() => {
          this.$refs.topoSelector && this.$refs.topoSelector.resize()
        })
      }
    }
  },
  beforeRouteEnter(to, from, next) {
    next((vueModule) => {
      const vm = vueModule
      if (from.name === 'uptime-check-node-add' || from.name === 'uptime-check') {
        vm.isLoading = true
        vm.isFromNode = true
        vm.getNodeList()
      }
    //   else {
    //     vm.handleInitTaskForm()
    //     vm.setDefaultData()
    //   }
    })
  },
  beforeRouteLeave(to, from, next) {
    this.formDone = {
      show: false,
      status: 'success',
      errorMsg: '',
      data: []
    }
    next()
  },
  methods: {
    // 判断当前targetNodeType
    targetNodeTypeInfo(nodes) {
      let result = ''
      const { INSTANCE, TOPO, SERVICE_TEMPLATE, SET_TEMPLATE } = {
        INSTANCE: 'INSTANCE',
        TOPO: 'TOPO',
        SERVICE_TEMPLATE: 'SERVICE_TEMPLATE',
        SET_TEMPLATE: 'SET_TEMPLATE'
      }
      if (nodes) {
        const firstNode = nodes[0]
        if (firstNode.bk_obj_id !== 0 && typeof(firstNode.bk_obj_id) !== 'undefined') {
          switch (firstNode.bk_obj_id) {
            case 'biz':
            case 'set':
            case 'module':
              result = TOPO
              break
            case 'SET_TEMPLATE':
              result = SET_TEMPLATE
              break
            case 'SERVICE_TEMPLATE':
              result = SERVICE_TEMPLATE
              break
            default:
              result = INSTANCE
          }
        } else {
          result = INSTANCE
        }
      }
      return result
    },
    handleBackToAdd() {
      this.formDone.show = false
      this.setDefaultData()
    },
    async handleInitTaskForm() {
      this.isLoading = true
      if (this.id) {
        this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      }
      this.generationFormField()
      this.handleSetBusiness()
      await Promise.all([this.getNodeList(), this.getGroupList(), this.getHosts()]).catch(() => {
        this.isLoading = false
      })
      if (this.$route.params.groupName) {
        const item = this.groupList.find(item => item.name === this.$route.params.groupName)
        this.task.groups.push(item.id)
      }
      // 获取当前task数据
      if (this.id) {
        await this.getTaskInfo(this.id)
        this.$store.commit(
          'app/SET_NAV_TITLE',
          `${this.$t('route-' + '编辑拨测任务').replace('route-', '')} - #${this.id} ${this.task.name}`
        )
      }
      this.isLoading = false
      this.topoSelector.isShow = true
    },
    cancel() {
      this.$router.back()
    },
    handleChangeBiz() {
      this.getNodeList()
    },
    handleChangeProtocol(val) {
      const { name } = this.task
      this.task = this.backup[val]
      this.task.name = name
      if (!this.task.business) {
        this.task.business = parseInt(this.$store.getters.bizId, 10)
      }
      if (this.requiredOptions.timeout) {
        this.requiredOptions.timeout = false
      }
      this.topoSelector.isShow = val !== 'HTTP'
    },
    generationFormField() {
      const tpl = {
        business: '',
        protocol: 'HTTP',
        name: '',
        method: 'GET',
        urls: '',
        submitContent: '',
        port: '',
        nodes: [],
        requestContent: '',
        timeout: 3000,
        groups: [],
        target: []
      }
      const protocols = ['HTTP', 'TCP', 'UDP', 'ICMP']
      protocols.forEach((item) => {
        tpl.protocol = item
        this.backup[item] = JSON.parse(JSON.stringify(tpl))
      })
      this.task = this.backup.HTTP
    },
    valiDateUrl(val) {
      const regx = new RegExp('^'
                        + '(?:(?:https||http)://)'
                        + '(?:\\S+(?::\\S*)?@)?'
                        + '(?:'
                        + '(?:[0-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])'
                        + '(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}'
                        + '(?:\\.(?:[0-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-5]))'
                        + '|'
                        + '(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)'
                        + '(?:\\.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*'
                        + '(?:\\.(?:[a-z\\u00a1-\\uffff]{2,}))'
                        + ')'
                        + '(?::\\d{2,5})?'
                        + '(?:/\\S*)?'
                        + '$', 'i')
      this.urlsErrorMsg = val.indexOf('http') > -1 ? this.$t('请输入合法的URL地址') : this.$t('缺少URL协议字符，如http://')
      return regx.test(val.trim())
    },
    getHosts() {
      const params = {
        bk_biz_id: this.task.business,
        page: 1
      }
      return hostAgentStatus(params).then((data) => {
        this.hosts = data
      })
    },
    // 获取拨测节点信息
    getNodeList() {
      return new Promise((resolve, reject) => {
        // if (Array.isArray(this.node[this.task.business])) {
        //     resolve(this.node[this.task.business])
        // } else {
        listUptimeCheckNode({ bk_biz_id: this.task.business }).then((data) => {
          resolve(data)
          this.$set(this.node, `${this.task.business}`, data)
          const curNode = this.node[this.task.business].map(item => (item.id))
          const len = this.task.nodes.length - 1
          for (let i = len; i >= 0; i--) {
            if (!curNode.includes(this.task.nodes[i])) {
              this.task.nodes.splice(i, 1)
            }
          }
          if (this.isFromNode) {
            this.task.nodes.push(this.$route.params.taskId)
            this.isLoading = false
          }
        })
          .catch(err => reject(err))
        // }
      })
    },
    // 获取任务组信息
    getGroupList() {
      return listUptimeCheckGroup().then((data) => {
        this.groupList = data
      })
    },
    async getTaskInfo(id) {
      const data = await retrieveUptimeCheckTask(id).catch(() => {
        this.isLoading = false
      })
      if (!data) {
        this.$bkMessage({
          theme: 'error',
          message: this.$t('没有找到对应的数据')
        })
        this.$router.push({
          name: 'uptime-check'
        })
      } else {
        this.backFillData(data, data.config)
      }
    },
    submit() {
      if (!this.validate(this.protocol.value)) {
        this.isSubmit = true
        // 提交必须经过以下步骤：测试 -> 保存 -> 部署
        const params = this.getParams(this.protocol.value)
        // 无论参数是否变更，都走一样的流程
        this.handleCreateTaskSubmit(params)
      }
    },
    // 创建task时提交流程
    async handleCreateTaskSubmit(params) {
      const startTime = +new Date()
      this.toEditId = ''
      this.pollingObj.status.msg = this.$t('拨测任务下发中')
      // 测试
      const testResult = await this.test(params)
      if (!testResult) return (this.pollingObj.show = false)
      // 保存
      const saveStatus = await this.save(this.getParams(this.protocol.value, 'SAVE'))
      this.formDone.data = this.getMetricDataFromData(saveStatus)
      // 发布
      const depolyRes = await this.depoly(saveStatus.id)
      if (depolyRes && !depolyRes.result) { // 发布失败
        this.toEditId = saveStatus.id
        return this.showErrorPage(depolyRes.message)
      }
      this.pollingObj.show = true
      // 轮训拨测任务状态
      const polling = (taskId, callBack) => {
        const nowTime = +new Date()
        // 发布五分钟超时
        const isTimeout = ((nowTime - startTime) / 1000 / 60) > 5
        if (isTimeout) {
          this.toEditId = saveStatus.id
          return callBack({ status: 'timeout', message: this.$t('拨测任务下发超时') })
        }
        runningStatusUptimeCheckTask(taskId).then((data) => {
          if (data.status === 'running' || data.status === 'start_failed') {
            data.status === 'start_failed' && (this.toEditId = saveStatus.id)
            callBack(data)
          } else {
            // 轮询事件间隔10S
            const timer = setTimeout(() => {
              polling(taskId, callBack)
              clearTimeout(timer)
            }, 10000)
          }
        })
          .catch((err) => {
            callBack(err)
          })
      }
      polling(saveStatus.id, (res) => {
        this.pollingObj.show = false
        // 拨测服务发布成功
        if (res.status === 'running') {
          this.$bkMessage({
            theme: 'success',
            message: this.$t('部署成功')
          })
          this.isSubmit = false
          this.formDone.status = 'success'
          this.formDone.show = true
        } else {
          const msg = this.handleErrorMessage(res)
          this.showErrorPage(msg)
        }
      })
    },
    handleErrorMessage(res) {
      let errorMsg = ''
      if (res.error_log && res.error_log.length) {
        errorMsg = res.error_log.reduce((pre, item) => (pre += `${item}<br/>`), '')
      } else {
        errorMsg = res.message || ''
      }
      return errorMsg
    },
    showErrorPage(msg) {
      this.pollingObj.show = false
      this.isLoading = false
      this.isSubmit = false
      this.formDone.status = 'error'
      this.formDone.errorMsg = msg
      this.formDone.show = true
    },
    assemblyData(params) {
      if (this.$refs.advancedRef) {
        const advanced = this.$refs.advancedRef.getValue()
        const data = JSON.parse(JSON.stringify(params.config))
        data.protocol = this.task.protocol
        data.nodes = this.task.nodes
        data.period = advanced.period
        data.response_code = advanced.response_code
        data.response = advanced.response
        data.response_format = advanced.response_format
        data.insecure_skip_verify = advanced.insecure_skip_verify
        data.bk_state_name = advanced.location.bk_state_name
        data.bk_province_name = advanced.location.bk_province_name
        return data
      }
    },
    /**
     * 检查配置是否有更改
     */
    validateChange(newData, oldData) {
      delete oldData.location
      const newKeys = Object.keys(newData)
      const oldKeys = Object.keys(oldData)
      if (newKeys.length !== oldKeys.length) {
        return true
      }
      for (let i = 0; i < newKeys.length; i++) {
        const key = newKeys[i]
        const newVal = newData[key]
        const oldVal = oldData[key]
        if (typeof newVal !== 'undefined' && typeof oldVal === 'undefined') {
          return true
        } if (typeof newVal === 'string' || typeof newVal === 'number' || typeof newVal === 'boolean') {
          if (newVal !== oldVal) {
            return true
          }
        } else if (key === 'nodes' && Array.isArray(newVal) && Array.isArray(oldVal)) {
          const newNodes = newVal.sort((a, b) => a - b).join('')
          const oldNodes = oldVal.sort((a, b) => a - b).join('')
          if (newNodes !== oldNodes) {
            return true
          }
        } else if (key === 'headers') {
          const newHeaders = JSON.stringify(newVal)
          const oldHeaders = JSON.stringify(oldVal)
          if (newHeaders !== oldHeaders) {
            return true
          }
        }
      }
      return false
    },
    test(params) {
      return testUptimeCheckTask(params, { needMessage: false }).catch((err) => {
        this.isLoading = false
        this.isSubmit = false
        this.formDone.status = 'error'
        this.formDone.errorMsg = err.message || ''
        this.formDone.show = true
      })
    },
    save(params) {
      const id = this.createprocess.isCreate ? this.createprocess.id : this.id
      const ajaxFn = id ? updateUptimeCheckTask(id, params, { needMessage: false })
        : createUptimeCheckTask(params, { needMessage: false })
      return ajaxFn.catch((err) => {
        this.isLoading = false
        this.isSubmit = false
        this.formDone.errorMsg = err.message || ''
        this.formDone.status = 'error'
        this.formDone.show = true
      })
    },
    depoly(id) {
      return deployUptimeCheckTask(id, {}, { needRes: true }).then(res => Promise.resolve(res))
        .catch((err) => {
          if (!this.id) {
            this.createprocess.isCreate = true
            this.createprocess.id = id
          }
          this.pollingObj.show = false
          this.isLoading = false
          this.isSubmit = false
          this.formDone.errorMsg = err.message || ''
          this.formDone.status = 'error'
          this.formDone.show = true
          return Promise.reject(err)
        })
    },
    getConfig(advanced) {
      const config = {
        period: advanced.period
      }
      if (this.protocol.value === 'ICMP') {
        config.max_rtt = this.task.timeout
        config.total_num = advanced.total_num
        config.size = advanced.size
        config.hosts = this.task.target
        return config
      }
      config.timeout = this.task.timeout
      config.response = advanced.response
      config.response_format = advanced.response_format
      if (this.protocol.value === 'HTTP') {
        config.method = this.task.method
        config.urls = this.task.urls.trim()
        config.request = this.task.method === 'POST' ? this.task.submitContent : null
        config.headers = advanced.headers
        config.response_code = advanced.response_code
        config.insecure_skip_verify = advanced.insecure_skip_verify
      } else {
        config.hosts = this.task.target
        config.port = this.task.port.trim()
        if (this.protocol.value === 'UDP') {
          config.request = this.task.requestContent.trim()
        }
      }
      return config
    },
    /**
     * @desc 获取参数
     * @param {String} protocol - 协议：'HTTP'，'TCP'，'UDP'
     * @param {String} type - 类型：'TEST'-测试，'SAVE'-保存
     */
    getParams(protocol, type = 'TEST') {
      const { task } = this
      const advanced = this.$refs.advancedRef.getValue()
      const config = this.getConfig(advanced)
      const params = {
        bk_biz_id: task.business,
        protocol: this.protocol.value,
        node_id_list: task.nodes.filter(item => !!item),
        config
      }
      if (type === 'SAVE') {
        params.location = advanced.location
        params.name = task.name.trim()
        params.group_id_list = task.groups
      }
      return params
    },
    validate(protocol = 'HTTP') {
      let options = ['business', 'name', 'nodes', 'timeout']
      const rules = {
        business: val => Boolean(val),
        name: () => this.validateName(),
        nodes: val => Boolean(val.length),
        timeout: val => this.handleValidateTimeout(val)
      }
      if (protocol === 'HTTP') {
        if (this.task.method === 'POST') {
          options = options.concat(['submitContent'])
          rules.submitContent = val => Boolean(val)
        }
        options = options.concat(['urls'])
        rules.urls = this.valiDateUrl
      } else {
        rules.target = val => val.length
        options = options.concat(['target'])
        if (protocol !== 'ICMP') {
          rules.port = val => /^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$/.test(val.trim())
        }
        if (protocol === 'TCP') {
          options = options.concat(['port'])
        } else if (protocol === 'UDP') {
          options = options.concat(['port', 'requestContent'])
          rules.requestContent = val => !(val.length % 2) && /^[a-fA-F0-9]+$/.test(val.trim())
        }
      }
      const result = []
      options.forEach((option) => {
        const fn = rules[option]
        this.requiredOptions[option] = !fn(this.task[option])
        result.push(this.requiredOptions[option])
        if (option === 'urls' && this.requiredOptions[option]) {
          this.urlsErrorMsg = this.task[option].indexOf('http') > -1
            ? this.$t('请输入合法的URL地址')
            : this.$t('缺少URL协议字符，如http://')
        }
      })
      return result.includes(true)
    },
    // 回显form数据
    backFillData(data, cfig = { hosts: [] }) {
      const config = cfig
      this.task.business = data.bk_biz_id
      this.protocol.value = data.protocol
      this.task.name = data.name
      this.task.groups = data.groups.map(group => group.id)
      data.nodes.forEach((node) => {
        const sameNode = this.node[data.bk_biz_id].find(item => item.id === node.id)
        if (sameNode && !this.task.nodes.some(id => id === node.id)) {
          this.task.nodes.push(node.id)
        }
      })
      if (this.protocol.value === 'HTTP') {
        this.task.submitContent = config.request || ''
        this.task.urls = config.urls
        this.task.method = config.method
        this.task.timeout = config.timeout
      } else if (this.protocol.value === 'ICMP') {
        this.task.timeout = config.max_rtt
        this.task.target = config.hosts
      } else {
        this.task.timeout = config.timeout
        this.task.port = config.port
        this.task.target = config.hosts
        if (this.protocol.value === 'UDP') {
          this.task.requestContent = config.request
        }
      }
      config.location = data.location
      this.advancedOptions = config
      this.targetNodeType = this.targetNodeTypeInfo(config.hosts)
      this.$nextTick(() => {
        this.oldOriginData = this.assemblyData(data)
      })
    },
    getMetricDataFromData(data) {
      if (!data) return []
      return Object.keys(this.uptimeCheckMetricMap).map((key) => {
        const metricData = {
          metric: key,
          label: this.uptimeCheckMetricMap[key],
          resultTableId: `uptimecheck.${data.protocol.toLowerCase()}`,
          resultTableLabel: 'uptimecheck',
          relatedId: data.id,
          relatedName: data.name,
          status: 1,
          detail: '',
          value: ''
        }
        if (['available', 'task_duration'].includes(key)) {
          metricData.detail = this.$t('已配置')// ${this.uptimeCheckMetricMap[key]}
          metricData.value = data[this.uptimeCheckMetricMap[key]] || ''
        } else if (key === 'response_code' && data.protocol.toLowerCase() === 'http') {
          metricData.detail = data.config.response_code ? this.$t('已配置') : this.$t('未配置')
          metricData.value = data.config.response_code || ''
          metricData.status = data.config.response_code ? 1 : 0
        } else if (key === 'message' && data.protocol.toLowerCase() !== 'icmp') {
          metricData.detail = data.config.response ? this.$t('已配置') : this.$t('未配置')
          metricData.value = data.config.response || ''
          metricData.status = data.config.response ? 1 : 0
        }
        return metricData
      })
        .filter(item => item.detail || data.protocol.toLowerCase() === 'http')
    },
    handleFail(msg) {
      this.$bkMessage({
        theme: 'error',
        message: msg,
        ellipsisLine: 0
      })
      this.isLoading = false
    },
    handleSetBusiness() {
      switch (this.operatorType) {
        case 'edit':
          this.task.business = this.$route.params.bizId === undefined
            ? this.$store.getters.bizId
            : this.$route.params.bizId
          break
        case 'add':
          this.task.business = this.$store.getters.bizId
          break
      }
    },
    // 更新IP选择器当前选中的items
    handleTopoCheckedChange(checkedData) {
      const { data } = checkedData
      if (data.length > 0) {
        this.requiredOptions.target = false
      }
      this.task.target = data
    },
    handleClearTaskData(v) {
      if (v) {
        this.$store.commit('app/SET_NAV_TITLE', this.$t('新建拨测任务'))
        this.advancedOptions = {}
        this.setDefaultData()
        this.handleInitTaskForm()
      }
      if (this.operatorType === 'edit' && v) {
        this.$router.push({
          name: 'uptime-check-task-add'
        })
      }
      this.formDone.show = false
    },
    handleCreateTaskNode() {
      const dropInstance = this.$refs.taskNodeSelect && this.$refs.taskNodeSelect.$refs.selectDropdown.instance
      if (dropInstance?.state.isVisible) {
        dropInstance.hide(0)
      }
      this.$router.push({
        name: 'uptime-check-node-add'
      })
    },
    setDefaultData() {
      this.protocol.value = 'HTTP'
      this.requiredOptions = {
        business: false,
        name: false,
        timeout: false,
        nodes: false,
        urls: false,
        port: false,
        requestContent: false,
        submitContent: false,
        target: false
      }
      this.isShowAdvanced = false
      this.$refs.advancedRef.setDefaultData()
      this.topoSelector = {
        isShow: false,
        validateText: this.$t('请选择目标机器')
      }
      this.createprocess = {
        isCreate: false,
        id: ''
      }
    },
    handleValidateTimeout() {
      this.requiredOptions.timeout = !this.task.timeout
      || this.task.timeout <= 0
      || this.task.timeout > this.maxAvailableDurationLimit
      return !this.requiredOptions.timeout
    },
    validateName() {
      let isPass = true
      if (!Boolean(this.task.name)) {
        isPass = false
        this.requiredOptions.name = true
        this.nameErrorMsg = this.$t('必填项')
      } else if (this.task.name.length > 50) {
        isPass = false
        this.requiredOptions.name = true
        this.nameErrorMsg = this.$t('任务名不能超过50个字符')
      } else {
        isPass = true
        this.requiredOptions.name = false
        this.nameErrorMsg = ''
      }
      return isPass
    },
    validatePort() {
      const port = +this.task.port
      this.requiredOptions.port = !(0 < port && port <= 65535)
    }
  }
}
</script>
<style lang="scss" scoped>
.task-form {
  padding-top: 12px;
  min-height: calc(100vh - 100px);
  .uptime-form-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-bottom: 20px;
    color: #63656e;
    &.ip-selector {
      align-items: flex-start;
      .out-line {
        outline: 1px solid #dcdee5;
      }
      /deep/ .left-content {
        &-wrap {
          height: 230px;
          .static-topo {
            margin-top: 0;
          }
        }
      }
      .ip-input-layout {
        /deep/ .left-content-wrap {
          height: auto;
        }
      }
      /deep/ .left-tab {
        display: none;
      }
      /deep/ .ip-select-right {
        border-top: 1px solid #dcdee5;
        background-image: linear-gradient(-90deg, #dcdee5 1px, rgba(0, 0, 0, 0)
        1px, rgba(0, 0, 0, 0) 100%),linear-gradient(0deg, #dcdee5 1px, rgba(0, 0, 0, 0)
        1px, rgba(0, 0, 0, 0) 100%);
        .right-wrap {
          border-top: 0;
        }
      }
      /deep/ .right-empty {
        margin-top: 120px;
      }
    }
    &.advanced-option {
      margin-bottom: 0;
    }
    &.submit-content {
      align-items: start;
    }
    .item-label {
      flex: 0 0 100px;
      margin-right: 15px;
      text-align: right;
      font-size: 14px;
      &.item-required:after {
        content: "*";
        color: red;
        position: relative;
        left: 5px;
        font-size: 12px;
      }
      &.group {
        padding-right: 6px;
      }
    }
    .item-container {
      position: relative;
      /deep/ .ip-select {
        /* stylelint-disable-next-line declaration-no-important*/
        height: 340px !important;
      }
      .need-border {
        /deep/ .ip-select-right {
          border-bottom: 1px solid #dcdee5;
        }
      }
      &.item-advance {
        height: 18px;
        display: flex;
        align-items: center;
      }
      /deep/ .tooltips-icon {
        right: 5px;
        top: 8px;
      }
      &.timeout {
        display: inline-flex;
        align-items: center;
        /deep/ .tooltips-icon {
          right: 38px;
          top: 8px;
        }
        .timeout-select {
          width: 160px;
        }
        .hint-icon {
          width: 18px;
          height: 18px;
          line-height: 18px;
          display: inline-block;
          fill: #fff;
          margin-left: 11px;
          cursor: pointer;
          .icon-monitor {
            font-size: 16px;
          }
        }
      }
      .icon-tips:hover {
        color: #3a84ff;
      }
      /deep/ .bk-form-radio {
        margin-right: 20px;
        margin-bottom: 0;
        .icon-check {
          &::before {
            content: none;
          }
        }
      }
      .validate-hint {
        position: absolute;
        font-size: 12px;
        color: red;
      }
      .reset-width {
        width: 503px;
        background-color: #fff;
      }
      .unit {
        width: 32px;
        height: 32px;
        line-height: 31px;
        text-align: center;
        font-size: 14px;
        color: #63656e;
      }
      .protocol-radio {
        width: 82px;
        .radio-icmp-tips {
          border-bottom: 1px dashed #000;
        }
      }
      .method-radio {
        width: 82px;
        margin-right: 15px;
      }
      .btn-submit {
        margin-right: 10px;
      }
      /deep/ .bk-button-icon-loading::before {
        content: "";
      }
      .item-container-tips {
        margin-top: 6px;
      }
      &.target {
        /deep/ .bk-select {
          width: unset;
        }
        .topo-selector {
          min-width: 1100px;
        }
      }
    }
    .icon {
      font-size: 16px
    }
  }
  .last-item {
    margin-bottom: 17px;
  }
  .text-item {
    margin-bottom: 18px;
  }
  .advanced-option-fade {
    &-enter-active {
      transition: opacity .5s cubic-bezier(.25, 1, .25, 1);
    }
    &-leave-active,
    &-enter,
    &-leave-to {
      opacity: 0;
    }
  }
}
</style>
