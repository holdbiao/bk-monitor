<template>
  <div class="data-retrieval-operations">
    <!-- 头部按钮组 -->
    <div class="bk-button-group btn-group">
      <bk-button :class="['btn', { 'is-selected': btnGroupAcitve === 0 }]">{{ $t('指标检索') }}</bk-button>
      <bk-button
        :class="['btn', { 'is-selected': btnGroupAcitve === 1 }]"
        @click="$emit('log-click')"
      >{{ $t('日志检索') }}</bk-button>
    </div>
    <!-- tab栏 -->
    <bk-tab :active="curTab" @tab-change="changeTab" type="unborder-card" class="tab-wrapper">
      <bk-tab-panel v-for="(panel, index) in tabList" v-bind="panel" :key="index"></bk-tab-panel>
    </bk-tab>
    <div class="scroll-wrapper" v-bkloading="{ isLoading: loading }">
      <!-- 查询条件 / 查询历史 -->
      <keep-alive>
        <component :is="curTab"></component>
      </keep-alive>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import DataQueryConditions from './data-query-conditions.vue'
import DataQueryHistory from './data-query-history.vue'
import MonitorVue from '../../../types/index'
import { IHistoryListItem } from '../index'
import DataRetrieval from '../../../store/modules/data-retrieval'

@Component({
  name: 'data-retrieval-operations',
  components: {
    DataQueryConditions,
    DataQueryHistory
  }
})
export default class DataRetrievalOperations extends Vue<MonitorVue> {
  // 数据检索 0 / 日志检索 1
  btnGroupAcitve: 0 | 1 = 0;
  // tab数据
  tabList: { name: string; label: string }[] = [
    {
      name: 'data-query-conditions',
      label: '数据查询'
    },
    {
      name: 'data-query-history',
      label: '查询历史'
    }
  ];

  loading = false

  // 查询历史列表
  historyList: IHistoryListItem[] = [];

  get curTab() {
    return DataRetrieval.curTabGetter
  }

  get promiseListFullPage() {
    return DataRetrieval.promiseListFullPage
  }

  created() {
    this.$store.dispatch('strategy-config/getScenarioList')
    this.loading = true
    // 加入请求队列
    DataRetrieval.addPromiseListFullPage(DataRetrieval.getLabelList())
    DataRetrieval.addPromiseListFullPage(DataRetrieval.getMainlineObjectTopo())
    DataRetrieval.addPromiseListFullPage(DataRetrieval.getListQueryHistory())
    Promise.all(this.promiseListFullPage).finally(() => {
      // 清空promise list
      this.loading = false
      DataRetrieval.clearPromiseListFullPage()
    })
  }

  changeTab(value) {
    DataRetrieval.setData({ expr: 'curTab', value })
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.data-retrieval-operations {
  .btn-group {
    display: flex;
    padding: 16px 20px 6px 20px;
    .btn {
      flex: 1;
    }
    /deep/ .bk-button.is-selected {
      background-color: rgba(58, 132, 255, .06);
    }
  }
  .tab-wrapper {
    /deep/.bk-tab-label-list {
      display: flex;
      width: 100%;
      padding: 0 20px;
      .bk-tab-label-item {
        flex: 1;
        padding-left: 10px;
        padding-right: 10px;
        min-width: 0;
        &.active {
          &::after {
            left: 0;
            width: 100%;
          }
        }
      }
    }
    /deep/.bk-tab-section {
      padding: 0;
    }
  }
  .scroll-wrapper {
    height: calc(100vh - 96px - 52px);
    overflow: auto;
    /deep/.icon-arrow-down {
      display: inline-block;
      width: 24px;
      height: 24px;
      font-size: 28px;
      &::before {
        width: 100%;
        height: 100%;
        transform: rotate(0deg);
        transition: all .3s ease-in-out;

        @include content-center;
      }
    }
    /deep/.arrow-right {
      &::before {
        transform: rotate(-90deg);
      }
    }
  }
}
</style>
