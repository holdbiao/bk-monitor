<template>
  <div class="migrate-dashboard" v-monitor-loading="{ isLoading: loading }">
    <bk-table
      class="migrate-dashboard-table"
      :empty-text="$t('暂无数据')"
      :data="tableData">
      <bk-table-column :label="$t('仪表盘名称')">
        <template v-slot="{ row }">
          <div>
            {{ row.name }}
          </div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('迁移状态')">
        <template v-slot="{ row }">
          <div class="status-col">
            <span :class="'status-' + statusMap[row.status].status"></span>
            <span class="status-name">{{ statusMap[row.status].name }}</span>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column min-width="220" :label="$t('详细信息')">
        <template v-slot="{ row }">
          <div :title="row.detail">
            {{ row.message }}
          </div>
        </template>
      </bk-table-column>
    </bk-table>
    <bk-pagination
      v-show="totalData.data.length"
      class="migrate-dashboard-pagination"
      align="right"
      size="small"
      show-total-count
      pagination-able
      @change="handlePageChange"
      @limit-change="handleLimitChange"
      :current="totalData.page"
      :limit="totalData.pageSize"
      :count="totalData.data.length"
      :limit-list="pageList">
    </bk-pagination>
    <div class="migrate-dashboard-tips">
      {{ $t('1.迁移会在新版仪表盘中按旧版仪表盘配置新建仪表盘。不会清空新版仪表盘的数据。') }}<br />
      {{ $t('2.多次点击迁移会创建多份相同配置的仪表盘，同名仪表盘会在名字后面加上“_Copy”。') }}
    </div>
    <div class="migrate-dashboard-footer">
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH }"
        @click="authority.MANAGE_AUTH ? handleMigrateOldDashboard() : handleShowAuthorityDetail()"
        theme="primary">
        {{ $t('开始迁移') }}
      </bk-button>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Mixins } from 'vue-property-decorator'
import commonPageSizeMixin from '../../mixins/commonPageSizeMixin'
import { migrateOldDashboard, getOldDashboards } from '../../../monitor-api/modules/grafana'
import MonitorVue from '../../types/index'
import * as migrageAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'

@Component({
  name: 'migrate-dashboard'
})
export default class MigrateDashboard
  extends Mixins(commonPageSizeMixin, authorityMixinCreate(migrageAuth))<MonitorVue> {
  loading = false
  statusMap: {} = {}
  pageList: number[] = [10, 20, 50, 100]
  totalData = {
    data: [],
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  get tableData(): Array<any> {
    return this.totalData.data.slice(
      this.totalData.pageSize * (this.totalData.page - 1),
      this.totalData.pageSize * this.totalData.page
    )
  }

  async created() {
    this.statusMap = {
      NOT_MIGRATE: {
        name: this.$t('未迁移'),
        status: 1
      },
      SUCCESS: {
        name: this.$tc('成功'),
        status: 2
      },
      FAILED: {
        name: this.$tc('失败'),
        status: 3
      }
    }
    this.loading = true
    const data = await getOldDashboards().catch(() => ([]))
    if (data.length) {
      this.totalData.data = data
    }
    this.loading = false
  }

  handleMigrateOldDashboard() {
    this.$bkInfo({
      title: this.$t('是否开始迁移？'),
      confirmFn: async (vm) => {
        vm.close()
        this.loading = true
        const data = await migrateOldDashboard().catch(() => ([]))
        if (data.length) {
          this.totalData.data = data
          this.$bkMessage({
            theme: 'success',
            message: this.$t('迁移完成，请确认迁移结果')
          })
        }
        this.loading = false
      }
    })
  }

  // 切换当前页
  handlePageChange(page: number) {
    this.totalData.page = page
  }

  // 切换页码
  handleLimitChange(limit: number) {
    this.totalData.page = 1
    this.totalData.pageSize = limit
    this.handleSetCommonPageSize(`${limit}`)
  }
}
</script>

<style lang="scss" scoped>
    @import "../home/common/mixins";
    $statusBorderColors: #c4c6cc #2dcb56 #ea3636;
    $statusColors:  #f0f1f5 #94f5a4 #fd9c9c;

    .migrate-dashboard {
      &-table {
        font-size: 12px;
        .status-col {
          display: flex;
          align-items: center;
          height: 20px;
          line-height: 14px;

          @for $i from 1 through length($statusColors) {
            .status-#{$i} {
              display: inline-block;
              width: 12px;
              height: 12px;
              border-radius: 50%;
              background: nth($statusColors, $i);
              border: 1px solid nth($statusBorderColors, $i);
              margin-right: 5px;
            }
          }
          .status-name {
            font-size: 12px;
            color: $defaultFontColor;
          }
        }
      }
      &-pagination {
        background: #fff;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        border-top: 0;
        /deep/ .bk-page-count {
          width: 115px;
        }
      }
      &-tips {
        font-size: 14px;
      }
      &-footer {
        margin-top: 10px;
      }
    }
</style>
