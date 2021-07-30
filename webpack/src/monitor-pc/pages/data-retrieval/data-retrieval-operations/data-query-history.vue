<template>
  <div class="data-query-history">
    <bk-exception v-if="!historyList.length" type="empty" scene="part" class="empty-wrapper">
      <span>{{$t('暂无数据')}}</span>
    </bk-exception>
    <template v-else>
      <data-query-history-item
        v-for="(item, index) in historyList"
        :index="index"
        :data="item"
        :key="'key' + item.id">
      </data-query-history-item>
    </template>
  </div>
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import DataQueryHistoryItem from './data-query-history-item.vue'
import MonitorVue from '../../../types/index'
import DataRetrieval from '../../../store/modules/data-retrieval'

@Component({
  name: 'data-query-history',
  components: {
    DataQueryHistoryItem
  }
})
export default class DataQueryHistory extends Vue<MonitorVue> {
  get historyList() {
    return DataRetrieval.historyListData
  }

  deactivated() {
    // 清空暂存历史
    DataRetrieval.clearQueryHistoryCache()
  }
}
</script>

<style lang="scss" scoped>
.data-query-history {
  height: 100%;
  .empty-wrapper {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    .part-img {
      margin-top: -100px;
    }
  }
}
</style>
