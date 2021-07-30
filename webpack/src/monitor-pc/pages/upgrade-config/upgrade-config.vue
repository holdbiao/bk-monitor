<template>
  <div class="upgrade-config" v-monitor-loading="{ isLoading: loading }">
    <div class="upgrade-config-header">
      <i class="icon-monitor icon-tips"></i>
      {{ $t('蓝鲸监控3.2版本对大部分的功能进行了最新的设计，为了确保您获得平滑的使用体验，请通过本页面进行数据迁移的确认。') }}
      <span @click="handleGotoLink('monitorUpdate')"
            class="header-detail">
        {{ $t('查看迁移内容') }}
      </span>
    </div>
    <div class="upgrade-config-content">
      <ul class="tab-list">
        <li class="tab-list-item" v-for="(tab, index) in tabList"
            @click="handleTabChange(index)"
            :key="index"
            :class="{ 'tab-active': index === tabActive }">
          {{tab}}
        </li>
        <li class="tab-list-blank"></li>
      </ul>
      <bk-table class="upgrade-table"
                :empty-text="$t('暂无数据')"
                :data="tableData">
        <template v-if="tabActive === 2">
          <bk-table-column :key="tabActive + 'bizName'"
                           :label="$t('业务名称')"
                           prop="bizName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'oldMonitorName'"
                           :label="$t('原监控源名称')"
                           prop="oldMonitorName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'oldStrategyName'"
                           :label="$t('原策略项名称')"
                           prop="oldStrategyName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'status'" :label="$t('迁移状态')">
            <template v-slot="{ row }">
              <div class="status-col">
                <span :class="'status-' + statusMap[row.status].status"></span>
                <span class="status-name">{{ statusMap[row.status].name }}</span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'detail'" min-width="220" :label="$t('详细信息')">
            <template v-slot="{ row }">
              <div :title="row.detail">
                {{ row.detail }}
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'newStrategyName'" :label="$t('迁移后策略名称')">
            <template v-slot="{ row }">
              <div :title="row.newStrategyName"
                   :class="{ 'col-strategy': row.newsStrategyId }"
                   @click="row.newsStrategyId && handleGotoStrategy(row.newsStrategyId)">
                {{ row.newStrategyName }}
              </div>
            </template>
          </bk-table-column>
        </template>
        <template v-else-if="tabActive === 3">
          <bk-table-column :key="tabActive + 'bizName'"
                           :label="$t('业务名称')"
                           prop="bizName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'oldGroupName'"
                           :label="$t('原分组名称')"
                           prop="oldGroupName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'oldViewName'"
                           :label="$t('原视图名称')"
                           prop="oldViewName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'status'" :label="$t('迁移状态')">
            <template v-slot="{ row }">
              <div class="status-col">
                <span :class="'status-' + statusMap[row.status].status"></span>
                <span class="status-name">{{ statusMap[row.status].name }}</span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'detail'" min-width="180" :label="$t('详细信息')">
            <template v-slot="{ row }">
              <div :title="row.detail">
                {{ row.detail }}
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'newGroupName'" :label="$t('迁移后分组名称')">
            <template v-slot="{ row }">
              <div :title="row.newGroupName">
                {{ row.newGroupName }}
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'newViewName'"
                           :label="$t('迁移后视图名称')"
                           prop="newViewName">
          </bk-table-column>
        </template>
        <template v-else-if="tabActive === 0">
          <bk-table-column :key="tabActive + 'bizName'" :label="$t('业务名称')" prop="bizName"></bk-table-column>
          <bk-table-column :key="tabActive + 'oldViewName'"
                           :label="$t('视图名称')"
                           prop="oldViewName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'status'" :label="$t('迁移状态')">
            <template v-slot="{ row }">
              <div class="status-col">
                <span :class="'status-' + statusMap[row.status].status"></span>
                <span class="status-name">{{ statusMap[row.status].name }}</span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'detail'" min-width="180" :label="$t('详细信息')">
            <template v-slot="{ row }">
              <div :title="row.detail">
                {{ row.detail }}
              </div>
            </template>
          </bk-table-column>
        </template>
        <template v-else-if="tabActive === 1">
          <bk-table-column :key="tabActive + 'bizName'" :label="$t('业务名称')" prop="bizName"></bk-table-column>
          <bk-table-column :key="tabActive + 'oldTaskName'"
                           :label="$t('任务名称')"
                           prop="oldTaskName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'status'" :label="$t('迁移状态')">
            <template v-slot="{ row }">
              <div class="status-col">
                <span :class="'status-' + statusMap[row.status].status"></span>
                <span class="status-name">{{ statusMap[row.status].name }}</span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :key="tabActive + 'detail'" min-width="180" :label="$t('详细信息')">
            <template v-slot="{ row }">
              <div :title="row.detail">
                {{ row.detail }}
              </div>
            </template>
          </bk-table-column>
        </template>
        <template v-else-if="tabActive === 4 || tabActive === 5">
          <bk-table-column :key="tabActive + 'bizName'"
                           :label="$t('业务名称')"
                           prop="bizName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'pluginName'"
                           :label="$t('插件名')"
                           prop="pluginName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'pluginAliaName'"
                           :label="$t('插件别名')"
                           prop="pluginAliaName">
          </bk-table-column>
          <bk-table-column :key="tabActive + 'operate'" :label="$t('操作')">
            <template v-slot="{ row }">
              <div class="operate-col" @click="handleDownloadPlugin(tabActive, row)">
                {{$t('导出')}}
              </div>
            </template>
          </bk-table-column>
        </template>
      </bk-table>
      <bk-pagination
        v-show="totalData.length"
        class="upgrade-pagination list-pagination"
        align="right"
        size="small"
        show-total-count
        pagination-able
        @change="handlePageChange"
        @limit-change="handleLimitChange"
        :current="pagination.page"
        :limit="pagination.pageSize"
        :count="totalData.length"
        :limit-list="pageList">
      </bk-pagination>
    </div>
    <div class="upgrade-config-footer">
      <div class="footer-line">
        {{ $t('1、“脚本采集” 和 “自定义exporter”不支持直接迁移，请通过该页面进行 “导出” 操作，然后在 “监控配置” - “插件” 页面中手动导入') }}
      </div>
      <div class="footer-line">{{ $t('2、仅对迁移状态为“准备”或“失败”的配置项进行迁移，已经迁移成功的配置项将被忽略') }}</div>
      <div class="footer-line">{{ $t('3、请确认以上迁移数据，确认无误后，点击“开始迁移”将立即开始迁移') }}</div>
      <div class="footer-line">
        <bk-button
          :disabled="loading"
          @click="handleExecuteUpgrade"
          class="footer-line-btn"
          theme="primary">
          {{ $t('开始迁移') }}
        </bk-button>
        <bk-button
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="footer-line-btn"
          theme="primary"
          @click="authority.MANAGE_AUTH ? handleStopStrategy() : handleShowAuthorityDetail()">
          {{ $t('停用旧版监控策略') }}
        </bk-button>
        <bk-button
          v-authority="{ active: !authority.MANAGE_AUTH }"
          class="footer-line-btn"
          theme="default"
          @click="authority.MANAGE_AUTH ? handleCreateBuildInStrategy() : handleShowAuthorityDetail()">
          {{ $t('仅创建默认策略') }}
        </bk-button>
        <bk-button
          v-authority="{ active: !authority.MANAGE_AUTH }"
          :disabled="!canMigrateStrategy"
          class="footer-line-btn"
          theme="primary"
          @click="authority.MANAGE_AUTH ? handleUpgradeStrategy() : handleShowAuthorityDetail()">
          {{ $t('策略批量重试') }}
        </bk-button>
        <!-- <bk-checkbox v-model="needClear">{{ $t('清空新版本已配置的告警策略')}}</bk-checkbox> -->
      </div>
    </div>
    <!-- <monitor-dialog
            width="856"
            :need-header="false"
            :value.sync="showDetail"
            :need-footer="false">
            <viewer :value="detailMarkDown" height="600px" class="upgrade-detial"></viewer>
        </monitor-dialog> -->
  </div>
</template>
<script lang="ts">
import Viewer from '../../components/markdown-editor/markdown-viewer.vue'
import { Component, Mixins } from 'vue-property-decorator'
import MonitorDialog from '../../../monitor-ui/monitor-dialog/monitor-dialog.vue'
import { listUpgradeItems,
  executeUpgrade,
  exportCollectorAsPlugin,
  createBuildInStrategy,
  disableOldStrategy,
  migrateStrategy } from '../../../monitor-api/modules/upgrade'
import commonPageSizeMixin from '../../mixins/commonPageSizeMixin'
import documentLinkMixin from '../../mixins/documentLinkMixin'
import authorityMixinCreate from '../../mixins/authorityMixin'
import * as upgradeAuth from './authority-map'

interface IPagination {
  page?: number,
  pageSize?: number
}
@Component({
  components: {
    MonitorDialog,
    Viewer
  }
})
export default class UpgradeConfig extends Mixins(
  commonPageSizeMixin,
  documentLinkMixin,
  authorityMixinCreate(upgradeAuth)
) {
  isMove = false
  tabList: string[] = []
  tabActive = 0
  monitorItems = []
  customMonitorViews = []
  dashboardData = []
  uptimecheckData = []
  scriptCollect = []
  customExporter = []
  monitorPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  customPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  dashboardPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  uptimecheckPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  scriptCollectPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  customExporterPagination: IPagination = {
    page: 1,
    pageSize: this.handleGetCommonPageSize()
  }

  pageList: number[] = [10, 20, 50, 100]
  // needClear: boolean = false
  showDetail = false
  statusMap: any = {}
  detailMarkDown = `# 数据迁移内容总览

## 1. 采集类

以下内容**不支持迁移**

- 组件采集：包含**已下发实例**，以及**自定义导入exporter**
- 脚本采集
- 日志采集`
  loading = false
  get totalData(): Array<any> {
    switch (this.tabActive) {
      case 2:
        return this.monitorItems
      case 3:
        return this.customMonitorViews
      case 4:
        return this.scriptCollect
      case 5:
        return this.customExporter
      case 0:
        return this.dashboardData
      case 1:
        return this.uptimecheckData
      default:
        return []
    }
  }

  get tableData(): Array<any> {
    return this.totalData.slice(
      this.pagination.pageSize * (this.pagination.page - 1),
      this.pagination.pageSize * this.pagination.page
    )
  }

  get pagination(): IPagination {
    switch (this.tabActive) {
      case 2:
        return this.monitorPagination
      case 3:
        return this.customPagination
      case 4:
        return this.scriptCollectPagination
      case 5:
        return this.customExporterPagination
      case 0:
        return this.dashboardPagination
      case 1:
        return this.uptimecheckPagination
      default:
        return {}
    }
  }

  get canMigrateStrategy(): boolean {
    return (this.monitorItems || []).some(item => item.status !== 'SUCCESS')
  }

  created() {
    this.tabList = [
      String(this.$t('仪表盘视图')),
      String(this.$t('拨测任务')),
      String(this.$t('监控策略')),
      String(this.$t('自定义监控视图')),
      String(this.$t('脚本采集')),
      String(this.$t('自定义Exporter'))
    ]
    this.statusMap = {
      READY: {
        name: this.$t('准备'),
        status: 1
      },
      SUCCESS: {
        name: this.$t('成功'),
        status: 2
      },
      FAILED: {
        name: this.$t('失败'),
        status: 3
      }
    }
    this.handleGetListData()
  }

  // 点击tab触发
  handleTabChange(index: number) {
    this.tabActive = index
  }

  // 获取列表数据
  async handleGetListData() {
    this.loading = true
    const data = await listUpgradeItems().catch(() => false)
    this.handleSetData(data)
    this.loading = false
  }

  // 点击开始迁移
  handleExecuteUpgrade(): void {
    // const bkInfo = {
    //   type: 'warning',
    //   title: this.$t('您还未迁移过，当前已经配置的策略，会被\'蓝鲸监控\'的策略覆盖，请确认是否继续。'),
    //   container: document.querySelector('.upgrade-config'),
    //   confirmFn: () => {
    //     this.handleUpgrade()
    //   }
    // }
    // if (this.isMove) {
    //   bkInfo.title = this.$t('您已经迁移过配置，继续会覆盖当前的配置，确认是否继续。')
    //   this.$bkInfo(bkInfo)
    // } else {
    //   this.$bkInfo(bkInfo)
    // }
    this.handleUpgrade()
  }

  async handleUpgrade() {
    this.loading = true
    const data = await executeUpgrade({
      bk_biz_id: this.$store.getters.bizId
    }).catch(() => false)
    this.handleSetData(data)
    this.loading = false
    data && this.$bkMessage({
      theme: 'success',
      message: this.$t('迁移完成，请确认迁移结果')
    })
  }

  // 点击仅创建默认策略
  async handleCreateBuildInStrategy() {
    this.loading = true
    const data = await createBuildInStrategy({
      bk_biz_id: this.$store.getters.bizId
    }).then(() => true)
      .catch(() => false)
    this.loading = false
    data && this.$bkMessage({
      theme: 'success',
      message: this.$t('默认策略创建成功')
    })
  }

  // 刷新table数据
  handleSetData(data): void {
    if (data) {
      this.monitorItems = data.monitor_items ? data.monitor_items.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        oldMonitorName: item.origin_strategy.monitor_name,
        oldStrategyName: item.origin_strategy.item_name,
        originId: item.origin_strategy.item_id,
        status: item.status,
        detail: item.message || '--',
        newStrategyName: item.new_strategy.name || '--',
        newsStrategyId: item.new_strategy.id || 0
      })) : []
      this.customMonitorViews = data.custom_monitor_views ? data.custom_monitor_views.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        oldGroupName: item.origin_menu.name,
        oldViewName: item.origin_view.name,
        newGroupName: item.new_menu.name || '--',
        newViewName: item.new_view.name || '--',
        detail: item.message || '--',
        status: item.status
      })) : []
      this.dashboardData = data.dashboard_views ? data.dashboard_views.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        newViewName: item.new_view.name,
        oldViewName: item.old_view.name,
        detail: item.message || '--',
        status: item.status
      })) : []
      this.uptimecheckData = data.uptimecheck_tasks ? data.uptimecheck_tasks.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        newTaskName: item.new_task.name,
        oldTaskName: item.old_task.name,
        detail: item.message || '--',
        status: item.status
      })) : []
      this.scriptCollect = data.script_collectors ? data.script_collectors.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        pluginName: item.name,
        pluginAliaName: item.display_name,
        id: item.id
      })) : []
      this.customExporter = data.exporter_collectors ? data.exporter_collectors.map(item => ({
        bizName: (this.$store.getters.bizList.find(set => +set.id === +item.bk_biz_id) || { text: '' }).text,
        pluginName: item.name,
        pluginAliaName: item.display_name,
        id: item.id
      })) : []
      for (let i = 0; i < Object.keys(data).length; i++) {
        this.isMove = data[Object.keys(data)[i]].some(item => item.status === 'SUCCESS')
        if (this.isMove) {
          break
        }
      }
    }
  }

  // 切换当前页
  handlePageChange(page: number) {
    this.pagination.page = page
  }

  // 切换页码
  handleLimitChange(limit: number) {
    this.pagination.page = 1
    this.pagination.pageSize = limit
    this.handleSetCommonPageSize(`${limit}`)
  }

  // 跳转策略详情页面
  handleGotoStrategy(id: number | string) {
    const data: any = {
      name: 'strategy-config-detail',
      params: {
        id
      }
    }
    this.$router.push(data)
  }

  // 点击导出时触发
  async handleDownloadPlugin(tabActive, item) {
    this.loading = true
    const data = await exportCollectorAsPlugin({
      config_type: tabActive === 4 ? 'script' : 'exporter',
      config_id: item.id
    }).catch(() => false)
    if (data) {
      const url = process.env.NODE_ENV === 'development'
        ? `${process.env.proxyUrl}/media${data.download_path}`
        : `${window.location.origin}${window.site_url}media${data.download_path}`
      // 创建a标签的方式不会弹新窗口
      const element = document.createElement('a')
      element.setAttribute('href', url)
      // element.setAttribute('download', item.pluginName)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    }
    this.loading = false
  }

  //  停用旧版监控策略
  handleStopStrategy() {
    this.$bkInfo({
      type: 'warning',
      title: this.$t('是否停用所有旧版监控策略？停用后将不再产生告警'),
      container: document.querySelector('.upgrade-config'),
      confirmFn: () => {
        this.loading = true
        disableOldStrategy({
          bk_biz_id: this.$store.getters.bizId
        }).then(() => {
          this.$bkMessage({
            theme: 'success',
            message: this.$t('停用旧版监控策略成功')
          })
        })
          .finally(() => {
            this.loading = false
          })
      }
    })
  }

  async handleUpgradeStrategy() {
    this.loading = true
    this.tabActive = 2
    const data = await migrateStrategy({ bk_biz_id: this.$store.getters.bizId,
      item_ids: this.monitorItems.filter(item => item.status !== 'SUCCESS').map(item => item.originId) })
      .catch(() => [])
    this.$bkMessage({
      message: this.$t('策略迁移完成，请确认迁移结果'),
      theme: 'success'
    })
    if (data.length) {
      data.forEach((item) => {
        const itemData = this.monitorItems.find(set => set.originId === item.origin_strategy.item_id)
        if (itemData) {
          itemData.status = item.status
          itemData.detail = item.message || '--'
          itemData.newStrategyName = item.new_strategy.name || '--'
          itemData.newsStrategyId = item.new_strategy.id || 0
        }
      })
    }
    this.loading = false
  }
}
</script>
<style lang="scss" scoped>
    @import "../home/common/mixins";
    $statusBorderColors: #c4c6cc #2dcb56 #ea3636;
    $statusColors:  #f0f1f5 #94f5a4 #fd9c9c;

    .upgrade-config {
      &-header {
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        .icon-tips {
          color: #979ba5;
          margin-right: 5px;
          font-size: 14px;
          height: 14px;
        }
        .header-detail {
          cursor: pointer;
          color: #3a84ff;
        }
      }
      &-content {
        border-radius: 2px;
        background: #fff;
        margin-bottom: 10px;
        overflow: hidden;

        @include border-1px();
        .tab-list {
          display: flex;
          flex-direction: row;
          justify-content: flex-start;
          align-items: center;
          line-height: 42px;
          background: #fafbfd;
          padding: 0;
          margin: 0;
          font-size: 14px;
          &-item {
            flex: 0 0 120px;
            border-right: 1px solid #dcdee5;
            border-bottom: 1px solid #dcdee5;
            text-align: center;
            &.tab-active {
              color: #3a84ff;
              background: #fff;
              border-bottom: 0;
            }
            &:hover {
              cursor: pointer;
              color: #3a84ff;
            }
          }
          &-blank {
            flex: 1 1 auto;
            height: 42px;
            border-bottom: 1px solid #dcdee5;
          }
        }
        .upgrade-table {
          margin-top: 16px;
          border-left: 0;
          border-right: 0;
          font-size: 12px;
          &:after {
            width: 0;
          }
          &:before {
            height: 0;
          }
          .col-strategy {
            color: #3a84ff;
            cursor: pointer;
          }
          .operate-col {
            cursor: pointer;
            color: #3a84ff;
          }
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
        .upgrade-pagination {
          margin: 15px;
          /deep/ .bk-page-count {
            width: 115px;
          }
        }
      }
      &-footer {
        margin-bottom: 10px;
        .footer-line {
          margin-top: 10px;
          display: flex;
          align-items: center;
          &-btn {
            margin-right: 10px;
          }
        }
      }
      .upgrade-detial-dialog {
        width: 800px;
      }
      /deep/ .bk-dialog-wrapper .bk-dialog-content.bk-dialog-content-drag {
        /* stylelint-disable-next-line declaration-no-important*/
        width: 440px !important;
      }
      /deep/ .bk-dialog-wrapper .bk-info-box .bk-dialog-type-header .header {
        /* stylelint-disable-next-line declaration-no-important*/
        white-space: normal !important;
        font-size: 16px;
      }
    }
</style>
