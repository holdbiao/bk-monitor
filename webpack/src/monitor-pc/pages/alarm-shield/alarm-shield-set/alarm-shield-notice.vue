<template>
  <div class="alarm-shield-notice" :class="{ 'is-show': isShow }">
    <div class="notice-btn">
      <bk-switcher v-model="isShow" size="small" theme="primary" style="margin-right: 10px" @change="handleChangeShow"></bk-switcher> {{ $t('通知设置') }} </div>
    <div v-if="isShow" class="notice-config">
      <div class="notice-item notice-input" :class="{ 'verify-show': rule.isMemberValue }">
        <div class="notice-item-label notice-input-label"> {{ $t('通知对象') }} </div>
        <verify-input :show-validate.sync="rule.isMemberValue" :validator="{ content: $t('请至少添加一个通知对象') }">
          <div class="notice-item-content">
            <bk-tag-input
              class="bk-member-selector" :placeholder="$t('请选择通知对象')"
              v-model="member.value"
              :save-key="'id'"
              :display-key="'display_name'"
              :search-key="'id'"
              :use-group="true"
              :list="member.data"
              :tag-tpl="renderMemberTag"
              :tpl="renderMerberList"
              :trigger="'focus'">
            </bk-tag-input>
          </div>
        </verify-input>
      </div>
      <div class="notice-item" :class="{ 'verify-show': rule.isNotificationMethod }">
        <div class="notice-item-label"> {{ $t('通知方式') }} </div>
        <verify-input :show-validate.sync="rule.isNotificationMethod" :validator="{ content: $t('请至少选择一种通知方式') }">
          <div class="notice-item-content">
            <bk-checkbox-group v-model="notificationMethod">
              <bk-checkbox v-for="(item, index) in setWay" :key="index" class="checkbox-group" :value="item.type">{{item.label}}</bk-checkbox>
            </bk-checkbox-group>
          </div>
        </verify-input>
      </div>
      <div class="notice-item" style="margin-bottom: 30px">
        <div class="notice-item-label"> {{ $t('通知时间') }} </div>
        <verify-input :show-validate.sync="rule.isNoticeNumber" :validator="{ content: $t('通知时间只能为整数') }">
          <div class="notice-item-content noitce-number">
            <span class="mr-10"> {{ $t('屏蔽开始/结束前') }} </span>
            <div class="input-demo mr-10">
              <bk-input type="number" :max="1440" :min="1" v-model="noticeNumber" @change="handleTriggerNumber" placeholder="0"></bk-input>
            </div>
            <span> {{ $t('分钟发送通知') }} </span>
          </div>
        </verify-input>
      </div>
    </div>
  </div>
</template>

<script>
import VerifyInput from '../../../components/verify-input/verify-input'
import { getNoticeWay, getReceiver } from '../../../../monitor-api/modules/notice_group'
import { memberSelectorMixin } from '../../../common/mixins'
export default {
  name: 'alarm-shield-notice',
  components: {
    VerifyInput
  },
  mixins: [memberSelectorMixin],
  data() {
    return {
      bizId: '',
      isShow: false,
      noticeNumber: 5,
      notificationMethod: [],
      member: {
        data: [],
        value: [],
        noticeWayError: false
      },
      setWay: [],
      rule: {
        isNotificationMethod: false,
        isMemberValue: false,
        isNoticeNumber: false
      }
    }
  },
  created() {
    this.bizId = this.$store.getters.bizId
    this.getNoticeData()
  },
  methods: {
    handleChangeShow(v) {
      this.$emit('change-show', v)
    },
    handleSelectNoticeWay() {
      this.member.noticeWayError = !this.member.value.length
    },
    handleTriggerNumber(v) {
      if ((`${v}`).includes('.')) {
        this.noticeNumber = Number(v.replace(/\./gi, ''))
      }
    },
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
    getNoticeData() {
      const receiver = getReceiver({ bk_biz_id: this.bizId })
      const noticeWay = getNoticeWay({ bk_biz_id: this.bizId })
      Promise.all([receiver, noticeWay]).then((data) => {
        const [member, setWay] = data
        this.member.data = member
        this.setWay = setWay
      })
        .catch(() => {})
    },
    getNoticeConfig() {
      const { rule } = this
      const noticeNumberRule = /^\d+$/
      if (this.isShow) {
        if (!this.notificationMethod.length || !this.member.value.length || !noticeNumberRule.test(this.noticeNumber)) {
          rule.isNotificationMethod = !this.notificationMethod.length
          rule.isMemberValue = !this.member.value.length
          rule.isNoticeNumber = !noticeNumberRule.test(this.noticeNumber)
          return false
        }
        return {
          notice_receiver: this.handleNoticeReceiver(),
          notice_way: this.notificationMethod,
          notice_time: this.noticeNumber
        }
      }
      return true
    },
    setNoticeData(data) {
      this.isShow = true
      this.member.value = data.member.value
      this.notificationMethod = data.notificationMethod
      this.noticeNumber = data.noticeNumber
    }
  }
}
</script>

<style lang="scss" scoped>
    .alarm-shield-notice {
      font-size: 14px;
      color: #63656e;
      .is-show {
        margin-bottom: 30px;
      }
      .notice-btn {
        display: flex;
        align-items: center;
        margin: 0 0 18px 80px;
      }
      .notice-config {
        .verify-show {
          /* stylelint-disable-next-line declaration-no-important */
          margin-bottom: 32px !important;
        }
        .notice-item {
          display: flex;
          align-items: center;
          margin-bottom: 20px;
          &-label {
            min-width: 56px;
            text-align: right;
            margin-right: 24px;
            position: relative;
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
            .mr-10 {
              margin-right: 10px;
            }
          }
          .noitce-number {
            display: flex;
            align-items: center;
            .bk-form-control {
              width: 68px;
            }
          }
        }
        .notice-input {
          align-items: flex-start;
          &-label {
            margin-top: 6px;
          }
        }
      }
      .bk-member-selector {
        width: 834px;
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
      margin-right: 8px;
    }
</style>
