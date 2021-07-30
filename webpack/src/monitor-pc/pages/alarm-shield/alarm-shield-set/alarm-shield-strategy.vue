<template>
  <div class="alarm-shield-strategy">
    <!-- 所属 -->
    <div class="strategy-item">
      <div class="item-label"> {{ $t('所属') }} </div>
      <div class="strategy-item-content">
        <bk-select style="width: 413px;" readonly v-model="bizId">
          <bk-option v-for="(option, index) in bizList"
                     :key="index"
                     :id="option.id"
                     :name="option.text">
          </bk-option>
        </bk-select>
      </div>
    </div>
    <!-- 屏蔽策略 -->
    <div class="strategy-item" :class="{ 'verify-show': rule.strategyId }">
      <div class="item-label"> {{ $t('屏蔽策略') }} </div>
      <verify-input :show-validate.sync="rule.strategyId" :validator="{ content: $t('请选择屏蔽策略') }">
        <div class="strategy-item-content">
          <bk-select style="width: 836px;"
                     searchable
                     multiple
                     :disabled="isEdit"
                     v-model="strategyId"
                     @change="handleStrategyInfo">
            <bk-option v-for="option in strategyList"
                       :key="option.id"
                       :id="option.id"
                       :name="option.name">
              <span style="margin-right: 9px">{{ option.name }}</span>
              <span style="color: #c4c6cc">{{ option.firstLabelName }}-{{ option.secondLabelName }}（#{{ option.id }}）</span>
            </bk-option>
          </bk-select>
        </div>
      </verify-input>
    </div>
    <!-- 选择策略后展示 -->
    <template v-if="isShowDetail">
      <!-- 策略内容 -->
      <div class="strategy-detail" v-if="isOneStrategy">
        <div class="item-label"> {{ $t('策略内容') }} </div>
        <!-- 策略详情展示组件 -->
        <strategy-detail :strategy-data="strategyData"></strategy-detail>
      </div>
      <!-- 选择实例 IP 节点 -->
      <div class="strategy-detail" v-if="isShowShieldScope && !(dataTarget.length === 1 && dataTarget[0] === '')">
        <div class="item-label"> {{ $t('屏蔽范围') }} </div>
        <!-- 选择器组件 -->
        <shield-target ref="shieldTarget" :is-edit="isEdit" :target-data="targetData" :type="targetType" :data-target="dataTarget"></shield-target>
      </div>
      <div class="strategy-item">
        <div class="item-label"> {{ $t('告警等级') }} </div>
        <verify-input :show-validate="rule.noticeLever" :validator="{ content: $t('请至少选择一种告警等级') }">
          <div class="strategy-item-content">
            <bk-checkbox-group v-model="noticeLever" @change="handleAlarmLevel">
              <bk-checkbox v-for="(item, index) in levelMap" :key="index"
                           :value="index + 1" class="checkbox-group">
                {{ item }}
              </bk-checkbox>
            </bk-checkbox-group>
          </div>
        </verify-input>
      </div>
    </template>
    <!-- 屏蔽时间 -->
    <shield-date-config ref="noticeDate"></shield-date-config>
    <!-- 屏蔽时间 -->
    <div class="strategy-desc">
      <div class="item-label"> {{ $t('屏蔽原因') }} </div>
      <div class="strategy-desc-content">
        <bk-input class="content-desc" type="textarea" v-model="desc" :row="3" :maxlength="100"></bk-input>
      </div>
    </div>
    <!-- 通知组 -->
    <alarm-shield-notice ref="notice" @change-show="handleChangeShow"></alarm-shield-notice>
    <div class="strategy-form">
      <div class="strategy-btn">
        <bk-button class="button" :theme="'primary'" @click="handleSubmit"> {{ $t('提交') }} </bk-button>
        <bk-button class="button ml10"
                   :theme="'default'"
                   @click="$router.push({ name: 'alarm-shield' })">
          {{ $t('取消') }}
        </bk-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import ShieldDateConfig from '../alarm-shield-components/alarm-shield-date.vue'
import AlarmShieldNotice from '../alarm-shield-components/alarm-shield-notice.vue'
import VerifyInput from '../../../components/verify-input/verify-input.vue'
import ShieldTarget from '../alarm-shield-components/alarm-shield-target.vue'
import StrategyDetail from '../alarm-shield-components/strategy-detail.vue'
import { addShield, editShield } from '../../../../monitor-api/modules/shield'
import { plainStrategyList, strategyInfo } from '../../../../monitor-api/modules/strategies'
import alarmShieldMixin from '../../../mixins/alarmShieldMixin'
import strategyMapMixin from '../../../mixins/strategyMapMixin'
import { transformDataKey } from '../../../../monitor-common/utils/utils'
import { Component, Mixins, Watch, Ref, Prop } from 'vue-property-decorator'
// eslint-disable-next-line no-unused-vars
import { Location } from 'vue-router/types/router'
// eslint-disable-next-line no-unused-vars
import { TranslateResult } from 'vue-i18n/types/index'
// eslint-disable-next-line no-unused-vars
import MonitorVue from '../../../types/index'

interface IStrategyList {
  firstLabelName: string,
  id: string | number,
  name: string,
  scenario: string,
  secondLabelName: string
}
interface IParams {
  'bk_biz_id': string,
  category: string,
  'dimension_config': IDimensionConfig
  description: string,
  'shield_notice': boolean,
  'cycle_config': {},
  'begin_time': string,
  'end_time': string,
  'notice_config'?: {},
  id?: string,
  level?: string[]
}
interface IDimensionConfig {
  id: number[],
  level: string[],
  'scope_type'?: string,
  target?: []
}
@Component({
  components: {
    ShieldDateConfig,
    AlarmShieldNotice,
    VerifyInput,
    StrategyDetail,
    ShieldTarget
  }
})
export default class AlarmShieldStrategy extends Mixins(alarmShieldMixin, strategyMapMixin)<MonitorVue> {
  isEdit = false // 是否编辑
  bizList: { id: string, name: string }[] = [] // 业务列表
  bizId = '' // 当前业务
  strategyList: IStrategyList[] = [] // 蔽策略的列表
  strategyData: any = {} //   被屏蔽策略的数据
  strategyId: number[] = [] // 被屏蔽策略的id
  isShowDetail = false // 是否展示策略详情
  // isOneStrategy: boolean = false // 是否只选择一个策略
  noticeLever: string[] = [] // 告警等级
  desc = '' // 屏蔽原因
  noticeShow = false // 是否展示通知设置
  levelMap: TranslateResult[] = [] // 告警等级Map
  targetData: any[] = [] // 勾选的屏蔽范围
  targetType = '' // 屏蔽范围类型
  dataTarget: string[] = []
  //  校验提示
  rule: { strategyId: boolean, noticeLever: boolean } = {
    strategyId: false,
    noticeLever: false
  }

  //  屏蔽范围组件
  @Ref() readonly shieldTarget!: ShieldTarget
  //  编辑时回填的屏蔽详情数据
  @Prop({ default: () => ({}) })
  shieldData: any

  //  是否来自策略列表页
  @Prop({ default: () => ({}) })
  fromStrategy: { is: boolean, id: number}

  @Prop({ default: false })
  edit: boolean

  @Watch('shieldData', { deep: true })
  onShieldDataChange(v: any = {}): void {
    if (this.$route.name === 'alarm-shield-edit') {
      this.isEdit = true
      const data: any = transformDataKey(v)
      this.handleSetEditData(data)
    } else {
      this.isEdit = false
    }
  }

  //  是否展示屏蔽范围
  get isShowShieldScope(): boolean {
    if (this.isEdit) {
      return !!this.targetData.length
    }
    return this.strategyId.length !== 0
  }

  get isOneStrategy(): boolean {
    return this.strategyId.length === 1
  }

  created() {
    this.levelMap = [this.$t('致命'), this.$t('预警'), this.$t('提醒')]
  }

  activated() {
    this.bizId = this.$store.getters.bizId
    this.bizList = this.$store.getters.bizList
    this.getStrategyData()
  }

  //  告警勾选时校验
  handleAlarmLevel(arr: string[]): void {
    this.rule.noticeLever = !arr.length
  }

  //  编辑时 处理屏蔽详情数据
  handleSetEditData(data: any = {}): void {
    //  回填基本数据
    this.bizId = data.bkBizId
    this.strategyId = data.dimensionConfig.strategies.map(item => item.id)
    // this.strategyData = data.dimensionConfig.itemList[0]
    this.noticeLever = data.dimensionConfig.level
    this.desc = data.description
    //  回填通知时间 每天 每周 每月
    const { cycleConfig } = data
    const cycleMap: { 1: string, 2: string, 3: string, 4: string} = { 1: 'single', 2: 'day', 3: 'week', 4: 'month' }
    const type = cycleMap[cycleConfig.type]
    const shieldDate: any = {}
    shieldDate.typeEn = type
    shieldDate[type] = {
      list: [...cycleConfig.dayList, ...cycleConfig.weekList],
      range: [cycleConfig.beginTime, cycleConfig.endTime]
    }
    shieldDate.dateRange = [data.beginTime, data.endTime]
    //  单次
    if (cycleConfig.type === 1) {
      shieldDate[type].range = [data.beginTime, data.endTime]
      shieldDate.dateRange = []
    }
    const RNoticeDate: any = this.$refs.noticeDate
    RNoticeDate.setDate(shieldDate)
    //  回填通知设置部分数据
    this.noticeShow = data.shieldNotice
    if (this.noticeShow) {
      const shieldNoticeData = {
        notificationMethod: data.noticeConfig.noticeWay,
        noticeNumber: data.noticeConfig.noticeTime,
        member: {
          value: data.noticeConfig.noticeReceiver.map(item => item.id)
        }
      }
      const RNotice: any = this.$refs.notice
      RNotice.setNoticeData(shieldNoticeData)
    }
    //  回填屏蔽范围部分数据
    if (data.dimensionConfig.target && data.dimensionConfig.target.length) {
      this.targetData = data.dimensionConfig.target.map(item => ({ name: item }))
      this.targetType = data.dimensionConfig.scopeType
    }
  }

  //  获取策略轻量列表
  async getStrategyData(): Promise<any> {
    this.$emit('update:loading', true)
    const data = await plainStrategyList().catch(() => {
      this.$emit('update:loading', false)
    })
    this.strategyList = transformDataKey(data)
    if (!this.edit) {
      this.$emit('update:loading', false)
    }
  }

  //  获取被屏蔽的策略详情
  handleStrategyInfo(id: number[]): void {
    if (id.length === 0) {
      this.isShowDetail = true
      return
    }
    if (id.length === 1) {
      this.$emit('update:loading', true)
      this.isShowDetail = false
      if (!this.isEdit) {
        this.noticeLever = []
      }
      strategyInfo({ id: id[0] }).then((data) => {
        const [strategyDataItem] =  transformDataKey(data).itemList
        this.strategyData = strategyDataItem
        this.isShowDetail = true
      })
        .catch(() => {
          this.isShowDetail = false
        })
        .finally(() => {
          this.$emit('update:loading', false)
        })
    } else {
      this.isShowDetail = true
    }
    const res = this.strategyList.filter(item => id.indexOf(item.id) > -1).map(item => item.dataTarget)
    this.dataTarget = Array.from(new Set(res))
  }

  //  提交
  handleSubmit(): void {
    const RNotice: any = this.$refs.notice
    const notice = RNotice.getNoticeConfig()
    const RNoticeDate: any = this.$refs.noticeDate
    const date = RNoticeDate.getDateData()
    if (!this.strategyId || !this.noticeLever.length || !notice || !date) {
      this.rule.strategyId = !this.strategyId
      this.rule.noticeLever = !this.noticeLever.length
      return
    }
    const cycle = this.getDateConfig(date)

    const params: IParams = {
      bk_biz_id: this.bizId,
      category: 'strategy',
      dimension_config: {
        id: this.strategyId,
        level: this.noticeLever
      },
      description: this.desc,
      shield_notice: this.noticeShow,
      cycle_config: cycle.cycle_config,
      begin_time: cycle.begin_time,
      end_time: cycle.end_time
    }
    if (this.shieldTarget && !this.isEdit && this.isShowShieldScope) {
      const targetData: {'scope_type': string, target: [] } = this.shieldTarget.getTargetData()
      if (targetData.target.length) {
        params.dimension_config.scope_type = targetData.scope_type
        params.dimension_config.target = targetData.target
      }
    }
    if (this.noticeShow) {
      params.notice_config = notice
    }
    this.$emit('update:loading', true)
    const routerParams: Location = { name: 'alarm-shield', params: { refresh: 'true' } }
    if (this.isEdit) {
      params.id = this.shieldData.id
      params.level = this.noticeLever
      editShield(params).then(() => {
        this.$bkMessage({ theme: 'success', message: this.$t('修改成功') })
        this.$router.push(routerParams)
      })
        .finally(() => {
          this.$emit('update:loading', false)
        })
    } else {
      addShield(params).then(() => {
        this.$bkMessage({ theme: 'success', message: this.$t('恭喜，屏蔽创建成功') })
        this.$router.push(routerParams)
      })
        .finally(() => {
          this.$emit('update:loading', false)
        })
    }
  }

  //  是否展示通知设置
  handleChangeShow(v): void {
    this.noticeShow = v
  }
}
</script>

<style lang="scss" scoped>
    .alarm-shield-strategy {
      min-height: calc(100vh - 145px);
      font-size: 14px;
      color: #63656e;
      padding: 40px 0 36px 30px;
      .strategy-btn {
        margin-left: 134px;
        .button {
          margin-right: 8px;
        }
      }
      .verify-show {
        /* stylelint-disable-next-line declaration-no-important */
        margin-bottom: 32px !important;
      }
      .strategy-item {
        display: flex;
        align-items: center;
        height: 32px;
        margin-bottom: 20px;
        .item-label {
          min-width: 110px;
          text-align: right;
          margin-right: 24px;
          position: relative;
          flex: 0 0;
          &::before {
            content: "*";
            color: #ea3636;
            position: absolute;
            top: 2px;
            right: -9px;
          }
        }
        &-content {
          flex-grow: 1;
          .checkbox-group {
            margin-right: 32px;
          }
        }
      }
      .strategy-detail {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        .item-label {
          min-width: 110px;
          text-align: right;
          margin-right: 24px;
          padding-top: 6px;
          flex: 0 0;
        }
        &-content {
          display: flex;
          flex-direction: column;
          padding: 18px 21px 11px 21px;
          min-width: 836px;
          width: calc(100vw - 306px);
          background: #fafbfd;
          border: 1px solid #dcdee5;
          border-radius: 2px;
          .column-item {
            min-height: 32px;
            display: flex;
            align-items: flex-start;
            margin-bottom: 10px;
          }
          .item-label {
            min-width: 70px;
            text-align: right;
            margin-right: 6px;
          }
          .item-content {
            word-wrap: break-word;
            word-break: break-all;
          }
          .item-aggDimension {
            background: #fff;
            font-size: 12px;
            text-align: center;
            height: 32px;
            line-height: 16px;
            border-radius: 2px;
            border: 1px solid #dcdee5;
            margin: 0 2px 2px 0;
            padding: 7px 12px 9px 12px;
          }
          .item-aggCondition {
            max-width: calc(100vw - 322px);
            display: flex;
            flex-wrap: wrap;
            .item-blue {
              color: #3a84ff;
            }
            .item-yellow {
              color: #ff9c01;
            }
          }
          &-aggCondition {
            align-items: flex-start;
          }
        }
      }
      .strategy-desc,
      .strategy-form {
        display: flex;
        align-items: flex-start;
        height: 62px;
        margin-bottom: 17px;
        .item-label {
          min-width: 110px;
          text-align: right;
          margin-right: 24px;
          padding-top: 6px;
          flex: 0 0;
        }
        &-content {
          .content-desc {
            width: 836px;
          }
        }
        .strategy-btn {
          display: flex;
        }
        /deep/ .bk-textarea-wrapper .bk-form-textarea.textarea-maxlength {
          margin-bottom: 0;
        }
        /deep/ .bk-form-textarea {
          min-height: 60px;
        }
      }
      /deep/ .notice-component .set-shield-config-item .item-label {
        text-align: left;
      }
    }
</style>
