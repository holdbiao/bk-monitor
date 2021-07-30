<template>
  <monitor-dialog
    :value.sync="show" :title="$t('变量列表')"
    width="960"
    :need-footer="false"
    @on-confirm="handleConfirm"
    @change="handleValueChange">
    <div class="variate-wrapper">
      <ul class="preview-tab">
        <li v-for="(tab,index) in variateList"
            :key="index"
            :class="{ 'tab-active': tabActive === index }"
            @click="tabActive = index"
            class="preview-tab-item">
          {{tab.name}}
        </li>
      </ul>
      <div class="variate-list">
        <bk-table class="variate-list-table" :data="tableData">
          <bk-table-column min-width="200" :label="$t('变量名')">
            <template v-slot="{ row }">
              {{ `{{${row.id}\}\}`}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('含义')" prop="name"> </bk-table-column>
          <bk-table-column :label="$t('示例')" prop="description"></bk-table-column>
        </bk-table>
        <div class="variate-list-desc">
          <h5 class="desc-title"> {{ $t('格式说明') }} </h5>
          <div class="item-title"> {{ $t('变量格式：') }} </div>
          <div class="item-desc"> {{descData['format'] || '--'}}</div>
          <div class="item-title"> {{ $t('对象包含：') }} </div>
          <div class="item-desc">
            <template v-if="descData['object']">
              <div v-for="item in descData['object']" :key="item.id">{{item.id}} {{item.name}}</div>
            </template>
            <template v-else>
              --
            </template>
          </div>
          <div class="item-title"> {{ $t('字段名：') }} </div>
          <div class="item-desc">{{descData['field'] || '--'}}</div>
        </div>
        <div class="variate-list-mask"></div>
      </div>
    </div>
  </monitor-dialog>
</template>
<script>
import MonitorDialog from '../../../../../monitor-ui/monitor-dialog/monitor-dialog'
export default {
  name: 'strategy-variate-list',
  components: {
    MonitorDialog
  },
  // 是否显示
  props: {
    dialogShow: Boolean,
    variateList: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      show: false,
      tabActive: 0
    }
  },
  computed: {
    tableData() {
      const tab = this.variateList[this.tabActive]
      return tab ? tab.items : []
    },
    descData() {
      const tab = this.variateList[this.tabActive]
      return tab ? tab.description : {}
    }
  },
  watch: {
    dialogShow: {
      handler(v) {
        this.show = v
      },
      immediate: true
    }
  },
  beforeDestroy() {
    this.handleConfirm()
  },
  methods: {
    // dialog显示变更触发
    handleValueChange(v) {
      this.$emit('update:dialogShow', v)
    },
    handleConfirm() {
      this.show = false
      this.$emit('update:dialogShow', false)
    }
  }
}
</script>
<style lang="scss" scoped>
  .variate-wrapper {
    // margin-bottom: -26px;
    margin-top: 10px;
    height: 528px;
    position: relative;
    .preview-tab {
      display: flex;
      height: 36px;
      border-bottom: 1px solid #dcdee5;
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
    .variate-list {
      margin-top: 10px;
      display: flex;
      &-table {
        flex: 1;
        /deep/ .bk-table-body-wrapper {
          overflow-y: auto;
          overflow-x: hidden;
          max-height: 435px;
        }
      }
      &-desc {
        flex: 0 0 153px;
        border: 1px solid #dcdee5;
        border-left: 0;
        border-radius: 0px 2px 0px 0px;
        padding: 15px 10px 15px 18px;
        font-size: 12px;
        color: #63656e;
        .desc-title {
          font-weight: bold;
          margin: 0;
        }
        .item-title {
          margin-top: 16px;
          line-height: 16px;
        }
        .item-desc {
          color: #979ba5;
          margin-top: 6px;
          line-height: 16px;
          word-break: break-word;
        }
      }
      &-mask {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 5px;
        z-index: 9;
        background-color: #fff;
      }
    }
  }
</style>
