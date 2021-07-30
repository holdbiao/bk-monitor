<template>
  <article class="config-history" v-bkloading="{ isLoading: loading }">
    <!--友情提示-->
    <section class="config-history-tip" v-show="tableData.length > 0 && tipShow">
      <div class="tip-left">
        <span class="icon-monitor icon-tips left-icon"></span>
        <span class="left-title ml10"> {{ $t('仅保留最近30天的历史记录') }} </span>
      </div>
      <bk-button
        text
        class="tip-right"
        @click="handleHideTips"> {{ $t('不再提示') }} </bk-button>
    </section>
    <!--历史列表-->
    <section class="config-history-content" v-show="tableData.length > 0">
      <bk-table
        @row-click="handleRowClick"
        :data="tableData">
        <bk-table-column :label="$t('导入时间')" prop="createTime"></bk-table-column>
        <bk-table-column :label="$t('操作人')" prop="createUser"></bk-table-column>
        <bk-table-column :label="$t('执行结果')" width="220">
          <template #default="{ row }">
            <div class="status-col" v-if="['upload', 'importing'].includes(row.status)">
              <div class="status-item">
                <span class="status-runing icon-monitor icon-loading"></span>
                <span> {{ $t('导入中') }} </span>
              </div>
            </div>
            <div class="status-col" v-else>
              <div class="status-item"
                   v-for="(value, name, index) of row.detail"
                   :key="index"
                   v-show="value">
                <span :class="`status-${statusMap[name] ? statusMap[name].status : 'failed'}`"></span>
                <span>{{ getStatusText(name, row.detail) }}</span>
              </div>
            </div>
          </template>
        </bk-table-column>
      </bk-table>
    </section>
    <!--列表空数据-->
    <section class="config-history-empty" v-show="tableData.length === 0">
      <span class="empty-icon"><i class="icon-monitor icon-hint"></i></span>
      <span class="empty-drop"> {{ $t('未发现导入记录') }} </span>
      <span class="empty-tip"> {{ $t('仅保留最近30天的历史记录') }} </span>
    </section>
  </article>
</template>
<script>
import { mapActions } from 'vuex'
import { importConfigMixin } from '../../../common/mixins'

export default {
  name: 'import-configuration-history',
  mixins: [importConfigMixin], // 导入配置定时任务相关
  data() {
    return {
      // 表格数据
      tableData: [],
      // 状态Map
      statusMap: {
        successCount: {
          name: this.$t('成功'),
          status: 'success'
        },
        failedCount: {
          name: this.$t('失败'),
          status: 'failed'
        }
      },
      loading: false,
      tipShow: true,
      // tips过期时间 30 天（毫秒）
      expire: 3600000 * 24 * 30
    }
  },
  created() {
    this.handleInit()
  },
  methods: {
    ...mapActions('import', ['getHistoryList']),
    async handleInit() {
      this.loading = true
      // 判断提示信息是否过期
      if (window.localStorage) {
        const expireTime = window.localStorage.getItem('__import-history-tip__')
        this.tipShow = new Date().getTime() > expireTime
      }
      this.tableData = await this.getHistoryList()
      this.handleSetRuningQueue()
      this.loading = false
    },
    // 设置运行队列，刷新数据
    handleSetRuningQueue() {
      // taskQueue from mixin
      this.taskQueue = this.tableData.filter(item => ['upload', 'importing'].includes(item.status))
    },
    // 任务队列调用函数 mixin内部调用
    async handleQueueCallBack() {
      this.tableData = await this.getHistoryList()
      // 移除队列中不在运行中的任务
      this.taskQueue.forEach((item, index) => {
        this.tableData.forEach((row) => {
          if (item.id === row.id && row.status === 'imported') {
            this.taskQueue.splice(index, 1)
          }
        })
      })
    },
    getStatusText(countName, detail) {
      let unit = ''
      switch (countName) {
        case 'successCount':
          detail.failedCount ? unit = this.$t('个') : unit = this.$t('全部')
          break
        case 'failedCount':
          detail.successCount ? unit = this.$t('个') : unit = this.$t('全部')
          break
      }
      return `${unit === this.$t('个') ? detail[countName] : ''}${unit}${this.statusMap[countName].name}`
    },
    handleRowClick(row) {
      this.$router.push({
        name: 'import-configuration-importing',
        params: {
          id: row.id
        }
      })
    },
    handleHideTips() {
      if (window.localStorage) {
        const dateTime = new Date().getTime() + this.expire
        window.localStorage.setItem('__import-history-tip__', dateTime)
        this.tipShow = false
      }
    }
  }
}
</script>
<style lang="scss" scoped>
  @import "../../../static/css/common";

  $statusColors: #94f5a4 #fd9c9c #3a84ff;
  $statusBorderColors: #2dcb56 #ea3636 #3a84ff;
  $tipBackground: #f0f8ff;
  $tipBorderColor: #a3c5fd;
  $emptyTipColor: #979ba5;

  @mixin layout-flex($flexDirection: row, $alignItems: stretch, $justifyContent: flex-start) {
    display: flex;
    flex-direction: $flexDirection;
    align-items: $alignItems;
    justify-content: $justifyContent;
  }
  @mixin row-status($i: 1) {
    margin-right: 10px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: nth($statusColors, $i);
    border: 1px solid nth($statusBorderColors, $i);
  }

  /deep/ .bk-table-row {
    cursor: pointer;
  }
  .config-history {
    min-height: 100%;
    &-tip {
      padding: 0 12px;
      margin-bottom: 10px;
      height: 36px;
      border-radius: 2px;
      background: $tipBackground;

      @include layout-flex(row, center, space-between);
      @include border-1px($tipBorderColor);
      .tip-left {
        @include layout-flex(row, center, flex-start);
      }
      .left-title {
        color: $defaultFontColor;
      }
      .left-icon {
        margin-top: 2px;
        font-size: 14px;
        color: $primaryFontColor;
      }
      .tip-right {
        font-size: 12px;
      }
    }
    &-content {
      .status-col {
        @include layout-flex(row, center);
      }
      .status-item {
        margin-right: 18px;
        height: 20px;

        @include layout-flex(row, center);
      }
      .status-runing {
        margin-right: 6px;
        margin-left: -4px;
        width: 16px;
        height: 16px;
        font-size: 16px;
        color: nth($statusColors, 3);
        animation: button-icon-loading 1s linear infinite;
      }
      .status-success {
        @include row-status(1);
      }
      .status-failed {
        @include row-status(2);
      }
    }
    &-empty {
      @include layout-flex(column, center);
      .empty-icon {
        margin-top: 226px;
        height: 42px;
        width: 42px;
        font-size: 42px;
        color: $slightFontColor;
      }
      .empty-drop {
        margin-top: 6px;
        line-height: 19px;
        font-size: 14px;
        font-weight: bold;
        color: $defaultFontColor;
      }
      .empty-tip {
        margin-top: 6px;
        line-height: 16px;
        color: $emptyTipColor;
      }
    }
  }
</style>
