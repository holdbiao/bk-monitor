<template>
  <bk-dialog
    :value="isShowVariableTable"
    theme="primary"
    :header-position="'left'"
    :show-footer="false"
    @after-leave="handleAfterLeave" :title="$t('推荐变量')"
    width="960px">
    <div class="variable-table">
      <div class="dialog-left">
        <bk-table style="margin-top: 15px;"
                  :data="data"
                  size="small">
          <bk-table-column :label="$t('变量名')" prop="name" min-width="100"></bk-table-column>
          <bk-table-column :label="$t('含义')" prop="description" min-width="70"></bk-table-column>
          <bk-table-column :label="$t('示例')" prop="example" min-width="70"></bk-table-column>
        </bk-table>
      </div>
      <div class="dialog-right">
        <div class="title"> {{ $t('格式说明') }} </div>
        <div class="item">
          <bk-popover>
            <div><span class="tips"> {{ $t('变量格式') }} </span>：</div>
            <div slot="content"> {{ $t('inja2模板引擎') }} </div>
          </bk-popover>
          <div class="content" v-text="'{{target.对象.字段名}}'"></div>
        </div>
        <div class="item">
          <div> {{ $t('对象包含：') }} </div>
          <div class="content">host {{ $t('主机') }}</div>
          <div class="content">process {{ $t('进程') }}</div>
          <div class="content">service {{ $t('服务实例') }}</div>
        </div>
        <div class="item">
          <div> {{ $t('字段名：') }} </div>
          <div class="content"> {{ $t('CMDB中定义的字段名') }} </div>
        </div>
      </div>
      <div class="foot"></div>
    </div>
  </bk-dialog>
</template>

<script>
import { getCollectVariables } from '../../../../../monitor-api/modules/collecting'
export default {
  props: {
    isShowVariableTable: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      data: []
    }
  },
  created() {
    this.getTableData()
  },
  methods: {
    getTableData() {
      getCollectVariables().then((data) => {
        this.data = data
      })
    },
    handleAfterLeave() {
      this.$emit('update:isShowVariableTable', false)
    }
  }
}
</script>

<style lang="scss" scoped>
    /deep/ .bk-dialog-wrapper .bk-dialog-header {
      padding: 3px 24px 14px;
    }
    /deep/ .bk-table-body-wrapper {
      max-height: 430px;
      overflow: auto;
      overflow-x: hidden;
    }
    /deep/ .bk-dialog-wrapper .bk-dialog-body {
      padding: 3px 24px 0;
    }
    .variable-table {
      font-size: 12px;
      color: #63656e;
      display: flex;
      position: relative;
      .dialog-left {
        width: 760px;
        max-height: 474px;
        overflow: auto;
        margin-right: 20px;
        /deep/ .bk-table {
          /* stylelint-disable-next-line declaration-no-important */
          margin-top: 0px !important;
        }
      }
      .dialog-right {
        width: 120px;
        .title {
          font-weight: bold;
          margin-bottom: 16px;
        }
        .item {
          margin-bottom: 16px;
          .content {
            color: #979ba5;
          }
          .tips {
            border-bottom: 1px dashed #63656e;
            cursor: pointer;
          }
        }
      }
      .foot {
        position: absolute;
        width: 100%;
        height: 4px;
        background: #fff;
        bottom: 0px;
        z-index: 1;
      }
    }
</style>
