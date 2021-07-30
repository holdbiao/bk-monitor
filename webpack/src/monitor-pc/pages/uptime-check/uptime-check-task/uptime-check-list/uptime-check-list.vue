<template>
  <div class="task-list">
    <bk-table class="task-list-table"
              :data="tableData"
              ref="table" :empty-text="$t('没有搜索到相关拨测任务')">
      <bk-table-column :label="$t('任务名称')" min-width="150">
        <template slot-scope="scope">
          <div class="col-name">
            <span @click="handleClickName(scope.row)">{{scope.row.name || '--'}}</span>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('目标地址')" min-width="350">
        <template slot-scope="scope">
          <div class="col-url">{{scope.row.url || '--'}}</div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('协议')" min-width="80">
        <template slot-scope="scope">
          <div class="col-url">{{ scope.row.protocol }}</div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('响应时长')">
        <template slot-scope="scope" min-width="120">
          <span :style="{ color: scope.row.alarm_num === 0 ? '' : '#EA3636' }">
            {{scope.row.task_duration !== null ? `${scope.row.task_duration}ms` : '--'}}
          </span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('可用率')" min-width="120">
        <template slot-scope="scope">
          <div class="col-available">
            <div class="rate-name">
              {{scope.row.available !== null ? `${scope.row.available}%` : '--'}}
            </div>
            <bk-progress
              :color="filterAvailable(scope.row.available, scope.row.status)"
              :show-text="false"
              :percent="+(scope.row.available * 0.01).toFixed(2) || 0">
            </bk-progress>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('所属分组')" min-width="120">
        <template slot-scope="scope">
          <span>{{scope.row.groups && scope.row.groups.length ? scope.row.groups.map(item => item.name).join(',') : '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('创建人')" prop="create_user" min-width="120">
      </bk-table-column>
      <bk-table-column :label="$t('状态')" width="120">
        <template slot-scope="scope">
          <span :style="{ color: scope.row.status === 'stoped' ? '#c7c7c7' : (['start_failed','stop_failed'].includes(scope.row.status) ? '#EA3636' : '#63656E') }">{{table.statusMap[scope.row.status]}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('启/停')" width="120">
        <template slot-scope="scope">
          <bk-switcher
            v-authority="{ active: !authority.MANAGE_AUTH }"
            class="col-switcher"
            :ref="`switch-${scope.$index}`"
            @change.native="handleStatusChange(scope.row, scope.$index)"
            :value="scope.row.switch"
            :disabled="['starting','new_draft', 'stoping'].includes(scope.row.status)"
            size="small">
          </bk-switcher>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="150">
        <template slot-scope="scope">
          <div class="col-operate">
            <span
              v-authority="{ active: !authority.MANAGE_AUTH }"
              class="col-operate-btn"
              @click="authority.MANAGE_AUTH ? handleRowEdit(scope) : handleShowAuthorityDetail()">
              {{ $t('编辑') }}
            </span>
            <span
              v-authority="{ active: !authority.MANAGE_AUTH }"
              class="col-operate-btn"
              @click="authority.MANAGE_AUTH ? handleRowDelete(scope.row) : handleShowAuthorityDetail()">
              {{ $t('删除') }}
            </span>
            <span
              v-authority="{ active: !authority.MANAGE_AUTH }"
              :class="['col-operate-more', { 'more-active': popover.active === scope.$index }]"
              @click="authority.MANAGE_AUTH ? handleShowMoreList(scope.row, scope.$index, $event) : handleShowAuthorityDetail()">
              <i data-popover="true" class="bk-icon icon-more"></i>
            </span>
          </div>
        </template>
      </bk-table-column>
    </bk-table>
    <bk-pagination
      v-if="tableData && tableData.length"
      class="task-list-pagination list-pagination"
      align="right"
      size="small"
      show-total-count
      @change="handlePageChange"
      @limit-change="handleLimitChange"
      v-bind="pagination">
    </bk-pagination>
    <div v-show="false">
      <div class="more-group" ref="moreGroup">
        <span class="more-group-btn" @click="handleCloneTask"> {{ $t('克隆') }} </span>
      </div>
    </div>
  </div>
</template>
<script>
import { createNamespacedHelpers } from 'vuex'
import { uptimeCheckMixin } from '../../../../common/mixins'
import { changeStatusUptimeCheckTask, destroyUptimeCheckTask,
  cloneUptimeCheckTask } from '../../../../../monitor-api/modules/model'
import { SET_PAGE, SET_PAGE_SIZE } from '../../../../store/modules/uptime-check-task'
const { mapGetters, mapActions, mapMutations } = createNamespacedHelpers('uptime-check-task')
export default {
  name: 'uptime-check-list',
  mixins: [uptimeCheckMixin],
  inject: ['authority', 'handleShowAuthorityDetail'],
  props: {
    changeStatus: Function
  },
  data() {
    return {
      table: {
        data: [],
        loading: false,
        statusMap: {
          running: this.$t('运行中'),
          stoped: this.$t('已停用'),
          start_failed: this.$t('启用失败'),
          stop_failed: this.$t('停用失败'),
          starting: this.$t('启用中'),
          stoping: this.$t('停用中'),
          new_draft: this.$t('未保存')
        }
      },
      watchInstance: null,
      popover: {
        instance: null,
        active: -1,
        data: {}
      }
    }
  },
  computed: {
    ...mapGetters(['keyword', 'tableData', 'pagination'])
  },
  created() {
    this.watchInstance = this.$watch('keyword', () => {
      this.setTabelData()
    })
  },
  activated() {
    this.$refs.table.doLayout()
  },
  beforeDestroy() {
    this.watchInstance()
  },
  methods: {
    ...mapActions(['setTabelData']),
    ...mapMutations([SET_PAGE_SIZE, SET_PAGE]),
    handleClickName(item) {
      this.$emit('detail-show', item)
    },
    handlePageChange(page) {
      this.SET_PAGE(page)
      this.setTabelData()
    },
    handleRowEdit(data) {
      this.$emit('edit', data.row)
    },
    handleLimitChange(limit) {
      this.SET_PAGE(1)
      this.SET_PAGE_SIZE(limit)
      this.setTabelData()
    },
    handleStatusChange(rowData, index) {
      if (!this.authority.MANAGE_AUTH) {
        this.$refs[`switch-${index}`].enabled = rowData.switch
        this.handleShowAuthorityDetail()
        return
      }
      const row = rowData
      this.table.loading = true
      changeStatusUptimeCheckTask(row.id, { status: row.switch ? 'stoped' : 'running' }).then((data) => {
        row.status = data.status
        this.changeStatus(row.id, row.status)
        this.$bkMessage({
          theme: 'success',
          message: data.status === 'running' ? this.$t('任务启动成功') : this.$t('任务停止成功')
        })
        this.table.loading = false
      })
        .catch(() => {
          this.$refs[`switch-${index}`].enabled = row.switch
          this.table.loading = false
        })
    },
    handleRowDelete(row) {
      this.$bkInfo({
        title: this.$t('确认要删除？'),
        maskClose: true,
        confirmFn: () => {
          this.table.loading = true
          destroyUptimeCheckTask(row.id, {}).then(() => {
            this.$bkMessage({
              theme: 'success',
              message: this.$t('任务删除成功！')
            })
            this.$emit('update-all')
          })
            .finally(() => {
              this.table.loading = false
            })
        }
      })
    },
    // 显示更多操作
    handleShowMoreList(row, index, e) {
      this.popover.data = row
      this.popover.active = index
      if (!this.popover.instance) {
        this.popover.instance = this.$bkPopover(e.target, {
          content: this.$refs.moreGroup,
          arrow: false,
          trigger: 'click',
          placement: 'bottom',
          theme: 'light common-monitor',
          maxWidth: 520,
          duration: [200, 0],
          onHidden: () => {
            this.popover.active = -1
            this.popover.instance.destroy()
            this.popover.instance = null
          }
        })
      }
      this.popover.instance && this.popover.instance.show(100)
    },
    // 克隆任务
    handleCloneTask() {
      this.table.loading = true
      cloneUptimeCheckTask(this.popover.data.id, {}, { needRes: true }).then(() => {
        this.$emit('update-all')
        this.SET_PAGE(1)
        this.setTabelData()
        this.$bkMessage({
          theme: 'success',
          message: this.$t('任务克隆成功！')
        })
      })
        .finally(() => {
          this.table.loading = false
        })
    }
  }
}
</script>
<style lang="scss" scoped>
.task-list {
  font-size: 12px;
  color: #63656e;
  &-table {
    .col-name {
      color: #3a84ff;
      cursor: pointer;
    }
    .col-available {
      .rate-name {
        line-height: 16px;
      }
      /deep/ .progress-bar {
        box-shadow: none;
      }
    }
    // /deep/ .bk-table-body {
    //     width: 100%;
    // }
    .col-switcher {
      &.is-checked {
        background: #3a84ff;
      }
    }
    .col-operate {
      color: #3a84ff;
      display: flex;
      align-items: center;
      cursor: pointer;
      :not(:last-child) {
        margin-right: 10px;
      }
      &-more {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        .icon-more {
          color: #3a84ff;
          font-size: 14px;
        }
        &:hover {
          background: #ddd;
          cursor: pointer;
        }
        &.more-active {
          background: #ddd;
        }
      }
    }
    .col-url {
      direction: rtl;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      unicode-bidi: plaintext;
    }
  }
  &-pagination {
    background: #fff;
    border: 1px solid #dcdee5;
    padding: 15px;
    border-radius: 2px;
    border-top: 0;
  }
}
.more-group {
  display: flex;
  flex-direction: column;
  width: 68px;
  // padding: 6px 0;
  color: #63656e;
  font-size: 12px;
  border: 1px solid #dcdee5;
  &-btn {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding-left: 10px;
    height: 32px;
    background: #fff;
    &:hover {
      background: #f0f1f5;
      color: #3a84ff;
      cursor: pointer;
    }
  }
}
</style>
