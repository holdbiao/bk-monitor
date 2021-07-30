<template>
  <div class="alarm-shield-scope">
    <div class="set-shield-config-item">
      <div class="item-label item-required"> {{ $t('所属') }} </div>
      <div class="item-container">
        <bk-select readonly v-model="biz.value" :clearable="false">
          <bk-option v-for="(item, index) in biz.list" :key="index" :id="item.id" :name="item.text"></bk-option>
        </bk-select>
      </div>
    </div>
    <div class="set-shield-config-item shield-scope" :class="{ 'edit': isEdit }">
      <div class="item-label item-required"> {{ $t('屏蔽范围') }} </div>
      <div class="item-container">
        <div class="bk-button-group" v-if="!isEdit">
          <bk-button v-for="(item, index) in bkGroup.list" :key="index" class="scope-item" :class="{ 'is-selected': bkGroup.value === item.id }" @click.stop="handleScopeChange(item.id)">
            {{item.name}}
          </bk-button>
        </div>
        <bk-table class="static-table" v-else-if="bkGroup.value !== 'biz'" ref="bkTable" :data="tableData" :max-height="450">
          <bk-table-column :label="labelMap[bkGroup.value]" prop="name"></bk-table-column>
        </bk-table>
        <span v-else> {{ $t('业务') }} </span>
      </div>
    </div>
    <div class="set-shield-config-item tips-wrapper" :class="{ 'tab-biz': bkGroup.value === 'biz' }" v-if="!isEdit">
      <div class="item-label"></div>
      <div class="item-container">
        <span class="tips-text"><i class="icon-monitor icon-tips item-icon"></i>{{tips[bkGroup.value]}}</span>
      </div>
    </div>
    <div class="set-shield-config-item topo-selector" v-show="bkGroup.value !== 'biz' && !isEdit">
      <div class="item-label"></div>
      <div class="item-container">
        <shield-target :target-type="bkGroup.value" ref="shieldTarget"></shield-target>
      </div>
    </div>
    <shield-date-config ref="noticeDate"></shield-date-config>
    <div class="set-shield-config-item">
      <div class="item-label cause-label"> {{ $t('屏蔽原因') }} </div>
      <div class="item-container shield-cause">
        <bk-input v-model="shieldDesc" type="textarea" :row="3" :maxlength="100"></bk-input>
      </div>
    </div>
    <shiled-notice ref="shieldNotice"></shiled-notice>
    <div class="set-shield-config-item">
      <div class="item-label"></div>
      <div class="item-container mb20">
        <bk-button theme="primary" @click="handleSubmit"> {{ $t('提交') }} </bk-button>
        <bk-button @click="handleCancel" class="ml10"> {{ $t('取消') }} </bk-button>
      </div>
    </div>
  </div>
</template>
<script>
import ShieldDateConfig from '../../alarm-shield-components/alarm-shield-date'
import ShiledNotice from '../../alarm-shield-components/alarm-shield-notice'
import ShieldTarget from './alarm-shield-target'
import { addShield, editShield } from '../../../../../monitor-api/modules/shield'
export default {
  name: 'alarm-shield-scope',
  components: {
    ShieldDateConfig,
    ShiledNotice,
    ShieldTarget
  },
  props: {
    shieldData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    const defaultData = this.generationDefaultData()
    return {
      bigTreeData: [],
      isEdit: false,
      topoLoading: false,
      tips: {
        instance: this.$t('服务实例屏蔽: 屏蔽告警中包含该实例的通知'),
        ip: this.$t('主机屏蔽: 屏蔽告警中包含该IP通知,包含对应的实例'),
        node: this.$t('节点屏蔽: 屏蔽告警中包含该节点下的所有IP和实例的通知'),
        biz: this.$t('业务屏蔽: 屏蔽告警中包含该业务的所有通知')
      },
      ...defaultData
    }
  },
  computed: {
    isInstance() {
      return this.bkGroup.value === 'instance'
    },
    prop() {
      return this.bkGroup.value === 'ip' ? 'ip' : 'name'
    }
  },
  watch: {
    shieldData: {
      handler(v) {
        if (this.$route.name === 'alarm-shield-edit') {
          this.isEdit = true
          this.handleSetEditData(v)
        } else {
          this.isEdit = false
        }
      },
      deep: true
    },
    'bkGroup.value'() {
      this.targetError = false
    }
  },
  activated() {
    const defaultData = this.generationDefaultData()
    Object.keys(defaultData).forEach((key) => {
      this[key] = defaultData[key]
    })
    this.biz.list = this.$store.getters.bizList
    this.biz.value = this.$store.getters.bizId
  },
  methods: {
    generationDefaultData() {
      return {
        biz: {
          list: [],
          value: ''
        },
        instanceType: 'service',
        tableData: [],
        topoSelector: {
          checkedData: [],
          defaultActive: 1
        },
        labelMap: {
          ip: this.$t('主机'),
          instance: this.$t('服务实例'),
          node: this.$t('节点名称'),
          biz: this.$t('业务')
        },
        shieldDesc: '',
        bkGroup: {
          list: [
            { name: this.$t('服务实例'), id: 'instance' },
            { name: this.$t('主机'), id: 'ip' },
            { name: this.$t('节点'), id: 'node' },
            { name: this.$t('业务'), id: 'biz' }
          ],
          value: 'ip'
        },
        targetError: false
      }
    },
    handleScopeChange(v) {
      this.bkGroup.value = v
      this.instanceType = v === 'instance' ? 'service' : ''
      const type = {
        ip: 0,
        instance: 1,
        node: 2
      }
      this.topoSelector.defaultActive = type[v]
    },
    handleSetEditData(data) {
      const cycleConfig = data.cycle_config
      const cycleMap = { 1: 'single', 2: 'day', 3: 'week', 4: 'month' }
      const type = cycleMap[cycleConfig.type]
      const isSingle = cycleConfig.type === 1
      const shieldDate = {}
      shieldDate.typeEn = type
      shieldDate[type] = {
        list: [...cycleConfig.day_list, ...cycleConfig.week_list],
        range: isSingle ? [data.begin_time, data.end_time] : [cycleConfig.begin_time, cycleConfig.end_time]
      }
      shieldDate.dateRange = isSingle ? [] : [data.begin_time, data.end_time]
      this.$refs.noticeDate.setDate(shieldDate)
      if (data.shield_notice) {
        const shieldNoticeData = {
          notificationMethod: data.notice_config.notice_way,
          noticeNumber: data.notice_config.notice_time,
          member: {
            value: data.notice_config.notice_receiver.map(item => item.id)
          }
        }
        this.$refs.shieldNotice.setNoticeData(shieldNoticeData)
      }
      this.biz.value = data.bk_biz_id
      this.shieldDesc = data.description
      this.bkGroup.value = data.scope_type
      if (this.bkGroup.value !== 'biz') {
        this.tableData = data.dimension_config.target.map(item => ({ name: item }))
      }
    },
    handleGetShieldCycle() {
      const result = this.$refs.noticeDate.getDateData()
      if (!result) return
      const cycleDate = result[result.typeEn]
      const isSingle = result.typeEn === 'single'
      const params = {
        begin_time: isSingle ? '' : cycleDate.range[0],
        end_time: isSingle ? '' : cycleDate.range[1],
        day_list: result.typeEn === 'month' ? result.month.list : [],
        week_list: result.typeEn === 'week' ? result.week.list : [],
        type: result.type
      }
      return {
        begin_time: isSingle ? cycleDate.range[0] : result.dateRange[0],
        end_time: isSingle ? cycleDate.range[1] : result.dateRange[1],
        cycle_config: params
      }
    },
    handleDimensionConfig() {
      const dimension = this.bkGroup.value
      const dimensionConfig = { scope_type: this.bkGroup.value }
      if (dimension !== 'biz') {
        const data = this.$refs.shieldTarget.handleGetTarget()
        if (!data.length) {
          this.targetError = true
          return
        }
        const target = {
          ip: dimension === 'ip' && data.map(item => ({ ip: item.ip, bk_cloud_id: item.bkCloudId })),
          node: dimension === 'node' && data.map(item => ({ bk_obj_id: item.bkObjId, bk_inst_id: item.bkInstId })),
          instance: dimension === 'instance' && data.map(item => item.service_instance_id)
        }
        dimensionConfig.target = target[dimension]
      }
      return dimensionConfig
    },
    handleParams() {
      const cycleConfig = this.handleGetShieldCycle()
      const noticeData = this.$refs.shieldNotice.getNoticeConfig()
      if (!cycleConfig || !noticeData) return
      const params = {
        category: 'scope',
        ...cycleConfig,
        shield_notice: typeof noticeData !== 'boolean',
        notice_config: {},
        description: this.shieldDesc
      }
      if (params.shield_notice) {
        params.notice_config = {
          notice_time: noticeData.notice_time,
          notice_way: noticeData.notice_way,
          notice_receiver: noticeData.notice_receiver
        }
      }
      if (this.isEdit) {
        params.id = this.$route.params.id
      } else {
        const config = this.handleDimensionConfig()
        if (!config) return
        params.dimension_config = config
      }
      return params
    },
    handleSubmit() {
      const params = this.handleParams()
      if (!params) return
      this.$emit('update:loading', true)
      const ajax = this.isEdit ? editShield : addShield
      const text = this.isEdit ? this.$t('编辑屏蔽成功') : this.$t('创建屏蔽成功')
      ajax(params).then(() => {
        this.$router.push({ name: 'alarm-shield', params: { refresh: true } })
        this.$bkMessage({ theme: 'success', message: text, ellipsisLine: 0 })
      })
        .catch(() => {
        // console.error(err.data.message)
        })
        .finally(() => {
          this.$emit('update:loading', false)
        })
    },
    handleCancel() {
      this.$router.back()
    }
  }
}
</script>
<style lang="scss" scoped>
.alarm-shield-scope {
  padding: 40px 0 0 30px;
  .set-shield-config-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-bottom: 20px;
    font-size: 14px;
    color: #63656e;
    .item-label {
      min-width: 110px;
      text-align: right;
      margin-right: 24px;
      position: relative;
      flex: 0 0;
      &.cause-label {
        position: relative;
        top: -18px;
      }
    }
    &.shield-scope {
      margin-bottom: 8px;
    }
    &.topo-selector {
      margin-bottom: 26px;
    }
    &.edit {
      align-items: flex-start;
      margin-bottom: 26px;
      .item-label {
        top: 4px;
      }
    }
    &.tips-wrapper {
      margin-bottom: 10px;
    }
    &.tab-biz {
      margin-bottom: 28px;
    }
    .tips-text {
      display: flex;
      align-items: center;
      font-size: 12px;
    }
    .icon-tips {
      margin-right: 6px;
      font-size: 14px;
      line-height: 1;
      color: #979ba5;
    }
    .item-required::after {
      content: "*";
      color: red;
      position: absolute;
      top: 2px;
      right: -9px;
    }
    .item-container {
      // width: 836px;
      .scope-item {
        width: 168px;
      }
      /deep/ .bk-textarea-wrapper .bk-form-textarea.textarea-maxlength {
        margin-bottom: 0px;
      }
      /deep/ .bk-form-textarea {
        min-height: 60px;
      }
      /deep/ .bk-table::before {
        height: 0;
      }
      .static-table {
        width: 836px;
        /deep/ .cell {
          padding-left: 30px;
        }
        &:before {
          height: 1px;
        }
      }
      &.shield-cause {
        width: 836px;
      }
    }
    .bk-select {
      width: 413px;
    }
  }
}
</style>
