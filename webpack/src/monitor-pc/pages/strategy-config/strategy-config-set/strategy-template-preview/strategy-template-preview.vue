<template>
  <monitor-dialog
    :value.sync="show"
    :title="$t('告警模板预览')"
    width="860"
    :need-footer="true"
    @on-confirm="handleConfirm"
    @change="handleValueChange">
    <template>
      <div v-bkloading="{ isLoading: loading }">
        <ul class="preview-tab">
          <li v-for="(item,index) in renderData"
              :key="index"
              :class="{ 'tab-active': tabActive === index }"
              @click="handleTabItemClick(item, index)"
              class="preview-tab-item">
            {{item.label}}
          </li>
        </ul>
        <preview-template :render-list="renderTemplate"></preview-template>
      </div>
    </template>
  </monitor-dialog>
</template>
<script>
import PreviewTemplate from './preview-template'
import MonitorDialog from '../../../../../monitor-ui/monitor-dialog/monitor-dialog'
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('strategy-config')
export default {
  name: 'strategy-template-preview',
  components: {
    PreviewTemplate,
    MonitorDialog
  },
  props: {
    // 是否显示
    dialogShow: Boolean,
    // 通知模板
    template: {
      type: String,
      required: true
    },
    // 监控对象id
    scenario: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      show: false,
      renderData: [],
      tabActive: 0,
      loading: false,
      oldTemplate: ''
    }
  },
  computed: {
    renderTemplate() {
      const data = this.renderData[this.tabActive]
      return (data?.messages.map(item => ({
        ...item,
        tabActive: this.tabActive,
        message: item.message.replace(/\n/gmi, '</br>').replace(/<style[^>]*>[^<]+<\/style>/gmi, '')
      }))) || []
    }
  },
  watch: {
    dialogShow: {
      async handler(v) {
        this.show = v
        if (v && this.template.length && this.oldTemplate !== this.template) {
          this.loading = true
          this.oldTemplate = this.template
          const data = await this.getRenderNoticeTemplate({
            scenario: this.scenario,
            template: this.template
          })
          this.renderData = data
          this.loading = false
        }
      },
      immediate: true
    }
  },
  beforeDestroy() {
    this.handleConfirm()
  },
  methods: {
    ...mapActions(['getRenderNoticeTemplate']),
    //  dialog显示变更触发
    handleValueChange(v) {
      this.$emit('update:dialogShow', v)
    },
    // tabitem 点击触发事件
    handleTabItemClick(item, index) {
      this.tabActive = index
    },
    handleConfirm() {
      this.show = false
      this.$emit('update:dialogShow', false)
    }
  }
}
</script>
<style lang="scss" scoped>
    .preview-tab {
      display: flex;
      height: 36px;
      border-bottom: 1px solid #dcdee5;
      margin-top: 10px;
      align-items: center;
      font-size: 14px;
      color: #63656e;
      &-item {
        display: flex;
        align-items: center;
        margin-right: 22px;
        height: 100%;
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
        cursor: pointer;
        &.tab-active {
          border-bottom-color: #3a84ff;
          color: #3a84ff;
        }
        &:hover {
          color: #3a84ff;
        }
      }
    }
</style>
