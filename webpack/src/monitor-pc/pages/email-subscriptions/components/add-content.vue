<template>
  <bk-sideslider
    class="add-content-wrap"
    :width="806"
    :is-show.sync="isShow"
    :quick-close="true">
    <div slot="header">{{ $t('添加内容') }}</div>
    <div class="content-main" slot="content">
      <bk-form
        :model="formData"
        :rules="rules"
        ref="validateForm"
        :label-width="113"
        class="form-wrap">
        <bk-form-item :label="$t('子标题')" :required="true" :property="'contentTitle'" :error-display-type="'normal'">
          <bk-input
            class="input"
            :placeholder="$t('请输入子标题')"
            v-model="formData.contentTitle"></bk-input>
        </bk-form-item>
        <bk-form-item :label="$t('说明')">
          <bk-input
            class="input"
            :placeholder="$t('请输入说明')"
            :type="'textarea'"
            :rows="3"
            :maxlength="200"
            v-model="formData.contentDetails">
          </bk-input>
        </bk-form-item>
        <bk-form-item :label="$t('模块布局')" :required="true">
          <bk-radio-group class="radio-wrap" v-model="formData.rowPicturesNum">
            <bk-radio :value="2">{{`2${$t('个/行')}`}}</bk-radio>
            <bk-radio :value="1">{{`1${$t('个/行')}`}}</bk-radio>
          </bk-radio-group>
        </bk-form-item>
        <bk-form-item
          :label="$t('已选图表')"
          :required="true"
          :property="'graphs'"
          :error-display-type="'normal'">
          <select-chart v-model="formData.graphs"></select-chart>
        </bk-form-item>
      </bk-form>
      <div class="footer-wrap">
        <bk-button theme="primary" :disabled="!canSave" @click="handleConfirm">{{$t('确认')}}</bk-button>
        <bk-button @click="isShow = false">{{$t('取消')}}</bk-button>
      </div>
    </div>
  </bk-sideslider>
</template>

<script lang="ts">
import { Vue, Component, PropSync, Prop, Watch, Emit, Ref } from 'vue-property-decorator'
import selectChart from './select-chart.vue'
import { IContentFormData } from '../types'
/**
 * 添加内容-侧边伸缩栏
 */
@Component({
  name: 'add-content',
  components: {
    selectChart
  }
})
export default class AddContent extends Vue {
  // 侧栏展示状态
  @PropSync('show', { type: Boolean, default: false }) isShow: boolean
  // 新增/编辑状态
  @Prop({ default: 'add', type: String }) private readonly type: 'add' | 'edit'
  // 编辑传入数据
  @Prop({ type: Object }) private readonly data: IContentFormData
  @Ref('validateForm') private readonly validateFormRef: any

  // 表单展示数据
  private formData: IContentFormData = {
    contentTitle: '',
    contentDetails: '',
    rowPicturesNum: 2,
    graphs: []
  }

  private rules = {
    contentTitle: [
      { required: true, message: window.i18n.t('必填项'), trigger: 'none' }
    ],
    contentDetails: [
      { required: true, message: window.i18n.t('必填项'), trigger: 'none' }
    ],
    rowPicturesNum: [
      { required: true, message: window.i18n.t('必填项'), trigger: 'none' }
    ],
    graphs: [
      {
        validator(val) {
          return !!val.length
        },
        message: window.i18n.t('必填项'),
        trigger: 'none'
      }
    ]
  }

  get canSave() {
    const { contentTitle, rowPicturesNum, graphs } = this.formData
    return !!(contentTitle && rowPicturesNum && graphs.length)
  }

  /**
     * 数据更新操作
     * @params data 更新的数据
     */
  @Watch('data', { immediate: true, deep: true })
  dataChange(data: IContentFormData) {
    data && (this.formData = data)
  }

  /**
     * 初始化表单
     * @params show 展开状态
     */
  @Watch('isShow', { immediate: true })
  initFormData(show: boolean) {
    if (show && this.type === 'add') {
      this.formData = {
        contentTitle: '',
        contentDetails: '',
        rowPicturesNum: 2,
        graphs: []
      }
    }
  }
  /**
     * 确认操作
     */
  private handleConfirm() {
    this.validateFormRef.validate().then(() => {
      this.isShow = false
      this.updateData()
    })
  }

  /**
     * 对外派发更新数据事件
     */
  @Emit('change')
  private updateData() {
    return this.formData
  }
}
</script>

<style lang="scss" scoped>
.add-content-wrap {
  .content-main {
    position: relative;
    height: calc(100vh - 60px);
    max-height: calc(100vh - 60px);
    .form-wrap {
      padding: 24px 0;
      max-height: calc(100vh - 111px);
      overflow-y: auto;
      background-color: #fff;
      box-sizing: border-box;
      /deep/.bk-label-text {
        font-size: 12px;
      }
      /deep/.bk-form-item {
        &:not(:first-child) {
          margin-top: 18px;
        }
      }
      .radio-wrap {
        & > :not(:last-child) {
          margin-right: 56px;
        }
      }
      .bk-form-item.is-error {
        /deep/.bk-select {
          border-color: #c4c6cc;
        }
      }
      .input {
        width: 465px;
      }
    }
    .footer-wrap {
      position: absolute;
      bottom: 0;
      left: 0;
      display: flex;
      align-items: center;
      padding: 0 24px;
      width: 100%;
      height: 51px;
      background: #fafbfd;
      border: 1px solid #dcdee5;
      & > :not(:last-child) {
        margin-right: 10px;
      }
    }
  }
}
</style>
