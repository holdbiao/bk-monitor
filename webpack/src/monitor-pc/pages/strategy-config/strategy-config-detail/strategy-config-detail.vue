<template>
  <div class="strategy-detail" :class="{ 'strategy-detail-loading': allLoading }" v-bkloading="{ isLoading: allLoading }">
    <div class="detail-header">
      {{$t('如需变更策略信息请点击')}}
      <span
        v-authority="{ active: !authority.MANAGE_AUTH }"
        v-if="strategyStatus !== 'DELETED'"
        class="header-btn"
        @click="authority.MANAGE_AUTH ? handleToStrategyEdit() : handleShowAuthorityDetail()">
        {{ $t('编辑策略') }}
      </span>
      <span class="header-btn" @click="record.show = true">{{$t('查看变更记录')}}</span>
      <span class="right-text">{{ $t(strategy.enabled ? '停用该策略' : '启用该策略') }}</span>
      <div class="switch-wrap">
        <bk-switcher
          size="small"
          v-model="strategy.enabled"
          theme="primary"
          @click.native="handleEditStatus"
          v-if="strategyItem.length"
          :disabled="strategyStatus !== '' && strategyStatus !== 'UNCHANGED'">
        </bk-switcher>
        <div
          v-if="!authority.MANAGE_AUTH"
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="switch-wrap-modal"
          @click.stop.prevent="!authority.MANAGE_AUTH && handleShowAuthorityDetail()">
        </div>
      </div>
    </div>
    <div class="strategy-config-detail">
      <div class="strategy-detail-left">
        <div class="detail-content">
          <div class="detail-own">
            <div class="detail-own-title">{{ $t('基本信息') }}</div>
            <div class="detail-own-item">
              <span class="item-label"> {{ $t('所属业务') }} </span>
              <span>{{ header.bizId }}</span>
            </div>
            <div class="detail-own-item">
              <span class="item-label"> {{ $t('策略名称') }} </span>
              <span>{{ header.name }}</span>
            </div>
            <div class="detail-own-item">
              <span class="item-label"> {{ $t('监控对象') }} </span>
              <span>{{ header.firstName }}—{{ header.secondName }}</span>
            </div>
            <div class="detail-own-item">
              <span class="item-label"> {{ $t('标签') }} </span>
              <span class="label-list">
                <span
                  class="label-tag"
                  v-show="header.labels"
                  v-for="(item, i) in header.labels"
                  :key="item + i">{{item.replace(/\//g, ' / ')}}</span>
              </span>
            </div>
          </div>
          <!-- 监控项组件 -->
          <strategyConfigDetailTarget
            :target="target"
            :strategy-list="strategyItem"
            @show-target="targetShow = true"
            @dimension-list-change="handleDimensionListChange"
            @target-loading="handleTargetLoading">
          </strategyConfigDetailTarget>
          <!-- 触发条件table表格 -->
          <div class="set-more">
            <div class="set-more-title">{{ $t('高级设置') }}</div>
            <div class="set-more-content">
              <table class="content-table">
                <tbody>
                  <tr>
                    <td style="width: 140px;" class="table-title"> {{ $t('触发条件') }} </td>
                    <td>{{ $t('在') }} <span class="bold-span">{{ advanceSet.triggerConfig.checkWindow }}</span> {{ $t('个周期内满足') }} <span class="bold-span">{{advanceSet.triggerConfig.count}}</span> {{ $t('次检测算法触发告警；') }} </td>
                  </tr>
                  <tr>
                    <td style="width: 140px;" class="table-title"> {{ $t('恢复条件') }} </td>
                    <td>{{ $t('连续') }} <span class="bold-span">{{ advanceSet.recoveryConfig.checkWindow }}</span> {{ $t('个周期内不满足触发条件表示恢复；') }} </td>
                  </tr>
                  <tr>
                    <td rowspan="1" class="border-left table-title">{{ $t('无数据告警') }}</td>
                    <td class="border-right"><bk-switcher style="margin-right: 5px;" theme="primary" v-model="advanceSet.noDataConfig.isEnabled" size="small" disabled></bk-switcher>
                      <div style="display: inline-block;" v-if="advanceSet.noDataConfig.isEnabled">
                        {{ $t('当数据连续丢失') }} <span class="bold-span">{{ advanceSet.noDataConfig.continuous }}</span> {{ $t('个周期后触发告警') }}
                        <template v-if="advanceSet.noDataConfig.aggDimension && advanceSet.noDataConfig.aggDimension.length">
                          ，{{$t('基于以下维度')}}
                          <span class="common-label" v-for="item in advanceSet.noDataConfig.aggDimension" :key="item">
                            {{item}}
                          </span>
                          {{$t('进行判断')}}
                        </template>
                      </div>
                      <template v-else>
                        {{$t('暂未设置无数据告警')}}
                      </template>
                    </td>
                  </tr>
                  <tr>
                    <td rowspan="1" class="table-title"><span class="table-title-position">{{ $t('告警通知模板') }}</span></td>
                    <td class="table-alarm-template"><pre>{{ advanceSet.messageTemplate }}</pre></td>
                  </tr>
                </tbody>
              </table>
              <div class="set-more-btn" @click="handleShowPreviewTemplate">{{ $t('模板预览') }}</div>
            </div>
          </div>
          <!-- 通知方式 -->
          <div class="set-notice" v-if="actionType.length">
            <div class="set-notice-title">{{ $t('通知设置') }}</div>
            <div class="set-notice-item">
              <span class="item-label"> {{ $t('推送通知') }} </span>
              <div class="item-content">
                <bk-checkbox class="item-check" :disabled="true" :checked="true"> {{ $t('发生告警时通知') }} </bk-checkbox>
                <bk-checkbox v-if="actionList.config.sendRecoveryAlarm" :disabled="true" style="margin-left: 30px" v-model="actionList.config.sendRecoveryAlarm" :true-value="true" :false-value="false"> {{ $t('告警恢复时通知') }} </bk-checkbox>
              </div>
            </div>
            <div class="set-notice-item">
              <span class="item-label"> {{ $t('通知间隔') }} </span>
              <div class="item-content"> {{ $t('若告警未恢复并且未确认，则每隔') }} <span class="bold-span">{{ actionList.config.alarmInterval }}</span> {{ $t('分钟再进行告警') }} </div>
            </div>
            <div class="set-notice-item">
              <span class="item-label"> {{ $t('通知时间段') }} </span>
              <div class="item-content">{{ actionList.config.alarmStartTime }}~{{ actionList.config.alarmEndTime }}</div>
            </div>
            <div class="set-notice-item" style="align-items: flex-start">
              <span class="item-label" style="padding-top: 2px;"> {{ $t('通知告警组') }} </span>
              <div class="item-group">
                <div class="item-group-alarm" v-if="actionType.includes('notice')">
                  <div v-for="(item, key) in actionList.noticeGroupList"
                       :key="key"
                       class="group-alarm"
                       @click="handleShowAlarmGroupDetail(item)">
                    {{ item.displayName }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 监控目标组件 -->
        <monitor-dialog
          v-if="target.target && target.target.length"
          width="960"
          :title="$t('查看监控目标')"
          :need-footer="false"
          :value.sync="targetShow">
          <strategy-config-detail-table :table-data="target.target" :target-type="target.bkTargetType" :obj-type="target.bkObjType"></strategy-config-detail-table>
        </monitor-dialog>
        <!-- 详情页 组件 -->

        <alarm-group-detail :id="alarmGroup.id" :detail="alarmGroup" @edit-group="handleEditAlarmGroup"></alarm-group-detail>
        <!-- 模板预览 -->
        <strategy-template-preview
          v-if="header.scenario && advanceSet.messageTemplate"
          :dialog-show.sync="advanceSet.previewTemplate"
          :template="advanceSet.messageTemplate"
          :scenario="header.scenario">
        </strategy-template-preview>
        <!-- 变更记录 -->
        <change-record :record-data="record.data" :show.sync="record.show"></change-record>
      </div>
      <!-- 策略辅助视图 -->
      <div class="strategy-detail-right ml20"
           :style="{ width: isNaN(strategyView.rightWidth) ? strategyView.rightWidth : `${strategyView.rightWidth}px` }">
        <div class="right-wrapper" v-if="curMetricItem && !allLoading">
          <strategy-view
            ref="strategyView"
            :cur-metric-item="curMetricItem"
            :target-list="selectorTarget"
            :dimension-list="dimensionList"
            :where="curMetricItem.aggCondition">
          </strategy-view>
          <div class="drag" @mousedown="handleMouseDown"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { strategyConfigDetail, getScenarioList, bulkEditStrategy } from '../../../../monitor-api/modules/strategies'
import { strategySnapshot } from '../../../../monitor-api/modules/alert_events'
import { collapseMixin, strategyThresholdMixin } from '../../../common/mixins'
import { transformDataKey } from '../../../../monitor-common/utils/utils'
import strategyConfigDetailTarget from './strategy-config-detail-target.vue'
import strategyConfigDetailTable from './strategy-config-detail-table.vue'
import MonitorDialog from '../../../../monitor-ui/monitor-dialog/monitor-dialog'
import AlarmGroupDetail from '../../alarm-group/alarm-group-detail/alarm-group-detail'
import StrategyTemplatePreview from '../strategy-config-set/strategy-template-preview/strategy-template-preview'
import ChangeRecord from '../../../components/change-record/change-record'
import * as ruleAuth from '../authority-map'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import StrategyView from '../strategy-config-set/strategy-view/strategy-view.vue'

export default {
  name: 'StrategyConfigDetail',
  components: {
    strategyConfigDetailTarget,
    strategyConfigDetailTable,
    MonitorDialog,
    AlarmGroupDetail,
    StrategyTemplatePreview,
    ChangeRecord,
    StrategyView
  },
  mixins: [collapseMixin, strategyThresholdMixin, authorityMixinCreate(ruleAuth)],
  props: {
    title: String // 标题
  },
  provide() {
    const authority = {}
    Object.defineProperty(authority, 'MANAGE_AUTH', {
      get: () => this.authority.ALARM_GROUP_MANAGE_AUTH
    })
    return {
      authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail,
      alarmGroupAuth: {
        MANAGE_AUTH: ruleAuth.ALARM_GROUP_MANAGE_AUTH
      }
    }
  },
  data() {
    return {
      active: 1,
      strategyTargetShow: false,
      panels: [
        { name: this.$t('策略详情'), label: this.$t('策略详情') },
        { name: this.$t('监控目标'), label: this.$t('监控目标') }
      ],
      header: {
        name: ''
      },
      strategyItem: [],
      advanceSet: { // 触发条件table数据
        messageTemplate: '',
        noDataConfig: {},
        recoveryConfig: {},
        triggerConfig: {},
        previewTemplate: false
      },
      actionList: {}, // 通知方式数据
      actionType: [], // 通知方式类型
      targetShow: false,
      target: {
      }, // 监控指标数据
      scenarioList: [],
      fromEvent: false,
      loading: false,
      targetLoading: true,
      // 策略快照title
      strategyStatusMap: {
        UPDATED: this.$t('（已修改）'),
        DELETED: this.$t('（已删除）'),
        UNCHANGED: ''
      },
      strategyStatus: '',
      alarmGroup: {
        show: false,
        id: 0,
        title: ''
      },
      record: {
        show: false,
        data: {}
      },
      strategy: {
        enabled: false,
        id: 0,
        switch: false
      },
      strategyView: {
        rightWidth: '40%',
        range: [300, 1200]
      },
      // 监控维度
      dimensions: []
    }
  },
  computed: {
    // 是否显示监控目标  存在objectType且不来自事件中心且不是服务拨测类型
    isShowTargetTab() {
      return (this.header.objectType !== null && this.header.objectType)
        && !this.fromEvent && !~this.header.scenario.indexOf('uptimecheck')
    },
    // loading是当前页面 targetLoading是strategy-config-detail-target组件派发的loading
    allLoading() {
      return this.loading || this.targetLoading
    },
    curMetricItem() {
      if (this.strategyItem && this.strategyItem.length) {
        const thresholds = this.strategyItem[0].detectAlgorithmList || []
        const algorithm = {
          deadly: [],
          warning: [],
          remind: []
        }
        const levelMap = {
          1: 'deadly',
          2: 'warning',
          3: 'remind'
        }
        thresholds.reduce((algorithm, next) => {
          const key = levelMap[next.level]
          const algorithmList = next.algorithmList.map(item => ({
            type: item.algorithmType,
            config: item.algorithmType === 'IntelligentDetect'
              ? { ...item.algorithmConfig, sensitivity_value: item.algorithmConfig.sensitivityValue }
              : this.handleThreshold2Config(item.algorithmConfig),
            title: this.$t('静态阈值'),
            algorithmUnit: item.algorithmUnit
          }))
          algorithm[key].push(...algorithmList)
          return algorithm
        }, algorithm)
        return {
          ...this.strategyItem[0],
          metricName: this.strategyItem[0].metricField,
          // 兼容老数据格式
          algorithm,
          indexStatement: this.strategyItem[0].keywordsQueryString,
          metricAliaName: this.strategyItem[0].itemName
        }
      }
      return null
    },
    dimensionList() {
      if (this.curMetricItem?.aggDimension?.length && this.dimensions.length) {
        return this.dimensions.filter(item => this.curMetricItem.aggDimension.includes(item.id))
      }
      return this.curMetricItem?.aggDimension?.map(id => ({ id, name: id })) || []
    },
    selectorTarget() {
      return transformDataKey(this.target.target, true)
    }
  },
  created() {
    this.handleDetailConfig()
  },
  beforeRouteEnter(to, from, next) {
    next((vueModule) => {
      const vm = vueModule
      vm.fromEvent = from.name === 'event-center-detail'
    })
  },
  methods: {
    // 起停用策略
    handleEditStatus() {
      const { enabled, id } = this.strategy
      if (!enabled) {
        this.$bkInfo({
          title: this.$t('请确认是否停用'),
          confirmFn: async () => {
            await this.$nextTick()
            const result = await  bulkEditStrategy({ id_list: [id], edit_data: { is_enabled: enabled } })
              .catch(() => {
                this.strategy.enabled = !enabled
                return false
              })
            this.$bkMessage({ theme: 'success', message: result ? this.$t('停用成功') :  this.$t('停用失败') })
          },
          cancelFn: () => {
            this.strategy.enabled = !enabled
          }
        })
      } else {
        bulkEditStrategy({ id_list: [id], edit_data: { is_enabled: enabled } }).then(() => {
          this.$bkMessage({ theme: 'success', message: this.$t('启用成功') })
        })
          .catch(() => {
            this.strategy.enabled = !enabled
            return false
          })
      }
    },
    handleTabChange(active) {
      this.strategyTargetShow = active !== 1
      this.active = active
    },
    getDetailData() {
      const { params } = this.$route
      if (this.fromEvent) {
        params.bk_biz_id = this.$route.params.bizId
        return strategySnapshot({
          id: params.eventId,
          bk_biz_id: params.bizId
        }).then(res => transformDataKey(res))
          .catch(() => {})
      }
      return strategyConfigDetail({
        id: params.id
      }).then(res => transformDataKey(res))
        .catch(() => {})
    },
    handleDimensionListChange(dimensionMap, dimensions) {
      this.dimensions = dimensions || []
      const { noDataConfig } = this.advanceSet
      if (noDataConfig?.aggDimension?.length) {
        const data = noDataConfig.aggDimension.map(id => dimensionMap.get(id) || id)
        noDataConfig.aggDimension = data
      }
    },
    // 编辑告警组
    handleEditAlarmGroup(id) {
      this.alarmGroup.show = false
      this.$router.push({
        name: 'alarm-group-edit',
        params: { id }
      })
    },
    // 处理策略详情数据
    async handleDetailConfig() {
      this.loading = true
      this.active = 1
      try {
        this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
        this.scenarioList = await getScenarioList().then(res => res)
          .catch(() => {})
        const detailData = await this.getDetailData()
        this.handleDetailData(detailData)
        this.loading = false
      } catch (error) {
        this.$store.commit('app/SET_NAV_TITLE', ' ')
        this.loading = false
        this.targetLoading = false
      }
    },
    // 点击模板预览触发
    handleShowPreviewTemplate() {
      this.advanceSet.previewTemplate = true
    },
    // 点击告警组项目查看详情
    handleShowAlarmGroupDetail(item) {
      if (item.id) {
        this.alarmGroup.show = true
        this.alarmGroup.title = item.displayName
        this.alarmGroup.id = item.id
      }
    },
    // 分离详情数据到各个子组件
    handleDetailData(res) {
      this.handleHeaderData(res)
      res.itemList.forEach(item => (item.descVisible = true))
      this.strategyItem = res.itemList
      this.strategy.id = res.id
      this.strategy.enabled = res.isEnabled
      this.strategy.switch = res.isEnabled
      this.record.data = {
        createUser: res.createUser,
        createTime: res.createTime,
        updateUser: res.updateUser,
        updateTime: res.updateTime
      }
      this.handleTriggerList(res)
      this.handleActionList(res)
      this.strategyStatus = this.fromEvent ? res.strategyStatus : ''
      const { id } = res // 详情id
      const status = this.strategyStatusMap[res.strategyStatus]
      this.$store.commit('app/SET_NAV_TITLE', this.fromEvent
        ? `${this.$t('route-' + '策略详情').replace('route-', '')} - #${id} ${res.name}${status}`
        : `${this.$t('route-' + '策略详情').replace('route-', '')} - #${id} ${res.name}`)
      this.handleTableData(res)
    },
    // header数据处理
    handleHeaderData(data) {
      const { bizList } = this.$store.getters
      const bizId = bizList.find(item => +item.id === +data.bkBizId)
      let firstName = ''
      let secondName = ''
      this.scenarioList.forEach((item) => {
        item.children.forEach((el) => {
          if (el.id === data.scenario) {
            firstName = el.name
            secondName = item.name
          }
        })
      })
      this.header = {
        id: data.id,
        bizId: bizId.text,
        name: data.name,
        scenario: data.scenario,
        objectType: data.bkObjType,
        firstName,
        secondName,
        labels: data.labels
      }
    },
    // advanceSet触发告警模块数据处理
    handleTriggerList(res) {
      const { noDataConfig, messageTemplate } = res
      const { triggerConfig, recoveryConfig } = res.itemList[0]
      this.advanceSet = { noDataConfig, messageTemplate, triggerConfig, recoveryConfig, previewTemplate: false }
    },
    // 策略目标数据处理
    handleTableData(res) {
      const { bkTargetType, bkObjType, bkTargetDetail } = res
      this.target = {
        bkTargetType,
        bkObjType,
        target: bkTargetDetail
      }
    },
    // 告警通知数据处理
    handleActionList(res) {
      this.actionType = res.actionList.map(item => item.actionType)
      if (this.actionType.includes('notice')) {
        this.actionList = res.actionList.find(item => item.actionType === 'notice')
      } else {
        this.actionList = res.actionList[0]
      }
    },
    async handleTargetLoading(v) {
      await this.$nextTick()
      this.targetLoading = v
    },
    // 跳转策略编辑事件
    handleToStrategyEdit() {
      this.$router.push({ name: 'strategy-config-edit', params: { id: this.$route.params.id } })
    },

    handleMouseDown(e) {
      const node = e.target
      const { parentNode } = node

      if (!parentNode) return

      const nodeRect = node.getBoundingClientRect()
      const rect = parentNode.getBoundingClientRect()
      document.onselectstart = function () {
        return false
      }
      document.ondragstart = function () {
        return false
      }
      const handleMouseMove = (event) => {
        const [min, max] = this.strategyView.range
        const newWidth = rect.right - event.clientX + nodeRect.width
        if (newWidth < min) {
          this.strategyView.rightWidth = min
        } else {
          this.strategyView.rightWidth = Math.min(newWidth, max)
        }
      }
      const handleMouseUp = () => {
        document.body.style.cursor = ''
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
        document.onselectstart = null
        document.ondragstart = null
      }
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    // // 复制链接事件
    // handleCopyLink () {
    //     const url = window.location.href
    //     copyText(url, (err) => {
    //         this.$bkMessage('error', err)
    //     })
    //     this.$bkMessage({ theme: 'success', message: this.$t('链接复制成功') })
    // }
  }
}
</script>

<style lang="scss" scoped>
@import "strategy-detail-mixin";

.strategy-config-detail {
  display: flex;
  .strategy-detail-left {
    flex: 1;
  }
  .strategy-detail-right {
    .right-wrapper {
      position: relative;
      background: #fff;
      box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .1);
      min-height: calc(100% - 16px);
    }
  }
}
.drag {
  position: fixed;
  top: 0;
  width: 8px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-items: center;
  outline: 0;
  &::after {
    content: " ";
    height: 18px;
    width: 0;
    border-left: 2px dotted #c4c6cc;
    position: absolute;
    left: 2px;
  }
  &:hover {
    cursor: col-resize;
  }
}
.strategy-detail {
  color: #63656e;
  font-size: 12px;
  min-height: calc(100vh - 80px);
  &.strategy-detail-loading {
    left: 0;
    right: 0;
    max-height: calc(100vh - 80px);

    /* stylelint-disable-next-line declaration-no-important */
    position: absolute !important;
  }
  .detail-header {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    .header-btn {
      color: #3a84ff;
      cursor: pointer;
      margin-left: 10px;
    }
    .right-text {
      margin-left: auto;
      color: #3a84ff;
      margin-right: 6px;
    }
    .switch-wrap {
      position: relative;
      &-modal {
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        background: transparent;
        z-index: 29;
        &:hover {
          cursor: pointer;
        }
      }
    }
  }
  .detail-own {
    min-height: 190px;

    @include common-panel;
    &-title {
      @include common-panel-title;
    }
    &-item {
      @include common-panel-item;
      .label-list {
        display: flex;
        flex-wrap: wrap;
        .label-tag {
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: left;
          height: 24px;
          line-height: 16px;
          border-radius: 2px;
          background: #f0f1f5;
          margin: 0 2px 2px 0;
          padding: 4px 10px;
        }
      }
    }
  }
  .set-more {
    padding-bottom: 18px;

    @include common-panel;
    &-title {
      @include common-panel-title;
    }
    &-content {
      .content-table {
        width: 100%;
        border-collapse: collapse;
        tr {
          td {
            min-height: 16px;
            line-height: 16px;
            text-align: left;
            padding-bottom: 20px;
            &.table-title {
              text-align: right;
              padding-right: 24px;
              position: relative;
              color: #979ba5;
            }
            .bold-span {
              font-weight: bold;
              margin: 0 1px;
            }
            .common-label {
              @include common-label;
            }
            .table-title-position {
              position: absolute;
              width: 140px;
              left: -24px;
              top: 8px;
            }
            &.table-alarm-template {
              padding-bottom: 0;
              pre {
                word-break: break-all;
                line-height: 120%;
                padding: 15px 20px;
                background: #f5f6fa;
                border-radius: 2px;
                margin: 0 40px 0 0;
                white-space: pre-wrap;
                min-height: 120px;
              }
            }
          }
        }
      }
    }
    &-btn {
      color: #3a84ff;
      cursor: pointer;
      margin: 8px 0 0 140px;
    }
  }
  .set-notice {
    margin-bottom: 20px;

    @include common-panel;
    &-title {
      @include common-panel-title;
    }
    &-item {
      @include common-panel-item;
      .item-label {
        color: #979ba5;
        text-align: right;
      }
      .item-group {
        display: flex;
        flex-direction: column;
        &-alarm {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          margin-bottom: 10px;
          .group-alarm {
            font-size: 12px;
            background: #f0f1f5;
            border-radius: 2px;
            height: 24px;
            line-height: 24px;
            padding: 0 10px;
            margin-right: 6px;
            &:hover {
              cursor: pointer;
              color: #3a84ff;
            }
          }
        }
      }
    }
    /deep/ .bk-form-checkbox.is-disabled .bk-checkbox-text {
      color: #63656e;
    }
  }
}
</style>
