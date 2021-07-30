<template>
  <bk-dialog v-model="show" :show-footer="false" :close-icon="false" width="420">
    <div class="dialog">
      <!-- 导出正常 -->
      <div v-if="state !== 'FAILURE'">
        <div class="dialog-header">
          <img src="../../../static/images/svg/spinner.svg">
          <span v-if="state === 'PENDING' || state === 'PREPARE_FILE'"> {{ $t('文件准备中...') }} </span>
          <span v-else-if="state === 'MAKE_PACKAGE'"> {{ $t('文件打包中...') }} </span>
        </div>
        <div class="dialog-tips"> {{ $t('所含内容文件') }} </div>
        <div class="dialog-content">
          <div class="column">
            <div> {{ $t('采集配置文件') }} <span v-show="isMakePackage" class="gray">（{{packageNum.collect_config_file}} {{ $t('个') }}）</span></div>
            <div> {{ $t('自动关联采集配置文件') }} <span v-show="isMakePackage" class="gray">（{{packageNum.associated_collect_config}} {{ $t('个') }} ）</span></div>
          </div>
          <div class="column">
            <div> {{ $t('策略配置文件') }} <span v-show="isMakePackage" class="gray">（{{packageNum.strategy_config_file}} {{ $t('个') }}）</span></div>
            <div> {{ $t('自动关联插件文件') }} <span v-show="isMakePackage" class="gray">（{{packageNum.associated_plugin}} {{ $t('个') }}）</span></div>
          </div>
          <div> {{ $t('视图配置文件') }} <span v-show="isMakePackage" class="gray">（{{packageNum.view_config_file}} {{ $t('个') }}）</span></div>
        </div>
      </div>
      <!-- 导出失败 -->
      <div v-else>
        <div class="dialog-header">
          <i class="icon-monitor icon-remind"></i><span> {{ $t('导出失败，请重试！') }} </span>
        </div>
        <div class="dialog-tips" :class="{ 'tips-err': state === 'FAILURE' }"> {{ $t('失败原因') }} </div>
        <div class="dialog-content dialog-content-err">
          <div class="column">{{message}}</div>
          <div class="btn"><span style="margin-right: 16px" @click="handlerRetry"> {{ $t('点击重试') }} </span><span @click="handleCloseDialog"> {{ $t('取消') }} </span></div>
        </div>
      </div>
    </div>
  </bk-dialog>
</template>

<script>
export default {
  name: 'export-configuration-dialog',
  props: {
    // 导出状态 PENDING PREPARE_FILE MAKE_PACKAGE FAILURE
    state: {
      type: String,
      default: 'PREPARE_FILE'
    },
    // 文件具体个数
    packageNum: {
      type: Object,
      default: () => ({})
    },
    // 控制dialog显示
    show: {
      type: Boolean,
      default: false
    },
    // 错误信息
    message: String
  },
  computed: {
    // 判断各文件数值是否有值
    isMakePackage() {
      return this.state === 'MAKE_PACKAGE' && Object.keys(this.packageNum).length
    }
  },
  methods: {
    // 导出失败取消按钮事件
    handleCloseDialog() {
      this.$emit('update:show', false)
    },
    // 重试操作事件
    handlerRetry() {
      this.$parent.handleSubmit()
    }
  }
}
</script>

<style lang="scss" scoped>
  .dialog {
    position: relative;
    &-header {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 80px;
      border-bottom: 1px solid #d8d8d8;
      color: #313238;
      font-size: 20px;
      img {
        width: 32px;
        height: 32px;
        margin-right: 14px;
      }
      i {
        font-size: 32px;
        margin-right: 14px;
        color: #ea3636;
      }

    }
    &-tips {
      font-size: 12px;
      position: absolute;
      color: #c4c6cc;
      background: #fff;
      padding: 0 7px;
      top: 70px;
      left: 170px;
      margin: auto;
    }
    .tips-err {
      left: 180px;
    }
    &-content {
      font-size: 12px;
      height: 140px;
      padding: 25px 40px 30px 40px;
      .column {
        margin-bottom: 18px;
        max-width: 340px;
        max-height: 42px;
        display: flex;
        overflow: hidden;
        word-wrap: break-word;
        word-break: normal;
        div {
          width: 50%;
        }
      }
      .gray {
        color: #c4c6cc;
      }
    }
    &-content-err {
      font-size: 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: start;
      padding-top: 30px;
      .btn {
        color: #3a84ff;
        span {
          cursor: pointer;
        }
      }
    }
  }
  /deep/ .bk-dialog-body {
    padding: 0;
  }
  /deep/ .bk-dialog-tool {
    display: none;
  }
</style>
