<template>
  <bk-dialog
    :value="show"
    :show-footer="false"
    :mask-close="false"
    ext-cls="plugin-dialog-multiple"
    header-position="left"
    @cancel="handleDialogClose"
    width="640">
    <template slot="header">
      <div class="dialog-title">
        {{ $t('导入中') }}
      </div>
    </template>
    <div class="dilog-container">
      <div class="dialog-content" v-for="(item, index) in files" :key="index" ref="content">
        <span class="icon-monitor icon-CPU dialog-content-icon"></span>
        <div class="dialog-content-desc">
          <div class="desc-name">
            <div class="item-name" v-bk-overflow-tips>{{ item.name }}</div>
            <div v-if="item.versonShow" class="item-verson">（{{ $t("版本") }}{{ item.verson }}）</div>
            <div class="item-status"
                 :style="{ 'color': statusMap[item.status] }"
                 @mouseleave="handleMouseLeave"
                 @mouseenter="handleMouseEnter($event, item.text)">
              {{ item.status }}
            </div>
          </div>
          <bk-progress
            v-if="item.percentShow"
            class="desc-process"
            :percent="item.percent"
            :show-text="false"
            size="small"
            color="#3A84FF">
          </bk-progress>
        </div>
      </div>
      <div class="dialog-footer">
        <bk-button v-show="isSuccess" class="dialog-footer-btn" theme="primary" @click="handleDialogClose"> {{ $t('完成') }} </bk-button>
      </div>
    </div>
    <div></div>
  </bk-dialog>
</template>

<script>
export default {
  name: 'plugin-dialog-multiple',
  props: {
    show: Boolean,
    files: {
      type: Array,
      default: () => ([])
    }
  },
  data() {
    return {
      statusMap: {
        [this.$t('成功')]: '#2DCB56',
        [this.$t('上传失败')]: '#EA3636',
        [this.$t('插件重名')]: '#EA3636',
        [this.$t('插件已存在')]: '#EA3636',
        [this.$t('非官方插件')]: '#EA3636',
        [this.$t('插件包不完整')]: '#EA3636',
        [this.$t('上传中...')]: '#3A84FF',
        [this.$t('解析中...')]: '#3A84FF',
        [this.$t('解析失败')]: '#EA3636'
      },
      popoverInstance: null
    }
  },
  computed: {
    isSuccess() {
      return this.files.every(item => item.isOk)
    }
  },
  methods: {
    handleDialogClose() {
      this.$emit('update:show', false)
      this.$emit('refalsh-table-data')
    },
    handleMouseEnter(event, text) {
      if (text) {
        this.popoverInstance = this.$bkPopover(event.target, {
          content: text,
          arrow: true,
          maxWidth: 382,
          showOnInit: true,
          distance: 22,
          offset: -120
        })
        this.popoverInstance.show(100)
      }
    },
    handleMouseLeave() {
      if (this.popoverInstance) {
        this.popoverInstance.hide(0)
        this.popoverInstance.destroy()
        this.popoverInstance = null
      }
    }
  }
}
</script>

<style lang="scss" scoped>
  .plugin-dialog-multiple {
    .dialog-title {
      font-size: 24px;
      color: #313238;
      line-height: 32px;
    }
    .dilog-container {
      color: #63656e;
      font-size: 12px;
      margin-top: -10px;
      .dialog-content {
        display: flex;
        align-items: center;
        border-radius: 2px;
        height: 42px;
        padding: 0 12px;
        background: #f5f7fa;
        margin-bottom: 6px;
        &-icon {
          color: #3a84ff;
          font-size: 20px;
        }
        &-desc {
          flex: 1;
          margin-left: 9px;
          .desc-name {
            display: flex;
            align-items: center;
            justify-content: space-between;
            &-size {
              margin-left: auto;
            }
            .item-name {
              width: 226px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              flex-grow: 1;
            }
            .item-verson {
              width: 66px;
              margin-right: 10px;
            }
            .item-status {
              width: 72px;
              text-align: right;
            }
          }
        }
      }
      .dialog-footer {
        margin-top: 24px;
        display: flex;
        justify-content: flex-end;
        &-btn {
          margin-left: 10px;
        }
      }
    }
  }
  /deep/ .bk-dialog-body {
    padding: 3px 26px 26px;
  }
</style>
