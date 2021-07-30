<template>
  <div v-show="false">
    <div ref="content" class="receiver-list-wrap" v-bkloading="{ isLoading: loading }">
      <div class="title">{{$t('订阅人员列表')}}</div>
      <bk-table
        class="receiver-list-table"
        :data="tableData">
        <template v-for="(item, index) in tableColumnsMap">
          <bk-table-column
            v-if="item.key !== 'handle'"
            :key="index"
            :label="item.label"
            :prop="item.key"
            :width="item.width"
            :formatter="item.formatter">
          </bk-table-column>
          <bk-table-column
            :key="'handle-' + index"
            v-else-if="needHandle"
            :label="item.label"
            :prop="item.key">
            <template slot-scope="scope">
              <bk-button
                v-if="!scope.row.isEnabled && scope.row.createTime"
                :text="true"
                @click="emitReceiver(scope.row)">{{$t('恢复订阅')}}{{scope.row[item.key]}}</bk-button>
            </template>
          </bk-table-column>
        </template>
      </bk-table>
      <div class="arrow" :data-placement="placement"></div>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, PropSync, Ref, Watch, Emit } from 'vue-property-decorator'
const { i18n } = window
/**
 * 接收人列表
 */
@Component({
  name: 'receiver-list'
})
export default class ReceiverList extends Vue {
  @PropSync('show', { default: false, type: Boolean }) localShow
  @Prop({ default: null, type: Element }) readonly target
  @Prop({ default: () => [], type: Array }) readonly tableData
  @Prop({ default: 'bottom', type: String }) readonly placement
  @Prop({ default: false, type: Boolean }) readonly needHandle
  @Prop({ default: false, type: Boolean }) readonly loading

  @Ref('content') private readonly contentRef: any

  private tipsPopoverInstance: any = null
  private offsetMap = {
    'bottom-start': -10,
    'bottom-end': 10
  }

  private tableColumnsMap: any = [
    {
      label: i18n.t('订阅人'),
      key: 'name'
    },
    {
      label: i18n.t('订阅时间'),
      key: 'createTime',
      width: 150,
      formatter: row => row.createTime || '--'
    },
    {
      label: i18n.t('订阅状态'),
      key: 'isEnabled',
      formatter: row => (row.isEnabled === null ? '--' : (row.isEnabled ? i18n.t('已订阅') : i18n.t('已取消')))
    },
    {
      label: i18n.t('最后一次发送'),
      key: 'lastSendTime',
      width: 150,
      formatter: row => row.lastSendTime || '--'
    },
    {
      label: i18n.t('操作'),
      key: 'handle'
    }
  ]

  @Watch('localShow')
  handleShowChange(v: boolean) {
    if (v) {
      this.initTipsPopover()
    }
  }

  @Emit('on-receiver')
  emitReceiver(row) {
    return row
  }

  destroyed() {
    this.hiddenPopover()
  }

  private initTipsPopover() {
    if (!this.target) return
    if (!this.tipsPopoverInstance) {
      this.tipsPopoverInstance = this.$bkPopover(this.target, {
        content: this.contentRef,
        theme: 'receiver-list',
        trigger: 'manual',
        hideOnClick: true,
        interactive: true,
        arrow: false,
        zIndex: 100,
        offset: this.offsetMap[this.placement],
        placement: this.placement,
        onHidden: () => {
          this.tipsPopoverInstance?.destroy()
          this.tipsPopoverInstance = null
          this.localShow = false
        }
      })
      this.tipsPopoverInstance?.show()
    }
  }

  private hiddenPopover() {
    this.tipsPopoverInstance?.hide()
  }
}
</script>

<style lang="scss">
.receiver-list-wrap {
  position: relative;
  padding: 16px;
  width: 640px;
  // height: 300px;
  border: 1px solid #dcdee5;
  background-color: #fff;
  box-shadow: 0px 3px 6px 0px rgba(0,0,0,.1);
  .receiver-list-table {
    .bk-table-body-wrapper {
      /* stylelint-disable-next-line declaration-no-important */
      max-height: 420px !important;

      /* stylelint-disable-next-line declaration-no-important */
      overflow-y: auto !important;
    }
  }
  .title {
    margin-bottom: 8px;
  }
  .arrow {
    position: absolute;
    top: -4px;
    width: 6px;
    height: 6px;
    background-color: #fff;
    border: 1px solid #dcdee5;
    border-right: 0;
    border-bottom: 0;
    transform: rotate(45deg);
  }
  .arrow[data-placement=bottom-start] {
    left: 14px;
  }
  .arrow[data-placement=bottom-end] {
    right: 14px;
  }
}
.receiver-list-theme {
  color: #63656e;
  padding: 0px;
  box-shadow: 0;

  /* stylelint-disable-next-line declaration-no-important */
  overflow: visible !important;
  .tippy-backdrop {
    background: none;
    width: 0;
  }
}
</style>
