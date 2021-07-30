<template>
  <div v-bkloading="{ isLoading: loading }" class="escalation">
    <article class="escalation-form">
      <section class="escalation-form-title">{{ $t('基本信息') }}</section>
      <!--表单-->
      <section class="escalation-form-content">
        <bk-form :model="formData" :label-width="107">
          <!--ID-->
          <bk-form-item ext-cls="content-basic" :label="$t('数据ID') " required>
            <bk-input v-model="formData[currentItemIdName]" :placeholder="$t('系统自动生成')" disabled></bk-input>
          </bk-form-item>
          <!-- Token -->
          <bk-form-item ext-cls="content-basic" :label="'Token'" required>
            <bk-input v-model="formData.token" :placeholder="$t('系统自动生成')" disabled></bk-input>
          </bk-form-item>
          <!--名称-->
          <bk-form-item :ext-cls="rule.name ? 'content-check' : 'content-basic'" :label="$t('名称')" property="name" required>
            <verify-input :show-validate.sync="rule.name" :validator="{ content: rule.nameTips }">
              <bk-input v-model="formData.name"
                        :placeholder="type === 'customEvent' ? $t('请输入自定义事件名称') : $t('请输入数据ID的名称')"
                        @blur="handleCheckName">
              </bk-input>
            </verify-input>
          </bk-form-item>
          <!--监控对象-->
          <bk-form-item :ext-cls="rule.scenario ? 'content-check' : 'content-basic'" :label="$t('监控对象')" property="scenario" required>
            <verify-input :show-validate.sync="rule.scenario" :validator="{ content: $t('必填项') }">
              <bk-select v-model="formData.scenario" :placeholder="$t('请选择')" :clearable="false" class="form-content-select">
                <bk-option-group
                  v-for="(group, index) in scenarioList"
                  :name="group.name"
                  :key="index">
                  <bk-option v-for="(option, groupIndex) in group.children"
                             :key="groupIndex"
                             :id="option.id"
                             :name="option.name">
                  </bk-option>
                </bk-option-group>
              </bk-select>
            </verify-input>
          </bk-form-item>
        </bk-form>
      </section>
    </article>
    <!-- 事件列表 -->
    <div class="escalation-form escalation-list">
      <span class="escalation-form-title" v-if="type === 'customEvent'">{{ $t('事件列表') }}</span>
      <span class="escalation-form-title" v-else>{{ $t('时序列表') }}</span>
      <span class="escalation-list-explain">{{ $t('（新建完成后自动获取）') }}</span>
    </div>
    <!-- 底部按钮 -->
    <div class="escalation-footer">
      <bk-button
        class="mc-btn-add"
        theme="primary"
        @click="handleSubmit"
        :icon="btnLoadingIcon"
        :disabled="disableSubmit">
        {{ submitBtnText }}
      </bk-button>
      <bk-button @click="handleCancel" class="ml10 mc-btn-add"> {{ $t('取消') }} </bk-button>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Watch, Vue } from 'vue-property-decorator'
import VerifyInput from '../../components/verify-input/verify-input.vue'
import { createCustomEventGroup, createCustomTimeSeries } from '../../../monitor-api/modules/custom_report'
import { IRule, IFormData, IParams } from '../../types/custom-escalation/custom-escalation-set'
import MonitorVue from '../../types/index'
import { getLabel } from '../../../monitor-api/modules/commons'

@Component({
  components: {
    VerifyInput
  }
})
export default class customEscalationSet extends Vue<MonitorVue> {
//   //  区别自定义事件和自定义指标
//   @Prop({
//     default: 'customEvent',
//     validator: v => ['customEvent', 'customTimeSeries'].includes(v)
//   }) readonly type: string

  private loading = false
  private scenarioList: any[] = [] // 监控对象
  private currentItemIdName = 'bkEventGroupId' // 当前 ID 字段
  private disableSubmit = false // 是否禁用提交按钮（防止重复点击）
  private btnLoadingIcon = '' // 提交时显示按钮loading效果
  // 表单model
  private formData: IFormData = {
    bkEventGroupId: '',
    bkDataId: '',
    name: '',
    scenario: '',
    token: ''
  }

  // 校验
  private rule: IRule = {
    name: false,
    scenario: false,
    nameTips: ''
  }

  @Watch('type', { immediate: true })
  onTypeChange(v: string) {
    v === 'customEvent' ? this.currentItemIdName = 'bkEventGroupId' : this.currentItemIdName = 'bkDataId'
  }

  //  按钮文案
  get submitBtnText() {
    if (this.btnLoadingIcon === 'loading') {
      return this.$t('创建中...')
    }
    return this.$t('提交')
  }

  get type() {
    return this.$route.name === 'custom-set-event' ? 'customEvent' : 'customTimeSeries'
  }

  created() {
    this.handleInit()
    this.rule.nameTips = this.$tc('必填项')
  }

  //  表单初始化
  async handleInit() {
    this.loading = true
    this.type === 'customEvent'
      ? this.$store.commit('app/SET_NAV_TITLE', this.$t('新建自定义事件'))
      : this.$store.commit('app/SET_NAV_TITLE', this.$t('新建自定义指标'))
    if (!this.scenarioList.length) {
      // this.scenarioList = await this.$store.dispatch('custom-escalation/getScenarioList')
      this.scenarioList = await getLabel({ include_admin_only: false }).catch(() => [])
    }
    this.loading = false
  }

  //  名字失焦校验
  async handleCheckName() {
    if (this.formData.name) {
      const res = this.type === 'customEvent'
        ? await this.$store.dispatch('custom-escalation/validateCustomEventName', { name: this.formData.name })
        : await this.$store.dispatch('custom-escalation/validateCustomTimetName', { name: this.formData.name })
      if (!res) {
        this.rule.nameTips = this.$tc('名称已存在')
        this.rule.name = true
      }
    }
  }

  //  提交前校验
  beforeSubmit() {
    let res = true
    if (!this.formData.name) {
      res = false
      this.rule.name = true
    }
    if (!this.formData.scenario) {
      res = false
      this.rule.scenario = true
    }
    return res
  }

  //  提交（事件、时序）
  async handleSubmit() {
    if (!this.beforeSubmit()) {
      return
    }
    this.disableSubmit = true
    this.btnLoadingIcon = 'loading'
    const params = {
      name: this.formData.name,
      scenario: this.formData.scenario
    }
    let result: IParams = {}
    if (this.type === 'customEvent') {
      // 自定义事件
      result = await createCustomEventGroup(params).catch(() => ({ bk_event_group_id: '' }))
      this.handleToDetail(result.bk_event_group_id)
    } else {
      // 自定义指标
      result = await createCustomTimeSeries(params).catch(() => ({ time_series_group_id: '' }))
      this.handleToDetail(result.time_series_group_id)
    }
    this.disableSubmit = false
    this.btnLoadingIcon = ''
  }

  //  跳转详情
  handleToDetail(id: string) {
    if (id) {
      this.$bkMessage({
        theme: 'success',
        message: this.$t('创建成功')
      })

      const name = this.type === 'customEvent' ? 'custom-detail-event' : 'custom-detail-timeseries'
      this.$router.replace({
        name,
        params: {
          id,
          isCreat: 'creat'
        }
      })
    }
  }

  //  取消按钮
  handleCancel() {
    this.$router.push({ name: 'custom-escalation' })
  }
}
</script>

<style lang="scss" scoped>
    @import "../../static/css/common";

    /deep/ {
      .bk-button-icon-loading::before {
        content: "";
      }
      .step-verify-input .bottom-text {
        padding-top: 10px;
      }
    }
    .escalation {
      height: calc(100vh - 80px);
      &-form {
        font-size: 12px;
        padding: 23px 20px 4px 37px;
        border-radius: 2px;
        background: $whiteColor;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, .1);

        @include border-1px($color: $defaultBorderColor);
        &-title {
          font-weight: bold;
        }
        &-content {
          margin-top: 25px;
          .content-basic {
            margin-bottom: 20px;
            width: 576px;
          }
          .content-check {
            margin-bottom: 32px;
            width: 576px;
          }
          .form-content-select {
            width: 180px;
          }
        }
      }
      &-list {
        margin-top: 16px;
        padding-bottom: 24px;
        height: 64px;
        display: flex;
        align-items: center;
        &-explain {
          color: $unsetIconColor;
        }
      }
      &-footer {
        margin-top: 20px;
      }
    }
</style>
