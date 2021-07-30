<template>
  <div class="subscriptions-set-wrap" v-bkloading="{ isLoading }">
    <!-- 基本信息 -->
    <div class="content-wrap">
      <div class="title-wrap">
        <span class="title">{{$t('基本信息')}}</span>
      </div>
      <div class="content-main">
        <bk-form
          class="base-info-form"
          :rules="rules"
          :model="formData"
          ref="validateForm">
          <bk-form-item
            :label="$t('邮件标题')"
            :required="true"
            :property="'mailTitle'"
            :error-display-type="'normal'">
            <bk-input
              class="input"
              :placeholder="$t('请输入邮件标题')"
              v-model="formData.mailTitle"></bk-input>
          </bk-form-item>
          <bk-form-item
            :label="$t('接收人')"
            :required="true"
            :property="'receivers'"
            :error-display-type="'normal'">
            <div class="form-item-row">
              <!-- 人员选择器 -->
              <member-selector style="width: 465px; height: 32px;" v-model="formData.receivers" :group-list="memberGroupListFilter"></member-selector>
              <i
                class="icon-monitor icon-tips"
                v-bk-tooltips="{ content: $t('主动添加和订阅的生效人员'), showOnInit: false, duration: 200, placements: ['top'] }">
              </i>
              <div class="receiver-btn" ref="receiverTarget" @click="handleShowReceiver">
                <i class="icon-monitor icon-audit"></i>
                <span class="text">{{$t('订阅人员列表')}}</span>
              </div>
            </div>
          </bk-form-item>
          <bk-form-item
            :label="$t('管理员')"
            :required="true"
            :property="'managers'"
            :error-display-type="'normal'">
            <div class="form-item-row">
              <!-- 人员选择器 -->
              <member-selector style="width: 465px; height: 32px;" v-model="formData.managers" :group-list="memberGroupListFilter"></member-selector>
              <i
                class="icon-monitor icon-tips"
                v-bk-tooltips="{ content: $t('可以对本订阅内容进行修改的人员'), showOnInit: false, duration: 200, placements: ['top'] }">
              </i>
            </div>
          </bk-form-item>
          <bk-form-item :label="$t('发送频率')" :required="true">
            <time-period v-model="formData.frequency"></time-period>
          </bk-form-item>
          <!-- 订阅内容的校验替身 -->
          <bk-form-item
            ref="reportContentsFormItem"
            v-show="false"
            :required="true"
            :property="'reportContents'"
            :error-display-type="'normal'">
          </bk-form-item>
        </bk-form>
      </div>
    </div>
    <!-- 订阅内容 -->
    <div class="content-wrap mt24">
      <div class="title-wrap">
        <span class="title">{{$t('订阅内容')}}</span>
        <span class="add-btn" @click="handleShowContent('add')"><span class="icon-monitor icon-mc-plus-fill" />{{$t('添加内容')}}</span>
      </div>
      <div class="content-main">
        <bk-table
          class="drag-table-wrap"
          style="margin-top: 16px;"
          :key="tableKey"
          :data="formData.reportContents">
          <bk-table-column :width="52">
            <template>
              <span class="icon-drag"></span>
            </template>
          </bk-table-column>
          <bk-table-column
            v-for="column in tableColumnsMap"
            :key="column.key"
            :label="column.label"
            :prop="column.key"
            :width="column.width"
            :formatter="formatterColumn">
          </bk-table-column>
          <bk-table-column :label="$t('操作')" :width="150">
            <template slot-scope="props">
              <bk-button class="mr10" theme="primary" text @click="handleShowContent('edit', props.row, props.$index)">{{$t('编辑')}}</bk-button>
              <bk-button class="mr10" theme="primary" text @click="handleDelContent(props.$index)">{{$t('删除')}}</bk-button>
            </template>
          </bk-table-column>
        </bk-table>
        <div class="errors-tips" v-if="errors && errors.field === 'reportContents'">{{errors.content}}</div>
      </div>
    </div>
    <div class="footer-wrap">
      <bk-button theme="primary" @click="handleSave" :loading="saveLoading">{{$t('保存')}}</bk-button>
      <bk-button
        v-bk-tooltips="{
          content: $t('往当前用户发送一封测试邮件'),
          placements: ['top']
        }"
        @click="handleTest"
        :loading="testLoading">{{$t('测试')}}</bk-button>
      <bk-button @click="handleCancel">{{$t('取消')}}</bk-button>
    </div>
    <!-- 侧栏-添加内容 -->
    <add-content
      :show.sync="showAddContent"
      :data="curEditContentData"
      :type="setType"
      @change="handleContentChange">
    </add-content>
    <!-- 测试提示 -->
    <monitor-dialog
      :need-footer="false"
      :need-header="false"
      :value.sync="showTips">
      <div class="tips-content-wrap">
        <div class="tips-title-wrap">
          <span :class="['icon-monitor', tipsContent[tipsType].icon]"></span>
          <span class="tips-title">{{tipsContent[tipsType].title}}</span>
        </div>
        <div class="tips-content">{{tipsContent[tipsType].content}}</div>
      </div>
    </monitor-dialog>
    <!-- 接收人列表浮层 -->
    <receiver-list
      :show.sync="receiverList.show"
      :target="receiverTargetRef"
      :table-data="receiverListTableData"
      placement="bottom-start"
      :need-handle="true"
      :loading="receiverListLoading"
      @on-receiver="handleOnReciver">
    </receiver-list>
  </div>
</template>

<script lang="ts">
import { Component, Mixins, Ref, Prop } from 'vue-property-decorator'
import timePeriod from './components/time-period.vue'
import addContent from './components/add-content.vue'
import { IContentFormData, ITableColumnItem } from './types'
import { deepClone, transformDataKey } from '../../../monitor-common/utils/utils'
import MonitorDialog from '../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import BkUserSelector from '@blueking/user-selector'
import { memberSelectorMixin } from '../../common/mixins'
// import { getReceiver } from '../../../monitor-api/modules/notice_group'
import { reportCreateOrUpdate, reportTest, reportContent, groupList } from '../../../monitor-api/modules/report'
import { bkForm, bkFormItem } from 'bk-magic-vue'
import memberSelector from '../alarm-group/alarm-group-add/member-selector.vue'
import Sortable from 'sortablejs'
import MonitorVue from '../../types/index'
import ReceiverList from './components/receiver-list.vue'
/**
 * 邮件订阅新建/编辑页
 */
@Component({
  name: 'subscriptions-set',
  components: {
    timePeriod,
    addContent,
    MonitorDialog,
    BkUserSelector,
    memberSelector,
    ReceiverList
  }
})
export default class SubscriptionsSet extends Mixins(memberSelectorMixin)<MonitorVue> {
  @Prop({ default: '', type: [Number, String] }) readonly id: number | string
  @Ref('validateForm') private readonly validateFormRef: bkForm
  @Ref('reportContentsFormItem') private reportContentsFormItemRef: bkFormItem
  @Ref('receiverTarget') private receiverTargetRef: Element


  private isLoading = false
  private saveLoading = false
  private testLoading = false
  // 侧栏展示状态
  private showAddContent = false
  // 侧栏新增/编辑状态
  private setType: 'add' | 'edit' = 'add'
  private testVal: any = ''

  private formData: any = {
    mailTitle: '',
    receivers: [],
    managers: [],
    frequency: null,
    reportContents: []
  }
  private sortEndReportContents = []
  private curFromIndex = 0

  private rules: any = {
    mailTitle: [{ required: true, message: window.i18n.t('必填项'), trigger: 'none' }],
    receivers: [{ validator(val) {
      return !!val.length
    }, message: window.i18n.t('必填项'), trigger: 'none' }],
    managers: [{ validator(val) {
      return !!val.length
    }, message: window.i18n.t('必填项'), trigger: 'none' }],
    reportContents: [{ validator(val) {
      return !!val.length
    }, message: window.i18n.t('必填项'), trigger: 'none' }]
  }
  private errors: any = null
  // 表格列数据
  private tableColumnsMap: ITableColumnItem[] = [
    { label: window.i18n.t('子标题'), key: 'contentTitle' },
    { label: window.i18n.t('图表数量'), key: 'graphs', width: 150 },
    { label: window.i18n.t('布局'), key: 'rowPicturesNum', width: 150 },
    { label: window.i18n.t('说明'), key: 'contentDetails' }
  ]
  private tableKey = 'tableKey'
  // 当前编辑的数据
  private curEditContentData: IContentFormData = null
  // 当前编辑数据索引
  private curEditContentIndex: number = null

  // 测试提示数据
  private showTips = false
  private tipsType: 'success' | 'fail' = 'fail'
  private tipsContent: any = {
    success: {
      icon: 'icon-check-circle',
      title: window.i18n.t('测试邮件发送成功'),
      content: window.i18n.t('邮件任务已生成，请一分钟后到邮箱查看')
    },
    fail: {
      icon: 'icon-mc-close-fill',
      title: window.i18n.t('测试邮件发送失败'),
      content: window.i18n.t('您好，订阅邮件模板发送失败，请稍后重试！')
    }
  }

  // 人员数据
  private memberList: any = []
  // 接收人数据
  private receiverList: any = {
    show: false
  }
  // 接收用户数据
  private receiversUser: any = []
  // 所有receiver数据
  private receivers: any = []
  private receiverListLoading = false

  get receiverListTableData() {
    const groupList = this.memberList.find(item => item.id === 'group')?.children || []
    let list = []
    if (this.id) { // 编辑
      const receivers = []
      this.formData.receivers.forEach((item) => {
        const res = groupList.find(set => item === set.id)
        res ? receivers.push(...res.children) : receivers.push(item)
      })
      receivers.forEach((item) => {
        const res = this.receiversUser.find(set => set.id === item)
        let temp = {}
        if (res) {
          const { createTime, isEnabled, lastSendTime } = res
          temp = {
            name: item,
            createTime,
            isEnabled,
            lastSendTime
          }
        } else {
          temp = {
            name: item,
            createTime: '',
            isEnabled: null,
            lastSendTime: ''
          }
        }
        list.push(temp)
      })
    } else {
      const temp = []
      this.formData.receivers.forEach((item) => {
        const res = groupList.find(set => item === set.id)
        if (res) {
          temp.push(...res.children)
        } else {
          temp.push(item)
        }
      })
      list = temp.map(item => ({
        name: item,
        createTime: '',
        isEnabled: null,
        lastSendTime: ''
      }))
    }
    return list
  }

  get isSuperUser() {
    return this.$store.getters.isSuperUser
  }

  // 人员数据筛选
  get memberGroupListFilter() {
    if (this.isSuperUser) {
      const temp = deepClone(this.memberList)
      const list = temp.filter(item => item.id === 'group')
      list.forEach((item) => {
        item.children = item.children.map((group) => {
          group.username = group.id
          delete group.children
          return group
        })
      })
      return list
    }
    return []
  }

  created() {
    if (this.id) this.getEditInfo(this.id)
    // 获取通知对象数据
    // getReceiver({ bk_biz_id: 0 }).then((data) => {
    //   this.memberList = data
    // })
    groupList().then((data) => {
      this.memberList = [{
        id: 'group',
        display_name: '用户组',
        children: data
      }]
    })
  }

  mounted() {
    this.rowDrop()
  }

  /**
   * 编辑信息
   */
  private getEditInfo(id) {
    this.isLoading = true
    reportContent({ report_item_id: id }).then((res) => {
      const data = transformDataKey(res)
      this.formData.frequency = data.frequency
      this.formData.mailTitle = data.mailTitle
      this.formData.managers = data.managers.filter(item => !item.group).map(item => item.id)
      this.receivers = data.receivers
      this.formData.reportContents = data.contents
      this.formData.reportItemId = data.id
      this.getReceiverId(data.receivers)
      this.formData.reportContents.forEach((content) => {
        content.graphs = content.graphName.map(item => ({
          id: item.graphId,
          name: item.graphName
        }))
      })
    })
      .finally(() => this.isLoading = false)
  }

  // 更新本地接收人数据
  private getReceiverId(receivers) {
    this.receivers = receivers
    this.receiversUser = receivers.filter(item => item.type === 'user')
    this.formData.receivers = receivers.filter(item => !item.group)
      .filter(item => item.isEnabled)
      .map(item => item.id)
  }

  /**
     * 表格数据格式化
     * @params column 列数据column
     * @params cellValue 值
     */
  private formatterColumn(row, column, cellValue) {
    if (column.property === 'layout') return cellValue + this.$t('个/行')
    if (column.property === 'graphs') return cellValue.length
    return cellValue
  }

  /**
     * 展开内容编辑侧栏
     * @params type 新增/编辑状态
     * @params row 行数据
     * @params index 数据索引
     */
  private handleShowContent(type: 'add' | 'edit', row?: any, index?: number) {
    this.setType = type
    if (type === 'edit') {
      this.curEditContentIndex = index
      const temp = deepClone(row)
      this.curEditContentData = temp
    } else if (type === 'add') {
      this.curEditContentData = null
    }
    this.showAddContent = true
  }

  /**
     * 内容值更新
     * @params data 编辑/新增更新的值
     */
  private handleContentChange(data: IContentFormData) {
    // 清除订阅内容的错误信息
    this.reportContentsFormItemRef.handlerFocus()
    const temp = deepClone(data)
    if (this.setType === 'edit') {
      this.formData.reportContents.splice(this.curEditContentIndex, 1, temp)
    } else if (this.setType === 'add') {
      this.formData.reportContents.push(temp)
    }
  }

  /**
     * 删除订阅内容
     * @params index 数据索引
     */
  private handleDelContent(index: number) {
    this.formData.reportContents.splice(index, 1)
  }

  /**
   * 处理新增编辑接收人参数
   */
  private getReceiversParams(receivers) {
    let res = []
    const groupList = this.memberList.find(item => item.id === 'group').children
    res = receivers.map((item) => {
      const flag = groupList.find(set => set.id === item)
      return {
        id: item,
        is_enabled: true,
        type: flag ? 'group' : 'user'
      }
    })
    this.receivers.forEach((item) => {
      if (item.group) {
        res.push({
          id: item.id,
          group: item.group,
          is_enabled: item.isEnabled,
          type: item.type
        })
      }
    })
    return res
  }

  /**
     * 保存配置 新建/编辑
     */
  private handleSave() {
    this.saveLoading = true
    this.validateFormRef.validate().then(() => {
      this.errors = null
      const groupList = this.memberList.find(item => item.id === 'group').children
      let params = deepClone(this.formData)
      params.receivers = this.getReceiversParams(params.receivers)
      params.managers = params.managers.map((item) => {
        const flag = groupList.find(set => set.id === item)
        return {
          id: item,
          type: flag ? 'group' : 'user'
        }
      })
      params.reportContents.forEach((content) => {
        content.graphs = content.graphs.map(chart => chart.id)
      })
      params = transformDataKey(params, true)
      reportCreateOrUpdate(params).then(() => {
        this.$router.push({
          name: 'email-subscriptions'
        })
      })
        .finally(() => {
          this.saveLoading = false
        })
    })
      .catch((err) => {
        console.log(err)
        this.errors = err
        this.saveLoading = false
      })
  }

  /**
   * 测试邮件
   */
  private handleTest() {
    this.testLoading = true
    this.validateFormRef.validate().then(() => {
      const { reportContents, mailTitle, receivers, frequency } = deepClone(this.formData)
      // const groupList = this.memberList.find(item => item.id === 'group').children
      let params = {
        mail_title: mailTitle,
        receivers,
        report_contents: reportContents,
        frequency
      }
      params.receivers = this.getReceiversParams(params.receivers)
      params.report_contents.forEach((content) => {
        content.graphs = content.graphs.map(chart => chart.id)
      })
      params = transformDataKey(params, true)
      reportTest(params).then(() => {
        this.tipsType = 'success'
      })
        .catch(() => {
          this.tipsType = 'fail'
        })
        .finally(() => {
          this.showTips = true
          this.testLoading = false
        })
    })
      .catch((err) => {
        this.errors = err
        this.testLoading = false
      })
  }

  /**
   * 取消返回上一页
   */
  private handleCancel() {
    this.$router.go(-1)
  }

  // 恢复订阅
  private handleOnReciver(row) {
    if (!this.id) return
    this.receiverListLoading = true
    const receivers = deepClone(this.receivers)
    receivers.forEach(item => item.id === row.name && (item.isEnabled = !item.isEnabled))
    let params = {
      reportItemId: this.id,
      receivers
    }
    params = transformDataKey(params, true)
    reportCreateOrUpdate(params).then(() => {
      this.getReceiverId(receivers)
      this.$bkMessage({ message: this.$t('订阅成功'), theme: 'success' })
    })
      .finally(() => this.receiverListLoading = false)
  }

  /**
     * 表格行拖拽
     */
  private rowDrop() {
    const tbody = document.querySelector('.drag-table-wrap .bk-table-body-wrapper tbody')
    Sortable.create(tbody, {
      onStart: ({ oldIndex: from }) => {
        this.curFromIndex = from
      },
      onEnd: ({ newIndex: to, oldIndex: from }) => {
        if (to === from) return
        this.formData.reportContents = deepClone(this.sortEndReportContents)
        this.tableKey = String(new Date())
        this.sortEndReportContents = []
        this.$nextTick(() => {
          this.rowDrop()
        })
      },
      onChange: ({ newIndex: to }) => {
        const from = this.curFromIndex
        this.sortEndReportContents = this.sortEndReportContents.length
          ? this.sortEndReportContents : deepClone(this.formData.reportContents)
        const temp = this.sortEndReportContents[to]
        this.sortEndReportContents[to] = this.sortEndReportContents[from]
        this.sortEndReportContents[from] = temp
        this.curFromIndex = to
      }
    })
  }

  private handleShowReceiver() {
    this.receiverList.show = true
  }
}
</script>

<style lang="scss" scoped>
.subscriptions-set-wrap {
  padding-bottom: 20px;
  .content-wrap {
    padding: 22px 37px;
    border-radius: 2px;
    background-color: #fff;
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, .05);
    .title-wrap {
      display: flex;
      align-items: center;
      .title {
        font-size: 12px;
        font-weight: 700;
        color: #63656e;
        line-height: 16px;
      }
      .add-btn {
        display: flex;
        align-items: center;
        color: #3a84ff;
        margin-left: 34px;
        cursor: pointer;
        .icon-mc-plus-fill {
          font-size: 16px;
          margin-right: 4px;
        }
      }
    }
    .base-info-form {
      margin-top: 26px;
      /deep/.bk-label-text {
        font-size: 12px;
      }
      /deep/.bk-form-item {
        &:not(:first-child) {
          margin-top: 18px;
        }
      }
      .input {
        width: 465px;
      }
      .bk-member-selector {
        width: 465px;
        min-height: 32px;
        .bk-selector-member {
          padding: 0 10px;
          display: flex;
          align-items: center;
        }
        .avatar {
          width: 22px;
          height: 22px;
          border: 1px solid #c4c6cc;
          border-radius: 50%;
        }
        /deep/ .tag-list {
          > li {
            height: 22px;
          }
          .no-img {
            color: #979ba5;
            font-size: 22px;
            background: #fafbfd;
            border-radius: 16px;
            margin-right: 5px;
          }
          .key-node {
            /* stylelint-disable-next-line declaration-no-important */
            border: 0 !important;

            /* stylelint-disable-next-line declaration-no-important */
            background: none !important;
            .tag {
              height: 22px;
              background: none;
              display: flex;
              align-items: center;
              .avatar {
                width: 22px;
                height: 22px;
                float: left;
                margin-right: 8px;
                border-radius: 50%;
                vertical-align: middle;
                border: 1px solid #c4c6cc;
              }
            }
          }
        }
      }
      .form-item-row {
        display: flex;
        align-items: center;
        .icon-tips {
          margin-left: 8px;
          font-size: 16px;
          color: #63656e;
          &:hover {
            color: #3a84ff;
          }
        }
        .receiver-btn {
          display: flex;
          align-items: center;
          height: 16px;
          font-size: 0;
          margin-left: 18px;
          cursor: pointer;
          color: #3a84ff;
          .icon-monitor {
            font-size: 14px;
          }
          .text {
            font-size: 12px;
            margin-left: 5px;
          }
        }
      }
    }
    .content-main {
      .drag-table-wrap {
        /deep/.sortable-chosen {
          td {
            background-color: #eef5ff;
          }
        }
      }
      .icon-drag {
        display: inline-block;
        height: 14px;
        position: relative;
        cursor: move;
        &::after {
          content: " ";
          height: 14px;
          width: 2px;
          position: absolute;
          top: 0;
          border-left: 2px dotted #979ba5;
          border-right: 2px dotted #979ba5;
        }
      }
      .errors-tips {
        font-size: 12px;
        color: #ea3636;
        line-height: 18px;
        margin: 2px 0 0;
      }
    }
  }
  .mt24 {
    margin-top: 24px;
  }
  .footer-wrap {
    display: flex;
    margin-top: 24px;
    & > :not(:last-child) {
      margin-right: 10px;
    }
  }
  .tips-content-wrap {
    padding-top: 3px;
    padding-bottom: 23px;
    .tips-title-wrap {
      font-size: 0;
      margin-bottom: 7px;
      .icon-monitor {
        font-size: 18px;
        margin-right: 7px;
      }
      .icon-check-circle {
        color: #2dcb56;
      }
      .icon-mc-close-fill {
        color: #ea3636;
      }
      .tips-title {
        height: 21px;
        font-size: 16px;
        font-weight: 700;
        text-align: left;
        color: #313238;
        line-height: 21px;
      }
    }
    .tips-content {
      font-size: 14px;
      text-align: left;
      color: #63656e;
      line-height: 19px;
      padding-left: 25px;
    }
  }
  /deep/.monitor-dialog {
    min-height: 112px;
  }
}
.only-notice {
  display: flex;
  align-items: center;
  padding-left: 10px;
}
.only-img {
  color: #979ba5;
  font-size: 22px;
  background: #fafbfd;
  border-radius: 16px;
  margin-right: 5px;
}

</style>
