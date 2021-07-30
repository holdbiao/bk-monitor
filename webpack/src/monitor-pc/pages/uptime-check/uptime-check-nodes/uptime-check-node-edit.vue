<template>
  <div class="node-edit" v-bkloading="{ isLoading: isInitLoading }">
    <div v-if="isShow">
      <div class="node-edit-item">
        <div class="item-label label-required"> {{ $t('所属业务') }} </div>
        <div class="item-container">
          <div class="business-container">
            <verify-input :show-validate.sync="rules.bk_biz_id.validate">
              <bk-select class="business-select"
                         :style="{ background: canSelectBusiness ? '#fafafa' : '#FFFFFF' }" :placeholder="$t('选择业务')"
                         v-model="node.bk_biz_id"
                         :clearable="false"
                         :disabled="canSelectBusiness"
                         @toggle="handleBusinessToggle">
                <bk-option v-for="item in businessList"
                           :key="item.id"
                           :id="item.id"
                           :name="item.text">
                  <div @click="handleBusinessOptClick(item.id)">{{item.text}}</div>
                </bk-option>
              </bk-select>
            </verify-input>
            <bk-checkbox
              v-authority="{ active: !authority.MANAGE_NODE_AUTH }"
              :disabled="!authority.MANAGE_NODE_AUTH"
              :class="['business-checkbox', {
                'auth-disabled': !authority.MANAGE_NODE_AUTH
              }]"
              v-model="node.is_common"
              @click.native="!authority.MANAGE_NODE_AUTH && handleShowAuthorityDetail(uptimeAuth.MANAGE_NODE_AUTH)">
              {{ $t('设为公共节点') }}
            </bk-checkbox>
          </div>
        </div>
      </div>
      <div class="node-edit-item">
        <div class="item-label label-required target-item"> {{ $t('选择目标') }} </div>
        <div class="item-container">
          <div class="target-container">
            <verify-input :show-validate.sync="rules.ip.validate"
                          :validator="{ content: rules.ip.message }"
                          position="right">
              <label :class="['target-label', { 'selected': node.target === '1', 'is-empty': rules.ip.validate }]">
                <input type="radio" id="selfNode" value="1" v-model="node.target">
                <label for="selfNode" class="selected"></label>
                <div class="label-container" ref="ipPopover">
                  <span class="label-text"> {{ $t('自建节点') }} </span>
                  <bk-input class="label-input"
                            :value="node.ip"
                            @change="handleIpChange(...arguments, $event)"
                            @input="handleIpInput">
                  </bk-input>
                  <span class="label-icon-select" @click="selectTarget"> {{ $t('使用选择器') }} </span>
                </div>
              </label>
            </verify-input>
            <label class="target-label disabled">
              <input type="radio" id="cloudNode" value="2" disabled>
              <label for="cloudNode" class="selected"></label>
              <div class="label-container">
                <span class="label-text"> {{ $t('云拨测') }} </span>
                <bk-input class="label-input" :placeholder="$t('待开放，敬请期待')" disabled></bk-input>
              </div>
            </label>
          </div>
        </div>
      </div>
      <div class="node-edit-item">
        <div class="item-label"> {{ $t('地区') }} </div>
        <div class="item-container">
          <div class="area-container">
            <bk-select class="area-select" :placeholder="$t('选择国家')"
                       v-model="node.country"
                       searchable
                       @change="handleCountryChange">
              <bk-option v-for="item in countryList"
                         :key="item.code"
                         :id="item.cn"
                         :name="item.cn">
                <div @click="handleCountryOptClick(item)">{{item.cn}}</div>
              </bk-option>
            </bk-select>
            <bk-select class="area-select" :placeholder="$t('选择省份')"
                       v-model="node.city"
                       searchable>
              <bk-option v-for="item in cityList"
                         :key="item.code"
                         :id="item.cn"
                         :name="item.cn">
              </bk-option>
            </bk-select>
            <svg class="hint-icon" viewBox="0 0 64 64" v-bk-tooltips.right="$t('从配置平台过滤地区和运营商')">
              <g>
                <circle cx="32" cy="32" r="25" fill="#63656E" />
              </g>
              <g>
                <path d="M32,4C16.5,4,4,16.5,4,32s12.5,28,28,28s28-12.5,28-28S47.5,4,32,4z M32,56C18.7,56,8,45.3,8,32S18.7,8,32,8s24,10.7,24,24S45.3,56,32,56z" />
                <path d="M30.9,25.2c-1.8,0.4-3.5,1.3-4.8,2.6c-1.5,1.4,0.1,2.8,1,1.7c0.6-0.8,1.5-1.4,2.5-1.8c0.7-0.1,1.1,0.1,1.2,0.6c0.1,0.9,0,1.7-0.3,2.6c-0.3,1.2-0.9,3.2-1.6,5.9c-1.4,4.8-2.1,7.8-1.9,8.8c0.2,1.1,0.8,2,1.8,2.6c1.1,0.5,2.4,0.6,3.6,0.3c1.9-0.4,3.6-1.4,5-2.8c1.6-1.6-0.2-2.7-1.1-1.8c-0.6,0.8-1.5,1.4-2.5,1.6c-0.9,0.2-1.4-0.2-1.6-1c-0.1-0.9,0.1-1.8,0.4-2.6c2.5-8.5,3.6-13.3,3.3-14.5c-0.2-0.9-0.8-1.7-1.6-2.1C33.3,24.9,32,24.9,30.9,25.2z" />
                <circle cx="35" cy="19" r="3" />
              </g>
            </svg>
          </div>
        </div>
      </div>
      <div class="node-edit-item">
        <div class="item-label"> {{ $t('运营商') }} </div>
        <div class="item-container">
          <div class="operator-container">
            <bk-radio-group v-model="node.carrieroperator"
                            @change="handleOpearatorChange">
              <bk-radio class="operator-radio"
                        v-for="(item, index) in operatorList"
                        :key="index"
                        :value="item.cn">
                {{item.cn}}
              </bk-radio>
              <bk-radio class="operator-radio" :value="$t('自定义')">
                <div ref="customCarrieroperator">
                  <span v-if="node.carrieroperator !== $t('自定义')"> {{ $t('自定义') }} </span>
                  <verify-input v-else
                                :show-validate.sync="rules.carrieroperator.validate"
                                :validator="{ content: rules.carrieroperator.message }">
                    <bk-input
                      class="operator-input"
                      ref="operatorInput"
                      v-model.trim="customCarrieroperator"
                      @focus="handleOperatorFocus(...arguments, $event)"
                      @input="handleOperatorInput">
                    </bk-input>
                  </verify-input>
                </div>
              </bk-radio>
            </bk-radio-group>
          </div>
        </div>
      </div>
      <div class="node-edit-item">
        <div class="item-label label-required"> {{ $t('节点名称') }} </div>
        <div class="item-container">
          <verify-input class="name-container" :show-validate.sync="rules.name.validate">
            <bk-input v-model.trim="node.name" @blur="validateField(node.name, rules.name)"></bk-input>
          </verify-input>
        </div>
      </div>
      <div class="node-edit-item">
        <div class="item-label"></div>
        <div class="item-container">
          <bk-button
            v-authority="{ active: !authority.MANAGE_AUTH }"
            class="button-submit"
            theme="primary"
            :icon="isSubmitLoading ? 'loading' : ''"
            :disabled="isSubmitLoading"
            @click="authority.MANAGE_AUTH ? handleSubmit() : handleShowAuthorityDetail(uptimeAuth.MANAGE_AUTH)">
            {{submitBtnText}}
          </bk-button>
          <bk-button @click="handleBack"> {{ $t('取消') }} </bk-button>
        </div>
      </div>
    </div>
    <uptime-check-node-done class="uptime-check-node-done" :options="options" v-else @cancel="handleCancel" @confirm="handleBack"></uptime-check-node-done>
    <div v-show="false">
      <div class="ip-popover-container"
           ref="ipPopoverContent"
           :style="{ width: `${ipPopover.width}px` }">
        <ul class="ip-popover"
            v-show="filterIpList.length">
          <li class="ip-popover-item"
              v-for="item in filterIpList"
              :key="item.ip"
              @mousedown.stop="handleIpOptClick(item)">
            <span class="item-text">{{item.ip}}</span>
            <span class="item-status" v-if="item.is_built"> {{ $t('（已创建节点）') }} </span>
          </li>
        </ul>
        <div class="no-data" v-show="!filterIpList.length"> {{ $t('无匹配选项') }} </div>
      </div>
    </div>
    <div v-show="false">
      <div class="operator-popover-container"
           ref="operatorPopoverContent">
        <ul class="operator-popover"
            v-show="filterCustomOperatorList.length">
          <li class="operator-popover-item"
              v-for="item in filterCustomOperatorList"
              :key="item"
              @click.stop="handleOperatorOptClick(item)">
            <span class="item-text">{{item}}</span>
          </li>
        </ul>
        <div class="no-data" v-show="!filterCustomOperatorList.length"> {{ $t('无匹配选项') }} </div>
      </div>
    </div>
    <uptime-check-node-edit-topo
      v-model="table.isShow"
      :ip-list="paramsList"
      :default-checked-ip="node.ip"
      @checked-ip="handleCheckedIp">
    </uptime-check-node-edit-topo>
    <!-- <uptime-check-node-edit-table :is-show="table.isShow" :ip-list="paramsList" @configIp="handleCheckedIp" @show-change="status => table.isShow = status"></uptime-check-node-edit-table> -->
  </div>
</template>

<script>
// import uptimeCheckNodeEditTable from './uptime-check-node-edit-table'
import VerifyInput from '../../plugin-manager/plugin-instance/set-steps/verify-input'
import UptimeCheckNodeDone from './uptime-check-node-done'
import uptimeCheckNodeEditTopo from './uptime-check-node-edit-topo'
import { debounce } from 'throttle-debounce'
import { selectUptimeCheckNode, selectCarrierOperator } from '../../../../monitor-api/modules/uptime_check'
import { countryList, ispList } from '../../../../monitor-api/modules/commons'
import { createUptimeCheckNode, updateUptimeCheckNode, retrieveUptimeCheckNode,
  isExistUptimeCheckNode, fixNameConflictUptimeCheckNode } from '../../../../monitor-api/modules/model'
import formLabelMixin from '../../../mixins/formLabelMixin'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import * as uptimeAuth from '../authority-map'

export default {
  name: 'UptimeCheckNodeEdit',
  components: {
    VerifyInput,
    UptimeCheckNodeDone,
    uptimeCheckNodeEditTopo
    // uptimeCheckNodeEditTable
  },
  mixins: [formLabelMixin, authorityMixinCreate(uptimeAuth)],
  props: {
    id: [String, Number]
  },
  data() {
    return {
      uptimeAuth,
      isShow: true,
      isInitLoading: false,
      isSubmitLoading: false,
      node: {
        id: '',
        bk_biz_id: +this.$store.getters.bizId,
        target: '1',
        ip: '',
        country: '',
        city: '',
        name: '',
        carrieroperator: '',
        is_common: false,
        plat_id: ''
      },
      rules: {
        bk_biz_id: {
          validate: false,
          message: this.$t('必填项'),
          rule: [
            { required: true }
          ]
        },
        ip: {
          validate: false,
          message: this.$t('请输入IP'),
          rule: [
            { required: true, message: this.$t('请输入IP') },
            { required: true, message: this.$t('请输入合法的IP'), validator: this.validateIPIsValid },
            { required: true, message: this.$t('找不到该主机'), validator: this.validateIPIsExist },
            { required: true, message: this.$t('该主机已创建节点'), validator: this.validateIPIsCreated }
          ]
        },
        name: {
          validate: false,
          message: this.$t('必填项'),
          rule: [
            { required: true, message: this.$t('请输入节点名称') },
            { required: true, message: this.$t('该节点名称已存在'), validator: this.validateNameIsExist }
          ]
        },
        carrieroperator: {
          validate: false,
          message: this.$t('必填项'),
          rule: [
            { required: true, message: this.$t('请输入运营商名称'), validator: this.validateOperatorEmpty },
            { required: true, message: this.$t('不允许超过10个字符'), validator: this.validateOperatorLength },
            { required: true, message:
            `${this.$t('不允许包含如下特殊字符：')}" / \\ [ ] ' : ; | = , + * ? < > { }${this.$t('空格')}`,
            validator: this.validateOperatorFormat }
          ]
        }
      },
      countryList: [],
      cityList: [],
      operatorList: [],
      businessList: this.$store.getters.bizList,
      ipList: [],
      paramsList: [],
      filterIpList: [],
      customOperatorList: [],
      filterCustomOperatorList: [],
      ipPattern: /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}$/,
      options: {
        isLoading: false,
        status: true,
        statusTitle: this.$t('拨测节点创建成功'),
        cancelText: this.$t('返回列表'),
        confirmText: this.$t('添加拨测任务')
      },
      ipPopover: {
        instance: null,
        width: 0
      },
      operatorPopover: {
        instance: null
      },
      handleIpInput: null,
      handleOperatorInput: null,
      customCarrieroperator: '',
      table: {
        isShow: false
      },
      isFromTask: false
    }
  },
  computed: {
    // 只要存在节点id，下一步时，走编辑接口。
    isEdit: {
      get() {
        return this.id !== undefined || Number.isInteger(this.node.id)
      },
      set(newValue) {
        this.isEdit = newValue
      }
    },
    isSuperUser() {
      return this.$store.getters.isSuperUser
    },
    prefixName() {
      const { node } = this
      const address = node.country || node.city ? `${node.country} ${node.city}` : ''
      return node.carrieroperator
        ? `${address} ${node.carrieroperator === this.$t('自定义') ? this.customCarrieroperator : node.carrieroperator}`
        : `${address}`
    },
    // 能否选择 `所属业务`
    canSelectBusiness() {
      // 全业务时可选
      return this.node.bk_biz_id !== 0
    },
    submitBtnText() {
      const res = this.isEdit ? this.$t('执行中...') : this.$t('创建中...')
      return this.isSubmitLoading ? res : this.$t('提交')
    }
  },
  watch: {
    prefixName(val) {
      if (val && !this.isEdit) {
        this.node.name = val
        this.validateField(this.node.name, this.rules.name)
      }
    }
  },
  created() {
    this.node.bk_biz_id = +this.$store.getters.bizId
    this.businessList = this.$store.getters.bizList
    this.isInitLoading = true
    if (this.isEdit) {
      this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      const bizId = this.$route.params.bizId === undefined ? this.$store.getters.bizId : this.$route.params.bizId
      Promise.all([this.getAreaList(), this.getNodeDetail(this.id, bizId),
        this.getOperatorList(), this.getHostRegionIspList(bizId)]).then((res) => {
        if (res[1]) {
          this.handleNodeInfo(res[1])
        }
      })
        .finally(() => {
          this.$store.commit(
            'app/SET_NAV_TITLE',
            `${this.$t('route-' + '编辑拨测节点').replace('route-', '')} - ${this.node.ip}`
          )
          this.isInitLoading = false
        })
    } else {
      Promise.all([this.getAreaList(), this.getOperatorList(),
        this.getHostRegionIspList(this.node.bk_biz_id)]).finally(() => {
        this.isInitLoading = false
      })
    }
    this.handleIpInput = debounce(300, (v) => {
      this.filterIpList = this.ipList.filter(item => item.ip.indexOf(v) > -1).slice(0, 100)
    })
    this.handleOperatorInput = debounce(300, (v) => {
      this.filterCustomOperatorList = this.customOperatorList.filter(item => item.indexOf(v) > -1)
    })
  },
  mounted() {
    this.initFormLabelWidth({ safePadding: 12 })
  },
  beforeDestroy() {
    this.ipPopover.instance?.destroy()
    this.operatorPopover.instance?.destroy()
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (from.name === 'uptime-check-task-add' || from.name === 'uptime-check-task-edit') {
        vm.isFromTask = true
      }
    })
  },
  methods: {
    handleCheckedIp(data) {
      this.node.ip = data.ip
      const ipconfig = this.ipList.filter(item => item.ip === data.ip && item.plat_id === data.bkCloudId)
      this.handleIpOptClick(ipconfig[0])
    },
    async validateField(value, ruleMap) {
      const { rule } = ruleMap
      for (const item of rule) {
        if (item.required && !value && !item.validator) { // 空值
          ruleMap.validate = true
          ruleMap.message = item.message
          return true
        } if (item.required && item.validator && typeof item.validator === 'function') { // 非空有校验器
          const res = item.validator(value)
          if (this.isPromise(res)) {
            ruleMap.validate = await res
          } else {
            ruleMap.validate = !res
          }
          if (ruleMap.validate) {
            ruleMap.message = item.message
            return true
          }
        }
      }
      ruleMap.validate = false
      return false
    },
    async validate() {
      const { node } = this
      const { rules } = this
      let keys = Object.keys(this.rules)
      if (this.node.carrieroperator !== this.$t('自定义')) {
        keys = keys.filter(item => item !== 'carrieroperator')
      }
      for (const item of keys) {
        if (!rules[item].validate) {
          await this.validateField(node[item], rules[item])
        }
      }
      return keys.every(item => rules[item].validate === false)
    },
    validateIPIsValid(val) {
      return this.ipPattern.test(val)
    },
    validateIPIsExist(val) {
      return !!this.ipList.find(item => item.ip === val)
    },
    async validateIPIsCreated(val) {
      let res = false
      if (!this.isEdit) {
        res = await this.getIPIsExist(this.node.bk_biz_id, val)
      }
      return res.is_exist
    },
    validateOperatorEmpty(val) {
      if (val === this.$t('自定义')) {
        return this.customCarrieroperator !== ''
      }
      return true
    },
    validateOperatorLength(val) {
      if (val === this.$t('自定义')) {
        return !this.validateStrLength(this.customCarrieroperator)
      }
      return true
    },
    validateOperatorFormat(val) {
      if (val === this.$t('自定义')) {
        return !/["/[\]':;|=,+*?<>{}.\\]+/g.test(this.customCarrieroperator)
      }
      return true
    },
    validateStrLength(str, length = 10) {
      const cnLength = (str.match(/[\u4e00-\u9fa5]/g) || []).length
      const enLength = (str || '').length - cnLength
      return (cnLength * 2) + enLength > length
    },
    handleTargetFocus(val) {
      this.node.target = val
    },
    selectTarget() {
      this.table.isShow = true
    },
    handleCountryChange(newVal) {
      if (!newVal) {
        this.cityList = []
        this.node.city = ''
      }
    },
    handleCountryOptClick(option) {
      this.cityList = option.children
      this.node.city = ''
    },
    setCity(code) {
      const country = this.countryList.find(item => item.cn === code) || {}
      if (country.children?.length) {
        this.cityList = country.children
      }
    },
    async handleSubmit() {
      if (await this.validate()) {
        const { node, isEdit } = this
        const params = this.getParams(node)
        if (isEdit) {
          await this.update(node.id, params)
        } else {
          await this.create(params)
        }
        this.isSubmitLoading = false
        if (this.isFromTask) {
          this.$router.push({ name: 'uptime-check-task-add', params: { taskId: node.id } })
        } else {
          this.isShow = false
          this.handleSubmitRes(true, isEdit ? this.$t('拨测节点编辑成功') : this.$t('拨测节点创建成功'))
        }
      }
    },
    getParams(node) {
      return {
        location: {
          country: node.country,
          city: node.city
        },
        bk_biz_id: node.bk_biz_id,
        carrieroperator: node.carrieroperator === this.$t('自定义')
          ? this.customCarrieroperator
          : (node.carrieroperator || ''),
        ip: node.ip,
        is_common: node.is_common,
        name: node.name,
        plat_id: node.plat_id
      }
    },
    create(params) {
      this.isSubmitLoading = true
      return createUptimeCheckNode(params).then((data) => {
        this.node.id = data.id
      })
        .finally(() => {
          this.isSubmitLoading = false
        })
    },
    update(id, params) {
      this.isSubmitLoading = true
      return updateUptimeCheckNode(id, params).finally(() => {
        this.isSubmitLoading = false
      })
    },
    handleBack() {
      if (location.hash === '#create') {
        location.hash = ''
      }
      if (this.isFromTask) {
        this.$router.back()
      } else {
        this.$router.push({
          name: 'uptime-check',
          params: {
            id: 'uptime-check-node'
          }
        })
      }
    },
    handleCancel() {
      this.handleBack()
    },
    getAreaList() {
      return countryList().then((data) => {
        this.countryList = data
      })
    },
    getOperatorList() {
      return ispList().then((data) => {
        this.operatorList = data
      })
    },
    getHostRegionIspList(id) {
      return selectUptimeCheckNode({ bk_biz_id: id }).then((data) => {
        this.ipList = data
        data.forEach((item) => {
          this.paramsList.push({
            ip: item.ip,
            agentStatus: item.agent_status,
            cloudName: item.plat_name,
            isBuilt: item.is_built,
            bkCloudId: item.plat_id
          })
        })
      })
    },

    handleNodeInfo(info) {
      const { node } = this
      Object.keys(node).forEach((item) => {
        node[item] = info[item]
      })
      const { location } = info
      node.country = location.country
      node.city = location.city
      this.setCity(location.country)
      node.target = '1' // 自建节点
      if (node.carrieroperator && ![this.$t('移动'), this.$t('电信'), this.$t('联通')].includes(node.carrieroperator)) {
        this.customCarrieroperator = node.carrieroperator
        node.carrieroperator = this.$t('自定义')
      }
    },
    handleSubmitRes(result, title) {
      const { options } = this
      options.isLoading = false
      options.status = result
      options.statusTitle = title
    },
    handleBusinessToggle(toggle) {
      !toggle && this.validateField(this.node.bk_biz_id, this.rules.bk_biz_id)
    },
    getNodeDetail(id, businessId) {
      return retrieveUptimeCheckNode(id, { bk_biz_id: businessId })
    },
    handleBusinessOptClick(val) {
      const { node } = this
      if (val && val !== node.bk_biz_id) {
        if (!this.validateField(node.bk_biz_id, this.rules.bk_biz_id)) {
          this.getHostRegionIspList(node.bk_biz_id)
        }
        node.ip = ''
        node.country = ''
        node.city = ''
        node.name = ''
      }
    },
    handleIpOptClick(host) {
      const { node } = this
      node.plat_id = host.plat_id
      node.country = host.country
      node.city = host.city
      node.carrieroperator = host.carrieroperator
      node.ip = host.ip
      this.setCity(node.country)
      this.validateField(node.ip, this.rules.ip)
    },
    handleIpToggle(toggle) {
      !toggle && this.validateField(this.node.ip, this.rules.ip)
    },
    getIPIsExist(businessId, ip) {
      return isExistUptimeCheckNode({ bk_biz_id: businessId, ip })
    },
    isPromise(value) {
      return value && Object.prototype.toString.call(value) === '[object Promise]'
    },
    async validateNameIsExist() {
      const { node } = this
      return fixNameConflictUptimeCheckNode({
        bk_biz_id: node.bk_biz_id,
        id: node.id,
        name: node.name
      }).then((data) => {
        node.name = data.name
      })
    },
    handleIpChange(v, e) {
      const { ipPopover } = this
      const { ipPopoverContent } = this.$refs
      const { target } = e
      ipPopover.width = target.clientWidth
      if (!ipPopover.instance) {
        ipPopover.instance = this.$bkPopover(target, {
          content: ipPopoverContent,
          arrow: false,
          trigger: 'click',
          placement: 'bottom',
          theme: 'light edit-ip-node',
          duration: [275, 0],
          appendTo: () => this.$refs.ipPopover
        })
        // .instances[0]
      } else {
        ipPopover.instance.reference = target
        ipPopover.instance.content = ipPopoverContent
      }
      ipPopover.instance?.show(100)
    },
    handleOpearatorChange(v) {
      if (v === this.$t('自定义')) {
        this.$nextTick(() => {
          this.$refs.customCarrieroperator.focus()
        })
      }
    },
    async handleOperatorFocus(v, e) {
      this.$nextTick(() => {
        this.$refs.operatorInput.focus()
      })
      if (!this.customOperatorList.length) {
        await this.getCustomOperatorList()
      }
      this.handleOperatorPopoverShow(e)
    },
    handleOperatorPopoverShow(e) {
      const { operatorPopover } = this
      const { operatorPopoverContent } = this.$refs
      const { customCarrieroperator } = this.$refs
      const { target } = e
      operatorPopover.width = target.width
      if (!operatorPopover.instance) {
        operatorPopover.instance = this.$bkPopover(target, {
          content: operatorPopoverContent,
          arrow: false,
          trigger: 'click',
          placement: 'bottom',
          maxWidth: 120,
          theme: 'light edit-operator-node',
          duration: [275, 0],
          appendTo: () => customCarrieroperator
        })
        // .instances[0]
      } else {
        operatorPopover.instance.reference = customCarrieroperator
        operatorPopover.instance.content = operatorPopoverContent
      }
      this.operatorPopover.instance?.show(100)
    },
    handleOperatorOptClick(opreator) {
      this.customCarrieroperator = opreator
    },
    getCustomOperatorList() {
      return selectCarrierOperator().then((data) => {
        this.filterCustomOperatorList = data
        this.customOperatorList = data
      })
    }
  }
}
</script>

<style lang="scss" scoped>
    @mixin fix-bk-checkbox {
      &:after {
        top: 2px;
        left: 5px;
      }
    }

    .node-edit {
      height: calc(100vh - 100px);
      padding-top: 20px;
      .node-edit-item {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        .item-label {
          min-width: 74px;
          text-align: right;
          margin-right: 20px;
          color: #63656e;
          font-size: 14px;
          height: 32px;
          line-height: 32px;
          &.label-required:after {
            content: "*";
            color: red;
            position: relative;
            margin: 2px -7px 0 2px;
            font-size: 12px;
          }
          &.target-item {
            align-self: flex-start;
          }
        }
        .item-container {
          line-height: 1;
          /deep/ .bk-form-radio {
            .icon-check:before {
              content: "";
            }
          }
          .name-container {
            width: 490px;
            /deep/ .tooltips-icon {
              top: 8px;
              right: 10px;
            }
          }
          .operator-radio {
            margin-right: 48px;
            margin-bottom: 0;
            .operator-input {
              /deep/ .bk-form-input {
                border-top: 0;
                border-right: 0;
                border-left: 0;
                width: 120px;
                background-color: #fafbfd;
                &:focus {
                  /* stylelint-disable-next-line declaration-no-important */
                  background-color: #fafbfd !important;

                  /* stylelint-disable-next-line declaration-no-important */
                  border-color: #c4c6cc !important;
                }
              }
            }
          }
          .target-container {
            width: 720px;
            .target-label {
              display: inline-flex;
              align-items: center;
              width: 720px;
              height: 42px;
              background: #fff;
              border-radius: 2px;
              border: 1px solid #dcdee5;
              padding: 0 21px 0 11px;
              cursor: pointer;
              position: relative;
              margin-bottom: 10px;
              input[type="radio"] {
                width: 16px;
                height: 16px;
                outline: none;
                visibility: visible;
                cursor: pointer;
                vertical-align: middle;
                background-color: #fff;
                color: #fff;
                border-radius: 50%;
                border: 1px solid #979ba5;
                display: inline-block;
                background-position: 0 0;

                /* stylelint-disable-next-line property-no-vendor-prefix */
                -webkit-appearance: none;
                position: relative;
                margin: 0 5px 0 0;
                &:checked {
                  color: #3a84ff;
                  background-position: -33px 0;
                  border-color: #3a84ff;
                  +.selected {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    position: absolute;
                    left: 15px;
                    top: 50%;
                    margin-top: -4px;
                    display: block;
                    background: #3a84ff;
                  }
                }
                &:disabled {
                  cursor: not-allowed;
                  background-color: #fafbfd;
                  border-color: #dcdee5;
                }
              }
              .label-container {
                display: flex;
                align-items: center;
                width: 100%;
                height: 100%;
                /deep/ .bk-select {
                  border: 0;
                  box-shadow: none;
                  height: 40px;
                  line-height: 40px;
                  .bk-select-angle.icon-angle-down {
                    display: none;
                  }
                  .bk-select-clear.icon-close {
                    top: 14px;
                  }
                  .bk-select-name {
                    height: 40px;
                    line-height: 40px;
                  }
                }
                .label-text {
                  height: 19px;
                  line-height: 19px;
                  font-size: 14px;
                  color: #63656e;
                }
                .label-input {
                  flex: 1;
                  margin-left: 21px;
                  /deep/ .bk-form-input {
                    border: 0;
                    height: 40px;
                    padding: 0;
                    &:disabled {
                      /* stylelint-disable-next-line declaration-no-important */
                      background-color: #fff !important;
                    }
                  }
                }
                .label-icon-select {
                  flex: 0 0 70px;
                  margin-left: 21px;
                  width: 70px;
                  height: 19px;
                  font-size: 14px;
                  color: #3a84ff;
                  line-height: 19px;
                }
              }
              &.selected {
                border-color: #3a84ff;
              }
              &.disabled {
                color: #ccc;
                cursor: not-allowed;
                .label-text {
                  color: #dcdee5;
                }
              }
              &.is-empty {
                border-color: #ff5656;
              }
              &:last-child {
                margin-bottom: 0;
              }
            }
            /deep/ .tooltips-icon {
              top: 13px;
              right: 100px;
            }
          }
          .business-container {
            display: flex;
            align-items: center;
            .business-select {
              width: 320px;
              // background: #FFFFFF;
            }
            .business-checkbox {
              margin-left: 16px;
              margin-bottom: 0;
              &.auth-disabled {
                cursor: pointer;
              }
            }
            .is-empty {
              .business-select {
                border-color: #f00;
              }
              /deep/ .tooltips-icon {
                right: 30px;
                top: 8px;
              }
            }
          }
          .area-container {
            display: inline-flex;
            width: 514px;
            align-items: center;
            .area-select {
              width: 240px;
              margin-right: 10px;
              background-color: #fff;
            }
            .hint-icon {
              width: 21px;
              height: 21px;
              fill: #fff;
              cursor: pointer;
            }
          }
          .operator-container {
            height: 32px;
            line-height: 32px;
          }
          .default-container {
            .default-checkbox {
              /deep/ .bk-checkbox {
                @include fix-bk-checkbox();
              }
            }
          }
          .button-submit {
            margin-right: 10px;
            /deep/ .icon-loading:before {
              content: ""
            }
          }
        }
      }
      .uptime-check-node-done {
        margin-top: 31px;
      }
      /deep/ .tippy-tooltip {
        padding: 0;
        .ip-popover-container,
        .operator-popover-container {
          max-height: 204px;
          overflow-y: auto;
          .ip-popover,
          .operator-popover {
            padding: 0;
            margin: 0;
            .ip-popover-item,
            .operator-popover-item {
              height: 32px;
              line-height: 32px;
              cursor: pointer;
              display: list-item;
              padding-left: 15px;
              width: 100%;
              .item-text {
                display: inline-block;
                height: 16px;
                line-height: 16px;
                font-size: 12px;
                color: #63656e;
              }
              &:hover {
                background: #e1ecff;
                .item-text {
                  color: #3a84ff;
                }
              }
              .item-status {
                display: inline-block;
                height: 16px;
                line-height: 16px;
                font-size: 12px;
                color: #c4c6cc;
                margin-left: 5px;
              }
            }
          }
          .no-data {
            height: 32px;
            line-height: 32px;
            padding-left: 15px;
            font-size: 12px;
            color: #63656e;
          }
        }
        .operator-popover-container {
          width: 120px;
        }
      }
    }
</style>
