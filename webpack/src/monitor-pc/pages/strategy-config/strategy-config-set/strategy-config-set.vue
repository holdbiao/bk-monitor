<!--
 * @Date: 2021-06-25 14:32:26
 * @LastEditTime: 2021-06-25 16:02:12
 * @Description: 
-->
<template>
  <div class="strategy-config" v-bkloading="{ isLoading: loading }" :class="{ 'set-loading': loading }">
    <div class="strategy-config-left strategy-config-set">
      <div class="set-add">
        <div class="set-add-title">{{ $t('基本信息') }}</div>
        <div class="set-add-item">
          <span class="item-label"> {{ $t('所属') }} </span>
          <div class="item-content">
            <bk-select v-model="header.bizId" searchable :clearable="false" :readonly="bizId > 0">
              <bk-option
                v-for="(option, index) in bizList"
                :key="index"
                :id="option.id"
                :name="option.text">
              </bk-option>
            </bk-select>
          </div>
        </div>
        <div class="set-add-item">
          <span class="item-label"> {{ $t('策略名称') }} </span>
          <div class="item-content">
            <bk-input ref="strategyName" :maxlength="128" :minlength="1" :class="{ 'error-check': validate.strategyName && header.strategyName.length === 0 }" v-model.trim="header.strategyName"></bk-input>
            <div class="error-tips need-position" v-show="validate.strategyName && header.strategyName.length === 0"> {{ $t('必填项，请输入') }} </div>
          </div>
        </div>
        <div class="set-add-item">
          <span class="item-label"> {{ $t('监控对象') }} </span>
          <div class="item-content">
            <!-- <i class="icon-monitor icon-tips item-icon" v-bk-tooltips="typeToolTip"></i> -->
            <bk-select class="header-select" v-model="header.typeId" :readonly="left.metricList.length > 0" :clearable="false">
              <bk-option-group
                v-for="(group, index) in scenarioList"
                :name="group.name"
                :key="index">
                <bk-option
                  v-for="(option, groupIndex) in group.children"
                  :key="groupIndex"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-option-group>
            </bk-select>
          </div>
        </div>
        <div class="set-add-item">
          <span class="item-label multi-label no-required"> {{ $t('标签') }} </span>
          <div class="item-content">
            <multi-label-select
              mode="select"
              :checked-node="header.labels"
              :tree-data="labelTreeData"
              @checkedChange="handleLabelCheckedChange" />
          </div>
        </div>
      </div>
      <ul class="set-panel" v-if="!left.metricList.length" v-bkloading="{ isLoading: dimensionValueLoading }">
        <li class="set-panel-item" v-for="(item, index) in metricSetList" :key="item.id" @click="handleSelectMetric(item)">
          <i class="item-icon icon-monitor icon-mc-plus-fill" :ref="'setPanel-' + index"></i>
          <span class="item-content" :class="{ 'need-split': index < 2 }">{{ item.name }}</span>
        </li>
      </ul>
      <template v-else>
        <div v-bkloading="{ isLoading: dimensionValueLoading }" class="set-wrapper" v-for="(metric, key) in left.metricList" :key="key" @click="handleLeftClick(key)">
          <div class="set-wrapper-title">
            {{curMetricItem.metricAliaName}}<span v-if="!(['time_series', 'log'].includes(curMetricItem.dataTypeLabel) && $i18n.locale !== 'zhCN')" class="title-desc">（{{curMetricItem.metricDes}}）</span>
            <i v-if="curMetricItem && curMetricItem.metricDesc.length" class="icon-monitor icon-tips set-desc" @click="curMetricItem.metricDescVisible = !curMetricItem.metricDescVisible"></i>
            <span @click="handleEditMetric(metric,key)" class="title-icon icon-monitor icon-bianji"></span>
            <span @click="handleDeleteMetric(metric,key)" class="icon-monitor icon-mc-delete"></span>
          </div>
          <div class="right-form">
            <template v-if="curMetricItem && curMetricItem.metricDesc.length">
              <strategy-custom-desc :desc-list="curMetricItem.metricDesc" v-model="curMetricItem.metricDescVisible"></strategy-custom-desc>
            </template>
            <!-- <template v-if="curMetricItem.dataTypeLabel === 'event'"> -->
            <template v-if="curMetricItem.dataTypeLabel === 'event' && curMetricItem.dataSourceLabel === 'bk_monitor'">
              <div class="right-form-item">
                <span class="item-label item-required"> {{ $t('告警级别') }} </span>
                <div class="item-content no-hidden">
                  <bk-radio-group v-model="algorithm.eventLevel">
                    <bk-radio v-for="(item,index) in panel"
                              :key="index"
                              :value="item.level">
                      {{item.name}}
                    </bk-radio>
                  </bk-radio-group>
                  <div class="error-tips need-position" style="bottom: -19px;" v-show="validate.eventLevel && algorithm.eventLevel < 1"> {{ $t('必选项，请选择') }} </div>
                </div>
              </div>
            </template>
            <!-- <template v-if="sourceTypeConst !== 'BK-EVENT'"> -->
            <template v-if="curMetricItem.dataTypeLabel === 'log' && curMetricItem.dataSourceLabel !== 'bk_monitor'">
              <div class="right-form-item mt-10">
                <span class="item-label item-required"> {{ $t('检索语句') }} </span>
                <div class="item-content">
                  <bk-input class="item-content-input" v-model.trim="curMetricItem.indexStatement" @change="handleQueryStrategyView"></bk-input>
                  <div class="item-message">
                    <div class="item-message-error" v-show="validate.indexStatement && curMetricItem.indexStatement.length === 0"> {{ $t('请输入检索语句') }} </div>
                  <!-- {{ $t('检索语句说明') }} -->
                  </div>
                </div>
              </div>
            </template>
            <template v-if="sourceTypeConst !== 'BK-EVENT'">
              <div class="right-form-item">
                <span class="item-label item-required"> {{ $t('汇聚方法') }} </span>
                <div class="item-content">
                  <bk-select class="item-content-select" v-model="curMetricItem.aggMethod" @change="handleAggMethodChange" :clearable="false">
                    <!-- <bk-option v-if="curMetricItem.dataTypeLabel === 'event' && curMetricItem.dataSourceLabel === 'bk_monitor'" key="COUNT" id="COUNT" :name="'COUNT'"></bk-option> -->
                    <!-- <template v-else> -->
                    <bk-option v-for="(option, index) in aggMethodList"
                               :key="index"
                               :id="option.id"
                               :name="option.name">
                    </bk-option>
                    <bk-option v-if="showRealTime(metric)" key="REAL_TIME" id="REAL_TIME" :name="$t('实时')"></bk-option>
                  <!-- </template> -->
                  </bk-select>
                </div>
              </div>
              <div class="right-form-item" v-if="curMetricItem.aggMethod !== 'REAL_TIME'">
                <span class="item-label item-required"> {{ $t('汇聚周期') }} </span>
                <div class="item-content">
                  <!-- <bk-select class="item-content-select" v-model="curMetricItem.aggInterval" :clearable="false">
                  <bk-option v-for="(option, index) in set.aggIntervalList"
                             :key="index + '-' + curMetricItem.id"
                             :id="option.id"
                             :name="option.name">
                  </bk-option>
                </bk-select> -->
                  <cycle-input
                    v-model="curMetricItem.aggInterval"
                    :placeholder="$t('请输入汇聚周期')"
                    :list="set.aggIntervalList"
                    @input="handleCycleInput">
                  </cycle-input>
                  <div
                    v-show="validate.aggInterval && !curMetricItem.aggInterval"
                    class="error-tips need-position"
                    style="bottom: -18px;"> {{ $t('必填项，请输入') }} </div>
                </div>
              </div>
            </template>
            <template v-if="curMetricItem.aggMethod !== 'REAL_TIME' && (sourceTypeConst !== 'BK-EVENT')">
              <div class="right-form-item">
                <span class="item-label" :style="{ marginTop: curMetricItem.dimensions.length ? '2px' : '0px' }"> {{ $t('监控维度') }} </span>
                <div class="item-content dimension-content">
                  <strategy-dimension-input
                    :ref="'dimension-' + curMetricItem.id"
                    :key="dimensionKey"
                    :metric-field="curMetricItem.metricName"
                    :type-id="header.typeId"
                    :dimensions="curMetricItem.dimensions"
                    :data-source-label="curMetricItem.dataSourceLabel"
                    :data-type-label="curMetricItem.dataTypeLabel"
                    :dimension-list="dimensionListFilter"
                    :monitor-type="`${curMetricItem.dataSourceLabel}_${curMetricItem.dataTypeLabel}`"
                    @dimension-select="handleDimensionSelect"
                    @dimension-delete="handleDimensionDelete">
                  </strategy-dimension-input>
                </div>
              </div>
            </template>
            <div class="right-form-item">
              <span class="item-label"> {{ $t('监控条件') }} </span>
              <div class="item-content">
                <strategy-condition-input
                  :conditions="curMetricItem.conditions"
                  :key="conditionsKey"
                  :ref="'condition-' + curMetricItem.id"
                  :dimension-list="curMetricItem.conditionList"
                  :result-table-id="curMetricItem.resultTableId"
                  :metric-field="curMetricItem.metricName"
                  :data-type-label="curMetricItem.dataTypeLabel"
                  :data-source-label="curMetricItem.dataSourceLabel"
                  :method-list="curMetricItem.conditionSet"
                  :need-filter-method="needFilterMethod"
                  :type-id="header.typeId"
                  :biz-id="header.bizId"
                  :field="curMetricItem.metricName"
                  @on-set-value="handleConditionsValue"
                  @on-item-select="handleConditionsValue">
                </strategy-condition-input>
              </div>
            </div>
            <template v-if="canSetTarget">
              <div class="right-form-item">
                <span class="item-label"> {{ $t('监控目标') }} </span>
                <div class="item-content">
                  <template v-if="target.list.length">
                    <span class="target-desc" style="color: #63656e;">{{ target.desc.message}}</span>
                    <span class="target-desc">{{ target.desc.subMessage}}</span>
                  </template>
                  <span class="target-btn" :style="{ marginLeft: target.list.length ? '10px' : '0' }" @click="handleTargetAdd">{{ !target.list.length ? $t('点击选择') : $t('修改目标') }}</span>
                  <span v-if="!target.list.length" class="target-title">{{$t('（基于CMDB业务拓扑选择集群、模块、IP等。默认为本业务）')}}</span>
                  <!-- <div class="error-tips need-position" style="bottom: -18px;" v-show="validate.target && target.list.length < 1"> {{ $t('未添加监控目标，请添加后在保存') }} </div> -->
                </div>
              </div>
            </template>
            <template v-if="sourceTypeConst !== 'BK-EVENT'">
              <div class="right-form-item need-start">
                <span class="item-label item-required need-position"> {{ $t('检测算法') }} </span>
                <div class="item-content item-algorithms need-left">
                  <algorithms-panel-item
                    v-for="(item,index) in panel"
                    :key="index + '-' + curMetricItem.id"
                    :type-item="item"
                    :type-id="header.typeId"
                    :is-icmp="isICMP"
                    :alarm-data="handleGetAlarmData(item)"
                    :data-type-label="curMetricItem.dataTypeLabel"
                    :data-source-label="curMetricItem.dataSourceLabel"
                    :agg-method="curMetricItem.aggMethod"
                    :unit="curMetricItem.unit"
                    @edit-algorithm="handleEditAlgorithm"
                    @delete-algorithm="handleDeleteAlgorithm"
                    @add-algorithm="handleAddAlgorithm"
                    @panel-change="handlePanelChange">
                  </algorithms-panel-item>
                  <div class="error-tips algorithm-error" v-show="left.metricList.length && validate.strategyAlgorithm && !hasAlgorithm"> {{ $t('未添加检测算法，请添加后再保存') }} </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
      <div class="set-advance" v-if="left.metricList.length">
        <div class="set-advance-title" @click="more.active = left.metricList.length && !more.active">
          <i class="bk-icon icon-down-shape" :style="{ 'transform': more.active ? 'rotate(0deg)' : 'rotate(-90deg)' }"></i><span class="title-name">{{ $t('高级设置') }}
          </span>
        </div>
        <transition :css="false"
                    @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
                    @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave">
          <div class="set-advance-content" v-show="more.active && left.metricList.length" :style="{ marginBottom: more.active ? '12px' : '0' }">
            <table class="content-table">
              <tbody>
                <template v-for="(item, index) in left.metricList">
                  <tr :key="index + 'trigger'">
                    <td :rowspan="left.metricList.length" style="width: 142px;" class="border-top border-left table-title"> {{ $t('触发条件') }} </td>
                    <!-- <td class="border-top alias-name">{{item.metricAliaName}}</td> -->
                    <td class="border-top border-right">
                      <div class="col-trigger">
                        {{ $t('在') }}<bk-input size="small" class="col-trigger-input" v-model="item.triggerConfig.checkWindow" type="number" :max="60" :precision="0" :min="1"></bk-input> {{ $t('个周期内满足') }} <bk-input size="small" class="col-trigger-input" type="number" v-model="item.triggerConfig.count" :max="+item.triggerConfig.checkWindow" :min="1" :precision="0"></bk-input> {{ $t('次检测算法触发告警通知') }} <span class="icon-monitor icon-mind-fill trigger-icon" v-show="validate.triggerValidate && isTriggerValidate" v-bk-tooltips="{ content: '要求: 满足次数<=周期数，且都为正整数', placements: ['right'] }"></span>
                      </div>
                    </td>
                  </tr>
                  <tr :key="index + 'recover'">
                    <td :rowspan="left.metricList.length" style="width: 142px;" class="border-top border-left table-title"> {{ $t('恢复条件') }} </td>
                    <td class="border-top border-right">
                      <div class="col-trigger"> {{ $t('连续') }} <bk-input size="small" class="col-trigger-input" type="number" v-model="item.recoveryConfig.checkWindow" :max="60" :min="1" :precision="0"></bk-input> {{ $t('个周期内不满足触发条件表示恢复') }} <span class="icon-monitor icon-mind-fill trigger-icon" v-show="validate.recoverValidate && isRecoverValidate" v-bk-tooltips="{ content: $t('要求: 触发条件周期数为正整数') , placements: ['right'] }"></span>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr>
                  <td rowspan="1" class="border-left table-title"> {{ $t('无数据告警') }} </td>
                  <td colspan="2" class="border-right">
                    <div class="col-undefined">
                      <bk-switcher class="col-undefined-switcher" v-model="more.noDataConfig.isEnable" theme="primary" size="small"></bk-switcher>
                      <template v-if="more.noDataConfig.isEnable">
                        {{ $t('当数据连续丢失') }} <bk-input class="col-undefined-input" size="small" v-model="more.noDataConfig.continuous" type="number" :max="50" :min="1" :precision="0"></bk-input> {{ $t('个周期后触发告警通知') }}
                        <template v-if="!canSetTarget && more.noDataConfig.dimensionList.length">
                          ，{{$t('基于以下维度')}}
                          <bk-select v-model="more.noDataConfig.dimensions" size="small" searchable multiple class="col-undefined-select">
                            <bk-option v-for="option in more.noDataConfig.dimensionList"
                                       :key="option.id"
                                       :id="option.id"
                                       :name="option.name">
                            </bk-option>
                          </bk-select>
                          {{$t('进行判断')}}
                        </template>
                      </template>
                      <span class="icon-monitor icon-mind-fill trigger-icon" v-show="validate.noDataValidate && isNoDataValidate" v-bk-tooltips="{ content: $t('要求: 周期数>=1，且为正整数') , placements: ['right'] }"></span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="content-template">
              <div class="content-template-left"> {{ $t('告警通知模板') }} </div>
              <div class="content-template-right">
                <!-- <bk-input class="right-content" type="textarea" v-model="more.messageTemplate" :maxlength="100"></bk-input> -->
                <template-input ref="templateInput" :default-value="more.messageTemplate" :trigger-list="more.triggerList" @change="handleTemplateChange"></template-input>
                <div class="right-desc">
                  <span class="desc-detail" :class="{ 'btn-disabled': !more.messageTemplate.length }" @click="more.messageTemplate.length && handlePreviewDetail()"> {{ $t('模板预览') }} </span>
                  <span class="preview-detail" @click="handleVariateList"> {{ $t('变量列表') }} </span>
                  <span class="preview-detail" @click="handleGotoLink('strategyTemplate')"> {{ $t('模板使用说明') }} <i class="icon-monitor icon-mc-wailian"></i></span>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
      <div class="set-notice">
        <div class="set-notice-title">{{ $t('通知设置') }}</div>
        <div class="set-notice-item">
          <span class="item-label"> {{ $t('推送通知') }} </span>
          <div class="item-content">
            <bk-checkbox class="item-check" :value="true" disabled> {{ $t('发生告警时通知') }} </bk-checkbox>
            <bk-checkbox v-model="curNoticeConfig.noticeConfig.sendRecoveryAlarm"> {{ $t('告警恢复时通知') }} </bk-checkbox>
          </div>
        </div>
        <div class="set-notice-item">
          <span class="item-label"> {{ $t('通知间隔') }} </span>
          <div class="item-content"> {{ $t('若告警未恢复并且未确认，则每隔') }} <bk-input size="small" class="item-interval" type="number" :max="1440" :min="1" :precision="0" v-model="curNoticeConfig.noticeConfig.alarmInterval" @change="handleSetInt(curNoticeConfig.noticeConfig, 'alarmInterval', $event)"></bk-input> {{ $t('分钟再进行告警') }} <div class="error-tips need-position" style="bottom: -11px;" v-show="validate.alarmInterval && +curNoticeConfig.noticeConfig.alarmInterval === 0"> {{ $t('请输入大于0的数字') }} </div>
          </div>
        </div>
        <div class="set-notice-item">
          <span class="item-label"> {{ $t('通知时间段') }} </span>
          <div class="item-content">
            <bk-time-picker
              class="item-input"
              v-model="curNoticeConfig.noticeConfig.alarmTimeRange"
              :placeholder="$t('选择时间范围')"
              :type="'timerange'"
              :clearable="false"
              allow-cross-day>
            </bk-time-picker>
          </div>
        </div>
        <div class="set-notice-item">
          <span class="item-label label-required">{{ $t('通知告警组') }}</span>
          <div class="item-content" style="max-width: calc(100% - 230px);">
            <template>
              <!-- <strategy-alarm-group v-if="groupList.length" :alarm-group-list="groupList">

                        </strategy-alarm-group> -->
              <bk-select
                ext-popover-cls="alarm-group-popover"
                class="item-input item-content-input"
                ref="alarmGroupSelect"
                :popover-width="380"
                searchable
                multiple
                v-model="curNoticeConfig.noticeGroup">
                <bk-option v-for="(option) in groupList"
                           :key="option.id"
                           :id="option.id"
                           :name="option.name">
                  <div class="alarm-group-wrap">
                    <div class="group-content">
                      <div class="item-name">{{option.name}}</div>
                      <div class="item-person">{{option.receiver.join(',')}}</div>
                    </div>
                    <i v-if="curNoticeConfig.noticeGroup.includes(option.id)" class="bk-icon icon-check-1 check-icon" />
                  </div>
                </bk-option>
                <div
                  v-authority="{ active: !authority.ALARM_GROUP_MANAGE_AUTH }"
                  slot="extension"
                  class="item-input-create"
                  @click="authority.ALARM_GROUP_MANAGE_AUTH
                    ? handleCreateAlarmGroup()
                    : handleShowAuthorityDetail(ruleAuth.ALARM_GROUP_MANAGE_AUTH)">
                  <i class="bk-icon icon-plus-circle"></i> {{ $t('新增告警组') }} </div>
              </bk-select>
            </template>
            <div class="error-tips need-position" style="bottom: -19px;" v-show="validate.noticeGroup && curNoticeConfig.noticeGroup.length === 0"> {{ $t('必填项，请输入') }} </div>
          </div>
        </div>
      </div>
      <div class="set-footer">
        <template v-if="left.metricList.length > 0">
          <bk-button
            v-authority="{
              active: !authority.MANAGE_AUTH
            }"
            theme="primary"
            :disabled="left.metricList.length < 1"
            @click="authority.MANAGE_AUTH ? handleSaveAndset() : handleShowAuthorityDetail()">
            {{ $t('保存') }}
          </bk-button>
        <!-- <bk-button class="set-footer-btn" theme="primary" v-else @click="handleGotoSelectTarget"> {{ $t('前往选择监控目标') }} </bk-button> -->
        </template>
        <bk-button class="set-footer-btn" :style="{ marginLeft: left.metricList.length > 0 ? '10px' : '0' }" @click="handleCancel"> {{ $t('取消') }} </bk-button>
      </div>
      <strategy-config-algorithm
        :is-icmp="isICMP"
        v-if="curMetricItem"
        :dialog-show="algorithm.show"
        :selected-algorithms="selectedAlgorithms"
        :uptime-check-type="curMetricItem && curMetricItem.metricName"
        :default-unit="curMetricItem && curMetricItem.unit"
        :unit-suffix-id="curMetricItem && curMetricItem.unitSuffixId"
        :unit-suffix-list="curMetricItem && curMetricItem.unitSuffixList"
        :mode="algorithm.mode"
        :value="algorithm.editData"
        :agg-method="curMetricItem && curMetricItem.aggMethod"
        :data-type-label="curMetricItem && curMetricItem.dataTypeLabel"
        :data-source-label="curMetricItem && curMetricItem.dataSourceLabel"
        :all-algorithm="curMetricItem && curMetricItem.algorithm"
        @hide-dialog="handleDialogChange"
        @confirm-dialog="handleDialogConfirm">
      </strategy-config-algorithm>
      <strategy-config-metric
        v-if="scenarioList.length"
        ref="StrategyConfigMetric"
        :id="id"
        :is-show="metric.oldShow"
        :is-edit="metric.oldisEdit"
        :metric="metric.metricObj"
        :monitor-type.sync="header.typeId"
        :meric-type="mericType"
        :scenario-list="scenarioList"
        @on-add="handleAddMetric"
        @hide-dialog="handleHideMetricDialog">
      </strategy-config-metric>
      <strategy-config-metric-new
        ref="StrategyConfigMetricNew"
        :id="id"
        :is-show="metric.show"
        :is-edit="metric.isEdit"
        :metric="metric.metricObj"
        :monitor-type.sync="header.typeId"
        :scenario-list="scenarioList"
        @on-add="handleAddMetric"
        @show-change="handleHideMetricDialog"
        @hide-dialog="handleHideMetricDialog">
      </strategy-config-metric-new>
      <strategy-config-retrieval
        :scenario-list="scenarioList"
        :monitor-type.sync="header.typeId"
        :dialog-show.sync="retrieval.show"
        :index-id="retrieval.indexId"
        @set-retrieval="handleRetievalConfirm"></strategy-config-retrieval>
      <strategy-template-preview :dialog-show.sync="more.previewTemplate" :template="more.messageTemplate" :scenario="header.typeId"></strategy-template-preview>
      <strategy-variate-list :dialog-show.sync="more.variateListShow" :variate-list="more.variateList"></strategy-variate-list>
      <strategy-set-target
        v-if="target.show"
        :dialog-show.sync="target.show"
        :biz-id="header.bizId"
        :object-type="curMetricItem.dataTarget"
        :target-list="target.list"
        :target-type="curMetricItem.targetType"
        :message="target.desc"
        can-save-empty
        @message-change="handleTargetDesChange"
        @target-type-change="handleTargetTypeChange"
        @targets-change="handleTargetChange">
      </strategy-set-target>
      <!-- 首次进来tip提示 -->
      <div v-show="false">
        <div class="remind-tips" ref="remindTips">
          <div class="remind-tips-title">{{ $t('添加监控项') }}</div>
          <div class="remind-tips-desc">{{$t('监控项为策略配置')}}<span class="desc-strong">{{$t('核心内容')}}</span>（<span class="desc-important"> * </span>），{{$t('三类监控项可任选其一')}}</div>
          <div class="remind-tips-content">
            <span class="content-label">{{$t('监控指标') }}</span>
            <span class="content-label">{{$t('事件') }}</span>
            <span class="content-label">{{$t('日志关键字')}}</span>
          </div>
          <div class="remind-tips-footer" @click="handleHideRemidTips">{{$t('我知道了')}}</div>
        </div>
      </div>
    </div>
    <!-- 策略辅助视图 -->
    <div class="strategy-config-right ml20"
         :style="{ width: isNaN(strategyView.rightWidth) ? strategyView.rightWidth : `${strategyView.rightWidth}px` }">
      <div class="right-wrapper">
        <strategy-view
          ref="strategyView"
          :cur-metric-item="curMetricItem"
          :target-list="target.list"
          :dimension-list="more.noDataConfig.dimensionList"
          :where="strategyView.where"
          :loading="loading">
        </strategy-view>
        <div class="drag" :style="{ position: curMetricItem ? 'fixed' : 'static' }" @mousedown="handleMouseDown"></div>
      </div>
    </div>
  </div>
</template>
<script>
import { collapseMixin, strategyThresholdMixin } from '../../../common/mixins'
import documentLinkMixin from '../../../mixins/documentLinkMixin'
import StrategyConfigAlgorithm from './strategy-config-algorithm/strategy-config-algorithm'
import StrategyConfigMetric from './strategy-config-metric/strategy-config-metric'
import StrategyConfigMetricNew from './strategy-config-metric/strategy-config-metric-new'
import StrategyConditionInput from './strategy-set-input/strategy-condition-input'
import StrategyDimensionInput from './strategy-set-input/strategy-dimension-input'
import AlgorithmsPanelItem from './strategy-set-input/algorithm-panel-item'
import StrategyConfigRetrieval from './strategy-config-retrieval/strategy-config-retreval'
import StrategyTemplatePreview from './strategy-template-preview/strategy-template-preview'
import StrategyVariateList from './strategy-variate-list/strategy-variate-list'
import TemplateInput from './strategy-template-input/strategy-template-input'
import StrategySetTarget from './strategy-set-target/strategy-set-target'
import StrategyCustomDesc from './strategy-custom-desc/strategy-custom-desc'
import MultiLabelSelect from '../../../components/multi-label-select/multi-label-select.tsx'
import { labelListToTreeData } from '../../../components/multi-label-select/utils'
import { deepClone, transformDataKey, getUrlParam, random } from '../../../../monitor-common/utils/utils'
import { createNamespacedHelpers } from 'vuex'
import { SET_STRATEGY_PARAMS, SET_EMPTY_DIMENSION } from '../../../store/modules/strategy-config'
import { strategyConfigDetail, getMetricList, strategyLabelList } from '../../../../monitor-api/modules/strategies'
import CycleInput from '../../../components/cycle-input/cycle-input'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import * as ruleAuth from '../authority-map'
import StrategyView from './strategy-view/strategy-view.vue'
import { debounce } from 'throttle-debounce'
// import StrategyAlarmGroup from './strategy-alarm-group/strategy-alarm-group'
const { mapActions, mapGetters, mapMutations } = createNamespacedHelpers('strategy-config')

export default {
  name: 'StrategyConfigSet',
  components: {
    StrategyConfigAlgorithm,
    StrategyConfigMetric,
    StrategyConditionInput,
    StrategyDimensionInput,
    AlgorithmsPanelItem,
    StrategyConfigRetrieval,
    TemplateInput,
    StrategyTemplatePreview,
    StrategyVariateList,
    StrategySetTarget,
    StrategyCustomDesc,
    StrategyConfigMetricNew,
    CycleInput,
    StrategyView,
    MultiLabelSelect
    // StrategyAlarmGroup
  },
  mixins: [collapseMixin, strategyThresholdMixin, documentLinkMixin, authorityMixinCreate(ruleAuth)],
  props: {
    id: {
      type: [String, Number],
      default: 0
    }
  },
  data() {
    const defaultData = this.getDefaultData()
    return {
      ruleAuth,
      testDialog: true,
      metricSetList: [
        {
          name: this.$t('添加监控指标'),
          id: 'common'
        },
        {
          name: this.$t('添加事件'),
          id: 'event'
        },
        {
          name: this.$t('添加日志关键字'),
          id: 'log'
        }
      ],
      panel: [
        {
          expand: true,
          level: 1,
          type: 'deadly',
          name: this.$t('致命')
        },
        {
          expand: false,
          level: 2,
          type: 'warning',
          name: this.$t('预警')
        },
        {
          expand: false,
          level: 3,
          type: 'remind',
          name: this.$t('提醒')
        }
      ],
      addToolTip: {
        content: this.$t('组合策略功能暂未开放，敬请期待！'),
        theme: 'add-metric',
        placements: ['bottom-start']
      },
      set: {
        aggMethodList: [
          {
            id: 'SUM',
            name: 'SUM'
          },
          {
            id: 'AVG',
            name: 'AVG'
          },
          {
            id: 'MAX',
            name: 'MAX'
          },
          {
            id: 'MIN',
            name: 'MIN'
          },
          {
            id: 'COUNT',
            name: 'COUNT'
          }
        ],
        aggIntervalList: [
          {
            id: 60,
            name: '1'
          },
          {
            id: 120,
            name: '2'
          },
          {
            id: 300,
            name: '5'
          },
          {
            id: 600,
            name: '10'
          },
          {
            id: 900,
            name: '15'
          },
          {
            id: 1200,
            name: '20'
          }
        ],
        typeTipMap: {
          hosts: this.$t('指的主机系统和硬件的层面. 如 CPU MEM 服务器硬件等.监控范围对应”CMDB-主机拓扑“,最小粒度为IP'),
          services: this.$t('指的是运行在服务器操作系统之上的,如服务模块,组件等. 监控范围对应”CMDB-服务拓扑“,最小粒度为实例'),
          applications: this.$t('指的是用户使用应用的情况,应用的运营数据,如登陆数,服务拨测等')
        }
      },
      loading: true,
      created: false,
      needFilterMethod: true, // 日志关键字指标维度数据不需要过滤
      strategyView: {
        rightWidth: '40%',
        range: [300, 1200],
        where: []
      },
      handleQueryStrategyView: null,
      ...defaultData,
      labelTreeData: []
    }
  },
  computed: {
    ...mapGetters(['groupList', 'dimensionValueLoading', 'scenarioList', 'algorithmOptionMap', 'logDimensionLoading']),
    bizId() {
      return this.$store.getters.bizId
    },
    bizList() {
      return this.$store.getters.bizList
    },
    canSetTarget() {
      return !(this.curMetricItem.dataTarget === 'NONE'
        || (['log'].includes(this.curMetricItem.dataTypeLabel) && this.curMetricItem.dataSourceLabel !== 'bk_monitor'))
    },
    typeToolTip() {
      const group = this.scenarioList.find(item => item.children.some(set => set.id === this.header.typeId))
      const tip = group ? this.set.typeTipMap[group.id] : ''
      return {
        content: tip || '',
        showOnInit: false,
        placements: ['right']
      }
    },
    curMetricItem() {
      const tempObj = this.left.metricList[this.left.active] || null
      if (this.$i18n.locale === 'enUS' && tempObj && tempObj.dataTypeLabel === 'time_series') {
        tempObj.metricAliaName = `${tempObj.resultTableId}.${tempObj.metricName}`
      }
      return tempObj
    },
    hasAlgorithm() {
      return this.curMetricItem && this.curMetricItem.algorithm
        ? Object.keys(this.curMetricItem.algorithm).some(key => this.curMetricItem.algorithm[key].length > 0) : false
    },
    isTriggerValidate() {
      if (this.curMetricItem) {
        const { triggerConfig } = this.curMetricItem
        return ((triggerConfig.checkWindow < 1 || triggerConfig.count < 1)
                        || ((`${triggerConfig.checkWindow}`).match(/\./) || (`${triggerConfig.count}`).match(/\./))
                        || (+triggerConfig.checkWindow < +triggerConfig.count))
      }
      return false
    },
    isRecoverValidate() {
      if (this.curMetricItem) {
        const { recoveryConfig } = this.curMetricItem
        return ((recoveryConfig.checkWindow < 1)
          || ((`${recoveryConfig.checkWindow}`).match(/\./)))
        // || (+recoveryConfig.checkWindow < +triggerConfig.checkWindow))
      }
      return false
    },
    isNoDataValidate() {
      if (this.curMetricItem) {
        const { noDataConfig } = this.more
        return (noDataConfig.continuous < 1 || (`${noDataConfig.continuous}`).match(/\./))
      }
      return false
    },
    isNoticeValidate() {
      if (this.curMetricItem) {
        const { actionType, noticeGroup } = this.curNoticeConfig
        return actionType.length < 1 || (actionType.includes('notice') && noticeGroup.length < 1)
      }
      return false
    },
    curAlgorithmItem() {
      return this.curMetricItem && this.algorithm.type ? this.curMetricItem.algorithm[this.algorithm.type] : []
    },
    selectedAlgorithms() {
      if (this.curAlgorithmItem && this.curAlgorithmItem.length) {
        return this.curAlgorithmItem.map(item => item.type)
      }
      return []
    },
    curNoticeConfig() {
      return this.noticeList[0]
    },
    aggMethodList() {
      if ((this.curMetricItem.dataTypeLabel === 'log' && this.curMetricItem.dataSourceLabel !== 'bk_monitor')
        || (this.curMetricItem.dataTypeLabel === 'event' && this.curMetricItem.dataSourceLabel === 'custom')) {
        return this.set.aggMethodList.filter(item => item.id === 'COUNT')
      } if (this.header.typeId === 'uptimecheck') {
        return this.curMetricItem.aggMethodList
      }
      return this.set.aggMethodList
    },
    sourceTypeConst() {
      if (!this.curMetricItem) {
        return 'NONE'
      } if (this.curMetricItem.dataTypeLabel === 'event') {
        if (this.curMetricItem.dataSourceLabel === 'custom') {
          return 'CUSTOM-EVENT'
        } if (this.curMetricItem.dataSourceLabel === 'bk_monitor') {
          return 'BK-EVENT'
        }
      } else if (this.curMetricItem.dataTypeLabel === 'log') {
        return 'LOG'
      }
      return 'COMMOM'
    },
    conditionsKey() {
      if (this.curMetricItem.conditionList && this.curMetricItem.conditions) {
        return `condition-${+new Date()}`
      }
      return `condition-${+new Date()}`
    },
    isICMP() {
      if (this.curMetricItem
      && this.curMetricItem.resultTableId
       && this.curMetricItem.resultTableId === 'uptimecheck.icmp') {
        return true
      }
      return false
    },
    dimensionKey() {
      let key = `dimension-${this.curMetricItem.id}`
      if (this.curMetricItem.dimensions && this.dimensionListFilter) {
        key = random(8)
      }
      return key
    },
    dimensionListFilter() {
      if (!this.needFilterMethod) return this.curMetricItem.dimensionList
      return this.curMetricItem.dimensionList.filter((item) => {
        if ('is_dimension' in item) return item.is_dimension
        return true
      })
    }
  },
  watch: {
    id: {
      handler(v, old) {
        if (`${v}` !== `${old}`) {
          this.left.active = 0
          this.strategyView.where = []
          const promiseList = []
          // if (!this.groupList.length) {
          //     promiseList.push(this.getNoticeGroupList())
          // }
          if (!this.scenarioList.length) {
            promiseList.push(this.getScenarioList())
          }
          if (this.id) {
            promiseList.push(this.getDetialData())
          }
          promiseList.push(this.handleGetVariateList())
          if (promiseList.length) {
            this.loading = true
            Promise.all(promiseList).catch((err) => {
              if (err.data && err.data.code === 3313003) {
                this.needCheck = false
                this.$router.back()
              }
              console.error(err)
            })
              .finally(() => {
                const indexSetId = getUrlParam('indexSetId') || 0
                const scenarioId = getUrlParam('scenarioId')
                if (indexSetId && scenarioId && +v < 1 && this.created) {
                  this.created = false
                  this.handleSetDataFromRetreval(indexSetId, scenarioId)
                } else {
                  `${v}` === '0' ? this.handleBackDisplayData() : this.loading = false
                }
              })
          }
        }
      },
      immediate: true
    }
  },
  created() {
    this.created = true
    this.header.bizId = this.bizId
    this.handleQueryStrategyView = debounce(600, this.queryStrategyView)
  },
  mounted() {
    if (!this.id && !localStorage.getItem(`${this.$store.getters.userName}-strategy-config-set-tips`)) {
      const timer = setTimeout(() => {
        this.handleShowRemindTips()
        localStorage.setItem(`${this.$store.getters.userName}-strategy-config-set-tips`, true)
        clearTimeout(timer)
      }, 2000)
    }
  },
  async beforeRouteLeave(to, from, next) {
    this.handleHideMetricDialog(false)
    this.handleSetGroupHide()
    if (this.needCheck && (to.name !== 'strategy-config-target' && to.name !== 'alarm-group-add')) {
      const needNext = await this.handleCancel(false)
      next(needNext)
    } else {
      next()
    }
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.getLabelListApi()
      if (from.name !== 'strategy-config-target' && from.name !== 'alarm-group-add') {
        const defaultData = vm.getDefaultData()
        Object.keys(defaultData).forEach((key) => {
          vm[key] = defaultData[key]
        })
        vm.header.typeId = to.params.objectId ? to.params.objectId : vm.header.typeId
        if (vm.id && !vm.loading && `${vm.id}` === `${to.params.id}`) {
          vm.loading = true
          Promise.all([vm.handleGetVariateList(), vm.getDetialData()]).finally(() => {
            vm.loading = false
          })
        } else if (from.name === 'uptime-check-task-add' || from.name === 'uptime-check-task-edit') {
          vm.loading = true
          vm.handleBackDisplayData()
        } else if (from.name === 'performance-detail'
          || from.name === 'data-retrieval'
          || from.name === 'view-detail'
          || from.name === 'custom-detail-event'
          || vm.$route.query.data) {
          // dashboard-panels.vue 组件跳转新增策略
          vm.handleFromPerformentPararms()
        }
      } else if (from.name === 'alarm-group-add') {
        to.params.alarmGroupId && vm.curNoticeConfig.noticeGroup.push(to.params.alarmGroupId)
      }
    })
  },
  activated() {
    this.getNoticeGroupList()
  },
  deactivated() {
    this.algorithm.show = false
    this.left.timer && clearTimeout(this.left.timer)
    this.handleDestroyRemindTips()
  },
  beforeDestroy() {
    this.algorithm.show = false
    this.left.timer && clearTimeout(this.left.timer)
    this.handleDestroyRemindTips()
  },
  methods: {
    ...mapActions(['getNoticeGroupList',
      'addStrategyConfig',
      'getScenarioList',
      'getLogFields',
      'getNoticeVariableList',
      'getIndexSetList']),
    ...mapMutations([SET_STRATEGY_PARAMS, SET_EMPTY_DIMENSION]),
    // 维度选择时触发
    handleDimensionSelect(dimensionList, hooks) {
      const { noDataConfig } = this.more
      noDataConfig.dimensionList = dimensionList || []
      noDataConfig.dimensions = noDataConfig.dimensions.filter(id => dimensionList.some(item => item.id === id))
      this.validate.dimensions = false
      hooks !== 'created' && this.handleQueryStrategyView(true)
    },
    // 维度删除时触发
    handleDimensionDelete(item, dimensionList) {
      const { noDataConfig } = this.more
      const index = noDataConfig.dimensions.indexOf(item.id)
      index > -1 && noDataConfig.dimensions.splice(index, 1)
      noDataConfig.dimensionList = dimensionList || []
      this.handleQueryStrategyView(true)
    },
    // 显示提示
    handleShowRemindTips() {
      this.tipsInstance = this.$bkPopover(this.$refs['setPanel-0'][0], {
        content: this.$refs.remindTips,
        theme: 'light common-monitor strategy-remind',
        trigger: 'manual',
        placement: 'bottom-start',
        offset: '5, 20',
        arrow: true,
        zIndex: 999,
        onHide: () => !this.tipsRemindShow
      })
      this.tipsInstance && this.tipsInstance.show(100)
    },
    // 销毁提示实例
    handleDestroyRemindTips() {
      if (this.tipsInstance) {
        this.tipsInstance.hide(0)
        this.tipsInstance.destroy()
        this.tipsInstance = null
      }
    },
    // 点击tip上我知道了触发
    handleHideRemidTips() {
      this.tipsRemindShow = false
      this.tipsInstance && this.tipsInstance.hide && this.tipsInstance.hide(100)
    },
    // 监控目标描述变化时触发
    handleTargetDesChange(message) {
      this.target.desc = message
    },
    handleTargetAdd() {
      this.target.show = !this.target.show
    },
    handleTargetTypeChange(type) {
      this.curMetricItem.targetType = type
    },
    // 监控目标变化时填充目标IP
    dimensionsFillChange(targets) {
      const filterType = ['biz']
      const dimensionsType = ['bk_target_ip', 'bk_target_cloud_id']
      const { dimensionList } = this.more.noDataConfig
      const isAuto = targets.some((item) => {
        if (item.bk_obj_id) {
          return !filterType.includes(item.bk_obj_id)
        }
        return false
      })
      const dimensionListTemp = dimensionList.map(item => item.id)
      const metricListObj = this.left.metricList[this.left.active] || null
      const resultList = deepClone(dimensionListTemp)
      dimensionsType.forEach((item) => {
        if (!dimensionListTemp.includes(item) && isAuto && metricListObj !== null) {
          resultList.push(item)
        }
      })
      this.$set(this.left.metricList[this.left.active], 'dimensions', resultList)
    },
    // 监控目标变化时触发
    handleTargetChange(targets) {
      this.dimensionsFillChange(targets)
      this.target.list = targets
      this.handleQueryStrategyView()
    },
    handleBackDisplayData() {
      let data = null
      if (this.$route.params.metric) {
        // 获取路由回显数据
        data = this.$route.params.metric
      } else {
        // 获取session数据
        const dashboardData = JSON.parse(sessionStorage.getItem('__dashboard-Metric__'))
        if (dashboardData !== null) {
          data = transformDataKey(dashboardData)
          data.metricName = dashboardData.metric_field
          data.metricAlicName = dashboardData.metric_field_name
          sessionStorage.removeItem('__dashboard-Metric__')
        }
      }
      if (data) {
        this.handleDatadDashboard(data)
      } else {
        this.loading = false
      }
    },
    // 点击选择各种指标
    handleSelectMetric(item) {
      this.tipsRemindShow = false
      this.handleHideRemidTips()
      if (item.id === 'log') {
        this.handleLeftAddRetrieval()
      } else {
        this.mericType = item.id
        this.handleLeftAdd(item)
      }
    },
    // 仪表盘跳转新增策略触发
    async handleDatadDashboard(data) {
      let mertric = {}
      this.metric.isEdit = true
      if (data.dataTypeLabel === 'event') {
        const params = {
          data_source_label: data.dataSourceLabel,
          data_type_label: data.dataTypeLabel,
          page: 1,
          page_size: 10,
          search_fields: {
            metric_field: data.metricName,
            result_table_id: data.resultTableId
          }
        }
        const res = await getMetricList(params)
        mertric = res.metric_list.find(item => {
          return item.metric_field === data.metricName
                  && item.result_table_id === data.resultTableId
                  && item.data_source_label === data.dataSourceLabel
                  && item.data_type_label === data.dataTypeLabel
        }) || res.metric_list[0]
      } else {
        const { StrategyConfigMetricNew } = this.$refs
        if (StrategyConfigMetricNew) {
          this.loading = true
          mertric = await StrategyConfigMetricNew.getMetric({
            dataSourceLabel: data.dataSourceLabel,
            dataTypeLabel: data.dataTypeLabel,
            resultTableId: data.resultTableId,
            metricName: data.metricName,
            resultTableId: data.resultTableId,
            resultTableLabel: data.resultTableLabel,
            relatedName: data.relatedName,
            relatedId: data.relatedId
          })
        }
      }
      this.metric.metricObj = mertric
      await this.handleAddMetric(mertric)
      this.curMetricItem.aggMethod = data.resultTableLabel === 'uptimecheck' ? mertric.method_list[0] : data.aggMethod
      this.curMetricItem.aggInterval = data.aggInterval
      if (data.resultTableLabel === 'uptimecheck') {
        this.curMetricItem.dimensions = mertric.default_dimensions
        this.curMetricItem.conditions = mertric.default_condition
      } else {
        this.curMetricItem.dimensions = data.aggDimension.length ? data.aggDimension : this.curMetricItem.dimensions
        this.curMetricItem.conditions = data.aggCondition.length ? data.aggCondition : this.curMetricItem.conditions
      }
      if (data.targets) {
        this.handleTargetChange(data.targets)
        this.handleSetTargetDesc(this.target.list, this.curMetricItem.targetType, this.curMetricItem.objectType)
      }
      this.loading = false
    },
    // 设置默认data的数据
    getDefaultData() {
      return {
        mericType: 'common',
        target: {
          show: false,
          list: [],
          desc: {
            message: '',
            subMessage: ''
          }
        },
        needCheck: true,
        header: {
          bizId: this.bizId,
          typeId: 'service_module',
          groupId: 'services',
          sourceType: 'BKMONITOR',
          strategyName: '',
          labels: []
        },
        left: {
          enter: -1,
          active: -1,
          metricList: [
          ],
          popoverInstance: null,
          timer: null
        },
        more: {
          active: false,
          noDataConfig: {
            continuous: 5,
            isEnable: false,
            dimensions: [],
            dimensionList: []
          },
          messageTemplate: `{{content.level}}
{{content.begin_time}}
{{content.time}}
{{content.duration}}
{{content.target_type}}
{{content.data_source}}
{{content.content}}
{{content.current_value}}
{{content.biz}}
{{content.target}}
{{content.dimension}}
{{content.detail}}
{{content.related_info}}`,
          previewTemplate: false,
          variateListShow: false,
          variateList: [],
          triggerList: []
        },
        algorithm: {
          show: false,
          mode: 'add',
          type: '',
          editData: null,
          eventLevel: 0
        },
        metric: {
          oldShow: false,
          oldisEdit: false,
          show: false,
          isEdit: false,
          metricObj: null
        },
        noticeList: [
          {
            actionType: ['notice'],
            noticeConfig: {
              sendRecoveryAlarm: false,
              alarmTimeRange: ['00:00:00', '23:59:59'],
              alarmInterval: 120
            },
            noticeGroup: [],
            messageActionId: 0,
            actionId: 0
          }
        ],
        validate: {
          strategyName: false,
          noticeGroup: false,
          strategyAlgorithm: false,
          eventLevel: false,
          triggerValidate: false,
          recoverValidate: false,
          noDataValidate: false,
          alarmInterval: false,
          indexStatement: false,
          target: false,
          dimensions: false,
          aggInterval: false
        },
        retrieval: {
          show: false,
          indexId: 0
        },
        tipsInstance: null,
        tipsRemindShow: true
      }
    },
    // 日志检索跳转到监控默认设置关键字指标
    async handleSetDataFromRetreval(indexSetId, scenarioId) {
      this.loading = true
      const data = await this.getIndexSetList({
        bk_biz_id: this.$store.getters.bizId,
        index_set_id: indexSetId
      })
      // eslint-disable-next-line camelcase
      if (data?.metric_list?.length) {
        data.metric_list[0].id = data.metric_list[0].index_set_id
        let dimension = getUrlParam('dimension')
        let condition = getUrlParam('condition')
        try {
          dimension && (dimension = JSON.parse(dimension))
          condition && (condition = JSON.parse(condition))
        } catch (e) {
          dimension = []
          condition = []
        }
        await this.handleAddMetric(Object.assign(data.metric_list[0], {
          default_condition: condition,
          default_dimensions: dimension,
          id: data.metric_list[0].index_set_id
        }))
        this.curMetricItem.indexStatement = getUrlParam('indexStatement') || '*'
      }
      this.header.typeId = scenarioId
      this.loading = false
    },
    handleLeftEnter(v) {
      this.left.enter = v
    },
    handleLeftLeave() {
      this.left.enter = -1
    },
    handleLeftClick(v) {
      this.left.active = v
    },
    // 修改计算公式触发
    handleAggMethodChange(v) {
      this.curMetricItem.aggMethod = v
      if (v === 'REAL_TIME') {
        Object.keys(this.curMetricItem.algorithm).forEach((key) => {
          const item = this.curMetricItem.algorithm[key]
          if (item?.length) {
            this.curMetricItem.algorithm[key] = item.filter(set => set.type === 'Threshold')
          }
        })
      }
      this.handleQueryStrategyView()
    },
    // 添加监控指标
    handleLeftAdd(item) {
      if (item.id === 'event') {
        this.metric.oldShow = true
        this.metric.oldisEdit = false
      } else {
        this.metric.show = true
        this.metric.isEdit = false
      }
    },
    // 添加关键字
    handleLeftAddRetrieval() {
      this.retrieval.show = true
    },
    // 点击模板预览触发
    handlePreviewDetail() {
      this.more.previewTemplate = true
    },
    // 添加日志关键字关键项
    handleRetievalConfirm(data) {
      this.retrieval.show = false
      this.handleAddMetric(data)
    },
    // 点击变量列表
    handleVariateList() {
      this.more.variateListShow = true
    },
    async handleAddMetric(metric) {
      if (!this.curMetricItem) {
        const data = await this.handleTransformMetric(metric)
        this.left.metricList.push(data)
        this.left.active = 0
        this[SET_EMPTY_DIMENSION]()
        this.strategyView.where = []
        this.handleClearTarget()
      } else if (this.curMetricItem.id !== metric.id) {
        this.left.metricList = []
        this.strategyView.where = []
        if (metric.data_type_label === 'log') {
          const data = await this.handleTransformMetric(metric)
          this.left.metricList.push(data)
          this[SET_EMPTY_DIMENSION]()
        } else {
          await this.$nextTick()
          const data = await this.handleTransformMetric(metric)
          this.left.metricList.push(data)
          this[SET_EMPTY_DIMENSION]()
        }
        this.handleClearTarget()
      }
    },
    handleClearTarget() {
      this.target.list = []
      this.target.desc.message = ''
      this.target.desc.subMessage = ''
    },
    // 获取策略模板变量列表
    async handleGetVariateList() {
      const data = await this.getNoticeVariableList()
      this.more.variateList = data
      this.more.triggerList = data.reduce((pre, cur) => {
        pre.push(...cur.items)
        return pre
      }, [])
    },
    // 通知模板编辑变化触发
    handleTemplateChange(v) {
      this.more.messageTemplate = v || ''
    },
    handleLeftTooltips() {
      if (this.left.metricList.length && !this.left.timer) {
        if (!this.left.popoverInstance) {
          this.left.popoverInstance = this.$bkPopover(this.$refs.leftAdd, {
            content: this.$t('组合策略功能暂未开放，敬请期待！'),
            theme: 'dark add-metric',
            arrow: true,
            trigger: 'manual',
            placement: 'bottom-start',
            hideOnClick: false
          })
        }
        this.left.popoverInstance && this.left.popoverInstance.show(100)
        this.left.timer = setTimeout(() => {
          this.left.popoverInstance && this.left.popoverInstance.hide(100)
          clearTimeout(this.left.timer)
          this.left.timer = null
        }, 2000)
      }
    },
    handlePanelChange(v, level) {
      this.panel.forEach((item) => {
        item.expand = item.level === level ? v : false
      })
    },
    // 点击新增算法
    handleAddAlgorithm(type, item) {
      this.algorithm.type = item.type
      this.algorithm.mode = 'add'
      this.algorithm.editData = null
      this.algorithm.show = true
    },
    // 点击编辑算法
    handleEditAlgorithm(type, item) {
      this.algorithm.mode = 'edit'
      this.algorithm.type = type
      this.algorithm.editData = deepClone(item)
      this.algorithm.show = true
    },
    // 点击删除算法
    handleDeleteAlgorithm(type, item, index) {
      this.algorithm.mode = 'delete'
      this.algorithm.type = type
      this.algorithm.editData = null
      this.algorithm.show = false
      this.curAlgorithmItem.splice(index, 1)
      this.handleQueryStrategyView()
    },
    handleDialogChange() {
      this.algorithm.show = false
    },
    handleDialogConfirm(v, data) {
      if (this.algorithm.mode === 'add') {
        data.hover = false
        this.curAlgorithmItem.push(data)
      } else if (this.algorithm.mode === 'edit') {
        const item = this.curAlgorithmItem.find(item => item.type === data.type)
        if (item) {
          Object.keys(data).forEach((key) => {
            item[key] = data[key]
          })
        }
      }
      this.algorithm.show = false
      this.handleQueryStrategyView()
    },
    // 关闭监控指标弹窗
    handleHideMetricDialog(v) {
      this.metric.show = v
      this.metric.isEdit = false
      this.metric.oldShow = v
      this.metric.oldisEdit = false
    },
    // 转换将指标项转换为组件所需数据
    async handleTransformMetric(data) {
      this.needFilterMethod = true
      this.header.typeId = data.result_table_label
      const objectType = data.data_target ? data.data_target.replace('_target', '').toLocaleUpperCase() : 'HOST'
      const metricData = {
        metricAliaName: data.metric_field_name,
        metricName: data.metric_field,
        dataTarget: objectType,
        dataTypeLabel: data.data_type_label,
        dataSourceLabel: data.data_source_label,
        resultTableLabel: data.result_table_label,
        resultTableName: data.result_table_name,
        objectType: objectType || '',
        targetType: objectType === 'HOST' ? 'INSTANCE' : 'TOPO', // topo 动态 instance 静态
        id: (data.data_type_label === 'log' && data.data_source_label !== 'bk_monitor') ? data.index_set_id : data.id,
        name: data.name || data.metric_field_name,
        unit: data.unit || '',
        unitSuffixId: data.unit_suffix_id || 'NONE',
        unitSuffixList: (data.unit_suffix_list || []).map(set => ({ ...set, id: set.id || 'NONE' })),
        unitConversion: data.unit_conversion,
        aggMethod: data.method_list && data.method_list.length ? data.method_list[0] : 'AVG',
        aggInterval: 60,
        relatedId: data.related_id || '',
        dimensionList: data.dimensions || [],
        conditionList: [],
        resultTableId: data.result_table_id,
        relatedName: data.related_name,
        dimensions: data.default_dimensions || [],
        conditions: (data.result_table_label === 'uptimecheck')
          ? (data.related_id && data.default_condition ? data.default_condition : [])
          : (data.default_condition || []),
        metricDes: data.metric_description || '',
        aggMethodList: data.method_list ? data.method_list.map(set => ({ id: set, name: set })) : [],
        algorithm: {
          deadly: [],
          warning: [],
          remind: []
        },
        triggerConfig: {
          count: data.default_trigger_config.count,
          checkWindow: data.default_trigger_config.check_window
        },
        recoveryConfig: {
          checkWindow: data.default_trigger_config.check_window
        },
        extendFields: data.extend_fields || {},
        metricDesc: data.remarks || [],
        metricDescVisible: !!(data.remarks && data.remarks.length)
      }
      if (metricData.dataSourceLabel === 'custom' && metricData.dataTypeLabel === 'event') {
        metricData.aggMethod = 'COUNT'
      }
      if ((metricData.dataTypeLabel === 'log' && metricData.dataSourceLabel !== 'bk_monitor')
        || (metricData.dataSourceLabel === 'bk_log_search' && metricData.dataTypeLabel === 'time_series')) {
        this.needFilterMethod = false
        const logFields = await this.getLogFields({
          bk_biz_id: this.$store.getters.bizId,
          index_set_id: data.index_set_id || data.related_id
        })
        if (metricData.dataTypeLabel === 'log') {
          metricData.indexStatement = '*'
        }
        metricData.aggMethod = metricData.dataTypeLabel === 'log' ? 'COUNT' : 'AVG'
        metricData.indexSetId = metricData.dataTypeLabel === 'log' ? data.index_set_id : data.related_id
        metricData.dimensionList = logFields.dimension || []
        metricData.conditionList = deepClone(logFields.dimension || [])
        metricData.conditionSet = logFields.condition || []
      } else {
        const conditionList = deepClone(data.dimensions || [])
        // if (metricData.dataTypeLabel !== 'event') {
        //     conditionList.push({
        //         id: data.metric_field,
        //         name: data.metric_field_name
        //     })
        // }
        metricData.conditionList = conditionList
      }
      // 系统事件只支持include、exclude和正则
      if (metricData.dataSourceLabel === 'bk_monitor' && metricData.dataTypeLabel === 'event') {
        metricData.conditionSet = [
          { id: 'eq', name: '=' },
          { id: 'neq', name: '!=' },
          { id: 'include', name: 'include' },
          { id: 'exclude', name: 'exclude' },
          { id: 'reg', name: 'regex' }
        ]
      }
      return metricData
    },
    // 点击编辑指标项
    handleEditMetric(item) {
      if (item.dataTypeLabel === 'log') {
        this.retrieval.show = true
        this.retrieval.indexId = item.dataSourceLabel === 'bk_monitor' ? item.id : item.indexSetId
      } else if (item.dataTypeLabel === 'event') {
        this.metric.oldShow = true
        this.metric.oldisEdit = true
        this.metric.metricObj = item
      } else {
        this.metric.show = true
        this.metric.isEdit = true
        this.metric.metricObj = item
      }
    },
    // 点击删除指标项
    handleDeleteMetric(item, index) {
      this.left.active = -1
      this.left.enter = -1
      this.more.active = false
      this.left.metricList.splice(index, 1)
      this.metric.metricObj = null
      this.validate.strategyAlgorithm = false
      this.strategyView.where = []
    },
    // 点击取消
    handleCancel(needBack = true) {
      return new Promise((resolve) => {
        this.$bkInfo({
          title: this.$t('是否放弃本次操作？'),
          confirmFn: () => {
            this.needCheck = false
            needBack && this.$router.back()
            resolve(true)
          },
          cancelFn: () => resolve(false)
        })
      })
    },
    // 点击保存
    handleSaveAndset() {
      if (this.handleValidate()) {
        this.loading = true
        const params = this.handleTransformParams()
        if (params) {
          this.addStrategyConfig(params).then(() => {
            this.$bkMessage({
              theme: 'success',
              message: this.id ? this.$t('编辑策略成功') : this.$t('创建策略成功')
            })
            this.needCheck = false
            this.$router.push({ name: 'strategy-config' })
          })
            .finally(() => {
              this.loading = false
            })
        }
      }
    },
    // 点击跳转到选择目标
    handleGotoSelectTarget() {
      if (this.handleValidate()) {
        const params = this.handleTransformParams()
        this[SET_STRATEGY_PARAMS](params)
        this.$router.push({
          name: 'strategy-config-target',
          params: {
            objectType: this.curMetricItem.dataTarget,
            strategyId: this.id
          }
        })
      }
    },
    // 保存前验证
    handleValidate() {
      let mark = true
      const { dataTypeLabel, triggerConfig, recoveryConfig, dataSourceLabel } = this.curMetricItem
      const { noDataConfig } = this.more
      const { actionType, noticeGroup } = this.curNoticeConfig
      if (this.header.strategyName.trim().length < 1) {
        this.validate.strategyName = true
        this.$refs.strategyName.$refs.input.focus()
        mark = false
      }
      if (actionType.length < 1 || (actionType.includes('notice') && noticeGroup.length < 1)) {
        this.validate.noticeGroup = true
        mark = false
      }
      if ((triggerConfig.checkWindow < 1 || triggerConfig.count < 1)
                    || ((`${triggerConfig.checkWindow}`).match(/\./) || (`${triggerConfig.count}`).match(/\./))
                    || (+triggerConfig.checkWindow < +triggerConfig.count)) {
        this.validate.triggerValidate = true
        mark = false
        this.more.active = true
      }
      if ((recoveryConfig.checkWindow < 1)
                    || ((`${recoveryConfig.checkWindow}`).match(/\./))) {
        // || (+recoveryConfig.checkWindow < +triggerConfig.checkWindow)
        this.validate.recoverValidate = true
        mark = false
        this.more.active = true
      }
      if (this.curNoticeConfig.noticeConfig.alarmInterval <= 0) {
        this.validate.alarmInterval = true
        mark = false
      }
      if (noDataConfig.continuous < 1 || (`${noDataConfig.continuous}`).match(/\./)) {
        this.validate.noDataValidate = true
        mark = false
        this.more.active = true
      }
      if (dataTypeLabel === 'event' && dataSourceLabel === 'bk_monitor' && this.algorithm.eventLevel < 1) {
        this.validate.eventLevel = true
        mark = false
      }
      if ((dataSourceLabel !== 'bk_monitor') && !this.hasAlgorithm) {
        this.validate.strategyAlgorithm = true
        mark = false
      }
      // 验证索引语句是否为空
      if (dataTypeLabel === 'log' && dataSourceLabel !== 'bk_monitor'
        && this.curMetricItem.indexStatement.length === 0) {
        this.validate.indexStatement = true
        mark = false
      }
      // 汇聚周期
      if (!(dataTypeLabel === 'event' && dataSourceLabel === 'bk_monitor') && !this.curMetricItem.aggInterval) {
        this.validate.aggInterval = true
        mark = false
      }
      //   验证监控目标
      // if (this.canSetTarget && this.target.list.length < 1) {
      //   this.validate.target = true
      //   mark = false
      // }
      // 监控维度
      if (this.header.typeId === 'uptimecheck' && noDataConfig.dimensionList.length < 1) {
        this.$bkMessage({
          theme: 'error',
          message: this.$t('请选择监控维度')
        })
        this.validate.dimensions = true
        mark = false
      }
      // 验证监控条件
      if (this.handleValidateMethods()) {
        mark = false
        this.$bkMessage({
          theme: 'error',
          message: this.$t('不支持大于、大于等于、小于和小于等于条件')
        })
      }
      return mark
    },
    handleValidateMethods() {
      return this.left.metricList.some((item) => {
        let aggCondition = null
        // 只校验【监控采集】类(非系统事件)的指标 ---（日志和自定义事件不校验）
        if (item.dataTypeLabel !== 'event' && item.dataSourceLabel === 'bk_monitor') {
          aggCondition = this.$refs[`condition-${item.id}`][0].getValue()
        }
        // 监控条件不支持 <, <=, >, >=
        const excludeMethods = aggCondition?.some(item => item && ['gt', 'gte', 'lt', 'lte'].includes(item.method))
        return excludeMethods
      })
    },
    handleGetAlarmData(item) {
      return this.curMetricItem && this.curMetricItem.algorithm ? this.curMetricItem.algorithm[item.type] : []
    },
    // 设置告警组弹窗关闭
    handleSetGroupHide() {
      const dropInstance = this.$refs.alarmGroupSelect && this.$refs.alarmGroupSelect.$refs.selectDropdown.instance
      if (dropInstance?.state.isVisible) {
        dropInstance.hide(0)
      }
    },
    // 点击新增告警组
    handleCreateAlarmGroup() {
      this.handleSetGroupHide()
      this.$router.push({
        name: 'alarm-group-add',
        params: {
          strategyId: this.id || '0'
        }
      })
    },
    handleSetInt(data, key, v) {
      if (v) {
        data[key] = +(`${v}`).replace(/\./g, '')
      }
    },
    // 转换提交后台参数
    handleTransformParams() {
      try {
        const { header } = this
        const { noDataConfig } = this.more
        let target = null
        const itemList = this.left.metricList.map((item) => {
          let aggDimension = []
          let aggCondition = []
          if (!(item.dataTypeLabel === 'event' && item.dataSourceLabel === 'bk_monitor')) {
            // aggDimension = this.curMetricItem.aggMethod === 'REAL_TIME' || (item.dataTypeLabel === 'event' && item.dataSourceLabel === 'custom') ? [] : this.$refs['dimension-' + item.id][0].getValue()
            aggDimension = this.curMetricItem.aggMethod === 'REAL_TIME'
              ? []
              : this.$refs[`dimension-${item.id}`][0].getValue()
          }
          aggCondition = this.$refs[`condition-${item.id}`][0].getValue()
          const algorithmList = []
          Object.keys(item.algorithm).forEach((key) => {
            const algorithmData = item.algorithm[key]
            const { level } = this.panel.find(set => set.type === key)
            // if (item.dataTypeLabel === 'event') {
            if (item.dataTypeLabel === 'event' && item.dataSourceLabel === 'bk_monitor') {
              if (this.algorithm.eventLevel === level) {
                algorithmList.push({
                  level,
                  algorithm_list: []
                })
              }
            } else if (algorithmData.length) {
              algorithmList.push({
                level,
                algorithm_list: algorithmData.map((set) => {
                  if (set.type === 'Threshold') {
                    return {
                      algorithm_type: set.type,
                      algorithm_config: this.handleConfig2Threshold(set.config),
                      algorithm_unit: set.algorithmUnit === 'NONE' ? '' : set.algorithmUnit
                    }
                  }
                  return {
                    algorithm_type: set.type,
                    algorithm_config: set.config,
                    algorithm_unit: set.algorithmUnit === 'NONE' ? '' : set.algorithmUnit
                  }
                })
              })
            }
          })

          const itemConfig = {
            id: item.itemId || 0,
            name: item.name || '',
            data_type_label: item.dataTypeLabel,
            data_source_label: item.dataSourceLabel,
            result_table_id: item.resultTableId,
            result_table_label: item.resultTableLabel,
            agg_method: item.aggMethod,
            agg_interval: item.aggInterval,
            agg_dimension: aggDimension,
            agg_condition: aggCondition,
            metric_field: item.metricName,
            keywords_query_string: item.indexStatement || '',
            unit: item.unit,
            unit_conversion: item.unitConversion,
            trigger_config: {
              count: +item.triggerConfig.count,
              check_window: +item.triggerConfig.checkWindow
            },
            recovery_config: {
              check_window: +item.recoveryConfig.checkWindow
            },
            detect_algorithm_list: algorithmList,
            extend_fields: item.extendFields
          }
          if (this.canSetTarget) {
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
            let field = ''
            if (this.curMetricItem.dataTarget === 'HOST') {
              field = hostTargetFieldType[item.targetType]
            } else {
              field = serviceTargetFieldType[item.targetType]
            }
            target = this.target?.list?.length ? [[{
              field,
              method: 'eq',
              value: this.handleCheckedData(item.targetType, this.target.list)
            }]] : []
            itemConfig.target = target
          }

          return itemConfig
        })
        const noticeList = this.noticeList.map((item) => {
          const config = item.noticeConfig
          const typeList = item.actionType
          return typeList.map((type) => {
            const configData = {
              alarm_interval: +config.alarmInterval,
              alarm_end_time: config.alarmTimeRange[1] || '',
              alarm_start_time: config.alarmTimeRange[0] || '',
              send_recovery_alarm: config.sendRecoveryAlarm
            }
            if (type === 'notice') {
              return {
                id: item.actionId || 0,
                action_type: type,
                config: configData,
                notice_group_list: item.noticeGroup
              }
            }
            return {
              id: item.messageActionId || 0,
              action_type: type,
              config: configData
            }
          })
        })
        const params = {
          name: header.strategyName,
          bk_biz_id: header.bizId,
          source_type: header.sourceType,
          scenario: header.typeId,
          data_target: this.curMetricItem.dataTarget,
          no_data_config: {
            continuous: +noDataConfig.continuous,
            is_enabled: noDataConfig.isEnable
          },
          message_template: this.more.messageTemplate,
          item_list: itemList,
          action_list: noticeList[0],
          labels: header.labels
        }
        if (!this.canSetTarget && this.curMetricItem.dimensionList.length) {
          params.no_data_config.agg_dimension = noDataConfig.dimensions || []
        }
        if (this.id) {
          params.id = this.id
        }
        return params
      } catch (e) {
        console.error(e)
        this.loading = false
        return null
      }
    },
    // 简化参数给后端，不然会报错
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
    // 编辑时设置监控目标描述
    handleSetTargetDesc(targetList, bkTargetType, bkObjType) {
      if (targetList?.length) {
        const len = targetList.length
        if (['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
          const count = targetList.reduce((pre, item) => {
            const allHost = item.all_host || []
            return Array.from(new Set([...pre, ...allHost]))
          }, []).length
          const textMap = {
            TOPO: `${this.$t('个')}${this.$t('节点')}`,
            SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
            SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
          }
          this.target.desc.message = `${len} ${textMap[bkTargetType]}`
          const subText = bkObjType === 'SERVICE'
            ? `${this.$t('个')}${this.$t('实例')}`
            : `${this.$t('台')}${this.$t('主机')}`
          this.target.desc.subMessage = `（ ${count} ${subText}）`
        } else {
          this.target.desc.message = `${len} ${this.$t('台')}${this.$t('主机')}`
        }
      } else {
        this.target.desc.message = ''
        this.target.desc.subMessage = ''
      }
    },
    // 编辑进入获取策略详情
    getDetialData() {
      return new Promise((resolve, reject) => {
        strategyConfigDetail({ id: this.id }).then((data) => {
          this.$store.commit('app/SET_NAV_TITLE', `${this.$t('编辑')} - #${this.id} ${data.strategy_name}`)
          this.needFilterMethod = true
          const listData = []
          const promiseList = data.item_list.map(item => (async (item) => {
            let dimensionList = []
            let conditionList = []
            const SetData = {}
            let dataTarget = 'NONE'
            if ((item.data_type_label === 'log' && item.data_source_label !== 'bk_monitor')
              || (item.data_source_label === 'bk_log_search' && item.data_type_label === 'time_series')) {
              this.needFilterMethod = false
              const logFields = await this.getLogFields({
                bk_biz_id: this.$store.getters.bizId,
                index_set_id: item.index_set_id || item.extend_fields.index_set_id
              })
              SetData.indexStatement = item.keywords_query_string || ''
              SetData.aggMethod = item.data_source_label === 'bk_log_search' ? item.agg_method : 'COUNT'
              SetData.indexSetId = item.index_set_id || ''
              SetData.dimensionList = logFields.dimension || []
              SetData.conditionList = deepClone(logFields.dimension || [])
              SetData.conditionSet = logFields.condition || []
            } else {
              const res = await getMetricList({
                data_source_label: item.data_source_label,
                data_type_label: item.data_type_label,
                page: 1,
                page_size: 10,
                search_fields: {
                  result_table_id: item.result_table_id,
                  metric_field: item.metric_field
                }

              })
              const metricData = res.metric_list.find(set => {
                return set.metric_field === item.metric_field
                        && set.result_table_id === item.result_table_id
                        && set.data_source_label === item.data_source_label
                        && set.data_type_label === item.data_type_label
              }) || res.metric_list[0]
              dimensionList = metricData.dimensions
              conditionList = deepClone(dimensionList)
              if (item.data_type_label !== 'event' && data.scenario !== 'uptimecheck') {
                conditionList.push({ id: item.metric_field, name: item.name })
              }
              if (item.data_source_label === 'bk_monitor' && item.data_type_label === 'event') {
                SetData.conditionSet = [
                  { id: 'eq', name: '=' },
                  { id: 'neq', name: '!=' },
                  { id: 'include', name: 'include' },
                  { id: 'exclude', name: 'exclude' },
                  { id: 'reg', name: 'regex' }
                ]
              }
              SetData.dimensionList = dimensionList || []
              SetData.conditionList = conditionList
              if (metricData) {
                dataTarget =  metricData.data_target
                  ? metricData.data_target.replace('_target', '').toLocaleUpperCase()
                  : 'HOST'
              }
            }
            const algorithmsList = []
            let expandLevel = 0
            item.detect_algorithm_list.forEach((algorithm) => {
              if (item.data_type_label === 'event' && item.data_source_label === 'bk_monitor') {
                this.algorithm.eventLevel = algorithm.level
              } else {
                algorithmsList[algorithm.level] = algorithm.algorithm_list.map((set) => {
                  const setConfig = set.algorithm_config
                  if (set.algorithm_type !== 'Threshold') {
                    Object.keys(setConfig).forEach(key => (setConfig[key] === null && (setConfig[key] = '')))
                  }
                  return {
                    type: set.algorithm_type,
                    config: set.algorithm_type === 'Threshold' ? this.handleThreshold2Config(setConfig) : setConfig,
                    hover: false,
                    title: this.algorithmOptionMap[set.algorithm_type],
                    algorithmUnit: set.algorithm_unit || 'NONE'
                  }
                })
                if (!expandLevel && algorithmsList[algorithm.level]) {
                  expandLevel = algorithm.level
                }
              }
            })
            expandLevel > 1 && this.handlePanelChange(true, expandLevel)
            this.mericType = item.data_type_label === 'event' ? 'event' : 'common'
            const setItem = {
              metricAliaName: item.name,
              metricName: item.metric_field,
              dataTarget,
              dataTypeLabel: item.data_type_label,
              dataSourceLabel: item.data_source_label,
              resultTableLabel: item.result_table_label,
              resultTableName: item.result_table_name,
              id: item.data_type_label === 'log' ? item.index_set_id : item.id,
              itemId: item.item_id || 0,
              name: item.name,
              unit: item.unit,
              unitSuffixId: item.unit_suffix_id || 'NONE',
              unitSuffixList: (item.unit_suffix_list || []).map(set => ({ ...set, id: set.id || 'NONE' })),
              unitConversion: item.unit_conversion,
              aggMethod: item.agg_method,
              aggMethodList: item.method_list && item.method_list.length
                ? item.method_list.map(set => ({ id: set, name: set })) : [],
              aggInterval: item.agg_interval || 60,
              dimensionList,
              conditionList,
              resultTableId: item.result_table_id,
              relatedName: item.related_name || '',
              dimensions: item.agg_dimension,
              conditions: item.agg_condition,
              relatedId: item.related_id || '',
              metricDes: item.metric_description || '',
              objectType: data.bk_obj_type || '',
              targetType: data.bk_target_type || '',
              metricDesc: item.remarks || [],
              metricDescVisible: !!(item.remarks && item.remarks.length),
              algorithm: {
                deadly: algorithmsList[1] || [],
                warning: algorithmsList[2] || [],
                remind: algorithmsList[3] || []
              },
              triggerConfig: {
                count: item.trigger_config.count,
                checkWindow: item.trigger_config.check_window
              },
              recoveryConfig: {
                checkWindow: item.recovery_config && item.recovery_config.check_window
              },
              extendFields: item.extend_fields || {}
            }
            listData.push(Object.assign(setItem, SetData))
          })(item))
          Promise.all(promiseList).then(() => {
            const { header, more, target } = this
            header.bizId = data.bk_biz_id
            header.strategyName = data.name
            header.sourceType = data.source_type
            header.typeId = data.scenario
            header.labels = data.labels ? data.labels.map(item => `/${item}/`) : []
            if (data.bk_target_type === 'TOPO') {
              // 为topo时，bk_target_detail字段和itemTarget[0][0].value一样，但是内容更详细，这里为了获取名称来回显IP选择器
              target.list = data.bk_target_detail || []
            } else {
              const itemTarget = data.item_list[0].target
              target.list = itemTarget?.length && itemTarget[0].length ? itemTarget[0][0].value : []
            }

            this.handleSetTargetDesc(data.bk_target_detail, data.bk_target_type, data.bk_obj_type)
            more.noDataConfig.continuous = data.no_data_config.continuous
            more.noDataConfig.isEnable = data.no_data_config.is_enabled
            more.noDataConfig.dimensions = data.no_data_config.agg_dimension || []
            const noticeData = data.action_list.find(set => set.action_type === 'notice')
            const messageData = data.action_list.find(set => set.action_type === 'message_queue')
            const noticeListata = {
              actionId: noticeData ? noticeData.action_id : 0,
              messageActionId: messageData ? messageData.action_id : 0,
              actionType: data.action_list.map(set => set.action_type),
              noticeConfig: {
                sendRecoveryAlarm: noticeData
                  ? noticeData.config.send_recovery_alarm
                  : messageData.config.send_recovery_alarm,
                alarmTimeRange: [
                  noticeData
                    ? noticeData.config.alarm_start_time
                    : messageData.config.alarm_start_time,
                  noticeData
                    ? noticeData.config.alarm_end_time
                    : messageData.config.alarm_end_time
                ],
                alarmInterval: noticeData
                  ? noticeData.config.alarm_interval
                  : messageData.config.alarm_interval
              },
              noticeGroup: noticeData ? noticeData.notice_group_id_list : messageData.notice_group_id_list
            }
            this.noticeList = [noticeListata]
            more.messageTemplate = data.message_template
            this.left.metricList = listData
            this.left.active = 0
            // 初始化策略视图的where条件
            this.strategyView.where = listData[0]?.conditions || []
            this.algorithm.type = Object.keys(this.curMetricItem.algorithm)
              .find(key => this.curMetricItem.algorithm[key].length > 0)
            this.panel.forEach(set => (set.expand = this.algorithm.type === set.type))
            // this.algorithm.editData = this.curAlgorithmItem
            resolve()
          })
            .catch(reject)
        })
          .catch(reject)
      })
    },
    getLabelListApi() {
      const params = {
        bk_biz_id: this.$store.getters.bizId,
        strategy_id: 0
      }
      strategyLabelList(params).then((res) => {
        const data = transformDataKey(res)
        const globalData = [
          ...data.global,
          ...data.globalParentNodes.map(item => ({ id: item.labelId, labelName: item.labelName }))
        ]
        const customData = [
          ...data.custom,
          ...data.customParentNodes.map(item => ({ id: item.labelId, labelName: item.labelName }))
        ]
        this.labelTreeData = [
          {
            group: 'global',
            groupName: '全局标签',
            children: labelListToTreeData(globalData)
          },
          {
            group: 'custom',
            groupName: '自定义标签',
            children: labelListToTreeData(customData)
          }
        ]
      })
    },
    // 是否支持实时数据
    showRealTime(item) {
      return item.dataSourceLabel === 'bk_monitor'
        && item.dataTypeLabel === 'time_series' && /^system\./.test(item.resultTableId)
    },
    handleFromPerformentPararms() {
      const metric = this.$route.query.data ? JSON.parse(this.$route.query.data) : this.$route.params.data
      const data = {
        aggCondition: metric.where || [],
        aggDimension: metric.group_by || [],
        aggInterval: metric.interval,
        aggMethod: metric.method,
        dataSourceLabel: metric.data_source_label,
        dataTypeLabel: metric.data_type_label,
        metricAliaName: metric.metric_field,
        metricName: metric.metric_field,
        relatedName: '',
        relatedId: '',
        resultTableId: metric.result_table_id,
        resultTableLabel: metric.result_table_label,
        targets: (metric.target || []).map(item => ({ ip: item.bk_target_ip, bk_cloud_id: item.bk_target_cloud_id }))
      }
      this.handleDatadDashboard(data)
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
    },
    // 监控条件值变更
    handleConditionsValue(data) {
      if (!data) return

      this.strategyView.where = data.filter(item => item.value && !!item.value.length)
      if (this.strategyView.where.length === 0) return

      this.handleQueryStrategyView(true)
    },
    queryStrategyView(refreshDimension = false) {
      this.$refs.strategyView && this.$refs.strategyView.handleQueryChart(refreshDimension)
    },
    handleCycleInput() {
      this.handleQueryStrategyView()
    },
    handleLabelCheckedChange(checked) {
      this.header.labels = checked
    }
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

@mixin strategy-panel ($height: 240px) {
  min-height: $height;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .1);
  margin-bottom: 16px;
}
@mixin strategy-title {
  margin: 22px 0 0 36px;
  font-weight: bold;
  margin-bottom: 15px;
}

.strategy-config {
  display: flex;
  &-left {
    flex: 1;
  }
  &-right {
    .right-wrapper {
      position: relative;
      background: #fff;
      box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .1);
      min-height: calc(100% - 68px);
    }
  }
}
.strategy-config-set {
  color: #63656e;
  &.set-loading {
    left: 0;
    right: 0;
    height: calc(100vh - 80px);

    /* stylelint-disable-next-line declaration-no-important */
    position: absolute !important;
  }
  .set-add {
    display: flex;
    flex-direction: column;
    margin-bottom: 16px;

    @include strategy-panel;
    &-title {
      margin-bottom: 25px;

      @include strategy-title;
    }
    &-item {
      display: flex;
      position: relative;
      align-items: center;
      margin-bottom: 20px;
      .item-label {
        position: relative;
        width: 126px;
        text-align: right;
        &::after {
          content: "*";
          color: #ea3636;
        }
      }
      .no-required {
        &::after {
          display: none;
        }
      }
      .item-label {
        align-self: flex-start;
        margin-top: 7px;
      }
      .item-content {
        flex: 1 1 465px;
        max-width: 465px;
        margin-left: 14px;
        .header-select {
          width: 200px;
        }
      }
      .item-icon {
        position: absolute;
        left: 74px;
        font-size: 14px;
        color: #7a8193;
        top: 3px;
        cursor: pointer;
      }
      .error-check {
        /deep/ .bk-form-input {
          border-color: #ea3636;
        }
      }
    }
  }
  .set-panel {
    display: flex;
    align-items: center;
    padding: 0 4px;

    @include strategy-panel(64px);
    &-item {
      display: flex;
      color: #3a84ff;
      margin-left: 16px;
      align-items: center;
      cursor: pointer;
      .item-icon {
        font-size: 16px;
      }
      .item-content {
        margin: 0 16px 0 6px;
        position: relative;
        &.need-split {
          &::after {
            color: #dcdee5;
            content: "|";
            width: 1px;
            height: 12px;
            position: absolute;
            right: -16px;
            top: 2px;
          }
        }
      }
    }
  }
  .set-notice {
    display: flex;
    flex-direction: column;
    margin-bottom: 20px;
    font-size: 12px;

    @include strategy-panel(280px);
    &-title {
      margin-bottom: 30px;

      @include strategy-title;
    }
    &-item {
      display: flex;
      align-items: center;
      position: relative;
      margin-bottom: 20px;
      .item-label {
        text-align: right;
        width: 126px;
        padding-right: 5px;
        margin-right: 16px;
        &.label-required {
          position: relative;
          &::after {
            content: "*";
            color: #ea3636;
            position: absolute;
            left: 126px;
            top: 2px;
          }
        }
        &.item-notice {
          position: absolute;
          top: -2px;
        }
      }
      .item-content {
        display: flex;
        align-items: center;
        flex: 1;
        margin-right: 40px;
        position: relative;
        &.notice-content {
          margin-left: 98px;
          .content-wrap {
            display: flex;
            flex-direction: column;
            .content-item {
              margin-bottom: 20px;
            }
          }
          .content-select {
            margin: 10px 0 20px;
            position: relative;
          }
          .content-queue {
            color: #979ba5;
            font-size: 12px;
            margin: 10px 0 20px 24px;
          }
        }
        .item-check {
          margin-right: 30px;
        }
        .item-input {
          min-width: 240px;
        }
        .item-interval {
          display: inline-block;
          width: 74px;
          margin: 0 10px;
        }
        /deep/ .bk-form-checkbox .bk-checkbox-text {
          font-size: 12px;
        }
      }
    }
  }
  .set-advance {
    display: flex;
    flex-direction: column;

    @include strategy-panel(64px);
    &-title {
      display: flex;
      margin: 20px 0 10px 13px;
      align-items: center;
      height: 24px;
      cursor: pointer;
      .bk-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
      }
      .title-name {
        font-weight: bold;
      }
    }
    &-content {
      .content-table {
        width: 100%;
        text-align: center;
        border-collapse: collapse;
        font-size: 12px;
        margin-bottom: 10px;
        tr {
          td {
            height: 44px;
            line-height: 44px;
            text-align: left;

            @include ellipsis;
            &.table-title {
              text-align: right;
              padding-right: 22px;
            }
            &.border-left {
              border-left: 0;
            }
            &.border-right {
              border-right: 0;
            }
            &.border-top {
              border-top: 0;
              &.alias-name {
                width: 180px;
                max-width: 180px;
              }
            }
            /deep/ .bk-input-number {
              position: relative;
              line-height: 32px;
              box-sizing: border-box;
              height: 32px;
              .input-number-option {
                height: 30px;
                background: none;
                top: 2px;
                bottom: 0px;
              }
            }
            .col-trigger {
              display: flex;
              align-items: center;
              &-input {
                width: 74px;
                display: flex;
                align-items: center;
                margin: 0 10px;
              }
            }
            .col-undefined {
              display: flex;
              align-items: center;
              &-input {
                width: 74px;
                margin: 0 10px;
              }
              &-switcher {
                margin-right: 10px;
              }
              &-select {
                width: 280px;
                margin: 0 10px;
              }
            }
            .trigger-icon {
              color: #ea3636;
              font-size: 16px;
              cursor: pointer;
              margin-left: 6px;
            }
          }
        }
      }
      .content-template {
        display: flex;
        width: 100%;
        font-size: 12px;
        &-left {
          flex: 0 0 145px;
          text-align: right;
          padding-right: 24px;
          padding-top: 4px;
        }
        &-right {
          flex: 1;
          padding-right: 51px;
          .right-content {
            margin-bottom: 7px;
          }
          /deep/ .bk-form-textarea {
            min-height: 60px;
          }
          .right-desc {
            font-size: 12px;
            color: #979ba5;
            display: flex;
            align-items: center;
            margin-top: 4px;
            .desc-detail,
            %desc-detail {
              color: #3a84ff;
              cursor: pointer;
              display: flex;
              align-items: center;
              height: 20px;
              i {
                height: 20px;
                font-size: 20px;
                display: flex;
                align-items: center;
              }
            }
            .preview-detail {
              margin-left: 10px;

              @extend %desc-detail;
            }
          }
        }
      }
    }
    &-btn {
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #3a84ff;
      font-size: 14px;
      cursor: pointer;
      &.more-disabled {
        color: #c4c6cc;
        cursor: not-allowed;
      }
      .icon-monitor {
        font-size: 24px;
        height: 24px;
        width: 24px;
        transition: transform .3s linear;
        transform-origin: center;
        display: flex;
        align-items: center;
        justify-content: center;
        &.more-active {
          transform: rotate(180deg);
        }
      }
    }
    .btn-disabled {
      /* stylelint-disable-next-line declaration-no-important */
      cursor: not-allowed !important;

      /* stylelint-disable-next-line declaration-no-important */
      color: #c4c6cc !important;
    }
  }
  .set-wrapper {
    display: flex;
    flex-direction: column;
    padding-bottom: 32px;

    @include strategy-panel(200px);
    &-title {
      display: flex;
      align-items: center;
      padding-right: 34px;
      margin-bottom: 20px;
      margin-top: 20px;

      @include strategy-title;
      .title-desc {
        color: #c4c6cc;
        font-weight: normal;
      }
      .title-icon {
        margin-left: auto;
      }
      .icon-monitor {
        font-size: 22px;
        color: #979ba5;
        &:hover {
          cursor: pointer;
          color: #3a84ff;
        }
      }
      .set-desc {
        font-size: 16px;
        margin-left: 8px;
      }
    }
    .right-form {
      flex: 0;
      &-item {
        display: flex;
        align-items: center;
        font-size: 12px;
        flex-wrap: wrap;
        margin-bottom: 20px;
        &.need-start {
          position: relative;
          // margin-top: 8px;
          align-items: flex-start;
          // min-height: 42px;
        }
        .item-label {
          text-align: right;
          width: 126px;
          margin-right: 16px;
          &.need-position {
            position: absolute;
            top: 7px;
          }
          &::after {
            content: "*";
            color: #ea3636;
            visibility: hidden;
          }
          &.item-required::after {
            visibility: visible;
          }
        }
        .item-content {
          display: flex;
          flex: 1;
          align-items: center;
          position: relative;
          // overflow: hidden;
          &.need-left {
            margin-left: 142px;
          }
          &-select {
            width: 180px;
            margin-right: 40px;
          }
          &-input {
            flex: 0 1 356px;
          }
          &.no-hidden {
            overflow: visible;
          }
          /deep/ .bk-form-radio {
            margin-right: 24px;
          }
          &.item-algorithms {
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;
          }
          .target-btn {
            color: #3a84ff;
            cursor: pointer;
          }
          .target-title {
            color: #c4c6cc;
          }
          .target-desc {
            color: #979ba5;
          }
        }
        .item-message {
          color: #979ba5;
          position: absolute;
          top: 34px;
          &-error {
            color: #ea3636;
            margin-top: -2px;
          }
        }
        &.mt-10 {
          margin-top: 10px;
        }
      }
    }
    /deep/ .right-panel {
      border-left: 0;
      border-right: 0;
      z-index: 2;
      &:not(:last-child) {
        border-bottom: 0;
      }
    }
  }
  .set-footer {
    font-size: 0;
    margin-bottom: 20px;
    &-btn {
      margin-left: 10px;
    }
  }
  .error-tips {
    font-size: 12px;
    color: #ea3636;
    margin-top: 2px;
    &.need-position {
      position: absolute;
      // bottom: -19px;
    }
    &.algorithm-error {
      min-width: 100%;
      margin-top: -4px;
      // margin-bottom: 11px;
    }
  }
}
.remind-tips {
  display: flex;
  flex-direction: column;
  padding: 0 16px;
  font-size: 12px;
  color: #63656e;
  width: 360px;
  &-title {
    font-weight: bold;
    font-size: 14px;
    color: #313238;
    margin-top: 16px;
  }
  &-desc {
    margin-top: 8px;
    .desc-strong {
      font-weight: bold;
    }
    .desc-important {
      color: #ea3636;
    }
  }
  &-content {
    margin-top: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    .content-label {
      flex: 0 0 104px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #f0f1f5;
      border-radius: 2px;
      height: 32px;
    }
  }
  &-footer {
    display: flex;
    margin-top: 10px;
    justify-content: flex-end;
    color: #3a84ff;
    cursor: pointer;
    margin-bottom: 18px;
  }
}
.alarm-group-wrap {
  display: flex;
  align-items: center;
  width: 100%;
  height: 52px;
  padding: 0 10px 0 20px;
  &:hover {
    background-color: #e1ecff;
  }
  .group-content {
    flex: 1;
    line-height: 20px;
    overflow: hidden;
    .item-name,
    .item-person {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .item-name {
      font-weight: 700;
      color: #63656e;
    }
    .item-person {
      color: #979ba5;
    }
  }
  .check-icon {
    font-size: 24px;
  }
}
.item-input-create {
  margin: 0 -16px;
  padding-left: 22px;
  background: #fff;
  color: #3a84ff;
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
</style>

<style lang="scss">
.alarm-group-popover {
  /deep/ .bk-option-content {
    padding: 0;
  }
}
</style>
