<template>
  <bk-sideslider
    :width="780"
    :quick-close="true"
    :is-show.sync="detail.show"
    :title="detail.title" @hidden="handleDetailClose">
    <div class="alarm-detail-header" slot="header">
      <span v-if="loading" class="header-name">{{ $t('加载中...') }}</span>
      <span v-else class="header-name">{{ `${$t('告警组详情')} - #${detail.id} ${detail.title}` }}</span>
      <span
        class="header-edit"
        v-authority="{ active: !authority.MANAGE_AUTH }"
        @click="authority.MANAGE_AUTH ? handleEditAlarmGroup() : handleShowAuthorityDetail(alarmGroupAuth.MANAGE_AUTH)">{{ $t('编辑告警组') }}</span>
      <span class="header-record" @click="handleShowChangeRecord">{{ $t('查看变更记录') }}</span>
    </div>
    <div slot="content" class="alarm-details" v-bkloading="{ 'isLoading': loading }">
      <div class="alarm-details-col">
        <div class="alarm-details-label">{{ $t('所属') }}</div>
        <div class="alarm-details-item">{{ bizName }}</div>
      </div>
      <div class="alarm-details-col">
        <div class="alarm-details-label">{{ $t('告警组名称') }}</div>
        <div class="alarm-details-item alarm-details-content">{{ detailData.name }}</div>
      </div>
      <div class="alarm-details-col text-top" style="margin-bottom: 14px">
        <div class="alarm-details-label alarm-details-person-label">{{ $t('通知对象') }}</div>
        <div class="alarm-details-item alarm-details-person">
          <template v-if="detailData.noticeReceiver && detailData.noticeReceiver.length">
            <div class="person-box" v-for="(item, index) in detailData.noticeReceiver" :key="index">
              <div class="person-image">
                <img v-if="item.logo" :src="item.logo">
                <i v-else-if="!item.logo && item.type === 'group'"
                   class="icon-monitor icon-mc-user-group no-img">
                </i>
                <i v-else-if="!item.logo && item.type === 'user'"
                   class="icon-monitor icon-mc-user-one no-img">
                </i>
              </div>
              <span class="person-name">{{ item.displayName }}</span>
            </div>
          </template>
          <span class="notice-empty" v-else>--</span>
        </div>
      </div>
      <div class="alarm-details-col text-top">
        <div class="alarm-details-label alarm-details-noticeway-label">{{ $t('通知方式') }}</div>
        <div class="alarm-details-notice-way alarm-details-item">
          <table class="notice-table" cellspacing="0" v-if="noticeWay">
            <thead>
              <th>{{ $t('告警级别') }}</th>
              <th v-for="(item, index) in noticeWay" :key="index">
                <div>
                  <!-- <i class="icon-monitor icon" :class="item.icon"></i> -->
                  <img class="item-img" :src="item.icon" />
                  {{ item.label }}
                </div>
              </th>
            </thead>
            <tbody>
              <tr v-for="(item, index) in noticeData" :key="index">
                <td>{{ item.title }}</td>
                <td v-for="notice in item.list"
                    :key="notice.type"
                    :class="{ 'work-group': notice.type === 'wxwork-bot' }">
                  <i v-if="notice.checked && notice.type !== 'wxwork-bot'" class="bk-icon icon-check-1 checklist"></i>
                  <div :title="notice.workGroupId"
                       class="wechat-group-id"
                       v-if="notice.type === 'wxwork-bot' && notice.checked && notice.workGroupId">
                    {{ notice.workGroupId }}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="alarm-details-col">
        <div class="alarm-details-label">{{ $t('回调地址') }}</div>
        <div class="alarm-details-item">{{ detailData.webhookUrl || '--' }}</div>
      </div>
      <div class="alarm-details-col text-top">
        <div class="alarm-details-label alarm-details-des-label">{{ $t('说明') }}</div>
        <div class="alarm-details-item">
          <pre style="margin: 0; white-space: pre-wrap;">{{ detailData.message || '--' }}</pre>
        </div>
      </div>
      <change-record :record-data="detailData" :show.sync="recordShow"></change-record>
    </div>
  </bk-sideslider>
</template>

<script>
import { mapActions } from 'vuex'
import ChangeRecord from '../../../components/change-record/change-record'
export default {
  name: 'alarm-group-detail',
  components: {
    ChangeRecord
  },
  inject: ['authority', 'handleShowAuthorityDetail', 'alarmGroupAuth'],
  props: {
    id: {
      type: [String, Number], // 告警组详情ID
      default: 0
    },
    detail: {
      type: Object,
      default() {
        return {
          show: false,
          title: ''
        }
      }
    }
  },
  data() {
    return {
      recordShow: false,
      detailData: {},
      bizName: '',
      noticeWay: [], // 通知方式
      noticeData: [], //  通知表格勾选数据
      webhookUrl: '',
      iconMap: {
        weixin: 'icon-mc-weixin',
        mail: 'icon-mc-youjian',
        sms: 'icon-mc-duanxin',
        voice: 'icon-mc-dianhua',
        'wxwork-bot': 'icon-qiye-weixin'
      },
      levelMap: {
        1: this.$t('致命'),
        2: this.$t('预警'),
        3: this.$t('提醒')
      },
      loading: false
    }
  },
  watch: {
    id(newV) {
      if (newV !== 0) {
        this.handleDetailData(newV)
      }
    },
    immediate: true
  },
  created() {
    this.id && this.handleDetailData(this.id)
  },
  methods: {
    ...mapActions('alarm-group', ['noticeGroupDetail', 'getNoticeWay']),
    handleEditAlarmGroup() {
      this.$emit('edit-group', this.id)
    },
    handleShowChangeRecord() {
      this.recordShow = true
    },
    handleDetailClose() {
      this.$emit('detail-close', false)
    },
    async handleDetailData(id) {
      this.loading = true
      // 通知方式接口
      this.noticeWay = await this.getNoticeWay()
      // 替换数据中对应的icon的展示样式
      this.noticeWay.forEach((way) => {
        way.icon = `data:image/png;base64,${way.icon}`
      })
      // 告警详情数据
      this.detailData = await this.noticeGroupDetail({ id })
      const tableData = []
      Object.keys(this.detailData.noticeWay).forEach((key, index) => {
        const noticeWay = this.detailData.noticeWay[key]
        // 渲染初始表格
        const list = this.noticeWay.map((set) => {
          if (set.type === 'wxwork-bot') {
            return { type: set.type, checked: false, workGroupId: '' }
          }
          return { type: set.type, checked: false }
        })
        // 对应勾选
        noticeWay.forEach((notice) => {
          const listItem = list.find(set => set.type === notice)
          listItem && (listItem.checked = true)
        })
        // 企业微信群勾选项
        if (this.detailData.wxworkGroup && this.detailData.wxworkGroup[key]) {
          const listItem = list.find(set => set.type === 'wxwork-bot')
          if (listItem) {
            listItem.checked = true
            listItem.workGroupId = this.detailData.wxworkGroup[key]
          }
        }
        tableData.push({
          list,
          level: key,
          title: this.levelMap[index + 1]
        })
      })
      this.noticeData = tableData.reverse()
      // 筛选出所属业务
      if (this.detailData.bkBizId === 0) {
        this.bizName = this.$t('全业务')
      } else {
        const bizItem = this.$store.getters.bizList.filter(item => this.detailData.bkBizId === item.id)
        this.bizName = bizItem[0].text
      }
      this.loading = false
    }
  }
}
</script>

<style lang="scss" scoped>
    .alarm-details {
      display: flex;
      flex-direction: column;
      padding: 38px 40px 38px 30px;
      color: #63656e;
      .alarm-dividing-line {
        width: 100%;
        height: 1px;
        background: #dcdee5;
        margin-bottom: 20px;
      }
      &-content {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }
      &-col {
        display: flex;
        align-items: center;
        line-height: 16px;
        margin-bottom: 20px;
      }
      &-item {
        flex: 1;
        word-break: break-all;
      }
      &-label {
        width: 70px;
        color: #979ba5;
        text-align: right;
        margin-right: 21px;
      }
      &-person {
        display: flex;
        flex-flow: row wrap;
        .person-box {
          display: flex;
          align-items: center;
          margin-bottom: 10px;
          height: 26px;
        }
        .person-image {
          display: flex;
          align-items: center;
          img {
            width: 24px;
            height: 24px;
            border-radius: 50%;
          }
          .no-img {
            color: #c4c6cc;
            font-size: 22px;
            background: #fafbfd;
            border-radius: 16px;
          }
        }
        .person-name {
          margin-left: 6px;
          margin-right: 20px;
        }
      }
      &-person-label {
        position: relative;
        top: 5px;
      }
      &-noticeway-label {
        position: relative;
        top: 4px;
      }
      &-des-label {
        position: relative;
        top: 1px;
      }
      .notice-empty {
        position: relative;
        top: 5px;
      }
      .text-top {
        align-items: start;
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
          height: 40px;
          text-align: center;
          border-right: 1px solid #dcdee5;
          border-bottom: 1px solid #dcdee5;
          background-color: #fff;
          &:last-child {
            border-right: 0;
          }
          &.work-group {
            width: 20%;
          }
          .checklist {
            color: #2dcb56;
            font-size: 24px;
            font-weight: 600;
          }
          .wechat-group-id {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 200px;
            padding: 0 10px;
          }
        }
      }
    }
    .alarm-detail-header {
      display: flex;
      align-items: center;
      .header-name {
        max-width: 513px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .header-edit {
        color: #3a84ff;
        cursor: pointer;
        margin-left: auto;
        font-size: 12px;
        font-weight: normal;
      }
      .header-record {
        margin: 0 40px 0 16px;

        /* stylelint-disable-next-line scss/at-extend-no-missing-placeholder */
        @extend .header-edit;
      }
    }
</style>
