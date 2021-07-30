<template>
  <div>
    <bk-table :data="data">
      <bk-table-column :label="$t('时间')" prop="time">
        <template #default="{ row }">
          {{ getFormatTime(row) }}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('日志')" prop="content" :min-width="200">
        <template #default="{ row }">
          <span class="log" @click="handleShowDetai(row)">{{ row.content }}</span>
        </template>
      </bk-table-column>
    </bk-table>
    <!-- <div class="load-more" v-if="data.length > 0 && !isLast">
      <bk-button class="btn" text @click="handleLoadMore">{{$t('查看更多')}}</bk-button>
    </div> -->
    <bk-dialog
      v-model="showLogDetail"
      :show-footer="false"
      header-position="left"
      :width="700"
      :title="$t('日志详情')">
      <div class="log-content">
        {{ logDetail }}
      </div>
    </bk-dialog>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit } from 'vue-property-decorator'
import moment from 'moment'

@Component({ name: 'strategy-view-log' })
export default class StrategyViewLog extends Vue {
  @Prop({ default: () => [], type: Array }) private readonly data!: any[]
  @Prop({ default: false, type: Boolean }) private readonly isLast!: boolean

  private showLogDetail = false
  private logDetail = ''

  handleShowDetai(row) {
    this.logDetail = row.content
    this.showLogDetail = true
  }

  @Emit('load-more')
  handleLoadMore() {}

  getFormatTime({ time }) {
    if (typeof time === 'string') {
      return moment(time).format('YYYY-MM-DD HH:mm:ss')
    } if (typeof time === 'number') {
      if (time.toString().length === 10) return moment(time).format('YYYY-MM-DD HH:mm:ss')
      return moment.unix(time / 1000).format('YYYY-MM-DD HH:mm:ss')
    }
    return time
  }
}
</script>
<style lang="scss" scoped>
.log {
  cursor: pointer;
  &:hover {
    color: #3a84ff;
  }
  &-content {
    height: 380px;
    background: #f5f6fa;
    border-radius: 2px;
    padding: 15px 20px;
    overflow: auto;
    word-break: break-all;
  }
}
.load-more {
  height: 24px;
  background: #fafbfd;
  display: flex;
  justify-content: center;
  border: 1px solid #dcdee5;
  margin-top: -1px;
  .btn {
    font-size: 12px;
  }
}
</style>
