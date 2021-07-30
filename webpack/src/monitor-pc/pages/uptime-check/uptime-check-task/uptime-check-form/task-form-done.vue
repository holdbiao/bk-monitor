<template>
  <article class="task-from-done">
    <section class="done-top">
      <div class="done-top-icon">
        <i class="icon-monitor" :class="currentStatusText.icon"></i>
      </div>
      <div class="done-top-title">
        {{ currentStatusText.title }}
      </div>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="done-top-content" v-if="status === 'error' && errorMsg" v-html="errorMsg"></div>
      <div class="done-top-operate">
        <bk-button class="mr10" @click="cancelUptimeCheckTask">{{ currentStatusText.cancelText }}</bk-button>
        <bk-button theme="primary" @click="goToEdit" v-if="showToEdit">{{ currentStatusText.confirmText }}</bk-button>
        <bk-button theme="primary" @click="confirmUptimeCheckTask" v-else>{{ currentStatusText.confirmText }}</bk-button>
      </div>
    </section>
    <section class="done-bottom" v-if="status === 'success' && tableData.length > 0">
      <bk-table :data="tableData">
        <bk-table-column :label="$t('指标')" prop="label" width="198"></bk-table-column>
        <bk-table-column :label="$t('详情')" prop="detail" width="311"></bk-table-column>
        <bk-table-column :label="$t('操作')" width="102">
          <template #default="{ row }">
            <bk-button
              class="table-operate-button"
              theme="primary"
              text
              :disabled="row.status === 0"
              @click="goStrategy(row)"> {{ $t('前往配置策略') }} </bk-button>
          </template>
        </bk-table-column>
      </bk-table>
    </section>
  </article>
</template>
<script>
export default {
  name: 'uptime-check-task-done',
  props: {
    // 拨测新增报错时显示
    errorMsg: String,
    editId: [String, Number],
    status: {
      type: String,
      default: 'success',
      validator(value) {
        return ['success', 'error'].includes(value)
      }
    },
    tableData: {
      type: Array,
      default: () => []
    },
    type: {
      type: String,
      default: 'add',
      validator(value) {
        return ['add', 'edit'].includes(value)
      }
    }
  },
  data() {
    return {
      success: {
        add: {
          icon: 'icon-duihao icon-success',
          title: this.$t('拨测任务创建成功'),
          cancelText: this.$t('返回列表'),
          confirmText: this.$t('继续添加拨测任务')
        },
        edit: {
          icon: 'icon-duihao icon-success',
          title: this.$t('拨测任务编辑成功'),
          cancelText: this.$t('返回列表'),
          confirmText: this.$t('继续添加拨测任务')
        }
      },
      error: {
        add: {
          icon: 'icon-chahao icon-error',
          title: this.$t('拨测任务创建失败'),
          cancelText: this.$t('放弃'),
          confirmText: this.$t('修改后重试')
        },
        edit: {
          icon: 'icon-chahao icon-error',
          title: this.$t('拨测任务编辑失败'),
          cancelText: this.$t('放弃'),
          confirmText: this.$t('修改后重试')
        }
      }
    }
  },
  computed: {
    currentStatusText() {
      return this[this.status][this.type]
    },
    showToEdit() {
      return this.status === 'error' && this.editId && this.type === 'add'
    }
  },
  methods: {
    cancelUptimeCheckTask() {
      this.$emit('back-add')
      this.$router.push({
        name: 'uptime-check'
      })
    },
    confirmUptimeCheckTask() {
      this.status === 'success' ? this.$emit('clear-task-data', true) : this.$emit('clear-task-data', false)
    },
    goStrategy(row) {
      this.$router.push({
        name: 'strategy-config-add',
        params: {
          metric: {
            aggCondition: [],
            aggDimension: [],
            aggInterval: 60,
            aggMethod: 'AVG',
            dataSourceLabel: 'bk_monitor',
            dataTypeLabel: 'time_series',
            metricName: row.metric,
            metricAlicName: row.label,
            resultTableId: row.resultTableId,
            resultTableLabel: row.resultTableLabel,
            // uniqueId: '',
            relatedId: row.relatedId,
            relatedName: row.relatedName
          }
        }
      })
    },
    goToEdit() {
      this.$router.push({
        name: 'uptime-check-task-edit',
        params: {
          id: this.editId
        }
      })
    }
  }
}
</script>
<style lang="scss" scoped>
    @mixin horizontal-center {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    @mixin done-top-item($marginTop, $fontSize, $color) {
      margin-top: $marginTop;
      font-size: $fontSize;
      color: $color;
    }

    .task-from-done {
      @include horizontal-center;
      .done-top {
        @include horizontal-center;
        &-icon {
          margin-top: 54px;
          .icon-success {
            font-size: 50px;
            color: #2dcb56;
          }
          .icon-error {
            font-size: 50px;
            color: #ea3636;
          }
        }
        &-title {
          @include done-top-item(16px, 16px, #313238);
        }
        &-content {
          max-width: 500px;

          @include done-top-item(12px, 12px, #63656E);
        }
        &-operate {
          margin-top: 19px;
        }
      }
      .done-bottom {
        margin-top: 40px;
        .table-operate-button {
          padding: 0;
        }
      }
    }
</style>
