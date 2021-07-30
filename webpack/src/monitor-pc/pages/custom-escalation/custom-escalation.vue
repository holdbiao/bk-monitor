<template>
  <article class="custom-escalation" v-monitor-loading="{ isLoading: loading }">
    <!--tab（自定义事件、自定义指标）-->
    <section class="custom-escalation-tab">
      <div class="tab-item"
           v-for="item in tab.list"
           :key="item.id"
           :class="{ 'tab-active': item.id === tab.active }"
           @click="handleTabChange(item)">
        {{ item.name }}
      </div>
    </section>
    <!--tab 内容区域-->
    <section class="custom-escalation-content">
      <section class="content-left">
        <page-tips
          style="margin-top: 16px"
          :tips-text="$t('自定义上报是一种最灵活和自由的方式上报数据。如果是通过HTTP上报，agent和插件都不需要安装；如果是通过SDK和命令行上报，依赖bkmonitorbeat采集器。')"
          :link-text="$t('采集器安装前往节点管理')"
          :link-url="`${$store.getters.bkNodemanHost}#/plugin-manager/list`"
          doc-link="fromCustomRreporting">
        </page-tips>
        <!--添加 和 搜索-->
        <section class="content-left-operator">
          <bk-button
            v-authority="{ active: !hasManageAuth }"
            class="mc-btn-add"
            theme="primary"
            @click="hasManageAuth ? addCustomEscalation() : handleSetShowAuthDetail()">
            {{ $t('新建') }}
          </bk-button>
          <bk-input
            ext-cls="operator-input" :placeholder="$t('支持ID/名称搜索')"
            right-icon="bk-icon icon-search"
            v-model="searchValue[tab.active]"
            @change="handleSearch">
          </bk-input>
        </section>
        <!--表格-->
        <section class="content-left-table">
          <bk-table
            v-bkloading="{ isLoading: tableData.loading }"
            size="medium"
            :data="tableData[tab.active]"
            :pagination="pagination[tab.active]"
            @page-change="handlePageChange"
            @page-limit-change="handlePageLimitChange">
            <bk-table-column :label="$t('数据ID')" width="100">
              <template #default="{ row }">
                <span>{{ `#${row.bkDataId}` }}</span>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('名称')" prop="name" min-width="100">
              <template #default="{ row }">
                <span @click="handleGotoDetail(row)" class="col-btn">{{ row.name }}</span>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('监控对象')" prop="scenarioDisplay" min-width="80">
              <template #default="{ row }">
                <span>{{ row.scenarioDisplay.join('-') }}</span>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('关联策略')" width="100">
              <template #default="{ row }">
                <div class="col-strategy">
                  <span :class="{ 'col-btn': row.relatedStrategyCount > 0 }" @click="handleGotoStrategy(row)">{{ row.relatedStrategyCount }}</span>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('创建记录')">
              <template #default="{ row }">
                <div class="col-change">
                  <span class="col-change-author">{{ row.createUser }}</span>
                  <span>{{ row.createTime }}</span>
                </div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('更新记录')">
              <template #default="{ row }">
                <div class="col-change" v-if="row.updateUser && row.updateTime">
                  <span class="col-change-author">{{ row.updateUser }}</span>
                  <span>{{ row.updateTime }}</span>
                </div>
                <div v-else>{{ $t('--') }}</div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('操作')" :width="tab.active === 'customTimeSeries' ? 120 : 80">
              <template #default="{ row }">
                <bk-button
                  v-if="tab.active === 'customTimeSeries'"
                  style="margin-right: 10px;"
                  theme="primary" text
                  @click="handleToView(row.timeSeriesGroupId)"> {{ $t('检查视图') }} </bk-button>
                <span v-bk-tooltips="{ placements: ['top-end'], content: $t('有关联的{0}个策略，请先删除策略。', [row.relatedStrategyCount]), disabled: row.relatedStrategyCount <= 0 }">
                  <bk-button
                    v-authority="{ active: !hasManageAuth }"
                    theme="primary"
                    text
                    :disabled="row.relatedStrategyCount !== 0"
                    @click="hasManageAuth ? handleEscalationDelete(row) : handleSetShowAuthDetail()"> {{ $t('删除') }} </bk-button>
                </span>
              </template>
            </bk-table-column>
            <template #empty>
              <template v-if="hasViewAuth">
                <i class="icon-monitor icon-hint table-empty-icon"></i>
                <div class="table-empty-title"> {{ $t('查询无数据') }} </div>
              </template>
              <template v-else>
                <bk-exception type="403" scene="part">
                  <div>{{$t('您没有该资源的查看权限')}}</div>
                  <bk-button @click="applyUrl && handleGotoApplyAuth()" theme="primary" text>{{$t('去申请')}}</bk-button>
                </bk-exception>
              </template>
            </template>
          </bk-table>
        </section>
      </section>
      <!--说明和SDK下载-->
      <section class="content-right">
        <left-panel :list="panelList"></left-panel>
      </section>
    </section>
  </article>
</template>

<script lang="ts">
import { debounce } from 'throttle-debounce'
import leftPanel from './left-panel.vue'
import commonPageSizeMixin from '../../mixins/commonPageSizeMixin'
import { Component, Watch, Mixins } from 'vue-property-decorator'
import { IList, Itab, ISearchValue, IPanelList,
  ITableData, ISearchParams } from '../../types/custom-escalation/custom-escalation'
import MonitorVue from '../../types/index'
import * as customAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
import { getAuthorityDetail, checkAllowedByActionIds } from '../../../monitor-api/modules/iam'
import pageTips from '../../components/pageTips/pageTips.vue'
Component.registerHooks([
  'beforeRouteEnter'
])

@Component({
  components: {
    leftPanel,
    pageTips
  }
})
export default class customEscalation
  extends Mixins(commonPageSizeMixin, authorityMixinCreate(customAuth))<MonitorVue> {
  private loading = false
  private currentItemIdName = 'bkEventGroupId' // 当前表格 ID 字段
  private pagination = this.handleSetDefaultPagination() // 分页
  private authChecked = false
  private applyUrl = ''
  //  tab 数据
  private tab: Itab = {
    active: 'customEvent',
    list: []
  }

  //  搜索词存放
  private searchValue: ISearchValue = {
    customEvent: '',
    customTimeSeries: ''
  }

  //  搜索防抖函数
  private handleSearch: Function | null = null

  //  表格数据
  private tableData: ITableData = {
    loading: false,
    customEvent: [],
    customTimeSeries: []
  }

  //  右侧使用说明和SDK面板
  private panelList: IPanelList[] = [
    {
      name: 'API',
      id: 'api',
      href: true
    },
    {
      name: 'Python',
      id: 'python',
      href: true
    }
  ]

  get hasManageAuth() {
    return this.tab.active === 'customEvent' ? this.authority.MANAGE_CUSTOM_EVENT : this.authority.MANAGE_CUSTOM_METRIC
  }
  get hasViewAuth() {
    return this.tab.active === 'customEvent' ? this.authority.VIEW_CUSTOM_EVENT : this.authority.VIEW_CUSTOM_METRIC
  }
  @Watch('tab.active')
  onTabActiveChange(v: string) {
    v === 'customEvent' ? this.currentItemIdName = 'bkEventGroupId' : this.currentItemIdName = 'timeSeriesGroupId'
    const hasActive = this.tab.list.some(item => item.id === v && item.hasActive)
    if (!hasActive) {
      this.handleInit()
    }
  }

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (!['custom-escalation-form', 'custom-detail-event', 'custom-detail-timeseries'].includes(from.name)) {
        vm.clearConditions()
      }
      !vm.loading && vm.handleInit()
    })
  }

  created() {
    this.handleSearch = debounce(300, false, this.handleSearchValueChange)
    this.tab.list = [
      {
        name: this.$tc('自定义事件'),
        id: 'customEvent',
        hasActive: false
      },
      {
        name: this.$tc('自定义指标'),
        id: 'customTimeSeries',
        hasActive: false
      }
    ]
  }

  //  初始化界面
  async handleInit(needLoading = false) {
    this.loading = needLoading
    this.tableData.loading = !needLoading
    this.tableData[this.tab.active] = []
    const params: ISearchParams = {
      search_key: this.searchValue[this.tab.active],
      page: this.pagination[this.tab.active].current,
      page_size: this.pagination[this.tab.active].limit
    }
    const hasAuth = await this.handleAuthCheck()
    if (hasAuth) {
      if (this.tab.active === 'customEvent') {
        // 自定义事件
        this.currentItemIdName = 'bkEventGroupId'
        this.tab.list[0].hasActive = true
        const data = await this.$store.dispatch('custom-escalation/getCustomEventList', params)
        this.tableData.customEvent = data.list
        this.pagination.customEvent.count = data.total
        this.authChecked = true
      } else {
        // 自定义指标
        this.currentItemIdName = 'timeSeriesGroupId'
        this.tab.list[1].hasActive = true
        const data = await this.$store.dispatch('custom-escalation/getCustomTimeSeriesList', params)
        this.tableData.customTimeSeries = data.list
        this.pagination.customTimeSeries.count = data.total
        this.authChecked = true
      }
    }
    this.loading = false
    this.tableData.loading = false
  }

  //  tab 切换事件
  handleTabChange(item: IList) {
    this.tab.active = item.id
  }

  //  跳转详情
  handleGotoDetail(row) {
    const name = this.tab.active === 'customEvent' ? 'custom-detail-event' : 'custom-detail-timeseries'
    this.$router.push({
      name,
      params: {
        id: row[this.currentItemIdName],
        type: this.tab.active
      }
    })
  }

  //  跳转策略配置界面
  handleGotoStrategy(row) {
    if (!row.relatedStrategyCount) return
    this.$router.push({
      name: 'strategy-config',
      params: {
        [this.currentItemIdName]: row[this.currentItemIdName] // 时序或者事件ID
      }
    })
  }
  // 权限设置
  async handleAuthCheck(): Promise<boolean> {
    if (this.authChecked) return this.hasViewAuth
    const authName = this.tab.active === 'customEvent' ? customAuth.VIEW_CUSTOM_EVENT : customAuth.VIEW_CUSTOM_METRIC
    const data = await checkAllowedByActionIds({ action_ids: [authName] }).catch(() => false)
    const hasAuth = Array.isArray(data) ? data.some(item => item.is_allowed) : false
    if (!hasAuth) {
      const authDetail =  await getAuthorityDetail({
        action_ids: [authName]
      })
      this.applyUrl = authDetail.apply_url
    }
    this.authChecked = true
    return hasAuth
  }
  // 跳转权限中心
  handleGotoApplyAuth() {
    if (window === top) {
      window.open(this.applyUrl, '__blank')
    } else {
      top.BLUEKING.api.open_app_by_other('bk_iam', this.applyUrl)
    }
  }
  //  添加自定义事件或者时序
  addCustomEscalation() {
    const name = this.tab.active === 'customEvent' ? 'custom-set-event' : 'custom-set-timeseries'
    this.$router.push({
      name,
      params: {
        type: this.tab.active
      }
    })
  }
  // 没有管理权限时处理
  handleSetShowAuthDetail() {
    this.handleShowAuthorityDetail(this.tab.active === 'customEvent'
      ? customAuth.MANAGE_CUSTOM_EVENT
      : customAuth.MANAGE_CUSTOM_METRIC)
  }

  //  搜索
  handleSearchValueChange() {
    // 重置页数
    this.pagination[this.tab.active].current = 1
    this.handleInit()
  }

  //  换页
  handlePageChange(page: number) {
    this.pagination[this.tab.active].current = page
    this.handleInit()
  }

  //  每页条数
  handlePageLimitChange(size: string) {
    if (size !== this.pagination[this.tab.active].limit) {
      this.pagination[this.tab.active].limit = size
      this.pagination[this.tab.active].current = 1
      this.handleSetCommonPageSize(size)
      this.handleInit()
    }
  }

  //  跳转检查视图 （仅时序）
  handleToView(id: string) {
    this.$router.push({ name: 'custom-escalation-view', params: { id } })
  }

  //  删除操作
  handleEscalationDelete(row) {
    const handleDeleteItem = async () => {
      // this.$store.commit('app/SET_MAIN_LOADING', true)
      this.loading = true
      let res
      if (this.tab.active === 'customEvent') {
        res = await this.$store.dispatch(
          'custom-escalation/deleteCustomEvent',
          { bk_event_group_id: row.bkEventGroupId }
        )
      } else {
        res = await this.$store.dispatch(
          'custom-escalation/deleteCustomTimeSeries',
          { time_series_group_id: row.timeSeriesGroupId }
        )
      }
      if (res) {
        this.$bkMessage({
          theme: 'success',
          message: this.$t('删除成功')
        })
        this.pagination[this.tab.active].current = 1
        this.handleInit()
      } else {
        this.loading = false
      }
    }
    this.$bkInfo({
      title: this.$t('确定删除该事件？'),
      confirmFn: () => {
        handleDeleteItem()
      }
    })
  }

  //  设置默认分页参数
  handleSetDefaultPagination() {
    const defaultPageSize = this.handleGetCommonPageSize()
    return {
      customEvent: {
        current: 1,
        count: 0,
        limit: defaultPageSize
      },
      customTimeSeries: {
        current: 1,
        count: 0,
        limit: defaultPageSize
      }
    }
  }

  //  还原分页参数和清空搜索框
  clearConditions() {
    this.pagination = this.handleSetDefaultPagination()
    this.searchValue.customEvent = ''
    this.searchValue.customTimeSeries = ''
  }
}
</script>
<style lang="scss" scoped>
    @import "../../static/css/common";

    @mixin layout-flex($flexDirection, $alignItems, $justifyContent) {
      display: flex;
      flex-direction: $flexDirection;
      align-items: $alignItems;
      justify-content: $justifyContent;
    }

    /deep/ {
      .cell .icon-filter-fill {
        margin-left: 5px;
        color: $slightFontColor;
      }
      .bk-table-empty-block {
        height: 418px;
        background: $whiteColor;
      }
      .bk-table-pagination-wrapper {
        background: $whiteColor;
      }
      .bk-table-pagination .bk-page-total-count {
        line-height: 34px;
        color: $defaultFontColor;
      }
    }
    .custom-escalation {
      margin: -22px -24px 0 -24px;
      padding: 0 24px 20px 24px;
      &-tab {
        margin: 0 -24px 0 -24px;
        padding: 0 24px;
        height: 40px;
        background: $whiteColor;
        border-bottom: 1px solid $defaultBorderColor;
        box-shadow: 0 2px 2px 0 rgba(0,0,0,.05);

        @include layout-flex(row, center, flex-start);
        .tab-item {
          width: 100px;
          height: 40px;
          line-height: 40px;
          font-size: $fontSmSize;
          text-align: center;
          cursor: pointer;
          &:hover {
            color: $primaryFontColor;
          }
        }
        .tab-active {
          color: $primaryFontColor;
          border-bottom: 2px solid $primaryFontColor;
        }
      }
      &-content {
        @include layout-flex(row, stretch, flex-start);
        .content-left {
          flex: 1 1 auto;
          padding-right: 20px;
          height: calc(100vh - 92px);
          overflow-y: auto;
          &-operator {
            margin-top: 20px;

            @include layout-flex(row, center, space-between);
            .operator-input {
              width: 360px;
            }
          }
          &-table {
            margin-top: 16px;
            .col-strategy {
              width: 48px;
              text-align: right;
              color: $unsetColor;
            }
            .col-btn {
              color: $primaryFontColor;
              cursor: pointer;
            }
            .col-change {
              @include layout-flex(column, stretch, flex-start);
              .col-change-author {
                margin-bottom: 3px;
              }
            }
            .col-operator {
              padding-left: 0;
              margin-right: 10px;
            }
            .table-empty-icon {
              font-size: 32px;
              color: $defaultBorderColor;
            }
            .table-empty-title {
              font-size: $fontSmSize;
              margin-top: 10px;
            }
          }
        }
        .content-right {
          flex-basis: 246px;
          margin-right: -24px;
          margin-bottom: -20px;
          border-left: 1px solid $defaultBorderColor;
          border-radius: 0 0 2px 2px;
          background: $whiteColor;
        }
      }
    }
</style>
