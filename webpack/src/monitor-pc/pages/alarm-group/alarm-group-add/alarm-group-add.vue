<template>
  <div class="alarm-group-add" :class="{ 'loading': pageLoading }" v-bkloading="{ 'isLoading': pageLoading }">
    <div class="alarm-group-item">
      <div class="item-label item-required"> {{ $t('所属') }} </div>
      <div class="item-container" style="width: 503px;">
        <bk-select
          :clearable="false"
          style="width: 503px;"
          readonly
          v-model="bizList.value" :placeholder="$t('请输入所属业务')">
          <bk-option v-for="(option, index) in bizList.data"
                     :key="index"
                     :id="option.id"
                     :name="option.text">
          </bk-option>
        </bk-select>
      </div>
    </div>
    <div class="alarm-group-item" :class="{ 'verify-show': rule.name }">
      <div class="item-label item-required"> {{ $t('告警组名称') }} </div>
      <div class="item-container">
        <verify-input style="width: 503px;" :show-validate.sync="rule.name" :validator="{ content: $t('请输入告警组名称') }">
          <bk-input :maxlength="128" v-model="name" :placeholder="$t('请输入')"></bk-input>
        </verify-input>
      </div>
    </div>
    <div class="alarm-group-item item-notice-member" :class="{ 'verify-show': rule.member }">
      <div class="item-label" :class="{ 'item-required': !isAllwxwork }" style="margin-top: 4px"> {{ $t('通知对象') }} </div>
      <div class="item-container">
        <div class="over-input" v-if="isShowOverInput">
          <img src="../../../static/images/svg/spinner.svg" class="status-loading" />
        </div>
        <!-- 人员选择器 -->
        <member-selector style="width: 100%;" v-model="member.value" :group-list="defaultGroupList"></member-selector>
        <span v-if="rule.member" class="error-message"> {{ $t('请选择通知对象 ') }} </span>
      </div>
    </div>
    <div class="alarm-group-item notification" :class="{ 'verify-show': rule.noticeWay }">
      <div class="item-label item-required"> {{ $t('通知方式') }} </div>
      <div class="item-container">
        <table class="notice-table" cellspacing="0">
          <thead>
            <th>{{ $t('告警级别') }}</th>
            <th v-for="(item, index) in noticeWay"
                :key="index"
                :class="{ 'header-work-group': item.type === 'wxwork-bot' }">
              <div>
                <!-- <i class="icon-monitor icon" :class="item.icon"></i> -->
                <img class="item-img" :src="item.icon" />
                {{ item.label }}
                <i class="icon-monitor icon-remind"
                   v-if="item.type === 'wxwork-bot'"
                   v-bk-tooltips.top="$t('获取群ID方法', { name: item.name })">
                </i>
              </div>
            </th>
          </thead>
          <tbody>
            <tr v-for="(item, index) in noticeData" :key="index">
              <td><i :class="`level-mark-${index + 1}`"></i><span class="level-title">{{ item.title }}</span></td>
              <td v-for="notice in item.list" :key="notice.type">
                <div class="cell">
                  <bk-switcher v-if="notice.type === 'voice'" v-model="notice.checked" size="small" theme="primary" :ref="'voice-' + index" @change="handleShowTips(arguments[0], index)"></bk-switcher>
                  <bk-switcher v-else v-model="notice.checked" size="small" theme="primary"></bk-switcher>
                  <bk-input
                    v-model="notice.workGroupId"
                    class="wechat-work-group ml10"
                    :placeholder="$t('请输入群ID,多个ID以分号隔开')"
                    type="textarea"
                    :rows="3"
                    v-if="notice.type === 'wxwork-bot' && notice.checked">
                  </bk-input>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <span v-if="rule.noticeWay || rule.workGroupId" class="error-message error-reciver">
          {{ rule.noticeWay ? $t('每个告警级别的必须选择一种通知方式') : $t('请输入企业微信群ID')}}
        </span>
      </div>
    </div>
    <div class="alarm-group-item">
      <div class="item-label"> {{ $t('回调地址') }} </div>
      <div class="item-container">
        <bk-input v-model="webhookUrl" :placeholder="$t('请输入')"></bk-input>
        <i class="icon-monitor icon-bangzhu icon-help" @click="handleGotoLink('callbackLink')"></i>
      </div>
    </div>
    <div class="alarm-group-item desc">
      <div class="item-label"> {{ $t('说明') }} </div>
      <div class="item-container">
        <bk-input
          type="textarea"
          :maxlength="100"
          v-model="message"
          :placeholder="$t('请输入')">
        </bk-input>
      </div>
    </div>
    <div class="footer">
      <bk-button theme="primary" :title="$t('提交')" @click="handleSubmit"> {{ $t('提交') }} </bk-button>
      <bk-button theme="default" :title="$t('取消')" @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </div>
  </div>
</template>

<script>
import documentLinkMixin from '../../../mixins/documentLinkMixin'
import VerifyInput from '../../../components/verify-input/verify-input'
import { noticeGroupDetail, noticeGroupConfig } from '../../../../monitor-api/modules/notice_group'
import { mapActions } from 'vuex'
import MemberSelector from './member-selector'

export default {
  name: 'AlarmGroupAdd',
  components: {
    VerifyInput,
    MemberSelector
  },
  mixins: [documentLinkMixin],
  data() {
    return {
      id: null,
      pageLoading: true,
      bizList: {
        data: [],
        value: ''
      },
      name: '',
      member: { // 通知人员数据
        data: [],
        value: []
      },
      noticeWay: [], // 通知方式
      noticeData: [], // 通知方式勾选数据
      webhookUrl: '',
      message: '',
      rule: { // 校验规则
        name: false,
        member: false,
        noticeWay: false,
        workGroupId: false
      },
      levelMap: {
        1: this.$t('致命'),
        2: this.$t('预警'),
        3: this.$t('提醒')
      },
      iconMap: {
        weixin: 'icon-mc-weixin',
        mail: 'icon-mc-youjian',
        sms: 'icon-mc-duanxin',
        voice: 'icon-mc-dianhua',
        'wxwork-bot': 'icon-qiye-weixin'
      },
      fromRoute: '',
      popoverInstance: null,
      isShowOverInput: true,
      // 默认的告警组列表
      defaultGroupList: []
    }
  },
  computed: {
    // 通知方式全部为机器人时，通知对象可为空
    isAllwxwork() {
      return this.noticeData.every((item) => {
        const set = item.list.filter(set => set.checked)
        return set.length === 1 && set[0].type === 'wxwork-bot'
      })
    },
    // 人员列表有效的id
    effectiveMemberIdList() {
      const temp = this.member.data
      const list = temp ? temp.reduce((total, item) => total.concat(item.children), []) : []
      return list.map(item => item.id)
    }
  },
  async created() {
    this.bizList.data = this.$store.getters.bizList
    this.bizList.value = +this.$store.getters.bizId
    // 获取通知对象数据
    this.getReceiver().then((data) => {
      this.member.data = data
      const groupData = data.find(item => item.id === 'group')
      groupData.type = 'group'
      groupData.children.map(item => (item.username = item.id))
      this.defaultGroupList.push(groupData)
    })
      .finally(() => {
        this.isShowOverInput = false
      })
    this.noticeWay = await this.getNoticeWay()
    // 替换数据中对应的icon的展示样式
    this.noticeWay.forEach((way) => {
      way.icon = `data:image/png;base64,${way.icon}`
    })
    if (typeof this.$route.params.id !== 'undefined') {
      this.id = this.$route.params.id
      this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      await this.getEditData(this.id).catch(() => {
        this.$store.commit('app/SET_NAV_TITLE', this.$t(' '))
        this.pageLoading = false
      })
    } else {
      this.handleRanderNoticeWay()
    }
    this.pageLoading = false
  },
  beforeRouteEnter(to, from, next) {
    next((v) => {
      const vm = v
      vm.fromRoute = from.name
    })
  },
  methods: {
    ...mapActions('alarm-group', ['noticeGroupDetail', 'getNoticeWay', 'getReceiver']),
    // 渲染通知方式表
    handleRanderNoticeWay() {
      const tableData = []
      // 渲染初始表格
      Object.keys(this.levelMap).forEach((key, index) => {
        const list = this.noticeWay.map((set) => {
          if (set.type === 'wxwork-bot') {
            return { type: set.type, checked: false, workGroupId: '' }
          }
          return { type: set.type, checked: false }
        })
        tableData.push({
          list,
          level: key,
          title: this.levelMap[index + 1]
        })
      })
      this.noticeData = tableData.reverse()
    },
    // 获取已勾选的通知人员数据
    handleNoticeReceiver() {
      const result = []
      const { data } = this.member
      this.member.value.forEach((id) => {
        data.forEach((item) => {
          item.children.forEach((set) => {
            if (id === set.id) {
              result.push(set)
            }
          })
        })
      })
      return result
    },
    // 获取通知方式的数据
    handleNoticeWayData() {
      const params = {
        1: [],
        2: [],
        3: []
      }
      this.noticeData.forEach((item) => {
        item.list.forEach((way) => {
          if (way.checked) {
            params[item.level].push(way.type)
          }
        })
      })
      return params
    },
    // 获取企业微信群通知方式信息
    handleGetWechatWorkGroupData() {
      const params = {}
      this.noticeData.forEach((item) => {
        // 企业微信群实现方式不一样，有单独的字段
        item.list.filter(set => set.type === 'wxwork-bot').forEach((way) => {
          if (way.checked) {
            params[item.level] = way.workGroupId
          }
        })
      })
      return params
    },
    // 规则校验
    handleValidate() {
      this.rule.name = !this.name
      this.rule.member = !this.member.value.length && !this.isAllwxwork
      const resList = this.noticeData.map(item => item.list.some(way => way.checked))
      this.rule.noticeWay = !(resList.every(bol => bol))
      // 企业微信群ID必填
      this.rule.workGroupId = this.noticeData.some((item) => {
        const way = item.list.find(way => way.type === 'wxwork-bot')
        return way?.checked && !way.workGroupId
      })
      return this.rule.name || this.rule.member || this.rule.noticeWay || this.rule.workGroupId
    },
    // 新增/修改告警组  提交按钮
    async handleSubmit() {
      if (this.handleValidate()) {
        return
      }
      this.pageLoading = true
      const params = {
        bk_biz_id: this.bizList.value,
        name: this.name,
        message: this.message,
        notice_way: this.handleNoticeWayData(),
        notice_receiver: this.handleNoticeReceiver(),
        webhook_url: this.webhookUrl
      }
      if (this.id) {
        params.id = this.id
      }
      const wechatWorkGroup = this.handleGetWechatWorkGroupData()
      if (Object.keys(wechatWorkGroup).length) {
        params.wxwork_group = wechatWorkGroup
      }
      const data = await noticeGroupConfig(params).catch(() => false)
      if (data) {
        if (this.fromRoute === 'alarm-group') {
          this.$router.push({ name: 'alarm-group' })
        } else if (this.fromRoute === 'strategy-config-add' || this.fromRoute === 'strategy-config-edit') {
          this.$router.replace({
            name: this.fromRoute,
            params: {
              alarmGroupId: data.id,
              id: this.$route.params.strategyId || '0'
            }
          })
        } else {
          this.$router.back()
        }
        this.$bkMessage({ theme: 'success', message: this.id ? this.$t('编辑成功') : this.$t('创建成功') })
      }
      this.pageLoading = false
    },
    // 取消事件
    handleCancel() {
      this.$router.back()
    },
    // 编辑 获取告警组详情
    getEditData(id) {
      return noticeGroupDetail({ id }).then((data) => {
        this.$store.commit('app/SET_NAV_TITLE', `${this.$t('编辑')} - #${id} ${data.name}`)
        this.bizList.value = data.bk_biz_id
        this.name = data.name
        this.message = data.message
        this.webhookUrl = data.webhook_url
        this.member.value = data.notice_receiver.map(item => item.id)
        // 批量导入时，告警组为空
        if (Object.keys(data.notice_way).length) {
          const noticeWay = {
            1: data.notice_way['1'] || [],
            2: data.notice_way['2'] || [],
            3: data.notice_way['3'] || []
          }
          const tableData = []
          Object.keys(noticeWay).forEach((key, index) => {
            // 渲染初始表格
            const list = this.noticeWay.map((set) => {
              if (set.type === 'wxwork-bot') {
                return { type: set.type, checked: false, workGroupId: '' }
              }
              return { type: set.type, checked: false }
            })
            // 对应勾选
            noticeWay[key].forEach((notice) => {
              const listItem = list.find(set => set.type === notice)
              listItem && (listItem.checked = true)
            })
            // 企业微信群勾选项
            if (noticeWay[key].includes('wxwork-bot') && data.wxwork_group && data.wxwork_group[key]) {
              const listItem = list.find(set => set.type === 'wxwork-bot')
              if (listItem) {
                listItem.checked = true
                listItem.workGroupId = data.wxwork_group[key]
              }
            }
            tableData.push({
              list,
              level: key,
              title: this.levelMap[index + 1]
            })
          })
          this.noticeData = tableData.reverse()
        } else {
          this.handleRanderNoticeWay()
        }
      })
    },
    handleShowTips(bool, index) {
      // 当打开语音按钮进行提示
      if (!bool) return
      const switcherEl = this.$refs[`voice-${index}`][0].$el
      const text = this.$t('电话按通知对象顺序依次拨打,用户组里无法保证顺序')
      this.handlePopoverShow(switcherEl, text)
    },
    // 提示列表显示方法
    handlePopoverShow(component, tipsText) {
      this.handleDestroyPopover()
      this.popoverInstance = this.$bkPopover(component, {
        content: tipsText,
        arrow: true,
        flip: false,
        flipBehavior: 'bottom',
        trigger: 'manul',
        placement: 'top',
        duration: [200, 0]
      })
      // 显示
      this.popoverInstance.show(100)
    },
    // 隐藏
    handleDestroyPopover() {
      if (this.popoverInstance) {
        this.popoverInstance.hide(0)
        this.popoverInstance.destroy && this.popoverInstance.destroy()
        this.popoverInstance = null
      }
    },
    // 处理批量粘贴输入通知人员
    handelPasteFn(v) {
      if (!v || !v.length) return []
      const str = v.toString().trim()
        .replace(/[;\s,]\s*/g, ';')
      const pasteList = str.toString().split(';')
      const list = pasteList.map(item => item.replace(/\([\s\S]*\)$/, ''))
      const effectiveIds = list.filter(item => this.effectiveMemberIdList.includes(item)
                    && !this.member.value.includes(item))
      this.member.value = this.member.value.concat(effectiveIds)
      return []
    }
  }
}
</script>

<style lang="scss" scoped>
$levelColors: #ffde3a #ff9c01 #ea3636;

.alarm-group-add {
  padding: 20px 135px 0 24px;
  &.loading {
    height: calc(100vh - 100px);
  }
  .verify-show {
    /* stylelint-disable-next-line declaration-no-important */
    margin-bottom: 32px !important;
  }
  .item-notice-member {
    /* stylelint-disable-next-line declaration-no-important */
    align-items: flex-start !important;
  }
  .alarm-group-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    min-height: 32px;
    margin-bottom: 20px;
    &.notification {
      align-items: flex-start;
    }
    &.desc {
      align-items: flex-start;
    }
    .item-label {
      flex: 0 0 76px;
      margin-right: 20px;
      text-align: right;
      position: relative;
      color: #63656e;
      font-size: 14px;
      &.item-required:after {
        content: "*";
        color: red;
        position: absolute;
        top: 3px;
        right: -10px;
        font-size: 12px;
      }
    }
    .item-container {
      position: relative;
      flex: 1;
      .over-input {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        height: 32px;
        width: 100%;
        z-index: 2;
        top: 0;
        position: absolute;
        &:hover {
          cursor: no-drop;
        }
        .status-loading {
          height: 16px;
          width: 16px;
        }
      }
      .notice-table {
        width: 100%;
        border: 1px solid #dcdee5;
        border-bottom: 0;
        color: #63656e;
        .icon {
          font-size: 16px;
          margin-right: 6px;
        }
        .item-img {
          width: 16px;
          height: 16px;
          filter: grayscale(100%);
          margin-right: 6px;
        }
        .icon-remind {
          font-size: 14px;
          position: relative;
          top: 1px;
          margin-left: 6px;
        }
        th {
          padding: 0;
          margin: 0;
          height: 40px;
          font-weight: 400;
          border-right: 1px solid #dcdee5;
          border-bottom: 1px solid #dcdee5;
          background: #fafbfd;
          &:first-child {
            width: 97px;
          }
          &:last-child {
            border-right: 0;
          }
          &.header-work-group {
            width: 290px;
          }
          div {
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
          }
        }
        td {
          padding: 0;
          margin: 0;
          text-align: center;
          border-right: 1px solid #dcdee5;
          border-bottom: 1px solid #dcdee5;
          background-color: #fff;

          @for $i from 1 through 3 {
            .level-mark-#{$i} {
              width: 3px;
              height: 12px;
              background: nth($levelColors, $i );
              display: inline-block;
              margin-right: 8px;
              vertical-align: middle;
            }
          }
          .level-title {
            font-weight: bold;
            color: #63656e;
            vertical-align: middle;
          }
          &:last-child {
            border-right: 0;
          }
          .cell {
            min-height: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px 0;
          }
          .wechat-work-group {
            width: 200px;
          }
        }
      }
      .error-message {
        position: absolute;
        top: 36px;
        color: #f56c6c;
        font-size: 12px;
        line-height: 1;
        &.error-reciver {
          position: relative;
          top: 2px;
        }
      }
      /deep/ .bk-textarea-wrapper .bk-form-textarea.textarea-maxlength {
        margin-bottom: 0px;
      }
      /deep/ .bk-form-textarea {
        min-height: 60px;
      }
    }
    .icon-help {
      position: absolute;
      right: -24px;
      top: 8px;
      font-size: 16px;
      margin-left: 8px;
      color: #979ba5;
      cursor: pointer;
      &:hover {
        color: #3a84ff;
      }
    }
  }
  .footer {
    font-size: 0;
    padding-left: 90px;
    .bk-button {
      font-size: 14px;
      margin-right: 10px;
    }
  }
  /deep/ .bk-select {
    background: #fff;
    &.is-disabled {
      background: #fafbfd;
    }
  }
}
</style>
