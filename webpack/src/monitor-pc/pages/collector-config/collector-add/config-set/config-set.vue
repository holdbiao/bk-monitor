<template>
  <div class="config-set" ref="configSet" v-bkloading="{ isLoading: loading }">
    <div class="set-edit">
      <div class="edit-item" v-if="config.mode === 'edit'">
        <div class="item-label">ID</div>
        <div class="item-container">{{info.id}}</div>
      </div>
      <div class="edit-item">
        <div class="item-label label-required"> {{ $t('所属业务') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="rules.bizId.validate"
                        :validator="{ content: rules.bizId.message }">
            <bk-select class="reset-width" :placeholder="$t('选择业务')"
                       v-model="info.bizId"
                       :disabled="!canSelectBusiness"
                       @change="handleSelectToggle(arguments, info.bizId, rules.bizId)">
              <bk-option v-for="item in businessList"
                         :key="item.id"
                         :id="item.id"
                         :name="item.text">
              </bk-option>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <div class="edit-item">
        <div class="item-label label-required"> {{ $t('名称') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="rules.name.validate"
                        :validator="{ content: rules.name.message }">
            <bk-input class="reset-width" :placeholder="$t('请输入采集任务名')"
                      v-model.trim="info.name"
                      @change="validateField(info.name, rules.name)">
            </bk-input>
          </verify-input>
        </div>
      </div>
      <div class="edit-item">
        <div class="item-label label-required"> {{ $t('采集对象') }} </div>
        <div class="item-container">
          <bk-select v-model="info.objectId"
                     @selected="handleObjectIdChange"
                     :clearable="false"
                     :disabled="disabled"
                     style="width: 320px;">
            <bk-option-group
              v-for="(group, index) in info.objectTypeList"
              :name="group.name"
              :key="index">
              <bk-option v-for="option in group.children"
                         :key="option.id"
                         :id="option.id"
                         :name="option.name">
              </bk-option>
            </bk-option-group>
          </bk-select>
        </div>
      </div>
      <div class="edit-item">
        <div class="item-label"> {{ $t('采集周期') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="rules.period.validate"
                        :validator="{ content: rules.period.message }">
            <bk-select class="reset-width"
                       v-model="info.period"
                       :clearable="false">
              <bk-option v-for="item in periodList"
                         :key="item.id"
                         :id="item.id"
                         :name="item.name">
              </bk-option>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <div class="edit-item">
        <div class="item-label label-required"> {{ $t('采集方式') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="rules.collectType.validate"
                        :validator="{ content: rules.collectType.message }">
            <bk-select class="reset-width" :placeholder="$t('请选择采集方式')"
                       v-model="info.collectType"
                       :clearable="false"
                       :disabled="disabled"
                       @change="handleCollectTypeChange">
              <!-- process类型只支持进程类的采集对象 -->
              <bk-option v-for="item in collectTypeList"
                         :key="item.name"
                         :id="item.name"
                         :name="item.alias"
                         v-show="item.name !== 'Process' || (info.objectId === 'host_process' && item.name === 'Process')">
              </bk-option>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <div class="edit-item" style="margin-bottom: 10px;" v-if="!['Log', 'SNMP_Trap', 'Process'].includes(info.collectType)">
        <div class="item-label label-required"> {{ $t('选择插件') }} </div>
        <div class="item-container">
          <verify-input
            :show-validate.sync="rules.plugin.validate"
            :validator="{ content: rules.plugin.message }">
            <bk-select
              class="reset-big-width"
              ref="selectPluin" :placeholder="$t('请选择插件')"
              v-model="info.plugin.id"
              searchable
              :clearable="false"
              :disabled="!canSelectPlugin"
              @change="handleSelectToggle(arguments, info.plugin.id, rules.plugin)"
              :remote-method="handleFilterPlugin">
              <bk-option
                v-for="item in filterPluginList"
                :key="item.pluginId"
                :id="item.pluginId"
                :name="item.pluginId">
                <div @click="handlePluginClick(item.pluginId, false, true, item.pluginType)">
                  {{ `${ item.pluginDisplayName ? item.pluginId + '（' + item.pluginDisplayName + '）' : item.pluginId }` }}
                </div>
              </bk-option>
              <div slot="extension" @click="handleToAddPlugin" style="cursor: pointer"><i class="bk-icon icon-plus-circle" style="margin-right: 6px"></i> {{ $t('新增插件') }} </div>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <!-- 选择snmpTrap插件类型 -->
      <div class="edit-item" style="margin-bottom: 10px;" v-if="isSnmpSelected && info.collectType === 'SNMP_Trap'">
        <div class="item-label label-required"> {{ $t('选择插件') }} </div>
        <div class="item-container">
          <verify-input
            :show-validate.sync="rules.plugin.validate"
            :validator="{ content: rules.plugin.message }">
            <bk-select
              class="reset-big-width"
              ref="selectPluin" :placeholder="$t('请选择插件')"
              v-model="info.plugin.snmpv"
              :clearable="false"
              :disabled="!canSelectPlugin">
              <bk-option
                v-for="item in SnmpVersion"
                :key="item.id"
                :id="item.id"
                :name="item.name">
                <div @click="handleSnmpVersion (item.id)">
                  {{item.name}}
                </div>
              </bk-option>
            </bk-select>
          </verify-input>
        </div>
      </div>
      <!-- 日志类型 -->
      <collector-log
        v-if="info.collectType === 'Log'"
        :log-data="logData"
        @log-can-save="handleLogSave"
        ref="collectorLog">
      </collector-log>
      <!-- process 类型 -->
      <process-params
        v-else-if="info.collectType === 'Process'"
        :process-params="processParams"
        ref="process"
        @change="handleProcessParamsChange">
      </process-params>
      <!-- <div class="edit-item" style="margin-bottom: 10px;" v-else>
        <div class="item-label label-required"> {{ $t('选择插件') }} </div>
        <div class="item-container">
          <verify-input :show-validate.sync="rules.plugin.validate"
                        :validator="{ content: rules.plugin.message }">
            <bk-select class="reset-big-width"
                       ref="selectPluin" :placeholder="$t('请选择插件')"
                       v-model="info.plugin.id"
                       searchable
                       :clearable="false"
                       :disabled="!canSelectPlugin"
                       @change="handleSelectToggle(arguments, info.plugin.id, rules.plugin)"
                       :remote-method="handleFilterPlugin">
              <bk-option v-for="item in filterPluginList"
                         :key="item.pluginId"
                         :id="item.pluginId"
                         :name="item.pluginId">
                <div @click="handlePluginClick(item.pluginId, false)">
                  {{ `${ item.pluginDisplayName ? item.pluginId + '（' + item.pluginDisplayName + '）' : item.pluginId }` }}
                </div>
              </bk-option>
              <div
                slot="extension"
                v-authority="{ active: !authority.PLUGIN_MANAGE_AUTH }"
                @click="authority.PLUGIN_MANAGE_AUTH ? handleToAddPlugin() : handleShowAuthorityDetail(collectAuth.PLUGIN_MANAGE_AUTH)"
                style="cursor: pointer">
                <i class="bk-icon icon-plus-circle"
                   style="margin-right: 6px"></i>
                {{ $t('新增插件') }}
              </div>
            </bk-select>
          </verify-input>
        </div>
      </div> -->
      <template v-if="info.plugin.type === 'Exporter'">
        <div class="edit-item edit-item-host" v-show="Object.keys(info.host).length">
          <div class="item-label label-required label-param"> {{ $t('绑定主机') }} </div>
          <div class="item-container">
            <div class="param-container">
              <verify-input class="param-item"
                            :show-validate.sync="rules.host.validate"
                            :validator="{ content: rules.host.message }"
                            position="right">
                <bk-input class="reset-big-width"
                          v-model.trim="info.host.default"
                          @blur="validateHost">
                  <template slot="prepend">
                    <bk-popover placement="top" :tippy-options="tippyOptions">
                      <div class="prepend-text">${host}=</div>
                      <div slot="content">
                        <div> {{ $t('参数名称：') }} {{ info.host.name }}</div>
                        <div> {{ $t('参数类型：') }} {{ paramType[info.host.mode] }}</div>
                        <div> {{ $t('参数说明：') }} {{ info.host.description || '--' }}</div>
                      </div>
                    </bk-popover>
                  </template>
                </bk-input>
              </verify-input>
            </div>
          </div>
        </div>
        <div class="edit-item edit-item-port" v-show="Object.keys(info.port).length">
          <div class="item-label label-param"> {{ $t('绑定端口') }} </div>
          <div class="item-container">
            <div class="param-container">
              <verify-input class="param-item"
                            :show-validate.sync="validateParam(info.port).validate"
                            :validator="{ content: validateParam(info.port).message }"
                            position="right">
                <bk-input class="reset-big-width"
                          v-model.trim="info.port.default"
                          @blur="info.port.default !== '' && validateParam(info.port)">
                  <template slot="prepend">
                    <bk-popover placement="top" :tippy-options="tippyOptions">
                      <div class="prepend-text">${port}=</div>
                      <div slot="content">
                        <div> {{ $t('参数名称：') }} {{ info.port.name }}</div>
                        <div> {{ $t('参数类型：') }} {{ paramType[info.port.mode] }}</div>
                        <div> {{ $t('参数说明：') }} {{ info.port.description || '--' }}</div>
                      </div>
                    </bk-popover>
                  </template>
                </bk-input>
              </verify-input>
            </div>
          </div>
        </div>
      </template>
      <div class="edit-item" v-show="info.plugin.id && !['Log', 'Process'].includes(info.collectType)">
        <div class="item-label label-param"> {{ $t('运行参数') }} </div>
        <div class="item-container" v-if="info.plugin.configJson.length">
          <div class="container-tips">{{ $t('参数的填写也可以使用CMDB变量') }}&nbsp;&nbsp;<span @click="handleVariableTable"> {{ $t('点击查看推荐变量') }} </span></div>
          <div class="param-container">
            <template v-for="(item, index) in info.plugin.configJson">
              <template v-if="item.auth_json !== undefined">
                <!-- snmp多用户 -->
                <auto-multi :key="index"
                            :template-data="SnmpAuthTemplate"
                            :souce-data="item.auth_json"
                            :tips-data="tipsData"
                            :param-type="paramType"
                            :allow-add="!(info.collectType === 'SNMP')"
                            @canSave="snmpAuthCanSave"
                            @triggerData="triggerAuthData">
                </auto-multi>
              </template>
              <template v-else-if="item.auth_priv">
                <verify-input class="param-item"
                              v-if="item.auth_priv[curAuthPriv] && item.auth_priv[curAuthPriv].need"
                              :key="index"
                              :show-validate.sync="item.validate.isValidate"
                              :validator="item.validate"
                              position="right">
                  <!-- 自动补全 -->
                  <auto-complete-input
                    class="reset-big-width"
                    :tips-data="tipsData"
                    :type="item.type"
                    :config="item"
                    @autoHandle="autoHandle"
                    v-model.trim="item.default"
                    :cur-auth-priv="curAuthPriv"
                    @curAuthPriv="handleAuthPriv"
                    @blur="handleParamValidate(item)">
                    <template slot="prepend">
                      <bk-popover placement="top" :tippy-options="tippyOptions">
                        <div class="prepend-text">{{ item.description ? item.description : item.name }}</div>
                        <div slot="content">
                          <div> {{ $t('参数名称：') }} {{ item.name }}</div>
                          <div> {{ $t('参数类型：') }} {{ paramType[item.mode] }}</div>
                          <div> {{ $t('参数说明：') }} {{ item.description || '--' }}</div>
                        </div>
                      </bk-popover>
                    </template>
                  </auto-complete-input>
                </verify-input>
              </template>
              <template v-else>
                <verify-input class="param-item"
                              :key="index"
                              :show-validate.sync="item.validate.isValidate"
                              :validator="item.validate"
                              position="right">
                  <!-- 自动补全 -->
                  <auto-complete-input
                    class="reset-big-width"
                    :tips-data="tipsData"
                    :type="item.type"
                    :config="item"
                    @autoHandle="autoHandle"
                    v-model.trim="item.default"
                    :cur-auth-priv="curAuthPriv"
                    @error-message="msg => handleErrorMessage(msg, item)"
                    @file-change="file => configJsonFileChange(file, item)"
                    @curAuthPriv="handleAuthPriv"
                    @blur="handleParamValidate(item)">
                    <template slot="prepend">
                      <bk-popover placement="top" :tippy-options="tippyOptions">
                        <div class="prepend-text">{{ item.description ? item.description : item.name }}</div>
                        <div slot="content">
                          <div> {{ $t('参数名称：') }} {{ item.name }}</div>
                          <div> {{ $t('参数类型：') }} {{ paramType[item.mode] }}</div>
                          <div> {{ $t('参数说明：') }} {{ item.description || '--' }}</div>
                        </div>
                      </bk-popover>
                    </template>
                  </auto-complete-input>
                </verify-input>
              </template>
            </template>
          </div>
        </div>
        <div class="item-container" v-else>
          <div class="no-param">
            <i class="icon-monitor icon-hint param-icon"></i>
            <span class="param-text"> {{ $t('由于插件定义时未定义参数，此处无需填写。') }} </span>
          </div>
        </div>
      </div>
      <div class="edit-item">
        <div class="item-label"></div>
        <div class="item-container">
          <div class="btn-container">
            <bk-button
              class="btn-preview"
              v-if="!['Log', 'Process'].includes(info.collectType) && info.collectType !== 'SNMP_Trap'"
              theme="default"
              v-show="isShowPreview"
              @click="handlePreview"> {{ $t('指标预览') }}
            </bk-button>
            <bk-button
              :class="['btn-next', { 'disabled': !canNext }]"
              theme="primary"
              :disabled="!canNext"
              @click="handleNext"> {{ $t('下一步') }} </bk-button>
            <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
          </div>
        </div>
      </div>
    </div>
    <div class="set-desc" :style="{ right: !btn.show ? -(descWidth + 1) + 'px' : '0px' }">
      <div class="set-desc-btn" @click="handleIntroductionShow" :style="{ left: btn.show ? '-23px' : '-24px' }">
        <div class="icon" :class="{ 'icon-show': !btn.show }"><i class="icon-monitor icon-double-up"></i></div>
        <!-- <div class="text"> {{ $t('插件说明') }} </div> -->
      </div>
      <div class="set-desc-box"
           :style="{ 'flex-basis': descWidth + 'px', width: descWidth + 'px' }"
           data-tag="resizeTarget"
           @mousedown="handleMouseDown"
           @mousemove="handleMouseMove"
           @mouseout="handleMouseOut">
        <collector-introduction :introduction="introduction"></collector-introduction>
        <div class="resize-line"
             v-show="resizeState.show"
             :style="{ left: (descWidth - resizeState.left) + 'px' }">
        </div>
      </div>
    </div>
    <indicator-preview :options="options"></indicator-preview>
    <variable-table :is-show-variable-table.sync="isShowVariableTable"></variable-table>
  </div>
</template>

<script>
import VerifyInput from '../../../plugin-manager/plugin-instance/set-steps/verify-input'
import IndicatorPreview from './indicator-preview'
import CollectorIntroduction from './collector-introduction'
import VariableTable from './variable-table'
import AutoCompleteInput from './auto-complete-input'
import AutoMulti from './auto-multi'
import CollectorLog from './collector-log'
import ProcessParams from  './process-params.vue'
import PERIOD_LIST from './data'
import { collectConfigDetail, getCollectVariables } from '../../../../../monitor-api/modules/collecting'
import { retrieveCollectorPlugin, listCollectorPlugin } from '../../../../../monitor-api/modules/model'
import { SET_OBJECT_TYPE, SET_INFO_DATA } from '../../../../store/modules/collector-config'
import { deepClone } from '../../../../../monitor-common/utils/utils'
import { createNamespacedHelpers } from 'vuex'
import formLabelMixin from '../../../../mixins/formLabelMixin'
import * as snmp from './snmp'
const { mapMutations, mapGetters } = createNamespacedHelpers('collector-config')

export default {
  name: 'ConfigSet',
  components: {
    VerifyInput,
    IndicatorPreview,
    CollectorIntroduction,
    VariableTable,
    AutoCompleteInput,
    CollectorLog,
    AutoMulti,
    ProcessParams
  },
  mixins: [formLabelMixin],
  inject: ['authority', 'handleShowAuthorityDetail', 'collectAuth'],
  props: {
    config: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      loading: false,
      isShowVariableTable: false,
      info: {
        bizId: window.cc_biz_id,
        name: '',
        objectType: 'SERVICE',
        objectGroupType: 'services',
        objectId: '',
        objectTypeList: [],
        period: 60,
        collectType: '',
        isShowHost: false,
        isShowPort: false,
        host: {},
        port: {},
        plugin: {
          id: '',
          type: '',
          descMd: '',
          isOfficial: false,
          isSafety: false,
          createUser: '',
          updateUser: '',
          metricJson: [],
          configJson: [],
          osTypeList: [],
          snmpv: ''
        }
      },
      rules: {
        bizId: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必选项') }
          ]
        },
        name: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必填项') },
            { required: true, message: this.$t('不能超过50个字符'), validator: this.validateName }
          ]
        },
        objectType: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必填项') }
          ]
        },
        period: {
          validate: false,
          message: '',
          rule: [
            { required: false, message: this.$t('必选项') }
          ]
        },
        collectType: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必选项') }
          ]
        },
        plugin: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必选项') }
          ]
        },
        host: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('必填项') },
            { required: true, message: this.$t('IP地址不能为空'), validator: this.validateIp }
          ]
        },
        ip: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('IP地址不能为空'), validator: this.validateIp }
          ]
        },
        port: {
          validate: false,
          message: '',
          rule: [
            { required: true, message: this.$t('请输入合法的端口'), validator: this.validatePort }
          ]
        },
        user: {
          validate: false,
          message: '',
          rule: [
            { required: false, message: this.$t('必填项') }
          ]
        },
        password: {
          validate: false,
          message: '',
          rule: [
            { required: false, message: this.$t('必填项') }
          ]
        }
      },
      collectTypeList: [],
      filterPluginList: [],
      pluginList: [],
      allPluginList: [],
      options: {
        isShow: false,
        data: [],
        isOfficial: false
      },
      pluginTypeMap: {
        Exporter: 'Exporter',
        Script: 'Script',
        JMX: 'JMX',
        DataDog: 'DataDog',
        // 'Built-In': 'BK-Monitor',
        Pushgateway: 'BK-Pull',
        Log: 'Log',
        Process: 'Process',
        SNMP_Trap: 'SNMP Trap',
        SNMP: 'SNMP'
      },
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
      others: {},
      introduce: {
        [this.$t('主机')]: this.$t('采集的数据为主机操作系统相关的，如CPU NET。'),
        [this.$t('服务')]: this.$t('采集的数据为CMDB中服务模块下的服务实例数据，可以支持多实例的采集，如mysql redis。')
      },
      btn: {
        show: true,
        introduction: true
      },
      methodMd: `${this.$t('插件类型是蓝鲸监控丰富支持采集能力的一种表现，插件的类型将越来越丰富。 往下具体介绍当前每种类型特点')}。\n\n`
                    + '### Exporter\n\n'
                    // eslint-disable-next-line vue/max-len
                    + `${this.$t('Exporter是用于暴露第三方服务的metrics给Prometheus。是Prometheus中重要的一个组件。按蓝鲸监控插件的规范就可以将开源的Exporter插件变成蓝鲸监控的采集能力。 运行的Exporter是go的二进制程序，需要启动进程和占用端口')}。\n\n`
                    + '### Script\n\n'
                    + `${this.$t('Script就是由用户自定义脚本进行Metrics采集。只要符合监控的标准格式就可以把数据采集上来。 支持的脚本有：')}\n\n`
                    + `* Linux Shell，Python，${this.$t('自定义')}\n\n`
                    + `* Windows Shell，Python，VBS，PowerShell,${this.$t('自定义')}\n\n`
                    + `${this.$t('自定义是直接执行，不用解释器进行执行。 如 ./脚本')}\n\n`
                    + '### DataDog\n\n'
                    // eslint-disable-next-line vue/max-len
                    + `${this.$t('Datadog是一个一站式云端性能监控平台，拥有丰富的采集能力。蓝鲸监控兼容了Datadog的采集能力，当前用户不能自定义插件。因为Datadog是由python编写，需要有python可运行环境，不需要占用端口')}。\n\n`
                    + '### JMX\n\n'
                    // eslint-disable-next-line vue/max-len
                    + `${this.$t('JMX可以采集任何开启了JMX服务端口的java进程的服务状态，通过jmx采集java进程的jvm信息，包括gc耗时、gc次数、gc吞吐、老年代使用率、新生代晋升大小、活跃线程数等信息')}。\n\n`
                    + '### BK-pull\n\n'
                    + `${this.$t('BK-pull主要是解决那些只暴露了端口服务的数据源。 通过pull拉取目标的数据')}。\n\n`
                    + '### Log\n\n'
                    + `${this.$t('Log主要是围绕日志相关的内容进行数据的采集，比如日志关键字等')}。`,
      resizeState: {
        show: false,
        ready: false,
        left: 0,
        draging: false,
        minWidth: 400,
        maxWidth: 800
      },
      descWidth: 400,
      tipsData: [], //  插件参数提示数据
      logCanSave: false, //  日志关键词采集能否保存
      logData: {}, // 日志回填数据
      processParams: {},
      isSnmpSelected: false, // 是否已选择snmp 插件
      // snmp 回填数据
      snmpData: {},
      // 是否可下一步
      SnmpCanSave: false,
      SnmpAuthCanSave: false,
      // snmp插件列表
      SnmpVersion: snmp.SnmpVersion,
      SnmpAuthTemplate: [],
      curAuthPriv: '',
      snmpIsOk: false
    }
  },
  computed: {
    ...mapGetters(['infoData']),
    businessList() {
      return this.$store.getters.bizList
    },
    // 是否显示指标预览
    isShowPreview() {
      return this.info.plugin.id !== ''
    },
    // 能否下一步
    canNext() {
      if (this.info.collectType === 'Log') {
        return this.info.plugin.id !== '' && this.logCanSave
      }
      if (this.info.collectType === 'SNMP_Trap') {
        if (this.info.plugin.snmpv === 'snmp_v3') {
          return this.SnmpOther() && this.SnmpCanSave && this.SnmpAuthCanSave
        }
        return this.SnmpOther() && this.SnmpCanSave
      }
      if (this.info.collectType === 'SNMP') {
        const snmpAuthIsOk = +this.info?.plugin?.collectorJson?.snmp_version === 3 ? this.SnmpAuthCanSave : true // eslint-disable-line
        return this.info.name !== '' && this.info.plugin.id !== '' && snmpAuthIsOk && this.snmpIsOk
      }
      return this.info.plugin.id !== '' && this.validateHost()
    },
    // 编辑模式下，采集方式和采集配置不可变
    disabled() {
      return this.config.mode === 'edit'
    },
    canSelectBusiness() {
      return !this.disabled && this.$store.getters.bizId === 0 // window.bizId === 0 全业务
    },
    canSelectPlugin() {
      return !this.disabled && this.info.collectType !== '' // 采集方式不为空
    },
    periodList() {
      return PERIOD_LIST
    },
    introduction() {
      let introduction = {}
      if (this.info.collectType === 'Log') {
        introduction = this.getLogIntroduction()
        return introduction
      }
      if (this.info.collectType === 'SNMP_Trap'
       && this.info.plugin.snmpv !== ''
       && this.info.plugin.snmpv !== undefined) {
        introduction = this.getSnmpIntroduction()
        return introduction
      }
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { configJson, metricJson, id, descMd, ...others } = this.info.plugin
      if (id) {
        introduction = {
          ...others,
          content: descMd,
          pluginId: id,
          type: 'plugin'
        }
      } else {
        introduction = { type: 'method', content: this.methodMd }
      }
      return introduction
    }
  },
  watch: {
    'info.objectGroupType': { // 更新采集对象组的类型
      handler: 'handleUpdateObjectType',
      immediate: true
    }
  },
  async created() {
    this.infoData && (this.info = deepClone(this.infoData))
    if (this.info.objectTypeList.length === 0) {
      await this.$store.dispatch('collector-config/getCollectorObject').then((data) => {
        this.info.objectTypeList = data
        const { objectId } = this.$route.params
        if (objectId) {
          this.handleSetObjTypeById(objectId)
          this.info.objectId = objectId
        }
      })
    }
    if (!this.info.objectId && !this.$route.params.pluginId) {
      this.info.objectId = 'component'
    }
  },
  mounted() {
    this.handleSetPlugin()
    if (this.config.mode === 'edit') {
      this.bizId = this.config.data.bizId
    } else {
      if (parseInt(this.$store.getters.bizId, 10) === 0) {
        this.info.bizId = ''
      }
    }
    this.handleConfig(this.config)
    this.resizeState.maxWidth = this.$refs.configSet.clientWidth
    // this.initFormLabelWidth()
  },
  beforeDestroy() {
    document.body.style.cursor = ''
    this.resizeState.dragging = false
    this.resizeState.show = false
    this.resizeState.ready = false
  },
  methods: {
    ...mapMutations([SET_OBJECT_TYPE, SET_INFO_DATA]),
    //  获取日志右边栏展示的内容
    snmpAuthCanSave(is) {
      this.SnmpAuthCanSave = is
    },
    triggerAuthData(v) {
      if (this.info.plugin.configJson) {
        this.info.plugin.configJson.forEach((item) => {
          if (item.auth_json) {
            return item.auth_json = v
          }
          return { ...item }
        })
      }
    },
    // 获取当前AuthPriv选项用于联动
    handleAuthPriv(val) {
      this.curAuthPriv = val
      this.autoHandle()
    },
    // 校验snmptrap运行参数
    //
    SnmpVersionValidate() {
      if (this.config.set.mode === 'edit') {
        this.autoHandle()
        this.SnmpCanSave = false
      } else {
        this.autoHandle()
      }
    },
    autoHandle() {
      if (this.info.collectType === 'SNMP_Trap') {
        this.SnmpCanSave = this.SnmpValidate()
      } else if (this.info.collectType === 'SNMP') {
        this.snmpIsOk = this.handleSnmpParamValidate()
      }
    },
    SnmpOther() {
      return this.info.plugin.snmpv !== '' && this.info.plugin.snmpv !== undefined && this.info.name !== ''
    },
    SnmpValidate() {
      const { plugin } = this.info
      let result = false
      if (plugin.configJson.length !== 0) {
        if (plugin.snmpv === 'snmp_v1' || plugin.snmpv === 'snmp_v2c') {
          // eslint-disable-next-line arrow-body-style
          result = plugin.configJson.every((item) => {
            if (item.key !== snmp.community) {
              return item.type === 'file' ? item.default.value !==  '' : item.default !== ''
            }
            return true
          })
        } else {
          result = plugin.configJson.every((item) => {
            if (item.auth_json === undefined && item.key !== snmp.community) {
              return item.type === 'file' ? item.default.value !==  '' : item.default !== ''
            }
            return true
          })
          // const excludeValidateMap = {
          //   authPriv: ['context_name'],
          //   authNoPriv: ['context_name', 'privacy_protocol', 'privacy_passphrase'],
          //   noAuthNoPriv: ['context_name', 'privacy_protocol',
          //     'privacy_passphrase', 'authentication_protocol', 'authentication_passphrase']
          // }
          // result = plugin.configJson.every((item) => {
          //   if (!excludeValidateMap[this.curAuthPriv].includes(item.key)) {
          //     return item.type === 'file' ? item.default.value !==  '' : item.default !== ''
          //   }
          //   return true
          // })
        }
      } else {
        result = false
      }
      return result
      // if ()
    },
    handleSnmpParamValidate() {
      const { plugin } = this.info
      const version = plugin.collectorJson.snmp_version
      // eslint-disable-next-line no-restricted-syntax
      for (const item of plugin.configJson) {
        if ([1, 2].includes(+version)) {
          if (item.default === '') {
            return false
          }
        } else {
          const includesMap = ['port', 'host']
          if (includesMap.includes(item.key) && item.default === '') {
            return false
          }
        }
      }
      return true
    },
    //  获取日志右边栏展示的内容
    getLogIntroduction() {
      return {
        pluginId: this.$t('日志关键字采集'),
        type: 'plugin',
        isOfficial: true,
        isSafety: true,
        osTypeList: ['linux', 'windows'],
        content: `## ${this.$t('功能介绍')}\n\n`
                        + `${this.$t('日志关键字插件，通过对于日志文件的关键匹配进行计数，并且存储最近一条原始日志内容。')}\n\n`
                        + `${this.$t('采集后的日志关键字数据可以在视图中查看变化趋势，也可以在策略里面配置告警规则。')}\n\n`
                        + `## ${this.$t('关键字规则配置方法')}\n\n`
                        + `### ${this.$t('参考例子：')}\n\n`
                        + `### ${this.$t('原始日志内容：')}\n\n`
                        + '```\nm=de4x5 init_module: Input/output error\n```\n\n'
                        + `### ${this.$t('关键字规则：')}\n\n`
                        + '```\nm=(?P<moudle>.*) init_module: Input/output error\n```\n\n'
                        + `${this.$t('就会得到关键字')} ${this.$t('并和')} moudle=de4x5 ${this.$t('匹配的次数。')}\n\n`
      }
    },
    getSnmpIntroduction() {
      const SnmpIntroduction = {
        snmp_v1: '## SNMP Trap V1\n\n'
                        + `### ${this.$t('功能介绍')}\n\n`
                        // eslint-disable-next-line vue/max-len
                        + `snmp trap${this.$t('将默认搭建')} snmp trap server${this.$t('接收不同设备的发送的事件数据。默认端口为')}162。${this.$t('注意选择对应的')}snmp${this.$t('版本')},${this.$t('本版本为')}V1。\n\n`
                        + `### ${this.$t('参数说明')}\n\n`
                        + `* Trap${this.$t('服务端口： 是trap接收的端口，默认为')}162\n\n`
                        // eslint-disable-next-line vue/max-len
                        + `* ${this.$t('绑定地址')}： ${this.$t('trap服务启动时绑定的地址，默认为0.0.0.0，如果要指定网卡，需要使用CMDB变量来使用如：')}`
                        + '```{{ target.host.bk_host_innerip }}```\n\n'
                        + `* ${this.$t('Yaml配置文件：是通过命令行工具将mib文件转换的yaml配置文件。')}\n\n`
                        + `* ${this.$t('团体名')}${this.$t('： Community')}\n\n`
                        + `* ${this.$t('是否汇聚')}：${this.$t('默认是开启的，采集周期内默认相同的内容会汇聚到成一条并且计数。')}\n\n\n`,
        snmp_v2c: '## SNMP Trap V2c\n\n'
                        + `### ${this.$t('功能介绍')}\n\n`
                        // eslint-disable-next-line vue/max-len
                        + `snmp trap${this.$t('将默认搭建')} snmp trap server${this.$t('接收不同设备的发送的事件数据。默认端口为')}162。${this.$t('注意选择对应的')}snmp${this.$t('版本')},${this.$t('本版本为')}V2c。\n\n`
                        + `### ${this.$t('参数说明')}\n\n`
                        + `* ${this.$t('Trap服务端口： 是trap接收的端口，默认为')}162\n\n`
                        // eslint-disable-next-line vue/max-len
                        + `* ${this.$t('绑定地址')}： ${this.$t('trap服务启动时绑定的地址，默认为0.0.0.0，如果要指定网卡，需要使用CMDB变量来使用如：')}`
                        + '```{{ target.host.bk_host_innerip }}```\n\n'
                        + `* ${this.$t('Yaml配置文件：是通过命令行工具将mib文件转换的yaml配置文件。')}\n`
                        + `* ${this.$t('团体名')}${this.$t('： Community ')}\n`
                        + `* ${this.$t('是否汇聚')}：${this.$t('默认是开启的，采集周期内默认相同的内容会汇聚到成一条并且计数。')}\n\n\n`,
        snmp_v3: `## ${this.$t('SNMP Trap V3')}\n\n`
                        + `### ${this.$t('功能介绍')}\n\n`
                        // eslint-disable-next-line vue/max-len
                        + `snmp trap${this.$t('将默认搭建')} snmp trap server${this.$t('接收不同设备的发送的事件数据。默认端口为')}162。${this.$t('注意选择对应的')}snmp${this.$t('版本')},${this.$t('本版本为')}V3。\n\n`
                        + `### ${this.$t('参数说明')}\n\n`
                        + `* ${this.$t('Trap服务端口： 是trap接收的端口，默认为')}162\n`
                        // eslint-disable-next-line vue/max-len
                        + `* ${this.$t('绑定地址')}： ${this.$t('trap服务启动时绑定的地址，默认为0.0.0.0，如果要指定网卡，需要使用CMDB变量来使用如：')}`
                        + '```{{ target.host.bk_host_innerip }}```\n'
                        + `* ${this.$t('Yaml配置文件：是通过命令行工具将mib文件转换的yaml配置文件。')}\n`
                        + `* ${this.$t('上下文名称')}${this.$t(' Context name')}\n`
                        + `* ${this.$t('安全名')}${this.$t(' Security name')}\n`
                        // eslint-disable-next-line vue/max-len
                        + `* ${this.$t('安全级别')}${this.$t(' Security level ，')} ${this.$t('选项有')} noAuthNoPriv， authNoPriv ， authPriv\n`
                        // eslint-disable-next-line vue/max-len
                        + `* ${this.$t('验证协议')}${this.$t(' Authentication protocol，')} ${this.$t('选项有')} MD5，SHA，DES，AES\n`
                        + `* ${this.$t('验证口令')}${this.$t(' Authentication passphrase')}\n`
                        + `* ${this.$t('隐私协议')}${this.$t(' Privacy protocol ,')}${this.$t('选项有')} DES ， AES\n`
                        + `* ${this.$t('私钥')}${this.$t(' Privacy paasphrase')}\n`
                        + `* ${this.$t('设备ID')}${this.$t(' Engine ID')}\n`
                        + `* ${this.$t('是否汇聚')}：${this.$t('默认是开启的，采集周期内默认相同的内容会汇聚到成一条并且计数。')}\n\n`
      }
      return {
        pluginId: this.$t('snmp trap'),
        type: 'plugin',
        isOfficial: true,
        isSafety: true,
        osTypeList: ['linux', 'windows'],
        content: SnmpIntroduction[this.info.plugin.snmpv]
      }
    },
    handleLogSave(v) {
      this.logCanSave = v
      if (this.config.mode === 'add') {
        this.info.plugin.id = v ? 'default_log' : ''
      }
    },
    handleMouseDown(e) {
      if (this.resizeState.ready) {
        let { target } = event
        while (target && target.dataset.tag !== 'resizeTarget') {
          target = target.parentNode
        }
        this.resizeState.show = true
        const rect = e.target.getBoundingClientRect()
        document.onselectstart = function () {
          return false
        }
        document.ondragstart = function () {
          return false
        }
        const handleMouseMove = (event) => {
          this.resizeState.dragging = true
          this.resizeState.left = rect.right - event.clientX
        }
        const handleMouseUp = () => {
          if (this.resizeState.dragging) {
            this.resizeState.left = this.resizeState.left < this.resizeState.minWidth
              ? this.resizeState.minWidth
              : this.resizeState.left
            this.resizeState.left = Math.min(this.resizeState.left, this.$refs.configSet.clientWidth)
            this.descWidth = this.resizeState.left
          }
          document.body.style.cursor = ''
          this.resizeState.dragging = false
          this.resizeState.show = false
          this.resizeState.ready = false
          document.removeEventListener('mousemove', handleMouseMove)
          document.removeEventListener('mouseup', handleMouseUp)
          document.onselectstart = null
          document.ondragstart = null
        }
        document.addEventListener('mousemove', handleMouseMove)
        document.addEventListener('mouseup', handleMouseUp)
      }
    },
    handleMouseMove() {
      if (this.btn.show) {
        let { target } = event
        while (target && target.dataset.tag !== 'resizeTarget') {
          target = target.parentNode
        }
        const rect = target.getBoundingClientRect()
        const bodyStyle = document.body.style
        if (rect.width > 12 && event.pageX - rect.left < 8) {
          bodyStyle.cursor = 'col-resize'
          this.resizeState.ready = true
        }
      }
    },
    handleMouseOut() {
      document.body.style.cursor = ''
      this.resizeState.ready = false
    },
    validateField(value, ruleMap) {
      const { rule } = ruleMap
      const res = {
        validate: false,
        message: ''
      }
      // eslint-disable-next-line
      for (let i = 0; i < rule.length; i++) {
        const item = rule[i]
        if (item.required && value === '') { // 空值
          res.validate = true
          ruleMap.validate = true
          res.message = item.message
          ruleMap.message = item.message
          return res
        } if (item.required && value
                        && item.validator && typeof item.validator === 'function') { // 非空有校验器
          res.validate = !item.validator(value)
          ruleMap.validate = !item.validator(value)
          if (ruleMap.validate) {
            res.message = item.message
            ruleMap.message = item.message
            return res
          }
        }
      }
      // v3.2
      // rule.forEach((item) => {
      //   if (item.required && value === '') { // 空值
      //     res.validate = true
      //     ruleMap.validate = true
      //     res.message = item.message
      //     ruleMap.message = item.message
      //     return res
      //   } if (item.required && value
      //                   && item.validator && typeof item.validator === 'function') { // 非空有校验器
      //     res.validate = !item.validator(value)
      //     ruleMap.validate = !item.validator(value)
      //     if (ruleMap.validate) {
      //       res.message = item.message
      //       ruleMap.message = item.message
      //       return res
      //     }
      //   }
      // })
      ruleMap.validate = false
      return res
    },
    validate() {
      const { info } = this
      const { rules } = this
      const includeFields = ['bizId', 'name', 'objectType', 'period', 'collectType']
      const keys = Object.keys(rules)
      keys.forEach((item) => {
        // validate=false 时需要重新触发校验，不校验运行参数部分
        !rules[item].validate && includeFields.includes(item) && this.validateField(info[item], rules[item])
      })
      let configValidate = false
      if (this.info.plugin && this.info.plugin.configJson) {
        // const configValidateList = this.info.plugin.configJson.map(item => {
        //   if(!item.auth_json === undefined){
        //     return this.handleParamValidate(item)
        //   }
        // })
        const configValidateList = []
        this.info.plugin.configJson.forEach((item) => {
          if (!item.auth_json === undefined) {
            configValidateList.push(this.handleParamValidate(item))
          }
          if (item.type === 'file') {
            configValidateList.push(this.handleParamValidate(item))
          }
        })
        configValidate = configValidateList.some(item => item.validate)
      }
      return keys.every(item => rules[item].validate === false) && !configValidate
    },
    validateStrLength(str, length = 50) {
      const cnLength = (str.match(/[\u4e00-\u9fa5]/g) || []).length // 汉字占 2 个字符
      const enLength = (str || '').length - cnLength
      return (cnLength * 2) + enLength > length
    },
    validateName(value) {
      return !this.validateStrLength(value)
    },
    validateIp(value) {
      return value.trim().length > 0
    },
    validatePort(value) {
      return /^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$/.test(value) // 0~65535
    },
    validateParam(value) {
      const { rules } = this
      let res = {
        validate: false
      }
      if (value.default !== '') { // 不为空才交给是否符合规则
        if (['host', 'ip'].includes(value.name)) {
          res = this.validateField(value.default, rules.ip)
        } else if (value.name === 'port') {
          res = this.validateField(value.default, rules.port)
        }
      } else {
        rules.ip.validate = false
        rules.port.validate = false
      }
      return res
    },
    handleParamValidate(item) {
      const { rules } = this
      let res = {
        validate: false
      }
      if (item.type === 'file') {
        res.validate = item.validate.isValidate
        return res
      }
      if (item.default !== '' || ['host', 'ip', 'port'].includes(item.name)) { // 不为空才交给是否符合规则
        if (['host', 'ip'].includes(item.name)) {
          res = this.validateField(item.default, rules.ip)
        } else if (item.name === 'port') {
          res = this.validateField(item.default, rules.port)
        }
      } else {
        rules.ip.validate = false
        rules.port.validate = false
      }
      item.validate.isValidate = res.validate
      item.validate.content = res.message
      return res
    },
    validateHost() {
      // 插件类型为 'Exporter' 需要校验绑定主机
      const hostRule = this.rules.host
      if (this.info.plugin.type === 'Exporter') {
        return this.validateField(this.info.host.default, hostRule)
      }
      hostRule.validate = false
      return true
    },
    // 以上为校验器
    // 选择框折叠时触发校验
    handleSelectToggle(toggle, value, rulesMap) {
      if (!toggle) {
        this.validateField(value, rulesMap)
      }
    },
    // 采集方式发生改变
    handleCollectTypeChange(newV, oldV) {
      if (oldV && newV !== oldV) {
        // 采集方式改变时，清空已有的插件信息
        this.handleDelPLugin()
        this.handleSnmpPugin()
        if (this.info.collectType === 'SNMP_Trap') {
          this.$set(this.info.plugin, 'snmpv', '')
        }
      }
      // 筛选插件列表
      this.filterPluginList = this.allPluginList.filter(item => item.pluginType === newV
      && item.labelInfo.second_label === this.info.objectId)
      this.pluginList = this.filterPluginList.slice()
      this.handleSnmpPugin()
      // process类型插件后端内置
      if (newV === 'Process') {
        this.info.plugin.id = 'default_process'
      }
    },
    // SNMP
    handleSnmpPugin() {
      if (this.info.collectType === 'SNMP_Trap') {
        this.isSnmpSelected = true
        // if (!isFirst) {
        //   this.$set(this.info.plugin, 'snmpv', '')
        // }
      }
    },
    handleDelPLugin() {
      const { plugin } = this.info
      plugin.id = ''
      plugin.type = ''
      plugin.descMd = ''
      plugin.isOfficial = false
      plugin.isSafety = false
      plugin.createUser = ''
      plugin.updateUser = ''
      plugin.configJson = []
      plugin.metricJson = []
      plugin.osTypeList = []
      this.$refs.selectPluin && (this.$refs.selectPluin.selectedNameCache = '')
    },
    // 选择插件版本时触发
    async handleSnmpVersion(id) {
      this.info.plugin.id = id
      const index = 2
      this.curAuthPriv = snmp.AuthPrivList[index]
      this.pluginTypeInfo(id, false, true)
      this.SnmpCanSave = false
      this.SnmpVersionValidate()
    },
    // 选择插件时触发
    async handlePluginClick(val, loading = true, needSetConfig = true, curPluginType) {
      const { mode } = this.config
      if (curPluginType === 'SNMP_Trap') {
        if (this.isSnmpSelected) {
          this.$set(this.info.plugin, 'snmpv', '')
        }
        this.isSnmpSelected = true
      } else {
        if (mode === 'edit') {
          this.$set(this.info.plugin, 'snmpv', `snmp_${this.snmpData.version}`)
          this.isSnmpSelected = true
        } else {
          this.isSnmpSelected = false
        }
        await this.pluginTypeInfo(val, loading, needSetConfig)
      }
      // this.initFormLabelWidth()
    },
    async pluginTypeInfo(val, loading, needSetConfig) {
      // 获取提示输入数据
      this.loading = true
      await getCollectVariables().then((data) => {
        this.tipsData = data
      })
      // 先去获取有关的所有插件，并处理数据
      await this.getPluginInfo(val).then((data) => {
        const { plugin } = this.info
        const { configJson, host, port,
          isShowHost, isShowPort } = this.handlePluginConfigJson(data.plugin_type, data.config_json)
        plugin.type = data.plugin_type
        plugin.descMd = data.description_md
        plugin.isOfficial = data.is_official
        plugin.isSafety = data.is_safety
        plugin.createUser = data.create_user
        plugin.updateUser = data.update_user
        plugin.metricJson = data.metric_json || []
        if (needSetConfig) {
          if (data.plugin_type === 'SNMP_Trap') {
            plugin.configJson = (configJson || []).map((item) => {
              if (item.auth_json !== undefined) {
                if (this.config.mode === 'edit') {
                  this.SnmpAuthTemplate = deepClone(item.template_auth_json[0].map(item => (
                    { ...item, validate: { isValidate: false, content: '' } }
                  )))
                } else {
                  this.SnmpAuthTemplate = deepClone(item.auth_json[0].map(item => (
                    { ...item, validate: { isValidate: false, content: '' } }
                  )))
                }
                plugin.SnmpAuthTemplate = this.SnmpAuthTemplate
                return { auth_json: item.auth_json.map(items => items.map(item => ({
                  ...item,
                  validate: {
                    isValidate: false,
                    content: ''
                  }
                }))) }
              }
              return {
                ...item,
                validate: {
                  isValidate: false,
                  content: ''
                }
              }
            })
          } else if (data.plugin_type === 'SNMP') {
            this.info.plugin.collectorJson = data.collector_json
            plugin.configJson = (configJson || []).map((item) => {
              this.SnmpAuthTemplate = []
              if (item.auth_json !== undefined) {
                if (this.config.mode === 'edit') {
                  const authJson = item.auth_json
                  authJson.forEach((set) => {
                    set.forEach((p) => {
                      const mode = p.mode === 'collector' ? 'collector' : 'plugin'
                      const paramDefault = this.info.params[mode][p.key]
                      p.default = paramDefault
                    })
                  })
                  return item
                }
                return { auth_json: [item.auth_json].map(items => items.map(item => ({
                  ...item,
                  validate: {
                    isValidate: false,
                    content: ''
                  }
                }))) }
              }
              if (this.config.mode === 'edit') {
                const mode = item.mode === 'collector' ? 'collector' : 'plugin'
                const paramDefault = this.info.params[mode][item.key]
                item.default = paramDefault
              }

              return {
                ...item,
                validate: {
                  isValidate: false,
                  content: ''
                }
              }
            })
          } else {
            plugin.configJson = (configJson || []).map((item) => {
              try {
                if (this.config.mode === 'edit') {
                  const mode = item.mode === 'collector' ? 'collector' : 'plugin'
                  const paramDefault = this.info.params[mode][item.key || item.name]
                  if (item.type === 'file') {
                    item.default = paramDefault.filename
                    item.file_base64 = paramDefault.file_base64
                  } else {
                    item.default = paramDefault
                  }
                }
              } catch (error) {
                console.log(error)
              }
              return {
                ...item,
                validate: {
                  isValidate: false,
                  content: ''
                }
              }
            })
          }
        }
        plugin.osTypeList = data.os_type_list || []
        this.info.isShowHost = isShowHost
        this.info.isShowPort = isShowPort
        this.info.host = host
        this.info.port = port
        this.info.plugin.supportRemote = data.is_support_remote
      })
        .catch((err) => {
          console.log(err)
        })
        .finally(() => this.loading = false)
    },
    // 指标预览显示，传参options
    handlePreview() {
      const { plugin } = this.info
      const { options } = this
      options.pluginId = plugin.id
      options.data = plugin.metricJson
      options.isOfficial = plugin.isOfficial
      options.isShow = true
    },
    handleCancel() {
      this.$router.push({
        name: 'collect-config'
      })
    },
    validateProcessParams() {
      if (this.info.collectType === 'Process') {
        return this.$refs.process && this.$refs.process.validate()
      }
      return true
    },
    handleNext() {
      // 清空缓存的info
      this[SET_INFO_DATA](null)
      if (this.validate() && this.validateProcessParams()) {
        if (this.info.collectType === 'Log') {
          this.info.log = this.$refs.collectorLog.getLogParams()
          this.info.log.log_path = this.info.log.log_path.map(path => path.trim())
        } else if (this.info.collectType === 'Process') {
          this.info.process = this.processParams
        }
        this.$emit('update:config', {
          ...this.config,
          set: { data: this.info, others: this.others, mode: 'edit', supportRemote: this.info.plugin.supportRemote }
        })
        this.$emit('next')
      }
    },
    //
    async handleConfig(v) {
      this.loading = true
      const { set } = v
      this.others = set.others || {}
      if (set.mode === 'edit') { // 从下一个页面跳转过来（上一步）
        this.info = set.data
        if (set.data.log) {
          this.logData = set.data.log
          this.logCanSave = true
        } else if (set.data.process) {
          this.processParams = set.data.process
        } else if (set.data.collectType === 'SNMP_Trap') {
          this.isSnmpSelected = true
          const { plugin } = set.data
          this.info.plugin.id = plugin.id
          if (plugin.snmpv === this.SnmpVersion[2].id) {
            this.SnmpAuthTemplate = plugin.SnmpAuthTemplate
            plugin.configJson.map((item) => {
              if (item.key === 'security_level') {
                this.curAuthPriv = item.default
              }
            })
          }
          this.SnmpCanSave = true
          this.SnmpAuthCanSave = true
        }
        if (set.data.collectType === 'SNMP') {
          this.snmpIsOk = this.handleSnmpParamValidate()
          this.SnmpAuthCanSave = true
        }
      } else if (v.mode === 'edit') { // 编辑
        const { id, updateParams: { pluginId } } = v.data
        const data = await this.getConfigInfo(id)
        if (data) {
          await this.handlePluginClick(pluginId, true, true)
        }
        if (data.collect_type === 'SNMP') {
          this.snmpIsOk = this.handleSnmpParamValidate()
          this.SnmpAuthCanSave = true
        }
        // await Promise.all([this.handlePluginClick(pluginId), this.getConfigInfo(id)]).catch(() => {})
      }
      await this.getPluginList().then(() => {
        this.info.collectType && this.handleCollectTypeChange(this.info.collectType)
      })
        .catch(() => {})
      this.loading = false
    },
    // 处理配置信息
    handleConfigInfo(data) {
      const pluginInfo = data.plugin_info
      const { collector, plugin } = data.params
      const tmpConfigJson = pluginInfo.config_json
      // 将插件信息中 configJson 的值，改为 data.params 中对应的值
      tmpConfigJson.forEach((item) => {
        if (item.mode === 'collector') {
          item.default = collector[item.name]
        } else {
          item.default = plugin[item.name]
        }
      })
      const { configJson, host,
        port, isShowHost, isShowPort } = this.handlePluginConfigJson(pluginInfo.plugin_type, tmpConfigJson)
      if (data.collect_type === 'Log') {
        this.logData = data.params.log
      } else if (data.collect_type === 'Process') {
        this.processParams = data.params.process
      } else if (data.collect_type === 'SNMP_Trap') {
        this.snmpData = data.params.snmp_trap
      }
      return {
        info: {
          id: data.id,
          bizId: data.bk_biz_id,
          name: data.name,
          objectType: data.target_object_type,
          objectId: data.label,
          period: collector.period,
          collectType: data.collect_type,
          isShowHost,
          isShowPort,
          host,
          port,
          params: data.params,
          plugin: {
            collectorJson: pluginInfo.collector_json,
            id: pluginInfo.plugin_id,
            type: pluginInfo.plugin_type,
            descMd: pluginInfo.description_md, //
            isOfficial: pluginInfo.is_official,
            isSafety: pluginInfo.is_safety,
            createUser: pluginInfo.create_user,
            updateUser: pluginInfo.update_user,
            metricJson: pluginInfo.metric_json,
            configJson: (configJson || []).map(item => ({
              ...item,
              validate: {
                isValidate: false,
                content: ''
              }
            })),
            osTypeList: pluginInfo.os_type_list,
            supportRemote: pluginInfo.is_support_remote
          }
        },
        others: {
          targetNodeType: data.target_node_type,
          // targetNodes: data.target_nodes,
          targetNodes: data.target,
          remoteCollectingHost: data.remote_collecting_host
        }
      }
    },
    // 获取插件列表
    getPluginList() {
      this.loading = true
      const params = {
        search_key: '',
        plugin_type: '',
        page: 1,
        page_size: 1000,
        order: '-update_time',
        status: 'release'
      }
      return new Promise((resolve, reject) => {
        listCollectorPlugin(params).then((data) => {
          resolve(data)
          const { count } = data
          const { list } = data
          if (count) {
            const collectTypeList = []
            Object.keys(count).forEach((item) => {
              const set = this.pluginTypeMap[item]
              if (set) {
                collectTypeList.push({
                  name: item,
                  alias: set
                })
              }
            })
            this.collectTypeList = collectTypeList
          }
          this.allPluginList = this.handlePluginList(list)
        })
          .catch((err) => {
            this.loading = false
            reject(err)
          })
      })
    },
    // 处理插件列表数据
    handlePluginList(data) {
      const res = []
      if (data.length) {
        data.forEach((item) => {
          res.push({
            pluginId: item.plugin_id,
            pluginDisplayName: item.plugin_display_name,
            pluginType: item.plugin_type,
            isOfficial: item.is_official,
            createUser: item.create_user,
            updateUser: item.update_user,
            updateTime: item.update_time,
            labelInfo: item.label_info
          })
        })
      }
      return res
    },
    // 获取插件信息
    getPluginInfo(id) {
      this.loading = true
      return new Promise((resolve, reject) => {
        retrieveCollectorPlugin(id).then((data) => {
          resolve(data)
        })
          .catch((err) => {
            this.loading = false
            reject(err)
          })
      })
    },
    setNavTitle(data) {
      this.$store.commit(
        'app/SET_NAV_TITLE',
        `${this.$t('route-' + '编辑配置').replace('route-', '')} - #${data.id} ${data.name}`
      )
    },
    //  获取采集配置信息（编辑）
    getConfigInfo(id) {
      this.loading = true
      return new Promise((resolve) => {
        collectConfigDetail({ id }).then((data) => {
          this.setNavTitle(data)
          const { info, others } = this.handleConfigInfo(data)
          if (data.params.snmp_trap) {
            this.curAuthPriv = data.params.snmp_trap.security_level
            this.SnmpCanSave = true
            this.SnmpAuthCanSave = true
          }
          this.info = info
          this.others = others
          resolve(data)
        })
          .catch(() => {
            this.loading = false
            resolve(false)
          })
      })
    },
    handlePluginConfigJson(type, data = []) {
      let configJson = []
      // snmp 多用户
      const snmpAuthJson = []
      let host = null
      let port = null
      // 如果是插件类型为 'Exporter'，则显示绑定主机和绑定端口
      data = data.map((item) => {
        if (item.type === 'file' && (typeof item.default === 'object') && item.key !== 'yaml') {
          const temp = deepClone(item.default)
          item.default = temp.filename
          item.file_base64 = temp.file_base64
        }
        return item
      })
      if (type === 'Exporter') {
        data.forEach((item) => {
          if (item.mode === 'collector' && item.name === 'host') {
            host = item
          } else if (item.mode === 'collector' && item.name === 'port') {
            port = item
          } else {
            configJson.push(item)
          }
        })
      } else if (type === 'SNMP_Trap') {
        configJson.push(...data)
        // data.forEach((item) => {
        //   if (item.auth_json !== undefined){
        //     snmpAuthJson = item.auth_json
        //   } else {
        //     configJson.push(item)
        //   }
        // })
      } else if (type === 'SNMP' && this.config.mode === 'edit') {
        configJson = data.map((item) => {
            if (item.auth_json) item.auth_json = [item.auth_json.map(set => {  // eslint-disable-line
            return { ...set, validate: { isValidate: false, content: '' } }
          })]
          return item
        })
        // configJson.push(...data)
      } else {
        configJson.push(...data)
      }
      return {
        configJson,
        host,
        port,
        isShowHost: host !== null,
        isShowPort: port !== null,
        snmpAuthJson
      }
    },
    handleFilterPlugin(v) {
      const keyword = (v || '').toLowerCase()
      this.filterPluginList = this.pluginList.filter(item => item.pluginId.toLowerCase().indexOf(keyword) > -1
      || (item.pluginDisplayName || '').toLowerCase().indexOf(keyword) > -1)
    },
    handleToAddPlugin() {
      this[SET_INFO_DATA](this.info)
      this.$router.push({
        name: 'plugin-add',
        params: { objectId: this.info.objectId }
      })
    },
    async handleSetPlugin() {
      const { params } = this.$route
      if (params.pluginType) {
        this.info.collectType = params.pluginType
      }
      if (params.pluginType && params.pluginId) {
        this.info.objectId = params.objectId
        await this.handlePluginClick(params.pluginId)
        this.info.plugin.id = params.pluginId
      }
    },
    handleIntroductionShow() {
      this.btn.show = !this.btn.show
    },
    handleObjectIdChange(val) {
      // 获取选中的采集对象组的类型
      const groupObj = this.info.objectTypeList.find(item => item.children.length
      && (item.children.findIndex(child => child.id === val) > -1))
      // 更新采集对象组类型
      this.handleUpdateObjectType(groupObj.id)
      if (this.info.collectType && this.info.collectType !== 'SNMP_Trap') {
        this.handleDelPLugin()
        if (this.info.collectType === 'Log') {
          // 更新采集方式为log的提交状态
          this.logCanSave && this.handleLogSave(true)
        } else if (this.info.collectType === 'Process' && val !== 'host_process') {
          // Process采集方式只有在采集对象为host_process(进程)时生效
          this.info.collectType = ''
        }
        this.filterPluginList = this.allPluginList.filter(item => item.pluginType === this.info.collectType
        && item.labelInfo.second_label === val)
        this.pluginList = this.filterPluginList.slice()
      } else {
        this.handleSnmpPugin()
      }
      this.handleSetObjTypeById(val)
    },
    handleSetObjTypeById(val) {
      this.info.objectType = this.info.objectTypeList.some(item => item.id === 'services'
      && item.children.some(set => set.id === val)) ? 'SERVICE' : 'HOST'
    },
    handleVariableTable() {
      this.isShowVariableTable = true
    },
    handleUpdateObjectType(v) {
      this[SET_OBJECT_TYPE](v === 'services' ? 'SERVICE' : '')
    },
    handleProcessParamsChange(params) {
      this.processParams = params
    },
    configJsonFileChange(file, item) {
      item.default = file.name
      item.file_base64 = file.fileContent
    },
    handleErrorMessage(msg, item) {
      item.validate.isValidate = !!msg
      item.validate.content = msg
    }
  }
}
</script>

<style lang="scss" scoped>
    .config-set {
      display: flex;
      position: relative;
      overflow: hidden;
      background-size: 100% 100%;
      background-image: linear-gradient(270deg, #dcdee5 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%);
      .set-edit {
        flex: 1;
        min-width: 529px;
        padding: 41px 35px 41px 42px;
        height: calc(100vh - 82px);
        overflow: auto;
        .edit-item {
          display: flex;
          align-items: center;
          min-height: 32px;
          margin-bottom: 20px;
          &.edit-item-host,
          &.edit-item-port {
            margin-bottom: 0px;
          }
          .item-label {
            position: relative;
            min-width: 75px;
            height: 32px;
            line-height: 32px;
            text-align: right;
            margin-right: 34px;
            color: #63656e;
            font-size: 12px;
            &.label-required:after {
              position: absolute;
              content: "*";
              color: #f00;
              right: -9px;
              font-size: 12px;
            }
            &.label-param {
              align-self: flex-start;
            }
          }
          .item-container {
            .container-tips {
              padding: 7px 0 9px 0;
              color: #63656e;
              span {
                color: #3a84ff;
                cursor: pointer;
              }
            }
            .reset-width {
              width: 320px;
            }
            .reset-big-width {
              width: 500px;
            }
            /deep/ .bk-select.is-disabled {
              background: #fafbfd;
              border-color: #dcdee5;
            }
            .type-radio {
              width: 94px;
              /deep/ .icon-check:before {
                content: ""
              }
            }
            /deep/ .param-container {
              display: flex;
              flex-direction: column;
              .param-item {
                margin-bottom: 5px;

                @media only screen and (min-width: 1720px) {
                  .reset-width {
                    width: 438px;
                  }
                }
                :last-child {
                  margin-bottom: 0;
                }
                .group-prepend,
                .file-input-wrap .prepend {
                  width: auto;
                  max-width: 50%;
                  background: #fafbfd;
                  .bk-tooltip,
                  .bk-tooltip-ref {
                    width: 100%;
                  }
                  /deep/ .prepend-text {
                    line-height: 30px;
                    padding: 0 20px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                  }
                }
                /deep/ .group-prepend,
                /deep/ .file-input-wrap .prepend {
                  width: auto;
                  max-width: 50%;
                  background: #fafbfd;
                  .bk-tooltip,
                  .bk-tooltip-ref {
                    width: 100%;
                  }
                  /deep/ .prepend-text {
                    line-height: 30px;
                    padding: 0 20px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                  }
                }
                /deep/ .bk-form-input {
                  width: 100%;
                }
              }
              .prepend-text {
                line-height: 30px;
                padding: 0 20px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
              }
            }
            /deep/ .bk-radio-text:before {
              content: " ";
              width: 30px;
              height: 1px;
              border-bottom: 1px dashed #c4c6cc;
              border-bottom-left-radius: 2px;
              position: absolute;
              left: 20px;
              top: 20px;
            }
            .is-empty {
              .bk-select {
                border-color: #ff5656;
              }
              /deep/ .tooltips-icon {
                top: 8px;
              }
            }
            .btn-container {
              font-size: 0;
              .btn-preview {
                margin-right: 10px;
              }
              .btn-next {
                margin-right: 10px;
                &.disabled {
                  background: #dcdee5;
                  color: #fff;
                }
              }
            }
            .no-param {
              display: inline-flex;
              align-items: center;
              width: auto;
              height: 32px;
              .param-icon {
                width: 16px;
                height: 16px;
                color: #ffa327;
                font-size: 16px;
              }
              .param-text {
                height: 16px;
                font-size: 12px;
                color: #63656e;
                margin-left: 7px;
              }
            }
          }
        }
      }
      .set-desc {
        position: absolute;
        right: 1px;
        z-index: 0;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        transition: right .3s;
        border-right: 1px solid #dcdee5;
        &-box {
          min-height: calc(100vh - 82px);
          width: 400px;
          min-width: 400px;
          border-left: 1px solid #dcdee5;
          position: relative;
          right: 0;
          box-sizing: border-box;
        }
      }
      .set-desc-show {
        right: -400px;
        border-right: 0;
      }
      .set-desc-btn {
        background: #fafbfd;
        height: 100px;
        width: 24px;
        border: 1px solid #dcdee5;
        border-radius: 8px 0 0 8px;
        position: absolute;
        left: -24px;
        text-align: center;
        padding-top: 43px;
        line-height: 100%;
        z-index: 9;
        .icon {
          color: #979ba5;
          font-size: 18px;
          transform: rotate(90deg);
          margin-bottom: 6px;
        }
        &:hover {
          background: #e1ecff;
          color: #3a84ff;
          border-color: #3a84ff;
          cursor: pointer;
          .icon {
            color: #3a84ff;
          }
        }
        .icon-show {
          transform: rotate(-90deg);
        }
      }
    }
</style>
