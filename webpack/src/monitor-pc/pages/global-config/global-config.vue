<template>
  <div class="global-config" v-monitor-loading="{ isLoading: loading }">
    <bk-form v-bind="formProps">
      <bk-form-item :label="$t('消息通知渠道')" required>
        <template>
          <ul class="channel-list">
            <li class="channel-list-item" @click="item.check = !item.check" :class="{ 'is-checked': item.check }" v-for="item in staticForm.ENABLED_NOTICE_WAYS" :key="item.id">
              <bk-checkbox class="item-check" :value="item.check"></bk-checkbox>
              <img class="item-img" :src="item.icon" />
              <span class="item-name">{{item.name}}</span>
            </li>
          </ul>
          <div class="channel-desc"> {{ $t('新增消息通知渠道') }} <span class="channel-desc-btn" @click="handleGotoLink('globalConfiguration')"> {{ $t('配置指引') }} </span>
            <div v-show="validate.channel && isValidateChannel" class="error-message" style="bottom: -18px;"> {{ $t('请选择消息通知渠道') }} </div>
          </div>
        </template>
      </bk-form-item>
      <bk-form-item :label="$t('通知方式')">
        <ul class="notice-list">
          <li class="notice-list-item" v-for="item in staticForm.MESSAGE_QUEUE_DSN" :key="item.id">
            <bk-checkbox v-model="item.check">{{item.name}}</bk-checkbox>
            <template v-if="item.id === 'message-queue'">
              <div class="message-set" v-show="item.check">
                <bk-select class="message-set-select" @change="handleSelectChange" :style="{ marginBottom: item.check ? '5px' : '0px' }" :clearable="false" :value="item.way">
                  <bk-option v-for="set in item.list"
                             :key="set.id"
                             :id="set.id"
                             :name="set.name">
                  </bk-option>
                </bk-select>
                <bk-input class="message-set-input" v-model="item.value" :placeholder="item.placeholder"></bk-input>
                <div v-show="validate.notice && isValidateNotice" class="error-message"> {{ $t('请输入正确的格式') }} </div>
              </div>
            </template>
          </li>
        </ul>
      </bk-form-item>
      <bk-form-item :label="$t('标签')">
        <multi-label-select
          mode="create"
          :tree-data="labelTreeData" />
      </bk-form-item>
    </bk-form>
    <create-form
      v-if="list.length"
      :form-list="list"
      :model="data"
      :rules="rules"
      :form-props="formProps"
      @reset="handleReset"
      @save="saveGlobalConfig">
    </create-form>
  </div>
</template>
<script>
import CreateForm from './create-form'
import MultiLabelSelect from '../../components/multi-label-select/multi-label-select.tsx'
import { labelListToTreeData } from '../../components/multi-label-select/utils'
import { listGlobalConfig, setGlobalConfig } from '../../../monitor-api/modules/config'
import { getNoticeWay } from '../../../monitor-api/modules/notice_group'
import documentLinkMixin from '../../mixins/documentLinkMixin'
import * as globalAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
import { strategyLabelList } from '../../../monitor-api/modules/strategies'
import { transformDataKey } from '../../../monitor-common/utils/utils'
export default {
  name: 'GlobalConfig',
  components: {
    CreateForm,
    MultiLabelSelect
  },
  mixins: [documentLinkMixin, authorityMixinCreate(globalAuth)],
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail
    }
  },
  data() {
    return {
      loading: false,
      data: {},
      list: [],
      rules: {},
      staticForm: {
        ENABLED_NOTICE_WAYS: [],
        MESSAGE_QUEUE_DSN: [
          {
            id: 'message-queue',
            name: this.$t('消息队列'),
            list: [
              {
                id: 'redis',
                name: 'Redis',
                placeholder: 'redis://:${password}@${host}:${port}/${db}/${key}'
              },
              {
                id: 'kafka',
                name: 'Kafka',
                placeholder: 'kafka://${username}:${password}@${host}:${port}/${topic}'
              }

            ],
            way: '',
            value: '',
            placeholder: '',
            check: false
          }
          // {
          //     id: 'worker-order',
          //     name: '工单'
          // },
          // {
          //     id: 'fault-healing',
          //     name: '故障自愈'
          // }
        ]
      },
      formProps: {
        'label-width': 186
      },
      validate: {
        channel: false,
        notice: false
      },
      labelTreeData: []
    }
  },
  computed: {
    isValidateChannel() {
      return !this.staticForm.ENABLED_NOTICE_WAYS.some(item => item.check)
    },
    isValidateNotice() {
      const item = this.staticForm.MESSAGE_QUEUE_DSN.find(set => set.check)
      if (item && item.id === 'message-queue') {
        const val = item.value.trim()
        return !(val.length > 0 && val.indexOf(`${item.way}://`) === 0)
      }
      return false
    }
  },
  created() {
    this.getListConfig()
    this.getLabelList()
  },
  methods: {
    /**
     * 获取全局标签数据列表(扁平数据)
     */
    getLabelList() {
      const params = {
        bk_biz_id: 0,
        strategy_id: 0
      }
      strategyLabelList(params).then((res) => {
        const data = transformDataKey(res)
        const globalData = [
          ...data.global,
          ...data.globalParentNodes.map(item => ({ id: item.labelId, labelName: item.labelName }))
        ]
        this.labelTreeData = labelListToTreeData(globalData)
      })
    },
    // 获取配置信息
    async getListConfig() {
      this.loading = true
      const noticeWay = await getNoticeWay({ show_all: true }).catch(() => ([]))
      const data = await listGlobalConfig().catch(() => false)
      if (data) {
        const formModel = {}
        const formRules = {}
        const formList = []
        data.forEach((item) => {
          const { key } = item
          if (key === 'ENABLED_NOTICE_WAYS') {
            this.staticForm[key] = noticeWay.map(way => ({
              id: way.type,
              name: way.label,
              icon: `data:image/png;base64,${way.icon}`,
              check: item.value.includes(way.type)
            }))
          } else if (key === 'MESSAGE_QUEUE_DSN') {
            const [dsn] = this.staticForm[key]
            dsn.value = item.value
            const matchs = (`${item.value}`).match(/^(redis|kafka)/) || ['redis']
            dsn.way = matchs[0]
            dsn.check = item.value.length > 1
          } else {
            formModel[item.key] = item.value
            if (item.rules && item.rules.length) {
              formRules[item.key] = item.rules
            }
            formList.push(item)
          }
        })
        this.data = formModel
        this.rules = formRules
        this.list = formList.map((item, i) => {
          if (item.type === 'tag-input') {
            item.formChildProps['allow-auto-match'] = true
            // 给taginput传入粘贴方法
            item.formChildProps['paste-fn'] = v => this.handlePaste(v, i)
          } else if (item.type === 'switcher') {
            item.formChildProps.size = 'small'
          }
          return item
        })
      }
      this.loading = false
    },
    handlePaste(v, i) {
      v = v.trim() // 去除前后空格
      const key = this.list[i].formItemProps.property
      const tagList = this.data[key]
      if (!tagList.includes(v)) {
        tagList.push(v)
      }
      return []
    },
    // 保存配置
    async saveGlobalConfig(validate) {
      let createValidate = false
      if (validate) {
        createValidate = await validate().then(() => true)
          .catch(() => false)
      }
      const staticValidate = this.handleValidate()
      if (createValidate && staticValidate) {
        this.$store.commit('app/SET_MAIN_LOADING', true)
        const configs = Object.keys(this.data).map(key => ({ key, value: this.data[key] }))
        Object.keys(this.staticForm).forEach((key) => {
          const item = this.staticForm[key]
          if (key === 'ENABLED_NOTICE_WAYS') {
            const value = []
            item.forEach(set => set.check && value.push(set.id))
            configs.push({
              key,
              value
            })
          } else if (key === 'MESSAGE_QUEUE_DSN') {
            configs.push({
              key,
              value: !item[0].check ? '' : item[0].value
            })
          }
        })
        await setGlobalConfig({ configs }, { needBiz: false }).then(() => {
          this.$bkMessage({
            theme: 'success',
            message: this.$t('保存成功！')
          })
          const [queueItem] = this.staticForm.MESSAGE_QUEUE_DSN
          this.$store.commit('app/SET_MESSAGE_QUEUE', {
            enable: queueItem.check,
            dsn: queueItem.value
          })
          this.$store.commit('app/SET_MAIN_LOADING', false)
        })
          .catch(() => {
            this.$store.commit('app/SET_MAIN_LOADING', false)
            this.handleReset()
          })
      }
    },
    // 验证固定的form信息
    handleValidate() {
      const { ENABLED_NOTICE_WAYS, MESSAGE_QUEUE_DSN } = this.staticForm
      let mark = true
      if (!ENABLED_NOTICE_WAYS.some(item => item.check)) {
        mark = false
        this.validate.channel = true
      }
      const [messageQueue] = MESSAGE_QUEUE_DSN
      if (messageQueue.check && !(messageQueue.value.trim().length > 1
            && messageQueue.value.trim().indexOf(`${messageQueue.way}://`) === 0)) {
        mark = false
        this.validate.notice = true
      }
      return mark
    },
    handleSelectChange(id) {
      const [item] = this.staticForm.MESSAGE_QUEUE_DSN
      if (item.way !== id) {
        item.way = id
        item.value = ''
        item.placeholder = item.list.find(set => set.id === id).placeholder
      }
    },
    handleReset() {
      this.validate.notice = false
      this.validate.channel = false
      this.getListConfig()
    }
  }
}
</script>
<style lang="scss" scoped>
.global-config {
  min-height: calc(100vh - 100px);
  font-size: 12px;
  margin: 20px 24px;
  .notice-list {
    display: flex;
    flex-direction: column;
    margin-bottom: 24px;
    &-item {
      margin-bottom: 18px;
      line-height: 28px;
      &:first-child {
        margin-bottom: 0px;
      }
      .item-check {
        margin-bottom: 4px;
      }
      .message-set {
        display: flex;
        margin-top: 4px;
        position: relative;
        &-select {
          width: 140px;
          margin-right: 6px;
          background-color: #fff;
        }
        &-input {
          width: 394px;
        }
      }
    }
  }
  .channel-list {
    display: flex;
    margin-bottom: 7px;
    &-item {
      width: 100px;
      height: 100px;
      border-radius: 2px;
      position: relative;
      display: flex;
      align-items: center;
      flex-direction: column;
      border: 1px solid #dcdee5;
      margin-right: 10px;
      background: #fff;
      .item-check {
        visibility: hidden;
        position: absolute;
        top: 3px;
        right: 3px;
      }
      .item-img {
        width: 32px;
        height: 32px;
        // background-color: #699DF4;
        margin-top: 23px;
      }
      .item-name {
        line-height: 16px;
        margin-top: 9px;
        font-size: 12px;
        color: #63656e;
      }
      &.is-checked {
        cursor: pointer;
        .item-check {
          visibility: visible;
        }
      }
      &:hover {
        box-shadow: 0px 0px 0px 2px #e1ecff;
        border-color: #699df4;
        cursor: pointer;
        .item-check {
          visibility: visible;
        }
      }
    }
  }
  .channel-desc {
    color: #979ba5;
    margin-bottom: 22px;
    line-height: 16px;
    position: relative;
    &-btn {
      margin-left: 4px;
      color: #3a84ff;
      cursor: pointer;
    }
  }
  .error-message {
    position: absolute;
    color: #ea3636;
    bottom: -15px;
    line-height: 16px;
  }
  /deep/ .bk-form-checkbox.is-checked {
    .bk-checkbox {
      border-color: #3a84ff;
      background-color: #3a84ff;
      background-clip: border-box;
    }
  }

}
</style>
